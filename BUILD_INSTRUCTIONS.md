# Building IDLIX Downloader Standalone Executable

This script bundles the IDLIX downloader with all dependencies (including FFmpeg) into a single executable file that users can run without installing anything.

## Prerequisites

- Python 3.8+
- pip
- Internet connection (for downloading FFmpeg)

## Build Instructions

### 1. Run the build script:

```bash
./build_executable.sh
```

This will:
- Install PyInstaller
- Download FFmpeg static binary (~80MB)
- Create PyInstaller spec file
- Build standalone executable

### 2. Find your executable:

```
dist/idlix-downloader
```

The executable is typically **~100-150 MB** and includes:
- Python runtime
- All Python dependencies (curl-cffi, beautifulsoup4, m3u8, etc.)
- FFmpeg binary
- Your application code

## Testing the Executable

```bash
# Test it works
./dist/idlix-downloader --help

# Interactive mode
./dist/idlix-downloader

# Command-line mode
./dist/idlix-downloader -u "https://idlix.example/movie" -q 1080p --auto
```

## Distribution

Users can simply download and run the executable:

```bash
# Make it executable (if needed)
chmod +x idlix-downloader

# Run it
./idlix-downloader
```

**No Python, no pip, no FFmpeg installation needed!** ✨

## Build for Different Platforms

### Linux (current)
```bash
./build_executable.sh  # Builds for Linux x64
```

### Windows
You'll need to build on Windows or use cross-compilation tools:
1. Install Python on Windows
2. Run: `python -m pip install pyinstaller`
3. Download FFmpeg.exe for Windows
4. Modify spec file to include ffmpeg.exe
5. Run: `pyinstaller idlix.spec`

### macOS
Similar process on macOS:
1. Use Homebrew to install dependencies
2. Download FFmpeg for macOS
3. Run build script

## Troubleshooting

### "ffmpeg: not found" error
- Make sure FFmpeg static binary is downloaded correctly
- Check that it's bundled in the executable (check spec file)

### Large executable size
- This is normal - includes entire Python runtime + FFmpeg
- Typical size: 100-150 MB
- Use UPX compression (already enabled) to reduce size

### Import errors
- Add missing modules to `hiddenimports` in spec file
- Rebuild with `./build_executable.sh`

## Clean Build

```bash
# Remove build artifacts
rm -rf build/ dist/ __pycache__/
rm -f idlix.spec

# Rebuild from scratch
./build_executable.sh
```

## File Structure After Build

```
idlix-downloader-py/
├── idlix.py                 # Source code (bundled version)
├── idlix_original.py        # Original source (backup)
├── crypto_helper.py         # Crypto module
├── ffmpeg                   # FFmpeg binary (downloaded)
├── idlix.spec              # PyInstaller spec
├── build/                  # Build artifacts (temp)
├── dist/
│   └── idlix-downloader    # ⭐ YOUR EXECUTABLE
└── build_executable.sh     # This build script
```

## Notes

- **Single file executable**: Everything bundled, nothing external needed
- **Cross-platform**: Build on target platform for best compatibility
- **Segment caching**: Cache directory still works (`~/.cache/idlix-downloader/`)
- **Resume support**: All features work exactly like Python version
