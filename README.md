# aikun-claude-manager

Claude Code 图形化管理工具，提供 API 配置、汉化补丁、工作目录管理等功能。

![Logo](logo.png)

## ✨ 功能

### 仪表盘
- Claude Code 安装状态、版本检测
- API 连接状态、当前模型显示
- 余额查询（需登录 aikun 账号）
- 思考程度快速切换（low / medium / high）
- 汉化补丁状态一览
- 一键启动 Claude（自动选工作目录）

### API 配置
- API Key 设置（Base URL 固定为 `aikun.cnzc.qzz.io`）
- 模型选择：支持按系列分类（Sonnet / Opus / Haiku / Fable），也可自定义输入
- 获取可用模型列表，点击即填
- API 连接测试
- 思考程度设置（low / medium / high）

### 汉化补丁
- 详细状态面板：安装类型、Claude 版本、二进制补丁状态、插件状态
- 一键安装汉化仓库、应用补丁、移除补丁
- 自动检测 Claude 进程，打补丁前提示关闭
- 插件启用/禁用管理

### 工作目录管理
- 分组管理工作文件夹
- 启动 Claude 时自动切换到指定目录
- 记住上次选择的目录

### 配置管理
- settings.json 完整编辑
- JSON 格式化显示

## 📦 下载

### GitHub Actions 云端打包（推荐）

前往 [Releases](https://github.com/hayou2002/aikun-claude-manager/releases) 页面下载对应平台的安装包：

| 平台 | 文件 |
|------|------|
| Windows | `aikun-claude-manager-windows.zip` |
| macOS | `aikun-claude-manager-macos.tar.gz` |
| Linux | `aikun-claude-manager-linux.tar.gz` |

解压后直接运行即可。

### 本地打包

```bash
# Windows
build.bat

# 或手动打包
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --noconsole --name "aikun-claude-manager" --add-data="ui;ui" --add-data="logo.png;." --icon=logo.ico main.py
```

### 从源码运行

```bash
git clone https://github.com/hayou2002/aikun-claude-manager.git
cd aikun-claude-manager
pip install -r requirements.txt
python main.py
```

## 🚀 使用步骤

### 1. 首次启动

双击运行程序，仪表盘会自动检测 Claude Code 安装状态。

### 2. 配置 API

1. 进入「API 配置」页面
2. 输入 API Key（从 [aikun.cnzc.qzz.io](https://aikun.cnzc.qzz.io) 获取）
3. 点击「测试连接」确认正常
4. 选择默认模型（必选）
5. 可选：设置其他系列模型和思考程度
6. 点击「保存配置」

### 3. 应用汉化补丁

1. 进入「汉化补丁」页面
2. 如果显示「仓库未安装」，点击「安装仓库」
3. **关闭所有 Claude Code 窗口**（重要！）
4. 点击「应用补丁」
5. 等待完成，状态显示「已打补丁」即可

### 4. 管理工作目录

1. 进入「工作目录」页面
2. 添加常用文件夹，可分组管理
3. 回到仪表盘，选择目录后点击「启动 Claude」

### 5. 查询余额

1. 点击仪表盘的「登录 aikun」按钮
2. 输入 API Key 登录
3. 余额会显示在仪表盘

## ⚠️ 注意事项

### 汉化补丁相关

- **Windows 原生安装**：打补丁/移除补丁前必须先关闭 Claude Code，因为 Windows 会锁定正在运行的 exe 文件
- 如果补丁状态显示「版本不匹配」，说明 Claude Code 更新了，需要重新打补丁
- 汉化补丁只翻译部分界面文案，不是完全汉化

### API 配置相关

- Base URL 固定为 `https://aikun.cnzc.qzz.io`，不需要手动填写
- Claude Code 会自动在 URL 后追加 `/v1/messages`，所以配置时**不要**加 `/v1`
- 思考程度通过环境变量 `CLAUDE_CODE_EFFORT_LEVEL` 设置，比 settings.json 字段更可靠

### 其他

- 配置文件位置：`~/.claude/settings.json`
- 汉化插件位置：`~/.claude/plugins/claude-code-zh-cn/`
- 余额查询需要先登录 aikun 账号

## 🛠️ 开发

### 项目结构

```
aikun-claude-manager/
├── main.py                  # 主程序（Python 后端）
├── ui/
│   └── index.html           # 界面（HTML/CSS/JS）
├── logo.png                 # 应用图标（1024x1024）
├── logo.ico                 # Windows 图标
├── logo_b64.txt             # 图标 base64 编码
├── requirements.txt         # Python 依赖
├── build.bat                # Windows 本地打包脚本
├── .github/
│   └── workflows/
│       └── build.yml        # GitHub Actions 自动打包
└── README.md
```

### 技术栈

- **后端**：Python 3.11+ / pywebview
- **前端**：HTML + CSS + JavaScript（内嵌在 pywebview 中）
- **打包**：PyInstaller

### GitHub Actions

推送 tag 会自动触发云端打包：

```bash
git tag v1.0.0
git push origin v1.0.0
```

打包完成后会在 Releases 页面生成三平台安装包。

## 📄 许可证

MIT License
