"""
openSquat同形/近似域检测服务
基于同形字符和字符串相似度的钓鱼域名检测
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import idna
from dataclasses import dataclass
import string

# 导入相关库
try:
    from confusable_homoglyphs.confusables import is_confusable
    from strsimpy.normalized_levenshtein import NormalizedLevenshtein
    from homoglyphs import Homoglyphs
    OPENSQUAT_AVAILABLE = True
except ImportError:
    OPENSQUAT_AVAILABLE = False
    print("⚠️ openSquat相关库未完全安装，同形检测功能将受限")

logger = logging.getLogger(__name__)

@dataclass
class DomainAnalysisResult:
    """域名分析结果"""
    domain: str
    is_suspicious: bool
    confidence: float
    suspicious_features: List[str]
    similar_domains: List[Dict[str, Any]]
    homoglyph_issues: List[Dict[str, Any]]
    risk_factors: List[str]

class OpenSquatDetector:
    """openSquat同形/近似域检测器"""

    def __init__(self):
        self.name = "opensquat"
        self.description = "基于同形字符和字符串相似度的钓鱼域名检测"
        self.version = "1.0.0"
        self.enabled = OPENSQUAT_AVAILABLE

        # 常见的钓鱼目标域名（银行、支付、社交等）
        self.target_domains = [
            # 国际银行和支付
            "paypal.com", "paypal.com", "bankofamerica.com", "chase.com",
            "wellsfargo.com", "citibank.com", "hsbc.com", "barclays.com",
            "mastercard.com", "visa.com", "amex.com", "stripe.com",

            # 中国银行
            "icbc.com.cn", "boc.cn", "ccb.com", "abchina.com", "cmbchina.com",
            "spdb.com.cn", "cib.com.cn", "cgbchina.com.cn", "hxb.com.cn",

            # 支付平台
            "alipay.com", "wechat.com", "unionpay.com", "quickpay.com",

            # 社交媒体
            "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
            "qq.com", "weibo.com", "tiktok.com", "youtube.com",

            # 邮箱服务
            "gmail.com", "outlook.com", "yahoo.com", "hotmail.com",
            "163.com", "126.com", "qq.com", "sina.com",

            # 电商平台
            "amazon.com", "taobao.com", "jd.com", "ebay.com",
            "aliexpress.com", "walmart.com", "target.com",

            # 科技公司
            "google.com", "microsoft.com", "apple.com", "adobe.com",
            "github.com", "stackoverflow.com", "dropbox.com",

            # 其他重要服务
            "netflix.com", "spotify.com", "steam.com", "epicgames.com"
        ]

        # 同形字符映射
        self.homoglyph_mapping = {
            'а': 'a', 'ɑ': 'a', 'а': 'a', 'α': 'a', 'а': 'a',
            'е': 'e', 'е': 'e', 'е': 'e', 'е': 'e', 'е': 'e',
            'о': 'o', 'о': 'o', 'о': 'o', 'о': 'o', 'о': 'o',
            'р': 'p', 'р': 'p', 'р': 'p', 'ρ': 'p',
            'с': 'c', 'с': 'c', 'с': 'c', 'с': 'c', 'с': 'c',
            'і': 'i', 'і': 'i', 'і': 'i', 'ι': 'i',
            'ј': 'j', 'ј': 'j', 'ј': 'j',
            'l': 'I', 'l': 'I', 'l': 'I',
            '0': 'o', 'о': 'o', 'о': 'o',
            '1': 'i', 'і': 'i', 'і': 'i',
            '5': 's', 'ѕ': 's', 'ѕ': 's',
            'vv': 'w', 'w': 'w',
            'rn': 'm', 'm': 'm'
        }

        # 初始化相似度计算器
        if OPENSQUAT_AVAILABLE:
            self.levenshtein = NormalizedLevenshtein()
            self.homoglyphs = Homoglyphs(categories=('LATIN', 'CYRILLIC', 'GREEK'))

    def is_available(self) -> bool:
        """检查检测器是否可用"""
        return self.enabled

    def analyze_domain(self, url: str) -> DomainAnalysisResult:
        """
        分析域名是否存在同形/近似域钓鱼风险

        Args:
            url: 要分析的URL

        Returns:
            域名分析结果
        """
        if not self.enabled:
            return DomainAnalysisResult(
                domain=self._extract_domain(url),
                is_suspicious=False,
                confidence=0.0,
                suspicious_features=[],
                similar_domains=[],
                homoglyph_issues=[],
                risk_factors=["openSquat库不可用"]
            )

        try:
            domain = self._extract_domain(url)
            if not domain:
                return DomainAnalysisResult(
                    domain=domain,
                    is_suspicious=False,
                    confidence=0.0,
                    suspicious_features=[],
                    similar_domains=[],
                    homoglyph_issues=[],
                    risk_factors=["无法提取域名"]
                )

            # 分析各种可疑特征
            suspicious_features = []
            similar_domains = []
            homoglyph_issues = []
            risk_factors = []

            # 1. 检查同形字符
            homoglyph_result = self._check_homoglyphs(domain)
            homoglyph_issues.extend(homoglyph_result['issues'])
            suspicious_features.extend(homoglyph_result['features'])

            # 2. 检查相似域名
            similarity_result = self._check_similarity(domain)
            similar_domains.extend(similarity_result['similar_domains'])
            suspicious_features.extend(similarity_result['features'])

            # 3. 检查域名结构
            structure_result = self._check_domain_structure(domain)
            suspicious_features.extend(structure_result['features'])
            risk_factors.extend(structure_result['risk_factors'])

            # 4. 检查特殊字符
            special_char_result = self._check_special_characters(domain)
            suspicious_features.extend(special_char_result['features'])
            risk_factors.extend(special_char_result['risk_factors'])

            # 计算综合置信度
            confidence = self._calculate_confidence(
                suspicious_features, homoglyph_issues, similar_domains, risk_factors
            )

            # 判断是否可疑
            is_suspicious = confidence > 0.6 or len(homoglyph_issues) > 0

            return DomainAnalysisResult(
                domain=domain,
                is_suspicious=is_suspicious,
                confidence=confidence,
                suspicious_features=suspicious_features,
                similar_domains=similar_domains,
                homoglyph_issues=homoglyph_issues,
                risk_factors=risk_factors
            )

        except Exception as e:
            logger.error(f"域名分析失败 {url}: {e}")
            return DomainAnalysisResult(
                domain=self._extract_domain(url),
                is_suspicious=False,
                confidence=0.0,
                suspicious_features=[],
                similar_domains=[],
                homoglyph_issues=[],
                risk_factors=[f"分析异常: {str(e)}"]
            )

    def _extract_domain(self, url: str) -> Optional[str]:
        """提取域名"""
        try:
            if not url or not url.strip():
                return None

            # 移除协议
            url = url.lower()
            if url.startswith(('http://', 'https://')):
                url = url[url.find('://') + 3:]

            # 提取域名部分
            domain = url.split('/')[0].split(':')[0]

            # 移除www.前缀
            if domain.startswith('www.'):
                domain = domain[4:]

            # 使用IDNA处理国际化域名
            try:
                domain = idna.encode(domain).decode('ascii')
            except (idna.IDNAError, UnicodeError):
                pass

            return domain
        except Exception:
            return None

    def _check_homoglyphs(self, domain: str) -> Dict[str, Any]:
        """检查同形字符"""
        issues = []
        features = []

        if not OPENSQUAT_AVAILABLE:
            return {'issues': issues, 'features': features}

        try:
            # 检查是否包含同形字符
            if is_confusable(domain):
                features.append("包含同形字符")
                issues.append({
                    "type": "confusable_characters",
                    "description": "域名包含可能被混淆的同形字符",
                    "severity": "high"
                })

            # 检查具体的同形字符映射
            ascii_domain = domain
            for cyrillic, latin in self.homoglyph_mapping.items():
                if cyrillic in domain:
                    ascii_domain = ascii_domain.replace(cyrillic, latin)
                    features.append(f"包含西里尔字符 '{cyrillic}' (伪装成 '{latin}')")
                    issues.append({
                        "type": "cyrillic_spoofing",
                        "character": cyrillic,
                        "replacement": latin,
                        "severity": "high"
                    })

            # 如果ASCII版本与原始域名不同，说明有同形字符
            if ascii_domain != domain:
                features.append("域名包含非标准字符")
                issues.append({
                    "type": "non_standard_characters",
                    "original": domain,
                    "ascii_version": ascii_domain,
                    "severity": "medium"
                })

        except Exception as e:
            logger.error(f"同形字符检查失败: {e}")

        return {'issues': issues, 'features': features}

    def _check_similarity(self, domain: str) -> Dict[str, Any]:
        """检查相似域名"""
        similar_domains = []
        features = []

        if not OPENSQUAT_AVAILABLE:
            return {'similar_domains': similar_domains, 'features': features}

        try:
            for target in self.target_domains:
                # 计算编辑距离相似度
                similarity = self.levenshtein.similarity(domain, target)

                if similarity > 0.7:  # 相似度阈值
                    similar_domains.append({
                        "domain": target,
                        "similarity": similarity,
                        "type": "high_similarity"
                    })

                    if similarity > 0.85:
                        features.append(f"与目标域名 {target} 高度相似 ({similarity:.2f})")
                    elif similarity > 0.7:
                        features.append(f"与目标域名 {target} 相似 ({similarity:.2f})")

        except Exception as e:
            logger.error(f"相似度检查失败: {e}")

        return {'similar_domains': similar_domains, 'features': features}

    def _check_domain_structure(self, domain: str) -> Dict[str, Any]:
        """检查域名结构"""
        features = []
        risk_factors = []

        try:
            # 检查域名长度
            if len(domain) > 30:
                features.append("域名过长")
                risk_factors.append("长域名可能用于隐藏恶意内容")

            # 检查连字符数量
            if domain.count('-') > 2:
                features.append("包含过多连字符")
                risk_factors.append("过多连字符可能是钓鱼网站特征")

            # 检查数字数量
            digit_count = sum(c.isdigit() for c in domain)
            if digit_count > len(domain) * 0.3:  # 超过30%是数字
                features.append("包含过多数字")
                risk_factors.append("高数字比例可能是钓鱼网站特征")

            # 检查子域名层数
            if domain.count('.') > 3:
                features.append("子域名层数过多")
                risk_factors.append("复杂子域名结构可能用于欺骗")

            # 检查是否为IP地址
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
                features.append("直接使用IP地址")
                risk_factors.append("直接IP访问通常是可疑的")

        except Exception as e:
            logger.error(f"域名结构检查失败: {e}")

        return {'features': features, 'risk_factors': risk_factors}

    def _check_special_characters(self, domain: str) -> Dict[str, Any]:
        """检查特殊字符"""
        features = []
        risk_factors = []

        try:
            # 检查非ASCII字符
            non_ascii = [c for c in domain if ord(c) > 127]
            if non_ascii:
                features.append("包含非ASCII字符")
                risk_factors.append("非ASCII字符可能用于同形攻击")

            # 检查可疑字符组合
            suspicious_patterns = [
                r'.*-.*-.*',  # 多个连字符
                r'.*\d{4,}.*',  # 连续4个以上数字
                r'.*[a-z]{4,}\d+.*',  # 长字符串加数字
                r'.*\d+[a-z]{4,}.*',  # 数字加长字符串
            ]

            for pattern in suspicious_patterns:
                if re.match(pattern, domain):
                    features.append("包含可疑字符模式")
                    risk_factors.append("可疑字符组合可能是钓鱼网站特征")
                    break

        except Exception as e:
            logger.error(f"特殊字符检查失败: {e}")

        return {'features': features, 'risk_factors': risk_factors}

    def _calculate_confidence(self, features: List[str], homoglyph_issues: List[Dict],
                            similar_domains: List[Dict], risk_factors: List[str]) -> float:
        """计算钓鱼置信度"""
        confidence = 0.0

        # 基于同形字符问题
        high_severity_issues = [i for i in homoglyph_issues if i.get('severity') == 'high']
        medium_severity_issues = [i for i in homoglyph_issues if i.get('severity') == 'medium']

        confidence += len(high_severity_issues) * 0.4
        confidence += len(medium_severity_issues) * 0.2

        # 基于相似域名
        high_similarity = [d for d in similar_domains if d.get('similarity', 0) > 0.85]
        medium_similarity = [d for d in similar_domains if d.get('similarity', 0) > 0.7]

        confidence += len(high_similarity) * 0.3
        confidence += len(medium_similarity) * 0.15

        # 基于可疑特征
        confidence += len(features) * 0.1

        # 基于风险因素
        confidence += len(risk_factors) * 0.05

        # 限制置信度范围
        return min(1.0, max(0.0, confidence))

    def get_target_domains(self) -> List[str]:
        """获取目标域名列表"""
        return self.target_domains.copy()

    def add_target_domain(self, domain: str) -> bool:
        """添加目标域名"""
        try:
            if domain and domain not in self.target_domains:
                self.target_domains.append(domain.lower())
                return True
        except Exception as e:
            logger.error(f"添加目标域名失败: {e}")
        return False

    def remove_target_domain(self, domain: str) -> bool:
        """移除目标域名"""
        try:
            if domain in self.target_domains:
                self.target_domains.remove(domain.lower())
                return True
        except Exception as e:
            logger.error(f"移除目标域名失败: {e}")
        return False

# 创建全局实例
opensquat_detector = OpenSquatDetector()