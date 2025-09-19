import { chromium } from 'playwright';

(async () => {
  console.log('🧪 测试新架构功能...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    const consoleMessages = [];
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push(text);
      console.log(`[控制台] ${text}`);
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
    });

    // 清除缓存并访问应用
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 检查应用初始化状态
    console.log('\n📊 应用状态检查:');
    const hasConsoleMessages = consoleMessages.length > 0;
    const hasInitMessages = consoleMessages.some(msg => msg.includes('初始化'));
    const hasDataLoadMessages = consoleMessages.some(msg => msg.includes('数据源'));

    console.log(`控制台消息: ${hasConsoleMessages ? '✅' : '❌'}`);
    console.log(`初始化消息: ${hasInitMessages ? '✅' : '❌'}`);
    console.log(`数据加载消息: ${hasDataLoadMessages ? '✅' : '❌'}`);

    // 检查元素
    console.log('\n🔍 元素检查:');
    const hasUrlsTextarea = await page.$('#urls') !== null;
    const hasThresholdSlider = await page.$('#threshold') !== null;
    const hasScanButton = await page.$('button:has-text("开始扫描")') !== null;
    const hasEvalButton = await page.$('button:has-text("开始评测")') !== null;
    const hasRulesContainer = await page.$('#rules') !== null;
    const hasModelsContainer = await page.$('#models') !== null;

    console.log(`URL输入框: ${hasUrlsTextarea ? '✅' : '❌'}`);
    console.log(`阈值滑块: ${hasThresholdSlider ? '✅' : '❌'}`);
    console.log(`扫描按钮: ${hasScanButton ? '✅' : '❌'}`);
    console.log(`评测按钮: ${hasEvalButton ? '✅' : '❌'}`);
    console.log(`规则容器: ${hasRulesContainer ? '✅' : '❌'}`);
    console.log(`模型容器: ${hasModelsContainer ? '✅' : '❌'}`);

    // 检查函数可用性
    console.log('\n🔧 函数可用性检查:');
    const functionCheck = await page.evaluate(() => {
      return {
        AppController: typeof window.AppController === 'object',
        ModalManager: typeof window.ModalManager === 'object',
        Utils: typeof window.Utils === 'object',
        runScan: typeof window.AppController?.runScan === 'function',
        runEval: typeof window.AppController?.runEval === 'function',
        showRuleDescription: typeof window.ModalManager?.showRuleDescription === 'function'
      };
    });

    Object.entries(functionCheck).forEach(([func, available]) => {
      console.log(`${func}: ${available ? '✅' : '❌'}`);
    });

    // 测试基本交互
    console.log('\n🖱️ 基本交互测试:');

    // 测试阈值滑块
    if (hasThresholdSlider) {
      await page.fill('#urls', 'https://www.baidu.com');
      await page.click('#threshold', { position: { x: 50, y: 10 } });
      await page.waitForTimeout(500);
      const thresholdValue = await page.$eval('#threshold-value', el => el.textContent);
      console.log(`阈值滑块: ${thresholdValue !== '0.50' ? '✅' : '⚠️'}`);
    }

    // 测试规则和模型是否加载
    const rulesContent = await page.$eval('#rules', el => el.innerHTML);
    const modelsContent = await page.$eval('#models', el => el.innerHTML);
    const hasRulesData = !rulesContent.includes('加载中');
    const hasModelsData = !modelsContent.includes('加载中');

    console.log(`规则数据加载: ${hasRulesData ? '✅' : '❌'}`);
    console.log(`模型数据加载: ${hasModelsData ? '✅' : '❌'}`);

    // 如果函数可用，测试扫描功能
    if (functionCheck.runScan && hasScanButton) {
      console.log('\n🔍 测试扫描功能...');
      try {
        await page.click('button:has-text("开始扫描")');
        await page.waitForTimeout(3000);

        const resultContent = await page.$eval('#result', el => el.innerHTML);
        const hasResults = !resultContent.includes('请输入URL并点击');
        console.log(`扫描功能: ${hasResults ? '✅' : '❌'}`);
      } catch (error) {
        console.log(`扫描功能测试失败: ${error.message}`);
      }
    }

    // 测试弹窗功能
    if (functionCheck.showRuleDescription) {
      console.log('\n🪟 测试弹窗功能...');
      try {
        // 查找规则帮助按钮
        const helpButtons = await page.$$('.help-btn');
        if (helpButtons.length > 0) {
          await helpButtons[0].click();
          await page.waitForTimeout(1000);

          const modalVisible = await page.evaluate(() => {
            const modal = document.getElementById('descriptionModal');
            return modal && modal.classList.contains('active');
          });
          console.log(`弹窗显示: ${modalVisible ? '✅' : '❌'}`);

          if (modalVisible) {
            // 关闭弹窗
            await page.click('.modal-close');
            await page.waitForTimeout(500);
          }
        } else {
          console.log('弹窗: ⚠️ 未找到帮助按钮');
        }
      } catch (error) {
        console.log(`弹窗功能测试失败: ${error.message}`);
      }
    }

    console.log('\n📈 测试总结:');
    const totalChecks = 15; // 总检查项数
    let passedChecks = 0;

    // 计算通过的检查
    if (hasInitMessages) passedChecks++;
    if (hasDataLoadMessages) passedChecks++;
    if (hasUrlsTextarea) passedChecks++;
    if (hasThresholdSlider) passedChecks++;
    if (hasScanButton) passedChecks++;
    if (hasEvalButton) passedChecks++;
    if (hasRulesContainer) passedChecks++;
    if (hasModelsContainer) passedChecks++;
    if (functionCheck.AppController) passedChecks++;
    if (functionCheck.ModalManager) passedChecks++;
    if (functionCheck.Utils) passedChecks++;
    if (functionCheck.runScan) passedChecks++;
    if (functionCheck.runEval) passedChecks++;
    if (hasRulesData) passedChecks++;
    if (hasModelsData) passedChecks++;

    console.log(`通过检查: ${passedChecks}/${totalChecks}`);
    console.log(`成功率: ${((passedChecks / totalChecks) * 100).toFixed(1)}%`);

    if (passedChecks >= totalChecks * 0.8) {
      console.log('🎉 新架构测试通过！');
    } else {
      console.log('⚠️ 新架构需要进一步优化');
    }

  } catch (error) {
    console.error('❌ 新架构测试失败:', error);
  } finally {
    await browser.close();
  }
})();