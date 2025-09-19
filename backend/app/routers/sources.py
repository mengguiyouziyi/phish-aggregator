from fastapi import APIRouter
from ..config import RULE_SOURCES as RULE_SOURCES_CFG, MODEL_SOURCES as MODEL_SOURCES_CFG
from ..services.model_registry import ModelRegistry
from pathlib import Path
from ..config import RULES_DIR, MODELS_DIR

router = APIRouter(prefix="/api/sources", tags=["sources"])
model_reg = ModelRegistry()

@router.get("/rules")
def list_rule_sources():
    out = []
    for key, meta in RULE_SOURCES_CFG.items():
        installed = any(RULES_DIR.glob(f"{key}__*"))
        out.append({"key": key, "name": meta["name"], "installed": installed, "homepage": meta.get("homepage")})
    return {"rules": out}

@router.get("/models")
def list_model_sources():
    # 把 config 里列出的 + 已下载但未注册的都返回
    reg = model_reg.list_models()
    out = []
    keys = set()
    for key, meta in MODEL_SOURCES_CFG.items():
        keys.add(key)
        installed = False
        if meta["type"] == "git":
            # 已克隆目录则视为 installed
            if (MODELS_DIR / key).exists():
                installed = True
        else:
            installed = True
        out.append({"key": key, "name": meta["name"], "installed": installed, "homepage": meta.get("repo","local")})
    # 加上注册表里发现的未在 config 中列出的目录
    for k, v in reg.items() if hasattr(reg, "items") else []:
        if k not in keys:
            out.append({"key": k, "name": v.get("name", k), "installed": True, "homepage": "local"})
    return {"models": out}
