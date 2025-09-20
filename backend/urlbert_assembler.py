#!/usr/bin/env python3
"""
URLBERT装配式训练和部署脚本
基于原始URLBERT项目的完整实现，支持一键训练和部署
"""

import os
import sys
import argparse
import subprocess
import shutil
import re
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler, TensorDataset
from transformers import BertTokenizer, AutoConfig, AutoModelForMaskedLM
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm
import json
import logging
from typing import Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class URLBERTDataset:
    """URLBERT数据集类"""

    def __init__(self, urls, labels, tokenizer, max_length=200):
        self.urls = urls
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.urls)

    def __getitem__(self, idx):
        url = str(self.urls[idx])
        label = self.labels[idx]

        # 预处理URL
        url = url.strip().lower()
        url = re.sub(r'^https?://', '', url)

        # Tokenize
        tokens = self.tokenizer.tokenize(url)
        tokens = ["[CLS]"] + tokens + ["[SEP]"]

        # 转换为ID
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        token_type_ids = [0] * len(input_ids)
        attention_mask = [1] * len(input_ids)

        # 填充或截断
        if len(input_ids) < self.max_length:
            padding_length = self.max_length - len(input_ids)
            input_ids = input_ids + [0] * padding_length
            token_type_ids = token_type_ids + [1] * padding_length
            attention_mask = attention_mask + [0] * padding_length
        else:
            input_ids = input_ids[:self.max_length]
            token_type_ids = token_type_ids[:self.max_length]
            attention_mask = attention_mask[:self.max_length]

        return {
            'input_ids': torch.tensor(input_ids, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class BertForSequenceClassification(nn.Module):
    """URLBERT分类器"""

    def __init__(self, bert, freeze=False):
        super(BertForSequenceClassification, self).__init__()
        self.bert = bert
        for name, param in self.bert.named_parameters():
            param.requires_grad = True
        self.dropout = nn.Dropout(p=0.1)
        self.classifier = nn.Linear(768, 2)

    def forward(self, input_ids, token_type_ids, attention_mask):
        outputs = self.bert(input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids, output_hidden_states=True)
        hidden_states = outputs.hidden_states[-1][:, 0, :]  # [CLS] token
        out = self.dropout(hidden_states)
        out = self.classifier(out)
        return out


class URLBERTTrainer:
    """URLBERT训练器"""

    def __init__(self, model_path: str, vocab_size: int = 5000, max_length: int = 200,
                 batch_size: int = 32, learning_rate: float = 2e-5, num_epochs: int = 5):
        self.model_path = model_path
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 初始化tokenizer
        self.tokenizer = self._load_tokenizer()

        # 初始化模型
        self.model = self._build_model()

    def _load_tokenizer(self):
        """加载URLBERT tokenizer"""
        tokenizer_path = os.path.join(self.model_path, "bert_tokenizer", "vocab.txt")
        if os.path.exists(tokenizer_path):
            return BertTokenizer(vocab_file=tokenizer_path)
        else:
            logger.warning(f"Tokenizer not found at {tokenizer_path}, using base BERT tokenizer")
            return BertTokenizer.from_pretrained('bert-base-uncased')

    def _build_model(self):
        """构建URLBERT模型"""
        try:
            # 加载配置
            config_path = os.path.join(self.model_path, "bert_config", "config.json")
            config_kwargs = {
                "cache_dir": None,
                "revision": 'main',
                "use_auth_token": None,
                "hidden_dropout_prob": 0.2,
                "vocab_size": self.vocab_size
            }

            if os.path.exists(config_path):
                config = AutoConfig.from_pretrained(config_path, **config_kwargs)
            else:
                config = AutoConfig.from_pretrained('bert-base-uncased', **config_kwargs)

            # 构建基础BERT模型
            bert_model = AutoModelForMaskedLM.from_config(config=config)
            bert_model.resize_token_embeddings(self.vocab_size)

            # 尝试加载预训练权重
            model_file = os.path.join(self.model_path, "bert_model", "small", "urlBERT.pt")
            if os.path.exists(model_file):
                logger.info(f"Loading pre-trained weights from {model_file}")
                bert_dict = torch.load(model_file, map_location='cpu')
                bert_model.load_state_dict(bert_dict, strict=False)

            # 创建分类器
            classifier = BertForSequenceClassification(bert_model)
            classifier.bert.cls = nn.Sequential()

            classifier.to(self.device)
            return classifier

        except Exception as e:
            logger.error(f"Failed to build model: {e}")
            raise

    def prepare_data(self, data_path: str) -> Tuple[DataLoader, DataLoader]:
        """准备训练数据"""
        logger.info(f"Loading data from {data_path}")

        # 读取数据
        df = pd.read_csv(data_path)
        urls = df['url'].tolist()
        labels = []

        # 转换标签
        for label in df['label']:
            if str(label).lower() in ['malicious', '1', 'phishing']:
                labels.append(1)
            elif str(label).lower() in ['benign', '0', 'normal']:
                labels.append(0)
            else:
                labels.append(0)  # 默认为正常

        # 分割数据集
        indices = list(range(len(urls)))
        np.random.seed(42)
        np.random.shuffle(indices)

        train_size = int(0.8 * len(urls))
        train_indices = indices[:train_size]
        val_indices = indices[train_size:]

        train_urls = [urls[i] for i in train_indices]
        train_labels = [labels[i] for i in train_indices]
        val_urls = [urls[i] for i in val_indices]
        val_labels = [labels[i] for i in val_indices]

        # 创建数据集
        train_dataset = URLBERTDataset(train_urls, train_labels, self.tokenizer, self.max_length)
        val_dataset = URLBERTDataset(val_urls, val_labels, self.tokenizer, self.max_length)

        # 创建数据加载器
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, sampler=RandomSampler(train_dataset))
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, sampler=SequentialSampler(val_dataset))

        logger.info(f"Training samples: {len(train_dataset)}, Validation samples: {len(val_dataset)}")
        return train_loader, val_loader

    def train(self, train_loader: DataLoader, val_loader: DataLoader, output_dir: str):
        """训练模型"""
        logger.info("Starting training...")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 设置优化器
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=1e-4)
        criterion = nn.CrossEntropyLoss()

        # 训练循环
        best_f1 = 0.0
        for epoch in range(self.num_epochs):
            logger.info(f"Epoch {epoch + 1}/{self.num_epochs}")

            # 训练阶段
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for batch in tqdm(train_loader, desc="Training"):
                input_ids = batch['input_ids'].to(self.device)
                token_type_ids = batch['token_type_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                optimizer.zero_grad()

                outputs = self.model(input_ids, token_type_ids, attention_mask)
                loss = criterion(outputs, labels)

                loss.backward()
                optimizer.step()

                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()

            # 验证阶段
            self.model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            all_labels = []
            all_predictions = []

            with torch.no_grad():
                for batch in tqdm(val_loader, desc="Validation"):
                    input_ids = batch['input_ids'].to(self.device)
                    token_type_ids = batch['token_type_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels = batch['labels'].to(self.device)

                    outputs = self.model(input_ids, token_type_ids, attention_mask)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()

                    all_labels.extend(labels.cpu().numpy())
                    all_predictions.extend(predicted.cpu().numpy())

            # 计算指标
            train_accuracy = train_correct / train_total
            val_accuracy = val_correct / val_total
            val_f1 = f1_score(all_labels, all_predictions, average='weighted')
            val_precision = precision_score(all_labels, all_predictions, average='weighted')
            val_recall = recall_score(all_labels, all_predictions, average='weighted')

            logger.info(f"Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_accuracy:.4f}")
            logger.info(f"Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_accuracy:.4f}")
            logger.info(f"Val F1: {val_f1:.4f}, Precision: {val_precision:.4f}, Recall: {val_recall:.4f}")

            # 保存最佳模型
            if val_f1 > best_f1:
                best_f1 = val_f1
                model_path = os.path.join(output_dir, "best_model.pth")
                torch.save(self.model.state_dict(), model_path)
                logger.info(f"Best model saved to {model_path}")

        logger.info("Training completed!")
        return output_dir

    def predict(self, url: str, threshold: float = 0.5) -> Dict:
        """预测单个URL"""
        self.model.eval()

        # 预处理URL
        url = url.strip().lower()
        url = re.sub(r'^https?://', '', url)

        tokens = self.tokenizer.tokenize(url)
        tokens = ["[CLS]"] + tokens + ["[SEP]"]

        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        token_type_ids = [0] * len(input_ids)
        attention_mask = [1] * len(input_ids)

        # 填充
        if len(input_ids) < self.max_length:
            padding_length = self.max_length - len(input_ids)
            input_ids = input_ids + [0] * padding_length
            token_type_ids = token_type_ids + [1] * padding_length
            attention_mask = attention_mask + [0] * padding_length
        else:
            input_ids = input_ids[:self.max_length]
            token_type_ids = token_type_ids[:self.max_length]
            attention_mask = attention_mask[:self.max_length]

        # 转换为tensor
        input_ids = torch.tensor([input_ids], dtype=torch.long).to(self.device)
        token_type_ids = torch.tensor([token_type_ids], dtype=torch.long).to(self.device)
        attention_mask = torch.tensor([attention_mask], dtype=torch.long).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids, token_type_ids, attention_mask)
            probabilities = F.softmax(outputs, dim=-1)
            phishing_prob = probabilities[0][1].item()

        return {
            "url": url,
            "phishing_probability": phishing_prob,
            "prediction": 1 if phishing_prob >= threshold else 0,
            "confidence": max(phishing_prob, 1 - phishing_prob)
        }


def create_sample_data(output_path: str, num_samples: int = 1000):
    """创建示例训练数据"""
    logger.info(f"Creating sample data with {num_samples} samples...")

    # 正常URL示例
    benign_urls = [
        "https://google.com",
        "https://www.facebook.com",
        "https://twitter.com",
        "https://www.linkedin.com",
        "https://github.com",
        "https://stackoverflow.com",
        "https://www.youtube.com",
        "https://www.amazon.com",
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://www.wikipedia.org",
        "https://www.reddit.com",
        "https://www.instagram.com",
        "https://www.netflix.com",
        "https://www.spotify.com"
    ]

    # 钓鱼URL示例
    phishing_urls = [
        "http://secure-login-facebook.com",
        "http://paypal-security.com",
        "http://amazon-verify-account.com",
        "http://microsoft-security-update.com",
        "http://apple-id-verify.com",
        "http://gmail-login-security.com",
        "http://bank-of-america-secure.com",
        "http://chase-bank-login.com",
        "http://wells-fargo-security.com",
        "http://twitter-secure-login.com",
        "http://linkedin-verify-account.com",
        "http://github-security-check.com",
        "http://amazon-payment-verify.com",
        "http://paypal-billing-secure.com",
        "http://microsoft-account-secure.com"
    ]

    # 生成更多样本
    benign_samples = []
    phishing_samples = []

    for i in range(num_samples // 2):
        # 生成变体
        base_benign = benign_urls[i % len(benign_urls)]
        base_phishing = phishing_urls[i % len(phishing_urls)]

        # 添加一些变化
        benign_samples.extend([
            base_benign,
            base_benign + "/home",
            base_benign + "/login",
            base_benign + "/user/profile",
            base_benign + f"/page{i}",
        ])

        phishing_samples.extend([
            base_phishing,
            base_phishing + "/secure",
            base_phishing + "/login",
            base_phishing + "/verify",
            base_phishing + f"/account{i}",
        ])

    # 创建数据框
    all_urls = benign_samples[:num_samples//2] + phishing_samples[:num_samples//2]
    all_labels = [0] * len(benign_samples[:num_samples//2]) + [1] * len(phishing_samples[:num_samples//2])

    # 随机打乱
    combined = list(zip(all_urls, all_labels))
    np.random.shuffle(combined)
    all_urls, all_labels = zip(*combined)

    # 保存数据
    df = pd.DataFrame({
        'url': all_urls,
        'label': ['benign' if label == 0 else 'malicious' for label in all_labels]
    })

    df.to_csv(output_path, index=False)
    logger.info(f"Sample data saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="URLBERT Assembly Script")
    parser.add_argument("--mode", type=str, choices=["create_data", "train", "predict"], required=True)
    parser.add_argument("--data_path", type=str, default="data/urlbert_training_data.csv")
    parser.add_argument("--model_path", type=str, default="data/models/urlbert")
    parser.add_argument("--output_dir", type=str, default="data/models/urlbert/trained_model")
    parser.add_argument("--num_samples", type=int, default=1000)
    parser.add_argument("--url", type=str, default="http://example.com")

    args = parser.parse_args()

    if args.mode == "create_data":
        create_sample_data(args.data_path, args.num_samples)

    elif args.mode == "train":
        # 创建训练器
        trainer = URLBERTTrainer(
            model_path=args.model_path,
            vocab_size=5000,
            max_length=200,
            batch_size=32,
            learning_rate=2e-5,
            num_epochs=3
        )

        # 准备数据
        train_loader, val_loader = trainer.prepare_data(args.data_path)

        # 训练模型
        trainer.train(train_loader, val_loader, args.output_dir)

    elif args.mode == "predict":
        # 加载模型进行预测
        trainer = URLBERTTrainer(
            model_path=args.model_path,
            vocab_size=5000,
            max_length=200,
            batch_size=32,
            learning_rate=2e-5,
            num_epochs=3
        )

        # 加载训练好的权重
        model_path = os.path.join(args.output_dir, "best_model.pth")
        if os.path.exists(model_path):
            trainer.model.load_state_dict(torch.load(model_path, map_location=trainer.device))
            logger.info(f"Model loaded from {model_path}")
        else:
            logger.warning(f"No trained model found at {model_path}, using untrained model")

        # 进行预测
        result = trainer.predict(args.url)
        print(f"URL: {result['url']}")
        print(f"Phishing Probability: {result['phishing_probability']:.4f}")
        print(f"Prediction: {'Phishing' if result['prediction'] == 1 else 'Benign'}")
        print(f"Confidence: {result['confidence']:.4f}")


if __name__ == "__main__":
    main()