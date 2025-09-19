import { chromium } from 'playwright';

(async () => {
  console.log('🧪 真实URL深度测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    page.on('console', msg => {
      if (msg.text().includes('✅') || msg.text().includes('❌') || msg.text().includes('🚀') || msg.text().includes('📋')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
    });

    // 清除缓存并访问应用
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 真实钓鱼网站测试URLs
    const testUrls = [
      'https://www.google.com',      // 正常网站
      'https://www.microsoft.com',  // 正常网站
      'https://www.facebook.com',    // 正常网站
      'https://www.amazon.com',      // 正常网站
      'https://apple.com',           // 正常网站
    ];

    console.log('\n🔍 测试1: 真实URL扫描测试');

    // 输入测试URLs
    await page.fill('#urls', testUrls.join('\n'));
    console.log(`已输入 ${testUrls.length} 个测试URL`);

    // 选择所有可用规则和模型
    const ruleCheckboxes = await page.$$('input[name="rule"]');
    const modelCheckboxes = await page.$$('input[name="model"]');

    console.log(`发现 ${ruleCheckboxes.length} 个规则选项`);
    console.log(`发现 ${modelCheckboxes.length} 个模型选项`);

    // 选择前3个规则
    for (let i = 0; i < Math.min(3, ruleCheckboxes.length); i++) {
      await ruleCheckboxes[i].check();
    }

    // 选择所有模型
    for (const modelCheckbox of modelCheckboxes) {
      await modelCheckbox.check();
    }

    console.log('已选择规则和模型');

    // 测试ANY策略
    console.log('\n🎯 测试ANY策略扫描...');
    await page.click('input[value="any"]');
    await page.waitForTimeout(500);

    const scanButton = await page.$('button:has-text("开始扫描")');
    if (scanButton) {
      await scanButton.click();
      await page.waitForTimeout(5000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      const hasResults = resultContent.includes('检测结果统计') && resultContent.includes('URL');

      if (hasResults) {
        console.log('✅ ANY策略扫描成功');

        // 分析结果
        const totalMatches = (resultContent.match(/总计: \d+ 个URL/g) || [])[0] || '';
        const phishingMatches = (resultContent.match(/钓鱼: \d+ 个/g) || [])[0] || '';
        const legitMatches = (resultContent.match(/正常: \d+ 个/g) || [])[0] || '';

        console.log(`扫描结果: ${totalMatches} | ${phishingMatches} | ${legitMatches}`);
      } else {
        console.log('❌ ANY策略扫描失败');
      }
    }

    // 测试WEIGHTED策略
    console.log('\n⚖️ 测试WEIGHTED策略扫描...');
    await page.click('input[value="weighted"]');
    await page.waitForTimeout(500);

    if (scanButton) {
      await scanButton.click();
      await page.waitForTimeout(5000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      const showsWeighted = resultContent.includes('WEIGHTED');
      const hasResults = resultContent.includes('检测结果统计');

      console.log(`WEIGHTED策略: ${showsWeighted ? '✅ 显示' : '❌ 未显示'}`);
      console.log(`扫描结果: ${hasResults ? '✅ 成功' : '❌ 失败'}`);
    }

    // 测试评测功能
    console.log('\n📊 测试评测功能...');
    const evalButton = await page.$('button:has-text("开始评测")');
    if (evalButton) {
      await evalButton.click();
      await page.waitForTimeout(5000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      const hasEvalResults = resultContent.includes('评测结果') && resultContent.includes('ANY') && resultContent.includes('WEIGHTED');

      console.log(`评测功能: ${hasEvalResults ? '✅ 成功' : '❌ 失败'}`);

      if (hasEvalResults) {
        console.log('✅ 策略对比评测正常工作');
      }
    }

  } catch (error) {
    console.error('❌ 真实URL测试失败:', error);
  } finally {
    await browser.close();
  }
})();