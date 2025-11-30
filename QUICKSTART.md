# Quick Start Guide - Electron Desktop App

## What's New? 🎉

Your IDLIX Downloader now has a **beautiful desktop app** with:
- 🎨 Modern, user-friendly interface
- 📊 Real-time progress tracking
- 💾 Resume interrupted downloads
- 🔄 Background download management
- 📁 Easy file browser integration

## Quick Setup (3 Steps)

### 1. Run Setup Script

```bash
./setup_electron.sh
```

This will:
- ✅ Install all Python dependencies (FastAPI, Uvicorn, aiosqlite)
- ✅ Build the Python backend executable
- ✅ Install Electron dependencies
- ✅ Test the API server

### 2. Start Development Mode

```bash
cd electron-app
npm start
```

This opens the desktop app using the built Python backend.

### 3. Try It Out!

1. Paste an IDLIX movie URL
2. Click "Extract"
3. Select your preferred quality
4. Choose download location
5. Click "Start Download"
6. Watch real-time progress!

## Build Standalone App

### For Your Current Platform

```bash
cd electron-app
npm run build
```

Outputs to `electron-app/dist-electron/`

### For Specific Platforms

```bash
npm run build:linux   # Linux AppImage/deb
npm run build:win     # Windows installer
npm run build:mac     # macOS dmg
```

## Project Structure

```
Your CLI tool (existing) ──┐
                           ├─→ Backend API (FastAPI) ──→ Electron App (Desktop UI)
                           └─→ Still works standalone!
```

**Both work simultaneously:**
- **CLI Mode**: `./dist/idlix-downloader -u "URL" -q 1080p`
- **API Mode**: `./dist/idlix-downloader --api-server --port 8765`
- **Desktop App**: Electron spawns API mode automatically

## Features Comparison

| Feature | CLI | Electron App |
|---------|-----|--------------|
| Download videos | ✅ | ✅ |
| Select quality | ✅ | ✅ |
| Resume downloads | ✅ | ✅ |
| Visual progress bar | ✅ | ✅✅ (Better!) |
| Multiple downloads | ❌ | ✅ |
| Download history | ❌ | ✅ |
| File browser integration | ❌ | ✅ |
| Settings persistence | ❌ | ✅ |

## Files Added

```
backend/
├── __init__.py
├── database.py              # SQLite persistence
├── api_server.py            # FastAPI REST API
└── requirements-api.txt     # API dependencies

electron-app/
├── package.json
├── src/
│   ├── main/
│   │   ├── index.js        # Electron main process
│   │   └── preload.js      # IPC bridge
│   └── renderer/
│       ├── index.html      # UI layout
│       ├── app.js          # Frontend logic
│       └── style.css       # Beautiful styling

create_spec_api.py           # PyInstaller spec generator
setup_electron.sh            # One-command setup
ELECTRON_README.md           # Full documentation
```

## Troubleshooting

### "Backend not ready"
```bash
# Test backend manually:
./dist/idlix-downloader --api-server --port 8765

# Should output:
# {"status": "ready", "port": 8765}
```

### "Cannot find module 'electron'"
```bash
cd electron-app
npm install
```

### Port already in use
The app automatically finds a free port. If issues persist:
```bash
# Kill any running instances:
pkill -f "idlix-downloader --api-server"
```

## Documentation

- **Quick Start**: This file
- **Full API Docs**: `ELECTRON_README.md`
- **CLI Usage**: `README.md`
- **Build Instructions**: `BUILD_INSTRUCTIONS.md`

## Next Steps

1. **Customize**: Edit `electron-app/src/renderer/` files
2. **Add Features**: Extend API in `backend/api_server.py`
3. **Distribute**: Build installers with `npm run build`

Enjoy your new desktop app! 🚀
