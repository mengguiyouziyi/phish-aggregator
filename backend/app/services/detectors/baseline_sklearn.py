from __future__ import annotations
from typing import Dict
from ..utils import url_char_features, extract_host

class HeuristicBaseline:
    """一个轻量启发式“模型”——根据 URL 字符特征、可疑词等打分。"""
    def __init__(self, name="heuristic_baseline"):
        self.name = name

    def predict_proba(self, url: str) -> float:
        f = url_char_features(url)
        score = 0.0
        # 简单经验打分（可按需调整权重）
        score += 0.0008 * f["len"]
        score += 0.8    * f["special_ratio"]
        score += 0.6    * (f["susp_words"] > 0)
        score += 0.2    * (f["digits"] > 5)
        host = extract_host(url)
        if host.count("-") >= 2:
            score += 0.2
        # 归一化到 [0,1]
        if score < 0: score = 0.0
        if score > 1: score = 1.0
        return float(score)

    def predict_label(self, url: str, threshold=0.5) -> int:
        return int(self.predict_proba(url) >= threshold)
