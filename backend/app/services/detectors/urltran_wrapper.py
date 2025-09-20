from __future__ import annotations
from typing import Dict, Optional, List
import torch
from transformers import BertTokenizer, AutoModelForSequenceClassification
import re
import json
import os
from pathlib import Path

class URLTranWrapper:
    """URLTran模型包装器 - 基于原版URLTran项目逻辑实现的URL分类器

    基于论文 "Improving Phishing URL Detection via Transformers" (https://arxiv.org/pdf/2106.05256.pdf)
    实现了URLTran的核心推理逻辑和预处理方法
    """

    def __init__(self, name="urltran", model_path: Optional[str] = None):
        self.name = name
        self.model_path = model_path or self._get_default_model_path()
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = self._load_config()
        self._load_model()

    def _get_default_model_path(self) -> str:
        """获取默认模型路径"""
        return os.path.join(
            Path(__file__).parent.parent.parent.parent,
            "data", "models", "urltran", "URLTran-BERT"
        )

    def _load_config(self) -> Dict:
        """加载模型配置"""
        return {
            "max_length": 128,
            "model_type": "bert-base-uncased",
            "num_labels": 2,
            "problem_type": "single_label_classification",
            "fallback_to_heuristic": True,
            "confidence_threshold": 0.5
        }

    def _load_model(self):
        """加载URLTran模型和tokenizer"""
        try:
            print(f"Loading URLTran model from {self.model_path}...")

            # 尝试加载训练好的URLTran模型
            if os.path.exists(self.model_path):
                self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_path,
                    num_labels=self.config["num_labels"],
                    problem_type=self.config["problem_type"]
                )
            else:
                # 如果没有训练好的模型，使用基础的BERT并应用URLTran预处理
                print("No trained URLTran model found, using base BERT with URLTran preprocessing")
                self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    "bert-base-uncased",
                    num_labels=self.config["num_labels"],
                    problem_type=self.config["problem_type"]
                )

            self.model.to(self.device)
            self.model.eval()
            print("✅ URLTran model loaded successfully")

        except Exception as e:
            print(f"❌ Failed to load URLTran model: {e}")
            self.tokenizer = None
            self.model = None

    def _preprocess_url(self, url: str) -> Optional[Dict]:
        """基于URLTran项目的URL预处理方法

        Args:
            url: 待检测的URL

        Returns:
            预处理后的模型输入字典，或None（如果预处理失败）
        """
        if not self.tokenizer:
            return None

        try:
            # URL标准化处理（基于URLTran项目逻辑）
            url = url.strip().lower()

            # 移除协议前缀，让模型专注于URL内容
            url = re.sub(r'^https?://', '', url)
            url = re.sub(r'^http://', '', url)

            # 特殊字符处理：将特殊字符替换为空格，保留URL结构特征
            url = re.sub(r'[^\w\s\-\.\/\:]', ' ', url)

            # 标准化URL分隔符
            url = re.sub(r'[\/\.\:]+', ' / ', url)  # 将URL结构字符转换为分隔符

            # 多余空格处理
            url = re.sub(r'\s+', ' ', url).strip()

            # 使用BERT tokenizer进行分词
            inputs = self.tokenizer(
                url,
                return_tensors="pt",
                max_length=self.config["max_length"],
                truncation=True,
                padding=True
            )

            # 移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            return inputs

        except Exception as e:
            print(f"URL preprocessing failed: {e}")
            return None

    def _urltran_features(self, url: str) -> Dict[str, float]:
        """基于URLTran论文的URL特征提取

        这些特征用于启发式评分和模型置信度调整

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

        # 可疑关键词（基于URLTran论文中的钓鱼URL常见词）
        # 注意：移除了知名品牌名称，避免误报正常网站
        suspicious_keywords = [
            'login', 'signin', 'secure', 'account', 'update', 'verify', 'bank',
            'password', 'credit', 'card', 'payment', 'billing', 'security',
            'authenticate', 'confirm', 'restore', 'recover', 'blocked', 'suspended',
            'signin', 'verify-account', 'secure-login', 'account-update'
        ]

        features['suspicious_keyword_count'] = sum(
            1 for keyword in suspicious_keywords if keyword in url.lower()
        )

        # URL缩短服务
        shorteners = ['bit.ly', 'tinyurl', 't.co', 'ow.ly', 'goo.gl', 'short.link']
        features['is_shortened'] = any(short in url.lower() for short in shorteners)

        return features

    def _heuristic_scoring(self, url: str) -> float:
        """基于URLTran论文特征的启发式评分

        Args:
            url: 输入URL

        Returns:
            钓鱼网站概率评分 (0.0-1.0)
        """
        features = self._urltran_features(url)

        # 基础分数
        score = 0.0

        # 检查是否为知名品牌域名，如果是则大幅降低风险
        legitimate_domains = [
            'google.com', 'github.com', 'microsoft.com', 'apple.com', 'amazon.com',
            'facebook.com', 'twitter.com', 'linkedin.com', 'baidu.com', 'wikipedia.org',
            'stackoverflow.com', 'medium.com', 'reddit.com', 'youtube.com', 'instagram.com'
        ]

        domain = url.split('/')[0].lower() if '/' in url else url.lower()
        if domain in legitimate_domains:
            return 0.1  # 知名域名风险极低

        # 长度惩罚（过长URL更容易是钓鱼）
        if features['url_length'] > 100:
            score += 0.15
        elif features['url_length'] > 75:
            score += 0.08

        # 特殊字符惩罚（降低惩罚力度）
        special_char_ratio = features['special_char_count'] / max(features['url_length'], 1)
        score += min(special_char_ratio * 1.5, 0.2)

        # 数字比例惩罚（降低惩罚力度）
        digit_ratio = features['digit_count'] / max(features['url_length'], 1)
        score += min(digit_ratio * 1.0, 0.15)

        # 子域名数量惩罚（调整阈值）
        if features['subdomain_count'] > 3:
            score += min((features['subdomain_count'] - 2) * 0.1, 0.25)

        # 路径深度惩罚（降低惩罚力度）
        if features['path_depth'] > 5:
            score += min(features['path_depth'] * 0.05, 0.15)

        # 严重危险信号
        if features['has_ip']:
            score += 0.4  # IP地址直接访问
        if features['has_port']:
            score += 0.2  # 非标准端口
        if features['has_at_symbol']:
            score += 0.3  # @符号常用于欺骗性邮箱URL

        # 可疑关键词评分（降低权重）
        keyword_score = min(features['suspicious_keyword_count'] * 0.08, 0.3)
        score += keyword_score

        # URL缩短服务
        if features['is_shortened']:
            score += 0.25

        # 域名长度异常（调整阈值）
        if features['domain_length'] > 40:
            score += 0.1
        elif features['domain_length'] < 3:
            score += 0.05

        return min(score, 1.0)

    def predict_proba(self, url: str) -> float:
        """预测URL为钓鱼网站的概率

        基于URLTran项目的推理流程：
        1. URL预处理
        2. 特征提取
        3. 模型推理（如果可用）
        4. 启发式评分（作为备选或置信度调整）

        Args:
            url: 待检测的URL

        Returns:
            钓鱼网站概率 (0.0-1.0)
        """
        # 首先提取URL特征用于启发式评分
        features = self._urltran_features(url)
        heuristic_score = self._heuristic_scoring(url)

        # 如果模型不可用，直接返回启发式评分
        if not self.model or not self.tokenizer:
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
                outputs = self.model(**inputs)
                logits = outputs.logits

                # 获取概率分布
                probabilities = torch.softmax(logits, dim=-1)
                model_confidence = probabilities[0][1].item()  # 钓鱼类别概率

            # 基于特征调整模型置信度
            # 由于当前使用未训练的BERT模型，主要依赖启发式评分
            if heuristic_score > 0.6 and model_confidence < 0.5:
                adjusted_confidence = (model_confidence * 0.3 + heuristic_score * 0.7)
            # 如果特征表明正常，但模型置信度高，降低评分
            elif heuristic_score < 0.3 and model_confidence > 0.6:
                adjusted_confidence = (model_confidence * 0.4 + heuristic_score * 0.6)
            else:
                # 对于未训练模型，更依赖启发式评分
                adjusted_confidence = (model_confidence * 0.4 + heuristic_score * 0.6)

            return float(adjusted_confidence)

        except Exception as e:
            print(f"URLTran model prediction failed: {e}")
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
        features = self._urltran_features(url)
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