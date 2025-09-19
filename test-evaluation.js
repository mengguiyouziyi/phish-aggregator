import { chromium } from 'playwright';

(async () => {
  console.log('🧪 评测功能测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    page.on('console', msg => {
      console.log(`[控制台] ${msg.text()}`);
    });

    page.on('pageerror', error => {
      console.log(`[页面错误] ${error.message}`);
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    console.log('\n🔍 检查评测功能...');

    // 查找评测按钮
    const evalButton = await page.$('button:has-text("开始评测")');
    if (!evalButton) {
      console.log('❌ 未找到评测按钮');
      return;
    }

    console.log('✅ 找到评测按钮');

    // 点击评测按钮
    console.log('\n📊 点击评测按钮...');
    await evalButton.click();
    await page.waitForTimeout(3000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`结果区域内容长度: ${resultContent.length} 字符`);

    if (resultContent.includes('错误') || resultContent.includes('Error')) {
      console.log('❌ 评测过程中出现错误');
      console.log('错误内容:', resultContent.substring(0, 200));
    } else if (resultContent.includes('评测结果')) {
      console.log('✅ 评测功能正常工作');
    } else {
      console.log('⚠️ 评测功能无响应或结果异常');
    }

  } catch (error) {
    console.error('❌ 评测测试失败:', error);
  } finally {
    await browser.close();
  }
})();