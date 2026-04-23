# Chroma Walnut UI

> A ChromaDB visual desktop management tool built with PyWebView + React

**[中文文档](README_CN.md)**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" />
  <img src="https://img.shields.io/badge/ChromaDB-0.6+-purple" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" />
  <img src="https://img.shields.io/badge/Ant_Design-6-0170FE?logo=antdesign" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

## Screenshots

<p align="center">
  <img src="docs/screenshot-welcome.png" width="700" alt="Welcome screen" />
</p>

<p align="center">
  <img src="docs/screenshot-overview.png" width="700" alt="Overview page" />
</p>

---

## Introduction

Chroma Walnut UI is a lightweight desktop client for ChromaDB, running as a native window without a browser. It supports multi-connection management, document browsing and editing, and vector similarity search — ideal for developers debugging and managing ChromaDB data locally.

## Features

- **Multi-connection management** — Manage multiple ChromaDB connections (local directory / HTTP service) with Bearer Token auth support and one-click connectivity testing
- **Collection management** — Create, delete, and browse collections with document counts and metadata
- **Document browsing** — Paginated view of document IDs, content, and Metadata (color-coded tags by type)
- **Vector display** — Optional embedding vector display with preview and one-click JSON copy
- **Vector search** — Semantic similarity search with filter support (requires vector model configuration)
- **Vector model config** — Per-collection embedding model setup (OpenAI-compatible API), with presets for Ollama / OpenAI / LM Studio / Qwen, and auto-detected dimensions after test
- **Schema view** — Collection info and HNSW parameters
- **Internationalization** — Chinese / English switching
- **Theme** — Light / Dark / System

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop container | [PyWebView](https://pywebview.flowrl.com/) 6.x |
| Backend | Python 3.12+, [ChromaDB](https://docs.trychroma.com/) 0.6+ |
| Frontend framework | React 19 + TypeScript |
| UI library | Ant Design 6 |
| State management | Zustand 5 |
| i18n | i18next + react-i18next |
| Build tool | Vite 8 |
| Package managers | [uv](https://github.com/astral-sh/uv) (Python) / npm (frontend) |

## Requirements

- Python **3.12+**
- Node.js **18+**
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OS: Windows / macOS / Linux

> **Windows users**: PyWebView on Windows requires WebView2, which ships with Microsoft Edge — no extra installation needed.

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/deepin_sir/chroma-walnut-ui.git
cd chroma-walnut-ui
```

### 2. Install Python dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install pywebview chromadb
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Run

**Production mode** (auto-builds frontend then opens the window):

```bash
uv run python main.py
# or
python main.py
```

**Development mode** (hot-reload frontend, ideal for contributors):

```bash
# Terminal 1: start the frontend dev server
cd frontend
npm run dev

# Terminal 2: start PyWebView pointing to localhost:5173
uv run python main.py --dev
```

## Building a Windows Executable

Use the included one-click packaging script to produce a standalone `.exe`:

```bash
uv run python build_windows.py
```

The script automatically:

1. Checks that Node.js and PyInstaller are available (installs PyInstaller if missing)
2. Builds the React frontend (`npm run build`)
3. Generates the walnut `.ico` icon
4. Packages everything with PyInstaller into `dist/ChromaWalnutUI/`

**Output**

```
dist/
└── ChromaWalnutUI/
    ├── ChromaWalnutUI.exe   ← launch this
    └── ...                  ← supporting files (must stay alongside the .exe)
```

> Distribute the entire `dist/ChromaWalnutUI/` folder to end users — the `.exe` depends on files in the same directory.

**End-user requirements**

- Windows 10 1803+ or Windows 11 (WebView2 / Microsoft Edge is built-in)
- No Python or Node.js installation required

## Project Structure

```
chroma_ui/
├── main.py                  # Entry: PyWebView window setup, --dev flag
├── api.py                   # Python API layer exposed to JavaScript
├── chroma_manager.py        # Multi-connection ChromaDB manager
├── icon_utils.py            # Pure-Python walnut ICO generator + Win32 icon setter
├── build_windows.py         # One-click Windows packaging script
├── pyproject.toml           # Python project config
├── uv.lock                  # uv lockfile
└── frontend/
    ├── src/
    │   ├── api/bridge.ts        # Type-safe JS ↔ Python API wrapper
    │   ├── store/appStore.ts    # Zustand global state
    │   ├── i18n/                # zh.ts / en.ts translation files
    │   ├── layouts/             # App shell with sidebar
    │   ├── components/          # Modals, WalnutLogo, FilterBuilder, ErrorBoundary
    │   ├── pages/               # Overview, Collections, Detail, Settings
    │   └── tabs/                # Data, Schema, Search tabs
    └── ...
```

## Data Storage

Configs are stored in the user home directory:

| File | Description |
|---|---|
| `~/.chroma_walnut_ui/connections.json` | All connection configs (Token stored in plain text, local use only) |
| `~/.chroma_walnut_ui/collection_embeddings.json` | Per-collection vector model configs |

## Vector Model Setup

Chroma Walnut UI works with any OpenAI-compatible Embeddings API:

| Provider | API URL | Model example |
|---|---|---|
| Ollama | `http://localhost:11434/v1/embeddings` | `nomic-embed-text` |
| OpenAI | `https://api.openai.com/v1/embeddings` | `text-embedding-3-small` |
| LM Studio | `http://localhost:1234/v1/embeddings` | as configured |
| Qwen (DashScope) | `https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings` | `text-embedding-v3` |

> You must click **Test Connection** before saving. The dimension is auto-filled after a successful test.

## FAQ

**Q: Blank window on startup?**

A: Check that Python dependencies (especially `pywebview`) are installed correctly. Windows users should ensure Edge WebView2 is available.

**Q: No hot-reload in dev mode?**

A: Make sure `npm run dev` is running inside the `frontend/` directory, and PyWebView is started with the `--dev` flag.

**Q: "Dimension mismatch" error during vector search?**

A: The documents were embedded with a different model/dimension than the one currently configured. Use the same model that was used when adding the documents.

**Q: HTTP connection requires Token authentication?**

A: Fill in the Token field when adding/editing a connection. Chroma Walnut UI sends it as `Authorization: Bearer <token>`.

**Q: The packaged `.exe` fails to start?**

A: Ensure Microsoft Edge (WebView2 runtime) is installed. On Windows 10 1803+ and Windows 11 it is already built-in. If not, download the [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

## Contributing

Issues and PRs are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)

## Author

Made with ❤️ by **deepin_sir**
