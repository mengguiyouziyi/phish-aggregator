const { chromium } = require('playwright');

(async () => {
  console.log('🔍 调试规则选择和命中问题...');

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

    // 监听API请求
    page.on('request', request => {
      if (request.url().includes('/api/scan')) {
        const postData = request.postData();
        if (postData) {
          const data = JSON.parse(postData);
          console.log('📤 扫描请求参数:');
          console.log(`  策略: ${data.strategy}`);
          console.log(`  选择的规则: [${data.use_rules.join(', ')}]`);
          console.log(`  选择的模型: [${data.use_models.join(', ')}]`);
          console.log(`  阈值: ${data.threshold}`);
        }
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/scan')) {
        try {
          const data = await response.json();
          console.log('\n📥 扫描响应结果:');
          data.results.forEach((result, index) => {
            console.log(`\nURL ${index + 1}: ${result.url}`);
            console.log(`  规则命中详情:`);
            Object.entries(result.rules || {}).forEach(([ruleName, isHit]) => {
              console.log(`    ${ruleName}: ${isHit ? '✅ 命中' : '❌ 未命中'}`);
            });
            console.log(`  模型预测:`);
            Object.entries(result.models || {}).forEach(([modelName, prediction]) => {
              console.log(`    ${modelName}: 概率=${prediction.proba}, 标签=${prediction.label}`);
            });
            console.log(`  聚合结果: 标签=${result.agg.label}, 分数=${result.agg.score}`);
          });
        } catch (e) {
          console.log('❌ 解析响应失败:', e);
        }
      }
    });

    // 等待页面加载
    await page.waitForTimeout(3000);

    // 检查规则选择状态
    const ruleCheck = await page.evaluate(() => {
      const ruleInputs = document.querySelectorAll('input[name="rule"]');
      const checkedRules = Array.from(document.querySelectorAll('input[name="rule"]:checked')).map(cb => cb.value);
      const allRules = Array.from(ruleInputs).map(input => ({
        value: input.value,
        checked: input.checked,
        label: input.parentElement.textContent.trim()
      }));

      return { checkedRules, allRules };
    });

    console.log('\n📋 规则选择状态:');
    console.log('所有可用规则:');
    ruleCheck.allRules.forEach((rule, index) => {
      console.log(`  ${index + 1}. ${rule.value} (${rule.label}) - ${rule.checked ? '✅ 已选' : '❌ 未选'}`);
    });
    console.log(`已选择的规则: [${ruleCheck.checkedRules.join(', ')}]`);

    // 使用百度URL进行测试
    await page.fill('#urls', 'https://www.baidu.com/index.php');
    console.log('\n🔍 测试URL: https://www.baidu.com/index.php');

    // 确保选择了前三个规则
    console.log('\n📌 确保选择前三个规则...');
    const firstThreeRules = await page.$$('input[name="rule"]');
    for (let i = 0; i < Math.min(3, firstThreeRules.length); i++) {
      await firstThreeRules[i].check();
      const ruleValue = await firstThreeRules[i].evaluate(el => el.value);
      console.log(`  ✅ 选中规则: ${ruleValue}`);
    }

    // 再次检查选择状态
    const updatedRuleCheck = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input[name="rule"]:checked')).map(cb => cb.value);
    });
    console.log(`更新后的选择: [${updatedRuleCheck.join(', ')}]`);

    // 执行扫描
    console.log('\n🔥 执行扫描测试...');
    await page.click('button:has-text("开始扫描")');
    await page.waitForTimeout(3000);

    // 检查弹窗内容问题
    console.log('\n🪟 检查弹窗说明内容...');
    await page.click('.help-btn'); // 点击第一个帮助按钮
    await page.waitForTimeout(1000);

    const modalContent = await page.evaluate(() => {
      const modal = document.getElementById('descriptionModal');
      if (modal && modal.classList.contains('active')) {
        return {
          title: document.getElementById('modalTitle')?.textContent || '',
          body: document.getElementById('modalBody')?.innerHTML || ''
        };
      }
      return null;
    });

    if (modalContent) {
      console.log('弹窗内容:');
      console.log(`标题: ${modalContent.title}`);
      console.log(`内容: ${modalContent.body.substring(0, 200)}...`);
      console.log(`是否包含"开发中": ${modalContent.body.includes('开发中')}`);
      console.log(`是否包含"敬请期待": ${modalContent.body.includes('敬请期待')}`);
    } else {
      console.log('❌ 未找到弹窗内容');
    }

  } catch (error) {
    console.error('❌ 调试失败:', error);
  } finally {
    await browser.close();
  }
})();