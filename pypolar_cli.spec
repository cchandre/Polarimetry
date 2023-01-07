# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

VERSION = "2.2"

DATA_FILES = [("pypolar/icons/*.png", "pypolar/icons"), ("pypolar/polarimetry.json", "pypolar"), ("/Users/cchandre/opt/anaconda3/lib/python3.8/site-packages/customtkinter/", "customtkinter/")]
BINARY_FILES = [("pypolar/calibration/*.mat", "pypolar/calibration"), ("pypolar/diskcones/*.mat", "pypolar/diskcones")]

a = Analysis(
    ['pypolar_cli.py'],
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
    icon='pypolar/main_icon.icns',
    bundle_identifier=None,
    version=VERSION,
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [{
            'CFBundleTypeIconFile': 'main_icon.icns'}]
    },
)
