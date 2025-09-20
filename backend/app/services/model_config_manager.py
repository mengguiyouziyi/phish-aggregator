"""
模型配置热装配管理器

支持动态加载、配置热重载和模型实例化的统一管理系统
"""

from __future__ import annotations
import json
import importlib
import time
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """模型配置数据类"""
    name: str
    type: str
    class_name: str
    module: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    description: str = ""

@dataclass
class RuleConfig:
    """规则配置数据类"""
    name: str
    type: str
    parser: str
    enabled: bool = True
    urls: List[str] = field(default_factory=list)
    update_interval: int = 86400
    description: str = ""

@dataclass
class ModelInstance:
    """模型实例数据类"""
    config: ModelConfig
    instance: Any
    loaded_at: float
    is_healthy: bool = True
    error_count: int = 0
    last_error: Optional[str] = None

class ConfigWatcher(FileSystemEventHandler):
    """配置文件监控器"""

    def __init__(self, manager: 'ModelConfigManager'):
        self.manager = manager
        self.last_modified = 0
        self.debounce_seconds = 5

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.name == "models.json":
            current_time = time.time()
            if current_time - self.last_modified > self.debounce_seconds:
                self.last_modified = current_time
                logger.info("Model configuration file modified, triggering hot reload")
                self.manager.reload_config()

class ModelConfigManager:
    """模型配置管理器 - 实现热装配功能"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self.model_instances: Dict[str, ModelInstance] = {}
        self.rule_configs: Dict[str, RuleConfig] = {}
        self.lock = Lock()
        self.observer: Optional[Observer] = None
        self.watcher: Optional[ConfigWatcher] = None

        # 加载初始配置
        self.reload_config()

        # 启动配置监控
        self._start_config_watcher()

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return os.path.join(
            Path(__file__).parent.parent,
            "config", "models.json"
        )

    def _start_config_watcher(self):
        """启动配置文件监控"""
        try:
            if self.config.get("system", {}).get("config_watcher", {}).get("enabled", False):
                config_dir = Path(self.config_path).parent
                self.watcher = ConfigWatcher(self)
                self.observer = Observer()
                self.observer.schedule(self.watcher, str(config_dir))
                self.observer.start()
                logger.info(f"Config watcher started for {config_dir}")
        except Exception as e:
            logger.warning(f"Failed to start config watcher: {e}")

    def reload_config(self):
        """重新加载配置"""
        try:
            with self.lock:
                # 读取配置文件
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    new_config = json.load(f)

                # 比较配置变化
                old_models = set(self.config.get("models", {}).keys())
                new_models = set(new_config.get("models", {}).keys())

                # 更新配置
                self.config = new_config

                # 处理模型配置变化
                self._handle_model_config_changes(old_models, new_models)

                # 重新加载规则配置
                self._load_rule_configs()

                logger.info("Configuration reloaded successfully")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

    def _handle_model_config_changes(self, old_models: set, new_models: set):
        """处理模型配置变化"""
        # 移除已删除的模型
        removed_models = old_models - new_models
        for model_name in removed_models:
            self._unload_model(model_name)

        # 更新或新增模型
        for model_name in new_models:
            model_config_dict = self.config["models"][model_name]
            if model_name in self.model_instances:
                # 模型已存在，检查是否需要重新加载
                if self._should_reload_model(model_name, model_config_dict):
                    self._reload_model(model_name, model_config_dict)
            else:
                # 新模型，尝试加载
                if model_config_dict.get("enabled", True):
                    self._load_model(model_name, model_config_dict)

    def _should_reload_model(self, model_name: str, new_config: Dict) -> bool:
        """判断是否需要重新加载模型"""
        old_instance = self.model_instances.get(model_name)
        if not old_instance:
            return True

        # 检查配置是否发生重要变化
        old_config = old_instance.config

        # 关键配置项比较
        critical_keys = ["module", "class_name", "config"]
        for key in critical_keys:
            if old_config.get(key) != new_config.get(key):
                logger.info(f"Model {model_name} configuration changed, reloading")
                return True

        return False

    def _load_model(self, model_name: str, config_dict: Dict):
        """加载模型"""
        try:
            # 创建模型配置对象
            model_config = ModelConfig(
                name=config_dict["name"],
                type=config_dict["type"],
                class_name=config_dict["class"],
                module=config_dict["module"],
                enabled=config_dict.get("enabled", True),
                config=config_dict.get("config", {}),
                dependencies=config_dict.get("dependencies", []),
                description=config_dict.get("description", "")
            )

            # 动态导入模块
            module = importlib.import_module(model_config.module)

            # 获取模型类
            model_class = getattr(module, model_config.class_name)

            # 实例化模型
            model_instance = model_class(**model_config.config)

            # 存储模型实例
            self.model_instances[model_name] = ModelInstance(
                config=model_config,
                instance=model_instance,
                loaded_at=time.time(),
                is_healthy=True
            )

            logger.info(f"✅ Model {model_name} loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load model {model_name}: {e}")
            # 创建错误实例记录
            if model_name in self.config["models"]:
                model_config_dict = self.config["models"][model_name]
                model_config = ModelConfig(
                    name=model_config_dict["name"],
                    type=model_config_dict["type"],
                    class_name=model_config_dict["class"],
                    module=model_config_dict["module"],
                    enabled=False,  # 标记为不可用
                    config=model_config_dict.get("config", {}),
                    dependencies=model_config_dict.get("dependencies", []),
                    description=f"Load failed: {str(e)}"
                )

                self.model_instances[model_name] = ModelInstance(
                    config=model_config,
                    instance=None,
                    loaded_at=time.time(),
                    is_healthy=False,
                    last_error=str(e)
                )

    def _reload_model(self, model_name: str, config_dict: Dict):
        """重新加载模型"""
        logger.info(f"Reloading model {model_name}")
        self._unload_model(model_name)
        self._load_model(model_name, config_dict)

    def _unload_model(self, model_name: str):
        """卸载模型"""
        if model_name in self.model_instances:
            instance = self.model_instances[model_name]
            if instance.instance:
                # 尝试清理模型资源
                try:
                    if hasattr(instance.instance, 'cleanup'):
                        instance.instance.cleanup()
                    elif hasattr(instance.instance, 'close'):
                        instance.instance.close()
                except Exception as e:
                    logger.warning(f"Error during model cleanup for {model_name}: {e}")

            del self.model_instances[model_name]
            logger.info(f"Model {model_name} unloaded")

    def _load_rule_configs(self):
        """加载规则配置"""
        self.rule_configs.clear()

        for rule_name, rule_dict in self.config.get("rules", {}).items():
            rule_config = RuleConfig(
                name=rule_dict["name"],
                type=rule_dict["type"],
                parser=rule_dict["parser"],
                enabled=rule_dict.get("enabled", True),
                urls=rule_dict.get("urls", []),
                update_interval=rule_dict.get("update_interval", 86400),
                description=rule_dict.get("description", "")
            )
            self.rule_configs[rule_name] = rule_config

    def get_model(self, model_name: str) -> Optional[Any]:
        """获取模型实例"""
        with self.lock:
            instance_info = self.model_instances.get(model_name)
            if instance_info and instance_info.is_healthy:
                return instance_info.instance
            return None

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        with self.lock:
            instance_info = self.model_instances.get(model_name)
            if instance_info:
                return {
                    "name": instance_info.config.name,
                    "type": instance_info.config.type,
                    "enabled": instance_info.config.enabled,
                    "healthy": instance_info.is_healthy,
                    "loaded_at": instance_info.loaded_at,
                    "error_count": instance_info.error_count,
                    "last_error": instance_info.last_error,
                    "description": instance_info.config.description,
                    "dependencies": instance_info.config.dependencies
                }
            return None

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有模型"""
        with self.lock:
            result = {}
            for model_name, instance_info in self.model_instances.items():
                result[model_name] = {
                    "name": instance_info.config.name,
                    "type": instance_info.config.type,
                    "enabled": instance_info.config.enabled,
                    "healthy": instance_info.is_healthy,
                    "loaded_at": instance_info.loaded_at,
                    "error_count": instance_info.error_count,
                    "last_error": instance_info.last_error,
                    "description": instance_info.config.description
                }
            return result

    def list_rules(self) -> Dict[str, Dict[str, Any]]:
        """列出所有规则"""
        with self.lock:
            result = {}
            for rule_name, rule_config in self.rule_configs.items():
                result[rule_name] = {
                    "name": rule_config.name,
                    "type": rule_config.type,
                    "enabled": rule_config.enabled,
                    "urls_count": len(rule_config.urls),
                    "update_interval": rule_config.update_interval,
                    "description": rule_config.description
                }
            return result

    def get_aggregation_config(self) -> Dict[str, Any]:
        """获取聚合配置"""
        return self.config.get("aggregation", {})

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.config.get("system", {})

    def predict_with_models(self, url: str, model_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """使用指定模型进行预测"""
        results = {}

        for model_name in model_names:
            try:
                model = self.get_model(model_name)
                if model:
                    # 调用模型的预测方法
                    proba = model.predict_proba(url)
                    label = model.predict_label(url,
                        self.config.get("aggregation", {}).get("default_threshold", 0.5)
                    )

                    results[model_name] = {
                        "proba": proba,
                        "label": label,
                        "success": True
                    }
                else:
                    results[model_name] = {
                        "proba": None,
                        "label": None,
                        "success": False,
                        "error": "Model not available"
                    }
            except Exception as e:
                logger.error(f"Prediction failed for model {model_name}: {e}")
                results[model_name] = {
                    "proba": None,
                    "label": None,
                    "success": False,
                    "error": str(e)
                }

                # 更新错误计数
                if model_name in self.model_instances:
                    self.model_instances[model_name].error_count += 1
                    self.model_instances[model_name].last_error = str(e)

        return results

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        healthy_models = 0
        total_models = len(self.model_instances)

        for instance_info in self.model_instances.values():
            if instance_info.is_healthy:
                healthy_models += 1

        return {
            "total_models": total_models,
            "healthy_models": healthy_models,
            "health_ratio": healthy_models / max(total_models, 1),
            "config_watcher_active": self.observer.is_alive() if self.observer else False,
            "config_file_exists": os.path.exists(self.config_path)
        }

    def shutdown(self):
        """关闭管理器"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # 清理所有模型
        for model_name in list(self.model_instances.keys()):
            self._unload_model(model_name)

        logger.info("ModelConfigManager shutdown completed")

# 全局实例
_model_manager: Optional[ModelConfigManager] = None

def get_model_manager() -> ModelConfigManager:
    """获取全局模型管理器实例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelConfigManager()
    return _model_manager

def reload_model_config():
    """重新加载模型配置"""
    manager = get_model_manager()
    manager.reload_config()

def shutdown_model_manager():
    """关闭模型管理器"""
    global _model_manager
    if _model_manager:
        _model_manager.shutdown()
        _model_manager = None