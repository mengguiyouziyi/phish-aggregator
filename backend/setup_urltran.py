#!/usr/bin/env python3
"""
URLTran快速设置脚本
一键下载预训练模型并设置URLTran
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """安装必要的依赖"""
    print("🔧 安装依赖...")

    dependencies = [
        "torch",
        "transformers",
        "pandas",
        "numpy",
        "scikit-learn",
        "tqdm"
    ]

    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {dep} 安装失败")

def download_pretrained_model():
    """下载预训练的BERT模型"""
    print("📥 下载预训练BERT模型...")

    model_dir = Path("data/models/urltran/URLTran-BERT")
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        from transformers import BertTokenizer, AutoModelForSequenceClassification

        # 下载并保存tokenizer和模型
        tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        model = AutoModelForSequenceClassification.from_pretrained(
            "bert-base-uncased",
            num_labels=2,
            problem_type="single_label_classification"
        )

        # 保存到指定目录
        tokenizer.save_pretrained(model_dir)
        model.save_pretrained(model_dir)

        print(f"✅ 模型已保存到 {model_dir}")
        return True

    except Exception as e:
        print(f"❌ 下载模型失败: {e}")
        return False

def create_training_data():
    """创建训练数据"""
    print("📊 创建训练数据...")

    try:
        # 使用之前创建的脚本生成数据
        from urltran_assembler import create_sample_data

        data_path = "data/urltran_training_data.csv"
        create_sample_data(data_path, num_samples=2000)

        print(f"✅ 训练数据已创建: {data_path}")
        return data_path

    except Exception as e:
        print(f"❌ 创建训练数据失败: {e}")
        return None

def quick_train():
    """快速训练URLTran模型"""
    print("🚀 开始快速训练...")

    try:
        from urltran_assembler import URLTranTrainer

        # 创建训练器
        trainer = URLTranTrainer(
            model_name="bert-base-uncased",
            max_length=128,
            batch_size=16,  # 减小batch size以适应内存
            learning_rate=2e-5,
            num_epochs=1  # 快速训练，只训练1个epoch
        )

        # 准备数据
        data_path = "data/urltran_training_data.csv"
        if not os.path.exists(data_path):
            data_path = create_training_data()

        train_loader, val_loader = trainer.prepare_data(data_path)

        # 训练模型
        output_dir = "data/models/urltran/trained_model"
        training_history = trainer.train(train_loader, val_loader, output_dir)

        print(f"✅ 模型训练完成，保存到: {output_dir}")
        return output_dir

    except Exception as e:
        print(f"❌ 训练失败: {e}")
        return None

def update_config():
    """更新模型配置文件"""
    print("⚙️ 更新配置文件...")

    config_path = "app/config/models.json"
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False

    try:
        import json

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 更新URLTran配置
        if 'urltran' in config.get('models', {}):
            config['models']['urltran']['enabled'] = True
            config['models']['urltran']['config']['model_path'] = "data/models/urltan/trained_model/best_model"
            print("✅ URLTran配置已更新")
        else:
            print("❌ 配置文件中找不到URLTran配置")
            return False

        # 保存更新后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"❌ 更新配置失败: {e}")
        return False

def test_urltran():
    """测试URLTran模型"""
    print("🧪 测试URLTran模型...")

    try:
        from app.services.detectors.urltran_wrapper import URLTranWrapper

        # 创建URLTran实例
        detector = URLTranWrapper(model_path="data/models/urltran/trained_model/best_model")

        # 测试URL
        test_urls = [
            "https://google.com",
            "http://tre-zorbridge-secure.pages.dev/",
            "https://github.com/microsoft/vscode"
        ]

        print("测试结果:")
        for url in test_urls:
            try:
                proba = detector.predict_proba(url)
                prediction = "钓鱼网站" if proba > 0.5 else "正常网站"
                print(f"  {url}: {prediction} (置信度: {proba:.4f})")
            except Exception as e:
                print(f"  {url}: 检测失败 - {e}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 URLTran快速设置脚本")
    print("=" * 50)

    # 步骤1: 安装依赖
    install_dependencies()

    # 步骤2: 下载预训练模型
    if download_pretrained_model():
        print("✅ 预训练模型准备完成")
    else:
        print("❌ 预训练模型准备失败")
        return

    # 步骤3: 创建训练数据
    data_path = create_training_data()
    if not data_path:
        print("❌ 训练数据准备失败")
        return

    # 步骤4: 快速训练
    model_path = quick_train()
    if not model_path:
        print("❌ 模型训练失败")
        return

    # 步骤5: 更新配置
    if update_config():
        print("✅ 配置更新完成")
    else:
        print("❌ 配置更新失败")
        return

    # 步骤6: 测试模型
    if test_urltan():
        print("✅ 模型测试通过")
    else:
        print("❌ 模型测试失败")
        return

    print("\n🎉 URLTran设置完成!")
    print("现在可以在系统中使用URLTran模型进行钓鱼网站检测了。")
    print(f"模型路径: {model_path}")

if __name__ == "__main__":
    main()