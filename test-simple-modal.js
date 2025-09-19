import { chromium } from 'playwright';

(async () => {
  console.log('🧪 简单弹窗测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听控制台错误
    page.on('pageerror', error => {
      console.log(`[错误] ${error.message}`);
    });

    page.on('console', msg => {
      if (msg.text().includes('错误') || msg.text().includes('失败')) {
        console.log(`[控制台] ${msg.text()}`);
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 检查ModalManager是否可用
    const modalManagerAvailable = await page.evaluate(() => {
      return typeof window.ModalManager !== 'undefined';
    });

    console.log(`ModalManager可用性: ${modalManagerAvailable ? '✅' : '❌'}`);

    if (!modalManagerAvailable) {
      console.log('❌ ModalManager未加载，检查JavaScript错误...');
      return;
    }

    // 测试一个简单的弹窗
    console.log('\n🪟 测试策略弹窗...');

    await page.evaluate(() => {
      window.ModalManager.showStrategyDescription('any');
    });

    await page.waitForTimeout(1000);

    const modalVisible = await page.evaluate(() => {
      const modal = document.getElementById('descriptionModal');
      return modal && modal.classList.contains('active');
    });

    console.log(`策略弹窗显示: ${modalVisible ? '✅' : '❌'}`);

    if (modalVisible) {
      const title = await page.$eval('#modalTitle', el => el.textContent);
      console.log(`弹窗标题: ${title}`);

      // 关闭弹窗
      await page.click('.modal-close');
      await page.waitForTimeout(500);
      console.log('✅ 弹窗测试成功');
    }

  } catch (error) {
    console.error('❌ 测试失败:', error);
  } finally {
    await browser.close();
  }
})();