import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='PyPOLAR',
    version='2.6.4',
    description='PyPOLAR is a Python-based app for analyzing polarization-resolved microscopy data to measure molecular orientation and order in biological samples',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    url='https://www.fresnel.fr/polarimetry',
    classifiers=[
      'Programming Language :: Python :: 3',
      'Intended Audience :: Education',
      'Intended Audience :: Science/Research',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent',
      'Topic :: Scientific/Engineering',
	  'Topic :: Scientific/Engineering :: Bio-Informatics',
	  'Topic :: Scientific/Engineering :: Visualization',
	  'Topic :: Scientific/Engineering :: Image Processing'
    ],
    python_requires='>=3.8',
    author='Cristel Chandre',
    author_email='cristel.chandre@cnrs.fr',
    license='BSD',
    py_modules=['PyPOLAR', 'pypolar_classes', 'generate_json'],
    package_dir={'': 'pypolar'}, 
    install_requires=[
		"colorcet==3.0.1",
		"customtkinter==5.2.0",
		"joblib==1.2.0",
		"matplotlib==3.6.2",
		"numpy==1.23.5",
		"opencv-python==4.8.1.78",
		"openpyxl==3.0.9",
		"pillow==10.3.0",
		"scikit-image==0.20.0",
		"scipy==1.9.1",
		"tksheet==6.2.5",
		"tk==8.6.13"]
)