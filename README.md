# [<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/main_icon.png" alt=" " width="50"/>](https://www.fresnel.fr/polarimetry) PyPOLAR 

PyPOLAR is a Python-based app for analyzing polarization-resolved microscopy data to measure molecular orientation and order in biological samples. 
To install PyPOLAR on your computer, check out the [latest release](https://github.com/cchandre/Polarimetry/releases), and download `PyPOLAR_installer.exe` for Windows or `PyPOLAR.dmg` for macOS.

Source code: [PyPOLAR.py](https://github.com/cchandre/Polarimetry/blob/master/pypolar/PyPOLAR.py)

Website: [www.fresnel.fr/polarimetry](https://www.fresnel.fr/polarimetry)

![Version](https://img.shields.io/badge/version-v2.6.2-blue)
![Platform](https://img.shields.io/badge/platform-macOS|Windows-orange)
![License](https://img.shields.io/badge/license-BSD-lightgray)

<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/PyPOLAR_layout.png" alt=" " width="400"/>  

The code was compiled with Python 3.8.16 with the packages listed in [requirements.txt](https://github.com/cchandre/Polarimetry/blob/master/pypolar/requirements.txt), and the app was created using [PyInstaller](https://pyinstaller.org/) 5.12.0.
___
##  Manual

### Table of Contents
  * [Left panel](#left-panel)
  * [Intensity tab](#intensity-tab)
  * [Thresholding/Mask tab](#thresholdingmask-tab)
  * [Options tab](#options-tab)
  * [Advanced tab](#advanced-tab)
  * [Edge Detection tab](#edge-detection-tab)

___
### Left panel

  * <ins>Choice of polarimetry method:</ins> <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/microscope.png" alt=" " width="30"/> `1PF` (one-photon fluorescence), `CARS` (coherent anti-Stokes Raman scattering), `SRS` (stimulated Raman scattering), `SHG` (second-harmonic generation), `2PF` (two-photon fluorescence), `4POLAR 2D` (2D 4POLAR fluorescence), `4POLAR 3D` (3D 4POLAR fluorescence).

  * <ins> Download data to be analyzed: </ins> <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/download_file.png" alt=" " width="30"/>: `Open file` (`.tiff` or `.tif` stack file) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/photo_fill.png" alt=" " width="30"/>, `Open folder` (containing `.tiff` or `.tif` stack files) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/folder_open.png" alt=" " width="30"/> , `Open analysis` (a compressed `.pykl` pickled file saved from a previous PyPOLAR analysis) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/analytics.png" alt=" " width="30"/> or `Open figure` (a `.pyfig` pickled file saved from a previous PyPOLAR analysis) <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/imagesmode.png" alt=" " width="30"/>. The analysis is performed with 8 or 16-bit images. In case of 32-bit images, they are converted to 16-bit images before analysis.   

  * <ins>Select the method of analysis:</ins>  <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/build.png" alt=" " width="30"/> `Thresholding (manual)` (thresholding and regions of interest are manually selected for each stack), `Thresholding (auto)` (thresholding and regions of interest are selected for the first stack and applied to each stack to be analyzed in batch mode), `Mask (manual)` (a binary segmentation mask is applied to the analysis; the name of the segmentation mask has to be identical to the one of the stack with a `.png` extension), `Mask (auto)` (batch analysis, similar to `Thresholding (auto)` but with a segmentation mask applied to each stack). For `Thresholding (auto)` and `Mask (auto)`, the menu icon is changed to <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/build_fill.png" alt=" " width="30"/>

  * <ins>Add ROI: </ins>  <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/roi.png" alt=" " width="30"/>   select a region of interest (ROI) on the [Thresholding/Mask](#thresholdingmask-tab) tab; each ROI, once confirmed, is numbered and displayed on the intensity image ([Intensity](#intensity-tab) tab), on the thresholded image ([Thresholding/Mask](#thresholdingmask-tab) tab) and in the ROI Manager. For each ROI, thresholding needs to be done *before* the drawing of the ROI. For polygonal ROIs, click successively the left mouse button; for freeform ROIs, click continuously the right mouse button. Double click to close the ROI.  
   NB: When Add ROI is active, it is not possible to use the navigation toolbar (for, e.g., pan, zoom). First close the ROI before using the navigation toolbar again.  

  #### Registration (4POLAR) 
  When the selected method of analysis is `4POLAR 2D` or `4POLAR 3D`, an image registration is needed. Two options: 
  * The registration has already been performed, so load the registration file (`*.pyreg` file containing the geometric transformation). Click 'Load'. 
  * Otherwise, the registration is performed with a beads image file (`*.tif` file) and a whitelight image file (named `Whitelight.tif`). The two files need to be in the same folder. Click 'Perform'. 
The registration proceeds as follows: First, it determines the contours of the four fields of view using the whitelight image  -- the image is thresholded using `cv2.threshold` with `cv2.THRESH_BINARY + cv2.THRESH_OTSU` and the contours are determined using `cv2.findContours` (see [OpenCV](https://docs.opencv.org/) documentation for more details) -- Second, the beads image is split in four equal-sized images corresponding to the four polarized images of the beads; The intensities in the four images are normalized and thresholded using `cv2.threshold`; Third, the registration is performed using the polarized image on the top left as the fixed image and the three other polarized images as moving images. We use the scale-invariant feature transform (SIFT) algorithm `cv2.SIFT_create` to detect local features in the images. Using a matching algorithm between the location of the beads in the fixed and moving images (by solving the linear sum assignment problem with [`scipy.optimize.linear_sum_assignment`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html#scipy-optimize-linear-sum-assignment)), we determine the perspective transformations using `cv2.findHomography`. These geometric transformations will be applied to all the images selected in the analysis. A figure displays the resulting three registrations: If this registration is satisfactory, click 'Validate'. If it is satisfactory and you want to save it (to skip performing this registration in future analysis), click 'Save'. 
If the SIFT registration is unsuccessful or unsatifactory, the parameters of the SIFT method can be changed. Click 'Change', and a window appear with two parameters to change:
    - `contrastThreshold`: The contrast threshold used to filter out weak features in semi-uniform (low-contrast) regions. The larger the threshold, the less features are produced by the detector.
    - `sigma`: The sigma of the Gaussian applied to the input image at the octave #0. If your image is captured with a weak camera with soft lenses, you might want to reduce the number. For more information on these parameters, see [cv::SIFT Class Reference](https://docs.opencv.org/4.x/d7/d60/classcv_1_1SIFT.html).

    Click 'Perform' to redo the registration. If at any stage, you want to abort registration, click 'Cancel'. A new registration can be initiated by selecting '4POLAR 2D' or '4POLAR 3D' as the method of analysis.

   * What if the file `Whitelight.tif` is missing? Use [Fiji](https://imagej.net/software/fiji/) to create `Whitelight.tif` from a beads image file.
     - Open the beads image file with [Fiji](https://imagej.net/software/fiji/).
     - Adjust the brightness/contrast settings (Tab Image > Adjust > Brightness/Contrast) to visualize the four quadrants that contain the beads. You can manually set the intensity range with the "Set" button of the brightness/contrast window if needed.
     - Using the *Oval* selection tool, draw a circle over the upper left quadrant; use shift to make the selection circular.
     - When satisfied with the position and size of the circular selection, right-click on the selection and select "Create Mask". A new window will open with the respective selection as a black circle.
     - Go back to the beads image file, click on the circular selection and displace it to the next quadrant; resize if needed to fit the quadrant. Right-click and "Create Mask" as before to add this second circular selection to the mask image.
     - Proceed in the same way for the two last quadrants.
     - Once done invert the LUT of the image to have white circles in a black background (Tab Image > Lookup Tables > Invert LUT). Save the mask as "Whitelight.tif".
     
     - An example of Fiji-built Whitelight is given below:
 
        <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/Whitelight.png" alt=" " width="200"/>

[&uarr;](#manual)

___
### Intensity tab

  The intensity tab displays the total intensity (total = sum over the angles) image of the stack to be analyzed if the `Stack` slider is set to 'T', or the image *n* of the stack if the value of the `Stack` slider is set to *n*. The selected dark value has been removed from the total intensity (see [Advanced](#advanced-tab) tab for more information on the computation of the dark value).  

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/contrast.png" alt=" " width="30"/> The contrast can be adjusted with the contrast slider on the right hand side of the tab. This value of the contrast will be used in the intensity images in the figures.

  * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/square.png" alt=" " width="30"/> displays the angle (in deg) and the length (in number of pixels) of the segment selected on the intensity image. The angle is defined counter-clockwise in the field of view (see [Options](#options-tab) tab). Click the left mouse button to select this segment. In order to display the distance in &mu;m, enter the length of a pixel in nm in the entry box right below.


  The lower left part of the tab indicates the name of the stack to be analyzed.

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

#### ROI Manager
<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/format_list.png" alt=" " width="30"/> opens the ROI Manager. 
    
 - `ROI`: displays the index of the ROI, as displayed in the intensity and thresholding/mask images.
 - `name`: to be entered by the user as a tag of the specific ROI; it will be saved in the MS Excel.
 - `group `: to be entered by the user as a tag of the specicif group the ROI belongs to; it will be saved in the MS Excel.
 - `select`: select the ROIs to be considered in the analysis.
 - `delete`: select the ROIs to be permanently deleted (then click the button `Delete` to actually delete them and update the table and images).
 - (for versions < 2.5) Button `Commit`: click this button to commit the changes made to the labels of the ROIs (names, groups and selection).
 - Button `Save`: save the information on all the ROIs as a binary `.pyroi` file.
 - Button `Load`: load the ROIs from a binary `.pyroi` file.
 - Button `Delete`: permanently deletes all the ROIs selected in `delete`; ROIs are renumbered in the ROI Manager and in the intensity and thresholding/mask images.

 Use the toggle header to select or deselect all ROIs. 
     
#### Edge Detection
Click on the (orange) button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/multiline_chart.png" alt=" " width="30"/> to open a window for the determination of the edges of the thresholded image (click 'Compute') as displayed in the [Thresholding/Mask](#thresholdingmask-tab) tab, or the contours of the dowloaded image (click 'Download'). The edges are displayed as blue lines on the thresholded image. To compute the edges, the Canny edge detector `cv2.Canny` is used with two parameters `low threshold` and `high threshold` (see [Edge Detection](#edge-detection-tab) tab) after a first Gaussian blur `cv2.GaussianBlur` of the image (with (5, 5) as width and height of the kernel - the standard deviations are calculated from the kernel size, see [OpenCV](https://docs.opencv.org/) for more details). The contours are determined from the edges using `cv2.findContours` (with the contour retrieval mode `cv2.RETR_TREE` and contour approximation algorithm `cv2.CHAIN_APPROX_NONE`). The contours shorter than `Length` defined in the [Edge Detection](#edge-detection-tab) tab are discarded. The obtained contours are smoothed out using a Savitzky-Golay filter `scipy.savgol_filter` with third-order polynomials and a window length defined by `Smoothing window` (in pixels) in the [Edge Detection](#edge-detection-tab) tab. From these smooth contours, the angles and the normal to the contours are computed. The angles &rho; with respect to the contours are computed in a layer around the contours defined by `Layer width` (in pixels) in the [Edge Detection](#edge-detection-tab) tab. There is the possibility to slightly move away from the contour by changing `Distance from contour` in the [Edge Detection](#edge-detection-tab) tab. All the selected figures involving &rho; are duplicated using the relative values of &rho; with respect to the contours.  
To close the edge detection module, click on the (blue) button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/multiline_chart.png" alt=" " width="30"/>.  

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

  The `Variables` table lists all the possible variables *C*. Check the boxes for the variables *C* to be displayed and/or saved in the analysis. For `1PF`, `4POLAR 2D`: (&rho;, &psi;). For `CARS`, `SRS`, `2PF`: (&rho;, S<sub>2</sub>, S<sub>4</sub>). For `SHG`: (&rho;, S<sub>SHG</sub>). For `4POLAR 3D`: (&rho;, &psi;, &eta;). The second and third columns display the minimum and maximum values of the variables used for the colorbars of histograms and composite and stick maps. These elements are editable (except for &rho;) if the switch is selected.
  The colormap for &rho; is `hsv` (and `colorwheel` from [Colorcet](https://colorcet.holoviz.org/) for colorblind-friendly visualization). The colormap for &psi;, S<sub>2</sub>, S<sub>4</sub>, S<sub>SHG</sub> is `jet` (and `viridis` for colorblind-friendly visualization). The colormap for &eta; is `plasma`.   
  The format of the figures to be saved is selected using the option menu in the frame `Save output`. 
  

#### Preferences
  * Checkbox `Axes on figures`: if selected, the pixel numbers on the axes of each figure is displayed (also visible on the `.tif` images if selected).
  
  * Checkbox `Colorbar on figures`: if selected, the colorbar of each composite or stick figure is displayed (also visible on the `.tif` images if selected).
  
  * Checkbox `Colorblind-friendly`: if selected, uses colorblind-friendly colormaps for figure (also used in the `.tif` images if selected).
  
  * Spinners for the number of pixels separating sticks on stick maps: `vertical` = number of pixels separating sticks vertically, `horizontal` = number of pixels separating sticks horizontally (i.e., 1 means every pixel, 2 means every other pixel, etc...); the spinners apply directly to open stick figures.
  
  * Spiiner for the number of bins used in histogrames (default=60). 

  * Button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/crop.png" alt=" " width="30"/>: click to open the Crop Manager. Enter the x-range (xlim) and y-range (ylim) and then click `Crop` for cropping figures; or click `Get` to get the x-range and y-range of the active figure; click on 'Create ROI' to create a rectangular ROI with the set limit on the active figure; the values are also the ones used in the saved animated gif (see `Save output`). Click on `Reset` to go back to the original x-range and y-range.
  
#### Miscellaneous tools
* Button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/query_stats.png" alt=" " width="30"/>: Click this button to visualize the accuracy of the fitting per pixel. The selection of the pixel is done on the composite figure of &rho;. 

* Button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/merge.png" alt=" " width="30"/>: Click this button to merge the histograms of the variables selected in the Variables table. Select the folder containing the `.mat` files to be concatenated. 

 * Checkbox `per ROI`: if selected, the results are displayed and saved separately for each ROI; otherwise, the results are displayed and saved by grouping all ROIs. 

#### Save output

  The `Save output` table lists the saving options: `Data (.pykl)` for saving data as a compressed pickle file (to download as `Open analysis` in the download selection), `Data (.mat)` for saving the values of the variables for each pixel used in the analysis as a MATLAB `.mat` file, `Mean values (.xlsx)` for saving the mean values of the variables in a MS Excel file, and `Movie (.gif)` for an animated gif file of the stack or a region of the stack. Use the Crop Manager to define this region.
  Note that the stem (i.e., filename without the extension) of the saved files is the stem of the analyzed polar stack. If the same polar stack is used for multiple analyses, the data are appended in the same MS Excel file.
  Using the option menu `Figures`, select the format of the figures to be saved (as selected in the Figures table for the variables selected in the Variables table). Possible formats are `.pdf` (default), `.png`, `.jpeg`, `.tif` and `.pyfig` (for later use in `Open figure`). 

 * <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/delete_forever.png" alt=" " width="30"/> reinitializes the `Show/Save` and `Variable` tables.


*Convention for the origin of the angles*: The orientation angles &rho; (for sticks and histograms) are computed counter-clockwise in the field of view using the convention specified in the following image. Please also note the numbering of the pixels in the horizontal and vertical axes. 

<img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/convention.png" alt=" " width="300"/>

For 4POLAR methods, the orientation angles &eta; (for sticks and histograms) are computed such that 0&deg; corresponds to being perpendicular to the image plane and 90&deg; to being parallel to the image plane. 

[&uarr;](#manual)

___
### Advanced tab

#### Dark

The `Used dark value` indicated in the entry box is the value used in the analysis to remove the small residual intensity of the stack. The default is the `Calculated dark value` indicated above the entry box. To change it, select the switch and enter the chosen value in the entry box. For `1PF`, the minimum possible value is 480.

*Method to compute the* `Calculated dark value`: Each image of the stack is paved with non-overlapping cells of 20x20 pixels. The mean value of each cell is computed for the first image of the stack (first angle). The average over all angles of the cell with the smallest mean value is the `Calculated dark value`.

#### Polarization

* The value of the offset angle used in the analysis is indicated. This angle (in degrees) is measured according to the convention mentioned in the [Options](#options-tab) tab. In order to manually change this value, the switch should be set to 'On'.

* <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/clockwise.png" alt=" " width="30"/> or <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/counterclockwise.png" alt=" " width="30"/>: click to select the polarization direction as clockwise or counter-clockwise. The direction shown on the button is the direction chosen in the analysis. 

The offset angle and the polarization direction are saved in the MS Excel file (see `Save output` in the [Options](#options-tab) tab).

#### Disk cone / Calibration data (for 1PF and 4POLAR)

For 1PF: The drop down menu lists all the disk cones included in the app. If the disk cone to be used is not in the list, select `other`and download the appropriate disk cone. The choice of disk cone also sets the value for the offset angle.
Click the button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/photo.png" alt=" " width="30"/> to visualize the disk cone used in the `1PF` analysis. The name of the disk cone used in the analysis is displayed on the lower part of the panel. The name of the disk cone is saved in the MS Excel file (see `Save output` in the [Options](#options-tab) tab). 

For 4POLAR: The upper drop down menu lists all the calibration data included in the app. If the calibration data to be used is not in the list, select `other` and download the appropriate calibration data. The calibration data is a `.txt` file with a name of the type `Calib*.txt` containing a 4x3 matrix for `4POLAR 2D` (see [template](https://github.com/cchandre/Polarimetry/blob/master/pypolar/calibration/Calib_th_2D.txt)) or a 4x4 matrix for `4POLAR 3D` (see [template](https://github.com/cchandre/Polarimetry/blob/master/pypolar/calibration/Calib_th_3D.txt)). The name of the calibration data used in the analysis is displayed on the lower part of the panel.
Select the distribution of the polarization angles (0&deg;, 45&deg;, 90&deg;, 135&deg;) using the lower drop down menu: UL (upper left), UR (upper right), LR (lower right) and LL (lower left). The choice of distribution is saved in the MS Excel file (see `Save output` in the [Options](#options-tab) tab).

#### Binning

This option is used to improve the quality of the stack if the signal is too weak. It performs a convolution of the stack with a kernel of 1's of size `Bin width` x `Bin height`. A side effect is a blurring of the stack as displayed in the intensity images. The binning values are saved in the MS Excel file (see `Save output` in the [Options](#options-tab) tab).

#### Rotation

* `Stick (deg)`: (editable) value of the angle (in degrees) to arbitrarily rotate the sticks (following the above-mentioned convention: positive=counter-clockwise, negative=clockwise)
* `Figure (deg)`: (editable) value of the angle (in degrees) to arbitrarily rotate the entire figure (following the above-mentioned convention: positive=counter-clockwise, negative=clockwise)
* `Reference (deg)`: (editable) value of the angle (in degrees) with respect to which &rho; is normalized; if the change of reference angle is combined with a figure rotation, the reference angle has to be determined in the rotated figure.

#### Intensity removal

This option is used to remove some intensity from the stack. First, define the size in pixels (`Bin width` and `Bin height`) of the patch in the part of the intensity image. Second, select a point (center of the patch of size `Bin width` x `Bin height`) in the intensity image by clicking the button <img src="https://github.com/cchandre/Polarimetry/blob/master/pypolar/icons/removal.png" alt=" " width="30"/>. Third, choose the value `Factor` (between 0 and 1) for the fraction of the mean intensity of the patch to be removed from the stack. The mean value over the selected patch weighted by the chosen factor is removed from the entire stack. The value `Removed intensity value` which is substracted from the stack is indicated in the lower part of the panel.

[&uarr;](#manual)

___
### Edge Detection tab

#### Edge detection

* `Low threshold`: integer between 0 and 255 - hysteresis thresholding value used in the Canny edge detector: edges with intensity gradients below this value are not edges and discarded
* `High threshold`: integer between 0 and 255 - hysteresis thresholding value used in the Canny edge detector: edges with intensity gradients larger than this value are sure to be edges
* `Length`: minimum length of a contour (in pixels)
* `Smoothing window`: length in pixels of the window used for the smoothing (using a Savitzky-Golay filter `scipy.savgol_filter`)

#### Layer

* `Distance from contour`: number of pixels separating the contour from the layer
* `Layer width`: width of the layer in the neighborhood of the contour (in pixels)

[&uarr;](#manual)

___
For more information: <cristel.chandre@cnrs.fr>
