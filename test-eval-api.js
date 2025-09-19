import { chromium } from 'playwright';

(async () => {
  console.log('🧪 测试评测API...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听网络请求
    page.on('request', request => {
      if (request.url().includes('/api/evaluate')) {
        console.log(`[请求] ${request.method()} ${request.url()}`);
        console.log(`[请求体] ${request.postData()}`);
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/evaluate')) {
        try {
          const data = await response.json();
          console.log(`[响应] ${response.url()}:`, JSON.stringify(data, null, 2));
        } catch (e) {
          console.log(`[响应] ${response.url()}: ${await response.text()}`);
        }
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 选择URLBERT模型
    const modelCheckboxes = await page.$$('input[name="model"]');
    for (const checkbox of modelCheckboxes) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, checkbox);
      if (label.includes('URLBERT')) {
        await checkbox.check();
        console.log('✅ 已选择URLBERT模型');
      } else {
        await checkbox.uncheck();
      }
    }

    // 选择规则
    const ruleCheckboxes = await page.$$('input[name="rule"]');
    if (ruleCheckboxes.length > 0) {
      await ruleCheckboxes[0].check();
      console.log('✅ 已选择一个规则');
    }

    // 开始评测
    console.log('\n🔍 开始评测...');
    await page.evaluate(() => {
      const evalButton = Array.from(document.querySelectorAll('button')).find(btn =>
        btn.textContent.includes('开始评测')
      );
      if (evalButton) {
        evalButton.click();
      }
    });

    // 等待评测完成
    console.log('⏳ 等待评测结果...');
    await page.waitForTimeout(10000);

    console.log('\n🎉 评测API测试完成！');

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();