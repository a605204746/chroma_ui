# Chroma Walnut UI

> A ChromaDB visual desktop management tool built with PyWebView + React

**[中文文档](README_CN.md)**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" />
  <img src="https://img.shields.io/badge/ChromaDB-0.6+-purple" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react" />
  <img src="https://img.shields.io/badge/Ant_Design-6-0170FE?logo=antdesign" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" />
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

Chroma Walnut UI is a lightweight desktop client for ChromaDB, running as a native window without a browser. It supports multi-connection management, collection browsing and editing, document management, and vector similarity search — ideal for developers debugging and managing ChromaDB data locally.

## Features

- **Multi-connection management** — Manage multiple ChromaDB connections (local directory / HTTP service) with Bearer Token auth support, one-click connectivity testing, and collapsible sidebar
- **Collection management** — Create, edit (rename + metadata), and delete collections; metadata key-value form with duplicate key validation
- **Document browsing** — Paginated view (10 / 20 / 30 per page) of document IDs, content, and Metadata; color-coded tags; full JSON modal; text selection enabled
- **Seed test data** — One-click insert of 50 sample documents for quick testing (requires vector model configured)
- **Vector display** — Optional embedding column with preview and one-click copy
- **Vector search** — Semantic similarity search with filter builder (requires vector model configuration)
- **Vector model config** — Per-collection OpenAI-compatible embedding API setup, with presets for Ollama / OpenAI / LM Studio / Qwen; auto-detected dimensions after connection test
- **Schema view** — Collection info, dimension, and inferred metadata field types
- **Responsive layout** — Sidebar auto-collapses below 1100 px; fluid font and padding scaling
- **Single instance** — Prevents duplicate windows via socket lock
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
- OS: Windows 10 1803+ / macOS 10.15+ / Ubuntu 20.04+

> **Windows**: WebView2 ships with Microsoft Edge — no extra installation needed.  
> **macOS**: No additional dependencies required.  
> **Linux**: Requires `libwebkit2gtk-4.1-0` and `libgtk-3-0` system packages.

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

> **Linux only**: install GTK/WebKitGTK system packages first:
> ```bash
> sudo apt-get install -y python3-gi python3-gi-cairo \
>   gir1.2-gtk-3.0 gir1.2-webkit2-4.1 libwebkit2gtk-4.1-dev
> ```

### 3. Install frontend dependencies

```bash
cd frontend && npm install && cd ..
```

### 4. Run

**Production mode** (builds frontend automatically, then opens the window):

```bash
uv run python main.py
```

**Development mode** (hot-reload, ideal for contributors):

```bash
# Terminal 1 — frontend dev server
cd frontend && npm run dev

# Terminal 2 — PyWebView pointing to localhost:5173
uv run python main.py --dev
```

## Building a Distributable Package

Use the included cross-platform packaging script. Run it on the target OS — PyInstaller cannot cross-compile.

```bash
# Release build (no console window)
uv run python build.py

# Debug build (console window visible — useful for diagnosing startup errors)
uv run python build.py --debug
```

The script automatically:

1. Checks Python, Node.js, and PyInstaller (installs if missing)
2. Builds the React frontend (`npm run build`)
3. Generates the platform-specific icon (`.ico` / `.icns` / `.png`)
4. Packages with PyInstaller using the correct platform flags
5. Archives the output into a distributable file

### Output per platform

| Platform | Output directory | Archive |
|---|---|---|
| Windows | `dist/ChromaWalnutUI/` | `dist/ChromaWalnutUI-Windows.zip` |
| macOS | `dist/ChromaWalnutUI.app` | `dist/ChromaWalnutUI-macOS.dmg` |
| Linux | `dist/ChromaWalnutUI/` | `dist/ChromaWalnutUI-Linux.tar.gz` |

### End-user runtime requirements

| Platform | Requirement |
|---|---|
| Windows | Windows 10 1803+ / Windows 11 (WebView2 built-in) |
| macOS | macOS 10.15 Catalina+ |
| Linux | `libwebkit2gtk-4.1-0`, `libgtk-3-0` |

## Automated Releases via GitHub Actions

Pushing a version tag triggers a three-platform build and creates a GitHub Release automatically:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow (`.github/workflows/release.yml`) runs `build.py` on `windows-latest`, `macos-latest`, and `ubuntu-22.04` in parallel, then attaches all three archives to the release. Tags containing `-` (e.g. `v1.0.0-beta`) are automatically marked as pre-release.

## Project Structure

```
chroma_ui/
├── main.py                  # Entry: PyWebView window, single-instance lock, geometry
├── api.py                   # Python API layer exposed to JavaScript
├── chroma_manager.py        # Multi-connection ChromaDB manager
├── icon_utils.py            # Pure-Python walnut ICO/ICNS/PNG generator
├── logger.py                # Unified logging (RotatingFileHandler, 5 MB × 3)
├── build.py                 # Cross-platform one-click packaging script
├── pyproject.toml
├── uv.lock
├── .github/
│   └── workflows/
│       └── release.yml      # CI/CD: tag → 3-platform build → GitHub Release
└── frontend/
    └── src/
        ├── api/bridge.ts        # Type-safe JS ↔ Python API wrapper
        ├── store/appStore.ts    # Zustand global state
        ├── i18n/                # zh.ts / en.ts translation files
        ├── layouts/             # App shell with collapsible sidebar
        ├── components/          # Modals, WalnutLogo, FilterBuilder
        ├── pages/               # Overview, Collections, CollectionDetail
        └── tabs/                # Data, Schema, Search tabs
```

## Data Storage

All data is stored under the user home directory — no registry, no system directories.

| Path | Description |
|---|---|
| `~/.chroma_walnut_ui/connections.json` | Connection configs (Token stored in plain text — local use only) |
| `~/.chroma_walnut_ui/collection_embeddings.json` | Per-collection vector model configs |
| `~/.chroma_walnut_ui/app.log` | Application log (rotates at 5 MB, keeps 3 backups) |

## Vector Model Setup

Chroma Walnut UI works with any OpenAI-compatible Embeddings API:

| Provider | API URL | Model example |
|---|---|---|
| Ollama | `http://localhost:11434/v1/embeddings` | `nomic-embed-text` |
| OpenAI | `https://api.openai.com/v1/embeddings` | `text-embedding-3-small` |
| LM Studio | `http://localhost:1234/v1/embeddings` | as configured |
| Qwen (DashScope) | `https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings` | `text-embedding-v3` |

> Click **Test Connection** before saving. The dimension is auto-filled after a successful test.  
> Each collection can have its own model — make sure it matches the model used when documents were added.

## FAQ

**Q: Blank window on startup?**

A: Check that Python dependencies (especially `pywebview`) are installed. Windows users should ensure Edge WebView2 is available. Check `~/.chroma_walnut_ui/app.log` for details.

**Q: No hot-reload in dev mode?**

A: Make sure `npm run dev` is running inside `frontend/`, and PyWebView is started with `--dev`.

**Q: "Dimension mismatch" error during vector search?**

A: The documents were embedded with a different model/dimension. Use the same model that was used when adding the documents.

**Q: HTTP connection with Token authentication?**

A: Fill in the Token field when adding/editing a connection. It is sent as `Authorization: Bearer <token>`.

**Q: The packaged app fails to start on Windows?**

A: Ensure Microsoft Edge (WebView2 runtime) is installed. On Windows 10 1803+ and Windows 11 it is built-in. Otherwise download the [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

**Q: macOS shows "app is damaged" or security warning?**

A: The app is not code-signed. Right-click → Open, or go to System Settings → Privacy & Security → Allow. For distribution, sign with `codesign`.

## Contributing

Issues and PRs are welcome. For major changes, please open an issue first to discuss.

## License

[MIT](LICENSE)

## Author

Made with ❤️ by **deepin_sir**
