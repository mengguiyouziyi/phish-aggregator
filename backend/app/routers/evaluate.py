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
    use_rules: List[str] = Field(default_factory=lambda: ["metamask_eth_phishing_detect","polkadot_js_phishing","phishing_database","cryptoscamdb"])
    use_models: List[str] = Field(default_factory=lambda: ["heuristic_baseline"])
    strategies: List[str] = ["any", "weighted"]
    threshold: float = 0.5

@router.post("")
def evaluate(req: EvalRequest):
    urls, labels = load_sample()
    rulesets = load_rulesets()
    # 创建规则名称映射
    rule_mapping = {
        "metamask_eth_phishing_detect": "metamask",
        "polkadot_js_phishing": "polkadot",
        "phishing_database": "phishing_database_domains",
        "cryptoscamdb": "cryptoscamdb"
    }

    # 支持多策略评估
    metrics = {}
    details = []

    for strategy in req.strategies:
        y_pred = []
        strategy_rows = []
        for url, yt in zip(urls, labels):
            rhits, reasons = check_with_rules(url, rulesets)
            # 只保留选择的规则，使用映射表
            selected_rules = [rule_mapping.get(rule, rule) for rule in req.use_rules]
            rhits = {k:v for k,v in rhits.items() if k in selected_rules}
            reasons = {k:v for k,v in reasons.items() if k in selected_rules}
            preds = model_reg.predict_all(url, req.use_models, req.threshold)
            agg = aggregate(rhits, preds, strategy=strategy, threshold=req.threshold)
            y_pred.append(agg["label"])
            strategy_rows.append({
                "url": url,
                "true_label": yt,
                "strategies": {
                    strategy: {
                        "agg": agg,
                        "rules": rhits,
                        "models": preds
                    }
                }
            })

        # 合并详细信息
        if not details:
            details = strategy_rows
        else:
            for i, row in enumerate(strategy_rows):
                details[i]["strategies"][strategy] = row["strategies"][strategy]

        # 计算指标
        metrics[strategy] = compute_metrics(labels, y_pred)

    return {"metrics": metrics, "details": details}
