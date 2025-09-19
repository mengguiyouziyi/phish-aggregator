#!/usr/bin/env python3
"""
拉取各规则/清单到 backend/app/data/rules 下。
"""
import os, sys, json, time, argparse
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE/"backend"))
from app.services.rule_sources import fetch_all, fetch_source

def main():
    parser = argparse.ArgumentParser(description="拉取钓鱼检测规则清单")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间（秒）")
    parser.add_argument("--retries", type=int, default=3, help="重试次数")
    parser.add_argument("--source", type=str, help="只拉取指定的规则源")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--clean", action="store_true", help="清理现有规则文件")

    args = parser.parse_args()

    if args.clean:
        print("[*] 清理现有规则文件...")
        rules_dir = BASE / "backend" / "app" / "data" / "rules"
        if rules_dir.exists():
            for file in rules_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            print(f"[✓] 已清理 {rules_dir}")
        else:
            print("[!] 规则目录不存在")

    print(f"[*] 开始拉取规则/清单 (超时: {args.timeout}s, 重试: {args.retries}次) ...")

    if args.source:
        print(f"[*] 只拉取规则源: {args.source}")
        res = {args.source: fetch_source(args.source, args.timeout, args.retries)}
    else:
        res = fetch_all(args.timeout, args.retries)

    success_count = 0
    total_count = len(res)

    for k, v in res.items():
        if v.get("ok"):
            print(f"✅ {k}: {len(v.get('files', []))} 个文件")
            if args.verbose:
                for f in v.get('files', []):
                    print(f"   📄 {Path(f).name}")
            success_count += 1
        else:
            print(f"❌ {k}: {v.get('error')}")

    print(f"\n[*] 完成: {success_count}/{total_count} 个规则源成功")

    if success_count < total_count:
        print("\n💡 建议检查网络连接或稍后重试")
        print("   某些规则源可能暂时不可用，但不影响基本功能")

if __name__ == "__main__":
    main()
