from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from ..services.dataset import load_sample
from ..services.list_loader import load_rulesets, check_with_rules
from ..services.model_registry import ModelRegistry
from ..services.aggregator import aggregate
from ..services.metrics import compute_metrics

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])
model_reg = ModelRegistry()

class EvalRequest(BaseModel):
    use_models: List[str] = Field(default_factory=lambda: ["heuristic_baseline"])
    strategy: str = "any"
    threshold: float = 0.5
    strategies: Optional[List[str]] = Field(default_factory=lambda: ["any", "weighted"])

@router.post("")
def evaluate(req: EvalRequest):
    urls, labels = load_sample()
    rulesets = load_rulesets()

    # 确定要评测的策略
    strategies = req.strategies or [req.strategy]

    results = {}
    all_details = []

    for strategy in strategies:
        y_pred = []
        rows = []
        for url, yt in zip(urls, labels):
            rhits, reasons = check_with_rules(url, rulesets)
            preds = model_reg.predict_all(url, req.use_models, req.threshold)
            agg = aggregate(rhits, preds, strategy=strategy, threshold=req.threshold)
            y_pred.append(agg["label"])
            rows.append({
                "url": url,
                "true_label": yt,
                "pred": agg["label"],
                "score": agg["score"],
                "rules": rhits,
                "models": preds,
                "agg": agg
            })

        m = compute_metrics(labels, y_pred)
        results[strategy] = m

        # 为详细结果添加策略信息
        for row in rows:
            row_with_strategy = row.copy()
            row_with_strategy["strategy"] = strategy
            all_details.append(row_with_strategy)

    return {"metrics": results, "details": all_details}
