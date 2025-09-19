const { chromium } = require('playwright');

(async () => {
  console.log('🧪 简单功能测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 访问应用
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // 监听控制台
    page.on('console', msg => {
      console.log(`[控制台] ${msg.text()}`);
    });

    // 等待页面加载
    await page.waitForTimeout(3000);

    // 1. 测试基本扫描功能
    console.log('\n🔍 测试基本扫描功能...');
    await page.fill('#urls', 'https://www.baidu.com');

    // 选择前两个规则
    const ruleInputs = await page.$$('input[name="rule"]');
    for (let i = 0; i < Math.min(2, ruleInputs.length); i++) {
      await ruleInputs[i].check();
    }

    // 点击扫描按钮
    await page.click('button:has-text("开始扫描")');
    await page.waitForTimeout(3000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    const hasResults = resultContent.includes('检测结果') && resultContent.includes('正常');
    console.log(`扫描结果显示: ${hasResults ? '✅ 正常' : '❌ 异常'}`);

    // 2. 测试弹窗功能
    console.log('\n🪟 测试弹窗功能...');
    await page.click('.help-btn');
    await page.waitForTimeout(1000);

    const modalVisible = await page.evaluate(() => {
      const modal = document.getElementById('descriptionModal');
      return modal && modal.classList.contains('active');
    });
    console.log(`弹窗显示: ${modalVisible ? '✅ 正常' : '❌ 异常'}`);

    if (modalVisible) {
      const modalTitle = await page.$eval('#modalTitle', el => el.textContent);
      console.log(`弹窗标题: ${modalTitle}`);
    }

    // 3. 测试评测功能
    console.log('\n📊 测试评测功能...');
    await page.evaluate(() => {
      const closeBtn = document.querySelector('.modal-close');
      if (closeBtn) closeBtn.click();
    });
    await page.waitForTimeout(500);

    await page.click('button:has-text("开始评测")');
    await page.waitForTimeout(3000);

    const evalContent = await page.$eval('#result', el => el.innerHTML);
    const hasEvalResults = evalContent.includes('评测结果');
    console.log(`评测结果显示: ${hasEvalResults ? '✅ 正常' : '❌ 异常'}`);

    console.log('\n🎉 测试总结:');
    console.log(`✅ 扫描功能: ${hasResults ? '正常' : '异常'}`);
    console.log(`✅ 弹窗功能: ${modalVisible ? '正常' : '异常'}`);
    console.log(`✅ 评测功能: ${hasEvalResults ? '正常' : '异常'}`);

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();