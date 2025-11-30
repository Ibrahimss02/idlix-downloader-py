# IDLIX Downloader - Quick Start

Multi-threaded IDLIX video downloader with caching, resume support, and standalone executables.

## 📦 Files

### Core Files
- **`idlix.py`** - Main application
- **`crypto_helper.py`** - Decryption module
- **`requirements.txt`** - Python dependencies

### Build Files
- **`build_executable.sh`** - Linux build script
- **`build_windows.bat`** - Windows build script
- **`create_spec_windows.py`** - PyInstaller spec generator
- **`pyi_rth_certifi.py`** - SSL certificate runtime hook
- **`pyi_rth_crash_handler.py`** - Crash logging hook
- **`hooks/hook-curl_cffi.py`** - PyInstaller curl_cffi hook

### Documentation
- **`README.md`** - Main documentation
- **`BUILD_INSTRUCTIONS.md`** - Detailed build guide
- **`PLATFORM_BUILDS.md`** - Cross-platform build info
- **`QUICKSTART.md`** - This file

## 🚀 Quick Usage

### Run from Python
```bash
# Interactive mode
python idlix.py

# Direct download
python idlix.py -u "URL" -q 1080p --auto
```

### Build Standalone Executable

**Linux:**
```bash
./build_executable.sh
./dist/idlix-downloader
```

**Windows:**
```cmd
build_windows.bat
dist\idlix-downloader.exe
```

## ✨ Features

✅ Multi-threaded downloads (16 threads)
✅ Segment caching & resume
✅ Progress bar (seg/s + MB/s)
✅ Error handling & retry (3x)
✅ FFmpeg merging with progress
✅ Cloudflare bypass
✅ Standalone executables

## 📁 Generated Files

- **`build/`** - Build artifacts (ignored)
- **`dist/`** - Executables (ignored)
- **`~/.cache/idlix-downloader/`** - Segment cache
- **`idlix_crash.log`** - Error logs (if crashed)

## 🧹 Clean Workspace

```bash
# Remove build artifacts
rm -rf build/ dist/

# Full clean
git clean -fdx
```

## 📖 More Info

- Build instructions: `BUILD_INSTRUCTIONS.md`
- Cross-platform: `PLATFORM_BUILDS.md`
- Full docs: `README.md`
