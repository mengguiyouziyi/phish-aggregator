import { chromium } from 'playwright';

(async () => {
  console.log('🧪 URLTran集成测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台消息
    page.on('console', msg => {
      if (msg.text().includes('✅') || msg.text().includes('❌') || msg.text().includes('URLTran')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 检查URLTran是否在模型列表中
    console.log('\n🔍 检查URLTran模型加载状态...');

    const modelCheckboxes = await page.$$('input[name="model"]');
    console.log(`发现 ${modelCheckboxes.length} 个模型选项`);

    let urltranFound = false;
    for (const checkbox of modelCheckboxes) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, checkbox);
      if (label.includes('URLTran')) {
        urltranFound = true;
        console.log('✅ URLTran模型在UI中显示');
        break;
      }
    }

    if (!urltranFound) {
      console.log('❌ URLTran模型未在UI中显示');
      return;
    }

    // 输入测试URLs
    console.log('\n📝 输入测试URLs...');
    const testUrls = [
      'https://www.google.com',
      'https://www.microsoft.com',
      'https://github.com'
    ];

    await page.fill('#urls', testUrls.join('\n'));
    console.log(`✅ 已输入 ${testUrls.length} 个测试URL`);

    // 选择URLTran模型
    console.log('\n🤖 选择URLTran模型...');
    for (const checkbox of modelCheckboxes) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, checkbox);
      if (label.includes('URLTran')) {
        await checkbox.check();
        console.log('✅ 已选择URLTran模型');
        break;
      }
    }

    // 选择一个规则
    const ruleCheckboxes = await page.$$('input[name="rule"]');
    if (ruleCheckboxes.length > 0) {
      await ruleCheckboxes[0].check();
      console.log('✅ 已选择一个规则');
    }

    // 使用ANY策略进行测试
    console.log('\n⚡ 使用ANY策略测试URLTran...');
    await page.click('input[value="any"]');

    // 开始扫描
    console.log('\n🔍 开始扫描测试...');
    await page.evaluate(() => {
      const scanButton = Array.from(document.querySelectorAll('button')).find(btn =>
        btn.textContent.includes('开始扫描')
      );
      if (scanButton) {
        scanButton.click();
      }
    });

    // 等待扫描完成
    console.log('⏳ 等待扫描结果...');
    await page.waitForTimeout(5000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 结果区域内容长度: ${resultContent.length} 字符`);

    if (resultContent.includes('URLTran') || resultContent.includes('urltran')) {
      console.log('✅ URLTran模型成功参与扫描');

      // 检查是否有具体的结果数据
      const hasResults = resultContent.includes('检测结果统计') && resultContent.includes('URL');
      console.log(`扫描结果: ${hasResults ? '✅ 成功' : '❌ 失败'}`);

      if (hasResults) {
        // 分析结果
        const totalMatches = (resultContent.match(/总计: \d+ 个URL/g) || [])[0] || '';
        const phishingMatches = (resultContent.match(/钓鱼: \d+ 个/g) || [])[0] || '';
        const legitMatches = (resultContent.match(/正常: \d+ 个/g) || [])[0] || '';

        console.log(`扫描结果: ${totalMatches} | ${phishingMatches} | ${legitMatches}`);
      }
    } else {
      console.log('⚠️ URLTran模型可能未参与扫描或结果未显示');
    }

    console.log('\n🎉 URLTran集成测试完成！');

  } catch (error) {
    console.error('❌ URLTran集成测试失败:', error);
  } finally {
    await browser.close();
  }
})();