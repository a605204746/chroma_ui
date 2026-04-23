# Chroma UI

> 一个基于 PyWebView + React 的 ChromaDB 可视化桌面管理工具

**[English Documentation](README.md)**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" />
  <img src="https://img.shields.io/badge/ChromaDB-0.6+-purple" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" />
  <img src="https://img.shields.io/badge/Ant_Design-6-0170FE?logo=antdesign" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

## 简介

Chroma UI 是一个轻量级的 ChromaDB 桌面客户端，无需浏览器，直接以原生窗口运行。支持多连接管理、文档浏览与编辑、向量相似度搜索等功能，适合开发者在本地调试和管理 ChromaDB 数据。

## 功能特性

- **多连接管理** — 同时管理多个 ChromaDB 连接（本地目录 / HTTP 服务），支持 Bearer Token 认证，一键测试连通性
- **集合管理** — 创建、删除、浏览集合，查看文档数量与集合 Metadata
- **文档浏览** — 分页展示文档 ID、内容、Metadata（彩色 Tag 按类型区分）
- **向量展示** — 可选显示 Embedding 向量，支持预览与一键复制 JSON
- **向量搜索** — 配置向量模型后，输入文本即可进行语义相似度搜索，支持过滤条件
- **向量模型配置** — 集合级别配置嵌入模型（兼容 OpenAI 格式 API），支持 Ollama / OpenAI / LM Studio / Qwen 快速填充，连接测试自动获取维度
- **Schema 查看** — 展示集合基本信息与 HNSW 参数
- **国际化** — 支持中文 / English 切换
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
- 系统：Windows / macOS / Linux

> **Windows 用户**：PyWebView 在 Windows 上依赖 WebView2，Edge 浏览器自带，无需额外安装。

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/deepin_sir/chroma-ui.git
cd chroma-ui
```

### 2. 安装 Python 依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install pywebview chromadb
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 运行

**生产模式**（自动构建前端并启动窗口）：

```bash
uv run python main.py
# 或
python main.py
```

**开发模式**（前端热更新，适合二次开发）：

```bash
# 终端 1：启动前端开发服务器
cd frontend
npm run dev

# 终端 2：启动 PyWebView（加载 localhost:5173）
uv run python main.py --dev
```

## 项目结构

```
chroma_ui/
├── main.py                  # 入口：PyWebView 窗口创建，--dev 参数控制模式
├── api.py                   # Python API 层：暴露给 JS 的所有方法
├── chroma_manager.py        # ChromaDB 多连接管理器
├── pyproject.toml           # Python 项目配置
├── uv.lock                  # uv 依赖锁文件
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx             # React 入口
        ├── App.tsx              # 根组件，主题 & 国际化 Provider
        ├── api/
        │   └── bridge.ts        # JS ↔ Python API 类型安全封装
        ├── types/
        │   └── index.ts         # 全局类型定义
        ├── store/
        │   └── appStore.ts      # Zustand 全局状态（连接、集合、导航）
        ├── i18n/
        │   ├── index.ts         # i18next 初始化
        │   ├── zh.ts            # 中文翻译
        │   └── en.ts            # 英文翻译
        ├── layouts/
        │   └── AppLayout.tsx    # 主布局：侧边栏连接列表 + 内容区
        ├── components/
        │   ├── ConnectionModal.tsx      # 新增/编辑连接弹窗（含连接测试）
        │   ├── CollectionModal.tsx      # 新建集合弹窗
        │   ├── DocumentModal.tsx        # 新增/编辑文档弹窗（动态键值对 Metadata）
        │   ├── EmbeddingConfigModal.tsx # 向量模型配置弹窗
        │   ├── FilterBuilder.tsx        # 搜索过滤条件构建器
        │   └── ErrorBoundary.tsx        # 渲染错误捕获
        ├── pages/
        │   ├── OverviewPage.tsx         # 概览页
        │   ├── CollectionsPage.tsx      # 集合列表页
        │   ├── CollectionDetailPage.tsx # 集合详情页（含 Tab 切换）
        │   └── SystemPage.tsx           # 系统设置页
        └── tabs/
            ├── DataTab.tsx      # 数据浏览 Tab
            ├── SchemaTab.tsx    # Schema 信息 Tab
            └── SearchTab.tsx    # 向量搜索 Tab
```

## 数据持久化

连接配置和向量模型配置保存在用户目录下：

| 文件 | 说明 |
|---|---|
| `~/.chroma_ui/connections.json` | 所有连接配置（含 Token，明文存储，仅本地使用） |
| `~/.chroma_ui/collection_embeddings.json` | 各集合的向量模型配置 |

## 向量模型配置说明

Chroma UI 支持任何兼容 OpenAI Embeddings 格式的 API：

| 服务 | API 地址 | 模型示例 |
|---|---|---|
| Ollama | `http://localhost:11434/v1/embeddings` | `nomic-embed-text` |
| OpenAI | `https://api.openai.com/v1/embeddings` | `text-embedding-3-small` |
| LM Studio | `http://localhost:1234/v1/embeddings` | 按实际填写 |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings` | `text-embedding-v3` |

> 配置保存前必须先点击「测试连通性」，成功后自动填入向量维度。

## 常见问题

**Q: 启动后窗口空白？**

A: 检查 Python 依赖是否正确安装，尤其是 `pywebview`；Windows 用户确认 Edge WebView2 已安装。

**Q: 开发模式下前端修改没有热更新？**

A: 确认 `npm run dev` 已在 `frontend/` 目录下启动，且 PyWebView 以 `--dev` 参数运行。

**Q: 向量搜索提示"维度不匹配"？**

A: 集合里的文档使用的向量维度与当前配置的模型维度不一致，请确保使用相同的模型。

**Q: HTTP 连接需要 Token 认证？**

A: 在新增/编辑连接时填写 Token 字段，Chroma UI 会自动以 `Authorization: Bearer <token>` 方式发送。

## 参与贡献

欢迎提 Issue 和 PR。重大改动请先开 Issue 讨论。

## License

[MIT](LICENSE)

## 作者

Made with ❤️ by **deepin_sir**
