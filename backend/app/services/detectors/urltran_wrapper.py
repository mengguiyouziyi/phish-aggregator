from __future__ import annotations
from typing import Dict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import re
import numpy as np

class URLTranWrapper:
    """URLTran模型包装器 - 使用预训练的BERT模型进行URL分类"""

    def __init__(self, name="urltran"):
        self.name = name
        self.model_name = "bert-base-uncased"
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()

    def _load_model(self):
        """加载预训练模型"""
        try:
            print(f"Loading {self.model_name} for URLTran...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=2,
                problem_type="single_label_classification"
            )
            self.model.to(self.device)
            self.model.eval()
            print(f"✅ {self.model_name} loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load {self.model_name}: {e}")
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
                outputs = self.model(**inputs)
                logits = outputs.logits

                # 获取概率
                probabilities = torch.softmax(logits, dim=-1)
                phishing_prob = probabilities[0][1].item()  # 假设索引1是钓鱼类别

                return float(phishing_prob)

        except Exception as e:
            print(f"URLTran prediction failed: {e}")
            return self._heuristic_fallback(url)

    def predict_label(self, url: str, threshold=0.5) -> int:
        """预测URL的标签（0=正常，1=钓鱼）"""
        proba = self.predict_proba(url)
        return int(proba >= threshold)