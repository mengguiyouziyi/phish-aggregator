from __future__ import annotations
from typing import Dict
from pathlib import Path
from ..config import MODELS_DIR

from .detectors.baseline_sklearn import HeuristicBaseline

class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, object] = {}
        self._load_builtin()

    def _load_builtin(self):
        self.models["heuristic_baseline"] = HeuristicBaseline()

        # 延迟加载URLTran模型
        try:
            from .detectors.urltran_wrapper import URLTranWrapper
            self.models["urltran"] = URLTranWrapper()
            print("✅ URLTran model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load URLTran: {e}")
            # 如果URLTran加载失败，不将其添加到模型列表中

        # 延迟加载URLBERT模型
        try:
            from .detectors.urlbert_wrapper import URLBERTWrapper
            self.models["urlbert"] = URLBERTWrapper()
            print("✅ URLBERT model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load URLBERT: {e}")
            # 如果URLBERT加载失败，不将其添加到模型列表中

        # 延迟加载视觉检测模型
        try:
            from .detectors.visual_wrapper import VisualDetectionWrapper
            self.models["phishpedia"] = VisualDetectionWrapper()
            print("✅ Visual detection model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load visual detection model: {e}")
            # 如果视觉检测模型加载失败，不将其添加到模型列表中

        # 延迟加载PhishIntention模型（视觉+交互）
        try:
            from .detectors.phishintention_wrapper import PhishIntentionWrapper
            self.models["phishintention"] = PhishIntentionWrapper()
            print("✅ PhishIntention (visual+interaction) model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load PhishIntention model: {e}")
            # 如果PhishIntention模型加载失败，不将其添加到模型列表中

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
