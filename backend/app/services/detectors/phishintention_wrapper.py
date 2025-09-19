"""
PhishIntention检测模型包装器
结合视觉相似性和交互模式的钓鱼网站检测
"""

import asyncio
import threading
from typing import Optional
from ..interaction_detector import interaction_detector
from ..visual_detector import visual_detector

class PhishIntentionWrapper:
    """PhishIntention检测模型包装器"""

    def __init__(self):
        self.name = "phishintention"
        self.description = "基于视觉相似性和交互模式的钓鱼网站检测"
        self.version = "1.0.0"
        self.visual_enabled = True
        self.interaction_enabled = True

    def predict_proba(self, url: str) -> Optional[float]:
        """
        预测URL的钓鱼概率

        Args:
            url: 要检测的URL

        Returns:
            钓鱼概率 (0.0-1.0)，如果检测失败返回None
        """
        try:
            # 使用线程来避免事件循环冲突
            result_container = {'result': None, 'exception': None}

            def run_async_in_thread():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(self._detect_combined(url))
                        result_container['result'] = result
                    finally:
                        loop.close()
                except Exception as e:
                    result_container['exception'] = e

            # 在新线程中运行异步代码
            thread = threading.Thread(target=run_async_in_thread)
            thread.start()
            thread.join(timeout=30)  # 30秒超时

            # 检查结果
            if result_container['exception']:
                raise result_container['exception']

            if result_container['result'] and "combined_score" in result_container['result']:
                confidence = result_container['result']["combined_score"]
                # 确保置信度在0-1范围内
                return max(0.0, min(1.0, confidence))

            return None

        except Exception as e:
            print(f"PhishIntention检测失败 {url}: {e}")
            return None

    async def _detect_combined(self, url: str) -> dict:
        """
        执行组合检测（视觉 + 交互）

        Args:
            url: 要检测的URL

        Returns:
            组合检测结果
        """
        visual_result = None
        interaction_result = None
        visual_score = 0.0
        interaction_score = 0.0

        # 并行执行视觉检测和交互检测
        tasks = []

        if self.visual_enabled:
            tasks.append(self._run_visual_detection(url))

        if self.interaction_enabled:
            tasks.append(self._run_interaction_detection(url))

        # 等待所有检测完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理检测结果
        if self.visual_enabled and len(results) > 0:
            if isinstance(results[0], dict) and not isinstance(results[0], Exception):
                visual_result = results[0]
                visual_score = visual_result.get("confidence", 0.0)

        if self.interaction_enabled and len(results) > (1 if self.visual_enabled else 0):
            result_index = 1 if self.visual_enabled else 0
            if isinstance(results[result_index], dict) and not isinstance(results[result_index], Exception):
                interaction_result = results[result_index]
                interaction_score = interaction_result.get("confidence", 0.0)

        # 计算组合分数
        combined_score = self._calculate_combined_score(
            visual_score, interaction_score,
            visual_result, interaction_result
        )

        # 构建最终结果
        final_result = {
            "url": url,
            "combined_score": combined_score,
            "is_phishing": combined_score > 0.65,  # 组合检测阈值
            "visual_score": visual_score,
            "interaction_score": interaction_score,
            "visual_enabled": self.visual_enabled,
            "interaction_enabled": self.interaction_enabled,
            "detection_methods": []
        }

        # 添加检测结果详情
        if visual_result:
            final_result["visual_result"] = visual_result
            final_result["detection_methods"].append("visual_similarity")

        if interaction_result:
            final_result["interaction_result"] = interaction_result
            final_result["detection_methods"].append("interaction_pattern")

        # 添加决策信息
        final_result["decision"] = self._generate_decision(
            combined_score, visual_result, interaction_result
        )

        return final_result

    async def _run_visual_detection(self, url: str) -> dict:
        """运行视觉检测"""
        try:
            return await visual_detector.detect_phishing(url)
        except Exception as e:
            print(f"视觉检测失败: {e}")
            return {"is_phishing": False, "confidence": 0.0, "error": str(e)}

    async def _run_interaction_detection(self, url: str) -> dict:
        """运行交互检测"""
        try:
            # 获取页面HTML内容进行交互分析
            from playwright.async_api import async_playwright
            from bs4 import BeautifulSoup

            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                try:
                    # 访问页面
                    await page.goto(url, timeout=10000)

                    # 获取页面内容
                    html_content = await page.content()

                    # 执行交互分析
                    result = await interaction_detector.analyze_interaction(url, html_content)

                    return result

                except Exception as e:
                    print(f"获取页面内容失败: {e}")
                    # 如果无法获取页面内容，返回默认结果
                    return {
                        "url": url,
                        "is_phishing": False,
                        "confidence": 0.0,
                        "message": f"无法获取页面内容: {str(e)}",
                        "interaction_metrics": {},
                        "suspicious_behaviors": [],
                        "risk_factors": []
                    }

                finally:
                    await browser.close()

        except Exception as e:
            print(f"交互检测失败: {e}")
            return {
                "url": url,
                "is_phishing": False,
                "confidence": 0.0,
                "message": f"交互检测失败: {str(e)}",
                "interaction_metrics": {},
                "suspicious_behaviors": [],
                "risk_factors": []
            }

    def _calculate_combined_score(self, visual_score: float, interaction_score: float,
                                visual_result: dict, interaction_result: dict) -> float:
        """
        计算组合检测分数

        Args:
            visual_score: 视觉检测分数
            interaction_score: 交互检测分数
            visual_result: 视觉检测结果
            interaction_result: 交互检测结果

        Returns:
            组合分数 (0.0-1.0)
        """
        # 权重配置
        visual_weight = 0.6  # 视觉检测权重更高
        interaction_weight = 0.4

        # 调整权重（如果某个检测失败）
        if not visual_result or visual_score == 0.0:
            visual_weight = 0.0
            interaction_weight = 1.0

        if not interaction_result or interaction_score == 0.0:
            visual_weight = 1.0
            interaction_weight = 0.0

        # 计算基础组合分数
        combined_score = (visual_score * visual_weight + interaction_score * interaction_weight)

        # 应用调整因子
        combined_score = self._apply_adjustment_factors(
            combined_score, visual_result, interaction_result
        )

        # 确保分数在有效范围内
        return max(0.0, min(1.0, combined_score))

    def _apply_adjustment_factors(self, base_score: float, visual_result: dict,
                                interaction_result: dict) -> float:
        """
        应用调整因子来优化组合分数

        Args:
            base_score: 基础组合分数
            visual_result: 视觉检测结果
            interaction_result: 交互检测结果

        Returns:
            调整后的分数
        """
        adjusted_score = base_score

        # 如果视觉检测显示高度相似性，提高分数
        if visual_result and visual_result.get("is_phishing", False):
            if visual_result.get("confidence", 0) > 0.8:
                adjusted_score += 0.1
            elif visual_result.get("confidence", 0) > 0.9:
                adjusted_score += 0.15

        # 如果交互检测发现高风险行为，提高分数
        if interaction_result:
            high_severity_behaviors = [
                b for b in interaction_result.get("suspicious_behaviors", [])
                if b.get("severity") == "high"
            ]
            if len(high_severity_behaviors) > 2:
                adjusted_score += 0.15
            elif len(high_severity_behaviors) > 0:
                adjusted_score += 0.08

        # 如果两种检测都指向钓鱼，大幅提高分数
        if (visual_result and visual_result.get("is_phishing", False) and
            interaction_result and interaction_result.get("is_phishing", False)):
            adjusted_score += 0.2

        # 如果两种检测结果冲突，取更高分数
        if visual_result and interaction_result:
            visual_phishing = visual_result.get("is_phishing", False)
            interaction_phishing = interaction_result.get("is_phishing", False)

            if visual_phishing != interaction_phishing:
                if visual_phishing:
                    adjusted_score = max(adjusted_score, visual_result.get("confidence", 0))
                else:
                    adjusted_score = max(adjusted_score, interaction_result.get("confidence", 0))

        return min(1.0, adjusted_score)

    def _generate_decision(self, combined_score: float, visual_result: dict,
                          interaction_result: dict) -> dict:
        """
        生成检测决策信息

        Args:
            combined_score: 组合分数
            visual_result: 视觉检测结果
            interaction_result: 交互检测结果

        Returns:
            决策信息字典
        """
        decision = {
            "is_phishing": combined_score > 0.65,
            "confidence": combined_score,
            "primary_method": "combined",
            "reasoning": [],
            "recommendations": []
        }

        # 确定主要检测方法
        if visual_result and interaction_result:
            visual_confidence = visual_result.get("confidence", 0)
            interaction_confidence = interaction_result.get("confidence", 0)

            if visual_confidence > interaction_confidence:
                decision["primary_method"] = "visual_similarity"
            else:
                decision["primary_method"] = "interaction_pattern"
        elif visual_result:
            decision["primary_method"] = "visual_similarity"
        elif interaction_result:
            decision["primary_method"] = "interaction_pattern"

        # 生成推理过程
        if combined_score > 0.65:
            decision["reasoning"].append(f"组合检测分数 {combined_score:.2f} 超过阈值 0.65")

            if visual_result and visual_result.get("is_phishing", False):
                decision["reasoning"].append("视觉检测发现与已知钓鱼网站高度相似")

            if interaction_result and interaction_result.get("is_phishing", False):
                decision["reasoning"].append("交互检测发现可疑行为模式")
        else:
            decision["reasoning"].append(f"组合检测分数 {combined_score:.2f} 低于安全阈值")

        # 生成建议
        if combined_score > 0.8:
            decision["recommendations"].extend([
                "强烈建议不要访问此网站",
                "网站可能存在严重安全风险",
                "建议立即举报此网站"
            ])
        elif combined_score > 0.65:
            decision["recommendations"].extend([
                "谨慎访问此网站",
                "建议仔细检查网站的真实性",
                "不要在网站上输入敏感信息"
            ])
        elif combined_score > 0.4:
            decision["recommendations"].append("建议进一步验证网站的真实性")
        else:
            decision["recommendations"].append("网站看起来相对安全")

        return decision

    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "combined",
            "methods": ["visual_similarity", "interaction_pattern"],
            "visual_enabled": self.visual_enabled,
            "interaction_enabled": self.interaction_enabled
        }

    def toggle_visual_detection(self, enabled: bool):
        """启用/禁用视觉检测"""
        self.visual_enabled = enabled

    def toggle_interaction_detection(self, enabled: bool):
        """启用/禁用交互检测"""
        self.interaction_enabled = enabled