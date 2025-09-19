const { chromium } = require('playwright');

(async () => {
  console.log('🔍 检查当前函数状态...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 访问应用
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // 监听控制台
    page.on('console', msg => {
      if (msg.text().includes('✅') || msg.text().includes('🔧') || msg.text().includes('⚠️')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    // 等待页面加载
    await page.waitForTimeout(3000);

    // 检查关键函数
    const functionCheck = await page.evaluate(() => {
      return {
        showDescription: typeof window.showDescription === 'function',
        showStrategyDescription: typeof window.showStrategyDescription === 'function',
        getChecked: typeof window.getChecked === 'function',
        runScan: typeof window.runScan === 'function',
        renderScan: typeof window.renderScan === 'function',
        getCurrentStrategy: typeof window.getCurrentStrategy === 'function',
        getStrategyExplanation: typeof window.getStrategyExplanation === 'function',
        descriptions: typeof window.descriptions !== 'undefined'
      };
    });

    console.log('📊 函数状态检查:');
    Object.entries(functionCheck).forEach(([func, exists]) => {
      console.log(`  ${func}: ${exists ? '✅' : '❌'}`);
    });

    // 检查descriptions数据
    const descriptionsCheck = await page.evaluate(() => {
      if (window.descriptions) {
        return {
          hasRules: !!window.descriptions['规则源'],
          hasModels: !!window.descriptions['模型'],
          sampleRule: window.descriptions['规则源'] ? Object.keys(window.descriptions['规则源'])[0] : null
        };
      }
      return null;
    });

    if (descriptionsCheck) {
      console.log('\n📋 Descriptions 数据检查:');
      console.log(`  包含规则源: ${descriptionsCheck.hasRules}`);
      console.log(`  包含模型: ${descriptionsCheck.hasModels}`);
      console.log(`  示例规则: ${descriptionsCheck.sampleRule}`);
    }

    // 检查原始showDescription函数是否能正常工作
    console.log('\n🪟 测试原始showDescription函数...');
    const hasOriginalShowDescription = await page.evaluate(() => {
      return typeof window.showDescription === 'function' &&
             window.showDescription.toString().includes('descriptions[type]');
    });

    console.log(`原始showDescription函数: ${hasOriginalShowDescription ? '✅ 正常' : '❌ 异常'}`);

  } catch (error) {
    console.error('❌ 检查失败:', error);
  } finally {
    await browser.close();
  }
})();