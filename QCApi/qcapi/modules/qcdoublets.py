from typing import Any
import scanpy as sc
from ..models import GlobalCache, QCDoubletsRequest

def filter_adata(adata: Any, countMx: int, countMn: int, geneMx: int, geneMn: int, mitoMx: int, mitoMn: int):
    mask = (
        (adata.obs.n_genes_by_counts < geneMx) &
        (adata.obs.n_genes_by_counts > geneMn) &
        (adata.obs.pct_counts_mt < mitoMx) &
        (adata.obs.pct_counts_mt > mitoMn) &
        (adata.obs.total_counts < countMx) &
        (adata.obs.total_counts > countMn)
    )

    # Apply the mask to filter AnnData object and perform scrublet
    return sc.pp.scrublet(adata[mask, :])


async def find_qc_doublets(request: QCDoubletsRequest):

    adata = filter_adata(
        GlobalCache.get_adata(), 
        request.countMax, 
        request.countMin, 
        request.geneMax, 
        request.geneMin, 
        request.mitoMax, 
        request.mitoMin
    )
    singlets = adata[adata.obs.predicted_doublet == False]
    