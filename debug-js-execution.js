import { chromium } from 'playwright';

(async () => {
  console.log('🔍 调试JavaScript执行问题...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台消息
    page.on('console', msg => {
      if (msg.text().includes('按钮') || msg.text().includes('绑定') || msg.text().includes('错误')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });

    // 等待JavaScript初始化完成
    await page.waitForTimeout(3000);

    // 检查AppController是否已加载
    const appControllerLoaded = await page.evaluate(() => {
      return typeof AppController !== 'undefined';
    });
    console.log(`[调试] AppController已加载: ${appControllerLoaded}`);

    // 检查AppController.init是否已执行
    const appInitialized = await page.evaluate(() => {
      return typeof AppController !== 'undefined' && AppController.initialized;
    });
    console.log(`[调试] AppController已初始化: ${appInitialized}`);

    // 检查bindEventListeners是否已执行
    const eventListenersBound = await page.evaluate(() => {
      // 查找页面上的所有按钮
      const buttons = Array.from(document.querySelectorAll('button'));
      const evalButton = buttons.find(btn => btn.textContent.includes('开始评测'));
      return evalButton ? evalButton.onclick : null;
    });
    console.log(`[调试] 评测按钮onclick函数: ${eventListenersBound}`);

    // 手动触发事件绑定
    console.log('\n🔧 手动触发事件绑定...');
    await page.evaluate(() => {
      if (typeof AppController !== 'undefined') {
        console.log('手动调用AppController.bindEventListeners()');
        AppController.bindEventListeners();
      }
    });

    // 等待一下
    await page.waitForTimeout(1000);

    // 再次检查按钮状态
    const afterBinding = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const evalButton = buttons.find(btn => btn.textContent.includes('开始评测'));
      return {
        onclickAttr: evalButton ? evalButton.getAttribute('onclick') : null,
        hasListener: evalButton && evalButton.onclick !== null
      };
    });
    console.log(`[调试] 手动绑定后状态:`, afterBinding);

    // 测试按钮点击
    console.log('\n🧪 测试按钮点击...');
    const evalButton = await page.$('button', { hasText: '开始评测' });
    if (evalButton) {
      await evalButton.click();
      console.log('✅ 按钮点击成功');

      // 等待评测结果
      await page.waitForTimeout(3000);

      const resultContent = await page.$eval('#result', el => el.innerHTML);
      if (resultContent.includes('评测结果')) {
        console.log('✅ 评测功能正常工作！');
      } else {
        console.log('❌ 评测功能仍未工作');
      }
    } else {
      console.log('❌ 未找到评测按钮');
    }

  } catch (error) {
    console.error('❌ 调试失败:', error);
  } finally {
    await browser.close();
  }
})();