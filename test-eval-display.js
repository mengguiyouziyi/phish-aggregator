import { chromium } from 'playwright';

(async () => {
  console.log('🧪 测试评测结果显示...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台消息
    page.on('console', msg => {
      if (msg.text().includes('评测') || msg.text().includes('指标') || msg.text().includes('NaN')) {
        console.log(`[控制台] ${msg.text()}`);
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

    // 选择一个规则
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
    await page.waitForTimeout(15000);

    // 检查评测结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 评测结果区域内容长度: ${resultContent.length} 字符`);

    if (resultContent.includes('评测结果')) {
      console.log('✅ 评测结果标题显示正常');

      // 检查是否有NaN值
      if (resultContent.includes('NaN')) {
        console.log('❌ 仍存在NaN值');
      } else {
        console.log('✅ 没有NaN值');
      }

      // 检查是否有指标数据
      if (resultContent.includes('准确率') && resultContent.includes('精确率') && resultContent.includes('召回率')) {
        console.log('✅ 评测指标显示正常');
      } else {
        console.log('❌ 评测指标显示异常');
      }

      // 检查是否有混淆矩阵
      if (resultContent.includes('混淆矩阵详情') && resultContent.includes('TP') && resultContent.includes('TN')) {
        console.log('✅ 混淆矩阵显示正常');
      } else {
        console.log('❌ 混淆矩阵显示异常');
      }

      // 检查是否有详细结果
      if (resultContent.includes('详细结果') && resultContent.includes('ANY策略') && resultContent.includes('WEIGHTED策略')) {
        console.log('✅ 详细结果显示正常');
      } else {
        console.log('❌ 详细结果显示异常');
      }

      // 提取并显示关键指标
      const accuracyMatch = resultContent.match(/(\d+\.\d+)%/g);
      if (accuracyMatch && accuracyMatch.length > 0) {
        console.log(`📊 检测到的指标值: ${accuracyMatch.slice(0, 4).join(', ')}`);
      }

    } else {
      console.log('❌ 评测结果未显示');
    }

    console.log('\n🎉 评测显示测试完成！');

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();