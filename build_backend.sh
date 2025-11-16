#!/bin/bash
# Build Script for IDLIX Downloader with Electron UI
# This script builds the Python backend with API support

set -e

echo "=========================================="
echo "IDLIX Downloader - Build Backend with API"
echo "=========================================="
echo ""

# Check dependencies
echo "[1/3] Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3.8+"
    exit 1
fi

if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip not found. Please install pip"
    exit 1
fi

echo "✓ Python $(python3 --version | cut -d' ' -f2)"
echo ""

# Install Python dependencies
echo "[2/3] Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt 2>&1 | grep -E "(Successfully installed|Requirement already satisfied)" | head -5 || true
python3 -m pip install --user -r backend/requirements-api.txt 2>&1 | grep -E "(Successfully installed|Requirement already satisfied)" | head -5 || true
python3 -m pip install --user pyinstaller 2>&1 | grep -E "(Successfully installed|Requirement already satisfied)" || true
echo "✓ Dependencies ready"
echo ""

# Build backend
echo "[3/3] Building Python backend with API support..."
echo "Generating PyInstaller spec..."
python3 create_spec_api.py

if [ -f "idlix_windows_api.spec" ]; then
    echo "Building executable..."
    python3 -m PyInstaller --clean idlix_windows_api.spec
else
    echo "❌ Failed to generate spec file"
    exit 1
fi

# Verify build
if [ -f "./dist/idlix-downloader" ]; then
    SIZE=$(du -h ./dist/idlix-downloader | cut -f1)
    echo ""
    echo "=========================================="
    echo "✓ Build complete!"
    echo "=========================================="
    echo "Backend executable: ./dist/idlix-downloader ($SIZE)"
    echo ""
    echo "Test the backend:"
    echo "  ./dist/idlix-downloader --api-server --port 8765"
    echo ""
    echo "For Electron app setup, see: ELECTRON_README.md"
    echo "=========================================="
else
    echo ""
    echo "❌ Build failed - executable not found"
    exit 1
fi
