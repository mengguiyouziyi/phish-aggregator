from __future__ import annotations
from typing import Dict

def aggregate(rule_hits: Dict[str, bool], model_preds: Dict[str, dict], strategy="any", weights=None, threshold=0.5) -> Dict[str, float]:
    """
    strategy:
      - "any": 任一规则命中 或 任一模型≥thr 即恶意
      - "weighted": 对模型概率做加权平均 + 规则命中直接加分
    """
    decision = 0
    score = 0.0

    if strategy == "any":
        if any(v for v in rule_hits.values()):
            decision = 1
            score = 1.0
        else:
            maxp = 0.0
            for v in model_preds.values():
                p = v.get("proba") or 0.0
                if p > maxp: maxp = p
            decision = int(maxp >= threshold)
            score = maxp
        return {"label": decision, "score": score}

    # weighted
    wsum = 0.0
    psum = 0.0
    if weights:
        for k, v in model_preds.items():
            p = v.get("proba")
            if p is None: 
                continue
            w = float(weights.get(k, 1.0))
            wsum += w
            psum += w * p
    else:
        cnt = 0
        for v in model_preds.values():
            p = v.get("proba")
            if p is None: continue
            psum += p
            cnt += 1
        wsum = max(1, cnt)
    avgp = psum / wsum
    # 规则命中给 0.2 加成（最多 1.0）
    if any(v for v in rule_hits.values()):
        avgp = min(1.0, avgp + 0.2)
    return {"label": int(avgp >= threshold), "score": avgp}
