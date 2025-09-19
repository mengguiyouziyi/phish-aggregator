import { chromium } from 'playwright';

(async () => {
  console.log('🔍 调查前端评测结果显示问题...');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // 监听所有控制台消息和错误
    page.on('console', msg => {
      console.log(`[控制台 ${msg.type()}] ${msg.text()}`);
      if (msg.type() === 'error') {
        console.error(`❌ JavaScript错误: ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.error(`❌ 页面错误: ${error.message}`);
      console.error(`错误堆栈: ${error.stack}`);
    });

    // 监听网络请求
    page.on('request', request => {
      if (request.url().includes('/api/evaluate')) {
        console.log(`[评测请求] ${request.method()} ${request.url()}`);
        console.log(`[请求数据] ${request.postData()}`);
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/evaluate')) {
        try {
          const data = await response.json();
          console.log(`[评测响应] 状态: ${response.status()}`);
          console.log(`[响应数据]`, JSON.stringify(data, null, 2));

          // 检查响应数据结构
          if (data.metrics && data.details) {
            console.log('✅ 响应数据结构正确');
            console.log(`📊 包含 ${Object.keys(data.metrics).length} 个策略的评测数据`);
            console.log(`📋 包含 ${data.details.length} 条详细结果`);
          } else {
            console.log('❌ 响应数据结构异常');
          }
        } catch (e) {
          console.log(`[评测响应] 状态: ${response.status()}, 解析失败: ${e.message}`);
          console.log(`[原始响应] ${await response.text()}`);
        }
      }
    });

    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 检查页面元素
    const resultElement = await page.$('#result');
    if (resultElement) {
      console.log('✅ 找到结果区域元素');
    } else {
      console.log('❌ 未找到结果区域元素');
    }

    // 选择URLBERT模型
    const modelCheckboxes = await page.$$('input[name="model"]');
    for (const checkbox of modelCheckboxes) {
      const label = await page.evaluate(el => el.nextElementSibling.textContent, checkbox);
      if (label.includes('URLBERT')) {
        await checkbox.check();
        console.log('✅ 已选择URLBERT模型');
      } else {
        await checkbox.uncheck();
      }
    }

    // 检查URL输入框
    const urlTextarea = await page.$('#urls');
    if (urlTextarea) {
      console.log('✅ 找到URL输入框');

      // 输入测试URL
      await urlTextarea.fill('http://tjhsfk.com/\nhttps://www.google.com/\nhttps://www.baidu.com/');
      console.log('✅ 已输入测试URL');
    } else {
      console.log('❌ 未找到URL输入框');
    }

    // 检查评测按钮
    const evalButton = await page.$('button', { hasText: '开始评测' });

    if (evalButton) {
      console.log('✅ 找到评测按钮');

      // 检查按钮的onclick属性
      const onclickAttr = await evalButton.getAttribute('onclick');
      console.log(`[调试] 按钮onclick属性: ${onclickAttr}`);

      // 尝试直接调用AppController.runEval()
      console.log('\n🔍 开始评测 (通过直接调用JavaScript)...');
      await page.evaluate(() => {
        if (typeof AppController !== 'undefined' && AppController.runEval) {
          AppController.runEval();
        } else {
          console.error('AppController.runEval 未找到');
        }
      });

      // 等待评测完成
      console.log('⏳ 等待评测结果...');

      // 等待结果区域变化
      let resultContent = '';
      let attempts = 0;
      const maxAttempts = 20;

      while (attempts < maxAttempts) {
        await page.waitForTimeout(1000);
        resultContent = await page.$eval('#result', el => el.innerHTML);

        if (resultContent.length > 133 || resultContent.includes('评测结果')) {
          console.log(`✅ 检测到评测结果更新 (第${attempts + 1}次检查)`);
          break;
        }

        attempts++;
      }

      // 检查最终结果
      console.log(`\n📋 评测结果区域内容长度: ${resultContent.length} 字符`);

      if (resultContent.includes('评测结果')) {
        console.log('✅ 评测结果标题显示正常');

        // 检查具体内容
        if (resultContent.includes('准确率') && resultContent.includes('精确率')) {
          console.log('✅ 评测指标显示正常');
        } else {
          console.log('❌ 评测指标显示异常');
        }

        if (resultContent.includes('混淆矩阵')) {
          console.log('✅ 混淆矩阵显示正常');
        } else {
          console.log('❌ 混淆矩阵显示异常');
        }

        if (resultContent.includes('详细结果')) {
          console.log('✅ 详细结果显示正常');
        } else {
          console.log('❌ 详细结果显示异常');
        }

        // 显示部分结果内容
        console.log('\n📊 评测结果预览:');
        console.log(resultContent.substring(0, 500) + '...');

      } else {
        console.log('❌ 评测结果未显示');
        console.log('结果区域内容:', resultContent);
      }

    } else {
      console.log('❌ 未找到评测按钮');
    }

    console.log('\n🎉 评测显示问题调查完成！');

  } catch (error) {
    console.error('❌ 调查失败:', error);
  } finally {
    await browser.close();
  }
})();