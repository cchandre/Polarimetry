"""
 py2app/py2exe build script for PolarimetryPlus.

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
 """

import sys
from setuptools import setup

APP = ['PyPOLAR.py']
VERSION = "2.2"
APP_NAME = "PyPOLAR"
AUTHOR = "Cristel Chandre"
AUTHOR_EMAIL = "cristel.chandre@cnrs.fr"
URL = "https://www.fresnel.fr/polarimetry"
DATA_FILES = [("icons", ["*.png"]), "polarimetry.json"]
OPTIONS = {}

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        options=dict(py2app=dict(argv_emulation=True)),
        #iconfile = 'app.icns',
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
    install_requires = ["customtkinter", "openpyxl", "opencv"],
    packages = ["pypolar"],
    package_dir = {"pypolar": "pypolar"},
    package_data = {"pypolar": ["calibration/*.mat", "diskcones/*.mat"]},
    **extra_options
)
