#!/usr/bin/env python3
"""
拉取各规则/清单到 backend/app/data/rules 下。
"""
import os, sys, json, time, argparse
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE/"backend"))
from app.services.rule_sources import fetch_all

if __name__ == "__main__":
    print("[*] 开始拉取规则/清单 ...")
    res = fetch_all()
    for k, v in res.items():
        if v.get("ok"):
            print(f"[OK] {k}: {v.get('files')}")
        else:
            print(f"[ERR] {k}: {v.get('error')}")
    print("[*] 完成")
