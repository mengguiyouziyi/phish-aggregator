# URLTran 项目使用说明

## 📋 概述

URLTran是基于Transformers的钓鱼网站检测模型，参考论文"Improving Phishing URL Detection via Transformers"实现。当前项目集成了URLTran模型，并提供了完整的训练、部署和使用流程。

## 🏗️ 项目结构

### 核心文件位置

1. **URLTran包装器**: `app/services/detectors/urltran_wrapper.py`
   - 主要的URLTran模型接口
   - 实现了预处理、特征提取、模型推理等功能

2. **原始URLTran项目**: `app/data/models/urltran/`
   - 包含原始URLTran项目的完整实现
   - `classifier.py` - 分类器训练代码
   - `data_prep.py` - 数据预处理代码
   - `README.md` - 原始项目文档

3. **新增装配脚本**:
   - `urltran_assembler.py` - 完整的URLTran训练和部署脚本
   - `setup_urltran.py` - 一键快速设置脚本

### 模型存储位置

- **预期模型路径**: `data/models/urltran/URLTran-BERT/`
- **训练输出路径**: `data/models/urltran/trained_model/`
- **当前状态**: 模型目录存在但为空（仅有.gitkeep文件）

## ⚙️ 当前状态

### 模型加载机制
```python
# 当前URLTran使用以下加载逻辑：
if os.path.exists(model_path):
    # 加载训练好的URLTran模型
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
else:
    # 回退到基础BERT模型 + URLTran预处理
    model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")
```

### 当前配置
- **模型**: bert-base-uncased（未微调）
- **Tokenizer**: BertTokenizer
- **最大长度**: 128
- **设备**: CPU/CUDA自动选择
- **分类**: 二分类（正常/钓鱼）

## 🚀 快速开始

### 方法1: 使用快速设置脚本（推荐）

```bash
# 在backend目录下运行
python setup_urltran.py
```

该脚本会自动：
1. 安装必要依赖
2. 下载预训练BERT模型
3. 创建训练数据
4. 快速训练URLTran模型
5. 更新配置文件
6. 测试模型功能

### 方法2: 手动训练

```bash
# 创建训练数据
python urltran_assembler.py --mode create_data --data_path training_data.csv --num_samples 2000

# 训练模型
python urltran_assembler.py --mode train --data_path training_data.csv --output_dir ./trained_model

# 测试模型
python urltran_assembler.py --mode predict --model_path ./trained_model/best_model --url "http://example.com"
```

## 🔧 配置说明

### 模型配置 (`app/config/models.json`)
```json
{
  "models": {
    "urltran": {
      "name": "URLTran",
      "type": "transformer",
      "class": "URLTranWrapper",
      "module": "app.services.detectors.urltran_wrapper",
      "enabled": true,
      "config": {
        "model_path": "data/models/urltran/URLTran-BERT"
      },
      "dependencies": ["torch", "transformers"]
    }
  }
}
```

## 📊 运行逻辑

### 1. 系统启动流程
```
FastAPI启动 → 加载模型配置 → 初始化URLTranWrapper → 模型就绪
```

### 2. URL检测流程
```
输入URL → URL预处理 → 特征提取 → 模型推理 → 置信度计算 → 结果返回
```

### 3. 详细处理步骤

#### URL预处理 (`_preprocess_url`)
```python
url = url.strip().lower()                    # 标准化
url = re.sub(r'^https?://', '', url)        # 移除协议
url = re.sub(r'[^\w\s\-\.\/\:]', ' ', url)  # 特殊字符处理
url = re.sub(r'[\/\.\:]+', ' / ', url)      # 分隔符标准化
url = re.sub(r'\s+', ' ', url).strip()      # 空格处理
```

#### 特征提取 (`_urltran_features`)
- URL长度、域名长度、路径长度
- 字符统计（数字、特殊字符、连字符、点号）
- 结构特征（子域名数量、路径深度）
- 危险模式（IP地址、端口、@符号）
- 可疑关键词检测
- URL缩短服务识别

#### 启发式评分 (`_heuristic_scoring`)
基于特征的加权评分系统：
- 长度惩罚：过长或过短的URL
- 特殊字符比例惩罚
- 子域名数量惩罚
- 严重危险信号：IP地址、非标准端口、@符号
- 可疑关键词评分
- URL缩短服务标记

#### 模型推理与置信度调整
```python
# 模型推理
with torch.no_grad():
    outputs = model(**inputs)
    probabilities = torch.softmax(logits, dim=-1)
    model_confidence = probabilities[0][1].item()

# 基于特征调整置信度
if heuristic_score > 0.7 and model_confidence < 0.5:
    adjusted_confidence = (model_confidence + heuristic_score) / 2
elif heuristic_score < 0.3 and model_confidence > 0.7:
    adjusted_confidence = (model_confidence * 0.7 + heuristic_score * 0.3)
else:
    adjusted_confidence = model_confidence
```

## 🧪 测试验证

### 当前测试结果
```python
# 测试URL: http://tre-zorbridge-secure.pages.dev/
# 检测结果: 0.6444 (64.44% 概率为钓鱼网站)
# 模型状态: 使用基础BERT + URLTran预处理
# 风险因素: 0个
```

### 测试更多URL
```python
from app.services.detectors.urltran_wrapper import URLTranWrapper

detector = URLTranWrapper()
test_urls = [
    "https://google.com",
    "http://tre-zorbridge-secure.pages.dev/",
    "https://github.com/microsoft/vscode"
]

for url in test_urls:
    proba = detector.predict_proba(url)
    detailed = detector.get_feature_analysis(url)
    print(f"{url}: {proba:.4f}")
```

## 🎯 性能优化建议

### 1. 模型训练优化
- 使用更多训练数据（建议10,000+样本）
- 增加训练epoch（建议3-5个）
- 调整学习率和batch size
- 使用更大的BERT模型（bert-large-uncased）

### 2. 特征工程优化
- 添加更多URL特征（如TLS证书信息、域名注册信息）
- 改进关键词词典
- 优化权重分配

### 3. 部署优化
- 模型量化以减少内存占用
- 使用GPU加速推理
- 实现模型缓存机制

## 📈 与原始项目对比

### 原始URLTran特点
- 使用1.8M URLs进行训练
- 实现了Masked Language Modeling预训练
- 支持多种tokenizer配置
- 完整的训练/验证流程

### 当前实现特点
- 基于原始论文逻辑重新实现
- 集成启发式评分系统
- 支持模型回退机制
- 适配现有项目架构
- 提供详细的特征分析

### 改进之处
1. **更好的错误处理**: 模型加载失败时自动回退
2. **特征增强**: 结合传统特征和深度学习
3. **置信度调整**: 基于启发式规则的置信度修正
4. **易于部署**: 一键设置和训练脚本

## 🔮 未来发展方向

1. **模型优化**: 训练专用的URLTran模型
2. **多模态检测**: 结合网页内容分析
3. **实时更新**: 支持模型在线更新
4. **性能监控**: 添加模型性能监控和预警
5. **A/B测试**: 支持多模型对比测试

---

**注意**: 当前使用的BERT模型未经钓鱼URL数据微调，建议使用提供的训练脚本对模型进行专门训练以获得更好的检测效果。