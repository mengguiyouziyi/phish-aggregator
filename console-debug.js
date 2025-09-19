const { chromium } = require('playwright');

(async () => {
  console.log('🔍 控制台调试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 访问应用
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // 捕获所有控制台消息
    const consoleMessages = [];
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push(text);
      console.log(`[控制台] ${text}`);
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
    });

    // 等待页面加载
    await page.waitForTimeout(5000);

    // 检查页面元素
    console.log('\n📋 检查页面元素...');
    const hasScanButton = await page.$('button:has-text("开始扫描")') !== null;
    const hasUrlInput = await page.$('#urls') !== null;
    const hasResultDiv = await page.$('#result') !== null;

    console.log(`扫描按钮: ${hasScanButton ? '✅' : '❌'}`);
    console.log(`URL输入框: ${hasUrlInput ? '✅' : '❌'}`);
    console.log(`结果区域: ${hasResultDiv ? '✅' : '❌'}`);

    // 检查函数是否可用
    console.log('\n🔧 检查函数可用性...');
    const functionCheck = await page.evaluate(() => {
      const functions = ['runScan', 'renderScan', 'runEval', 'renderEval', 'getChecked', 'showDescription', 'showStrategyDescription'];
      const results = {};

      functions.forEach(func => {
        results[func] = typeof window[func] === 'function';
      });

      return results;
    });

    console.log('函数可用性:');
    Object.entries(functionCheck).forEach(([func, available]) => {
      console.log(`  ${func}: ${available ? '✅' : '❌'}`);
    });

    // 尝试手动调用函数
    console.log('\n🧪 手动测试函数调用...');
    try {
      const manualResult = await page.evaluate(() => {
        if (typeof window.runScan === 'function') {
          window.runScan();
          return 'runScan called successfully';
        }
        return 'runScan not available';
      });
      console.log(`手动调用结果: ${manualResult}`);
    } catch (error) {
      console.log(`手动调用失败: ${error.message}`);
    }

    console.log('\n📊 控制台消息统计:');
    const errorMessages = consoleMessages.filter(msg => msg.includes('Error') || msg.includes('错误'));
    const warningMessages = consoleMessages.filter(msg => msg.includes('Warning') || msg.includes('警告'));
    const infoMessages = consoleMessages.filter(msg => msg.includes('✅') || msg.includes('🔧'));

    console.log(`错误消息: ${errorMessages.length} 条`);
    console.log(`警告消息: ${warningMessages.length} 条`);
    console.log(`信息消息: ${infoMessages.length} 条`);

    if (errorMessages.length > 0) {
      console.log('\n❌ 错误消息详情:');
      errorMessages.forEach(msg => console.log(`  ${msg}`));
    }

  } catch (error) {
    console.error('❌ 调试失败:', error);
  } finally {
    await browser.close();
  }
})();