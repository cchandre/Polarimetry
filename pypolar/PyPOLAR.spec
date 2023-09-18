"""
Environment: polarimetry_env

Usage:
    pyinstaller pypolar.spec

Recommendations:
    - on MacOS: xcode-select --install
    - change CTK_PATH using pip3 show customtkinter
    - If you experience problems packaging your apps, your first step should always be to update your PyInstaller and hooks package the latest versions using:
        pip3 install --upgrade PyInstaller pyinstaller-hooks-contrib

Possible issues:
    - MKL library conflict: conda remove mkl; conda install nomkl; conda install numpy
"""


# -*- mode: python ; coding: utf-8 -*-

import sys

__version__ = "2.5.2"

block_cipher = None

DATA_FILES = [("icons/*.png", "icons/"), ("polarimetry.json", "."), ("pypolar_classes.py", "."), ("generate_json.py", ".")]
BINARY_FILES = [("calibration/*.mat", "calibration/"), ("diskcones/*.mat", "diskcones/")]

if sys.platform == "darwin":
    CTK_PATH = "/Users/cchandre/opt/anaconda3/envs/polarimetry_env/lib/python3.8/site-packages/customtkinter/"
    DATA_FILES += [("icons/*.icns", "icons/")]
if sys.platform == 'win32':
    CTK_PATH = "c:/users/libreservice fresnel/anaconda3/envs/polarimetry_env/lib/site-packages/customtkinter/"
    extra_options = dict(icon='main_icon.ico', version_file='version.rc')
    DATA_FILES += [("icons/*.ico", "icons/"), ("version.rc", ".")]
else:
    extra_options = {}

DATA_FILES += [(CTK_PATH, "customtkinter/")]

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
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleGetInfoString': "Python-based app for analyzing polarization-resolved microscopy data to measure molecular orientation and order in biological samples",
            'NSHumanReadableCopyright': "BSD 2-Clause License\nCopyright © 2021, Cristel Chandre\nAll Rights Reserved",
            "CFBundlePackageType": "APPL",
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
                "UTTypeIdentifier": "fr.cnrs.fresnel.pypolar-pykl",
                "UTTypeDescription": "PyPOLAR Pickle",
                "UTTypeIconFile": "icons/pykl.icns",
                "UTTypeConformsTo": ["public.data"],
                "UTTypeReferenceURL": "https://www.fresnel.fr/polarimetry",
                "UTTypeTagSpecification": {
                    "public.filename-extension": "pykl",
                    "public.mime-type": "data/pypolar-pykl",
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
