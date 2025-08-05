# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Try to get FFmpeg from imageio_ffmpeg
try:
    from imageio_ffmpeg import get_ffmpeg_exe
    ffmpeg_path = get_ffmpeg_exe()
    ffmpeg_binaries = [(ffmpeg_path, '.')]
except Exception as e:
    print(f"Warning: Could not get FFmpeg from imageio_ffmpeg: {e}")
    ffmpeg_binaries = []

# Collect imageio_ffmpeg data if available
try:
    imageio_datas = collect_data_files('imageio_ffmpeg')
except:
    imageio_datas = []

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=ffmpeg_binaries,
    datas=imageio_datas,
    hiddenimports=[
        'sip',
        'PyQt5.sip',
        'imageio_ffmpeg',
        'imageio_ffmpeg.binaries'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# For Linux
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hls-converter-linux',
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
)