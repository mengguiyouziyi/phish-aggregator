from __future__ import annotations
from typing import Dict, Optional, List
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoConfig, AutoModelForMaskedLM, BertTokenizer
import re
import json
import os
from pathlib import Path


class URLBERTWrapper:
    """URLBERT模型包装器 - 基于原始URLBERT项目的实现

    基于论文 "Continuous Multi-Task Pre-training for Malicious URL Detection and Webpage Classification"
    实现了URLBERT的核心推理逻辑和预处理方法
    """

    def __init__(self, name="urlbert", model_path: Optional[str] = None):
        self.name = name
        self.model_path = model_path or self._get_default_model_path()
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = self._load_config()
        self._load_model()

    def _get_default_model_path(self) -> str:
        """获取默认模型路径"""
        # 优先使用训练好的模型路径
        trained_model_path = "/Users/sunyouyou/development/out_projects/phish-aggregator/backend/data/models/urlbert/trained_model"
        if os.path.exists(trained_model_path):
            return trained_model_path
        # 回退到原生URLBERT项目
        return "/Users/sunyouyou/development/out_projects/phish-aggregator/URLBERT"

    def _load_config(self) -> Dict:
        """加载模型配置"""
        return {
            "max_length": 200,
            "vocab_size": 5000,
            "model_type": "bert-base-uncased",
            "hidden_dropout_prob": 0.2,
            "num_labels": 2,
            "problem_type": "single_label_classification",
            "fallback_to_heuristic": True,
            "confidence_threshold": 0.5
        }

    def _load_model(self):
        """加载URLBERT模型和tokenizer"""
        try:
            print(f"Loading URLBERT model from {self.model_path}...")

            # 尝试加载URLBERT原生预训练模型 - 检查多个可能的路径
            possible_model_files = [
                os.path.join(self.model_path, "bert_model", "small", "urlBERT.pt"),  # 原生URLBERT预训练模型
                os.path.join(self.model_path, "best_model.pth"),  # 训练后的模型
                os.path.join(self.model_path, "urlBERT.pt"),  # 直接在模型目录
            ]

            # Tokenizer路径
            tokenizer_paths = [
                os.path.join(self.model_path, "bert_tokenizer", "vocab.txt"),
                os.path.join(os.path.dirname(self.model_path), "bert_tokenizer", "vocab.txt")
            ]
            config_path = os.path.join(self.model_path, "bert_config", "config.json")

            model_file = None
            for path in possible_model_files:
                if os.path.exists(path):
                    model_file = path
                    break

            # 加载tokenizer
            tokenizer_path = None
            for path in tokenizer_paths:
                if os.path.exists(path):
                    tokenizer_path = path
                    break

            if tokenizer_path:
                self.tokenizer = BertTokenizer(vocab_file=tokenizer_path)
                print(f"✅ URLBERT tokenizer loaded from {tokenizer_path}")
            else:
                self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
                print("✅ Base BERT tokenizer loaded")

            if model_file:
                # 加载URLBERT原生预训练模型
                print(f"Loading native URLBERT pre-trained model from {model_file}")

                # 使用URLBERT配置
                config_kwargs = {
                    "cache_dir": None,
                    "revision": 'main',
                    "use_auth_token": None,
                    "hidden_dropout_prob": 0.2,
                    "vocab_size": self.config["vocab_size"]
                }

                if os.path.exists(config_path):
                    config = AutoConfig.from_pretrained(config_path, **config_kwargs)
                else:
                    config = AutoConfig.from_pretrained('bert-base-uncased', **config_kwargs)

                # 构建BERT基础模型
                bert_model = AutoModelForMaskedLM.from_config(config=config)
                bert_model.resize_token_embeddings(self.config["vocab_size"])

                # 加载原生预训练权重
                model_dict = torch.load(model_file, map_location='cpu')
                bert_model.load_state_dict(model_dict, strict=False)

                # 创建分类器
                self.classifier = self._create_classifier(bert_model)
                self.classifier.to(self.device)
                self.classifier.eval()

                print("✅ Native URLBERT pre-trained model loaded successfully")
            else:
                # 如果没有原生预训练模型，使用基础的BERT
                print("No native URLBERT pre-trained model found, using base BERT")

                # 创建基础BERT分类器
                bert_model = AutoModelForMaskedLM.from_pretrained('bert-base-uncased')
                self.classifier = self._create_classifier(bert_model)
                self.classifier.to(self.device)
                self.classifier.eval()

        except Exception as e:
            print(f"❌ Failed to load URLBERT model: {e}")
            self.tokenizer = None
            self.classifier = None

    def _create_classifier(self, bert_model):
        """创建URLBERT分类器"""
        class BertForSequenceClassification(nn.Module):
            def __init__(self, bert, freeze=False):
                super(BertForSequenceClassification, self).__init__()
                self.bert = bert
                for name, param in self.bert.named_parameters():
                    param.requires_grad = True
                self.dropout = nn.Dropout(p=0.1)
                self.classifier = nn.Linear(768, 2)

            def forward(self, input_ids, token_type_ids=None, attention_mask=None):
                outputs = self.bert(input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids, output_hidden_states=True)
                hidden_states = outputs.hidden_states[-1][:,0,:]  # 使用[CLS] token
                out = self.dropout(hidden_states)
                out = self.classifier(out)
                return out

        classifier = BertForSequenceClassification(bert_model)
        classifier.bert.cls = nn.Sequential()  # 移除原始的MLM头
        return classifier

    def _preprocess_url(self, url: str) -> Optional[Dict]:
        """基于URLBERT项目的URL预处理方法

        Args:
            url: 待检测的URL

        Returns:
            预处理后的模型输入字典，或None（如果预处理失败）
        """
        if not self.tokenizer:
            return None

        try:
            # URL标准化处理
            url = url.strip().lower()

            # 移除协议前缀
            url = re.sub(r'^https?://', '', url)
            url = re.sub(r'^http://', '', url)

            # 使用URLBERT tokenizer进行分词
            tokens = self.tokenizer.tokenize(url)
            tokens = ["[CLS]"] + tokens + ["[SEP]"]

            # 获取input_id, seg_id, att_mask
            input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
            token_type_ids = [0] * len(input_ids)
            attention_mask = [1] * len(input_ids)

            # 填充或截断到指定长度
            pad_size = self.config["max_length"]
            if len(input_ids) < pad_size:
                # 填充
                padding_length = pad_size - len(input_ids)
                input_ids = input_ids + [0] * padding_length
                token_type_ids = token_type_ids + [1] * padding_length  # segment设为1表示填充部分
                attention_mask = attention_mask + [0] * padding_length
            else:
                # 截断
                input_ids = input_ids[:pad_size]
                token_type_ids = token_type_ids[:pad_size]
                attention_mask = attention_mask[:pad_size]

            # 转换为tensor
            input_ids = torch.tensor([input_ids], dtype=torch.long)
            token_type_ids = torch.tensor([token_type_ids], dtype=torch.long)
            attention_mask = torch.tensor([attention_mask], dtype=torch.long)

            # 移动到设备
            input_ids = input_ids.to(self.device)
            token_type_ids = token_type_ids.to(self.device)
            attention_mask = attention_mask.to(self.device)

            return {
                "input_ids": input_ids,
                "token_type_ids": token_type_ids,
                "attention_mask": attention_mask
            }

        except Exception as e:
            print(f"URLBERT preprocessing failed: {e}")
            return None

    def _urlbert_features(self, url: str) -> Dict[str, float]:
        """基于URLBERT论文的URL特征提取

        Args:
            url: 输入URL

        Returns:
            特征字典
        """
        features = {}

        # 基础特征
        features['url_length'] = len(url)
        features['domain_length'] = len(url.split('/')[0]) if '/' in url else len(url)
        features['path_length'] = len(url) - len(url.split('/')[0]) - 1 if '/' in url else 0

        # 字符统计
        features['digit_count'] = len(re.findall(r'\d', url))
        features['special_char_count'] = len(re.findall(r'[^\w\-\.]', url))
        features['hyphen_count'] = len(re.findall(r'\-', url))
        features['dot_count'] = len(re.findall(r'\.', url))

        # 结构特征
        features['subdomain_count'] = max(0, url.count('.') - 1)
        features['path_depth'] = url.count('/') - 1 if '/' in url else 0

        # 危险模式
        features['has_ip'] = bool(re.search(r'\d+\.\d+\.\d+\.\d+', url))
        features['has_port'] = bool(re.search(r':\d+', url))
        features['has_at_symbol'] = '@' in url

        # 可疑关键词（基于URLBERT论文中的钓鱼URL常见词）
        suspicious_keywords = [
            'login', 'signin', 'secure', 'account', 'update', 'verify', 'bank',
            'password', 'credit', 'card', 'payment', 'billing', 'security',
            'authenticate', 'confirm', 'restore', 'recover', 'blocked', 'suspended'
        ]

        features['suspicious_keyword_count'] = sum(
            1 for keyword in suspicious_keywords if keyword in url.lower()
        )

        # URL缩短服务
        shorteners = ['bit.ly', 'tinyurl', 't.co', 'ow.ly', 'goo.gl', 'short.link']
        features['is_shortened'] = any(short in url.lower() for short in shorteners)

        return features

    def _heuristic_scoring(self, url: str) -> float:
        """基于URLBERT特征的启发式评分

        Args:
            url: 输入URL

        Returns:
            钓鱼网站概率评分 (0.0-1.0)
        """
        features = self._urlbert_features(url)

        # 基础分数
        score = 0.0

        # 长度惩罚
        if features['url_length'] > 100:
            score += 0.15
        elif features['url_length'] > 75:
            score += 0.08

        # 特殊字符惩罚
        special_char_ratio = features['special_char_count'] / max(features['url_length'], 1)
        score += min(special_char_ratio * 1.5, 0.2)

        # 数字比例惩罚
        digit_ratio = features['digit_count'] / max(features['url_length'], 1)
        score += min(digit_ratio * 1.0, 0.15)

        # 子域名数量惩罚
        if features['subdomain_count'] > 3:
            score += min((features['subdomain_count'] - 2) * 0.1, 0.25)

        # 路径深度惩罚
        if features['path_depth'] > 5:
            score += min(features['path_depth'] * 0.05, 0.15)

        # 严重危险信号
        if features['has_ip']:
            score += 0.4
        if features['has_port']:
            score += 0.2
        if features['has_at_symbol']:
            score += 0.3

        # 可疑关键词评分
        keyword_score = min(features['suspicious_keyword_count'] * 0.08, 0.3)
        score += keyword_score

        # URL缩短服务
        if features['is_shortened']:
            score += 0.25

        return min(score, 1.0)

    def predict_proba(self, url: str) -> float:
        """预测URL为钓鱼网站的概率

        Args:
            url: 待检测的URL

        Returns:
            钓鱼网站概率 (0.0-1.0)
        """
        # 首先提取URL特征用于启发式评分
        features = self._urlbert_features(url)
        heuristic_score = self._heuristic_scoring(url)

        # 如果模型不可用，直接返回启发式评分
        if not self.classifier or not self.tokenizer:
            if self.config.get("fallback_to_heuristic", True):
                return heuristic_score
            else:
                return 0.5  # 中性分数

        try:
            # 预处理URL
            inputs = self._preprocess_url(url)
            if inputs is None:
                return heuristic_score

            # 模型推理
            with torch.no_grad():
                outputs = self.classifier(
                    inputs["input_ids"],
                    inputs["token_type_ids"],
                    inputs["attention_mask"]
                )

                # 获取概率分布
                probabilities = F.softmax(outputs, dim=-1)
                model_confidence = probabilities[0][1].item()  # 钓鱼类别概率

            # 基于特征调整模型置信度
            # 如果启发式评分高但模型置信度低，提高评分
            if heuristic_score > 0.6 and model_confidence < 0.5:
                adjusted_confidence = (model_confidence * 0.3 + heuristic_score * 0.7)
            # 如果特征表明正常，但模型置信度高，降低评分
            elif heuristic_score < 0.3 and model_confidence > 0.6:
                adjusted_confidence = (model_confidence * 0.7 + heuristic_score * 0.3)
            else:
                adjusted_confidence = model_confidence

            return float(adjusted_confidence)

        except Exception as e:
            print(f"URLBERT model prediction failed: {e}")
            return heuristic_score

    def predict_label(self, url: str, threshold: float = 0.5) -> int:
        """预测URL的标签

        Args:
            url: 待检测的URL
            threshold: 分类阈值

        Returns:
            0=正常网站, 1=钓鱼网站
        """
        proba = self.predict_proba(url)
        return int(proba >= threshold)

    def get_feature_analysis(self, url: str) -> Dict:
        """获取URL的详细特征分析

        Args:
            url: 待分析的URL

        Returns:
            包含特征分析和评分的字典
        """
        features = self._urlbert_features(url)
        heuristic_score = self._heuristic_scoring(url)
        model_score = self.predict_proba(url)

        return {
            "url": url,
            "features": features,
            "heuristic_score": heuristic_score,
            "model_score": model_score,
            "final_score": model_score,
            "prediction": self.predict_label(url),
            "risk_factors": self._identify_risk_factors(features, heuristic_score)
        }

    def _identify_risk_factors(self, features: Dict, score: float) -> List[str]:
        """识别风险因素

        Args:
            features: URL特征字典
            score: 风险评分

        Returns:
            风险因素列表
        """
        risk_factors = []

        if features['has_ip']:
            risk_factors.append("使用IP地址而非域名")
        if features['has_port']:
            risk_factors.append("使用非标准端口")
        if features['has_at_symbol']:
            risk_factors.append("包含@符号")
        if features['subdomain_count'] > 3:
            risk_factors.append(f"过多子域名({features['subdomain_count']}个)")
        if features['url_length'] > 100:
            risk_factors.append("URL过长")
        if features['suspicious_keyword_count'] > 2:
            risk_factors.append(f"包含可疑关键词({features['suspicious_keyword_count']}个)")
        if features['is_shortened']:
            risk_factors.append("使用URL缩短服务")
        if features['digit_count'] > features['url_length'] * 0.3:
            risk_factors.append("数字比例过高")

        return risk_factors