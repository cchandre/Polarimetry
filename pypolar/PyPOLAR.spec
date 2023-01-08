"""
Environment: polarimetry_env

Usage:
    pyinstaller pypolar.spec

Recommendations:
    - change CTK_PATH using pip3 show customtkinter
    - If you experience problems packaging your apps, your first step should always be to update your PyInstaller and hooks package the latest versions using:
        pip3 install --upgrade PyInstaller pyinstaller-hooks-contrib
"""


# -*- mode: python ; coding: utf-8 -*-

import sys

with open("__init__.py") as f:
        info = {}
        for line in f:
            if line.startswith("version"):
                exec(line, info)
                break

block_cipher = None

VERSION = info["version"]

CTK_PATH = "/Users/c.chandre/opt/anaconda3/envs/polarimetry_env/lib/python3.8/site-packages/customtkinter/"

DATA_FILES = [("icons/*.png", "icons/"), ("polarimetry.json", "."), (CTK_PATH, "customtkinter/")]
BINARY_FILES = [("calibration/*.mat", "calibration/"), ("diskcones/*.mat", "diskcones/")]

a = Analysis(['PyPOLAR.py'],
    pathex=[],
    binaries=BINARY_FILES,
    datas=DATA_FILES,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyPOLAR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='PyPOLAR')

if sys.platform == 'darwin':
    app = BUNDLE(coll,
        name='PyPOLAR.app',
        icon='main_icon.icns',
        bundle_identifier=None,
        version=VERSION,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,},)
