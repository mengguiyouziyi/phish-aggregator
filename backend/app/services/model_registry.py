from __future__ import annotations
from typing import Dict
from pathlib import Path
from ..config import MODELS_DIR

from .detectors.baseline_sklearn import HeuristicBaseline

# 这里可继续添加 URLTran / URLBERT / Phishpedia / PhishIntention 的包装器
# 为了开箱即用，目前仅内置 HeuristicBaseline；其余模型通过 scripts/fetch_models.py 安装后可在此扩展。

class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, object] = {}
        self._load_builtin()

    def _load_builtin(self):
        self.models["heuristic_baseline"] = HeuristicBaseline()

    def list_models(self) -> Dict[str, dict]:
        entries = {}
        for k, v in self.models.items():
            entries[k] = {"name": getattr(v, "name", k), "installed": True, "type": "builtin"}
        # 检查已下载但未集成的仓库（显示为可用但未启用）
        for sub in MODELS_DIR.iterdir():
            if sub.is_dir() and sub.name not in entries:
                entries[sub.name] = {"name": sub.name, "installed": True, "type": "git", "note": "仓库已在 data/models/ 下，但未在后端注册推断包装器"}
        return entries

    def predict_all(self, url: str, use: list[str], threshold=0.5) -> Dict[str, dict]:
        out = {}
        for key in use:
            if key in self.models:
                m = self.models[key]
                proba = m.predict_proba(url)
                out[key] = {"proba": proba, "label": int(proba >= threshold)}
            else:
                out[key] = {"proba": None, "label": None, "error": "model not registered"}
        return out
