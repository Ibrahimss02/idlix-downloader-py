#!/usr/bin/env python3
"""Create PyInstaller spec file with API support (cross-platform)"""
import sys
import os

# Detect platform and set FFmpeg binary name
if sys.platform == 'win32':
    ffmpeg_name = 'ffmpeg.exe'
else:
    ffmpeg_name = 'ffmpeg'

# Check if FFmpeg exists
ffmpeg_path = os.path.join(os.path.dirname(__file__), ffmpeg_name)
if not os.path.exists(ffmpeg_path):
    print(f"[WARNING] FFmpeg not found at {ffmpeg_path}")
    print("[INFO] PyInstaller will fail if FFmpeg is required")

spec_content = """# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect certifi CA bundle
certifi_datas = collect_data_files('certifi')

# Collect FastAPI and Uvicorn submodules
fastapi_imports = collect_submodules('fastapi')
uvicorn_imports = collect_submodules('uvicorn')
pydantic_imports = collect_submodules('pydantic')

a = Analysis(
    ['idlix.py'],
    pathex=[],
    binaries=[('FFMPEG_BINARY', '.')],
    datas=[
        ('crypto_helper.py', '.'),
        ('backend/database.py', 'backend'),
        ('backend/api_server.py', 'backend'),
        ('backend/__init__.py', 'backend')
    ] + certifi_datas,
    hiddenimports=[
        'curl_cffi',
        'curl_cffi.requests',
        'curl_cffi.const',
        'curl_cffi.curl',
        'curl_cffi.aio',
        '_cffi_backend',
        'certifi',
        'bs4',
        'bs4.builder',
        'bs4.builder._html5lib',
        'bs4.builder._htmlparser',
        'bs4.builder._lxml',
        'm3u8',
        'pyperclip',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'Crypto.Cipher._mode_ecb',
        'Crypto.Cipher._mode_cbc',
        'Crypto.Util',
        'Crypto.Util.Padding',
        'Crypto.Random',
        'Crypto.Hash',
        'Crypto.Hash.SHA256',
        # FastAPI and dependencies
        'fastapi',
        'fastapi.applications',
        'fastapi.routing',
        'fastapi.params',
        'fastapi.encoders',
        'starlette',
        'starlette.applications',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.routing',
        'starlette.responses',
        'starlette.requests',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pydantic',
        'pydantic.dataclasses',
        'pydantic.types',
        'aiosqlite',
        'multipart',
        'multipart.multipart',
    ] + fastapi_imports + uvicorn_imports + pydantic_imports,
    hookspath=['hooks'],
    hooksconfig=dict(),
    runtime_hooks=['pyi_rth_certifi.py', 'pyi_rth_crash_handler.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='idlix-downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""

# Replace FFMPEG_BINARY placeholder with actual filename
spec_content = spec_content.replace('FFMPEG_BINARY', ffmpeg_name)

with open('idlix_windows_api.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)

print('[OK] API-enabled spec file created: idlix_windows_api.spec')
print(f'[OK] Using FFmpeg binary: {ffmpeg_name}')
print('[OK] This spec includes FastAPI, Uvicorn, and database support')
print('[OK] Use: pyinstaller --clean idlix_windows_api.spec')
