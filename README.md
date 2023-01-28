# [<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/main_icon.png" alt=" " width="50"/>](https://www.fresnel.fr/polarimetry) PyPOLAR 

PyPOLAR is a Python-based app for analyzing polarization-resolved microscopy data to measure molecular orientation and order in biological samples. 
For installing PyPOLAR on your computer, check the [latest releases](https://github.com/cchandre/Polarimetry/releases), download `PyPOLAR_installer.exe` for Windows or `PyPOLAR.dmg` for MacOS.

Source code: [PyPOLAR.py](https://github.com/cchandre/Polarimetry/blob/master/pypolar/PyPOLAR.py)

Website: [www.fresnel.fr/polarimetry](https://www.fresnel.fr/polarimetry)

___
##  Manual

### Table of Contents
  * [Left panel](#left-panel)
  * [Intensity tab](#intensity-tab)
  * [Thresholding/Mask tab](#thresholdingmask-tab)
  * [Options tab](#options-tab)
  * [Advanced tab](#advanced-tab)

___
### Left panel

  * <ins>Choice of polarimetry method:</ins> <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/microscope.png" alt=" " width="30"/> `1PF` (one-photon fluorescence), `CARS` (coherent anti-Stokes Raman scattering), `SRS` (stimulated Raman scattering), `SHG` (second-harmonic generation), `2PF` (two-photon fluorescence), `4POLAR 2D` (2D 4polar fluorescence), `4POLAR 3D` (3D 4polar fluorescence).

  * <ins> Download data to be analyzed: </ins> <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/download_file.png" alt=" " width="30"/>: `Open file` (`.tiff` or `.tif` stack file) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/photo_fill.png" alt=" " width="30"/>, `Open folder` (containing `.tiff` or `.tif` stack files) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/folder_open.png" alt=" " width="30"/> or `Previous analysis` (a compressed `.pbz2` pickle file saved from a previous PyPOLAR analysis) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/analytics.png" alt=" " width="30"/>. The analysis is done with 16-bit images. In case of 32-bit images, they are converted to 16-bit images before analysis.   

  * <ins>Select the method of analysis:</ins>  <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/build.png" alt=" " width="30"/> `Thresholding (manual)` (thresholding and regions of interest are manually selected for each stack), `Thresholding (auto)` (thresholding and regions of interest are selected for the first stack and applied to each stack to be analyzed in batch mode), `Mask (manual)` (a binary segmentation mask is applied to the analysis; the name of the segmentation mask has to be identical to the one of the stack with a `.png` extension), `Mask (auto)` (batch analysis, similar to `Thresholding (auto)` but with a segmentation mask applied to each stack).

  * <ins>Add ROI: </ins>  <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/roi.png" alt=" " width="30"/>   select a region of interest (ROI) on the [Thresholding/Mask](#thresholdingmask-tab) tab; each ROI, once confirmed, is numbered and displayed on the intensity image ([Intensity](#intensity-tab) tab), on the thresholded image ([Thresholding/Mask](#thresholdingmask-tab) tab) and in the ROI Manager. For each ROI, thresholding needs to be done *before* the drawing of the ROI. For polygonal ROIs, click successively the left mouse button, for freehand ROIs, click continuously the right mouse button. Double click to close the ROI. 

  * <ins>Registration (4POLAR): </ins>   When the selected method of analysis is `4POLAR 2D` or `4POLAR 3D`, an image registration is needed. Two options: The registration has already been performed, so load the registration file (`*.pyreg` file containing the geometric transformation). Otherwise, the registration is performed with a beads image file (named `fbeads*.tif`) and a whitelight image file (named `Whitelight.tif`). The two files need to be in the same folder. The registration proceeds as follows: First, it determines the contours of the four fields of view using the whitelight image  -- the image is thresholded using `cv2.threshold` with `cv2.THRESH_BINARY + cv2.THRESH_OTSU` and the contours are determined using `cv2.findContours` (see [OpenCV](https://docs.opencv.org/) documentation for more details) -- Second, the beads image is split in four equal-sized images corresponding to the four polarized images of the beads; The intensities in the four images are normalized and thresholded using `cv2.threshold`; Third, the registration is performed using the polarized image on the top left as the fixed image and the three other polarized images as moving images. We use the scale-invariant feature transform (SIFT) algorithm `cv2.SIFT_create` to detect local features in the images. Using a matching algorithm between the location of the beads in the fixed and moving images (by solving the linear sum assignment problem with [`scipy.optimize.linear_sum_assignment`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html#scipy-optimize-linear-sum-assignment)), we determine the perspective transformations using `cv2.findHomography`. These geometric transformations will be applied to all the images selected in the analysis. A figure displays the resulting three registrations: If this registration is satisfactory, click 'OK'. If it is satisfactory and you want to save it (to skip performing this registration in future analysis), click 'OK and Save'. If it is not satisfactory, click 'Cancel'.

[&uarr;](#manual)

___
### Intensity tab

  The intensity tab displays the total intensity (total = sum over the angles) image of the stack to be analyzed if the `Stack` slider is set to 'T', or the image *n* of the stack if the value of the `Stack` slider is set to *n*. The selected dark value has been removed from the total intensity (see [Advanced](#advanced-tab) tab for more information on the computation of the dark value).  

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/contrast.png" alt=" " width="30"/> The contrast can be adjusted with the contrast slider on the right hand side of the tab. This value of the contrast will be used in the intensity images in the figures.

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/square.png" alt=" " width="30"/> displays the angle (in deg) and the length (in number of pixels) of the segment selected on the intensity image. The angle is defined with a counter-clockwise orientation in the field of view as specified in the [Options](#options-tab) tab). Click the left mouse button to select this segment.


  The lower part of the tab indicates the name of the stack to be analyzed.

[&uarr;](#manual)

___
### Thresholding/Mask tab

  The thresholding/mask tab displays the total intensity (total = sum over the angles) image of the stack to be analyzed with a threshold specified in `ILow`. The selected dark value has been removed from the intensity (see [Advanced](#advanced-tab) tab for more information on the dark).

  The value of `ILow` can be modified with the `ILow` slider. The entry box displays the selected `ILow` which can also be entered manually. The value of `ILow` used for the analysis is saved in the MS Excel file (see `Save output` in [Options](#options-tab) tab).

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/contrast.png" alt=" " width="30"/> For improved visualization, the contrast can be adjusted with the slider on the right hand side of the tab. The selected contrast does not affect the analysis. 

  The component of the image below the intensity threshold can be visualized in transparency using the `Transparency` slider. The selected transparency does not affect the analysis.

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/palette.png" alt=" " width="30"/>: click this button to change the colormaps used in the thresholded image ('hot' or 'gray').

 * For improved visualization, a dark <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/photo_fill.png" alt=" " width="30"/> or light <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/photo.png" alt=" " width="30"/> mode can be selected for the background.

* <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/open_in_new.png" alt=" " width="30"/> exports the binary mask in a `.png` format. Three options to create the masks: using selected ROIs only, using the image above threshold, or a combination of both (component of the image above threshold and inside selected ROIs). The file name of the exported mask includes the suffix `_mask` to avoid overwriting an existing mask for the same file. To use it for further analysis, remove this suffix.

* <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/format_list.png" alt=" " width="30"/> opens the ROI Manager. 

     - `ROI`: displays the index of the ROI, as displayed in the intensity and thresholding/mask images.
     - `name`: to be entered by the user as a tag of the specific ROI; it will be saved in the MS Excel.
     - `group `: to be entered by the user as a tag of the specicif group the ROI belongs to; it will be saved in the MS Excel.
     - `select`: select the ROIs to be considered in the analysis.
     - `delete`: select the ROIs to be permanently deleted (then click the button `Delete` to actually delete them and update the table and images).
     - Button `Commit`: click this button to commit the changes made to the labels of the ROIs (names, groups and selection).
     - Button `Save`: save the information on all the ROIs as a binary `.pyroi` file.
     - Button `Load`: load the ROIs from a binary `.pyroi` file.
     - Button `Delete`: permanently deletes all the ROIs selected in `delete`; ROIs are renumbered in the ROI Manager and in the intensity and thresholding/mask images.
     - Button `Delete All`: permamently deletes all the ROIs in the list.

[&uarr;](#manual)

___
### Options tab

#### Figures

 The `Show/Save` table lists all display outputs (`Composite`, `Sticks`, `Histogram`, `Intensity`):
  * `Composite` image of the variable *C* displays the values of *C* as color-coded pixels on top of the intensity image using the colors in the colormap.
  * `Sticks` image of the variable *C* displays the values of *C* as color-coded sticks (centered around pixels) on top of the intensity image with a color given by the value of *C* and an orientation given by the value of *&rho;*.
  * `Histogram` displays the histograms of the selected variables *C*. NB: the histograms for the variables *&rho;* (for all methods) and *&eta;* (for `4POLAR 3D`) are displayed as polar histograms.
  * `Intensity` image displays the intensity image of the [Intensity](#intensity-tab) tab with the applied contrast and the selected numbered ROIs.

Check the boxes in the Show column for the figure types to be displayed, and in the Save column for the figures to be saved (as `.tif` files).

#### Variables

  The `Variables` table lists all the possible variables *C*. Check the boxes for the variables *C* to be displayed and/or saved in the analysis. For `1PF`, `4POLAR 2D`: (&rho;, &psi;). For `CARS`, `SRS`, `2PF`: (&rho;, S<sub>2</sub>, S<sub>4</sub>). For `SHG`: (&rho;, S<sub>SHG</sub>). For `4POLAR 3D`: (&rho;, &psi;, &eta;). The second and third columns display the minimum and maximum values of the variables used for the colorbars of histograms and composite and stick maps. These elements are editable (except for *&rho;*) if the toggle switch is selected.
  

#### Save output

  The `Save output` table lists the saving options: `data (.pbz2)` for saving data as a compressed pickle file (to download as `Previous analysis` in the download selection), `figures (.tif)` for exporting the figures as TIFF files, `data (.mat)` for saving the values of the variables for each pixel used in the analysis as a MATLAB `.mat` file, `mean values (.xlsx)` for saving the mean values of the variables in a MS Excel file, and `movie (.gif)` for an animated gif file of the stack.


#### Post-processing
  * Checkbox `Add axes on figure`: if selected, the pixel numbers on the axes of each open figure is displayed (also visible on the `.tif` images if selected).

* Button `Crop figures`<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/crop.png" alt=" " width="30"/>: enter the x-range and y-range for cropping the figures; the values are also the ones used in the save animated gif. 

* Button `Show individual fit`<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/query_stats.png" alt=" " width="30"/>: Click this button to visualize the accuracy of the fitting per pixel. The selection of the pixel is done on the Composite figure of &rho;. 


#### Pixels separating sticks

  * Spinners for the number of pixels separating sticks on stick maps: `vertical` = number of pixels separating sticks vertically, `horizontal` = number of pixels separating sticks horizontally (i.e., 1 means every pixel, 2 means every other pixel, etc...); the spinners apply directly to open stick figures.


 * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/delete_forever.png" alt=" " width="30"/> reinitializes the `Show/Save` and `Variable` tables.
  * Checkbox `perROI`: if selected, the results are displayed and saved separately for each ROI; otherwise, the results are displayed and saved by grouping all ROIs.  


*Convention for the origin of the angles*: The orientation angles &rho; (for sticks and histograms) are computed with the following convention, related to the field of view. Please also note the numbering of the pixels in the horizontal and vertical axes.

<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/convention.png" alt=" " width="300"/>

[&uarr;](#manual)

___
### Advanced tab

#### Dark

The `Used dark value` indicated in the entry box is the value used in the analysis to remove the small residual intensity of the stack. The default is the `calculated dark value` indicated above the entry box. To change it, select the toggle and enter the chosen value in the entry box. For `1PF`, the minimum possible value is 480.

*Method to compute the* `Calculated dark value`: The stack is paved with non-overlapping cells of 20x20 pixels. The mean value of the first element of the stack (first angle) is computed for each cell. The average over all angles of the cell with the smallest mean value is the `Calculated dark value`.

#### Polarization

* The value of the offset angle used in the analysis is indicated. This angle is in degrees measured according to the convention mentioned in the [Options](#options-tab) tab. In order to manually change this value, the switch should be set to 'On'.

* Select the polarization direction as clockwise or counter-clockwise.

#### Disk cone / Calibration data (for 1PF and 4POLAR)

For 1PF: The drop down menu lists all the disk cones included in the app. If the disk cone to be used is not in the list, select `other`and download the appropriate disk cone. The choice of disk cone also sets the value for the offset angle.
Click the button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/photo.png" alt=" " width="30"/> `Display` to visualize the disk cone used in the `1PF` analysis. The name of the disk cone used in the analysis is displayed on the lower part of the panel.

For 4POLAR: The first drop down menu lists all the calibration data included in the app. If the calibration data to be used is not in the list, select `other`and download the appropriate calibration data. The calibration data is a `.mat` file with a name of the type `Calib*.mat` containing a 4x4 matrix *K*. The name of the calibration data used in the analysis is displayed on the lower part of the panel.
Select the distribution of the polarization angles (0&deg;, 45&deg;, 90&deg;, 135&deg;) using the second drop down menu: UL (upper left), UR (upper right), LR (lower right) and LL (lower left).

#### Binning

This option is used to improve the quality of the stack if the signal is too weak. It performs a convolution of the stack with a kernel of 1's of size `Bin width` x `Bin height`. A side effect is a blurring of the stack.

#### Rotation

* `Stick (deg)`: (editable) value of the angle (in degrees) to arbitrarily rotate the sticks (following the above-mentioned convention: positive=counter-clockwise, negative=clockwise)
* `Figure (deg)`: (editable) value of the angle (in degrees) to arbitrarily rotate the entire figure (following the above-mentioned convention: positive=counter-clockwise, negative=clockwise)

#### Remove background

This option is used to remove background from the stack (noise substraction). First, choose the value `Noise factor` (between 0 and 1) for the fraction of the mean intensity of the patch to be removed from the stack. Second, define the size in pixels (`Noise width` and `Noise height`) of the patch in the noisy part of the intensity image. Third, select a point (center of the patch of size `Noise width` x `Noise height`) in the intensity image by clicking the button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/exposure.png" alt=" " width="30"/> `Click background`. The mean value over the selected patch weighted by the Noise factor is removed from the entire stack. The noise removal level which is substracted from the stack is indicated in the lower panel of the panel.

[&uarr;](#manual)

___
For more information: <cristel.chandre@cnrs.fr>
