const { chromium } = require('playwright');

(async () => {
  console.log('🧪 基础测试 - 检查页面错误...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    const allMessages = [];
    page.on('console', msg => {
      const text = msg.text();
      allMessages.push(text);
      console.log(`[控制台] ${text}`);
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
      if (error.stack) {
        console.log(`[错误堆栈] ${error.stack}`);
      }
    });

    page.on('requestfailed', request => {
      console.log(`[请求失败] ${request.url()}: ${request.failure().errorText}`);
    });

    // 访问应用
    await page.goto('http://localhost:8000');

    // 等待页面加载
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);

    // 检查基本元素
    console.log('\n📋 基本元素检查:');
    const scanButton = await page.$('button[onclick="runScan()"]');
    const evalButton = await page.$('button:has-text("开始评测")');
    const helpButton = await page.$('.help-btn');

    console.log(`扫描按钮: ${scanButton ? '✅' : '❌'}`);
    console.log(`评测按钮: ${evalButton ? '✅' : '❌'}`);
    console.log(`帮助按钮: ${helpButton ? '✅' : '❌'}`);

    // 检查函数可用性
    console.log('\n🔧 函数可用性检查:');
    const functionCheck = await page.evaluate(() => {
      const functions = ['runScan', 'getChecked', 'showDescription'];
      const results = {};
      functions.forEach(func => {
        results[func] = typeof window[func] === 'function';
      });
      return results;
    });

    Object.entries(functionCheck).forEach(([func, available]) => {
      console.log(`${func}: ${available ? '✅' : '❌'}`);
    });

    // 尝试手动定义函数
    console.log('\n🔨 手动定义函数测试:');
    const manualDefineResult = await page.evaluate(() => {
      try {
        window.manualRunScan = async function() {
          console.log('手动runScan函数被调用');
          return '手动函数执行成功';
        };
        return '手动定义成功';
      } catch (error) {
        return `手动定义失败: ${error.message}`;
      }
    });

    console.log(`手动定义结果: ${manualDefineResult}`);

    // 检查手动定义的函数
    const manualFunctionCheck = await page.evaluate(() => {
      return typeof window.manualRunScan === 'function';
    });
    console.log(`手动函数可用性: ${manualFunctionCheck ? '✅' : '❌'}`);

    // 检查页面源码
    console.log('\n📝 页面源码检查:');
    const pageContent = await page.content();
    const hasScriptTags = pageContent.includes('<script>');
    const hasFunctionDefinitions = pageContent.includes('function runScan');
    const hasWindowAssignments = pageContent.includes('window.runScan');

    console.log(`包含script标签: ${hasScriptTags ? '✅' : '❌'}`);
    console.log(`包含function定义: ${hasFunctionDefinitions ? '✅' : '❌'}`);
    console.log(`包含window赋值: ${hasWindowAssignments ? '✅' : '❌'}`);

    // 检查script标签内容
    const scriptContent = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script');
      return Array.from(scripts).map((script, index) => {
        return {
          index: index,
          contentLength: script.textContent.length,
          hasWindowRunScan: script.textContent.includes('window.runScan'),
          hasFunctionRunScan: script.textContent.includes('function runScan'),
          hasDOMContentLoaded: script.textContent.includes('DOMContentLoaded')
        };
      });
    });

    console.log('\n📜 Script标签分析:');
    scriptContent.forEach(script => {
      console.log(`脚本${script.index}: 长度=${script.contentLength}, window.runScan=${script.hasWindowRunScan}, function runScan=${script.hasFunctionRunScan}, DOMContentLoaded=${script.hasDOMContentLoaded}`);
    });

    console.log('\n📊 消息统计:');
    console.log(`总消息数: ${allMessages.length}`);
    console.log(`错误消息: ${allMessages.filter(msg => msg.includes('Error') || msg.includes('错误')).length}`);
    console.log(`警告消息: ${allMessages.filter(msg => msg.includes('Warning') || msg.includes('警告')).length}`);
    console.log(`调试消息: ${allMessages.filter(msg => msg.includes('🔧') || msg.includes('🚀')).length}`);

  } catch (error) {
    console.error('❌ 基础测试失败:', error);
  } finally {
    await browser.close();
  }
})();