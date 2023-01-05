"""
 py2app/py2exe build script for PolarimetryPlus.

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
 """

import sys
from setuptools import setup

APP = ['PolarimetryPlus.py']
VERSION = "2.2"
APP_NAME = "PolarimetryPlus"
AUTHOR = "Cristel Chandre"
AUTHOR_EMAIL = "cristel.chandre@cnrs.fr"
URL = "https://www.fresnel.fr/polarimetry"
DATA_FILES = ["polarimetry.json", "apptools.py", "Icons_Python", "Icons_Python", "CalibrationData/*"]
OPTIONS = {}

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        options=dict(py2app=dict(argv_emulation=True)),
        #iconfile = 'app.icns',
        plist = {
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleGetInfoString': "Polarimetry Analysis",
            'CFBundleIdentifier': "https://www.fresnel.fr/polarimetry",
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHumanReadableCopyright': u"Copyright © 2021, Cristel Chandre, All Rights Reserved"
        }
    )
elif sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe'],
    )

setup(
    name = APP_NAME,
    version = VERSION,
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    url = URL,
    long_description_content_type = "text/markdown",
    long_description = "**Detailed Information:" +  URL + "**",
    app = APP,
    data_files = DATA_FILES,
    install_requires = ["customtkinter"],
    **extra_options
)
