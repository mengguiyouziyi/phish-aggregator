const fs = require('fs');
const path = require('path');

// 读取HTML文件
const htmlPath = path.join(__dirname, 'backend', 'app', 'static', 'index.html');
let html = fs.readFileSync(htmlPath, 'utf8');

// 添加热重载修复脚本
const fixScript = `
// 热重载修复 - 自动修复JavaScript函数问题
(function() {
  console.log('🔧 应用热重载修复...');

  // 检查loadSources函数是否可用
  if (typeof loadSources !== 'function') {
    console.log('🔧 修复loadSources函数...');

    // 创建修复版本的loadSources函数
    window.loadSources = async function() {
      try {
        console.log('📋 加载规则和模型列表...');

        const r1 = await fetch('/api/sources/rules').then(r => r.json());
        const r2 = await fetch('/api/sources/models').then(r => r.json());

        const rulesDiv = document.getElementById('rules');
        const modelsDiv = document.getElementById('models');

        if (rulesDiv) {
          const rulesHTML = (r1.rules || []).map(x => {
            const statusClass = x.installed ? 'status-success' : 'status-warning';
            const statusText = x.installed ? '已安装' : '未安装';
            return \`
              <label class="checkbox-item">
                <input type="checkbox" name="rule" value="\${x.key}" \${x.installed ? 'checked' : ''}>
                <span class="checkbox-label">\${x.name}</span>
                <button class="help-btn" onclick="showDescription('规则源', '\${x.key}')" title="查看详情">?</button>
                <span class="status-badge \${statusClass}">\${statusText}</span>
              </label>
            \`;
          }).join('');
          rulesDiv.innerHTML = rulesHTML;
        }

        if (modelsDiv) {
          const modelsHTML = (r2.models || []).map(x => {
            const statusClass = x.installed ? 'status-success' : 'status-warning';
            const statusText = x.installed ? '可用' : '未安装';
            const isChecked = x.key === 'heuristic_baseline' ? 'checked' : '';
            return \`
              <label class="checkbox-item">
                <input type="checkbox" name="model" value="\${x.key}" \${isChecked}>
                <span class="checkbox-label">\${x.name}</span>
                <button class="help-btn" onclick="showDescription('模型', '\${x.key}')" title="查看详情">?</button>
                <span class="status-badge \${statusClass}">\${statusText}</span>
              </label>
            \`;
          }).join('');
          modelsDiv.innerHTML = modelsHTML;
        }

        console.log('✅ 列表加载完成');
        return true;
      } catch (error) {
        console.error('❌ 加载失败:', error);
        return false;
      }
    };

    // 自动调用修复后的函数
    setTimeout(() => {
      console.log('🔧 自动调用修复的loadSources...');
      window.loadSources();
    }, 1000);
  }

  // 添加缺失的showDescription函数
  if (typeof showDescription !== 'function') {
    window.showDescription = function(type, key) {
      const modal = document.getElementById('descriptionModal');
      const modalTitle = document.getElementById('modalTitle');
      const modalBody = document.getElementById('modalBody');

      if (!modal || !modalTitle || !modalBody) return;

      modalTitle.textContent = \`\${type} - \${key}\`;
      modalBody.innerHTML = \`
        <div class="modal-section">
          <h3>详细信息</h3>
          <p>这是 \${type} \${key} 的详细说明。</p>
          <p>功能正在开发中，敬请期待完整内容。</p>
        </div>
      \`;

      modal.classList.add('active');
    };
  }

  // 添加缺失的showStrategyDescription函数
  if (typeof showStrategyDescription !== 'function') {
    window.showStrategyDescription = function(strategy) {
      const modal = document.getElementById('descriptionModal');
      const modalTitle = document.getElementById('modalTitle');
      const modalBody = document.getElementById('modalBody');

      if (!modal || !modalTitle || !modalBody) return;

      const strategyNames = {
        'any': 'any（命中任一即判钓鱼）',
        'weighted': 'weighted（按概率加权）'
      };

      modalTitle.textContent = \`聚合策略 - \${strategyNames[strategy] || strategy}\`;
      modalBody.innerHTML = \`
        <div class="modal-section">
          <h3>策略说明</h3>
          <p>这是 <strong>\${strategy}</strong> 策略的详细说明。</p>
          <p>功能正在开发中，敬请期待完整内容。</p>
        </div>
      \`;

      modal.classList.add('active');
    };
  }

  // 添加缺失的closeModal函数
  if (typeof closeModal !== 'function') {
    window.closeModal = function() {
      const modal = document.getElementById('descriptionModal');
      if (modal) {
        modal.classList.remove('active');
      }
    };
  }

  console.log('✅ 热重载修复应用完成');
})();
`;

// 查找合适的位置插入修复脚本
const bodyCloseIndex = html.indexOf('</body>');
if (bodyCloseIndex !== -1) {
  html = html.slice(0, bodyCloseIndex) + '<script>' + fixScript + '</script>' + html.slice(bodyCloseIndex);

  // 写回文件
  fs.writeFileSync(htmlPath, html);
  console.log('✅ HTML文件已修复，支持热重载');
} else {
  console.log('❌ 无法找到</body>标签');
}
