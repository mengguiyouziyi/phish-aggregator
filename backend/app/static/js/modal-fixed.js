/**
 * Phish Aggregator - 弹窗管理器
 * 钓鱼网站检测聚合平台弹窗功能
 *
 * @version 2.0.0
 * @author Claude
 * @license MIT
 */

// 弹窗管理器
const ModalManager = {
  /**
   * 显示规则描述弹窗
   * @param {string} ruleKey - 规则键名
   */
  showRuleDescription(ruleKey) {
    console.log(`显示规则描述: ${ruleKey}`);
    const descriptions = this.getRuleDescriptions();
    const ruleDesc = descriptions[ruleKey];

    if (!ruleDesc) {
      console.log(`未找到规则 ${ruleKey} 的描述信息`);
      this.showModal({
        title: `规则 - ${ruleKey}`,
        content: '<p>此规则的详细信息正在完善中...</p>',
        className: 'rule-modal'
      });
      return;
    }

    this.showModal({
      title: ruleDesc.overview || `规则 - ${ruleKey}`,
      content: this.buildRuleContent(ruleDesc),
      className: 'rule-modal'
    });
  },

  /**
   * 显示模型描述弹窗
   * @param {string} modelKey - 模型键名
   */
  showModelDescription(modelKey) {
    console.log(`显示模型描述: ${modelKey}`);
    const descriptions = this.getModelDescriptions();
    const modelDesc = descriptions[modelKey];

    if (!modelDesc) {
      console.log(`未找到模型 ${modelKey} 的描述信息`);
      this.showModal({
        title: `模型 - ${modelKey}`,
        content: '<p>此模型的详细信息正在完善中...</p>',
        className: 'model-modal'
      });
      return;
    }

    this.showModal({
      title: modelDesc.overview || `模型 - ${modelKey}`,
      content: this.buildModelContent(modelDesc),
      className: 'model-modal'
    });
  },

  /**
   * 显示策略描述弹窗
   * @param {string} strategy - 策略名称
   */
  showStrategyDescription(strategy) {
    console.log(`显示策略描述: ${strategy}`);
    const descriptions = this.getStrategyDescriptions();
    const strategyDesc = descriptions[strategy];

    if (!strategyDesc) {
      this.showModal({
        title: `策略 - ${strategy}`,
        content: '<p>此策略的详细信息正在完善中...</p>',
        className: 'strategy-modal'
      });
      return;
    }

    this.showModal({
      title: strategyDesc.title || `策略 - ${strategy}`,
      content: this.buildStrategyContent(strategyDesc),
      className: 'strategy-modal'
    });
  },

  /**
   * 显示弹窗
   * @param {Object} options - 弹窗选项
   */
  showModal(options) {
    const modal = document.getElementById('descriptionModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    if (!modal || !modalTitle || !modalBody) {
      console.error('弹窗元素未找到');
      return;
    }

    // 设置内容
    modalTitle.textContent = options.title;
    modalBody.innerHTML = options.content;

    // 添加样式类
    modal.className = 'modal active ' + (options.className || '');

    // 绑定键盘事件
    this.bindKeyboardEvents();

    // 触发动画
    setTimeout(() => {
      modalBody.style.opacity = '1';
      modalBody.style.transform = 'translateY(0)';
    }, 10);
  },

  /**
   * 关闭弹窗
   */
  closeModal() {
    const modal = document.getElementById('descriptionModal');
    const modalBody = document.getElementById('modalBody');

    if (!modal) return;

    // 添加关闭动画
    if (modalBody) {
      modalBody.style.opacity = '0';
      modalBody.style.transform = 'translateY(-20px)';
    }

    setTimeout(() => {
      modal.classList.remove('active');

      // 重置样式
      if (modalBody) {
        modalBody.style.opacity = '';
        modalBody.style.transform = '';
      }

      // 解绑键盘事件
      this.unbindKeyboardEvents();
    }, 300);
  },

  /**
   * 绑定键盘事件
   */
  bindKeyboardEvents() {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        this.closeModal();
      }
    };

    document.addEventListener('keydown', handleEscape);
    this._escapeHandler = handleEscape;
  },

  /**
   * 解绑键盘事件
   */
  unbindKeyboardEvents() {
    if (this._escapeHandler) {
      document.removeEventListener('keydown', this._escapeHandler);
      this._escapeHandler = null;
    }
  },

  /**
   * 构建规则内容
   * @param {Object} ruleDesc - 规则描述
   */
  buildRuleContent(ruleDesc) {
    let content = '';

    // 概述
    if (ruleDesc.overview) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">📋</span>
          规则概述
        </div>
        <div class="modal-section-content">
          <p>${ruleDesc.overview}</p>
        </div>
      </div>`;
    }

    // 主要特性
    if (ruleDesc.features && ruleDesc.features.length > 0) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">⚡</span>
          主要特性
        </div>
        <div class="modal-section-content">
          <ul>
            ${ruleDesc.features.map(feature => `<li>${feature}</li>`).join('')}
          </ul>
        </div>
      </div>`;
    }

    // 技术细节
    if (ruleDesc.technical_details) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">🔧</span>
          技术细节
        </div>
        <div class="modal-section-content">
          <ul>
            ${Object.entries(ruleDesc.technical_details).map(([key, value]) =>
              `<li><strong>${key}:</strong> ${value}</li>`
            ).join('')}
          </ul>
        </div>
      </div>`;
    }

    // 相关链接
    if (ruleDesc.links && ruleDesc.links.length > 0) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">🔗</span>
          相关链接
        </div>
        <div class="modal-section-content">
          <ul>
            ${ruleDesc.links.map(link =>
              `<li><a href="${link.url}" target="_blank" rel="noopener noreferrer">${link.title}</a></li>`
            ).join('')}
          </ul>
        </div>
      </div>`;
    }

    return content;
  },

  /**
   * 构建模型内容
   * @param {Object} modelDesc - 模型描述
   */
  buildModelContent(modelDesc) {
    let content = '';

    // 概述
    if (modelDesc.overview) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">🤖</span>
          模型概述
        </div>
        <div class="modal-section-content">
          <p>${modelDesc.overview}</p>
        </div>
      </div>`;
    }

    // 主要特性
    if (modelDesc.features && modelDesc.features.length > 0) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">⚡</span>
          主要特性
        </div>
        <div class="modal-section-content">
          <ul>
            ${modelDesc.features.map(feature => `<li>${feature}</li>`).join('')}
          </ul>
        </div>
      </div>`;
    }

    // 技术细节
    if (modelDesc.technical_details) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">🔧</span>
          技术细节
        </div>
        <div class="modal-section-content">
          <ul>
            ${Object.entries(modelDesc.technical_details).map(([key, value]) =>
              `<li><strong>${key}:</strong> ${value}</li>`
            ).join('')}
          </ul>
        </div>
      </div>`;
    }

    // 相关链接
    if (modelDesc.links && modelDesc.links.length > 0) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">🔗</span>
          相关链接
        </div>
        <div class="modal-section-content">
          <ul>
            ${modelDesc.links.map(link =>
              `<li><a href="${link.url}" target="_blank" rel="noopener noreferrer">${link.title}</a></li>`
            ).join('')}
          </ul>
        </div>
      </div>`;
    }

    return content;
  },

  /**
   * 构建策略内容
   * @param {Object} strategyDesc - 策略描述
   */
  buildStrategyContent(strategyDesc) {
    let content = '';

    // 概述
    if (strategyDesc.overview) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">🎯</span>
          策略概述
        </div>
        <div class="modal-section-content">
          <p>${strategyDesc.overview}</p>
        </div>
      </div>`;
    }

    // 工作原理
    if (strategyDesc.how_it_works) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">⚙️</span>
          工作原理
        </div>
        <div class="modal-section-content">
          <p>${strategyDesc.how_it_works}</p>
        </div>
      </div>`;
    }

    // 优缺点
    if (strategyDesc.advantages || strategyDesc.disadvantages) {
      content += `<div class="modal-section">
        <div class="modal-section-title">
          <span class="icon">⚖️</span>
          优缺点分析
        </div>
        <div class="modal-section-content">`;

      if (strategyDesc.advantages && strategyDesc.advantages.length > 0) {
        content += `<p><strong>优点:</strong></p><ul>`;
        strategyDesc.advantages.forEach(adv => {
          content += `<li>${adv}</li>`;
        });
        content += `</ul>`;
      }

      if (strategyDesc.disadvantages && strategyDesc.disadvantages.length > 0) {
        content += `<p><strong>缺点:</strong></p><ul>`;
        strategyDesc.disadvantages.forEach(disadv => {
          content += `<li>${disadv}</li>`;
        });
        content += `</ul>`;
      }

      content += `</div></div>`;
    }

    return content;
  },

  /**
   * 获取规则描述数据
   */
  getRuleDescriptions() {
    return {
      'metamask_eth_phishing_detect': {
        'overview': 'MetaMask以太坊钓鱼网站检测器',
        'features': [
          '专门针对以太坊生态系统的钓鱼网站检测',
          '由MetaMask团队维护的高质量规则集',
          '包含大量已知的以太坊相关钓鱼域名',
          '实时更新和社区驱动的规则维护',
          '支持钱包地址欺骗检测'
        ],
        'technical_details': {
          'implementation': '基于正则表达式和模式匹配',
          'coverage': '涵盖以太坊、DeFi、NFT等领域',
          'update_frequency': '持续更新，响应新威胁',
          'accuracy': '高准确率，低误报率'
        },
        'links': [
          {'title': 'GitHub仓库', 'url': 'https://github.com/MetaMask/eth-phishing-detect'},
          {'title': 'MetaMask官方文档', 'url': 'https://docs.metamask.io/'},
          {'title': '以太坊安全指南', 'url': 'https://ethereum.org/en/security/'}
        ]
      },
      'polkadot_js_phishing': {
        'overview': 'Polkadot.js钓鱼网站检测器',
        'features': [
          '专门针对Polkadot生态系统的钓鱼网站检测',
          '由Polkadot.js团队维护',
          '包含波卡相关钓鱼域名和模式',
          '支持跨链项目检测',
          '社区贡献的规则集'
        ],
        'technical_details': {
          'implementation': '基于域名和URL模式匹配',
          'coverage': '涵盖Polkadot、Kusama、 parachains等',
          'update_mechanism': '社区驱动更新',
          'integration': '与Polkadot.js生态系统深度集成'
        },
        'links': [
          {'title': '官方钓鱼检测页面', 'url': 'https://polkadot.js.org/phishing/'},
          {'title': 'Polkadot.js文档', 'url': 'https://polkadot.js.org/docs/'},
          {'title': '波卡安全中心', 'url': 'https://polkadot.network/security/'}
        ]
      },
      'phishing_database': {
        'overview': '通用钓鱼网站数据库检测器',
        'features': [
          '综合性钓鱼网站数据库',
          '包含多种类型钓鱼网站',
          '社区贡献和维护',
          '跨平台和跨币种支持',
          '开放的API接口'
        ],
        'technical_details': {
          'implementation': '基于GitHub仓库的数据库维护',
          'data_format': '结构化的JSON格式',
          'update_frequency': '社区持续更新',
          'verification': '多层次的验证机制'
        },
        'links': [
          {'title': 'GitHub仓库', 'url': 'https://github.com/Phishing-Database/Phishing.Database'},
          {'title': '数据库贡献指南', 'url': 'https://github.com/Phishing-Database/Phishing.Database/blob/master/CONTRIBUTING.md'},
          {'title': '钓鱼安全资源', 'url': 'https://example.com/phishing-resources'}
        ]
      },
      'cryptoscamdb': {
        'overview': 'CryptoScamDB API钓鱼检测器',
        'features': [
          '专注于加密货币相关诈骗检测',
          '通过API获取最新诈骗信息',
          '覆盖各类加密货币骗局',
          '实时数据同步',
          '社区报告机制'
        ],
        'technical_details': {
          'implementation': '基于REST API的数据获取',
          'data_source': 'CryptoScamDB官方数据库',
          'update_mechanism': '实时API调用',
          'coverage': '全球加密货币诈骗信息'
        },
        'links': [
          {'title': 'CryptoScamDB官网', 'url': 'https://cryptoscamdb.org/'},
          {'title': 'API文档', 'url': 'https://api.cryptoscamdb.org/'},
          {'title': '诈骗报告页面', 'url': 'https://cryptoscamdb.org/report'}
        ]
      }
    };
  },

  /**
   * 获取模型描述数据
   */
  getModelDescriptions() {
    return {
      'heuristic_baseline': {
        'overview': '启发式基准模型（内置）',
        'features': [
          '基于手工设计的特征工程',
          '使用逻辑回归算法',
          '可解释性强，运行速度快',
          '适合作为基准对比模型',
          '内置实现，无需外部依赖'
        ],
        'technical_details': {
          'implementation': '内置的启发式算法实现',
          'performance': '特征提取后推理速度极快',
          'accuracy': '基准准确率，适合作为基础模型',
          'interpretability': '模型决策过程完全可解释'
        },
        'links': [
          {'title': '钓鱼检测算法综述', 'url': 'https://example.com/phishing-detection-survey'},
          {'title': '特征工程指南', 'url': 'https://example.com/feature-engineering'},
          {'title': '模型可解释性', 'url': 'https://example.com/model-interpretability'}
        ]
      },
      'urltran': {
        'overview': 'URLTran - 基于Transformer的URL检测模型',
        'features': [
          '使用Transformer架构处理URL文本',
          '能够理解URL的语义信息',
          '对新型钓鱼模式有良好识别能力',
          '支持多语言URL检测',
          '预训练模型，开箱即用'
        ],
        'technical_details': {
          'architecture': '基于BERT的Transformer架构',
          'training_data': '大规模URL语料库预训练',
          'input_length': '支持最多512字符的URL',
          'inference_speed': '中等，需要GPU加速效果更佳'
        },
        'links': [
          {'title': 'GitHub仓库', 'url': 'https://github.com/bfilar/URLTran'},
          {'title': '论文链接', 'url': 'https://arxiv.org/abs/2104.08347'},
          {'title': 'Transformer模型介绍', 'url': 'https://example.com/transformer-guide'}
        ]
      },
      'urlbert': {
        'overview': 'URLBERT - 专门针对URL优化的BERT模型',
        'features': [
          '针对URL文本特点优化的BERT模型',
          '能够理解URL的层级结构和语义',
          '对字符级别的钓鱼特征敏感',
          '支持域名和路径的分离分析',
          '高准确率，低误报率'
        ],
        'technical_details': {
          'architecture': '基于BERT架构的URL专用模型',
          'tokenization': '专门的URL分词算法',
          'max_length': '针对URL优化的最大长度设置',
          'fine_tuning': '在钓鱼检测数据集上微调'
        },
        'links': [
          {'title': 'GitHub仓库', 'url': 'https://github.com/Davidup1/URLBERT'},
          {'title': 'BERT模型原理解析', 'url': 'https://example.com/bert-explanation'},
          {'title': 'URL安全分析', 'url': 'https://example.com/url-security'}
        ]
      }
    };
  },

  /**
   * 获取策略描述数据
   */
  getStrategyDescriptions() {
    return {
      'any': {
        'title': 'ANY 策略',
        'overview': '任一命中即判定策略，采用保守的安全原则',
        'how_it_works': '当任何一个规则命中时，立即判定为钓鱼网站（置信度1.0）；如果没有规则命中，则使用所有可用模型的最高预测概率作为最终结果。',
        'advantages': [
          '高安全性，不会漏掉已知的钓鱼模式',
          '响应速度快，规则匹配优先',
          '易于理解和调试',
          '对新型攻击有一定防护能力'
        ],
        'disadvantages': [
          '可能产生误报',
          '依赖规则的质量和完整性',
          '对纯模型依赖的情况较少优化'
        ]
      },
      'weighted': {
        'title': 'WEIGHTED 策略',
        'overview': '概率加权平均策略，平衡准确性和召回率',
        'how_it_works': '将所有模型的预测概率进行加权平均，每命中一个规则增加0.2的权重分数（最高1.0），最终分数超过阈值时判定为钓鱼网站。',
        'advantages': [
          '平衡准确性和召回率',
          '充分利用多个模型的优势',
          '对噪声数据有较好的鲁棒性',
          '可通过阈值灵活调整敏感度'
        ],
        'disadvantages': [
          '计算复杂度较高',
          '需要合理设置权重参数',
          '可能漏掉一些低置信度的钓鱼网站',
          '对模型性能依赖性高'
        ]
      }
    };
  }
};

// 导出到全局作用域
window.ModalManager = ModalManager;