import { chromium } from 'playwright';

(async () => {
  console.log('🔍 调试评测执行过程...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息
    page.on('console', msg => {
      console.log(`[控制台 ${msg.type()}] ${msg.text()}`);
    });

    page.on('pageerror', error => {
      console.error(`❌ 页面错误: ${error.message}`);
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

    // 检查应用状态
    const appState = await page.evaluate(() => {
      return {
        initialized: typeof AppController !== 'undefined' ? AppController.initialized : 'undefined',
        loading: typeof AppController !== 'undefined' ? AppController.loading : 'undefined',
        sources: typeof AppController !== 'undefined' ? Object.keys(AppController.sources || {}) : 'undefined'
      };
    });
    console.log(`[调试] AppController状态:`, appState);

    // 手动触发事件绑定
    await page.evaluate(() => {
      if (typeof AppController !== 'undefined') {
        AppController.bindEventListeners();
      }
    });

    // 等待一下
    await page.waitForTimeout(1000);

    // 直接调用runEval函数并监控执行过程
    console.log('\n🔍 直接调用AppController.runEval()...');
    const evalResult = await page.evaluate(async () => {
      const result = {
        success: false,
        error: null,
        urlsCount: 0,
        hasUrls: false,
        appLoading: false,
        buttonFound: false
      };

      try {
        // 检查状态
        result.appLoading = typeof AppController !== 'undefined' ? AppController.loading : false;

        // 检查URL输入
        const urlsTextarea = document.getElementById('urls');
        if (urlsTextarea) {
          const urls = urlsTextarea.value.split('\n').map(x => x.trim()).filter(Boolean);
          result.urlsCount = urls.length;
          result.hasUrls = urls.length > 0;
        }

        // 检查按钮
        const buttons = Array.from(document.querySelectorAll('button'));
        const evalButton = buttons.find(btn => btn.textContent.includes('开始评测'));
        result.buttonFound = !!evalButton;

        // 执行评测
        if (typeof AppController !== 'undefined') {
          await AppController.runEval();
          result.success = true;
        } else {
          result.error = 'AppController未定义';
        }

      } catch (error) {
        result.error = error.message;
        result.success = false;
      }

      return result;
    });

    console.log(`[调试] 评测执行结果:`, evalResult);

    // 等待评测完成
    console.log('\n⏳ 等待评测结果...');
    await page.waitForTimeout(5000);

    // 检查最终结果
    const finalResult = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 最终结果长度: ${finalResult.length} 字符`);

    if (finalResult.includes('评测结果')) {
      console.log('✅ 评测成功！');
    } else {
      console.log('❌ 评测失败');

      // 检查是否显示了通知
      const notifications = await page.$$('.notification');
      console.log(`[调试] 页面上的通知数量: ${notifications.length}`);

      if (notifications.length > 0) {
        const notificationText = await notifications[0].textContent();
        console.log(`[调试] 通知内容: ${notificationText}`);
      }
    }

  } catch (error) {
    console.error('❌ 调试失败:', error);
  } finally {
    await browser.close();
  }
})();