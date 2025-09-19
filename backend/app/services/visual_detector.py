"""
视觉钓鱼检测服务
基于屏幕截图和视觉相似性分析检测钓鱼网站
"""

import asyncio
import base64
import io
import os
import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import cv2
import torch
import torchvision.transforms as transforms
from PIL import Image
from playwright.async_api import async_playwright
import hashlib

class VisualPhishDetector:
    """视觉钓鱼检测器"""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_feature_extractor()
        self.known_targets = {}  # 存储已知目标网站的特征
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def _load_feature_extractor(self):
        """加载特征提取模型"""
        # 使用预训练的ResNet作为特征提取器
        import torchvision.models as models
        model = models.resnet50(pretrained=True)
        model.eval()
        model = model.to(self.device)
        # 移除最后的分类层
        model = torch.nn.Sequential(*(list(model.children())[:-1]))
        return model

    def _extract_features(self, image_path: str) -> Optional[np.ndarray]:
        """从图像中提取特征向量"""
        try:
            # 图像预处理
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])

            # 加载图像
            image = Image.open(image_path).convert('RGB')
            image_tensor = transform(image).unsqueeze(0).to(self.device)

            # 提取特征
            with torch.no_grad():
                features = self.model(image_tensor)
                features = features.squeeze().cpu().numpy()

            return features

        except Exception as e:
            print(f"特征提取失败: {e}")
            return None

    def _calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """计算特征向量之间的余弦相似度"""
        similarity = np.dot(features1, features2) / (np.linalg.norm(features1) * np.linalg.norm(features2))
        return float(similarity)

    async def _take_screenshot(self, url: str, timeout: int = 30000) -> Optional[str]:
        """对网站进行截图"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                # 设置视窗大小
                await page.set_viewport_size({"width": 1280, "height": 720})

                # 导航到URL
                await page.goto(url, timeout=timeout, wait_until="networkidle")

                # 等待页面加载完成
                await page.wait_for_timeout(3000)

                # 生成文件名
                url_hash = hashlib.md5(url.encode()).hexdigest()
                screenshot_path = os.path.join(self.screenshot_dir, f"{url_hash}.png")

                # 截图
                await page.screenshot(path=screenshot_path, full_page=True)

                await browser.close()
                return screenshot_path

        except Exception as e:
            print(f"截图失败 {url}: {e}")
            return None

    def _detect_visual_similarity(self, target_features: np.ndarray,
                                 known_features: np.ndarray, threshold: float = 0.85) -> Dict:
        """检测视觉相似性"""
        similarity = self._calculate_similarity(target_features, known_features)

        is_phishing = similarity >= threshold

        return {
            "is_phishing": is_phishing,
            "similarity_score": similarity,
            "confidence": similarity,
            "threshold": threshold
        }

    async def add_known_target(self, url: str, name: str) -> bool:
        """添加已知目标网站"""
        try:
            print(f"正在添加目标网站: {name} ({url})")

            # 截图
            screenshot_path = await self._take_screenshot(url)
            if not screenshot_path:
                return False

            # 提取特征
            features = self._extract_features(screenshot_path)
            if features is None:
                return False

            # 存储特征
            self.known_targets[name] = {
                "url": url,
                "screenshot_path": screenshot_path,
                "features": features,
                "added_at": time.time()
            }

            print(f"✅ 成功添加目标网站: {name}")
            return True

        except Exception as e:
            print(f"添加目标网站失败: {e}")
            return False

    async def detect_phishing(self, url: str, compare_targets: List[str] = None) -> Dict:
        """检测网站是否为钓鱼网站"""
        try:
            start_time = time.time()

            # 如果没有指定比较目标，使用所有已知目标
            if compare_targets is None:
                compare_targets = list(self.known_targets.keys())

            if not compare_targets:
                return {
                    "is_phishing": False,
                    "confidence": 0.0,
                    "message": "没有已知目标网站进行比较",
                    "details": {}
                }

            # 对目标网站截图
            screenshot_path = await self._take_screenshot(url)
            if not screenshot_path:
                return {
                    "is_phishing": False,
                    "confidence": 0.0,
                    "message": "无法获取网站截图",
                    "details": {}
                }

            # 提取目标网站特征
            target_features = self._extract_features(screenshot_path)
            if target_features is None:
                return {
                    "is_phishing": False,
                    "confidence": 0.0,
                    "message": "特征提取失败",
                    "details": {}
                }

            # 与每个已知目标进行比较
            results = {}
            max_similarity = 0.0
            best_match = None

            for target_name in compare_targets:
                if target_name in self.known_targets:
                    known_target = self.known_targets[target_name]
                    known_features = known_target["features"]

                    # 检测相似性
                    result = self._detect_visual_similarity(target_features, known_features)
                    results[target_name] = result

                    if result["similarity_score"] > max_similarity:
                        max_similarity = result["similarity_score"]
                        best_match = target_name

            # 判断是否为钓鱼网站
            is_phishing = max_similarity >= 0.85

            processing_time = time.time() - start_time

            return {
                "is_phishing": is_phishing,
                "confidence": max_similarity,
                "processing_time": processing_time,
                "best_match": best_match,
                "similarity_threshold": 0.85,
                "screenshot_path": screenshot_path,
                "comparison_results": results,
                "message": f"检测完成，与 {best_match} 相似度最高" if best_match else "未找到相似的目标网站"
            }

        except Exception as e:
            return {
                "is_phishing": False,
                "confidence": 0.0,
                "message": f"检测过程出错: {str(e)}",
                "details": {}
            }

    def get_known_targets(self) -> List[Dict]:
        """获取所有已知目标网站"""
        return [
            {
                "name": name,
                "url": data["url"],
                "added_at": data["added_at"]
            }
            for name, data in self.known_targets.items()
        ]

    def remove_target(self, name: str) -> bool:
        """移除目标网站"""
        try:
            if name in self.known_targets:
                target_data = self.known_targets[name]

                # 删除截图文件
                if os.path.exists(target_data["screenshot_path"]):
                    os.remove(target_data["screenshot_path"])

                # 从字典中移除
                del self.known_targets[name]

                print(f"✅ 已移除目标网站: {name}")
                return True
            else:
                print(f"❌ 目标网站不存在: {name}")
                return False

        except Exception as e:
            print(f"移除目标网站失败: {e}")
            return False

# 全局实例
visual_detector = VisualPhishDetector()

# 初始化一些常见的目标网站
async def initialize_targets():
    """初始化常见的目标网站"""
    print("🎯 正在初始化目标网站...")

    # 钓鱼网站常用伪装目标（包括银行、支付、社交、邮箱等）
    common_targets = [
        # 国际银行和支付
        ("https://www.paypal.com", "PayPal"),
        ("https://www.icbc.com.cn", "中国工商银行"),
        ("https://www.alipay.com", "支付宝"),
        ("https://www.bankofamerica.com", "Bank of America"),
        ("https://www.chase.com", "Chase Bank"),
        ("https://www.wellsfargo.com", "Wells Fargo"),
        ("https://www.citibank.com", "Citi Bank"),
        ("https://www.hsbc.com", "HSBC"),

        # 中国主要银行
        ("https://www.boc.cn", "中国银行"),
        ("https://www.ccb.com", "中国建设银行"),
        ("https://www.abchina.com", "中国农业银行"),
        ("https://www.cmbchina.com", "招商银行"),

        # 社交媒体
        ("https://www.facebook.com", "Facebook"),
        ("https://www.instagram.com", "Instagram"),
        ("https://www.twitter.com", "Twitter"),
        ("https://www.linkedin.com", "LinkedIn"),
        ("https://www.qq.com", "腾讯QQ"),
        ("https://weibo.com", "新浪微博"),

        # 邮箱服务
        ("https://mail.google.com", "Gmail"),
        ("https://outlook.live.com", "Outlook"),
        ("https://mail.yahoo.com", "Yahoo Mail"),
        ("https://mail.163.com", "网易邮箱"),
        ("https://mail.qq.com", "QQ邮箱"),

        # 电商平台
        ("https://www.amazon.com", "Amazon"),
        ("https://www.taobao.com", "淘宝"),
        ("https://www.jd.com", "京东"),
        ("https://www.ebay.com", "eBay"),

        # 科技公司
        ("https://www.google.com", "Google"),
        ("https://www.microsoft.com", "Microsoft"),
        ("https://www.apple.com", "Apple"),
        ("https://github.com", "GitHub"),

        # 其他常用服务
        ("https://www.netflix.com", "Netflix"),
        ("https://www.spotify.com", "Spotify"),
        ("https://www.dropbox.com", "Dropbox"),
    ]

    added_count = 0
    for url, name in common_targets:
        try:
            success = await visual_detector.add_known_target(url, name)
            if success:
                added_count += 1
                print(f"✅ 已添加目标: {name}")
            else:
                print(f"❌ 添加目标失败: {name}")

            # 添加延迟避免过于频繁的请求
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ 添加目标异常: {name} - {e}")

    print(f"🎯 目标网站初始化完成，共添加 {added_count} 个目标")