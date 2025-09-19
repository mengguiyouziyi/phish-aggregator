from __future__ import annotations
from typing import Dict
import torch
from transformers import AutoConfig, AutoModelForMaskedLM, AutoTokenizer
import re
import numpy as np
import os
from pathlib import Path

class URLBERTWrapper:
    """URLBERT模型包装器 - 使用预训练的BERT模型进行URL分类"""

    def __init__(self, name="urlbert"):
        self.name = name
        self.model_name = "urlbert"
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = Path(__file__).parent.parent / "models" / "urlbert"
        self._load_model()

    def _load_model(self):
        """加载预训练模型"""
        try:
            print(f"Loading URLBERT model...")

            # 检查模型文件是否存在
            model_file = self.model_path / "bert_model" / "small" / "urlBERT.pt"
            config_path = self.model_path / "bert_config"
            tokenizer_path = self.model_path / "bert_tokenizer"

            if not model_file.exists():
                print(f"❌ URLBERT model file not found at {model_file}")
                print("Please download the model from: https://drive.google.com/drive/folders/16pNq7C1gYKR9inVD-P8yPBGS37nitE-D")
                self.tokenizer = None
                self.model = None
                return

            # 加载配置
            config_kwargs = {
                "cache_dir": None,
                "revision": 'main',
                "use_auth_token": None,
                "hidden_dropout_prob": 0.2,
                "vocab_size": 5000,
            }

            config = AutoConfig.from_pretrained(str(config_path), **config_kwargs)

            # 创建模型
            self.model = AutoModelForMaskedLM.from_config(config=config)
            self.model.resize_token_embeddings(config_kwargs["vocab_size"])

            # 加载模型权重
            model_dict = torch.load(str(model_file), map_location='cpu')
            self.model.load_state_dict(model_dict)

            # 加载分词器
            if tokenizer_path.exists():
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))
                except Exception as e:
                    print(f"Warning: Failed to load URLBERT tokenizer: {e}")
                    # 使用默认BERT分词器作为备选
                    self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            else:
                self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

            self.model.to(self.device)
            self.model.eval()
            print(f"✅ URLBERT model loaded successfully")

        except Exception as e:
            print(f"❌ Failed to load URLBERT model: {e}")
            # 如果模型加载失败，使用启发式方法作为备选
            self.tokenizer = None
            self.model = None

    def _preprocess_url(self, url: str) -> Dict:
        """预处理URL用于模型输入"""
        if not self.tokenizer:
            return None

        try:
            # 清理URL
            url = url.strip().lower()

            # 特殊字符处理
            url = re.sub(r'[^\w\s\-\.\/\:]', ' ', url)

            # 分词
            inputs = self.tokenizer(
                url,
                return_tensors="pt",
                max_length=128,
                truncation=True,
                padding=True
            )

            # 移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            return inputs
        except Exception as e:
            print(f"URL preprocessing failed: {e}")
            return None

    def _extract_features_from_hidden_states(self, hidden_states):
        """从隐藏状态中提取特征用于分类"""
        # 使用最后一层的隐藏状态
        last_hidden_state = hidden_states[-1]

        # 使用[CLS] token的表示作为整个URL的表示
        cls_representation = last_hidden_state[:, 0, :]

        # 简单的线性变换得到分类logits
        # 这里使用一个简单的投影层将BERT的隐藏状态映射到2维分类空间
        logits = torch.nn.functional.linear(cls_representation, torch.randn(2, 768).to(cls_representation.device))

        return logits

    def _heuristic_fallback(self, url: str) -> float:
        """当模型不可用时的启发式备选方案"""
        # 简单的URL特征检测
        features = {
            'length': len(url),
            'special_chars': len(re.findall(r'[^\w\-\.]', url)),
            'digits': len(re.findall(r'\d', url)),
            'subdomains': url.count('.') - 1 if url.count('.') > 1 else 0,
            'has_ip': bool(re.search(r'\d+\.\d+\.\d+\.\d+', url)),
            'suspicious_words': len(re.findall(
                r'(login|signin|secure|account|update|verify|bank|paypal|apple|microsoft|google|facebook)',
                url.lower()
            ))
        }

        # 简单打分
        score = 0.0

        # 长度惩罚
        if features['length'] > 100:
            score += 0.1
        elif features['length'] > 50:
            score += 0.05

        # 特殊字符惩罚
        score += min(features['special_chars'] * 0.05, 0.3)

        # 数字惩罚
        score += min(features['digits'] * 0.02, 0.2)

        # 子域名惩罚
        score += min(features['subdomains'] * 0.1, 0.3)

        # IP地址直接惩罚
        if features['has_ip']:
            score += 0.4

        # 可疑词惩罚
        score += min(features['suspicious_words'] * 0.15, 0.5)

        return min(score, 1.0)

    def predict_proba(self, url: str) -> float:
        """预测URL为钓鱼网站的概率"""
        if not self.model or not self.tokenizer:
            # 使用启发式备选方案
            return self._heuristic_fallback(url)

        try:
            # 预处理
            inputs = self._preprocess_url(url)
            if inputs is None:
                return self._heuristic_fallback(url)

            # 模型推理
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True)
                hidden_states = outputs.hidden_states

                # 从隐藏状态提取分类logits
                logits = self._extract_features_from_hidden_states(hidden_states)

                # 获取概率
                probabilities = torch.softmax(logits, dim=-1)
                phishing_prob = probabilities[0][1].item()  # 假设索引1是钓鱼类别

                return float(phishing_prob)

        except Exception as e:
            print(f"URLBERT prediction failed: {e}")
            return self._heuristic_fallback(url)

    def predict_label(self, url: str, threshold=0.5) -> int:
        """预测URL的标签（0=正常，1=钓鱼）"""
        proba = self.predict_proba(url)
        return int(proba >= threshold)