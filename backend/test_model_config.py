#!/usr/bin/env python3
"""
测试模型配置系统和热装配功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.model_config_manager import get_model_manager
from app.services.model_registry import ModelRegistry
import time

def test_model_config_manager():
    """测试模型配置管理器"""
    print("=== 测试模型配置管理器 ===")

    # 获取模型管理器
    manager = get_model_manager()

    # 健康检查
    health = manager.health_check()
    print(f"系统健康状态: {health}")

    # 列出模型
    models = manager.list_models()
    print(f"可用模型: {list(models.keys())}")

    # 列出规则
    rules = manager.list_rules()
    print(f"可用规则: {list(rules.keys())}")

    # 获取聚合配置
    agg_config = manager.get_aggregation_config()
    print(f"默认聚合策略: {agg_config.get('default_strategy')}")

    # 测试预测
    test_url = "https://example.com/login"
    model_names = list(models.keys())[:2]  # 测试前两个模型

    if model_names:
        print(f"\n测试URL: {test_url}")
        results = manager.predict_with_models(test_url, model_names)
        for model_name, result in results.items():
            print(f"{model_name}: {result}")

    return manager

def test_model_registry():
    """测试模型注册表"""
    print("\n=== 测试模型注册表 ===")

    registry = ModelRegistry()

    # 健康检查
    health = registry.health_check()
    print(f"注册表健康状态: {health}")

    # 列出模型
    models = registry.list_models()
    print(f"注册表模型: {list(models.keys())}")

    # 测试预测
    test_url = "https://可疑网站.com/login"
    model_names = list(models.keys())[:2]

    if model_names:
        print(f"\n测试URL: {test_url}")
        results = registry.predict_all(test_url, model_names)
        for model_name, result in results.items():
            print(f"{model_name}: {result}")

def test_urltran_enhanced():
    """测试增强的URLTran"""
    print("\n=== 测试增强的URLTran ===")

    try:
        from app.services.detectors.urltran_wrapper import URLTranWrapper

        # 创建URLTran实例
        urltran = URLTranWrapper()

        # 测试URL
        test_urls = [
            "https://google.com",
            "http://192.168.1.1/login",
            "https://bit.ly/suspicious",
            "http://可疑钓鱼网站.com/secure/login",
            "https:// legitimate-site.com/path/to/page"
        ]

        for url in test_urls:
            try:
                proba = urltran.predict_proba(url)
                analysis = urltran.get_feature_analysis(url)
                print(f"\nURL: {url}")
                print(f"钓鱼概率: {proba:.3f}")
                print(f"风险因素: {analysis['risk_factors']}")
            except Exception as e:
                print(f"URL {url} 检测失败: {e}")

    except Exception as e:
        print(f"URLTran测试失败: {e}")

def test_config_hot_reload():
    """测试配置热重载"""
    print("\n=== 测试配置热重载 ===")

    manager = get_model_manager()

    # 获取当前配置
    before_models = manager.list_models()
    print(f"重载前模型数量: {len(before_models)}")

    # 模拟配置文件修改
    config_path = manager.config_path
    if os.path.exists(config_path):
        print(f"配置文件路径: {config_path}")
        print("请手动修改配置文件，观察热重载效果...")
        print("按 Ctrl+C 停止监控")

        try:
            # 监控一段时间
            for i in range(30):  # 30秒
                time.sleep(1)
                if i % 5 == 0:
                    health = manager.health_check()
                    print(f"[{i}s] 配置监控状态: {health}")
        except KeyboardInterrupt:
            print("\n停止监控")

    # 重新加载配置
    manager.reload_config()
    after_models = manager.list_models()
    print(f"重载后模型数量: {len(after_models)}")

def main():
    """主测试函数"""
    print("开始测试模型配置系统...")

    try:
        # 测试1: 模型配置管理器
        manager = test_model_config_manager()

        # 测试2: 模型注册表
        test_model_registry()

        # 测试3: 增强的URLTran
        test_urltran_enhanced()

        # 测试4: 配置热重载（可选）
        # test_config_hot_reload()

        print("\n✅ 所有测试完成!")

    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        try:
            from app.services.model_config_manager import shutdown_model_manager
            shutdown_model_manager()
        except:
            pass

if __name__ == "__main__":
    main()