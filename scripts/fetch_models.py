#!/usr/bin/env python3
"""
按需克隆/安装可选模型与工具至 backend/app/data/models
仅进行仓库克隆（不自动跑重型安装），并记录安装状态。
"""
import subprocess, sys, os, argparse, json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE / "backend" / "app" / "data" / "models"
CFG_FILE = BASE / "backend" / "app" / "config.py"

# 为了在脚本中读取 MODEL_SOURCES，简单解析 config.py（避免执行导入副作用）
def load_model_sources():
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", CFG_FILE)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)  # type: ignore
    return cfg.MODEL_SOURCES

def git_clone(url: str, dest: Path) -> bool:
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])
        return True
    except Exception as e:
        print(f"[ERR] git clone failed: {url}: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="安装所有条目（可选工具/教学项目不建议全装）")
    parser.add_argument("--items", nargs="*", help="指定 key 列表安装（见 config.MODEL_SOURCES）")
    args = parser.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    sources = load_model_sources()

    targets = list(sources.keys()) if args.all else (args.items or ["urltran", "urlbert"])
    status = {}

    for key in targets:
        meta = sources.get(key)
        if not meta:
            print(f"[SKIP] 未知 key: {key}")
            continue
        if meta.get("type") != "git":
            print(f"[SKIP] {key} 是内置或非git类型")
            status[key] = {"ok": True, "note": "builtin or non-git"}
            continue
        repo = meta["repo"]
        dest = MODELS_DIR / key
        if dest.exists():
            print(f"[OK] {key} 已存在 {dest}")
            status[key] = {"ok": True, "path": str(dest)}
            continue
        print(f"[*] 克隆 {key}: {repo}")
        ok = git_clone(repo, dest)
        if not ok and "azlan-ismail" in repo:
            status[key] = {"ok": False, "error": "repo missing (404?)"}
        else:
            status[key] = {"ok": ok, "path": str(dest) if ok else ""}

    (MODELS_DIR / "_install_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[*] 安装完成，状态写入 data/models/_install_status.json")
