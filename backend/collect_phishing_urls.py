#!/usr/bin/env python3
"""
从合法的安全数据库收集真实钓鱼网站URL用于测试

数据来源：
- OpenPhish: https://openphish.com/
- PhishTank: https://phishtank.org/
- URLhaus: https://urlhaus.abuse.ch/
"""

import requests
import json
import time
import re
from urllib.parse import urlparse
from typing import List, Dict
import os
import sys

class PhishingURLCollector:
    """钓鱼URL收集器"""

    def __init__(self):
        self.sources = {
            'openphish': {
                'url': 'https://openphish.com/feed.txt',
                'name': 'OpenPhish'
            },
            'phishing_database': {
                'url': 'https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt',
                'name': 'Phishing.Database'
            },
            'urlhaus': {
                'url': 'https://urlhaus.abuse.ch/downloads/text_online/',
                'name': 'URLhaus'
            }
        }

    def collect_from_openphish(self) -> List[str]:
        """从OpenPhish收集URL"""
        try:
            print("🔄 正在从 OpenPhish 收集数据...")
            response = requests.get('https://openphish.com/feed.txt', timeout=30)
            response.raise_for_status()

            urls = []
            for line in response.text.strip().split('\n'):
                if line.strip() and self.is_valid_url(line.strip()):
                    urls.append(line.strip())

            print(f"✅ OpenPhish 收集到 {len(urls)} 个URL")
            return urls[:100]  # 限制数量

        except Exception as e:
            print(f"❌ OpenPhish 收集失败: {e}")
            return []

    def collect_from_phishing_database(self) -> List[str]:
        """从Phishing.Database收集URL"""
        try:
            print("🔄 正在从 Phishing.Database 收集数据...")
            response = requests.get(
                'https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE-NOW.txt',
                timeout=30
            )
            response.raise_for_status()

            urls = []
            for line in response.text.strip().split('\n'):
                if line.strip() and self.is_valid_url(line.strip()):
                    urls.append(line.strip())

            print(f"✅ Phishing.Database 收集到 {len(urls)} 个URL")
            return urls[:100]

        except Exception as e:
            print(f"❌ Phishing.Database 收集失败: {e}")
            return []

    def collect_from_urlhaus(self) -> List[str]:
        """从URLhaus收集URL"""
        try:
            print("🔄 正在从 URLhaus 收集数据...")
            response = requests.get('https://urlhaus.abuse.ch/downloads/text_online/', timeout=30)
            response.raise_for_status()

            urls = []
            lines = response.text.strip().split('\n')
            for line in lines[1:]:  # 跳过标题行
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 1:
                        url = parts[0].strip()
                        if url and self.is_valid_url(url):
                            urls.append(url)

            print(f"✅ URLhaus 收集到 {len(urls)} 个URL")
            return urls[:100]

        except Exception as e:
            print(f"❌ URLhaus 收集失败: {e}")
            return []

    def is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def categorize_urls(self, urls: List[str]) -> Dict[str, List[str]]:
        """按类型分类URL"""
        categories = {
            'financial': [],  # 金融类
            'social_media': [],  # 社交媒体类
            'shopping': [],  # 购物类
            'government': [],  # 政府类
            'tech_company': [],  # 科技公司类
            'other': []  # 其他
        }

        # 关键词分类
        financial_keywords = ['bank', 'paypal', 'payment', 'card', 'credit', 'money', 'financial', 'secure']
        social_keywords = ['facebook', 'instagram', 'twitter', 'linkedin', 'social', 'profile']
        shopping_keywords = ['amazon', 'shop', 'store', 'buy', 'order', 'shipping']
        government_keywords = ['irs', 'government', 'tax', 'official', 'gov']
        tech_keywords = ['microsoft', 'apple', 'google', 'support', 'help', 'account']

        for url in urls:
            url_lower = url.lower()
            categorized = False

            if any(keyword in url_lower for keyword in financial_keywords):
                categories['financial'].append(url)
                categorized = True
            elif any(keyword in url_lower for keyword in social_keywords):
                categories['social_media'].append(url)
                categorized = True
            elif any(keyword in url_lower for keyword in shopping_keywords):
                categories['shopping'].append(url)
                categorized = True
            elif any(keyword in url_lower for keyword in government_keywords):
                categories['government'].append(url)
                categorized = True
            elif any(keyword in url_lower for keyword in tech_keywords):
                categories['tech_company'].append(url)
                categorized = True

            if not categorized:
                categories['other'].append(url)

        return categories

    def collect_all(self) -> Dict[str, any]:
        """从所有来源收集数据"""
        print("🚀 开始收集钓鱼网站数据...")

        all_urls = []
        sources_data = {}

        # 从各个来源收集
        openphish_urls = self.collect_from_openphish()
        if openphish_urls:
            all_urls.extend(openphish_urls)
            sources_data['openphish'] = {
                'count': len(openphish_urls),
                'urls': openphish_urls[:20]  # 只保存前20个作为示例
            }

        phishing_db_urls = self.collect_from_phishing_database()
        if phishing_db_urls:
            all_urls.extend(phishing_db_urls)
            sources_data['phishing_database'] = {
                'count': len(phishing_db_urls),
                'urls': phishing_db_urls[:20]
            }

        urlhaus_urls = self.collect_from_urlhaus()
        if urlhaus_urls:
            all_urls.extend(urlhaus_urls)
            sources_data['urlhaus'] = {
                'count': len(urlhaus_urls),
                'urls': urlhaus_urls[:20]
            }

        # 去重
        unique_urls = list(set(all_urls))
        print(f"📊 总计收集到 {len(unique_urls)} 个唯一URL")

        # 分类
        categories = self.categorize_urls(unique_urls[:200])  # 分类前200个

        result = {
            'total_count': len(unique_urls),
            'sources': sources_data,
            'categories': categories,
            'sample_urls': unique_urls[:50],  # 前50个作为示例
            'collection_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    def save_to_file(self, data: Dict, filename: str):
        """保存数据到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 数据已保存到 {filename}")
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")

    def generate_test_urls(self, data: Dict) -> List[str]:
        """生成用于测试的URL列表"""
        test_urls = []

        # 从各个类别选择URL
        for category, urls in data['categories'].items():
            if urls:
                test_urls.extend(urls[:10])  # 每个类别取10个

        # 确保有足够的数量
        while len(test_urls) < 100 and len(data['sample_urls']) > 0:
            remaining = 100 - len(test_urls)
            test_urls.extend(data['sample_urls'][:remaining])

        return test_urls[:100]

def main():
    """主函数"""
    collector = PhishingURLCollector()

    try:
        # 收集数据
        data = collector.collect_all()

        # 保存完整数据
        collector.save_to_file(data, 'phishing_urls_data.json')

        # 生成测试URL列表
        test_urls = collector.generate_test_urls(data)

        # 保存测试URL
        with open('phishing_test_urls.txt', 'w', encoding='utf-8') as f:
            for url in test_urls:
                f.write(url + '\n')

        print(f"✅ 生成了 {len(test_urls)} 个测试URL")
        print("📁 文件已保存:")
        print("   - phishing_urls_data.json (完整数据)")
        print("   - phishing_test_urls.txt (测试URL列表)")

        # 显示统计信息
        print(f"\n📈 数据统计:")
        print(f"   总URL数量: {data['total_count']}")
        print(f"   数据来源: {len(data['sources'])} 个")
        print(f"   分类数量: {len(data['categories'])} 个")

        for category, urls in data['categories'].items():
            print(f"   {category}: {len(urls)} 个")

        # 显示一些示例URL
        print(f"\n🔍 示例钓鱼URL:")
        for i, url in enumerate(test_urls[:10]):
            print(f"   {i+1}. {url}")

    except Exception as e:
        print(f"❌ 收集过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()