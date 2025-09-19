import { chromium } from 'playwright';

(async () => {
  console.log('🧪 带URL的评测功能测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    page.on('console', msg => {
      if (msg.text().includes('错误') || msg.text().includes('Error') || msg.text().includes('评测') || msg.text().includes('失败')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    console.log('\n📝 输入测试URLs...');

    // 输入一些测试URLs
    const testUrls = [
      'https://www.google.com',
      'https://www.microsoft.com',
      'https://github.com'
    ];

    await page.fill('#urls', testUrls.join('\n'));
    console.log(`✅ 已输入 ${testUrls.length} 个测试URL`);

    // 选择一些规则和模型
    console.log('\n⚙️ 选择规则和模型...');

    // 选择前2个规则
    const ruleCheckboxes = await page.$$('input[name="rule"]');
    for (let i = 0; i < Math.min(2, ruleCheckboxes.length); i++) {
      await ruleCheckboxes[i].check();
    }
    console.log(`✅ 已选择 ${Math.min(2, ruleCheckboxes.length)} 个规则`);

    // 选择前2个模型
    const modelCheckboxes = await page.$$('input[name="model"]');
    for (let i = 0; i < Math.min(2, modelCheckboxes.length); i++) {
      await modelCheckboxes[i].check();
    }
    console.log(`✅ 已选择 ${Math.min(2, modelCheckboxes.length)} 个模型`);

    // 点击评测按钮
    console.log('\n📊 开始评测...');
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
    await page.waitForTimeout(5000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 结果区域内容长度: ${resultContent.length} 字符`);

    if (resultContent.includes('评测结果')) {
      console.log('✅ 评测功能正常工作');

      // 检查是否有ANY和WEIGHTED策略结果
      const hasAny = resultContent.includes('ANY');
      const hasWeighted = resultContent.includes('WEIGHTED');
      console.log(`ANY策略结果: ${hasAny ? '✅' : '❌'}`);
      console.log(`WEIGHTED策略结果: ${hasWeighted ? '✅' : '❌'}`);

    } else if (resultContent.includes('错误') || resultContent.includes('Error')) {
      console.log('❌ 评测过程中出现错误');
      console.log('错误内容预览:', resultContent.substring(0, 300));
    } else {
      console.log('⚠️ 评测功能响应异常');
      console.log('结果预览:', resultContent.substring(0, 300));
    }

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();