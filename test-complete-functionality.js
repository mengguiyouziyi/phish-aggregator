import { chromium } from 'playwright';

(async () => {
  console.log('🧪 完整功能测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    page.on('console', msg => {
      if (msg.text().includes('✅') || msg.text().includes('❌') || msg.text().includes('🚀')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`[错误] ${error.message}`);
    });

    // 清除缓存并访问应用
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 测试1: 扫描功能
    console.log('\n🔍 测试1: 扫描功能');
    await page.fill('#urls', 'https://www.baidu.com\nhttps://www.google.com');

    // 选择一些规则
    const ruleCheckboxes = await page.$$('input[name="rule"]');
    if (ruleCheckboxes.length > 0) {
      await ruleCheckboxes[0].check();
      await ruleCheckboxes[1].check();
      console.log('已选择前两个规则');
    }

    // 点击扫描按钮
    const scanButton = await page.$('button:has-text("开始扫描")');
    if (scanButton) {
      await scanButton.click();
      await page.waitForTimeout(3000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      const hasScanResults = resultContent.includes('检测结果统计') || resultContent.includes('URL');
      console.log(`扫描功能: ${hasScanResults ? '✅ 成功' : '❌ 失败'}`);

      if (hasScanResults) {
        console.log('✅ 扫描结果正常显示');
      }
    } else {
      console.log('❌ 未找到扫描按钮');
    }

    // 测试2: 弹窗功能
    console.log('\n🪟 测试2: 弹窗功能');

    // 查找模型帮助按钮
    const helpButtons = await page.$$('.help-btn');
    if (helpButtons.length > 0) {
      await helpButtons[0].click();
      await page.waitForTimeout(1000);

      const modalVisible = await page.evaluate(() => {
        const modal = document.getElementById('descriptionModal');
        return modal && modal.classList.contains('active');
      });

      if (modalVisible) {
        console.log('✅ 弹窗正常显示');

        // 检查弹窗内容
        const modalTitle = await page.$eval('#modalTitle', el => el.textContent);
        const modalBody = await page.$eval('#modalBody', el => el.innerHTML);
        const hasRealContent = modalBody.includes('概述') || modalBody.includes('特性') || modalBody.includes('技术细节');

        console.log(`弹窗标题: ${modalTitle}`);
        console.log(`弹窗内容: ${hasRealContent ? '✅ 真实内容' : '❌ 占位符'}`);

        // 关闭弹窗
        await page.click('.modal-close');
        await page.waitForTimeout(500);
      } else {
        console.log('❌ 弹窗未显示');
      }
    } else {
      console.log('❌ 未找到帮助按钮');
    }

    // 测试3: 评测功能
    console.log('\n📊 测试3: 评测功能');

    const evalButton = await page.$('button:has-text("开始评测")');
    if (evalButton) {
      await evalButton.click();
      await page.waitForTimeout(3000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      const hasEvalResults = resultContent.includes('评测结果') || resultContent.includes('ANY') || resultContent.includes('WEIGHTED');
      console.log(`评测功能: ${hasEvalResults ? '✅ 成功' : '❌ 失败'}`);

      if (hasEvalResults) {
        console.log('✅ 评测结果正常显示');
      }
    } else {
      console.log('❌ 未找到评测按钮');
    }

    // 测试4: 策略差异
    console.log('\n🎯 测试4: 策略差异显示');

    // 切换到WEIGHTED策略
    await page.click('input[value="weighted"]');
    await page.waitForTimeout(500);

    if (scanButton) {
      await scanButton.click();
      await page.waitForTimeout(3000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      const showsWeighted = resultContent.includes('WEIGHTED');
      const showsStrategyExplanation = resultContent.includes('概率加权');

      console.log(`WEIGHTED策略显示: ${showsWeighted ? '✅' : '❌'}`);
      console.log(`策略说明显示: ${showsStrategyExplanation ? '✅' : '❌'}`);
    }

    // 测试5: 界面响应性
    console.log('\n📱 测试5: 界面响应性');

    // 测试阈值滑块
    await page.click('#threshold', { position: { x: 100, y: 10 } });
    await page.waitForTimeout(500);
    const thresholdValue = await page.$eval('#threshold-value', el => el.textContent);
    console.log(`阈值调整: ${thresholdValue !== '0.50' ? '✅' : '⚠️ 默认值'}`);

    // 测试策略切换
    await page.click('input[value="any"]');
    await page.waitForTimeout(300);
    const anySelected = await page.$eval('input[value="any"]', el => el.checked);
    console.log(`策略切换: ${anySelected ? '✅' : '❌'}`);

    console.log('\n🎉 完整功能测试完成！');

  } catch (error) {
    console.error('❌ 完整功能测试失败:', error);
  } finally {
    await browser.close();
  }
})();