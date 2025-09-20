"""
openSquat检测模型包装器
基于同形字符和域名相似度的钓鱼网站检测
"""

import threading
from typing import Optional
from ..opensquat_detector import opensquat_detector

class OpenSquatWrapper:
    """openSquat检测模型包装器"""

    def __init__(self):
        self.name = "opensquat"
        self.description = "基于同形字符和域名相似度的钓鱼网站检测"
        self.version = "1.0.0"
        self.enabled = True

    def predict_proba(self, url: str) -> Optional[float]:
        """
        预测URL的钓鱼概率

        Args:
            url: 要检测的URL

        Returns:
            钓鱼概率 (0.0-1.0)，如果检测失败返回None
        """
        try:
            # 检查检测器是否可用
            if not opensquat_detector.is_available():
                print("⚠️ openSquat检测器不可用")
                return None

            # 执行域名分析
            result = opensquat_detector.analyze_domain(url)

            # 检查结果
            if result.is_suspicious:
                confidence = result.confidence
                # 确保置信度在0-1范围内
                return max(0.0, min(1.0, confidence))
            else:
                # 如果没有明确标记为可疑，但有一些风险特征，返回较低的置信度
                if result.suspicious_features or result.homoglyph_issues:
                    return min(0.3, result.confidence)
                else:
                    return 0.0

        except Exception as e:
            print(f"openSquat检测失败 {url}: {e}")
            return None

    def get_detailed_analysis(self, url: str) -> Optional[dict]:
        """
        获取详细的分析结果

        Args:
            url: 要分析的URL

        Returns:
            详细分析结果字典
        """
        try:
            if not opensquat_detector.is_available():
                return None

            result = opensquat_detector.analyze_domain(url)
            return {
                "domain": result.domain,
                "is_suspicious": result.is_suspicious,
                "confidence": result.confidence,
                "suspicious_features": result.suspicious_features,
                "similar_domains": result.similar_domains,
                "homoglyph_issues": result.homoglyph_issues,
                "risk_factors": result.risk_factors,
                "target_domains_count": len(opensquat_detector.get_target_domains())
            }

        except Exception as e:
            print(f"详细分析失败 {url}: {e}")
            return None

    def get_info(self) -> dict:
        """获取模型信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "domain_similarity",
            "enabled": self.enabled,
            "available": opensquat_detector.is_available(),
            "target_domains_count": len(opensquat_detector.get_target_domains()),
            "features": [
                "同形字符检测",
                "域名相似度计算",
                "域名结构分析",
                "特殊字符检测"
            ]
        }

    def add_target_domain(self, domain: str) -> bool:
        """添加目标域名"""
        return opensquat_detector.add_target_domain(domain)

    def remove_target_domain(self, domain: str) -> bool:
        """移除目标域名"""
        return opensquat_detector.remove_target_domain(domain)

    def get_target_domains(self) -> list:
        """获取目标域名列表"""
        return opensquat_detector.get_target_domains()

    def toggle_detection(self, enabled: bool):
        """启用/禁用检测"""
        self.enabled = enabled