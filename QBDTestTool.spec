# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Get absolute path to src directory
src_path = os.path.abspath('src')

a = Analysis(
    ['src\\app.py'],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=[
        'win32com',
        'win32com.client',
        'pythoncom',
        'pywintypes',
        'win32api',
        'win32gui',
        'win32con',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QBDTestTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
