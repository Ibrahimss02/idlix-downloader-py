# Cross-Platform Build Instructions

The IDLIX downloader can be built as a standalone executable for different platforms. **You must build on the target platform** for best compatibility.

## 📦 Platform-Specific Builds

### 🐧 Linux (Current)

```bash
./build_executable.sh
```

**Output:** `dist/idlix-downloader` (Linux x64)

---

### 🪟 Windows

**Method 1: Build on Windows (Recommended)**

1. **Copy files to Windows:**
   ```powershell
   # From WSL, copy to Windows directory
   cp -r ~/idlix-downloader-py /mnt/c/Users/YourName/idlix-build/
   ```

2. **Open PowerShell/CMD on Windows:**
   ```cmd
   cd C:\Users\YourName\idlix-build
   ```

3. **Install Python dependencies:**
   ```cmd
   pip install curl-cffi beautifulsoup4 m3u8 pyperclip pycryptodome
   ```

4. **Run Windows build script:**
   ```cmd
   build_windows.bat
   ```

**Output:** `dist\idlix-downloader.exe` (~100-150 MB)

**Method 2: Using WSL (Not Recommended - may have compatibility issues)**

```bash
# Install Wine in WSL
sudo apt update
sudo apt install wine wine64

# Install Python for Windows via Wine
# ... this is complex and not recommended
```

---

### 🍎 macOS

**Build on macOS:**

1. **Install dependencies:**
   ```bash
   # Install Homebrew if not installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Python
   brew install python@3.11
   
   # Install dependencies
   pip3 install curl-cffi beautifulsoup4 m3u8 pyperclip pycryptodome pyinstaller
   ```

2. **Download FFmpeg for macOS:**
   ```bash
   wget https://evermeet.cx/ffmpeg/ffmpeg-6.0.zip
   unzip ffmpeg-6.0.zip
   chmod +x ffmpeg
   ```

3. **Modify spec file for macOS:**
   ```bash
   # Change 'ffmpeg.exe' to 'ffmpeg' in spec file
   # Windows uses .exe extension, macOS doesn't
   ```

4. **Build:**
   ```bash
   pyinstaller --clean idlix.spec
   ```

**Output:** `dist/idlix-downloader` (macOS executable)

---

## 🌐 Cross-Compilation (Advanced)

Cross-compiling (building for another OS) is **not recommended** and often doesn't work properly. PyInstaller bundles the Python runtime and platform-specific libraries.

### Why Cross-Compilation Doesn't Work Well:

- ❌ **Binary incompatibility:** Linux binaries won't run on Windows
- ❌ **Different library formats:** `.so` (Linux) vs `.dll` (Windows) vs `.dylib` (macOS)
- ❌ **Platform-specific code:** System calls differ between OS
- ❌ **FFmpeg binaries:** Each platform needs its own FFmpeg build

### Alternative: GitHub Actions CI/CD

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on: [push]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: ./build_executable.sh
      - uses: actions/upload-artifact@v3
        with:
          name: idlix-linux
          path: dist/idlix-downloader

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: build_windows.bat
      - uses: actions/upload-artifact@v3
        with:
          name: idlix-windows
          path: dist/idlix-downloader.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: ./build_executable.sh
      - uses: actions/upload-artifact@v3
        with:
          name: idlix-macos
          path: dist/idlix-downloader
```

This builds for all platforms automatically on GitHub!

---

## 📝 Summary

| Platform | Build Command | Output File | Build Location |
|----------|---------------|-------------|----------------|
| Linux | `./build_executable.sh` | `dist/idlix-downloader` | Linux machine |
| Windows | `build_windows.bat` | `dist/idlix-downloader.exe` | Windows machine |
| macOS | `./build_executable.sh` | `dist/idlix-downloader` | macOS machine |

**Best Practice:** Build on the target platform or use GitHub Actions for multi-platform builds.

---

## 🚀 Quick Start for Windows Users

Since you're using WSL, here's the fastest way:

1. **Copy to Windows:**
   ```bash
   # In WSL
   cp -r ~/idlix-downloader-py /mnt/c/Users/$USER/Desktop/idlix-build/
   ```

2. **Open PowerShell as Administrator on Windows**

3. **Navigate:**
   ```powershell
   cd C:\Users\$env:USERNAME\Desktop\idlix-build
   ```

4. **Install Python packages:**
   ```powershell
   pip install curl-cffi beautifulsoup4 m3u8 pyperclip pycryptodome pyinstaller
   ```

5. **Build:**
   ```powershell
   .\build_windows.bat
   ```

6. **Test:**
   ```powershell
   .\dist\idlix-downloader.exe --help
   ```

Done! You now have a Windows `.exe` file! 🎉
