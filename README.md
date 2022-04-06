# Polarimetry [<img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/polar.jpg" alt=" " width="50"/>](https://www.fresnel.fr/polarimetry)

Source files for the Matlab App Designer app Polarimetry (notably the `.mlapp` file). Additional files for post-processing polarimetry data are provided in the folder AdditionalFiles.

Website: [www.fresnel.fr/polarimetry](https://www.fresnel.fr/polarimetry)

___
<link href="https://fonts.googleapis.com/css2?family=Material+Icons"
      rel="stylesheet">

##  Manual

### Left Panel 

* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_biotech_black_48dp.png" alt=" " width="30"/> <ins>Choice of experimental method:</ins> `1PF` (one-photon fluorescence), `CARS` (coherent anti-Stokes Raman spectroscopy), `SRS` (simulated Raman spectroscopy), `SHG` (second-harmonic generation), `2PF` (two-photon fluorescence)

* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_add_photo_alternate_black_48dp.png" alt=" " width="30"/> <ins>Download</ins> a file (stack) or a folder containing `.tiff` or `.tif` files (stacks)

* <ins>Select the method of analysis:</ins> `Thresholding (manual)` (thresholding is manually selected for each stack), `Thresholding (auto)` (thresholding is selected intially and applied to each stack to be analyzed in batch mode), `Mask (manual)` (mask is applied to the analysis, the name of the mask is identical to the one of the stack with a `.png` extension), `Mask (auto)`  

* <ins>Add ROI:</ins> select a region of interest (ROI) on the Thresholding/Mask tab to be analyzed; each ROI once confirmed is numbered and displayed on the fluorescence image 


### Fluorescence Tab

The fluorescence tab displays the total intensity of the first stack to be analyzed. The selected Dark component has been removed from the intensity (see Advanced tab for more information on the Dark).   


### Thresholding/Mask Tab


### Options Tab
 
 
### Advanced Tab


___
For more information: <cristel.chandre@cnrs.fr>
