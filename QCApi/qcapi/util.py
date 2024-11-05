from fastapi import HTTPException, Depends
from pydantic_settings import BaseSettings
from pydantic import Field
import boto3
from functools import lru_cache
import json


class Settings(BaseSettings):
    environment: str = Field("dev", env="ENVIRONMENT")
    dataset_bucket: str = ""
    qc_dataset_bucket: str = ""
    workspace_path: str = "/tmp/workspace"  # Change from /tmp to avoid conflicts

    def initialize_buckets(self) -> None:
        """Set bucket names based on the environment, only called once."""
        if self.environment == "dev":
            self.dataset_bucket = "cellborgdatasetuploadbucket"
            self.qc_dataset_bucket = "cellborgqcdatasetbucket"
        else:
            self.dataset_bucket = f"cellborg-{self.environment}-datasetupload-bucket"
            self.qc_dataset_bucket = f"cellborg-{self.environment}-qcdataset-bucket"
        print(f"Initialized buckets for {self.environment} environment.")


# Use @lru_cache to cache the settings instance
@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.initialize_buckets()
    return settings


@lru_cache()
def get_s3_client():
    """Returns a singleton S3 client."""
    return boto3.client("s3")


async def upload_json_to_s3(
    data: str,
    s3_key: str,
    s3_client: boto3.client = Depends(get_s3_client),
    bucket: str = Depends(lambda: get_settings().qc_dataset_bucket),
):

    try:
        json_data = json.dumps(data)

        # Upload the JSON data to S3
        s3_client.put_object(
            Body=json_data, Bucket=bucket, Key=s3_key, ContentType="application/json"
        )

        print(f"Successfully uploaded JSON to S3: {s3_key}")

    except Exception as e:
        print(f"Failed to upload JSON to S3: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error uploading JSON to S3: {str(e)}"
        )


async def download_file(s3_client, bucket: str, key: str, local_path: str):
    """Download a file from S3."""
    try:
        print(f"Downloading {key} to {local_path}")
        s3_client.download_file(bucket, key, local_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error downloading {key}: {str(e)}"
        )
