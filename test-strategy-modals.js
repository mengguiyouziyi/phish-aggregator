import { chromium } from 'playwright';

(async () => {
  console.log('🧪 策略说明弹窗测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台消息
    page.on('console', msg => {
      if (msg.text().includes('✅') || msg.text().includes('❌') || msg.text().includes('显示策略描述')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 测试ANY策略按钮
    console.log('\n📋 测试ANY策略说明弹窗...');

    const anyStrategyButton = await page.$('button[onclick*="showStrategyDescription(\'any\')"]');
    if (anyStrategyButton) {
      await anyStrategyButton.click();
      await page.waitForTimeout(1000);

      const modalVisible = await page.evaluate(() => {
        const modal = document.getElementById('descriptionModal');
        return modal && modal.classList.contains('active');
      });

      console.log(`ANY策略弹窗显示: ${modalVisible ? '✅' : '❌'}`);

      if (modalVisible) {
        const title = await page.$eval('#modalTitle', el => el.textContent);
        console.log(`弹窗标题: ${title}`);

        // 关闭弹窗
        await page.click('.modal-close');
        await page.waitForTimeout(500);
      }
    } else {
      console.log('❌ 未找到ANY策略按钮');
    }

    // 测试WEIGHTED策略按钮
    console.log('\n⚖️ 测试WEIGHTED策略说明弹窗...');

    const weightedStrategyButton = await page.$('button[onclick*="showStrategyDescription(\'weighted\')"]');
    if (weightedStrategyButton) {
      await weightedStrategyButton.click();
      await page.waitForTimeout(1000);

      const modalVisible = await page.evaluate(() => {
        const modal = document.getElementById('descriptionModal');
        return modal && modal.classList.contains('active');
      });

      console.log(`WEIGHTED策略弹窗显示: ${modalVisible ? '✅' : '❌'}`);

      if (modalVisible) {
        const title = await page.$eval('#modalTitle', el => el.textContent);
        console.log(`弹窗标题: ${title}`);

        // 关闭弹窗
        await page.click('.modal-close');
        await page.waitForTimeout(500);
      }
    } else {
      console.log('❌ 未找到WEIGHTED策略按钮');
    }

    // 检查两个按钮是否都存在
    console.log('\n🔍 检查策略帮助按钮...');
    const anyButtonExists = await page.$('button[onclick*="showStrategyDescription(\'any\')"]') !== null;
    const weightedButtonExists = await page.$('button[onclick*="showStrategyDescription(\'weighted\')"]') !== null;

    console.log(`ANY策略按钮存在: ${anyButtonExists ? '✅' : '❌'}`);
    console.log(`WEIGHTED策略按钮存在: ${weightedButtonExists ? '✅' : '❌'}`);

    if (anyButtonExists && weightedButtonExists) {
      console.log('🎉 策略说明弹窗功能完整！');
    } else {
      console.log('⚠️ 策略说明弹窗功能不完整');
    }

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();