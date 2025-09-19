import { chromium } from 'playwright';

(async () => {
  console.log('🧪 测试评测按钮修复...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 输入测试URL
    const urlTextarea = await page.$('#urls');
    await urlTextarea.fill('http://tjhsfk.com/\nhttps://www.google.com/\nhttps://www.baidu.com/');

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

    // 检查按钮onclick属性
    const evalButton = await page.$('button', { hasText: '开始评测' });
    const onclickAttr = await evalButton.getAttribute('onclick');
    console.log(`[测试] 修复前按钮onclick属性: "${onclickAttr}"`);

    // 等待一下让JavaScript执行事件绑定
    await page.waitForTimeout(1000);

    // 再次检查onclick属性
    const onclickAttrAfter = await evalButton.getAttribute('onclick');
    console.log(`[测试] 修复后按钮onclick属性: "${onclickAttrAfter}"`);

    // 点击评测按钮
    console.log('\n🔍 点击评测按钮...');
    await evalButton.click();

    // 等待评测完成
    console.log('⏳ 等待评测结果...');
    await page.waitForTimeout(5000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 评测结果区域内容长度: ${resultContent.length} 字符`);

    if (resultContent.includes('评测结果') && resultContent.length > 1000) {
      console.log('✅ 评测按钮修复成功！评测功能正常工作');

      // 检查关键指标
      if (resultContent.includes('准确率') && resultContent.includes('精确率')) {
        console.log('✅ 评测指标显示正常');
      } else {
        console.log('❌ 评测指标显示异常');
      }
    } else {
      console.log('❌ 评测按钮修复失败，评测结果仍未显示');
      console.log('结果区域内容:', resultContent.substring(0, 200));
    }

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();