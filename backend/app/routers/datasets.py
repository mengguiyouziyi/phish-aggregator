from fastapi import APIRouter
from ..services.dataset import load_sample

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.get("/sample")
def get_sample_dataset():
    urls, labels = load_sample()
    return {"size": len(urls), "positives": sum(labels), "negatives": len(urls)-sum(labels)}
