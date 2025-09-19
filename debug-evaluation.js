import { chromium } from 'playwright';

(async () => {
  console.log('🔍 评测功能调试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    page.on('console', msg => {
      if (msg.text().includes('错误') || msg.text().includes('Error') || msg.text().includes('评测')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
      if (error.stack) {
        console.log(`[错误堆栈] ${error.stack}`);
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 点击评测按钮
    await page.evaluate(() => {
      const evalButton = Array.from(document.querySelectorAll('button')).find(btn =>
        btn.textContent.includes('开始评测')
      );
      if (evalButton) {
        evalButton.click();
      }
    });

    await page.waitForTimeout(3000);

    // 获取结果区域内容
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log('\n📋 结果区域内容:');
    console.log(resultContent);

    // 检查是否有JavaScript错误
    const consoleErrors = await page.evaluate(() => {
      return window.consoleErrors || [];
    });
    console.log('\n🚨 控制台错误:', consoleErrors);

  } catch (error) {
    console.error('❌ 调试失败:', error);
  } finally {
    await browser.close();
  }
})();