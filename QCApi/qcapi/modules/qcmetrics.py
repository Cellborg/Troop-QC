import os
import asyncio
import scanpy as sc

from boto3 import client as boto3_client
from ..models import GlobalCache, QCMetricsRequest
from ..util import (
    Settings,
    get_s3_client,
    download_file,
    get_settings,
    upload_json_to_s3,
)
from fastapi import HTTPException, Depends
from botocore.exceptions import ClientError, BotoCoreError


async def load_dataset(
    request: QCMetricsRequest,
    s3_client: boto3_client,
    settings: Settings,
):
    """Load dataset files from S3 and store them locally."""
    try:
        prefix = f"{request.user}/{request.project}/{request.dataset}/"
        print(f"Prefix: {prefix}")

        # List files in the dataset bucket
        response = s3_client.list_objects_v2(
            Bucket=settings.dataset_bucket, Prefix=prefix
        )
        files = response.get("Contents", [])

        if not files:
            raise HTTPException(
                status_code=404, detail="No files found in the dataset bucket."
            )

        tasks = []
        for file in files:
            current_key = file["Key"]  # Capture the current file's key in a local variable
            file_name = os.path.basename(current_key)
            local_path = os.path.join(settings.workspace_path, file_name)
            
            # Append the task with captured current_key and its dependent values
            tasks.append(
                download_file(
                    s3_client, settings.dataset_bucket, current_key, local_path
                )
            )

        # Execute downloads concurrently
        await asyncio.gather(*tasks)

        print("All files downloaded successfully.")
        return True

    except HTTPException as e:
        raise e
    except OSError as e:
        print(f"OS error while accessing the workspace: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"OS error while accessing the workspace: {str(e)}"
        )
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        print(f"S3 ClientError: {error_message}")
        raise HTTPException(status_code=500, detail=f"S3 ClientError: {error_message}")
    except BotoCoreError as e:
        print(f"S3 BotoCoreError: {str(e)}")
        raise HTTPException(status_code=500, detail=f"S3 BotoCoreError: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def read_10x_mtx(workspace_path: str = Depends(lambda: get_settings().workspace_path)):
    """ Read a 10X `.mtx` file using Scanpy and return the AnnData object. """
    try:
        print(f"Reading 10X `.mtx` file from: {workspace_path}")

        # Verify if the workspace path exists and is accessible
        if not os.path.exists(workspace_path):
            raise HTTPException(
                status_code=404, detail=f"Workspace path not found: {workspace_path}"
            )

        # Read the `.mtx` file
        adata = sc.read_10x_mtx(
            workspace_path,  # The directory with the `.mtx` file
            var_names="gene_symbols",  # Use gene symbols for variable names
            cache=True,  # Cache the result for faster subsequent reading
        )

        print("10X dataset successfully read.")
        return adata

    except OSError as e:
        print(f"OS error while accessing {workspace_path}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"OS error while accessing the workspace: {str(e)}"
        )
    except ValueError as e:
        print(f"Scanpy value error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error reading 10X data: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def calculate_qc_metrics(request: QCMetricsRequest):

    s3_client = get_s3_client()
    settings = get_settings()

    await load_dataset(request, s3_client, settings)

    adata = read_10x_mtx()

    MIN_GENES = 200
    MIN_CELLS = 3
    sc.pp.filter_cells(adata, MIN_GENES)
    sc.pp.filter_genes(adata, MIN_CELLS)

    # mitochondrial genes, "MT-" for human, "mt-" for mouse
    adata.var["mt"] = adata.var_names.str.startswith(request.mt)
    # ribosomal genes
    adata.var["ribo"] = adata.var_names.str.startswith(("RPS", "RPL"))
    # hemoglobin genes
    adata.var["hb"] = adata.var_names.str.contains("^HB[^(P)]")

    
    # The scanpy function {func}`~scanpy.pp.calculate_qc_metrics` calculates common quality control (QC) metrics, 
    # which are largely based on `calculateQCMetrics` from scater {cite}`McCarthy2017`. One can pass specific gene 
    # population to {func}`~scanpy.pp.calculate_qc_metrics` in order to calculate proportions of counts for these 
    # populations. Mitochondrial, ribosomal and hemoglobin genes are defined by distinct prefixes as listed below.

    sc.pp.calculate_qc_metrics(
        adata, qc_vars=["mt", "ribo", "hb"], inplace=True, log1p=True
    )

    GlobalCache.set_adata(adata)

    data = adata.obs[["n_genes", "total_counts", "pct_counts_mt"]]
    data_to_upload = {
        index: {
            "n_genes": row["n_genes"],
            "total_counts": row["total_counts"],
            "pct_counts_mt": row["pct_counts_mt"],
        }
        for index, row in data.iterrows()
    }

    s3_plots_dir = (
        f"{request.user}/{request.project}/{request.dataset}/QCMetrics/data.json"
    )

    print(f"Uploading QC Metrics data to S3: {s3_plots_dir}")

    await upload_json_to_s3(data_to_upload, s3_plots_dir)
