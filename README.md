# phish-aggregator

一个可直接部署的聚合式钓鱼网址检测 Web 项目。支持：
- **规则/清单**：MetaMask eth-phishing-detect、polkadot{.js} phishing、CryptoScamDB、Phishing.Database 等；
- **模型/工具**：URLTran、URLBERT、Phishpedia、PhishIntention、openSquat，以及你给出的示例/教学项目（SafeSurf、Phishing-URL-Detection、phishing_detector 等）；
- **自由组合**：在 Web 界面选择启用哪些规则、模型，设置聚合策略；
- **对比评测**：内置示例数据集，可一键运行评测，输出 Accuracy/Precision/Recall/F1、混淆矩阵等指标；
- **一键脚本**：`scripts/` 内提供拉取规则/清单与模型/仓库的脚本；
- **Docker**：提供最简 `docker-compose.yml` 直接跑起来。

> 设计目标：**开箱即用（默认只用规则+轻量启发式模型即可运行）**，重型模型（Phishpedia、PhishIntention、URLTran/URLBERT 等）通过 `scripts/fetch_models.py` 按需安装成可选插件。

---

## 快速开始（本机运行）

```bash
# 1) 克隆/解压本项目
cd phish-aggregator

# 2) 创建并激活虚拟环境（建议）
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3) 安装后端依赖
pip install -r backend/requirements.txt

# 4)（可选）拉取规则清单（含 MetaMask / Polkadot / Phishing.Database 等）
python scripts/fetch_rules.py

# 5) 启动服务
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 6) 打开浏览器访问
# http://localhost:8000
```

> 默认不开启重型模型，依旧可用。若需启用 URLTran/URLBERT/Phishpedia/PhishIntention 等，请看下文 “可选模型/工具安装”。

---

## 快速开始（Docker）

```bash
# 1) （首次）可先拉取规则清单到本地卷（可选）
docker run --rm -v $(pwd)/backend/app/data:/data python:3.10-slim   bash -lc "pip install requests && python - <<'PY'
from urllib.request import urlretrieve; import os
os.makedirs('/data/rules', exist_ok=True)
# 示例：Phishing.Database 活跃链接清单
url='https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt'
urlretrieve(url, '/data/rules/phishing_database_links_active_now.txt')
print('done')
PY"

# 2) 启动
docker compose up -d

# 3) 访问 http://localhost:8000
```

---

## Web 界面
- 左侧选择**规则清单**与**模型**，右侧可以输入 URL 列表或选择内置样例数据，点击 “开始扫描”。
- “评测”页可选择当前组合，对内置 `sample` 数据集跑指标并展示对比。

---

## 目录结构

```
phish-aggregator/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                # FastAPI 入口（提供 REST + 静态页）
│  │  ├─ config.py              # 配置
│  │  ├─ routers/               # 路由：sources/scan/evaluate/datasets
│  │  ├─ services/              # 规则/模型加载、聚合、指标、数据集
│  │  ├─ data/
│  │  │  ├─ rules/              # 规则清单缓存（fetch_rules.py 写入）
│  │  │  ├─ models/             # 可选模型权重/仓库（fetch_models.py 写入）
│  │  │  └─ datasets/           # 样例数据集
│  │  └─ static/                # 前端（纯静态，无需 Node）
│  └─ requirements.txt
├─ scripts/
│  ├─ fetch_rules.py            # 拉取规则/清单
│  ├─ fetch_models.py           # 克隆/安装模型&工具（可选）
│  ├─ fetch_repos.py            # 克隆你给的教学/演示仓库（可选）
│  └─ demo_run.sh               # 一键示例运行
├─ docker-compose.yml
├─ Makefile
└─ LICENSE
```

---

## 可选模型/工具安装（按需）

> 下列脚本 **不在本环境执行**，将在你的机器上执行。网络波动/依赖变化会导致失败，脚本已做**容错**并在 `backend/app/data/models/_install_status.json` 标记安装状态。

- URLTran（bfilar/URLTran）  
- URLBERT（Davidup1/URLBERT）  
- Phishpedia（lindsey98/Phishpedia）  
- PhishIntention（lindsey98/PhishIntention）  
- openSquat（atenreiro/opensquat）  
- 教学/演示项目：SafeSurf、Phishing-URL-Detection、phishing_detector、Phishing-link-detector、Phishing-URL-Detector、Phishing-detector 等。

执行：

```bash
python scripts/fetch_models.py      # 可交互选择安装项或加 --all 全装
python scripts/fetch_repos.py       # 克隆你给的教学/演示仓库（可选）
```

> **注意**：`azlan-ismail/phishing-ai-detector` 这个链接当前在 GitHub 上**不可用/未找到**，脚本会标记为 `missing`（你若有新地址，可在 `scripts/fetch_models.py` 里改成新链接）。

---

## 数据与清单来源（精准下载地址，放在代码块中便于复制）

- MetaMask eth-phishing-detect：
  - `https://raw.githubusercontent.com/MetaMask/eth-phishing-detect/main/src/config.json`
- polkadot{.js} phishing：
  - `https://raw.githubusercontent.com/polkadot-js/phishing/master/all.json`
  - `https://raw.githubusercontent.com/polkadot-js/phishing/master/address.json`
- Phishing.Database：
  - `https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt`
  - `https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-domains-ACTIVE.txt`
- CryptoScamDB：
  - 原始仓库：`https://github.com/CryptoScamDB/blacklist`（可尝试 API：`https://api.cryptoscamdb.org/v1/blacklist`）

> 其余模型/项目的精确仓库地址见 `scripts/fetch_models.py` 与 `scripts/fetch_repos.py` 中的清单。

---

## 许可证
本项目整体以 MIT 许可发布；各上游清单/模型保留其各自的原始许可，请遵循其仓库中的许可证文件。
