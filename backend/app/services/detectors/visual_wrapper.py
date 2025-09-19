"""
视觉检测模型包装器
"""

import asyncio
from typing import Optional
from ..visual_model_source import visual_model_source

class VisualDetectionWrapper:
    """视觉检测模型包装器"""

    def __init__(self):
        self.name = "phishpedia"
        self.description = "基于视觉相似性的钓鱼网站检测"
        self.version = "1.0.0"

    def predict_proba(self, url: str) -> Optional[float]:
        """
        预测URL的钓鱼概率

        Args:
            url: 要检测的URL

        Returns:
            钓鱼概率 (0.0-1.0)，如果检测失败返回None
        """
        try:
            # 运行异步检测
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 执行视觉检测
                result = loop.run_until_complete(
                    visual_model_source.check_urls([url])
                )

                # 检查结果
                if "results" in result and url in result["results"]:
                    url_result = result["results"][url]
                    if "confidence" in url_result:
                        confidence = url_result["confidence"]
                        # 确保置信度在0-1范围内
                        return max(0.0, min(1.0, confidence))

            finally:
                loop.close()

            return None

        except Exception as e:
            print(f"视觉检测失败 {url}: {e}")
            return None

    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "visual"
        }