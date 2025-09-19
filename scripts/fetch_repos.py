#!/usr/bin/env python3
"""
克隆你给出的教学/演示仓库到 backend/app/data/models/ 下（不默认参与推断）。
"""
import subprocess, sys, os, argparse, json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DIR = BASE / "backend" / "app" / "data" / "models"

REPOS = {
    "safesurf": "https://github.com/abhizaik/SafeSurf",
    "vaibhavbichave": "https://github.com/vaibhavbichave/Phishing-URL-Detection",
    "arvind-rs": "https://github.com/arvind-rs/phishing_detector",
    "shreyam": "https://github.com/ShreyamMaity/Phishing-link-detector",
    "srimani": "https://github.com/srimani-programmer/Phishing-URL-Detector",
    "asrith-reddy": "https://github.com/asrith-reddy/Phishing-detector",
    "azlan-ismail": "https://github.com/azlan-ismail/phishing-ai-detector"  # 可能不存在，脚本会提示
}

def git_clone(url: str, dest: Path) -> bool:
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])
        return True
    except Exception as e:
        print(f"[ERR] git clone failed: {url}: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="只克隆某些 key（见 REPOS）")
    args = parser.parse_args()

    DIR.mkdir(parents=True, exist_ok=True)
    targets = args.only or list(REPOS.keys())

    for key in targets:
        repo = REPOS[key]
        dest = DIR / f"repo_{key}"
        if dest.exists():
            print(f"[OK] {key} 已存在 {dest}")
            continue
        print(f"[*] 克隆 {key}: {repo}")
        ok = git_clone(repo, dest)
        if not ok and key=="azlan-ismail":
            print("[WARN] azlan-ismail/phishing-ai-detector 似乎不存在或私有，已跳过（可更新 REPOS 中的地址）")

    print("[*] 完成")
