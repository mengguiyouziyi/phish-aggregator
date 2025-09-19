const { chromium } = require('playwright');

(async () => {
  console.log('🔍 详细功能测试...');

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
      console.log(`[错误堆栈] ${error.stack}`);
    });

    // 等待页面完全加载
    await page.waitForTimeout(10000);

    // 检查页面是否加载完成
    const pageReady = await page.evaluate(() => {
      return document.readyState === 'complete';
    });
    console.log(`页面加载状态: ${pageReady ? '✅ 完成' : '❌ 未完成'}`);

    // 检查函数定义
    console.log('\n📝 检查脚本加载情况...');
    const scriptTags = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script');
      return Array.from(scripts).map((script, index) => {
        return {
          index: index,
          hasContent: script.textContent.length > 0,
          contentLength: script.textContent.length,
          hasSrc: script.src !== '',
          src: script.src
        };
      });
    });

    console.log('脚本标签统计:');
    scriptTags.forEach(script => {
      console.log(`  脚本${script.index}: 内容长度=${script.contentLength}, 有外部源=${script.hasSrc}`);
    });

    // 检查页面内容
    console.log('\n🔍 检查页面内容...');
    const pageContent = await page.content();
    const hasFunctionDefinitions = pageContent.includes('window.runScan = async function');
    const hasGlobalFix = pageContent.includes('全局函数修复脚本');
    const hasLoadSources = pageContent.includes('loadSources()');

    console.log(`包含函数定义: ${hasFunctionDefinitions ? '✅' : '❌'}`);
    console.log(`包含全局修复: ${hasGlobalFix ? '✅' : '❌'}`);
    console.log(`包含loadSources: ${hasLoadSources ? '✅' : '❌'}`);

    // 尝试直接执行JavaScript
    console.log('\n🧪 直接执行JavaScript测试...');
    try {
      const directResult = await page.evaluate(() => {
        // 尝试直接定义函数
        window.testFunction = function() {
          return '测试函数执行成功';
        };
        return window.testFunction();
      });
      console.log(`直接执行结果: ${directResult}`);
    } catch (error) {
      console.log(`直接执行失败: ${error.message}`);
    }

    // 检查我们定义的测试函数是否可用
    const testFunctionAvailable = await page.evaluate(() => {
      return typeof window.testFunction === 'function';
    });
    console.log(`测试函数可用性: ${testFunctionAvailable ? '✅' : '❌'}`);

    // 检查页面控制台消息
    console.log('\n📊 控制台消息分析:');
    const fixMessages = consoleMessages.filter(msg => msg.includes('🔧'));
    const successMessages = consoleMessages.filter(msg => msg.includes('✅'));
    const loadMessages = consoleMessages.filter(msg => msg.includes('加载') || msg.includes('load'));

    console.log(`修复相关消息: ${fixMessages.length} 条`);
    console.log(`成功相关消息: ${successMessages.length} 条`);
    console.log(`加载相关消息: ${loadMessages.length} 条`);

    if (fixMessages.length > 0) {
      console.log('修复消息:');
      fixMessages.forEach(msg => console.log(`  ${msg}`));
    }

    // 最后尝试手动触发点击事件
    console.log('\n🖱️ 测试按钮点击...');
    try {
      await page.click('button:has-text("开始扫描")');
      await page.waitForTimeout(2000);
      console.log('按钮点击执行完成');
    } catch (error) {
      console.log(`按钮点击失败: ${error.message}`);
    }

  } catch (error) {
    console.error('❌ 详细测试失败:', error);
  } finally {
    await browser.close();
  }
})();