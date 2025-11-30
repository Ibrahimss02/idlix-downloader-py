# 🎬 IDLIX Downloader - Desktop App

Beautiful desktop application for downloading videos from IDLIX streaming platform with real-time progress tracking and subtitle support.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)

## ✨ Features

- 🎨 **Modern Desktop UI** - Clean, intuitive Electron-based interface
- 📊 **Real-time Progress** - Live download progress with speed and ETA
- 💾 **Resume Downloads** - Automatically resume interrupted downloads
- 📝 **Subtitle Support** - Auto-download subtitles when available
- 🎯 **Quality Selection** - Choose from multiple video quality options
- ⚙️ **Settings Panel** - Customize download paths and threads
- 🔄 **Background Tasks** - Download queue management
- 🚀 **Multi-threaded** - Fast downloads with configurable thread count

## 📦 Installation

### Quick Start (Recommended)

Download the latest release for your platform:

**Windows:**
- Download `IDLIX-Downloader-Setup-*.exe`
- Run the installer
- FFmpeg is bundled (no additional requirements)

**Linux:**
- Download `IDLIX-Downloader-*.AppImage` (portable) or `*.deb` (Debian/Ubuntu)
- For AppImage: `chmod +x IDLIX-Downloader-*.AppImage && ./IDLIX-Downloader-*.AppImage`
- For .deb: `sudo dpkg -i idlix-downloader_*.deb`
- Requires: `ffmpeg` (install via `sudo apt install ffmpeg`)

**macOS:**
- Download `IDLIX-Downloader-*.dmg`
- Open and drag to Applications
- Requires: `ffmpeg` (install via `brew install ffmpeg`)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Ibrahimss02/idlix-downloader-py.git
cd idlix-downloader-py

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r backend/requirements-api.txt

# Build Python backend
pyinstaller --clean idlix_windows_api.spec

# Setup Electron app
cd electron-app
npm install
npm start  # Development mode
npm run build:linux    # Build for Linux
npm run build:win      # Build for Windows
npm run build:mac      # Build for macOS
```

## 🚀 Usage

1. **Enter Video URL** - Paste IDLIX movie/series URL
2. **Extract** - Click to fetch available quality options
3. **Select Quality** - Choose your preferred video quality
4. **Configure Download** - Set output path and filename
5. **Download** - Click to start (subtitle checkbox auto-detected)
6. **Track Progress** - Watch real-time download progress
7. **Resume/Cancel** - Resume interrupted or cancel active downloads

## 🛠️ Technical Stack

### Backend (Python)
- **FastAPI** - Modern async REST API
- **Uvicorn** - ASGI server
- **curl-cffi** - Cloudflare bypass
- **aiosqlite** - Async database
- **PyInstaller** - Standalone executable

### Frontend (Electron)
- **Electron 28** - Desktop app framework
- **Node.js 20+** - JavaScript runtime
- **electron-builder** - Multi-platform packaging
- **electron-store** - Settings persistence

## 📁 Project Structure

```
idlix-downloader-py/
├── backend/              # Python FastAPI backend
│   ├── api_server.py    # REST API endpoints
│   └── database.py      # SQLite database layer
├── electron-app/        # Electron desktop app
│   ├── src/
│   │   ├── main/       # Main process (Node.js)
│   │   └── renderer/   # Renderer process (HTML/CSS/JS)
│   └── package.json    # Electron dependencies
├── idlix.py            # Core downloader logic
├── crypto_helper.py    # AES decryption utilities
├── build_backend.sh    # Backend build script
└── idlix_windows_api.spec  # PyInstaller spec
```

## 🔧 Building from Source

### Prerequisites
- Python 3.10+
- Node.js 20+
- FFmpeg (for merging video segments)
- PyInstaller 6.0+

### Build Backend

**Linux/macOS:**
```bash
./build_backend.sh
```

**Windows:**
```bash
python create_spec_api.py
pyinstaller --clean idlix_windows_api.spec
```

### Build Desktop App

```bash
cd electron-app
npm install
npm run build:linux    # Outputs: .AppImage, .deb
npm run build:win      # Outputs: .exe installer
npm run build:mac      # Outputs: .dmg
```

## 🐛 Troubleshooting

### Backend fails to start
- Check if port is already in use
- Ensure Python backend was built correctly
- Check logs in terminal output

### FFmpeg not found (Linux/macOS)
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### Download stuck at 100%
- The app is merging video segments with FFmpeg
- This may take 30-60 seconds for large files
- Check terminal output for detailed logs

### Cloudflare errors
- curl-cffi handles Cloudflare automatically
- Update dependencies: `pip install --upgrade curl-cffi`

## 📝 Development

### Run in Development Mode

```bash
# Terminal 1: Start backend (built executable)
./dist/idlix-downloader --api-server

# Terminal 2: Start Electron
cd electron-app
npm start
```

### Debug Mode

Backend logs appear in the terminal where you launched the app.
Frontend console: Open Developer Tools (Ctrl+Shift+I / Cmd+Option+I)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **curl-cffi** for Cloudflare bypass
- **Electron** for cross-platform desktop framework
- **FastAPI** for modern Python API
- **FFmpeg** for video processing

## 📧 Contact

- GitHub: [@Ibrahimss02](https://github.com/Ibrahimss02)
- Repository: [idlix-downloader-py](https://github.com/Ibrahimss02/idlix-downloader-py)

---

Made with 💜 by @ibrahimss02
