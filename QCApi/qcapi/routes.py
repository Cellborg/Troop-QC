from .util import Settings, get_settings
from .models import QCMetricsRequest, QCDoubletsRequest
from .modules.qcmetrics import calculate_qc_metrics
from .modules.qcdoublets import find_qc_doublets
from fastapi import APIRouter, Depends
from pydantic import BaseModel


router = APIRouter()


class TestRequest(BaseModel):
    notting: str

@router.post("/testing")
async def test_route(request: TestRequest):
    return {"result": f"{request.notting}"}

@router.get("/test")
async def read_item(settings: Settings = Depends(get_settings)):
    return {"test": settings.qc_dataset_bucket}

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/qc_metrics")
async def qc_metrics(request: QCMetricsRequest):
    try:
        await calculate_qc_metrics(request)
        return {"success": True, "message": "QC Metrics Collected Successfully"}
    except Exception as err:
        print('ERROR: ', err)
        return {"success": False, "message": err}
    

@router.post("/qc_doublets")
async def qc_doublets(request: QCDoubletsRequest):
    try:
        await find_qc_doublets(request)
        return {"success": True, "message": "QC Doublets Found Successfully"}
    except Exception as err:
        print('ERROR: ', err)
        return {"success": False, "message": err}
