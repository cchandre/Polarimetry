# -*- mode: python ; coding: utf-8 -*-

DATA_FILES = [("icons/*.png", "icons"), ("polarimetry.json", "."), ("/Users/cchandre/opt/anaconda3/lib/python3.8/site-packages/customtkinter/", "customtkinter/")]
BINARY_FILES = [("calibration/*.mat", "calibration"), ("diskcones/*.mat", "diskcones")]

block_cipher = None

VERSION = "2.2"

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
    [],
    exclude_binaries=True,
    name='PyPOLAR',
    debug=False,
    bootloader_ignore_signals=False,
    #runtime_tmpdir=None,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PyPOLAR",
)

#app = BUNDLE(
#    exe,
#    name='PyPOLAR.app',
#    icon='main_icon.icns',
#    bundle_identifier=None,
#    version=VERSION,
#         info_plist={
#            'NSPrincipalClass': 'NSApplication',
#            'NSAppleScriptEnabled': False,
#            'CFBundleDocumentTypes': [
#                {
#                    'CFBundleTypeName': 'My File Format',
#                    'CFBundleTypeIconFile': 'main_icon.icns',
#                    'LSItemContentTypes': ['com.example.myformat'],
#                    'LSHandlerRank': 'Owner'
#                    }
#                ]
#            },
#)
