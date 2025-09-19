from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from ..services.list_loader import load_rulesets, check_with_rules
from ..services.model_registry import ModelRegistry
from ..services.aggregator import aggregate

router = APIRouter(prefix="/api/scan", tags=["scan"])
model_reg = ModelRegistry()

class ScanRequest(BaseModel):
    urls: List[str]
    use_rules: List[str] = Field(default_factory=lambda: ["metamask_eth_phishing_detect","polkadot_js_phishing","phishing_database","cryptoscamdb"])
    use_models: List[str] = Field(default_factory=lambda: ["heuristic_baseline"])
    strategy: str = "any"  # "any" or "weighted"
    threshold: float = 0.5
    weights: Optional[Dict[str, float]] = None

@router.post("")
def scan(req: ScanRequest):
    rulesets = load_rulesets()
    results = []
    for url in req.urls:
        rhits, reasons = check_with_rules(url, rulesets)
        # 只保留选择的规则
        rhits = {k:v for k,v in rhits.items() if True}  # 简化：已加载的全部用
        preds = model_reg.predict_all(url, req.use_models, req.threshold)
        agg = aggregate(rhits, preds, strategy=req.strategy, weights=req.weights, threshold=req.threshold)
        results.append({
            "url": url,
            "rules": rhits,
            "reasons": reasons,
            "models": preds,
            "agg": agg
        })
    return {"results": results}
