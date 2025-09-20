from __future__ import annotations
from typing import Dict, List, Optional
from pathlib import Path
from ..config import MODELS_DIR

# 导入新的配置管理器
from .model_config_manager import get_model_manager

class ModelRegistry:
    """基于配置管理器的模型注册表 - 支持热装配"""

    def __init__(self, use_config_manager: bool = True):
        self.use_config_manager = use_config_manager
        self.models: Dict[str, object] = {}
        self.model_manager = None

        if use_config_manager:
            try:
                self.model_manager = get_model_manager()
                print("✅ ModelConfigManager initialized successfully")
            except Exception as e:
                print(f"⚠️  Failed to initialize ModelConfigManager, falling back to legacy mode: {e}")
                self.use_config_manager = False
                self._load_builtin_legacy()

    def _load_builtin_legacy(self):
        """传统模式加载内置模型"""
        try:
            from .detectors.baseline_sklearn import HeuristicBaseline
            self.models["heuristic_baseline"] = HeuristicBaseline()
            print("✅ HeuristicBaseline loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load HeuristicBaseline: {e}")

        try:
            from .detectors.urltran_wrapper import URLTranWrapper
            self.models["urltran"] = URLTranWrapper()
            print("✅ URLTran loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load URLTran: {e}")

        try:
            from .safesurf_detector import SafeSurfWrapper
            self.models["safesurf"] = SafeSurfWrapper()
            print("✅ SafeSurf loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load SafeSurf: {e}")

    def get_model(self, model_name: str):
        """获取模型实例"""
        if self.use_config_manager and self.model_manager:
            return self.model_manager.get_model(model_name)
        else:
            return self.models.get(model_name)

    def list_models(self) -> Dict[str, dict]:
        """列出所有可用模型"""
        if self.use_config_manager and self.model_manager:
            # 使用配置管理器获取模型列表
            models_info = self.model_manager.list_models()
            entries = {}
            for model_name, info in models_info.items():
                entries[model_name] = {
                    "name": info["name"],
                    "installed": True,
                    "type": info["type"],
                    "enabled": info["enabled"],
                    "healthy": info["healthy"],
                    "description": info["description"]
                }
            return entries
        else:
            # 传统模式
            entries = {}
            for k, v in self.models.items():
                entries[k] = {
                    "name": getattr(v, "name", k),
                    "installed": True,
                    "type": "builtin"
                }

            # 检查已下载但未集成的仓库
            for sub in MODELS_DIR.iterdir():
                if sub.is_dir() and sub.name not in entries:
                    entries[sub.name] = {
                        "name": sub.name,
                        "installed": True,
                        "type": "git",
                        "note": "仓库已在 data/models/ 下，但未在后端注册推断包装器"
                    }
            return entries

    def predict_all(self, url: str, use: List[str], threshold: float = 0.5) -> Dict[str, dict]:
        """使用指定模型进行预测"""
        if self.use_config_manager and self.model_manager:
            # 使用配置管理器进行预测
            results = self.model_manager.predict_with_models(url, use)
            output = {}
            for model_name, result in results.items():
                if result["success"]:
                    output[model_name] = {
                        "proba": result["proba"],
                        "label": result["label"]
                    }
                else:
                    output[model_name] = {
                        "proba": None,
                        "label": None,
                        "error": result.get("error", "unknown error")
                    }
            return output
        else:
            # 传统模式
            output = {}
            for key in use:
                if key in self.models:
                    try:
                        m = self.models[key]
                        proba = m.predict_proba(url)
                        output[key] = {
                            "proba": proba,
                            "label": int(proba >= threshold)
                        }
                    except Exception as e:
                        output[key] = {
                            "proba": None,
                            "label": None,
                            "error": str(e)
                        }
                else:
                    output[key] = {
                        "proba": None,
                        "label": None,
                        "error": "model not available"
                    }
            return output

    def get_model_info(self, model_name: str) -> Optional[Dict[str, any]]:
        """获取模型详细信息"""
        if self.use_config_manager and self.model_manager:
            return self.model_manager.get_model_info(model_name)
        else:
            if model_name in self.models:
                model = self.models[model_name]
                return {
                    "name": getattr(model, "name", model_name),
                    "type": "legacy",
                    "installed": True,
                    "healthy": True
                }
            return None

    def health_check(self) -> Dict[str, any]:
        """系统健康检查"""
        if self.use_config_manager and self.model_manager:
            return self.model_manager.health_check()
        else:
            return {
                "total_models": len(self.models),
                "healthy_models": len(self.models),
                "health_ratio": 1.0,
                "config_watcher_active": False,
                "mode": "legacy"
            }

    def reload_config(self):
        """重新加载配置（仅配置管理器模式）"""
        if self.use_config_manager and self.model_manager:
            self.model_manager.reload_config()

    def list_rules(self) -> Dict[str, dict]:
        """列出规则配置（仅配置管理器模式）"""
        if self.use_config_manager and self.model_manager:
            return self.model_manager.list_rules()
        else:
            return {}

    def get_aggregation_config(self) -> Dict[str, any]:
        """获取聚合配置（仅配置管理器模式）"""
        if self.use_config_manager and self.model_manager:
            return self.model_manager.get_aggregation_config()
        else:
            return {
                "strategies": {
                    "any": {"name": "ANY Strategy"},
                    "weighted": {"name": "WEIGHTED Strategy"}
                },
                "default_strategy": "any",
                "default_threshold": 0.5
            }
