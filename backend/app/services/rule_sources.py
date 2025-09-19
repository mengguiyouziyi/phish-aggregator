from __future__ import annotations
from pathlib import Path
import json, requests, time
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import logging

from ..config import RULES_DIR, RULE_SOURCES as RULE_SOURCES_CFG

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """保存JSON文件，确保目录存在"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _save_text(path: Path, text: str):
    """保存文本文件，确保目录存在"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _download_with_retry(url: str, timeout: int = 30, max_retries: int = 3) -> Optional[requests.Response]:
    """带重试机制的下载函数"""
    session = requests.Session()

    # 设置请求头，模拟浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"下载 {url} (尝试 {attempt + 1}/{max_retries})")
            response = session.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"下载失败 {url}: {e}")
            if attempt < max_retries - 1:
                # 指数退避
                wait_time = (2 ** attempt) + 1
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"下载失败，已达最大重试次数: {url}")
                return None

    return None

def fetch_all(timeout=30, max_retries=3) -> dict:
    """拉取所有规则源，逐个容错。"""
    results = {}

    logger.info(f"开始拉取 {len(RULE_SOURCES_CFG)} 个规则源...")

    for key, meta in RULE_SOURCES_CFG.items():
        try:
            rs = RuleSource(key, meta)
            logger.info(f"处理规则源: {key}")

            if meta.get("parser") == "metamask":
                # 下载 config.json
                url = meta["urls"][0]
                r = _download_with_retry(url, timeout, max_retries)
                if r:
                    cfg = r.json()
                    _save_json(rs.local_path("config.json"), cfg)
                    results[key] = {"ok": True, "files": [str(rs.local_path("config.json"))]}
                    logger.info(f"✅ MetaMask 配置下载成功")
                else:
                    results[key] = {"ok": False, "error": "下载失败"}

            elif meta.get("parser") == "polkadot":
                saved = []
                success_count = 0
                for u in meta["urls"]:
                    r = _download_with_retry(u, timeout, max_retries)
                    if r:
                        name = u.split("/")[-1]
                        p = rs.local_path(name)
                        try:
                            if name.endswith(".json"):
                                _save_json(p, r.json())
                            else:
                                _save_text(p, r.text)
                            saved.append(str(p))
                            success_count += 1
                        except Exception as e:
                            logger.error(f"保存文件失败 {name}: {e}")
                            _save_text(p, r.text)  # 降级保存为文本
                            saved.append(str(p))
                            success_count += 1
                    else:
                        logger.warning(f"Polkadot 文件下载失败: {u}")

                if success_count > 0:
                    results[key] = {"ok": True, "files": saved}
                    logger.info(f"✅ Polkadot 成功下载 {success_count}/{len(meta['urls'])} 个文件")
                else:
                    results[key] = {"ok": False, "error": "所有文件下载失败"}

            elif meta.get("parser") == "phishing_database":
                saved = []
                success_count = 0

                # 尝试多个镜像源
                urls = meta["urls"]
                for i, u in enumerate(urls):
                    logger.info(f"尝试 Phishing Database 镜像 {i+1}/{len(urls)}: {u}")
                    r = _download_with_retry(u, timeout, max_retries)
                    if r:
                        name = u.split("/")[-1]
                        p = rs.local_path(name)
                        _save_text(p, r.text)
                        saved.append(str(p))
                        success_count += 1
                        logger.info(f"✅ Phishing Database 镜像 {i+1} 下载成功")
                        break  # 成功一个就停止
                    else:
                        logger.warning(f"Phishing Database 镜像 {i+1} 下载失败")

                if success_count > 0:
                    results[key] = {"ok": True, "files": saved}
                else:
                    results[key] = {"ok": False, "error": "所有镜像源下载失败"}

            elif meta.get("parser") == "cryptoscamdb":
                saved = []

                # 尝试 API
                api_url = meta["urls"][0]
                r = _download_with_retry(api_url, timeout, max_retries)
                if r:
                    try:
                        data = r.json()
                        p = rs.local_path("blacklist_api.json")
                        _save_json(p, data)
                        saved.append(str(p))
                        logger.info(f"✅ CryptoScamDB API 下载成功")
                    except Exception as e:
                        logger.error(f"解析 CryptoScamDB API 响应失败: {e}")

                # 如果 API 失败，尝试备用源
                if not saved and len(meta["urls"]) > 1:
                    backup_urls = meta["urls"][1:]
                    for backup_url in backup_urls:
                        r = _download_with_retry(backup_url, timeout, max_retries)
                        if r:
                            name = backup_url.split("/")[-1]
                            p = rs.local_path(name)
                            try:
                                if backup_url.endswith(".json"):
                                    _save_json(p, r.json())
                                else:
                                    _save_text(p, r.text)
                                saved.append(str(p))
                                logger.info(f"✅ CryptoScamDB 备用源下载成功: {backup_url}")
                                break
                            except Exception as e:
                                logger.error(f"保存备用源失败 {backup_url}: {e}")

                if saved:
                    results[key] = {"ok": True, "files": saved}
                else:
                    results[key] = {"ok": False, "error": "所有源下载失败"}
            else:
                results[key] = {"ok": False, "error": "unknown parser"}

        except Exception as e:
            logger.error(f"处理规则源 {key} 时发生错误: {e}")
            results[key] = {"ok": False, "error": str(e)}

        # 避免请求过快
        time.sleep(0.5)

    # 统计结果
    success_count = sum(1 for r in results.values() if r.get("ok"))
    logger.info(f"拉取完成: {success_count}/{len(RULE_SOURCES_CFG)} 个规则源成功")

    return results


def fetch_source(source_key: str, timeout=30, max_retries=3) -> dict:
    """拉取单个规则源"""
    if source_key not in RULE_SOURCES_CFG:
        return {"ok": False, "error": f"未知的规则源: {source_key}"}

    meta = RULE_SOURCES_CFG[source_key]
    rs = RuleSource(source_key, meta)

    try:
        logger.info(f"拉取单个规则源: {source_key}")

        if meta.get("parser") == "metamask":
            url = meta["urls"][0]
            r = _download_with_retry(url, timeout, max_retries)
            if r:
                cfg = r.json()
                _save_json(rs.local_path("config.json"), cfg)
                return {"ok": True, "files": [str(rs.local_path("config.json"))]}
            else:
                return {"ok": False, "error": "下载失败"}

        # 其他处理逻辑类似...
        return {"ok": False, "error": "暂不支持此规则源的单独拉取"}

    except Exception as e:
        logger.error(f"拉取规则源 {source_key} 失败: {e}")
        return {"ok": False, "error": str(e)}
