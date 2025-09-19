"""
视觉检测模型源
"""

import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging
from .visual_detector import visual_detector

logger = logging.getLogger(__name__)

class VisualModelSource:
    """视觉检测模型源"""

    def __init__(self):
        self.name = "visual_detection"
        self.description = "基于视觉相似性的钓鱼网站检测"
        self.version = "1.0.0"
        self.enabled = True

    def is_available(self) -> bool:
        """检查模型是否可用"""
        try:
            # 检查是否有所需的依赖
            import torch
            import cv2
            from PIL import Image
            return True
        except ImportError:
            logger.warning("视觉检测模型依赖不可用")
            return False

    async def check_urls(self, urls: List[str], threshold: float = 0.85) -> Dict[str, Any]:
        """
        检测URL列表是否为钓鱼网站

        Args:
            urls: 要检测的URL列表
            threshold: 相似度阈值

        Returns:
            检测结果字典
        """
        if not self.is_available():
            return {
                "error": "视觉检测模型不可用",
                "results": {}
            }

        if not urls:
            return {
                "error": "没有提供URL",
                "results": {}
            }

        results = {}

        try:
            # 对每个URL进行视觉检测
            for url in urls:
                try:
                    # 规范化URL
                    normalized_url = self._normalize_url(url)
                    if not normalized_url:
                        results[url] = {
                            "is_phishing": False,
                            "confidence": 0.0,
                            "error": "无效的URL"
                        }
                        continue

                    # 进行视觉检测
                    detection_result = await visual_detector.detect_phishing(normalized_url)

                    # 构建结果
                    results[url] = {
                        "is_phishing": detection_result["is_phishing"],
                        "confidence": detection_result["confidence"],
                        "message": detection_result["message"],
                        "details": {
                            "best_match": detection_result.get("best_match"),
                            "processing_time": detection_result.get("processing_time"),
                            "similarity_threshold": threshold,
                            "comparison_results": detection_result.get("comparison_results", {})
                        }
                    }

                    # 添加延迟避免过于频繁的请求
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"检测URL失败 {url}: {e}")
                    results[url] = {
                        "is_phishing": False,
                        "confidence": 0.0,
                        "error": str(e)
                    }

            return {
                "source": self.name,
                "version": self.version,
                "results": results,
                "total_urls": len(urls),
                "threshold": threshold
            }

        except Exception as e:
            logger.error(f"视觉检测失败: {e}")
            return {
                "error": f"视觉检测失败: {str(e)}",
                "results": {}
            }

    def _normalize_url(self, url: str) -> Optional[str]:
        """规范化URL"""
        try:
            if not url or not url.strip():
                return None

            # 移除首尾空格
            url = url.strip()

            # 如果没有协议，添加https://
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # 解析URL
            parsed = urlparse(url)

            # 构建规范化URL
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"

            return normalized

        except Exception:
            return None

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "available": self.is_available(),
            "known_targets_count": len(visual_detector.known_targets),
            "device": str(visual_detector.device) if hasattr(visual_detector, 'device') else "unknown"
        }

    async def add_target(self, url: str, name: str) -> Dict[str, Any]:
        """添加目标网站"""
        try:
            success = await visual_detector.add_known_target(url, name)
            return {
                "success": success,
                "message": f"目标网站 {name} 添加成功" if success else f"目标网站 {name} 添加失败"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"添加目标网站失败: {str(e)}"
            }

    async def remove_target(self, name: str) -> Dict[str, Any]:
        """移除目标网站"""
        try:
            success = visual_detector.remove_target(name)
            return {
                "success": success,
                "message": f"目标网站 {name} 移除成功" if success else f"目标网站 {name} 移除失败"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"移除目标网站失败: {str(e)}"
            }

    async def get_targets(self) -> Dict[str, Any]:
        """获取所有目标网站"""
        try:
            targets = visual_detector.get_known_targets()
            return {
                "success": True,
                "targets": targets,
                "count": len(targets)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取目标网站失败: {str(e)}",
                "targets": [],
                "count": 0
            }

    async def initialize_system(self) -> Dict[str, Any]:
        """初始化系统（添加常见目标网站）"""
        try:
            from .visual_detector import initialize_targets
            # 创建后台任务初始化目标网站
            asyncio.create_task(initialize_targets())
            return {
                "success": True,
                "message": "系统初始化已启动，正在添加常见目标网站..."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"系统初始化失败: {str(e)}"
            }

# 创建全局实例
visual_model_source = VisualModelSource()