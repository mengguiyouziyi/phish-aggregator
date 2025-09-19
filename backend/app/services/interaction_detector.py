"""
交互式钓鱼检测服务
基于用户交互模式和行为分析的钓鱼网站检测
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import logging
from dataclasses import dataclass
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class InteractionPattern:
    """交互模式数据类"""
    element_type: str
    element_tag: str
    element_id: str
    element_name: str
    element_action: str
    element_content: str
    element_attributes: Dict[str, str]
    element_position: Dict[str, float]
    element_size: Dict[str, float]
    is_suspicious: bool
    suspicious_reason: str

@dataclass
class InteractionMetrics:
    """交互指标数据类"""
    total_elements: int
    suspicious_elements: int
    form_count: int
    input_field_count: int
    button_count: int
    link_count: int
    script_count: int
    iframe_count: int
    avg_response_time: float
    interaction_score: float

class InteractionPhishDetector:
    """交互式钓鱼检测器"""

    def __init__(self):
        self.name = "phishintention"
        self.description = "基于交互模式的钓鱼网站检测"
        self.version = "1.0.0"
        self.enabled = True

        # 钓鱼网站特征模式
        self.suspicious_patterns = {
            "password_input": [
                r"password|pwd|passwd|pass",
                r"登录|密码|口令",
                r"sign.?in|log.?in"
            ],
            "sensitive_fields": [
                r"card|credit|debit",
                r"ssn|social.?security",
                r"account.?number|acct.?num",
                r"routing.?number"
            ],
            "urgent_actions": [
                r"紧急|urgent|immediate",
                r"verify|验证|确认",
                r"update|更新|升级",
                r"expired|过期|失效"
            ],
            "fake_domains": [
                r"security|secure|safe",
                r"account|accounts",
                r"login|signin|verify",
                r"update|support|service"
            ],
            "suspicious_redirects": [
                r"redirect|location|href",
                r"window\.location|document\.location",
                r"setTimeout|setInterval"
            ]
        }

        # 权重配置
        self.weights = {
            "suspicious_element": 0.15,
            "form_count": 0.10,
            "input_field_count": 0.05,
            "suspicious_redirect": 0.20,
            "iframe_count": 0.10,
            "script_count": 0.05,
            "domain_mismatch": 0.25,
            "urgent_language": 0.10
        }

    async def analyze_interaction(self, url: str, html_content: str) -> Dict[str, Any]:
        """
        分析网站的交互模式

        Args:
            url: 要分析的URL
            html_content: 页面HTML内容

        Returns:
            交互分析结果
        """
        try:
            start_time = time.time()

            # 解析HTML内容
            interaction_patterns = await self._extract_interaction_patterns(html_content)

            # 计算交互指标
            metrics = self._calculate_interaction_metrics(interaction_patterns)

            # 分析可疑行为
            suspicious_behaviors = self._analyze_suspicious_behaviors(interaction_patterns, url)

            # 计算钓鱼概率
            phishing_probability = self._calculate_phishing_probability(metrics, suspicious_behaviors)

            # 生成详细报告
            analysis_result = {
                "url": url,
                "is_phishing": phishing_probability > 0.7,
                "confidence": phishing_probability,
                "message": "网站存在交互式钓鱼风险" if phishing_probability > 0.7 else "网站交互模式正常",
                "processing_time": time.time() - start_time,
                "interaction_metrics": metrics.__dict__,
                "suspicious_behaviors": suspicious_behaviors,
                "interaction_patterns": [pattern.__dict__ for pattern in interaction_patterns[:20]],  # 限制返回数量
                "risk_factors": self._generate_risk_factors(metrics, suspicious_behaviors)
            }

            return analysis_result

        except Exception as e:
            logger.error(f"交互分析失败 {url}: {e}")
            return {
                "url": url,
                "is_phishing": False,
                "confidence": 0.0,
                "message": f"交互分析失败: {str(e)}",
                "processing_time": 0.0,
                "interaction_metrics": {},
                "suspicious_behaviors": [],
                "interaction_patterns": [],
                "risk_factors": []
            }

    async def _extract_interaction_patterns(self, html_content: str) -> List[InteractionPattern]:
        """提取交互模式"""
        patterns = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # 分析表单元素
            forms = soup.find_all('form')
            for form in forms:
                form_pattern = InteractionPattern(
                    element_type="form",
                    element_tag="form",
                    element_id=form.get('id', ''),
                    element_name=form.get('name', ''),
                    element_action=form.get('action', ''),
                    element_content=form.get_text(strip=True)[:200],
                    element_attributes=dict(form.attrs),
                    element_position={"x": 0, "y": 0},
                    element_size={"width": 0, "height": 0},
                    is_suspicious=self._is_suspicious_form(form),
                    suspicious_reason=self._get_suspicious_form_reason(form)
                )
                patterns.append(form_pattern)

            # 分析输入字段
            inputs = soup.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                input_type = input_elem.get('type', 'text')
                input_pattern = InteractionPattern(
                    element_type="input",
                    element_tag=input_elem.name,
                    element_id=input_elem.get('id', ''),
                    element_name=input_elem.get('name', ''),
                    element_action=f"type_{input_type}",
                    element_content=input_elem.get('placeholder', '')[:100],
                    element_attributes=dict(input_elem.attrs),
                    element_position={"x": 0, "y": 0},
                    element_size={"width": 0, "height": 0},
                    is_suspicious=self._is_suspicious_input(input_elem),
                    suspicious_reason=self._get_suspicious_input_reason(input_elem)
                )
                patterns.append(input_pattern)

            # 分析按钮
            buttons = soup.find_all(['button', 'input[type="button"]', 'input[type="submit"]'])
            for button in buttons:
                button_pattern = InteractionPattern(
                    element_type="button",
                    element_tag=button.name if button.name != 'input' else 'input',
                    element_id=button.get('id', ''),
                    element_name=button.get('name', ''),
                    element_action="click",
                    element_content=button.get_text(strip=True)[:100],
                    element_attributes=dict(button.attrs),
                    element_position={"x": 0, "y": 0},
                    element_size={"width": 0, "height": 0},
                    is_suspicious=self._is_suspicious_button(button),
                    suspicious_reason=self._get_suspicious_button_reason(button)
                )
                patterns.append(button_pattern)

            # 分析链接
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                link_pattern = InteractionPattern(
                    element_type="link",
                    element_tag="a",
                    element_id=link.get('id', ''),
                    element_name=link.get('name', ''),
                    element_action="navigate",
                    element_content=link.get_text(strip=True)[:100],
                    element_attributes=dict(link.attrs),
                    element_position={"x": 0, "y": 0},
                    element_size={"width": 0, "height": 0},
                    is_suspicious=self._is_suspicious_link(link),
                    suspicious_reason=self._get_suspicious_link_reason(link)
                )
                patterns.append(link_pattern)

            # 分析脚本
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.get_text()[:500] or script.get('src', '')
                script_pattern = InteractionPattern(
                    element_type="script",
                    element_tag="script",
                    element_id=script.get('id', ''),
                    element_name=script.get('name', ''),
                    element_action="execute",
                    element_content=script_content,
                    element_attributes=dict(script.attrs),
                    element_position={"x": 0, "y": 0},
                    element_size={"width": 0, "height": 0},
                    is_suspicious=self._is_suspicious_script(script),
                    suspicious_reason=self._get_suspicious_script_reason(script)
                )
                patterns.append(script_pattern)

            # 分析iframe
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                iframe_pattern = InteractionPattern(
                    element_type="iframe",
                    element_tag="iframe",
                    element_id=iframe.get('id', ''),
                    element_name=iframe.get('name', ''),
                    element_action="embed",
                    element_content=iframe.get('src', '')[:100],
                    element_attributes=dict(iframe.attrs),
                    element_position={"x": 0, "y": 0},
                    element_size={"width": 0, "height": 0},
                    is_suspicious=self._is_suspicious_iframe(iframe),
                    suspicious_reason=self._get_suspicious_iframe_reason(iframe)
                )
                patterns.append(iframe_pattern)

        except Exception as e:
            logger.error(f"提取交互模式失败: {e}")

        return patterns

    def _calculate_interaction_metrics(self, patterns: List[InteractionPattern]) -> InteractionMetrics:
        """计算交互指标"""
        metrics = InteractionMetrics(
            total_elements=len(patterns),
            suspicious_elements=len([p for p in patterns if p.is_suspicious]),
            form_count=len([p for p in patterns if p.element_type == "form"]),
            input_field_count=len([p for p in patterns if p.element_type == "input"]),
            button_count=len([p for p in patterns if p.element_type == "button"]),
            link_count=len([p for p in patterns if p.element_type == "link"]),
            script_count=len([p for p in patterns if p.element_type == "script"]),
            iframe_count=len([p for p in patterns if p.element_type == "iframe"]),
            avg_response_time=0.0,
            interaction_score=0.0
        )

        # 计算交互分数
        if metrics.total_elements > 0:
            metrics.interaction_score = metrics.suspicious_elements / metrics.total_elements

        return metrics

    def _analyze_suspicious_behaviors(self, patterns: List[InteractionPattern], url: str) -> List[Dict[str, Any]]:
        """分析可疑行为"""
        behaviors = []

        # 分析表单行为
        forms = [p for p in patterns if p.element_type == "form"]
        for form in forms:
            if form.is_suspicious:
                behaviors.append({
                    "type": "suspicious_form",
                    "severity": "high",
                    "description": form.suspicious_reason,
                    "element": form.__dict__
                })

        # 分析输入字段行为
        inputs = [p for p in patterns if p.element_type == "input"]
        sensitive_inputs = [p for p in inputs if p.is_suspicious]
        for input_elem in sensitive_inputs:
            behaviors.append({
                "type": "sensitive_input",
                "severity": "medium",
                "description": input_elem.suspicious_reason,
                "element": input_elem.__dict__
            })

        # 分析脚本行为
        scripts = [p for p in patterns if p.element_type == "script"]
        for script in scripts:
            if script.is_suspicious:
                behaviors.append({
                    "type": "malicious_script",
                    "severity": "high",
                    "description": script.suspicious_reason,
                    "element": script.__dict__
                })

        # 分析重定向行为
        redirect_scripts = [p for p in scripts if self._contains_redirect_pattern(p.element_content)]
        for script in redirect_scripts:
            behaviors.append({
                "type": "suspicious_redirect",
                "severity": "medium",
                "description": "发现可疑的重定向脚本",
                "element": script.__dict__
            })

        # 分析iframe行为
        iframes = [p for p in patterns if p.element_type == "iframe"]
        for iframe in iframes:
            if iframe.is_suspicious:
                behaviors.append({
                    "type": "suspicious_iframe",
                    "severity": "medium",
                    "description": iframe.suspicious_reason,
                    "element": iframe.__dict__
                })

        return behaviors

    def _calculate_phishing_probability(self, metrics: InteractionMetrics, behaviors: List[Dict[str, Any]]) -> float:
        """计算钓鱼概率"""
        probability = 0.0

        # 基于可疑元素数量
        probability += metrics.suspicious_elements * self.weights["suspicious_element"]

        # 基于表单数量
        if metrics.form_count > 2:
            probability += (metrics.form_count - 2) * self.weights["form_count"]

        # 基于输入字段数量
        if metrics.input_field_count > 5:
            probability += (metrics.input_field_count - 5) * self.weights["input_field_count"]

        # 基于iframe数量
        probability += metrics.iframe_count * self.weights["iframe_count"]

        # 基于脚本数量
        if metrics.script_count > 10:
            probability += (metrics.script_count - 10) * self.weights["script_count"]

        # 基于可疑行为严重程度
        severity_weights = {"high": 0.15, "medium": 0.08, "low": 0.03}
        for behavior in behaviors:
            probability += severity_weights.get(behavior["severity"], 0.05)

        # 限制概率范围
        return min(1.0, max(0.0, probability))

    def _generate_risk_factors(self, metrics: InteractionMetrics, behaviors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成风险因素"""
        factors = []

        if metrics.suspicious_elements > 0:
            factors.append({
                "factor": "suspicious_elements",
                "level": "high" if metrics.suspicious_elements > 3 else "medium",
                "description": f"发现 {metrics.suspicious_elements} 个可疑交互元素"
            })

        if metrics.form_count > 2:
            factors.append({
                "factor": "multiple_forms",
                "level": "medium",
                "description": f"页面包含 {metrics.form_count} 个表单"
            })

        if metrics.iframe_count > 0:
            factors.append({
                "factor": "iframes_present",
                "level": "medium",
                "description": f"页面包含 {metrics.iframe_count} 个iframe"
            })

        if metrics.script_count > 15:
            factors.append({
                "factor": "excessive_scripts",
                "level": "medium",
                "description": f"页面包含 {metrics.script_count} 个脚本"
            })

        # 添加基于行为的风险因素
        high_severity_behaviors = [b for b in behaviors if b.get("severity") == "high"]
        if high_severity_behaviors:
            factors.append({
                "factor": "high_severity_behaviors",
                "level": "high",
                "description": f"发现 {len(high_severity_behaviors)} 个高风险行为"
            })

        return factors

    # 可疑性检测方法
    def _is_suspicious_form(self, form) -> bool:
        """检查表单是否可疑"""
        action = form.get('action', '').lower()
        content = form.get_text().lower()

        # 检查是否提交到可疑URL
        suspicious_keywords = ['login', 'signin', 'auth', 'verify', 'update', 'secure']
        if any(keyword in action for keyword in suspicious_keywords):
            return True

        # 检查是否包含敏感字段
        sensitive_patterns = self.suspicious_patterns["password_input"]
        if any(re.search(pattern, content) for pattern in sensitive_patterns):
            return True

        return False

    def _get_suspicious_form_reason(self, form) -> str:
        """获取表单可疑原因"""
        action = form.get('action', '').lower()
        content = form.get_text().lower()

        if 'login' in action or 'signin' in action:
            return "表单提交到登录相关URL"

        if any(re.search(pattern, content) for pattern in self.suspicious_patterns["password_input"]):
            return "表单包含密码输入字段"

        if 'verify' in action or 'update' in action:
            return "表单提交到验证/更新URL"

        return "表单行为异常"

    def _is_suspicious_input(self, input_elem) -> bool:
        """检查输入字段是否可疑"""
        input_type = input_elem.get('type', 'text').lower()
        input_name = input_elem.get('name', '').lower()
        input_id = input_elem.get('id', '').lower()
        input_placeholder = input_elem.get('placeholder', '').lower()

        # 检查密码字段
        if input_type == 'password':
            return True

        # 检查敏感字段名称
        sensitive_patterns = self.suspicious_patterns["sensitive_fields"]
        text_to_check = f"{input_name} {input_id} {input_placeholder}"

        return any(re.search(pattern, text_to_check) for pattern in sensitive_patterns)

    def _get_suspicious_input_reason(self, input_elem) -> str:
        """获取输入字段可疑原因"""
        input_type = input_elem.get('type', 'text').lower()

        if input_type == 'password':
            return "密码输入字段"

        input_name = input_elem.get('name', '').lower()
        input_id = input_elem.get('id', '').lower()

        if 'card' in input_name or 'credit' in input_name:
            return "信用卡信息输入字段"

        if 'ssn' in input_name or 'social' in input_name:
            return "社会安全号码输入字段"

        if 'account' in input_name and 'number' in input_name:
            return "账户号码输入字段"

        return "输入字段包含敏感信息"

    def _is_suspicious_button(self, button) -> bool:
        """检查按钮是否可疑"""
        button_text = button.get_text().lower()
        button_id = button.get('id', '').lower()
        button_name = button.get('name', '').lower()

        text_to_check = f"{button_text} {button_id} {button_name}"

        # 检查紧急性语言
        urgent_patterns = self.suspicious_patterns["urgent_actions"]
        return any(re.search(pattern, text_to_check) for pattern in urgent_patterns)

    def _get_suspicious_button_reason(self, button) -> str:
        """获取按钮可疑原因"""
        button_text = button.get_text().lower()

        if 'urgent' in button_text or '紧急' in button_text:
            return "按钮包含紧急性语言"

        if 'verify' in button_text or '验证' in button_text:
            return "按钮包含验证相关语言"

        if 'update' in button_text or '更新' in button_text:
            return "按钮包含更新相关语言"

        return "按钮行为可疑"

    def _is_suspicious_link(self, link) -> bool:
        """检查链接是否可疑"""
        href = link.get('href', '').lower()
        link_text = link.get_text().lower()

        # 检查是否链接到可疑域名
        fake_domain_patterns = self.suspicious_patterns["fake_domains"]
        if any(pattern in href for pattern in fake_domain_patterns):
            return True

        # 检查链接文本是否可疑
        urgent_patterns = self.suspicious_patterns["urgent_actions"]
        if any(re.search(pattern, link_text) for pattern in urgent_patterns):
            return True

        return False

    def _get_suspicious_link_reason(self, link) -> str:
        """获取链接可疑原因"""
        href = link.get('href', '').lower()
        link_text = link.get_text().lower()

        if any(pattern in href for pattern in self.suspicious_patterns["fake_domains"]):
            return "链接指向可疑域名"

        if 'urgent' in link_text or '紧急' in link_text:
            return "链接包含紧急性语言"

        return "链接行为可疑"

    def _is_suspicious_script(self, script) -> bool:
        """检查脚本是否可疑"""
        script_content = script.get_text().lower()
        script_src = script.get('src', '').lower()

        # 检查是否包含重定向模式
        if self._contains_redirect_pattern(script_content):
            return True

        # 检查是否包含可疑的JavaScript代码
        suspicious_patterns = [
            r'document\.write',
            r'eval\s*\(',
            r'setTimeout.*location',
            r'window\.open',
            r'popup',
            r'alert.*password',
            r'prompt.*password'
        ]

        return any(re.search(pattern, script_content) for pattern in suspicious_patterns)

    def _get_suspicious_script_reason(self, script) -> str:
        """获取脚本可疑原因"""
        script_content = script.get_text().lower()

        if self._contains_redirect_pattern(script_content):
            return "脚本包含重定向代码"

        if 'document.write' in script_content:
            return "脚本使用document.write"

        if 'eval(' in script_content:
            return "脚本使用eval函数"

        if 'window.open' in script_content:
            return "脚本包含弹窗代码"

        return "脚本行为可疑"

    def _is_suspicious_iframe(self, iframe) -> bool:
        """检查iframe是否可疑"""
        iframe_src = iframe.get('src', '').lower()

        # 检查是否嵌入可疑内容
        if not iframe_src:
            return True  # 空src的iframe可能用于隐藏内容

        # 检查是否嵌入外部域名
        fake_domain_patterns = self.suspicious_patterns["fake_domains"]
        return any(pattern in iframe_src for pattern in fake_domain_patterns)

    def _get_suspicious_iframe_reason(self, iframe) -> str:
        """获取iframe可疑原因"""
        iframe_src = iframe.get('src', '').lower()

        if not iframe_src:
            return "iframe没有src属性"

        if any(pattern in iframe_src for pattern in self.suspicious_patterns["fake_domains"]):
            return "iframe嵌入可疑域名"

        return "iframe行为可疑"

    def _contains_redirect_pattern(self, text: str) -> bool:
        """检查是否包含重定向模式"""
        redirect_patterns = self.suspicious_patterns["suspicious_redirects"]
        return any(re.search(pattern, text) for pattern in redirect_patterns)

# 创建全局实例
interaction_detector = InteractionPhishDetector()