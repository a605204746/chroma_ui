# Chroma Walnut UI

> 一个基于 PyWebView + React 的 ChromaDB 可视化桌面管理工具

**[English Documentation](README.md)**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" />
  <img src="https://img.shields.io/badge/ChromaDB-0.6+-purple" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" />
  <img src="https://img.shields.io/badge/Ant_Design-6-0170FE?logo=antdesign" />
  <img src="https://img.shields.io/badge/平台-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

## 产品截图

<p align="center">
  <img src="docs/screenshot-welcome.png" width="700" alt="欢迎页" />
</p>

<p align="center">
  <img src="docs/screenshot-overview.png" width="700" alt="概览页" />
</p>

---

## 简介

Chroma Walnut UI 是一个轻量级的 ChromaDB 桌面客户端，无需浏览器，直接以原生窗口运行。支持多连接管理、集合编辑、文档增删改查、向量相似度搜索等功能，适合开发者在本地调试和管理 ChromaDB 数据。

## 功能特性

- **多连接管理** — 同时管理多个 ChromaDB 连接（本地目录 / HTTP 服务），支持 Bearer Token 认证，一键测试连通性，侧边栏可折叠
- **集合管理** — 创建、编辑（重命名 + Metadata）、删除集合；Metadata 支持键值对表单，重复键名校验
- **文档浏览** — 分页展示（每页 10 / 20 / 30 条可选），展示文档 ID、内容、Metadata 彩色标签；支持查看完整 JSON、文本框选复制
- **一键生成测试数据** — 内置 50 条中文示例文档，配置向量模型后一键插入，方便快速调试
- **向量展示** — 可选显示 Embedding 列，支持预览与一键复制
- **向量搜索** — 配置向量模型后输入文本即可进行语义相似度搜索，支持多条件过滤
- **向量模型配置** — 集合级别配置嵌入模型（兼容 OpenAI 格式 API），支持 Ollama / OpenAI / LM Studio / 通义千问快速填充，连接测试自动获取维度
- **Schema 查看** — 展示集合信息、向量维度，推断字段类型
- **响应式布局** — 窗口宽度 < 1100px 自动折叠侧边栏，字体与间距自适应缩放
- **单实例锁** — 防止重复打开多个窗口
- **国际化** — 中文 / English 随时切换
- **主题切换** — 亮色 / 暗色 / 跟随系统

## 技术栈

| 层 | 技术 |
|---|---|
| 桌面容器 | [PyWebView](https://pywebview.flowrl.com/) 6.x |
| 后端 | Python 3.12+，[ChromaDB](https://docs.trychroma.com/) 0.6+ |
| 前端框架 | React 19 + TypeScript |
| UI 组件库 | Ant Design 6 |
| 状态管理 | Zustand 5 |
| 国际化 | i18next + react-i18next |
| 构建工具 | Vite 8 |
| 包管理 | [uv](https://github.com/astral-sh/uv)（Python）/ npm（前端） |

## 环境要求

- Python **3.12+**
- Node.js **18+**
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip
- 系统：Windows 10 1803+ / macOS 10.15+ / Ubuntu 20.04+

> **Windows**：PyWebView 依赖 WebView2，Microsoft Edge 自带，无需额外安装。  
> **macOS**：无需额外系统依赖。  
> **Linux**：需要预先安装 `libwebkit2gtk-4.1-0` 和 `libgtk-3-0` 系统包。

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/deepin_sir/chroma-walnut-ui.git
cd chroma-walnut-ui
```

### 2. 安装 Python 依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install pywebview chromadb
```

> **Linux 用户** 需要先安装系统包：
> ```bash
> sudo apt-get install -y python3-gi python3-gi-cairo \
>   gir1.2-gtk-3.0 gir1.2-webkit2-4.1 libwebkit2gtk-4.1-dev
> ```

### 3. 安装前端依赖

```bash
cd frontend && npm install && cd ..
```

### 4. 运行

**生产模式**（自动构建前端并启动窗口）：

```bash
uv run python main.py
```

**开发模式**（前端热更新，适合二次开发）：

```bash
# 终端 1：启动前端开发服务器
cd frontend && npm run dev

# 终端 2：启动 PyWebView（加载 localhost:5173）
uv run python main.py --dev
```

## 跨平台打包

使用内置的跨平台打包脚本，在目标系统上运行即可生成对应平台的可执行文件（PyInstaller 不支持交叉编译，需要在对应系统上分别打包）。

```bash
# 正式包（无控制台）
uv run python build.py

# 调试包（保留控制台，用于排查启动错误）
uv run python build.py --debug
```

脚本自动完成：检查依赖 → 构建前端 → 生成图标 → PyInstaller 打包 → 压缩分发文件。

### 各平台输出

| 平台 | 输出目录 | 分发压缩包 |
|---|---|---|
| Windows | `dist/ChromaWalnutUI/` | `dist/ChromaWalnutUI-Windows.zip` |
| macOS | `dist/ChromaWalnutUI.app` | `dist/ChromaWalnutUI-macOS.dmg` |
| Linux | `dist/ChromaWalnutUI/` | `dist/ChromaWalnutUI-Linux.tar.gz` |

### 用户运行要求

| 平台 | 要求 |
|---|---|
| Windows | Windows 10 1803+ / Windows 11（已内置 WebView2） |
| macOS | macOS 10.15 Catalina+ |
| Linux | `libwebkit2gtk-4.1-0`、`libgtk-3-0` |

> Windows / macOS 分发时直接发给用户即可，无需安装 Python 或 Node.js。

## GitHub Actions 自动发布

推送版本 tag 即可自动触发三平台并行构建，并生成 GitHub Release：

```bash
git tag v1.0.0
git push origin v1.0.0
```

工作流（`.github/workflows/release.yml`）会在 `windows-latest`、`macos-latest`、`ubuntu-24.04` 上各自运行 `build.py`，完成后将三个平台的压缩包上传至 Release。包含 `-` 的 tag（如 `v1.0.0-beta`）自动标记为预发布版本。

## 项目结构

```
chroma_ui/
├── main.py                  # 入口：PyWebView 窗口，单实例锁，居中计算
├── api.py                   # Python API 层：所有暴露给 JS 的方法
├── chroma_manager.py        # ChromaDB 多连接管理器
├── icon_utils.py            # 纯 Python 核桃图标生成（ICO / ICNS / PNG）
├── logger.py                # 统一日志（RotatingFileHandler，5 MB × 3）
├── build.py                 # 跨平台一键打包脚本
├── pyproject.toml
├── uv.lock
├── .github/
│   └── workflows/
│       └── release.yml      # CI/CD：tag 触发 → 三平台构建 → GitHub Release
└── frontend/
    └── src/
        ├── api/bridge.ts        # JS ↔ Python API 类型安全封装
        ├── store/appStore.ts    # Zustand 全局状态
        ├── i18n/                # zh.ts / en.ts 翻译文件
        ├── layouts/             # 主布局：可折叠侧边栏 + 内容区
        ├── components/          # 各类弹窗、WalnutLogo、FilterBuilder
        ├── pages/               # 概览、集合列表、集合详情
        └── tabs/                # 数据浏览、Schema、向量搜索
```

## 数据持久化

所有数据存储在用户目录下，不写注册表，不污染系统目录。

| 路径 | 说明 |
|---|---|
| `~/.chroma_walnut_ui/connections.json` | 连接配置（含 Token 明文，仅本地使用） |
| `~/.chroma_walnut_ui/collection_embeddings.json` | 各集合的向量模型配置 |
| `~/.chroma_walnut_ui/app.log` | 应用日志（满 5 MB 自动轮转，保留 3 个备份） |

## 向量模型配置说明

Chroma Walnut UI 支持任何兼容 OpenAI Embeddings 格式的 API：

| 服务 | API 地址 | 模型示例 |
|---|---|---|
| Ollama | `http://localhost:11434/v1/embeddings` | `nomic-embed-text` |
| OpenAI | `https://api.openai.com/v1/embeddings` | `text-embedding-3-small` |
| LM Studio | `http://localhost:1234/v1/embeddings` | 按实际填写 |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings` | `text-embedding-v3` |

> 保存前必须先点击「测试连通性」，成功后自动填入向量维度。  
> 不同集合可使用不同模型，请与写入文档时保持一致。

## 常见问题

**Q: 启动后窗口空白？**

A: 检查 Python 依赖是否正确安装（尤其是 `pywebview`）。Windows 用户确认 Edge WebView2 可用。查看 `~/.chroma_walnut_ui/app.log` 可获取详细错误信息。

**Q: 开发模式下前端修改没有热更新？**

A: 确认 `npm run dev` 已在 `frontend/` 目录启动，且 PyWebView 以 `--dev` 参数运行。

**Q: 向量搜索提示"维度不匹配"？**

A: 集合里的文档是用其他模型写入的，当前配置的模型维度不一致。请使用与写入文档时相同的模型。

**Q: HTTP 连接需要 Token 认证？**

A: 在新增/编辑连接时填写 Token 字段，应用会自动以 `Authorization: Bearer <token>` 方式发送。

**Q: 打包后的 Windows `.exe` 启动失败？**

A: 确认已安装 Microsoft Edge（WebView2 运行时）。Windows 10 1803+ 和 Windows 11 已内置。若未安装，可从 [WebView2 官网](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) 下载。

**Q: macOS 提示"应用已损坏"或安全警告？**

A: 应用未经代码签名。右键 → 打开，或前往「系统设置 → 隐私与安全性」中点击「仍要打开」。如需分发，建议使用 `codesign` 对 `.app` 进行签名。

## 参与贡献

欢迎提 Issue 和 PR。重大改动请先开 Issue 讨论。

## License

[MIT](LICENSE)

## 作者

Made with ❤️ by **deepin_sir**
