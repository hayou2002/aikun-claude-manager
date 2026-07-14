# Claude Code 管理工具

一个专为 Claude Code 设计的管理工具，基于 aikun-gui 架构开发，提供直观的图形界面来管理 Claude Code 的配置、API 连接和汉化补丁。

## ✨ 功能特性

### 📊 仪表盘
- Claude Code 安装状态检测
- API 连接状态监控
- 当前模型配置显示
- 汉化补丁状态查看
- 快速操作按钮
- **余额查询功能**（需要登录）
- AI坤 API 官网跳转
- **常用工作文件夹设置**
- **系统信息显示**（平台、配置文件）

### 🔗 API 配置
- API Key 管理（Base URL 已固定为 aikun.cnzc.qzz.io）
- 模型下拉选择器（支持分类：Sonnet/Opus/Haiku/Fable）
- 默认模型设置（必选）
- 其他系列模型设置（非必选）
- API 连接测试
- 模型列表获取

### 🌐 汉化补丁
- 一键安装汉化仓库
- 补丁应用/移除
- 补丁状态检测

### ⚙️ 配置管理
- 完整配置文件编辑
- 环境变量管理
- 权限规则配置
- JSON 格式化显示

### 🛠️ 实用工具
- 快速启动 Claude Code
- 打开配置文件夹
- Claude 安装扫描
- 官方文档链接

## 🚀 快速开始

### 方法一：直接运行（推荐）
1. 下载 `ClaudeCodeManager.exe`
2. 双击运行即可

### 方法二：从源码运行
1. 克隆项目
```bash
git clone <repository-url>
cd claude-manager
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python main.py
```

## 🔧 打包为可执行文件

运行打包脚本：
```bash
build.bat
```

打包完成后，可执行文件将生成在 `dist/ClaudeCodeManager.exe`

## 📁 项目结构

```
claude-manager/
├── main.py              # 主程序
├── requirements.txt     # Python 依赖
├── build.bat            # 打包脚本
├── logo.png             # 应用图标
├── README.md            # 项目说明
└── ui/
    └── index.html       # 界面文件
```

## 🎯 使用场景

- **Claude Code 用户**：管理 API 配置、汉化界面
- **开发者**：快速切换不同的 API 端点和模型
- **团队**：统一 Claude Code 配置

## 🔒 安全说明

- API Key 仅在本地存储，不会上传到任何服务器
- 配置文件存储在用户目录下的 `.claude` 文件夹
- 所有网络请求仅用于 API 连接测试

## 📝 更新日志

### v1.2.0
- 修复窗口图标，使用自定义 Logo 替换 Python 默认图标
- 实现余额查询登录功能（参考 aikun-gui）
- 添加常用工作文件夹设置，支持从指定目录启动 Claude
- 修复系统信息显示平台未知的问题
- 修复 API 配置输入框样式，解决黑字黑底问题
- 修复配置管理页面样式问题
- 添加登录/退出登录功能
- 添加工作文件夹管理功能

### v1.1.0
- 修复 Logo 显示问题，使用 base64 编码确保正确加载
- 简化 API 配置界面，只显示 API Key 输入框
- 实现模型下拉选择器，支持按系列分类（Sonnet/Opus/Haiku/Fable）
- 添加默认模型必选功能
- 添加余额查询功能
- 添加 AI坤 API 官网跳转功能
- 优化仪表盘布局，增加账户信息卡片

### v1.0.0
- 初始版本发布
- 支持 Claude Code 安装检测
- 支持 API 配置管理
- 支持汉化补丁管理
- 基于 aikun-gui 架构开发

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License