"""
Usage:
    pyinstaller --clean --noconfirm PyPOLAR.spec

Recommendations:
    - on MacOS: xcode-select --install
    - If you experience problems packaging your apps, your first step should always be to update your PyInstaller and hooks package the latest versions using:
        pip3 install --upgrade PyInstaller pyinstaller-hooks-contrib
    - MKL library conflict: conda remove mkl; conda install nomkl; conda install numpy
"""

# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import platform
import customtkinter
import darkdetect

__version__ = "2.9.2"

block_cipher = None

arch = platform.machine().lower()

CTK_PATH = os.path.dirname(customtkinter.__file__)
DRK_PATH = os.path.dirname(darkdetect.__file__)

DATA_FILES = [("icons/*.png", "icons/"), 
    ("polarimetry.json", "."), 
    ("pypolar_classes.py", "."), 
    ("generate_json.py", "."), 
    ("calibration/*.txt", "calibration/"), 
    ("diskcones/*.mat", "diskcones/")]

BINARY_FILES = []

if sys.platform == "darwin":
    if 'arm' in arch or 'aarch64' in arch:
        TARGET_ARCH = 'arm64'
    elif 'x86' in arch or 'amd64' in arch:
        TARGET_ARCH = 'x86_64'
    else:
        TARGET_ARCH = None
    DATA_FILES += [("icons/*.icns", "icons/"), 
                (CTK_PATH, "customtkinter"),
                (DRK_PATH, "darkdetect")]
    extra_options = {}
elif sys.platform == 'win32':
    TARGET_ARCH = None
    extra_options = dict(icon='main_icon.ico', version_file='version.rc')
    DATA_FILES += [("icons/*.ico", "icons/"), 
        ("version.rc", "."),
        (CTK_PATH, "customtkinter"),
        (DRK_PATH, "darkdetect")]
else:
    TARGET_ARCH = None
    extra_options = {}

a = Analysis(['PyPOLAR.py'],
    pathex=[],
    binaries=BINARY_FILES,
    datas=DATA_FILES,
    hiddenimports=['setuptools', 'darkdetect', 'ctypes', 'ctypes.util'],
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
    target_arch=TARGET_ARCH,
    codesign_identity=None,
    entitlements_file=None,
    **extra_options)

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
        bundle_identifier="fr.cnrs.fresnel.pypolar",
        version=__version__,
        target_arch=TARGET_ARCH,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'NSHumanReadableCopyright': "BSD 2-Clause License\nCopyright © 2021, Cristel Chandre\nAll Rights Reserved",
            "CFBundlePackageType": "APPL",
            "LSApplicationCategoryType": "public.app-category.utilities",
            "CFBundleDevelopmentRegion": "English",
            "UTExportedTypeDeclarations": [
            {
                "UTTypeIdentifier": "fr.cnrs.fresnel.pypolar-pyroi",
                "UTTypeDescription": "PyPOLAR ROI",
                "UTTypeIconFile": "icons/pyroi.icns",
                "UTTypeConformsTo": ["public.data"],
                "UTTypeReferenceURL": "https://www.fresnel.fr/polarimetry",
                "UTTypeTagSpecification": {
                    "public.filename-extension": "pyroi",
                    "public.mime-type": "data/pypolar-pyroi",},
            },
            {
                "UTTypeIdentifier": "fr.cnrs.fresnel.pypolar-pyreg",
                "UTTypeDescription": "PyPOLAR Registration",
                "UTTypeIconFile": "icons/pyreg.icns",
                "UTTypeConformsTo": ["public.data"],
                "UTTypeReferenceURL": "https://www.fresnel.fr/polarimetry",
                "UTTypeTagSpecification": {
                    "public.filename-extension": "pyreg",
                    "public.mime-type": "data/pypolar-pyreg",
                },
            },
            {
                "UTTypeIdentifier": "fr.cnrs.fresnel.pypolar-pyfig",
                "UTTypeDescription": "PyPOLAR Figure",
                "UTTypeIconFile": "icons/pyfig.icns",
                "UTTypeConformsTo": ["public.data"],
                "UTTypeReferenceURL": "https://www.fresnel.fr/polarimetry",
                "UTTypeTagSpecification": {
                    "public.filename-extension": "pyfig",
                    "public.mime-type": "data/pypolar-pyfig",
                },
            },],
            })
