@echo off
REM Build script for Windows standalone executable

echo ===================================
echo IDLIX Downloader - Windows Build
echo ===================================

echo.
echo [1/6] Installing Python dependencies...
python -m pip install curl-cffi beautifulsoup4 m3u8 pyperclip pycryptodome certifi

echo.
echo [2/6] Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo [3/6] Downloading FFmpeg for Windows...
if not exist "ffmpeg.exe" (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'"
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force"
    move ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe .
    rmdir /s /q ffmpeg-master-latest-win64-gpl
    del ffmpeg.zip
    echo FFmpeg downloaded
) else (
    echo FFmpeg already exists
)

echo.
echo [4/6] Creating PyInstaller spec file...
python create_spec_windows.py

echo.
echo [5/6] Verifying dependencies...
python -c "import curl_cffi; import bs4; import m3u8; import pyperclip; import Crypto; import certifi; print('✓ All dependencies installed')"
if errorlevel 1 (
    echo.
    echo ✗ Missing dependencies! Install them first:
    echo   pip install curl-cffi beautifulsoup4 m3u8 pyperclip pycryptodome certifi
    exit /b 1
)

echo.
echo [6/6] Building executable...
pyinstaller --clean idlix_windows.spec

if exist "dist\idlix-downloader.exe" (
    echo.
    echo =========================================
    echo Build successful!
    echo =========================================
    echo Executable: dist\idlix-downloader.exe
    for %%A in (dist\idlix-downloader.exe) do echo Size: %%~zA bytes
    echo.
    echo Test it: dist\idlix-downloader.exe --help
    echo =========================================
) else (
    echo.
    echo Build failed!
    exit /b 1
)
