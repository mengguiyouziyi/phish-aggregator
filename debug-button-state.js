import { chromium } from 'playwright';

(async () => {
  console.log('🔍 调试按钮状态...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 获取所有按钮的信息
    const buttonsInfo = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.map((btn, index) => ({
        index,
        text: btn.textContent.trim(),
        onclick: btn.getAttribute('onclick'),
        className: btn.className,
        parentClass: btn.parentElement ? btn.parentElement.className : null,
        hasClickListener: btn.onclick !== null
      }));
    });

    console.log('📋 页面上所有按钮的信息:');
    buttonsInfo.forEach((btn, index) => {
      console.log(`按钮 ${index}: "${btn.text}"`);
      console.log(`  onclick属性: "${btn.onclick}"`);
      console.log(`  className: ${btn.className}`);
      console.log(`  parentClass: ${btn.parentClass}`);
      console.log(`  hasClickListener: ${btn.hasClickListener}`);
      console.log('---');
    });

    // 找到评测按钮
    const evalButton = buttonsInfo.find(btn => btn.text.includes('开始评测'));
    if (evalButton) {
      console.log(`\n🎯 评测按钮详细信息:`);
      console.log(evalButton);

      // 尝试手动绑定事件
      console.log('\n🔧 尝试手动绑定事件...');
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const evalBtn = buttons.find(btn => btn.textContent.includes('开始评测'));
        if (evalBtn) {
          // 移除现有的onclick属性
          evalBtn.removeAttribute('onclick');
          // 添加点击事件监听器
          evalBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🔍 评测按钮被点击了！');
            if (typeof AppController !== 'undefined' && AppController.runEval) {
              AppController.runEval();
            } else {
              console.error('AppController.runEval 未找到');
            }
          });
          console.log('✅ 手动事件绑定完成');
        }
      });

      // 等待一下
      await page.waitForTimeout(1000);

      // 检查绑定后的状态
      const afterBinding = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const evalBtn = buttons.find(btn => btn.textContent.includes('开始评测'));
        return {
          onclick: evalBtn ? evalBtn.getAttribute('onclick') : null,
          eventListeners: evalBtn ? evalBtn.onclick : null
        };
      });
      console.log('手动绑定后状态:', afterBinding);

      // 测试点击
      console.log('\n🧪 测试手动绑定后的按钮点击...');
      await page.click('button', { hasText: '开始评测' });

      // 等待评测完成
      await page.waitForTimeout(5000);

      // 检查结果
      const resultContent = await page.$eval('#result', el => el.innerHTML);
      if (resultContent.includes('评测结果')) {
        console.log('✅ 手动绑定成功！评测功能正常工作');
      } else {
        console.log('❌ 手动绑定失败');
        console.log('结果长度:', resultContent.length);
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