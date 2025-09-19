import { chromium } from 'playwright';

(async () => {
  console.log('🧪 URLBERT单URL测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台消息
    page.on('console', msg => {
      if (msg.text().includes('URLBERT') || msg.text().includes('urlbert') || msg.text().includes('模型') || msg.text().includes('策略')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    // 监听网络请求
    page.on('request', request => {
      if (request.url().includes('/api/scan') || request.url().includes('/api/evaluate')) {
        console.log(`[请求] ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/scan') || response.url().includes('/api/evaluate')) {
        try {
          const data = await response.json();
          console.log(`[响应] ${response.url()}:`, JSON.stringify(data, null, 2));
        } catch (e) {
          console.log(`[响应] ${response.url()}: ${await response.text()}`);
        }
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 只选择URLBERT模型
    console.log('\n🔍 选择URLBERT模型...');
    const modelCheckboxes = await page.$$('input[name="model"]');
    let urlbertSelected = false;

    for (const checkbox of modelCheckboxes) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, checkbox);
      console.log(`发现模型: ${label.trim()}`);

      if (label.includes('URLBERT')) {
        // 先取消选择所有模型
        await checkbox.uncheck();
        await checkbox.check();
        urlbertSelected = true;
        console.log('✅ 已选择URLBERT模型');
      } else {
        // 取消选择其他模型
        await checkbox.uncheck();
      }
    }

    if (!urlbertSelected) {
      console.log('❌ 未找到URLBERT模型');
      return;
    }

    // 输入测试URL
    console.log('\n📝 输入测试URL: http://tjhsfk.com/');
    await page.fill('#urls', 'http://tjhsfk.com/');
    console.log('✅ 已输入测试URL');

    // 检查策略显示问题
    console.log('\n🔍 检查策略显示...');
    const strategyRadios = await page.$$('input[name="strategy"]');
    for (const radio of strategyRadios) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, radio);
      const isChecked = await radio.isChecked();
      console.log(`策略: ${label.trim()} - 选中: ${isChecked}`);
    }

    // 使用ANY策略
    await page.click('input[value="any"]');
    console.log('✅ 已选择ANY策略');

    // 开始扫描
    console.log('\n🔍 开始扫描...');
    await page.evaluate(() => {
      const scanButton = Array.from(document.querySelectorAll('button')).find(btn =>
        btn.textContent.includes('开始扫描')
      );
      if (scanButton) {
        scanButton.click();
      }
    });

    // 等待扫描完成
    console.log('⏳ 等待扫描结果...');
    await page.waitForTimeout(8000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    console.log(`\n📋 扫描结果:\n${resultContent}`);

    // 检查是否使用了URLBERT
    if (resultContent.includes('URLBERT') || resultContent.toLowerCase().includes('urlbert')) {
      console.log('✅ 确认URLBERT参与了扫描');
    } else {
      console.log('❌ 未检测到URLBERT参与扫描');
    }

    // 检查策略显示
    if (resultContent.includes('undefined') || resultContent.includes('未知策略')) {
      console.log('❌ 发现策略显示问题');
    } else {
      console.log('✅ 策略显示正常');
    }

    console.log('\n🎉 URLBERT单URL测试完成！');

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();