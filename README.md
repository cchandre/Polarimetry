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

*  <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_center_focus_weak_black_48dp.png" alt=" " width="30"/> <ins>Add ROI:</ins> select a region of interest (ROI) on the Thresholding/Mask tab to be analyzed; each ROI once confirmed is numbered and displayed on the fluorescence image 


### Fluorescence Tab

The fluorescence tab displays the total intensity (total = sum over the angle) of the first stack to be analyzed. The selected Dark component has been removed from the intensity (see Advanced tab for more information on the Dark).  

The contrast can be adjusted with the slider on the right hand side of the tab. 

* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_square_foot_black_48dp.png" alt=" " width="30"/> displays the angle (in deg) of the segment selected on the fluorescence image


* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/baseline_restart_alt_black_48dp.png" alt=" " width="30"/> erases the selected ROIs 

For information, the lower part of the tab indicates the maximum total intensity and the name of the stack to be analyzed. 


### Thresholding/Mask Tab

The thresholding/mask tab displays the total intensity (total = sum over the angle) of the first stack to be analyzed with a threshold specified in `ILow`. The selected Dark component has been removed from the intensity (see Advanced tab for more information on the Dark). 

The value of `ILow` can be modified with the slider `ILow/Imax` (ratio of the selected `ILow` and the maximum total intensity indicated int he fluorescence tab). 

For improved visualization, the contrast can be adjusted with the slider on the right hand side of the tab. 

The component of the image below threshold can be visualized in transparency using the slider `Transparency`. 

For improved visualization, a dark <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_image_black_48dp.png" alt=" " width="30"/> or white <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/outline_insert_photo_black_48dp.png" alt=" " width="30"/> mode can be selected. 

* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_open_in_new_black_48dp.png" alt=" " width="30"/> exports the binary mask in a `.png` format. Three options to create the masks: using selected ROIs only, using all the image above threshold, or a combination of both (component of the image above threshold and inside selected ROIs). 

### Options Tab
 
 
### Advanced Tab


___
For more information: <cristel.chandre@cnrs.fr>
