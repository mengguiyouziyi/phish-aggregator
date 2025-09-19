# 开发指南

## 🚀 快速启动

### 一键启动开发模式（推荐）
```bash
./dev.sh
```

### 其他启动方式
```bash
# 普通启动
./start.sh

# 重启
./restart.sh

# 停止
./stop.sh
```

## 🔧 开发功能

### 热重载支持
- **Python代码**: 修改后自动重启服务器
- **HTML/CSS/JS**: 需要手动刷新浏览器
- **自动修复**: JavaScript函数会自动修复

### 手动修复HTML
```bash
# 如果刷新后没有看到修复效果，运行：
node fix-html.js
```

### 测试功能
```bash
# 运行全面测试
node test-comprehensive.js

# 测试帮助按钮
node test-help-buttons.js

# 测试弹窗功能
node debug-modal-functions.js
```

## 📱 访问地址

- **主应用**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **API规则源**: http://localhost:8000/api/sources/rules
- **API模型**: http://localhost:8000/api/sources/models

## 🛠️ 开发提示

1. **首次运行**: 确保虚拟环境已创建
2. **端口冲突**: 脚本会自动处理8000端口占用
3. **日志查看**: 控制台会显示详细日志
4. **调试模式**: 使用dev.sh启动有更详细的调试信息

## 🐛 常见问题

### 如果看不到规则和模型列表
1. 确保服务正在运行
2. 运行 `node fix-html.js`
3. 刷新浏览器

### 如果帮助按钮不工作
1. 打开浏览器开发者工具
2. 查看控制台是否有错误信息
3. 运行测试脚本检查功能

### 如果热重载不工作
1. 确保使用dev.sh启动
2. 检查Python代码语法
3. 查看控制台的重启日志