#!/usr/bin/env python3
"""
初始化视觉检测目标网站
"""

import asyncio
import aiohttp
import json

async def initialize_targets():
    """初始化目标网站"""
    print("🎯 初始化视觉检测目标网站...")

    try:
        async with aiohttp.ClientSession() as session:
            # 初始化检测系统
            async with session.post(
                "http://localhost:8000/initialize",
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 系统初始化成功")
                    print(f"响应: {result}")
                else:
                    print(f"❌ 系统初始化失败: {response.status}")
                    error_text = await response.text()
                    print(f"错误信息: {error_text}")

            # 添加一些常见的目标网站
            target_sites = [
                ("https://www.icbc.com.cn", "中国工商银行"),
                ("https://www.alipay.com", "支付宝"),
                ("https://www.qq.com", "腾讯QQ"),
                ("https://www.baidu.com", "百度"),
                ("https://www.jd.com", "京东"),
            ]

            for url, name in target_sites:
                try:
                    add_data = {"url": url, "name": name}
                    async with session.post(
                        "http://localhost:8000/targets",
                        json=add_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            print(f"✅ 添加目标: {name}")
                        else:
                            print(f"❌ 添加目标失败: {name} - {response.status}")
                except Exception as e:
                    print(f"❌ 添加目标异常: {name} - {e}")

            # 检查当前目标列表
            async with session.get(
                "http://localhost:8000/targets",
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"\n📊 当前目标列表:")
                    for target in result.get("targets", []):
                        print(f"  - {target.get('name', 'N/A')}: {target.get('url', 'N/A')}")
                else:
                    print(f"❌ 获取目标列表失败: {response.status}")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(initialize_targets())