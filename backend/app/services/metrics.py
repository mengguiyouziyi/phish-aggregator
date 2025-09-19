from __future__ import annotations
from typing import List, Dict

def compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt==1 and yp==1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt==0 and yp==0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt==0 and yp==1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt==1 and yp==0)
    total = max(1, len(y_true))
    acc = (tp+tn)/total
    prec = tp/max(1,tp+fp)
    rec = tp/max(1,tp+fn)
    f1 = 2*prec*rec/max(1,prec+rec)
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "tp": tp, "tn": tn, "fp": fp, "fn": fn}
