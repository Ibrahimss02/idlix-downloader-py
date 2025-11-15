#!/usr/bin/env python3
"""Create PyInstaller spec file for Windows build"""

spec_content = """# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect certifi CA bundle
certifi_datas = collect_data_files('certifi')

a = Analysis(
    ['idlix.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.')],
    datas=[('crypto_helper.py', '.')] + certifi_datas,
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
    ],
    hookspath=['hooks'],
    hooksconfig={},
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

with open('idlix_windows.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)

print('[OK] Spec file created: idlix_windows.spec')
print('[OK] Using custom hooks directory for curl_cffi')
print('[OK] Added certifi runtime hook to set CA bundle path')
print('[OK] Added crash handler runtime hook')
