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

The thresholding/mask tab displays the total intensity (total = sum over the angle) of the stack to be analyzed with a threshold specified in `ILow`. The selected Dark component has been removed from the intensity (see Advanced tab for more information on the Dark). 

The value of `ILow` can be modified with the slider `ILow/Imax` (ratio of the selected `ILow` and the maximum total intensity indicated int he fluorescence tab). 

For improved visualization, the contrast can be adjusted with the slider on the right hand side of the tab. 

The component of the image below threshold can be visualized in transparency using the slider `Transparency`. 

For improved visualization, a dark <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_image_black_48dp.png" alt=" " width="30"/> or light <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/outline_insert_photo_black_48dp.png" alt=" " width="30"/> mode can be selected for the background. 

* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_open_in_new_black_48dp.png" alt=" " width="30"/> exports the binary mask in a `.png` format. Three options to create the masks: using selected ROIs only, using all the image above threshold, or a combination of both (component of the image above threshold and inside selected ROIs). 

### Options Tab

The Display table lists all possible outputs (`Composite`, `Sticks`, `Histogram`, `Fluorescence`): `Composite` image of the variable *C* displays the values of *C* as an image that uses the colors in the colormap. `Sticks` displays the values of *C* as sticks with a color given by the value of *C* and an orientation given by the value of *&rho;*. `Histogram` represents the histograms of the selected variables. NB: the histogram of the orientation *&rho;* variable is a polar histogram. Check the boxes in the Show column for the figure types to be displayed, and in the Save column for the figures to be saved (in MATLAB `.fig` format).

The Variable table lists all the possible variables. Check the boxes for the variables to be displayed and/or saved in the analysis. For 1PF: (&rho;, &psi;). For CARS, SRS, 2PF: (&rho;, S<sub>2</sub>, S<sub>4</sub>). For SHG: (&rho;, S<sub>SHG</sub>) 

The Save extension table lists the saving options: `figures (.fig)` for saving the MATLAB `.fig` files; `data (.mat)` for saving the values of the variables for each pixel used in the analysis; `mean values (.xlsx)` for saving the mean values of the variables in a MS Excel file. 

* <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_delete_forever_black_48dp.png" alt=" " width="30"/> reinitializes the Display and Variable tables. 
* Switch `perROI`: `on` if the results are displayed and saved separately for each ROI; `off` if the results are displayed and saved by grouping all ROIs.  
* Tick box `Add axes on figure`: Check this box for adding the pixel numbers on the axes
* Tick box `Show individual fit`: Check this box to visualize the accuracy of the fitting per pixel. The selection of the pixel is done on the Composite figure of &rho; 
* Spinner `pixels per stick`: number of pixels separating sticks on the stick maps (same value vertically and horizontally)

* Drowdown menu `Colormap (Thresholding)` for the colormap used in the Thresholding/Mask tab 
 
### Advanced Tab

#### Remove Background 

This option is used to remove a noisy background from the stack (noise substraction). First, choose as well the value `Noise factor` (between 0 and 1) for the amount of intensity to be removed from the stack. Second, define the size in pixels (`Noise width` and `Noise height`) of the region in the noisy part of the fluorescence image. Third, select a point (center of the noisy patch of size Noise width x Noise height) in the fluorescence image by clicking on the button <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_exposure_black_48dp.png" alt=" " width="30"/> `Click background`. The mean value over the patch weighted by the Noise factor is removed from the entire stack. 

#### Binning

This option is used to improve the quality of the stack if the signal is too weak. It performs a box linear filter (box blur) with a kernel of 1s of size `Bin width` x `Bin height`. 

#### Dark

Two options: `Calulated dark value` (default) and `User dark value` to be manually entered by the user. This is used to remove the small residual fluorescence of the stack. 

<ins>Method:</ins> The stack is paved with cells of 20x20 pixels. The meanvalue of the first element of the stack (first angle) is computed for each cell. The average over all angles of the cell with the smallest meanvalue is the `calculated dark value`. 

#### Rotation

* `Stick (deg)`: value of the angle to arbitrarily rotate the sticks
* `Figure (deg)`: value of the angle to arbitrarily rotate the entire figure
 

#### Disk Cone (for 1PF)

The drop down menu lists all the disk cones included in the app. If the disk cone to be used is not in the list, select `other`and download the appropriate disk cone. 
Click on the button <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_image_black_48dp.png" alt=" " width="30"/> `Display` to visualize the Disk Cone used in the `1PF` analysis. 
For information, the value of the `Offset angle (deg)` used in the `1PF` analysis is indicated.  

___
For more information: <cristel.chandre@cnrs.fr>
