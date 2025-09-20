#!/usr/bin/env python3
"""
URLTran模型装配和训练脚本
基于原始URLTran项目实现完整的模型训练和部署流程

参考论文: "Improving Phishing URL Detection via Transformers" (https://arxiv.org/pdf/2106.05256.pdf)
原始项目: https://github.com/s2w-berkeley/URLTran
"""

import os
import sys
import json
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoConfig,
    BertTokenizer,
    AdamW,
    get_linear_schedule_with_warmup
)
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class URLTranDataset(Dataset):
    """URLTran数据集类 - 基于原始项目实现"""

    def __init__(self, urls: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.urls = urls
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

        # 预处理所有URL
        self.encodings = self._preprocess_urls()

    def _preprocess_urls(self):
        """基于URLTran项目的URL预处理方法"""
        processed_urls = []

        for url in self.urls:
            # URL标准化处理（基于原始URLTran逻辑）
            url = str(url).strip().lower()

            # 移除协议前缀
            url = url.replace('https://', '').replace('http://', '')

            # 特殊字符处理：将特殊字符替换为空格，保留URL结构特征
            import re
            url = re.sub(r'[^\w\s\-\.\/\:]', ' ', url)

            # 标准化URL分隔符
            url = re.sub(r'[\/\.\:]+', ' / ', url)

            # 多余空格处理
            url = re.sub(r'\s+', ' ', url).strip()

            processed_urls.append(url)

        # 使用tokenizer编码
        encodings = self.tokenizer(
            processed_urls,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="pt"
        )

        return encodings

    def __len__(self):
        return len(self.urls)

    def __getitem__(self, idx):
        item = {
            'input_ids': self.encodings['input_ids'][idx],
            'attention_mask': self.encodings['attention_mask'][idx],
            'label': torch.tensor(self.labels[idx], dtype=torch.long)
        }
        return item

class URLTranTrainer:
    """URLTran模型训练器 - 基于原始项目优化"""

    def __init__(self,
                 model_name: str = "bert-base-uncased",
                 max_length: int = 128,
                 batch_size: int = 32,
                 learning_rate: float = 2e-5,
                 num_epochs: int = 3,
                 device: Optional[str] = None):

        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 初始化tokenizer和模型
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = self._initialize_model()

        logger.info(f"URLTranTrainer initialized on device: {self.device}")

    def _initialize_model(self):
        """初始化URLTran模型"""
        config = AutoConfig.from_pretrained(self.model_name)
        config.num_labels = 2
        config.problem_type = "single_label_classification"

        model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            config=config
        )
        model.to(self.device)

        return model

    def prepare_data(self, data_path: str) -> Tuple[DataLoader, DataLoader]:
        """准备训练和验证数据"""
        logger.info(f"Loading data from {data_path}")

        # 读取数据
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        elif data_path.endswith('.json'):
            df = pd.read_json(data_path)
        else:
            raise ValueError("Unsupported data format. Use CSV or JSON.")

        # 检查数据列
        if 'url' not in df.columns or 'label' not in df.columns:
            raise ValueError("Data must contain 'url' and 'label' columns")

        # 清理数据
        df = df.dropna(subset=['url', 'label'])
        df['label'] = df['label'].astype(int)

        # 分割数据
        train_df, val_df = train_test_split(
            df, test_size=0.2, random_state=42, stratify=df['label']
        )

        logger.info(f"Training samples: {len(train_df)}, Validation samples: {len(val_df)}")

        # 创建数据集
        train_dataset = URLTranDataset(
            train_df['url'].tolist(),
            train_df['label'].tolist(),
            self.tokenizer,
            self.max_length
        )

        val_dataset = URLTranDataset(
            val_df['url'].tolist(),
            val_df['label'].tolist(),
            self.tokenizer,
            self.max_length
        )

        # 创建数据加载器
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False
        )

        return train_loader, val_loader

    def train(self, train_loader: DataLoader, val_loader: DataLoader, output_dir: str):
        """训练模型"""
        logger.info("Starting training...")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 优化器和学习率调度器
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate)
        total_steps = len(train_loader) * self.num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=int(0.1 * total_steps),
            num_training_steps=total_steps
        )

        best_f1 = 0.0
        training_history = []

        for epoch in range(self.num_epochs):
            logger.info(f"Epoch {epoch + 1}/{self.num_epochs}")

            # 训练阶段
            train_loss = self._train_epoch(train_loader, optimizer, scheduler)

            # 验证阶段
            val_accuracy, val_f1, val_report = self._validate_epoch(val_loader)

            # 记录训练历史
            epoch_history = {
                'epoch': epoch + 1,
                'train_loss': train_loss,
                'val_accuracy': val_accuracy,
                'val_f1': val_f1,
                'val_report': val_report
            }
            training_history.append(epoch_history)

            logger.info(f"Train Loss: {train_loss:.4f}")
            logger.info(f"Val Accuracy: {val_accuracy:.4f}")
            logger.info(f"Val F1: {val_f1:.4f}")

            # 保存最佳模型
            if val_f1 > best_f1:
                best_f1 = val_f1
                self._save_model(output_dir, f"best_model")
                logger.info(f"New best model saved with F1: {best_f1:.4f}")

            # 保存checkpoint
            self._save_model(output_dir, f"checkpoint_epoch_{epoch + 1}")

        # 保存训练历史
        self._save_training_history(training_history, output_dir)

        logger.info("Training completed!")
        return training_history

    def _train_epoch(self, train_loader: DataLoader, optimizer, scheduler) -> float:
        """训练一个epoch"""
        self.model.train()
        total_loss = 0.0

        for batch_idx, batch in enumerate(train_loader):
            optimizer.zero_grad()

            # 移动数据到设备
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['label'].to(self.device)

            # 前向传播
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss
            total_loss += loss.item()

            # 反向传播
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            if (batch_idx + 1) % 100 == 0:
                logger.info(f"Batch {batch_idx + 1}/{len(train_loader)}, Loss: {loss.item():.4f}")

        return total_loss / len(train_loader)

    def _validate_epoch(self, val_loader: DataLoader) -> Tuple[float, float, Dict]:
        """验证一个epoch"""
        self.model.eval()
        predictions = []
        true_labels = []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )

                logits = outputs.logits
                preds = torch.argmax(logits, dim=1)

                predictions.extend(preds.cpu().numpy())
                true_labels.extend(labels.cpu().numpy())

        # 计算指标
        accuracy = accuracy_score(true_labels, predictions)
        f1 = f1_score(true_labels, predictions, average='weighted')
        report = classification_report(true_labels, predictions, output_dict=True)

        return accuracy, f1, report

    def _save_model(self, output_dir: str, model_name: str):
        """保存模型"""
        model_path = os.path.join(output_dir, model_name)
        self.model.save_pretrained(model_path)
        self.tokenizer.save_pretrained(model_path)

        # 保存配置
        config = {
            'model_name': self.model_name,
            'max_length': self.max_length,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'num_epochs': self.num_epochs,
            'device': str(self.device)
        }

        with open(os.path.join(model_path, 'training_config.json'), 'w') as f:
            json.dump(config, f, indent=2)

    def _save_training_history(self, history: List[Dict], output_dir: str):
        """保存训练历史"""
        with open(os.path.join(output_dir, 'training_history.json'), 'w') as f:
            json.dump(history, f, indent=2)

class URLTranDeployer:
    """URLTran模型部署器"""

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = self._load_config()

        self._load_model()

    def _load_config(self) -> Dict:
        """加载模型配置"""
        config_path = os.path.join(self.model_path, 'training_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {
                'model_name': 'bert-base-uncased',
                'max_length': 128,
                'device': str(self.device)
            }

    def _load_model(self):
        """加载训练好的模型"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"URLTran model loaded successfully from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def predict(self, url: str) -> Dict:
        """预测URL是否为钓鱼网站"""
        # 预处理URL
        processed_url = self._preprocess_url(url)

        # 编码
        inputs = self.tokenizer(
            processed_url,
            truncation=True,
            padding=True,
            max_length=self.config.get('max_length', 128),
            return_tensors="pt"
        )

        # 移动到设备
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 预测
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=1)

            confidence = probabilities[0][1].item()  # 钓鱼网站概率
            prediction = int(confidence >= 0.5)

        return {
            'url': url,
            'prediction': prediction,  # 0=正常, 1=钓鱼
            'confidence': confidence,
            'is_phishing': prediction == 1
        }

    def _preprocess_url(self, url: str) -> str:
        """预处理URL"""
        import re

        url = str(url).strip().lower()
        url = url.replace('https://', '').replace('http://', '')
        url = re.sub(r'[^\w\s\-\.\/\:]', ' ', url)
        url = re.sub(r'[\/\.\:]+', ' / ', url)
        url = re.sub(r'\s+', ' ', url).strip()

        return url

def create_sample_data(output_path: str, num_samples: int = 1000):
    """创建示例训练数据"""
    logger.info(f"Creating sample data with {num_samples} samples...")

    # 示例钓鱼URL（基于我们收集的真实数据）
    phishing_urls = [
        "http://tre-zorbridge-secure.pages.dev/",
        "http://interbank-benefits-creditos-digitales.savvysalon.com/",
        "https://mycomoxvalley.ca/wp-includes/css/ca1/form17.html?partner=Scotiabank",
        "http://secure-trezor-i-get.typedream.app/",
        "http://secure-io-start.pages.dev/",
        "http://www.facebook-alerts.blogspot.com.ng/",
        "https://store.workshopmodsreview.com/sharedfiles/filesdetails/aug_poseidon/",
        "http://amazon-clone-6hsy.vercel.app/",
        "http://ledgerdevsupport.firebaseapp.com/",
        "http://customer-support-system-client-contact-desk.pages.dev/appeal_form"
    ]

    # 示例正常URL
    legitimate_urls = [
        "https://github.com/microsoft/vscode/blob/main/README.md",
        "https://stackoverflow.com/questions/12345678/how-to-solve-this-problem",
        "https://www.bbc.com/news/world-asia-china-67890123",
        "https://www.wikipedia.org/wiki/Computer_science",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "https://www.python.org/downloads/",
        "https://www.reddit.com/r/programming/",
        "https://medium.com/topic/technology",
        "https://news.ycombinator.com/",
        "https://www.coursera.org/learn/python"
    ]

    # 生成更多样本
    all_urls = []
    labels = []

    for i in range(num_samples):
        if i % 2 == 0:  # 钓鱼URL
            base_url = phishing_urls[i % len(phishing_urls)]
            # 添加一些变化
            variation = f"_var{i//len(phishing_urls)}"
            url = base_url.replace('/', f'{variation}/')
            label = 1
        else:  # 正常URL
            base_url = legitimate_urls[i % len(legitimate_urls)]
            url = base_url
            label = 0

        all_urls.append(url)
        labels.append(label)

    # 创建DataFrame
    df = pd.DataFrame({
        'url': all_urls,
        'label': labels
    })

    # 保存数据
    df.to_csv(output_path, index=False)
    logger.info(f"Sample data saved to {output_path}")

    return output_path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="URLTran Model Training and Deployment")
    parser.add_argument("--mode", choices=["train", "predict", "create_data"], default="train")
    parser.add_argument("--data_path", type=str, help="Path to training data")
    parser.add_argument("--output_dir", type=str, default="./urltran_model", help="Output directory")
    parser.add_argument("--url", type=str, help="URL to predict")
    parser.add_argument("--model_path", type=str, help="Path to trained model")
    parser.add_argument("--num_samples", type=int, default=1000, help="Number of samples for synthetic data")

    args = parser.parse_args()

    if args.mode == "create_data":
        create_sample_data(args.data_path or "sample_data.csv", args.num_samples)
        return

    elif args.mode == "train":
        # 准备数据
        if not args.data_path:
            args.data_path = "sample_data.csv"
            if not os.path.exists(args.data_path):
                create_sample_data(args.data_path, args.num_samples)

        # 创建训练器
        trainer = URLTranTrainer(
            model_name="bert-base-uncased",
            max_length=128,
            batch_size=32,
            learning_rate=2e-5,
            num_epochs=3
        )

        # 准备数据
        train_loader, val_loader = trainer.prepare_data(args.data_path)

        # 训练模型
        training_history = trainer.train(train_loader, val_loader, args.output_dir)

        logger.info("Training completed successfully!")

    elif args.mode == "predict":
        if not args.model_path or not args.url:
            logger.error("Model path and URL are required for prediction")
            return

        # 创建部署器
        deployer = URLTranDeployer(args.model_path)

        # 预测
        result = deployer.predict(args.url)

        print(f"URL: {result['url']}")
        print(f"Prediction: {'Phishing' if result['is_phishing'] else 'Legitimate'}")
        print(f"Confidence: {result['confidence']:.4f}")

if __name__ == "__main__":
    import argparse
    main()