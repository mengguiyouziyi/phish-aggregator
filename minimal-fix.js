const { chromium } = require('playwright');

(async () => {
  console.log('🔧 最小化修复测试...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有错误
    page.on('pageerror', error => {
      console.log(`[错误] ${error.message}`);
      if (error.stack) {
        console.log(`[堆栈] ${error.stack.split('\n')[0]}`);
      }
    });

    // 访问应用
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // 尝试手动注入工作函数
    console.log('\n🩹 手动注入修复函数...');
    const injectionResult = await page.evaluate(() => {
      try {
        // 简单的工作函数
        window.workingRunScan = async function() {
          console.log('✅ workingRunScan 被调用');
          const urls = document.getElementById('urls').value.split('\n').map(x=>x.trim()).filter(Boolean);
          if (!urls.length) {
            alert('请输入至少一个 URL');
            return;
          }

          const button = document.querySelector('button[onclick="runScan()"]');
          if (button) {
            button.textContent = '扫描中...';
            button.disabled = true;
          }

          try {
            const body = {
              urls: urls.slice(0, 1), // 只测试第一个URL
              use_rules: ['url_regex'],
              use_models: ['heuristic_baseline'],
              strategy: 'any',
              threshold: 0.5
            };

            const res = await fetch('/api/scan', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify(body)
            });

            const data = await res.json();
            console.log('📊 扫描结果:', data);

            if (button) {
              button.textContent = '开始扫描';
              button.disabled = false;
            }

            return '扫描完成';
          } catch (error) {
            console.error('扫描失败:', error);
            if (button) {
              button.textContent = '开始扫描';
              button.disabled = false;
            }
            return '扫描失败: ' + error.message;
          }
        };

        // 替换按钮的onclick事件
        const scanButton = document.querySelector('button[onclick="runScan()"]');
        if (scanButton) {
          scanButton.setAttribute('onclick', '');
          scanButton.addEventListener('click', window.workingRunScan);
          return '按钮修复成功';
        } else {
          return '未找到扫描按钮';
        }
      } catch (error) {
        return '注入失败: ' + error.message;
      }
    });

    console.log(`注入结果: ${injectionResult}`);

    // 测试修复后的按钮
    console.log('\n🧪 测试修复后的按钮...');
    await page.fill('#urls', 'https://www.baidu.com');
    await page.click('button:has-text("开始扫描")');
    await page.waitForTimeout(3000);

    // 检查结果
    const resultContent = await page.$eval('#result', el => el.innerHTML);
    const hasResults = resultContent.includes('检测结果') || resultContent.includes('URL');
    console.log(`扫描结果显示: ${hasResults ? '✅ 正常' : '❌ 无结果'}`);

  } catch (error) {
    console.error('❌ 最小化测试失败:', error);
  } finally {
    await browser.close();
  }
})();