import { chromium } from 'playwright';

(async () => {
  console.log('🧪 完整弹窗功能测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    page.on('console', msg => {
      if (msg.text().includes('✅') || msg.text().includes('❌') || msg.text().includes('🚀') ||
          msg.text().includes('📋') || msg.text().includes('未找到')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
    });

    // 清除缓存并访问应用
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    console.log('\n🪟 测试所有弹窗功能...');

    // 测试所有规则帮助按钮
    console.log('\n📋 测试规则说明弹窗:');
    const ruleHelpButtons = await page.$$('#rules .help-btn');
    console.log(`发现 ${ruleHelpButtons.length} 个规则帮助按钮`);

    let ruleSuccessCount = 0;
    for (let i = 0; i < Math.min(ruleHelpButtons.length, 3); i++) {
      try {
        console.log(`\n--- 测试规则 ${i + 1} ---`);

        // 点击帮助按钮
        await ruleHelpButtons[i].click();
        await page.waitForTimeout(1000);

        // 检查弹窗是否显示
        const modalVisible = await page.evaluate(() => {
          const modal = document.getElementById('descriptionModal');
          return modal && modal.classList.contains('active');
        });

        if (modalVisible) {
          console.log(`规则 ${i + 1} 弹窗: ✅ 显示成功`);

          // 获取弹窗内容
          const modalTitle = await page.$eval('#modalTitle', el => el.textContent);
          const modalBody = await page.$eval('#modalBody', el => el.innerHTML);

          console.log(`标题: ${modalTitle}`);

          // 检查是否有真实内容
          const hasRealContent = modalBody.includes('概述') ||
                               modalBody.includes('特性') ||
                               modalBody.includes('技术细节') ||
                               modalBody.length > 100;

          console.log(`内容质量: ${hasRealContent ? '✅ 详细内容' : '❌ 简单内容'}`);
          console.log(`内容长度: ${modalBody.length} 字符`);

          ruleSuccessCount++;

          // 关闭弹窗
          await page.click('.modal-close');
          await page.waitForTimeout(500);
        } else {
          console.log(`规则 ${i + 1} 弹窗: ❌ 未显示`);
        }
      } catch (error) {
        console.log(`规则 ${i + 1} 测试失败: ${error.message}`);
      }
    }

    // 测试所有模型帮助按钮
    console.log('\n🧠 测试模型说明弹窗:');
    const modelHelpButtons = await page.$$('#models .help-btn');
    console.log(`发现 ${modelHelpButtons.length} 个模型帮助按钮`);

    let modelSuccessCount = 0;
    for (let i = 0; i < Math.min(modelHelpButtons.length, 3); i++) {
      try {
        console.log(`\n--- 测试模型 ${i + 1} ---`);

        // 点击帮助按钮
        await modelHelpButtons[i].click();
        await page.waitForTimeout(1000);

        // 检查弹窗是否显示
        const modalVisible = await page.evaluate(() => {
          const modal = document.getElementById('descriptionModal');
          return modal && modal.classList.contains('active');
        });

        if (modalVisible) {
          console.log(`模型 ${i + 1} 弹窗: ✅ 显示成功`);

          // 获取弹窗内容
          const modalTitle = await page.$eval('#modalTitle', el => el.textContent);
          const modalBody = await page.$eval('#modalBody', el => el.innerHTML);

          console.log(`标题: ${modalTitle}`);

          // 检查是否有真实内容
          const hasRealContent = modalBody.includes('概述') ||
                               modalBody.includes('特性') ||
                               modalBody.includes('技术细节') ||
                               modalBody.includes('模型') ||
                               modalBody.length > 100;

          console.log(`内容质量: ${hasRealContent ? '✅ 详细内容' : '❌ 简单内容'}`);
          console.log(`内容长度: ${modalBody.length} 字符`);

          modelSuccessCount++;

          // 关闭弹窗
          await page.click('.modal-close');
          await page.waitForTimeout(500);
        } else {
          console.log(`模型 ${i + 1} 弹窗: ❌ 未显示`);
        }
      } catch (error) {
        console.log(`模型 ${i + 1} 测试失败: ${error.message}`);
      }
    }

    // 测试策略说明按钮
    console.log('\n🎯 测试策略说明弹窗:');
    const strategyHelpButton = await page.$('button[onclick*="showStrategyDescription"]');

    if (strategyHelpButton) {
      console.log('找到策略说明按钮，开始测试...');

      // 测试ANY策略说明
      await page.evaluate(() => {
        window.ModalManager.showStrategyDescription('any');
      });
      await page.waitForTimeout(1000);

      let modalVisible = await page.evaluate(() => {
        const modal = document.getElementById('descriptionModal');
        return modal && modal.classList.contains('active');
      });

      if (modalVisible) {
        console.log('ANY策略弹窗: ✅ 显示成功');

        const modalTitle = await page.$eval('#modalTitle', el => el.textContent);
        const modalBody = await page.$eval('#modalBody', el => el.innerHTML);

        console.log(`标题: ${modalTitle}`);
        console.log(`内容长度: ${modalBody.length} 字符`);

        // 关闭弹窗
        await page.click('.modal-close');
        await page.waitForTimeout(500);
      } else {
        console.log('ANY策略弹窗: ❌ 未显示');
      }

      // 测试WEIGHTED策略说明
      await page.evaluate(() => {
        window.ModalManager.showStrategyDescription('weighted');
      });
      await page.waitForTimeout(1000);

      modalVisible = await page.evaluate(() => {
        const modal = document.getElementById('descriptionModal');
        return modal && modal.classList.contains('active');
      });

      if (modalVisible) {
        console.log('WEIGHTED策略弹窗: ✅ 显示成功');

        const modalTitle = await page.$eval('#modalTitle', el => el.textContent);
        const modalBody = await page.$eval('#modalBody', el => el.innerHTML);

        console.log(`标题: ${modalTitle}`);
        console.log(`内容长度: ${modalBody.length} 字符`);

        // 关闭弹窗
        await page.click('.modal-close');
        await page.waitForTimeout(500);
      } else {
        console.log('WEIGHTED策略弹窗: ❌ 未显示');
      }
    } else {
      console.log('❌ 未找到策略说明按钮');
    }

    // 总结
    console.log('\n📊 弹窗测试总结:');
    console.log(`规则弹窗测试: ${ruleSuccessCount}/${Math.min(ruleHelpButtons.length, 3)} 成功`);
    console.log(`模型弹窗测试: ${modelSuccessCount}/${Math.min(modelHelpButtons.length, 3)} 成功`);

    const totalTested = Math.min(ruleHelpButtons.length, 3) + Math.min(modelHelpButtons.length, 3) + 2; // +2 for strategies
    const totalSuccess = ruleSuccessCount + modelSuccessCount + (strategyHelpButton ? 2 : 0);
    const successRate = ((totalSuccess / totalTested) * 100).toFixed(1);

    console.log(`总体成功率: ${successRate}% (${totalSuccess}/${totalTested})`);

    if (successRate >= 70) {
      console.log('🎉 弹窗功能测试通过！');
    } else {
      console.log('⚠️ 弹窗功能需要进一步优化');
    }

  } catch (error) {
    console.error('❌ 弹窗测试失败:', error);
  } finally {
    await browser.close();
  }
})();