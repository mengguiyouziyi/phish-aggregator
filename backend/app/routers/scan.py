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
    # 创建规则名称映射
    rule_mapping = {
        "metamask_eth_phishing_detect": "metamask",
        "polkadot_js_phishing": "polkadot",
        "phishing_database": "phishing_database_domains",
        "cryptoscamdb": "cryptoscamdb"
    }

    results = []
    for url in req.urls:
        rhits, reasons = check_with_rules(url, rulesets)
        # 只保留选择的规则，使用映射表
        selected_rules = [rule_mapping.get(rule, rule) for rule in req.use_rules]
        rhits = {k:v for k,v in rhits.items() if k in selected_rules}
        # 同样过滤reasons
        reasons = {k:v for k,v in reasons.items() if k in selected_rules}
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
