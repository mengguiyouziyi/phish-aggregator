/**
 * Phish Aggregator - 主应用脚本
 * 钓鱼网站检测聚合平台前端核心功能
 *
 * @version 2.0.0
 * @author Claude
 * @license MIT
 */

// 应用状态管理
const AppState = {
  initialized: false,
  loading: false,
  sources: {
    rules: [],
    models: []
  },
  config: {
    threshold: 0.5,
    strategy: 'any'
  }
};

// URL历史记录管理器
const URLHistoryManager = {
  STORAGE_KEY: 'phish_aggregator_url_history',
  MAX_ITEMS: 50,

  /**
   * 获取历史记录
   */
  getHistory() {
    try {
      const history = localStorage.getItem(this.STORAGE_KEY);
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('获取历史记录失败:', error);
      return [];
    }
  },

  /**
   * 保存历史记录
   * @param {Array} history - 历史记录数组
   */
  saveHistory(history) {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('保存历史记录失败:', error);
    }
  },

  /**
   * 添加URL到历史记录
   * @param {string|array} urls - URL字符串或URL数组
   */
  addURLs(urls) {
    const urlArray = Array.isArray(urls) ? urls : urls.split('\n').map(u => u.trim()).filter(Boolean);
    if (urlArray.length === 0) return;

    const history = this.getHistory();
    const timestamp = new Date().toISOString();

    urlArray.forEach(url => {
      // 检查是否已存在相同的URL
      const existingIndex = history.findIndex(item => item.url === url);

      if (existingIndex >= 0) {
        // 更新现有记录的时间戳和使用次数
        history[existingIndex].timestamp = timestamp;
        history[existingIndex].count = (history[existingIndex].count || 1) + 1;
        history[existingIndex].urlCount = urlArray.length;
      } else {
        // 添加新记录
        history.unshift({
          url: url,
          timestamp: timestamp,
          count: 1,
          urlCount: urlArray.length
        });
      }
    });

    // 按时间戳排序并限制数量
    history.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    const trimmedHistory = history.slice(0, this.MAX_ITEMS);

    this.saveHistory(trimmedHistory);
    this.renderHistory();
  },

  /**
   * 移除单个历史记录
   * @param {string} url - 要移除的URL
   */
  removeURL(url) {
    const history = this.getHistory();
    const filteredHistory = history.filter(item => item.url !== url);
    this.saveHistory(filteredHistory);
    this.renderHistory();
  },

  /**
   * 清空所有历史记录
   */
  clearHistory() {
    localStorage.removeItem(this.STORAGE_KEY);
    this.renderHistory();
  },

  /**
   * 格式化时间戳
   * @param {string} timestamp - ISO时间戳
   */
  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;

    return date.toLocaleDateString('zh-CN');
  },

  /**
   * 渲染历史记录列表
   */
  renderHistory() {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;

    const history = this.getHistory();

    if (history.length === 0) {
      historyList.innerHTML = '<div class="history-empty">暂无历史记录</div>';
      return;
    }

    historyList.innerHTML = history.map(item => `
      <div class="history-item" data-url="${item.url}">
        <div class="history-url">${Utils.escapeHtml(item.url)}</div>
        <div class="history-time">
          <span>${this.formatTime(item.timestamp)}</span>
          <div>
            ${item.urlCount > 1 ? `<span class="history-count">${item.urlCount}个</span>` : ''}
            ${item.count > 1 ? `<span class="history-count">${item.count}次</span>` : ''}
            <button class="history-item-remove" onclick="URLHistoryManager.removeURL('${item.url.replace(/'/g, "\\'")}')">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    `).join('');

    // 添加点击事件
    historyList.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', (e) => {
        // 如果点击的是删除按钮，不触发URL填充
        if (e.target.closest('.history-item-remove')) return;

        const url = item.dataset.url;
        this.fillURL(url);
      });
    });
  },

  /**
   * 填充URL到输入框
   * @param {string} url - 要填充的URL
   */
  fillURL(url) {
    const urlTextarea = document.getElementById('urls');
    if (!urlTextarea) return;

    // 如果输入框为空，直接填充
    if (!urlTextarea.value.trim()) {
      urlTextarea.value = url;
    } else {
      // 如果输入框已有内容，添加到新行
      const currentUrls = urlTextarea.value.split('\n').map(u => u.trim()).filter(Boolean);
      if (!currentUrls.includes(url)) {
        currentUrls.push(url);
        urlTextarea.value = currentUrls.join('\n');
      }
    }

    // 聚焦到输入框
    urlTextarea.focus();

    // 隐藏历史记录下拉框
    this.hideDropdown();
  },

  /**
   * 显示历史记录下拉框
   */
  showDropdown() {
    const dropdown = document.getElementById('history-dropdown');
    const historyBtn = document.getElementById('history-btn');

    if (dropdown) {
      dropdown.style.display = 'flex';
      historyBtn.classList.add('active');
      this.renderHistory();
    }
  },

  /**
   * 隐藏历史记录下拉框
   */
  hideDropdown() {
    const dropdown = document.getElementById('history-dropdown');
    const historyBtn = document.getElementById('history-btn');

    if (dropdown) {
      dropdown.style.display = 'none';
      historyBtn.classList.remove('active');
    }
  },

  /**
   * 切换下拉框显示状态
   */
  toggleDropdown() {
    const dropdown = document.getElementById('history-dropdown');
    if (dropdown.style.display === 'none' || !dropdown.style.display) {
      this.showDropdown();
    } else {
      this.hideDropdown();
    }
  }
};

// 工具函数库
const Utils = {
  /**
   * 显示通知消息
   * @param {string} message - 消息内容
   * @param {string} type - 消息类型 (success|warning|error|info)
   */
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-icon">${this.getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
      </div>
    `;

    document.body.appendChild(notification);

    // 自动移除通知
    setTimeout(() => {
      notification.classList.add('notification-fade-out');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  },

  /**
   * 获取通知图标
   */
  getNotificationIcon(type) {
    const icons = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  },

  /**
   * 格式化置信度百分比
   * @param {number} score - 分数值 (0-1)
   * @returns {string} 格式化的百分比
   */
  formatConfidence(score) {
    return `${(score * 100).toFixed(2)}%`;
  },

  /**
   * 防抖函数
   * @param {Function} func - 要防抖的函数
   * @param {number} wait - 等待时间
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * 节流函数
   * @param {Function} func - 要节流的函数
   * @param {number} limit - 时间限制
   */
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * 截断URL显示
   * @param {string} url - URL字符串
   * @param {number} maxLength - 最大长度
   * @returns {string} 截断后的URL
   */
  truncateUrl(url, maxLength = 50) {
    if (!url || url.length <= maxLength) return url;

    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname;
      const pathname = urlObj.pathname;

      if (hostname.length + pathname.length <= maxLength) {
        return url;
      }

      // 优先显示域名，截断路径
      if (hostname.length > maxLength - 10) {
        return hostname.substring(0, maxLength - 10) + '...';
      }

      const remainingLength = maxLength - hostname.length - 3;
      return hostname + pathname.substring(0, remainingLength) + '...';
    } catch {
      // 如果URL解析失败，简单截断
      return url.substring(0, maxLength - 3) + '...';
    }
  },

  /**
   * HTML转义
   * @param {string} text - 要转义的文本
   * @returns {string} 转义后的文本
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};

// API服务
const ApiService = {
  /**
   * 获取规则源列表
   */
  async getRules() {
    try {
      const response = await fetch('/api/sources/rules');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('获取规则失败:', error);
      throw error;
    }
  },

  /**
   * 获取模型源列表
   */
  async getModels() {
    try {
      const response = await fetch('/api/sources/models');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('获取模型失败:', error);
      throw error;
    }
  },

  /**
   * 执行扫描
   * @param {Object} params - 扫描参数
   */
  async scan(params) {
    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('扫描失败:', error);
      throw error;
    }
  },

  /**
   * 执行评测
   * @param {Object} params - 评测参数
   */
  async evaluate(params) {
    try {
      const response = await fetch('/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('评测失败:', error);
      throw error;
    }
  }
};

// UI管理器
const UIManager = {
  /**
   * 获取选中的复选框值
   * @param {string} name - 复选框名称
   */
  getChecked(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
      .map(el => el.value);
  },

  /**
   * 设置按钮加载状态
   * @param {HTMLElement} button - 按钮元素
   * @param {boolean} loading - 是否加载中
   * @param {string} originalText - 原始文本
   */
  setButtonLoading(button, loading, originalText) {
    if (loading) {
      button.disabled = true;
      button.innerHTML = '<span class="loading"></span> ' + originalText + '中...';
    } else {
      button.disabled = false;
      button.innerHTML = originalText;
    }
  },

  /**
   * 更新阈值显示
   * @param {number} value - 阈值
   */
  updateThresholdDisplay(value) {
    const display = document.getElementById('threshold-value');
    if (display) {
      display.textContent = parseFloat(value).toFixed(2);
    }
  },

  /**
   * 渲染规则列表
   * @param {Array} rules - 规则列表
   */
  renderRules(rules) {
    const container = document.getElementById('rules');
    if (!container) return;

    container.innerHTML = rules.map(rule => `
      <label class="checkbox-item">
        <input type="checkbox" name="rule" value="${rule.key}" ${rule.installed ? 'checked' : ''}>
        <span class="checkbox-label">${rule.name}</span>
        <button class="help-btn" onclick="ModalManager.showRuleDescription('${rule.key}')" title="查看详情">?</button>
        <span class="status-badge ${rule.installed ? 'status-success' : 'status-warning'}">
          ${rule.installed ? '已安装' : '未安装'}
        </span>
      </label>
    `).join('');
  },

  /**
   * 渲染模型列表
   * @param {Array} models - 模型列表
   */
  renderModels(models) {
    const container = document.getElementById('models');
    if (!container) return;

    container.innerHTML = models.map(model => `
      <label class="checkbox-item">
        <input type="checkbox" name="model" value="${model.key}" ${model.key === 'heuristic_baseline' ? 'checked' : ''}>
        <span class="checkbox-label">${model.name}</span>
        <button class="help-btn" onclick="ModalManager.showModelDescription('${model.key}')" title="查看详情">?</button>
        <span class="status-badge ${model.installed ? 'status-success' : 'status-warning'}">
          ${model.installed ? '可用' : '未安装'}
        </span>
      </label>
    `).join('');
  }
};

// 渲染引擎
const RenderEngine = {
  /**
   * 渲染扫描结果
   * @param {Object} data - 扫描结果数据
   */
  renderScanResults(data) {
    const container = document.getElementById('result');
    if (!container) return;

    const { strategy, threshold, results } = data;
    const total = results.length;
    const phishing = results.filter(r => r.agg.label === 1).length;
    const legit = results.filter(r => r.agg.label === 0).length;

    // 计算命中规则总数
    const hitRulesCount = results.reduce((sum, r) =>
      sum + Object.values(r.rules || {}).filter(Boolean).length, 0);

    const strategyInfo = StrategyManager.getStrategyInfo(strategy);
    const strategyExplanation = StrategyManager.getStrategyExplanation(strategy);

    let html = `
      <div class="scan-summary">
        <div class="summary-item">
          <span class="summary-label">📋 检测结果统计:</span>
          <span class="summary-value">总计: ${total} 个URL | 钓鱼: ${phishing} 个 | 正常: ${legit} 个</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">🎯 当前策略:</span>
          <span class="summary-value">${strategyInfo.name} (${strategyInfo.description})</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">📊 规则命中:</span>
          <span class="summary-value">${hitRulesCount} 个</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">💡 策略说明:</span>
          <span class="summary-value">${strategyExplanation}</span>
        </div>
      </div>
      <table class="results-table">
        <thead>
          <tr>
            <th>URL</th>
            <th>命中规则</th>
            <th>模型概率</th>
            <th>检测结果</th>
          </tr>
        </thead>
        <tbody>
    `;

    results.forEach(r => {
      const hitRules = Object.entries(r.rules || {})
        .filter(([_, hit]) => hit)
        .map(([rule, _]) => rule);

      const modelProbas = Object.entries(r.models || {})
        .map(([model, pred]) => `${model}: ${pred.proba.toFixed(4)}`)
        .join(', ');

      const isPhishing = r.agg.label === 1;
      const confidence = Utils.formatConfidence(r.agg.score);
      const ruleImpact = hitRules.length > 0 ? '规则影响' : '纯模型预测';

      html += `
        <tr>
          <td class="url-cell">
            <div class="url-content">
              <span class="url-text">${r.url}</span>
            </div>
          </td>
          <td>${hitRules.length > 0 ? hitRules.join(', ') : '-'}</td>
          <td>${modelProbas}</td>
          <td>
            <span class="label ${isPhishing ? 'phishing' : 'legit'}">
              ${isPhishing ? '🎣 钓鱼' : '✅ 正常'}
            </span>
            <div class="confidence">置信度: ${confidence} (${ruleImpact})</div>
          </td>
        </tr>
      `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
  },

  /**
   * 渲染评测结果
   * @param {Object} data - 评测结果数据
   */
  renderEvalResults(data) {
    const container = document.getElementById('result');
    if (!container) return;

    // 检查数据结构 - API返回 {metrics: Object, details: Array}
    let details = data.details || [];
    let metrics = data.metrics || {};

    if (!Array.isArray(details)) {
      console.error('评测数据格式错误:', data);
      Utils.showNotification('评测数据格式错误', 'error');
      return;
    }

    let html = '<div class="eval-results"><h3>评测结果</h3>';

    // 显示评测指标
    if (Object.keys(metrics).length > 0) {
      html += '<div class="eval-metrics">';
      html += '<h4>评测指标</h4>';
      html += '<table class="eval-table"><thead><tr><th>策略</th><th>准确率</th><th>精确率</th><th>召回率</th><th>F1分数</th></tr></thead><tbody>';

      Object.entries(metrics).forEach(([strategy, metric]) => {
        html += `
          <tr>
            <td>${strategy.toUpperCase()}</td>
            <td>${(metric.accuracy * 100).toFixed(2)}%</td>
            <td>${(metric.precision * 100).toFixed(2)}%</td>
            <td>${(metric.recall * 100).toFixed(2)}%</td>
            <td>${(metric.f1 * 100).toFixed(2)}%</td>
          </tr>
        `;
      });

      html += '</tbody></table>';

      // 显示混淆矩阵数据
      html += '<div class="confusion-matrix">';
      html += '<h4>混淆矩阵详情</h4>';
      html += '<table class="eval-table"><thead><tr><th>策略</th><th>TP</th><th>TN</th><th>FP</th><th>FN</th></tr></thead><tbody>';

      Object.entries(metrics).forEach(([strategy, metric]) => {
        html += `
          <tr>
            <td>${strategy.toUpperCase()}</td>
            <td>${metric.tp}</td>
            <td>${metric.tn}</td>
            <td>${metric.fp}</td>
            <td>${metric.fn}</td>
          </tr>
        `;
      });

      html += '</tbody></table></div></div>';
    }

    // 重新组织详细结果数据，按URL分组
    const urlResults = {};
    details.forEach(detail => {
      if (!urlResults[detail.url]) {
        urlResults[detail.url] = {
          url: detail.url,
          true_label: detail.true_label,
          strategies: {}
        };
      }
      urlResults[detail.url].strategies[detail.strategy] = detail;
    });

    // 显示详细结果
    if (Object.keys(urlResults).length > 0) {
      html += '<div class="eval-details">';
      html += '<h4>详细结果</h4>';
      html += '<table class="eval-table"><thead><tr><th>URL</th><th>真实标签</th><th>ANY策略</th><th>WEIGHTED策略</th></tr></thead><tbody>';

      Object.values(urlResults).forEach(result => {
        const anyResult = result.strategies.any || {};
        const weightedResult = result.strategies.weighted || {};

        const anyLabel = anyResult.pred === 1 ? '钓鱼' : '正常';
        const weightedLabel = weightedResult.pred === 1 ? '钓鱼' : '正常';

        const trueLabel = result.true_label === 1 ? '钓鱼' : '正常';

        html += `
          <tr>
            <td><a href="${result.url}" target="_blank">${Utils.truncateUrl(result.url)}</a></td>
            <td><span class="label ${result.true_label === 1 ? 'phishing' : 'legit'}">${trueLabel}</span></td>
            <td><span class="label ${anyResult.pred === 1 ? 'phishing' : 'legit'}">${anyLabel}</span></td>
            <td><span class="label ${weightedResult.pred === 1 ? 'phishing' : 'legit'}">${weightedLabel}</span></td>
          </tr>
        `;
      });

      html += '</tbody></table></div>';
    }

    html += '</div>';
    container.innerHTML = html;
  }
};

// 策略管理器
const StrategyManager = {
  /**
   * 获取策略信息
   * @param {string} strategy - 策略名称
   */
  getStrategyInfo(strategy) {
    const strategies = {
      'any': {
        name: 'ANY',
        description: '命中任一即判定'
      },
      'weighted': {
        name: 'WEIGHTED',
        description: '概率加权平均'
      }
    };
    return strategies[strategy] || { name: strategy, description: '未知策略' };
  },

  /**
   * 获取策略说明
   * @param {string} strategy - 策略名称
   */
  getStrategyExplanation(strategy) {
    const explanations = {
      'any': '任一规则命中即判钓鱼（满分1.0），无规则时用最高模型概率',
      'weighted': '模型概率加权平均，每命中一规则加0.2分（最高1.0）'
    };
    return explanations[strategy] || '策略说明未知';
  }
};

// 主应用控制器
const AppController = {
  /**
   * 初始化应用
   */
  async init() {
    console.log('🚀 初始化Phish Aggregator应用...');

    try {
      // 绑定事件监听器
      this.bindEventListeners();

      // 加载数据源
      await this.loadSources();

      AppState.initialized = true;
      console.log('✅ 应用初始化完成');

    } catch (error) {
      console.error('❌ 应用初始化失败:', error);
      Utils.showNotification('应用初始化失败: ' + error.message, 'error');
    }
  },

  /**
   * 绑定事件监听器
   */
  bindEventListeners() {
    // 阈值滑块
    const thresholdSlider = document.getElementById('threshold');
    if (thresholdSlider) {
      thresholdSlider.addEventListener('input', (e) => {
        UIManager.updateThresholdDisplay(e.target.value);
      });
    }

    // 扫描按钮
    const scanButton = Array.from(document.querySelectorAll('button')).find(btn =>
      btn.textContent.trim().includes('开始扫描') && btn.parentElement.className === 'button-group'
    );
    if (scanButton) {
      scanButton.setAttribute('onclick', '');
      scanButton.addEventListener('click', () => this.runScan());
      console.log('✅ 扫描按钮事件绑定成功');
    } else {
      console.error('❌ 未找到扫描按钮');
    }

    // 评测按钮
    const evalButton = Array.from(document.querySelectorAll('button')).find(btn =>
      btn.textContent.trim().includes('开始评测') && btn.parentElement.className === 'button-group'
    );
    if (evalButton) {
      // 完全移除现有的onclick属性和事件监听器
      evalButton.removeAttribute('onclick');
      evalButton.onclick = null;

      // 使用onclick属性直接绑定，保存this上下文
      const self = this;
      evalButton.onclick = function() {
        console.log('🔍 评测按钮被点击！');
        self.runEval();
      };
      console.log('✅ 评测按钮事件绑定成功');
    } else {
      console.error('❌ 未找到评测按钮');
    }

    // 历史记录按钮事件绑定
    const historyBtn = document.getElementById('history-btn');
    if (historyBtn) {
      historyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        URLHistoryManager.toggleDropdown();
      });
      console.log('✅ 历史记录按钮事件绑定成功');
    }

    // 清空历史记录按钮事件绑定
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    if (clearHistoryBtn) {
      clearHistoryBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('确定要清空所有历史记录吗？')) {
          URLHistoryManager.clearHistory();
          Utils.showNotification('历史记录已清空', 'success');
        }
      });
      console.log('✅ 清空历史记录按钮事件绑定成功');
    }

    // 点击页面其他地方关闭历史记录下拉框
    document.addEventListener('click', (e) => {
      const historyControls = document.querySelector('.url-history-controls');
      if (historyControls && !historyControls.contains(e.target)) {
        URLHistoryManager.hideDropdown();
      }
    });
  },

  /**
   * 加载数据源
   */
  async loadSources() {
    try {
      console.log('📋 加载规则和模型列表...');

      const [rulesData, modelsData] = await Promise.all([
        ApiService.getRules(),
        ApiService.getModels()
      ]);

      AppState.sources.rules = rulesData.rules || [];
      AppState.sources.models = modelsData.models || [];

      UIManager.renderRules(AppState.sources.rules);
      UIManager.renderModels(AppState.sources.models);

      console.log('✅ 数据源加载完成');

    } catch (error) {
      console.error('❌ 数据源加载失败:', error);
      Utils.showNotification('数据源加载失败', 'error');
      throw error;
    }
  },

  /**
   * 运行扫描
   */
  async runScan() {
    if (AppState.loading) return;

    const urls = document.getElementById('urls').value
      .split('\n')
      .map(x => x.trim())
      .filter(Boolean);

    if (!urls.length) {
      Utils.showNotification('请输入至少一个 URL', 'warning');
      return;
    }

    const scanButton = Array.from(document.querySelectorAll('button')).find(btn =>
      btn.textContent.trim().includes('开始扫描') && btn.parentElement.className === 'button-group'
    ) || document.querySelector('button[onclick*="runScan"]');

    if (!scanButton) {
      Utils.showNotification('未找到扫描按钮', 'error');
      return;
    }

    AppState.loading = true;
    UIManager.setButtonLoading(scanButton, true, '开始扫描');

    try {
      const params = {
        urls,
        use_rules: UIManager.getChecked('rule'),
        use_models: UIManager.getChecked('model'),
        strategy: document.querySelector('input[name="strategy"]:checked').value,
        threshold: parseFloat(document.getElementById('threshold').value)
      };

      const data = await ApiService.scan(params);
      RenderEngine.renderScanResults(data);

      // 保存URL到历史记录
      URLHistoryManager.addURLs(urls);

      Utils.showNotification('扫描完成', 'success');

    } catch (error) {
      console.error('扫描失败:', error);
      Utils.showNotification('扫描失败: ' + error.message, 'error');
    } finally {
      AppState.loading = false;
      UIManager.setButtonLoading(scanButton, false, '开始扫描');
    }
  },

  /**
   * 运行评测
   */
  async runEval() {
    if (AppState.loading) return;

    const urls = document.getElementById('urls').value
      .split('\n')
      .map(x => x.trim())
      .filter(Boolean);

    if (!urls.length) {
      Utils.showNotification('请输入至少一个 URL', 'warning');
      return;
    }

    const evalButton = Array.from(document.querySelectorAll('button')).find(btn =>
      btn.textContent.trim().includes('开始评测') && btn.parentElement.className === 'button-group'
    ) || document.querySelector('button[onclick*="runEval"]');

    if (!evalButton) {
      Utils.showNotification('未找到评测按钮', 'error');
      return;
    }

    AppState.loading = true;
    UIManager.setButtonLoading(evalButton, true, '开始评测');

    try {
      const params = {
        urls,
        use_rules: UIManager.getChecked('rule'),
        use_models: UIManager.getChecked('model'),
        strategies: ['any', 'weighted'],
        threshold: parseFloat(document.getElementById('threshold').value)
      };

      const data = await ApiService.evaluate(params);
      RenderEngine.renderEvalResults(data);

      // 保存URL到历史记录
      URLHistoryManager.addURLs(urls);

      Utils.showNotification('评测完成', 'success');

    } catch (error) {
      console.error('评测失败:', error);
      Utils.showNotification('评测失败: ' + error.message, 'error');
    } finally {
      AppState.loading = false;
      UIManager.setButtonLoading(evalButton, false, '开始评测');
    }
  }
};

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  AppController.init();
});

// 导出到全局作用域（为了向后兼容）
window.AppController = AppController;
window.Utils = Utils;
window.ApiService = ApiService;
window.UIManager = UIManager;
window.RenderEngine = RenderEngine;
window.StrategyManager = StrategyManager;
window.URLHistoryManager = URLHistoryManager;