from pydantic import BaseModel


class QCMetricsRequest(BaseModel):
    user: str
    project: str
    dataset: str
    mt: str


class QCDoubletsRequest(BaseModel):
    user: str
    project: str
    dataset: str
    countMax: int
    countMin: int
    geneMax: int
    geneMin: int
    mitoMax: int
    mitoMin: int


# cache.py: Global cache for in-memory objects
class GlobalCache:
    _adata = None

    @classmethod
    def set_adata(cls, adata):
        cls._adata = adata

    @classmethod
    def get_adata(cls):
        if cls._adata is None:
            raise ValueError("`adata` is not initialized.")
        return cls._adata
