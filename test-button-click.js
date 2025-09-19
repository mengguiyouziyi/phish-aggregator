import { chromium } from 'playwright';

(async () => {
  console.log('🧪 测试按钮点击事件...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台消息
    page.on('console', msg => {
      console.log(`[控制台] ${msg.text()}`);
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 输入测试URL
    await page.fill('#urls', 'http://tjhsfk.com/\nhttps://www.google.com/\nhttps://www.baidu.com/');

    // 选择URLBERT模型
    const modelCheckboxes = await page.$$('input[name="model"]');
    for (const checkbox of modelCheckboxes) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, checkbox);
      if (label.includes('URLBERT')) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }

    // 等待应用初始化
    await page.waitForTimeout(2000);

    // 直接调用评测功能（绕过按钮点击）
    console.log('\n🔍 直接调用评测功能...');
    await page.evaluate(() => {
      if (typeof AppController !== 'undefined' && AppController.runEval) {
        console.log('开始调用AppController.runEval()...');
        AppController.runEval();
      } else {
        console.error('AppController.runEval 未找到');
      }
    });

    // 等待评测完成
    console.log('⏳ 等待评测结果...');
    await page.waitForTimeout(5000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 评测结果长度: ${resultContent.length} 字符`);

    if (resultContent.includes('评测结果')) {
      console.log('✅ 直接调用成功！评测功能正常工作');

      // 提取关键指标
      const accuracyMatch = resultContent.match(/(\d+\.?\d*)%/g);
      if (accuracyMatch) {
        console.log(`📊 检测到的指标: ${accuracyMatch.slice(0, 4).join(', ')}`);
      }

      console.log('\n🎉 结论：评测功能完全正常，问题仅在于按钮事件绑定');

    } else {
      console.log('❌ 直接调用也失败，说明评测功能本身有问题');
    }

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();