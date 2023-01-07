"""
Environment: polarimetry_env

Usage:
    python3 setup.py py2app
"""

from setuptools import setup
import glob

VERSION = "2.2"

APP = ['PyPOLAR.py']
NAME = 'PyPOLAR'
DATA_FILES = [("icons", glob.glob('icons/*.png')), ("calibration", glob.glob('calibration/*.mat')), ("diskcones", glob.glob('diskcones/*.mat')), (".", glob.glob("polarimetry.json")), ("customtkinter", glob.glob("/Users/c.chandre/opt/anaconda3/lib/python3.9/site-packages/customtkinter/*.*"))]
OPTIONS = {"iconfile": 'main_icon.icns'}

setup(
    app=APP,
    name=NAME,
    version=VERSION,
    author='Cristel Chandre',
    author_email='cristel.chandre@gmail.com',
    url='https://www.fresnel.fr/polarimetry',
    download_url='https://github.com/cchandre/Polarimetry/tree/master/pypolar',
    project_urls={
        'Documentation': "https://github.com/cchandre/Polarimetry/blob/master/README.md",
        'Source': 'https://github.com/cchandre/Polarimetry/tree/master/pypolar',
        'Tracker': 'https://github.com/cchandre/Polarimetry/issues',
    },
    license='BSD 2-Clause "Simplified" License',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    install_requires=['pillow'],
    setup_requires=['py2app'],
)
