# Polarimetry [<img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/polar.jpg" alt=" " width="50"/>](https://www.fresnel.fr/polarimetry)

Source files for the Matlab App Designer app Polarimetry (notably the `.mlapp` file). Additional files for post-processing polarimetry data are provided in the folder AdditionalFiles.
For installing the app on your computer, check the [latest releases](https://github.com/cchandre/Polarimetry/releases) on this page, download PolarPlusInstaller_*your_OS* and install the app.

Website: [www.fresnel.fr/polarimetry](https://www.fresnel.fr/polarimetry)

___
##  Manual

### Table of Contents
  * [Left panel](#left-panel)
  * [Fluorescence tab](#fluorescence-tab)
  * [Thresholding/Mask tab](#thresholdingmask-tab)
  * [Options tab](#options-tab)
  * [Advanced tab](#advanced-tab)

___
### Left panel 

  * <ins>Choice of polarimetry method:</ins> <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_biotech_black_48dp.png" alt=" " width="30"/> `1PF` (one-photon fluorescence), `CARS` (coherent anti-Stokes Raman scattering), `SRS` (stimulated Raman scattering), `SHG` (second-harmonic generation), `2PF` (two-photon fluorescence), `4POLAR` (4polar fluorescence)

  * <ins>Download</ins> a file (stack) <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_add_photo_alternate_black_48dp.png" alt=" " width="30"/> or a folder <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_create_new_folder_black_48dp.png" alt=" " width="30"/> containing `.tiff` or `.tif` files (stacks)

  * <ins>Select the method of analysis:</ins> `Thresholding (manual)` (thresholding and regions of interest are manually selected for each stack), `Thresholding (auto)` (thresholding and regions of interest are selected for the first stack and applied to each stack to be analyzed in batch mode), `Mask (manual)` (the binary segmentation mask is applied to the analysis, the name of the segmentation mask is identical to the one of the stack with a `.png` extension), `Mask (auto)` (batch analysis, similar to `Thresholding (auto)` but with a segmentation mask applied for each stack) 

  * <ins>Add ROI: </ins>  <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_center_focus_weak_black_48dp.png" alt=" " width="30"/>   select a region of interest (ROI) on the [Thresholding/Mask](#thresholdingmask-tab) tab to be analyzed; each ROI once confirmed is numbered and displayed on the fluorescence image ([Fluorescence](#fluorescence-tab) tab) and on the thresholded image ([Thresholding/Mask](#thresholdingmask-tab) tab). For each ROI, thresholding needs to be done *before* the drawing of the ROI. 
  
  * <ins>Registration (4POLAR): </ins>   When the selected method of analysis is `4POLAR`, a registration file is needed. Two options: The registration has already been performed, so load the registration file (`*_reg.mat` file containing the geometric transformation). Otherwise, the registration is performed with a beads file (named `fbeads*.tif`) and a whitelight file (named `Whitelight.tif`). The two files need to be in the same folder. The registration proceeds as follows: First, it determines the contours of the four fields of view (the image is binarized using [`imbinarize`](https://mathworks.com/help/images/ref/imbinarize.html) with a threshold given by [`graythresh`](https://mathworks.com/help/images/ref/graythresh.html) and the contours are determined using [`bwboundaries`](https://mathworks.com/help/images/ref/bwboundaries.html)); Second, the beads image is split in four equal-sized images corresponding to these four fields of view; All these images are scaled and a background is removed using [`graythresh`](https://mathworks.com/help/images/ref/graythresh.html); Third, the registration with a fixed image (top left field of view) is done sequentially with the three other fields of view (moving images) using the MATLAB registration function [`imregtform`](https://mathworks.com/help/images/ref/imregtform.html) (with modality 'multimodal' and parameters MaximumIterations=1000, InitialRadius=1e-3, Epsilon=1.5e-6, GrowthFactor=1.0001). This function provides the geometric transformations which will be applied to all the images selected in the analysis. A MATLAB figure displays the resulting three registrations: If this registration is satisfactory, click on 'OK'. If it is satisfactory and you want to save it (to skip this registration in future analysis), click on 'OK and Save'. If it is not satisfactory, click on 'Cancel'.

[&uarr;](#manual)

___
### Fluorescence tab

  The fluorescence tab displays the total intensity (total = sum over the angles) of the stack to be analyzed (if `Stack` slider is set to 'T'), or the image *n* of the stack if the value of the `Stack` slider is set to *n*. The selected dark component has been removed from the total intensity (see [Advanced](#advanced-tab) tab for more information on the computation of the dark value).  

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_brightness_6_black_48dp.png" alt=" " width="30"/> The contrast can be adjusted with the contrast slider on the right hand side of the tab. 

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_square_foot_black_48dp.png" alt=" " width="30"/> displays the angle (in deg) of the segment selected on the fluorescence image (with a counter-clockwise orientation in the field of view as specified in the [Options](#options-tab) tab). 


  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/baseline_restart_alt_black_48dp.png" alt=" " width="30"/> erases the selected ROIs 

  For information, the lower part of the tab indicates the maximum total intensity and the name of the stack to be analyzed. 

[&uarr;](#manual)

___
### Thresholding/Mask tab

  The thresholding/mask tab displays the total intensity (total = sum over the angles) of the stack to be analyzed with a threshold specified in `ILow`. The selected Dark component has been removed from the intensity (see [Advanced](#advanced-tab) tab for more information on the Dark). 

  The value of `ILow` can be modified with the slider `ILow/Maximum` (ratio of the selected `ILow` and the maximum total intensity indicated in the [Fluorescence](#fluorescence-tab) tab). 

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_brightness_6_black_48dp.png" alt=" " width="30"/> For improved visualization, the contrast can be adjusted with the slider on the right hand side of the tab. 

  The component of the image below threshold can be visualized in transparency using the slider `Transparency`. 

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_open_in_new_black_48dp.png" alt=" " width="30"/> exports the binary mask in a `.png` format. Three options to create the masks: using selected ROIs only, using all the image above threshold, or a combination of both (component of the image above threshold and inside selected ROIs). 
  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/outline_palette_black_48dp.png" alt=" " width="30"/>: click on this button to change the colormaps used in the thresholding image ('hot' or 'gray').

 * For improved visualization, a dark <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_image_black_48dp.png" alt=" " width="30"/> or light <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/outline_insert_photo_black_48dp.png" alt=" " width="30"/> mode can be selected for the background.

[&uarr;](#manual)

___
### Options tab

 The `Show/Save` table lists all possible outputs (`Composite`, `Sticks`, `Histogram`, `Fluorescence`): 
  * `Composite` image of the variable *C* displays the values of *C* as color-coded pixels on top of the fluorescence image using the colors in the colormap. 
  * `Sticks` image of the variable *C* displays the values of *C* as color-coded sticks (centered around pixels) on top of the fluorescence image with a color given by the value of *C* and an orientation given by the value of *&rho;*. 
  * `Histogram` displays the histograms of the selected variables *C*. NB: the histogram of the orientation *&rho;* variable is displayed as a polar histogram. 
  * `Fluorescence` image displays the fluorescence image of the [Fluorescence](#fluorescence-tab) tab with the applied contrast and the selected numbered ROIs. 
  
Check the boxes in the Show column for the figure types to be displayed, and in the Save column for the figures to be saved (in MATLAB `.fig` format or as `.tif`).

  The `Variable` table lists all the possible variables *C*. Check the boxes for the variables *C* to be displayed and/or saved in the analysis. For `1PF`: (&rho;, &psi;). For `CARS`, `SRS`, `2PF`: (&rho;, S<sub>2</sub>, S<sub>4</sub>). For `SHG`: (&rho;, S<sub>SHG</sub>). For `4POLAR`: (&rho;, &psi;, &eta;). The second and third column display the minimum and maximum values of the variables (for the colorbars of histograms and composite and stick maps). These elements are editable (except for *&rho;*) if the right-hand-side switch is set to 'On'. 

  The `Save extension` table lists the saving options: `figures (.fig)` for saving the MATLAB `.fig` files, `figures (.tif)` for exporting the figures in a `.tif` format, `data (.mat)` for saving the values of the variables for each pixel used in the analysis, `mean values (.xlsx)` for saving the mean values of the variables in a MS Excel file, and `stack (.mp4)` 

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_delete_forever_black_48dp.png" alt=" " width="30"/> reinitializes the `Show/Save` and `Variable` tables. 
  * Switch `perROI`: `on` if the results are displayed and saved separately for each ROI; `off` if the results are displayed and saved by grouping all ROIs.  

#### Plot options
  * Tick box `Add axes on figure`: Check this box for adding the pixel numbers on the axes of MATLAB `.fig` figures and `.tif` figures. 
  * Spinners for the number of pixels separating sticks on stick maps: `vertical` = number of pixels separating sticks vertically, `horizontal` = number of pixels separating sticks horizontally (i.e., 1 means every pixel, 2 means every other pixel, etc...)


Tick box `Show individual fit`: Check this box to visualize the accuracy of the fitting per pixel. The selection of the pixel is done on the Composite figure of &rho; (checked automatically if the `Show individual fit` box is ticked)
 

*Convention for the origin of the angles*: The orientation angles &rho; (for sticks and histograms) are computed with the following convention, related to the field of view. Please also note the numbering of the pixels in the horizontal and vertical axes. 

<img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/convention.png" alt=" " width="300"/>

[&uarr;](#manual)

___
### Advanced tab

#### Dark

Two options: `Calculated dark value` (default) and `User dark value` to be manually entered by the user. This is used to remove the small residual fluorescence of the stack. The default value for `User dark value` is set to the minimum value of the stacks if the polarimetry data is 32 bits (e.g., for `CARS`, `SRS`, `SHG` and `2PF`), and to 480 otherwise (e.g., for `1PF` and `4POLAR`).

*Method to compute the* `Calculated dark value`: The stack is paved with non-overlapping cells of 20x20 pixels. The mean value of the first element of the stack (first angle) is computed for each cell. The average over all angles of the cell with the smallest mean value is the `Calculated dark value`. 

#### Offset angle

The value of the offset angle used in the analysis is indicated. This angle is in degrees measured according to the convention mentioned in the [Options](#options-tab) tab. In order to manually change this value, the switch should be set to 'On'. 

#### Disk Cone (for 1PF)

The drop down menu lists all the disk cones included in the app. If the disk cone to be used is not in the list, select `other`and download the appropriate disk cone. The choice of disk cone also sets the value for the offset angle. 
Click on the button <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_image_black_48dp.png" alt=" " width="30"/> `Display` to visualize the disk cone used in the `1PF` analysis. The name of the disk cone used in the analysis is displayed on the lower part of the panel. 

#### Calibration Data (for 4POLAR)

The first drop down menu lists all the calibration data included in the app. If the calibration data to be used is not in the list, select `other`and download the appropriate calibration data. The calibration data is a `.mat` file with a name of the type `Calib*.mat` containing a 4x4 matrix *K*. The name of the calibration data used in the analysis is displayed on the lower part of the panel. 
Select the distribution of the polarization angles (0&deg;, 45&deg;, 90&deg;, 135&deg;) using the second drop down menu: UL (upper left), UR (upper right), LR (lower right) and LL (lower left).

#### Binning

This option is used to improve the quality of the stack if the signal is too weak. It performs a convolution of the stack with a kernel of 1's of size `Bin width` x `Bin height`. A side effect is a blurring of the stack. 

#### Rotation

* `Stick (deg)`: (editable) value of the angle (in degrees) to arbitrarily rotate the sticks (following the above-mentioned convention: positive=counter-clockwise, negative=clockwise)
* `Figure (deg)`: (editable) value of the angle (in degrees) to arbitrarily rotate the entire figure (following the above-mentioned convention: positive=counter-clockwise, negative=clockwise)
 
#### Remove Background 

This option is used to remove background from the stack (noise substraction). First, choose the value `Noise factor` (between 0 and 1) for the fraction of the mean intensity of the patch to be removed from the stack. Second, define the size in pixels (`Noise width` and `Noise height`) of the patch in the noisy part of the fluorescence image. Third, select a point (center of the patch of size `Noise width` x `Noise height`) in the fluorescence image by clicking on the button <img src="https://github.com/cchandre/Polarimetry/blob/master/Icons/round_exposure_black_48dp.png" alt=" " width="30"/> `Click background`. The mean value over the selected patch weighted by the Noise factor is removed from the entire stack. The noise removal level which is substracted from the stack is indicated in the lower panel of the panel.

[&uarr;](#manual)

___
For more information: <cristel.chandre@cnrs.fr>
