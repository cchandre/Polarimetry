# -*- mode: python ; coding: utf-8 -*-

DATA_FILES = [("icons/*.png", "icons"), ("polarimetry.json", ".")]
BINARY_FILES = [("calibration/*.mat", "calibration"), ("diskcones/*.mat", "diskcones")]

block_cipher = None

with open("__init__.py") as f:
        info = {}
        for line in f:
            if line.startswith("version"):
                exec(line, info)
                break

VERSION = info["version"]

a = Analysis(
    ['PyPOLAR.py'],
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
    name='PyPOLAR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='PyPOLAR.app',
    icon='main_icon.icns',
    bundle_identifier=None,
    version=VERSION,
         info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'My File Format',
                    'CFBundleTypeIconFile': 'main_icon.icns',
                    'LSItemContentTypes': ['com.example.myformat'],
                    'LSHandlerRank': 'Owner'
                    }
                ]
            },
)
