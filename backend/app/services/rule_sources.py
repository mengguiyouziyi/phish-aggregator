from __future__ import annotations
from pathlib import Path
import json, requests, time

from ..config import RULES_DIR, RULE_SOURCES as RULE_SOURCES_CFG

class RuleSource:
    def __init__(self, key: str, meta: dict):
        self.key = key
        self.meta = meta
        self.local_files = []  # downloaded files

    def local_path(self, filename: str) -> Path:
        return RULES_DIR / f"{self.key}__{filename}"

    def is_installed(self) -> bool:
        # 简单判断是否已拉取过
        return any(RULES_DIR.glob(f"{self.key}__*"))

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _save_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")

def fetch_all(timeout=30) -> dict:
    """拉取所有规则源，逐个容错。"""
    results = {}
    for key, meta in RULE_SOURCES_CFG.items():
        try:
            rs = RuleSource(key, meta)
            if meta.get("parser") == "metamask":
                # 下载 config.json
                url = meta["urls"][0]
                r = requests.get(url, timeout=timeout)
                r.raise_for_status()
                cfg = r.json()
                _save_json(rs.local_path("config.json"), cfg)
                results[key] = {"ok": True, "files": [str(rs.local_path("config.json"))]}
            elif meta.get("parser") == "polkadot":
                saved = []
                for u in meta["urls"]:
                    r = requests.get(u, timeout=timeout)
                    r.raise_for_status()
                    # 文件名取 URL 最后段
                    name = u.split("/")[-1]
                    p = rs.local_path(name)
                    try:
                        # 有些是 json，有些文本
                        if name.endswith(".json"):
                            _save_json(p, r.json())
                        else:
                            _save_text(p, r.text)
                    except Exception:
                        _save_text(p, r.text)
                    saved.append(str(p))
                results[key] = {"ok": True, "files": saved}
            elif meta.get("parser") == "phishing_database":
                saved = []
                for u in meta["urls"]:
                    r = requests.get(u, timeout=timeout)
                    r.raise_for_status()
                    name = u.split("/")[-1]
                    p = rs.local_path(name)
                    _save_text(p, r.text)
                    saved.append(str(p))
                results[key] = {"ok": True, "files": saved}
            elif meta.get("parser") == "cryptoscamdb":
                # 优先 API
                saved = []
                try:
                    u = meta["urls"][0]
                    r = requests.get(u, timeout=timeout)
                    r.raise_for_status()
                    data = r.json()
                    p = rs.local_path("blacklist_api.json")
                    _save_json(p, data)
                    saved.append(str(p))
                except Exception as e:
                    results[key] = {"ok": False, "error": f"API failed: {e}"}
                results[key] = results.get(key, {"ok": True})
                results[key].setdefault("files", []).extend(saved)
            else:
                results[key] = {"ok": False, "error": "unknown parser"}
        except Exception as e:
            results[key] = {"ok": False, "error": str(e)}
        time.sleep(0.2)
    return results
