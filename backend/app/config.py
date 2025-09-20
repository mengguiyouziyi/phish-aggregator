import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("AGG_DATA_DIR", BASE_DIR / "data")).resolve()

RULES_DIR = DATA_DIR / "rules"
MODELS_DIR = DATA_DIR / "models"
DATASETS_DIR = DATA_DIR / "datasets"

RULES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# 规则与模型源清单（用于前端展示、脚本和后端统一引用）
RULE_SOURCES = {
    "metamask_eth_phishing_detect": {
        "name": "MetaMask eth-phishing-detect",
        "type": "domainlist",
        "urls": [
            "https://raw.githubusercontent.com/MetaMask/eth-phishing-detect/main/src/config.json"
        ],
        "parser": "metamask",
        "license": "varies (see repo)",
        "homepage": "https://github.com/MetaMask/eth-phishing-detect"
    },
    "polkadot_js_phishing": {
        "name": "polkadot{.js} phishing",
        "type": "domainlist",
        "urls": [
            "https://raw.githubusercontent.com/polkadot-js/phishing/master/all.json",
            "https://raw.githubusercontent.com/polkadot-js/phishing/master/address.json"
        ],
        "parser": "polkadot",
        "license": "varies (see repo)",
        "homepage": "https://polkadot.js.org/phishing/"
    },
    "phishing_database": {
        "name": "Phishing.Database",
        "type": "urllist",
        "urls": [
            "https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt",
            "https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-domains-ACTIVE.txt",
            # 备用镜像源
            "https://cdn.jsdelivr.net/gh/Phishing-Database/Phishing.Database@master/phishing-links-ACTIVE-NOW.txt",
            "https://cdn.jsdelivr.net/gh/Phishing-Database/Phishing.Database@master/phishing-domains-ACTIVE.txt",
            "https://gitcdn.xyz/repo/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt",
            "https://gitcdn.xyz/repo/Phishing-Database/Phishing.Database/master/phishing-domains-ACTIVE.txt"
        ],
        "parser": "phishing_database",
        "license": "MIT",
        "homepage": "https://github.com/Phishing-Database/Phishing.Database"
    },
    "cryptoscamdb": {
        "name": "CryptoScamDB (API)",
        "type": "domainlist",
        "urls": [
            "https://api.cryptoscamdb.org/v1/blacklist"
        ],
        "parser": "cryptoscamdb",
        "license": "MIT (varies by dataset)",
        "homepage": "https://github.com/CryptoScamDB/blacklist",
        "note": "GitHub仓库文件路径可能已变更，目前仅依赖API"
    }
}

MODEL_SOURCES = {
    "heuristic_baseline": {
        "name": "Heuristic Baseline (内置)",
        "type": "local",
        "installed": True,
        "homepage": "local"
    },
    "urltran": {
        "name": "URLTran",
        "type": "git",
        "repo": "https://github.com/bfilar/URLTran",
        "installed": True
    },
    "urlbert": {
        "name": "URLBERT",
        "type": "git",
        "repo": "https://github.com/Davidup1/URLBERT",
        "installed": True
    },
    "phishpedia": {
        "name": "Phishpedia (视觉)",
        "type": "local",
        "installed": True,
        "description": "基于视觉相似性的钓鱼网站检测",
        "note": "使用ResNet50特征提取和Playwright截图"
    },
    "phishintention": {
        "name": "PhishIntention (视觉+交互)",
        "type": "local",
        "installed": True,
        "description": "基于视觉相似性和交互模式的钓鱼网站检测",
        "note": "结合视觉分析和交互行为分析的综合检测模型"
    },
    "opensquat": {
        "name": "openSquat (同形/近似域)",
        "type": "local",
        "installed": True,
        "description": "基于同形字符和域名相似度的钓鱼网站检测",
        "note": "检测同形字符攻击、域名相似性和域名结构异常"
    },
    # 你给的教学/演示项目（通过 fetch_repos.py 克隆，默认不参与推断，仅展示/比对可用特征或调用其模型若适配）
    "safesurf": {
        "name": "SafeSurf (教学/工具)",
        "type": "git",
        "repo": "https://github.com/abhizaik/SafeSurf",
        "installed": False
    },
    "vaibhav_phishing_url_detection": {
        "name": "Phishing-URL-Detection (vaibhavbichave)",
        "type": "git",
        "repo": "https://github.com/vaibhavbichave/Phishing-URL-Detection",
        "installed": False
    },
    "arvind_phishing_detector": {
        "name": "phishing_detector (arvind-rs)",
        "type": "git",
        "repo": "https://github.com/arvind-rs/phishing_detector",
        "installed": False
    },
    "shreyam_phishing_link_detector": {
        "name": "Phishing-link-detector (ShreyamMaity)",
        "type": "git",
        "repo": "https://github.com/ShreyamMaity/Phishing-link-detector",
        "installed": False
    },
    "srimani_phishing_url_detector": {
        "name": "Phishing-URL-Detector (srimani-programmer)",
        "type": "git",
        "repo": "https://github.com/srimani-programmer/Phishing-URL-Detector",
        "installed": False
    },
    "asrith_phishing_detector": {
        "name": "Phishing-detector (asrith-reddy)",
        "type": "git",
        "repo": "https://github.com/asrith-reddy/Phishing-detector",
        "installed": False
    },
    "azlan_phishing_ai_detector": {
        "name": "phishing-ai-detector (azlan-ismail)",
        "type": "git",
        "repo": "https://github.com/azlan-ismail/phishing-ai-detector",
        "installed": False,
        "note": "（当前链接在 GitHub 未找到，脚本会标记 missing）"
    }
}
