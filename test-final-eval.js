import { chromium } from 'playwright';

(async () => {
  console.log('🧪 最终评测功能测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
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

    // 等待应用完全初始化
    await page.waitForTimeout(2000);

    // 检查初始化状态
    const initialized = await page.evaluate(() => {
      return typeof AppState !== 'undefined' && AppState.initialized;
    });
    console.log(`[测试] 应用初始化状态: ${initialized}`);

    // 查找并点击评测按钮
    const evalButton = await page.$('button', { hasText: '开始评测' });
    if (evalButton) {
      console.log('✅ 找到评测按钮，开始点击...');

      // 点击按钮
      await evalButton.click();

      // 等待评测完成
      console.log('⏳ 等待评测结果...');
      await page.waitForTimeout(5000);

      // 检查结果
      const resultContent = await page.$eval('#result', el => el.innerHTML);
      console.log(`\n📋 评测结果长度: ${resultContent.length} 字符`);

      if (resultContent.includes('评测结果')) {
        console.log('✅ 评测功能完全正常！');

        // 检查关键指标
        const checks = {
          '评测结果标题': resultContent.includes('评测结果'),
          '准确率指标': resultContent.includes('准确率'),
          '精确率指标': resultContent.includes('精确率'),
          '召回率指标': resultContent.includes('召回率'),
          'F1分数指标': resultContent.includes('F1分数'),
          '混淆矩阵': resultContent.includes('混淆矩阵'),
          '详细结果': resultContent.includes('详细结果'),
          'ANY策略': resultContent.includes('ANY'),
          'WEIGHTED策略': resultContent.includes('WEIGHTED')
        };

        console.log('\n📊 功能检查结果:');
        Object.entries(checks).forEach(([feature, passed]) => {
          console.log(`${passed ? '✅' : '❌'} ${feature}`);
        });

        const allPassed = Object.values(checks).every(passed => passed);
        if (allPassed) {
          console.log('\n🎉 所有功能检查通过！评测界面修复成功！');
        } else {
          console.log('\n⚠️  部分功能仍需完善');
        }

      } else {
        console.log('❌ 评测功能仍不正常');
        console.log('结果预览:', resultContent.substring(0, 200));
      }

    } else {
      console.log('❌ 未找到评测按钮');
    }

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();