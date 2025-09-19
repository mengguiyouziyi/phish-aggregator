from __future__ import annotations
from pathlib import Path
import json, re
from typing import Dict, Set, Tuple, List
from .utils import extract_host

from ..config import RULES_DIR

def load_rulesets() -> Dict[str, dict]:
    """加载已下载的清单到内存结构。"""
    rs = {}
    # metamask
    meta_path = RULES_DIR / "metamask_eth_phishing_detect__config.json"
    if meta_path.exists():
        try:
            cfg = json.loads(meta_path.read_text(encoding="utf-8"))
            bl = set(cfg.get("blocklist", []))
            al = set(cfg.get("allowlist", []))
            rs["metamask"] = {"block": bl, "allow": al}
        except Exception:
            pass

    # polkadot
    pd_all = RULES_DIR / "polkadot_js_phishing__all.json"
    if pd_all.exists():
        try:
            data = json.loads(pd_all.read_text(encoding="utf-8"))
            # all.json 为对象映射 { "domain": {...}, ... } 或数组（历史不同版本），做兼容
            if isinstance(data, dict):
                domains = set(data.keys())
            elif isinstance(data, list):
                domains = set(data)
            else:
                domains = set()
            rs["polkadot_all"] = {"block": domains}
        except Exception:
            pass

    # phishing.database (links/domains)
    pdb_links = RULES_DIR / "phishing_database__phishing-links-ACTIVE-NOW.txt"
    if pdb_links.exists():
        try:
            lines = [l.strip() for l in pdb_links.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip() and not l.startswith("#")]
            rs["phishing_db_links"] = {"urls": set(lines)}
        except Exception:
            pass

    pdb_domains = RULES_DIR / "phishing_database__phishing-domains-ACTIVE.txt"
    if pdb_domains.exists():
        try:
            lines = [l.strip() for l in pdb_domains.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip() and not l.startswith("#")]
            rs["phishing_db_domains"] = {"block": set(lines)}
        except Exception:
            pass

    # cryptoscamdb
    cs_api = RULES_DIR / "cryptoscamdb__blacklist_api.json"
    if cs_api.exists():
        try:
            data = json.loads(cs_api.read_text(encoding="utf-8"))
            items = set()
            # API 返回 payload 结构：{"result": {"active": {...}}}（不同版本可能不同，尽量兼容）
            for section in data.values():
                if isinstance(section, dict):
                    for k,v in section.items():
                        if isinstance(v, dict):
                            for dom in v.keys():
                                items.add(dom.lower())
            rs["cryptoscamdb"] = {"block": items}
        except Exception:
            pass

    return rs

def check_with_rules(url: str, rulesets: Dict[str, dict]) -> Tuple[Dict[str, bool], Dict[str, str]]:
    """对单个 URL 进行规则匹配；返回 (命中字典, 命中依据)。"""
    host = extract_host(url)
    hits = {}
    reasons = {}

    # metamask
    mm = rulesets.get("metamask")
    if mm:
        bl = mm.get("block", set())
        al = mm.get("allow", set())
        # 后缀匹配
        if any(host == d or host.endswith("." + d) for d in bl):
            hits["metamask"] = True
            reasons["metamask"] = "blocklist"
        elif any(host == d or host.endswith("." + d) for d in al):
            hits["metamask"] = False
            reasons["metamask"] = "allowlist"

    # polkadot
    pd = rulesets.get("polkadot_all")
    if pd:
        bl = pd.get("block", set())
        if any(host == d or host.endswith("." + d) for d in bl):
            hits["polkadot"] = True
            reasons["polkadot"] = "all.json"

    # phishing.database domains
    pdbd = rulesets.get("phishing_db_domains")
    if pdbd:
        bl = pdbd.get("block", set())
        if any(host == d or host.endswith("." + d) for d in bl):
            hits["phishing_database_domains"] = True
            reasons["phishing_database_domains"] = "phishing-domains-ACTIVE.txt"

    # phishing.database links（整 URL 精确匹配）
    pdbl = rulesets.get("phishing_db_links")
    if pdbl:
        urls = pdbl.get("urls", set())
        if url in urls:
            hits["phishing_database_links"] = True
            reasons["phishing_database_links"] = "phishing-links-ACTIVE-NOW.txt"

    # CryptoScamDB
    cs = rulesets.get("cryptoscamdb")
    if cs:
        bl = cs.get("block", set())
        if any(host == d or host.endswith("." + d) for d in bl):
            hits["cryptoscamdb"] = True
            reasons["cryptoscamdb"] = "API blacklist"

    return hits, reasons
