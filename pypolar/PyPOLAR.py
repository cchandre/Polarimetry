import customtkinter as CTk
from tkinter import Event as tkEvent
from tkinter import filedialog as fd
import sys
from pathlib import Path
import joblib
import pickle
import copy
import webbrowser
import numpy as np
from scipy.signal import convolve2d, savgol_filter
from scipy.interpolate import interpn
from scipy.ndimage import rotate
from scipy.io import savemat, loadmat
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.collections import PolyCollection
from matplotlib.backend_bases import FigureCanvasBase, _Mode, MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_pdf
from mpl_toolkits.axes_grid1 import make_axes_locatable
from colorcet import m_colorwheel
from PIL import Image
import cv2
from skimage.measure import manders_coloc_coeff, pearson_corr_coeff
import openpyxl
from itertools import permutations, chain
from datetime import date
import copy
from typing import List, Tuple, Union
from pypolar_classes import Stack, DataStack, Variable, ROI, Calibration, PyPOLARfigure, ROIManager, TabView, ToolTip
from pypolar_classes import Button, CheckBox, Entry, DropDown, Label, OptionMenu, SpinBox, ShowInfo, TextBox
from pypolar_classes import adjust, angle_edge, circularmean, divide_ext, find_matches, wrapto180
from pypolar_classes import button_size, geometry_info
from generate_json import font_macosx, font_windows, orange, gray, red, green, blue, text_color

try:
    from ctypes import windll 
    myappid = 'fr.cnrs.fresnel.pypolar'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

mpl.use('tkagg')

CTk.set_default_color_theme(Path(__file__).parent / 'polarimetry.json')
CTk.set_appearance_mode('dark')

plt.rcParams['font.size'] = 16
if sys.platform == 'darwin':
    plt.rcParams['font.family'] = font_macosx
    #mpl.use('macosx')
elif sys.platform == 'win32':
    plt.rcParams['font.family'] = font_windows
plt.rcParams['image.origin'] = 'upper'
plt.rcParams['figure.max_open_warning'] = 100
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['savefig.dpi'] = 100
plt.ion()

class Polarimetry(CTk.CTk):

    __version__ = '2.6.4'
    dict_versions = {'2.1': 'December 5, 2022', '2.2': 'January 22, 2023', '2.3': 'January 28, 2023', '2.4': 'February 2, 2023', '2.4.1': 'February 25, 2023', '2.4.2': 'March 2, 2023', '2.4.3': 'March 13, 2023', '2.4.4': 'March 29, 2023', '2.4.5': 'May 10, 2023', '2.5': 'May 23, 2023', '2.5.3': 'October 11, 2023', '2.6': 'October 16, 2023', '2.6.2': 'April 4, 2024', '2.6.3': 'July 18, 2024', '2.6.4': 'October 21, 2024'}
    __version_date__ = dict_versions.get(__version__, date.today().strftime('%B %d, %Y'))    

    ratio_app = 3 / 4
    ratio_fig = 3 / 5
    left_width = 205
    figsize = (450, 450)
    length_slider = 150

    url_github = 'https://github.com/cchandre/Polarimetry'
    url_wiki = url_github + '/wiki'
    url_fresnel = 'https://www.fresnel.fr/polarimetry'
    email = 'cristel.chandre@cnrs.fr'

    def __init__(self) -> None:
        super().__init__()

## MAIN
        base_dir = Path(__file__).parent
        image_path = base_dir / 'icons'

        height = int(self.ratio_app * self.winfo_screenheight())
        width = height + self.left_width
        delx, dely = self.winfo_screenwidth() // 10, self.winfo_screenheight() // 10
        dpi = self.winfo_fpixels('1i')
        self.figsize = (type(self).figsize[0] / dpi, type(self).figsize[1] / dpi)
        self.title('PyPOLAR')
        self.geometry(f'{width}x{height}+{delx}+{dely}')
        self.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.bind('<Command-q>', self.on_closing)
        self.bind('<Command-w>', self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)
        self.configure(fg_color=gray[0])
        self.icons = {file.stem: CTk.CTkImage(dark_image=Image.open(file).resize((60, 60)), size=(30, 30)) for file in image_path.glob('*.png')}
        if sys.platform == 'win32':
            self.iconbitmap(str(base_dir / 'main_icon.ico'))
            import winreg
            EXTS = ['.pyroi', '.pyreg', '.pyfig']
            TYPES = ['PyPOLAR ROI', 'PyPOLAR Registration', 'PyPOLAR Figure']
            ICONS = ['pyroi.ico', 'pyreg.ico', 'pyfig.ico']
            try:
                for EXT, TYPE, ICON in zip(EXTS, TYPES, ICONS):
                    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, EXT)
                    winreg.SetValue(key, None, winreg.REG_SZ, TYPE)
                    iconkey = winreg.CreateKey(key, 'DefaultIcon')
                    winreg.SetValue(iconkey, None, winreg.REG_SZ, str(image_path / ICON))
                    winreg.CloseKey(iconkey)
                    winreg.CloseKey(key)
            except WindowsError:
                pass

## DEFINE FRAMES
        left_frame = CTk.CTkScrollableFrame(master=self, corner_radius=0, fg_color=gray[0], scrollbar_button_color=gray[0], scrollbar_button_hover_color=gray[0])
        left_frame.pack(side=CTk.LEFT, fill=CTk.Y, expand=False)
        right_frame = CTk.CTkFrame(master=self, corner_radius=0, fg_color=gray[1])
        right_frame.pack(side=CTk.RIGHT, fill=CTk.BOTH, expand=True)
        self.tabview = TabView(right_frame)

## LEFT FRAME
        dict_left_frame = {'column': 0, 'padx': 20, 'pady': 20}
        Button(left_frame, text=' PyPOLAR', image=self.icons['blur_circular'], command=self.on_click_tab, tooltip=' - select a polarimetry method\n - download a .tiff stack file, a folder, or a PyPOLAR figure (.pyfig)\n - for a .tiff file or folder, select an option of analysis\n - select one or several regions of interest (ROI)\n - click on Analysis', hover=False, fg_color='transparent', font=CTk.CTkFont(size=24)).grid(row=0, column=0, padx=20, pady=(10, 40))
        self.method = CTk.StringVar()
        DropDown(left_frame, values=['1PF', 'CARS', 'SRS', 'SHG', '2PF', '4POLAR 2D', '4POLAR 3D'], image=self.icons['microscope'], command=self.method_dropdown_callback, variable=self.method, tooltip=' - 1PF: one-photon fluorescence\n - CARS: coherent anti-Stokes Raman scattering\n - SRS: stimulated Raman scattering\n - SHG: second-harmonic generation\n - 2PF: two-photon fluorescence\n - 4POLAR 2D: 2D 4POLAR fluorescence (not yet implemented)\n - 4POLAR 3D: 3D 4POLAR fluorescence').grid(row=1, **dict_left_frame)
        self.openfile_dropdown_value = CTk.StringVar()
        self.openfile_dropdown = DropDown(left_frame, values=['Open file', 'Open folder', 'Open figure'], image=self.icons['download_file'], variable=self.openfile_dropdown_value, command=self.open_file_callback, tooltip=' - open a file (.tif or .tiff stack file)\n - open a folder containing .tif or .tiff stack files\n - open figure (.pyfig file saved from a previous analysis)')
        self.openfile_dropdown.grid(row=2, **dict_left_frame)
        self.option = CTk.StringVar()
        self.options_dropdown = DropDown(left_frame, values=['Thresholding (manual)', 'Mask (manual)'], image=self.icons['build'], variable=self.option, state='disabled', command=self.options_dropdown_callback, tooltip=' select the method of analysis\n - intensity thresholding or segmentation mask for single file analysis (manual) or batch processing (auto)\n - the mask has to be binary and in PNG format and have the same file name as the respective polarimetry data file')
        self.options_dropdown.grid(row=3, **dict_left_frame)
        self.add_roi_button = Button(left_frame, text='Add ROI', image=self.icons['roi'], command=self.add_roi_callback, tooltip=' add a region of interest: polygon (left button), freeform (right button); double-click to close the ROI')
        self.add_roi_button.grid(row=4, **dict_left_frame)
        self.analysis_button = Button(left_frame, text='Analysis', command=self.analysis_callback, image=self.icons['play'], fg_color=green[0], hover_color=green[1], tooltip=' perform polarimetry analysis')
        self.analysis_button.grid(row=5, **dict_left_frame)
        Button(left_frame, text='Close figures', command=lambda:plt.close('all'), image=self.icons['close'], fg_color=red[0], hover_color=red[1], tooltip=' close all open figures').grid(row=6, **dict_left_frame)

## RIGHT FRAME: INTENSITY
        banner = CTk.CTkFrame(master=self.tabview.tab('Intensity'), fg_color='transparent')
        banner.pack(side=CTk.RIGHT, fill=CTk.Y, expand=False)
        Button(banner, image=self.icons['contrast'], command=self.contrast_intensity_button_callback, tooltip=' adjust contrast\n - the chosen contrast will be the one used\n for the intensity images in figures\n - the contrast changes the intensity value displayed in the navigation toolbar\n - the chosen contrast does not affect the analysis').grid(row=0, column=0, padx=10, pady=(20, 0))
        self.contrast_intensity_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation='vertical', height=self.length_slider, command=self.contrast_intensity_slider_callback)
        self.contrast_intensity_slider.set(1)
        self.contrast_intensity_slider.grid(row=1, column=0, padx=10, pady=(0, 20))
        self.compute_angle_button = Button(banner, image=self.icons['square'], command=self.compute_angle, tooltip=' left click to trace a line segment\n and determine its length and angle')
        self.compute_angle_button.grid(row=2, column=0, padx=10, pady=20)
        self.pixel_size = CTk.StringVar(value='0')
        entry = CTk.CTkEntry(banner, textvariable=self.pixel_size, border_color=gray[0], width=50, justify='center')
        ToolTip(entry, text=' enter the pixel size in nm')
        entry.grid(row=3, column=0, padx=10, pady=0)
        
        intensity_fig = Figure(figsize=(self.ratio_fig / dpi, self.ratio_fig / dpi), facecolor=gray[1])
        self.intensity_axis = intensity_fig.add_axes([0, 0, 1, 1])
        self.intensity_axis.set_axis_off()
        background = plt.imread(image_path / 'blur_circular-512.png')
        self.intensity_axis.imshow(background, cmap='gray', interpolation='bicubic', alpha=0.1)
        self.intensity_pyfig = PyPOLARfigure(intensity_fig, master=self.tabview.tab('Intensity'))

        bottomframe = CTk.CTkFrame(master=self.tabview.tab('Intensity'), fg_color='transparent')
        bottomframe.pack(side=CTk.BOTTOM, fill=CTk.X, expand=False, pady=5)
        self.filename_label = TextBox(master=bottomframe, width=200, height=50, tooltip=' name of file currently analyzed')
        self.filename_label.pack(side=CTk.LEFT, padx=(30, 0))
        sliderframe = CTk.CTkFrame(master=bottomframe, fg_color='transparent')
        sliderframe.pack(side=CTk.RIGHT)
        self.stack_slider = CTk.CTkSlider(master=sliderframe, from_=0, to=18, number_of_steps=18, width=self.length_slider, command=self.stack_slider_callback, state='disabled')
        self.stack_slider.set(0)
        self.stack_slider.pack(side=CTk.TOP)
        self.stack_slider_label = Label(master=sliderframe, text='T', tooltip=' slider at T for the total intensity, otherwise scroll through the images of the stack')
        self.stack_slider_label.pack(side=CTk.LEFT)
        Label(master=sliderframe, fg_color='transparent', text='Stack', tooltip=' slider at T for the total intensity, otherwise scroll through the images of the stack').pack(side=CTk.RIGHT)
        
## RIGHT FRAME: THRSH
        banner = CTk.CTkFrame(master=self.tabview.tab('Thresholding/Mask'), fg_color='transparent')
        banner.pack(side=CTk.RIGHT, fill=CTk.Y, expand=False)
        Button(banner, image=self.icons['contrast'], command=self.contrast_thrsh_button_callback, tooltip=' adjust contrast\n - the contrast changes the intensity value displayed in the navigation toolbar\n - the chosen contrast does not affect the analysis').grid(row=0, column=0, padx=10, pady=(20, 0))
        self.contrast_thrsh_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation='vertical', height=self.length_slider, command=self.contrast_thrsh_slider_callback)
        self.contrast_thrsh_slider.set(1)
        self.contrast_thrsh_slider.grid(row=1, column=0, padx=10, pady=(0, 20))
        Button(banner, image=self.icons['colorize'], command=self.change_colormap, tooltip=" change the colormap used for thresholding ('hot' or 'gray')").grid(row=2, column=0, padx=10, pady=10)
        self.no_background_button = Button(banner, image=self.icons['photo_fill'], command=self.no_background, tooltip=' change background to enhance visibility')
        self.no_background_button.grid(row=3, column=0, padx=10, pady=10)
        Button(banner, image=self.icons['open_in_new'], command=self.export_mask, tooltip=' export mask as .png').grid(row=4, column=0, padx=10, pady=10)
        Button(banner, image=self.icons['format_list'], command=self.roimanager_callback, tooltip=' open ROI Manager').grid(row=5, column=0, padx=10, pady=10)
        self.edge_button = Button(banner, image=self.icons['multiline_chart'], command=self.edge_button_callback, tooltip=' determine the edges of the thresholded image and compute orientations with respect to the edges')
        self.edge_button.grid(row=6, column=0, padx=10, pady=10)

        self.thrsh_axis_facecolor = gray[1]
        self.thrsh_fig = Figure(figsize=(self.ratio_fig / dpi, self.ratio_fig / dpi), facecolor=self.thrsh_axis_facecolor)
        self.thrsh_axis = self.thrsh_fig.add_axes([0, 0, 1, 1])
        self.thrsh_axis.set_axis_off()
        self.thrsh_axis.set_facecolor(self.thrsh_axis_facecolor)
        self.thrsh_axis.imshow(background, cmap='gray', interpolation='bicubic', alpha=0.1)
        self.thrsh_pyfig = PyPOLARfigure(self.thrsh_fig, master=self.tabview.tab('Thresholding/Mask'))

        bottomframe = CTk.CTkFrame(master=self.tabview.tab('Thresholding/Mask'), fg_color='transparent')
        bottomframe.pack(side=CTk.BOTTOM, fill=CTk.X, expand=False, pady=5)
        ilow_frame = CTk.CTkFrame(master=bottomframe, fg_color='transparent')
        ilow_frame.pack(side=CTk.LEFT, padx=(30, 0))
        self.ilow = CTk.StringVar(value='0')
        self.ilow_slider = CTk.CTkSlider(master=ilow_frame, from_=0, to=1, width=self.length_slider, command=self.ilow_slider_callback)
        self.ilow_slider.set(0)
        self.ilow_slider.grid(row=0, column=0, columnspan=2, sticky="sw")
        Label(master=ilow_frame, text='Ilow\n', anchor='w', tooltip= ' intensity value used for thresholding\n - use the slider or enter the value manually').grid(row=1, column=0, padx=20, sticky="sw")
        entry = CTk.CTkEntry(master=ilow_frame, textvariable=self.ilow, border_color=gray[1], width=100, justify=CTk.LEFT)
        entry.bind('<Return>', command=self.ilow2slider_callback)
        entry.grid(row=1, column=1, sticky="se")
        transparency_frame = CTk.CTkFrame(master=bottomframe, fg_color='transparent')
        transparency_frame.pack(side=CTk.RIGHT, padx=0)
        self.transparency_slider = CTk.CTkSlider(master=transparency_frame, from_=0, to=1, width=self.length_slider, command=self.transparency_slider_callback)
        self.transparency_slider.set(0)
        self.transparency_slider.grid(row=0, column=0)
        Label(master=transparency_frame, text='Transparency\n', tooltip=' use slider to adjust the transparency of the background image').grid(row=1, column=0, padx=20, sticky="sw")

## RIGHT FRAME: OPTIONS
        left_color = left_frame.cget('fg_color')
        dict_frame = {'fg_color': left_color}
        scrollable_frame = CTk.CTkScrollableFrame(master=self.tabview.tab('Options'), fg_color='transparent', scrollbar_fg_color='transparent', scrollbar_button_color=right_frame.cget('fg_color'), scrollbar_button_hover_color=left_color)
        scrollable_frame.columnconfigure((0, 1), weight=1)
        scrollable_frame.pack(side=CTk.LEFT, fill=CTk.BOTH, expand=True)
        
        show_save = CTk.CTkFrame(master=scrollable_frame, **dict_frame)
        show_save.grid(row=0, column=0, padx=0, pady=0)
        show_save.columnconfigure(0, weight=1)
        Label(master=show_save, text='Figures\n', width=250, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=3, padx=20, pady=(10, 0), sticky="n")
        Label(master=show_save, text='Show', width=30, anchor='w').grid(row=1, column=1, padx=(10, 20), pady=0, sticky="n")
        Label(master=show_save, text='Save', width=30, anchor='w').grid(row=1, column=2, padx=(0, 50), pady=0, sticky="n")
        labels = ['Composite', 'Sticks', 'Histogram', 'Intensity']
        self.show_table = [CheckBox(show_save) for _ in range(len(labels))]
        self.save_table = [CheckBox(show_save) for _ in range(len(labels))]
        for _ in range(len(labels)-1):
            Label(master=show_save, text=labels[_], anchor='w', width=80, height=30).grid(row=_+2, column=0, padx=(30, 0), sticky="n")
            self.save_table[_].configure(command=self.click_save_output)
            self.show_table[_].grid(row=_+2, column=1, pady=0, padx=(0, 10), sticky='n')
            self.save_table[_].grid(row=_+2, column=2, pady=0, padx=(0, 50), sticky='n')
        Label(master=show_save, text=labels[-1], anchor='w', width=80, height=30).grid(row=len(labels)+2, column=0, padx=(30, 0), pady=(0, 10), sticky="n")
        self.save_table[_].configure(command=self.click_save_output)    
        self.show_table[-1].grid(row=len(labels)+2, column=1, pady=(0, 10), padx=(0, 10), sticky='n')
        self.save_table[-1].grid(row=len(labels)+2, column=2, pady=(0, 10), padx=(0, 50), sticky='n')

        preferences = CTk.CTkFrame(master=scrollable_frame, **dict_frame)
        preferences.grid(row=1, column=0, rowspan=3, padx=0, pady=(20, 0), sticky="n")
        Label(master=preferences, text='Preferences\n', width=250, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky='n')
        self.add_axes_checkbox = CheckBox(preferences, text='\nAxes on figures\n', command=self.add_axes_on_all_figures)
        self.add_axes_checkbox.select()
        self.add_axes_checkbox.grid(row=1, column=0, columnspan=2, padx=40, pady=0, sticky='ew')
        self.colorbar_checkbox = CheckBox(preferences, text='\nColorbar on figures\n', command=self.colorbar_on_all_figures)
        self.colorbar_checkbox.select()
        self.colorbar_checkbox.grid(row=2, column=0, columnspan=2, padx=40, pady=0, sticky='ew')
        self.colorblind_checkbox = CheckBox(preferences, text='\nColorblind-friendly\n', command=self.colorblind_on_all_figures)
        self.colorblind_checkbox.grid(row=3, column=0, columnspan=2, padx=40, pady=(0, 10), sticky='ew')
        labels = [' pixels per stick (horizontal)', ' pixels per stick (vertical)']
        self.pixelsperstick_spinboxes = [SpinBox(master=preferences, command=self.pixelsperstick_spinbox_callback) for it in range(2)]
        for _ in range(2):
            self.pixelsperstick_spinboxes[_].grid(row=_+4, column=0, padx=(20, 0), pady=10)
            Label(master=preferences, text=labels[_], anchor='w', tooltip=' controls the density of sticks to be plotted').grid(row=_+4, column=1, padx=(0, 20), pady=10, sticky='w')
        self.histo_nbins = CTk.StringVar(value='60')
        SpinBox(master=preferences, from_=10, to_=90, step_size=10, textvariable=self.histo_nbins).grid(row=6, column=0, padx=(20, 0), pady=10)
        Label(master=preferences, text=' bins for histograms', anchor='w', tooltip=' controls the number of bins used in histograms').grid(row=6, column=1, padx=(0, 20), pady=10, sticky='w')
        Button(preferences, image=self.icons['crop'], command=self.crop_figures_callback, tooltip=' click button to define region and crop figures').grid(row=7, column=0, columnspan=2, pady=(0, 10))
        
        self.variable_table_frame = CTk.CTkFrame(master=scrollable_frame, **dict_frame)
        self.variable_table_frame.grid(row=0, column=1, padx=0, pady=0, sticky="n")

        banner = CTk.CTkFrame(master=scrollable_frame, fg_color=gray[1])
        banner.grid(row=1, column=1, padx=40, pady=(10, 0), sticky="n")
        Button(banner, image=self.icons['query_stats'], command=self.show_individual_fit_callback, tooltip=' show an individual fit\n - zoom into the region of interest in the Rho composite\n - click this button\n - select a pixel with the crosshair on the Rho composite then click').grid(row=0, column=0, padx=(0, 20), pady=0)
        Button(banner, image=self.icons['merge'], command=self.merge_histos, tooltip=' concatenate histograms\n - choose variables in the Variables table\n - click button to select the folder containing the .mat files').grid(row=0, column=1, padx=20, pady=0)
        self.per_roi = CheckBox(banner, text='per ROI', command=self.per_roi_callback, border_color=gray[0], tooltip=' show and save data/figures separately for each region of interest')
        self.per_roi.grid(row=0, column=2, padx=20, pady=0)

        save_ext = CTk.CTkFrame(master=scrollable_frame, **dict_frame)
        Label(master=save_ext, text='Save output\n', width=250, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=2, padx=(20, 20), pady=(10, 0), sticky="n")
        save_ext.grid(row=2, column=1, padx=0, pady=(10, 0), sticky="n")
        Label(save_ext, text='Figures', anchor='w').grid(row=1, column=0, padx=(40, 0), sticky='w')
        self.figure_extension = CTk.StringVar(value='.pdf')
        self.figure_extension_optionmenu = OptionMenu(save_ext, width=60, height=20, variable=self.figure_extension, values=['.pdf', '.png', '.jpeg', '.tif', '.pyfig'], state='disabled', fg_color=gray[0], button_color=gray[0], text_color_disabled=gray[1], button_hover_color=gray[0], anchor='e', tooltip=' select the file type for the saved figures')
        self.figure_extension_optionmenu.grid(row=1, column=1, padx=(0, 10))
        labels = ['Data (.mat)', 'Mean values (.xlsx)', 'Movie (.gif)']
        self.extension_table = [CheckBox(save_ext) for _ in range(len(labels))]
        for _ in range(len(labels)-1):
            Label(master=save_ext, text=labels[_], anchor='w').grid(row=_+2, column=0, padx=(40, 0), sticky='w')
            self.extension_table[_].grid(row=_+2, column=1, pady=0, padx=0)
        Label(master=save_ext, text=labels[-1], anchor='w').grid(row=len(labels)+1, column=0, padx=(40, 0), pady=(0, 10), sticky='w')
        self.extension_table[len(labels)-1].grid(row=len(labels)+1, column=1, pady=(0, 10), padx=0)    

        Button(scrollable_frame, image=self.icons['palette'], command=lambda:self.openweb('https://colab.research.google.com/drive/1Ho8kU1yYrtltQ0xPs5SB9osiB2fRG4SJ?usp=sharing'), tooltip=' opens the Jupyter Notebook to visualize and customize the colorbars used in PyPOLAR').grid(row=3, column=1, padx=(100, 0), pady=(10, 0), sticky="nw")

        Button(scrollable_frame, image=self.icons['delete_forever'], command=self.initialize_tables, tooltip=' reinitialize Figures, Save output and Variables tables').grid(row=3, column=1, padx=(0, 100), pady=(10, 0), sticky="ne")

## RIGHT FRAME: ADV
        scrollable_frame = CTk.CTkScrollableFrame(master=self.tabview.tab('Advanced'), fg_color='transparent', scrollbar_fg_color='transparent', scrollbar_button_color=right_frame.cget('fg_color'), scrollbar_button_hover_color=left_color)
        scrollable_frame.columnconfigure((0, 1), weight=1)
        scrollable_frame.pack(side=CTk.LEFT, fill=CTk.BOTH, expand=True)

        scrollable_frame.columnconfigure((0, 1, 2), weight=1)
        adv_elts = ['Dark', 'Binning', 'Polarization', 'Rotation', 'Disk cone / Calibration data', 'Intensity removal']
        adv_loc = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        columnspan = [1, 2, 1, 2, 1, 2]
        adv = {}
        for loc, elt, cspan in zip(adv_loc, adv_elts, columnspan):
            adv.update({elt: CTk.CTkFrame(master=scrollable_frame, **dict_frame)})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=(0, 20), sticky="n")
            Label(master=adv[elt], text=elt + '\n', width=230, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=cspan, padx=20, pady=(10, 0), sticky="n")

        self.dark_switch = CTk.CTkSwitch(master=adv['Dark'], text='', command=self.dark_switch_callback, onvalue='on', offvalue='off', width=50)
        self.dark_switch.grid(row=0, column=0, padx=20, pady=10, sticky='ne')
        self.dark = CTk.StringVar()
        self.dark_entry = Entry(adv['Dark'], text='Used dark value', textvariable=self.dark, row=1, column=0, sticky="nw", padx=40, tooltip=' for 1PF, use a dark value greater than 480\n - raw images correspond to a dark value 0')
        self.dark_entry.bind('<Return>', command=self.intensity_callback)
        self.dark_entry.set_state('disabled')       
        self.calculated_dark_label = Label(master=adv['Dark'], text='Calculated dark value = 0')
        self.calculated_dark_label.grid(row=2, column=0, sticky='w', padx=40, pady=(0, 10))
        
        self.offset_angle_switch = CTk.CTkSwitch(master=adv['Polarization'], text='', command=self.offset_angle_switch_callback, onvalue='on', offvalue='off', width=50)
        self.offset_angle_switch.grid(row=0, column=0, padx=20, pady=10, sticky='ne')
        self.offset_angle = CTk.StringVar(value='0')
        self.offset_angle_entry = Entry(adv['Polarization'], text='\nOffset angle (deg)\n', textvariable=self.offset_angle, row=1, sticky="nw", padx=40)
        self.offset_angle_entry.set_state('disabled')
        Label(master=adv['Polarization'], text=' ').grid(row=2, column=0)
        self.polar_dir = CTk.StringVar(value='clockwise')
        self.polarization_button = Button(adv['Polarization'], image=self.icons[self.polar_dir.get()], command=self.change_polarization_direction, tooltip=' change polarization direction')
        self.polarization_button.grid(row=2, column=0, pady=(0, 10))

        Button(adv['Disk cone / Calibration data'], image=self.icons['photo'], command=self.diskcone_display, tooltip=' display the selected disk cone (for 1PF)').grid(row=1, column=0, padx=(52, 0), pady=10, sticky='w')
        self.calib_dropdown = OptionMenu(master=adv['Disk cone / Calibration data'], values='', width=button_size[0]-button_size[1], height=button_size[1], dynamic_resizing=False, command=self.calib_dropdown_callback, tooltip=' 1PF: select disk cone depending on wavelength and acquisition date\n 4POLAR: select .mat file containing the calibration data')
        self.calib_dropdown.grid(row=1, column=0, padx=(0, 52), pady=10, sticky='e')
        self.calib_textbox = TextBox(master=adv['Disk cone / Calibration data'], width=250, height=50, state='disabled', fg_color=gray[0])
        self.calib_textbox.grid(row=3, column=0, pady=10)
        self.polar_dropdown = OptionMenu(master=adv['Disk cone / Calibration data'], width=button_size[0], height=button_size[1], dynamic_resizing=False, command=self.polar_dropdown_callback, state='disabled', text_color_disabled=gray[0], tooltip=' 4POLAR: select the distribution of polarizations (0,45,90,135) among quadrants clockwise\n Upper Left (UL), Upper Right (UR), Lower Right (LR), Lower Left (LL)')
        angles = [0, 45, 90, 135]
        self.dict_polar = {}
        for p in list(permutations([0, 1, 2, 3])):
            a = [angles[_] for _ in p]
            self.dict_polar.update({f'UL{a[0]}-UR{a[1]}-LR{a[2]}-LL{a[3]}': p})
        self.polar_dropdown.configure(values=list(self.dict_polar.keys()))
        self.polar_dropdown.grid(row=4, column=0, pady=10)

        labels = ['Bin width', 'Bin height']
        self.bin_spinboxes = [SpinBox(adv['Binning'], command=lambda:self.intensity_callback(event=1)) for _ in range(2)]
        for _ in range(2):
            self.bin_spinboxes[_].bind('<Return>', command=self.intensity_callback)
            self.bin_spinboxes[_].grid(row=_+1, column=0, padx=(30, 10), pady=0, sticky='e')
            Label(master=adv['Binning'], text='\n' + labels[_] + '\n', tooltip=' height and width of the bin used for data binning').grid(row=_+1, column=1, padx=(10, 60), pady=0, sticky='w')

        labels = ['Stick (deg)', 'Figure (deg)', 'Reference (deg)']
        self.rotation = [CTk.StringVar(value='0'), CTk.StringVar(value='0'), CTk.StringVar(value='0')]
        for _ in range(len(labels)):
            tooltip = ' positive value for counter-clockwise rotation\n negative value for clockwise rotation'
            if _ == 2:
                tooltip = u' normalize \u03C1 with respect to this angle\n -if combined with figure rotation, reference angle is determined in the rotated figure'
            Label(adv['Rotation'], text=labels[_] + '\n', tooltip=tooltip).grid(row=_+1, column=1, padx=(0, 10), pady=(6, 3), sticky='nw')
            entry = CTk.CTkEntry(adv['Rotation'], textvariable=self.rotation[_], width=50, justify='center')
            entry.grid(row=_+1, column=0, padx=20, pady=0, sticky='e')
            if _ != 1:
                entry.bind('<Return>', command=self.rotation_callback)
            elif _ == 1:
                entry.bind('<Return>', command=self.rotation1_callback)

        self.noise = [CTk.StringVar(value='1'), CTk.StringVar(value='3'), CTk.StringVar(value='3')]
        labels = ['Bin width', 'Bin height']
        for _ in range(2):
            SpinBox(adv['Intensity removal'], from_=3, to_=19, step_size=2, textvariable=self.noise[_+1]).grid(row=_+1, column=0, padx=(30, 10), pady=5, sticky='e')
            Label(master=adv['Intensity removal'], text='\n' + labels[_] + '\n', tooltip=' height and width of the bin used for intensity removal').grid(row=_+1, column=1, padx=(10, 60), pady=0, sticky='w')
        Label(master=adv['Intensity removal'], text='\nPick center of bin\n', tooltip=' pick center of the bin used for intensity removal').grid(row=3, column=1, padx=10, pady=0, sticky='w')
        Button(adv['Intensity removal'], image=self.icons['removal'], command=lambda:self.click_callback(self.intensity_axis, self.intensity_pyfig.canvas, 'click background'), tooltip=' click button and select a point on the intensity image').grid(row=3, column=0, pady=5, padx=25, sticky='e')
        CTk.CTkEntry(adv['Intensity removal'], textvariable=self.noise[0], width=50, justify='center').grid(row=4, column=0, sticky='e', padx=23)
        Label(adv['Intensity removal'], text='\nFactor\n', tooltip=' fraction of the mean intensity value to be substracted\n value between 0 and 1').grid(row=4, column=1, padx=10, sticky='w')
        self.intensity_removal_label = Label(master=adv['Intensity removal'], text='Removed intensity value = 0')
        self.intensity_removal_label.grid(row=5, column=0, columnspan=2, padx=(40, 10), pady=0, sticky='w')
        Label(master=adv['Intensity removal'], text=' ', height=5).grid(row=6, column=0)

## RIGHT FRAME: ABOUT
        dict_buttons = {'row': 0, 'padx': 20, 'pady': 20, 'sticky': "nw"}
        Button(self.tabview.tab('About'), image=self.icons['web'], command=lambda:self.openweb(type(self).url_fresnel), tooltip=' visit the polarimetry website').grid(column=0, **dict_buttons)
        Button(self.tabview.tab('About'), image=self.icons['mail'], command=self.send_email, tooltip=' send an email to report bugs and/or send suggestions').grid(column=1, **dict_buttons)
        Button(self.tabview.tab('About'), image=self.icons['GitHub'], command=lambda:self.openweb(type(self).url_github), tooltip=' visit the PyPOLAR GitHub page').grid(column=2, **dict_buttons)
        Button(self.tabview.tab('About'), image=self.icons['contact_support'], command=lambda:self.openweb(type(self).url_wiki), tooltip=' visit the PyPOLAR wiki').grid(column=3, **dict_buttons)
        about_textbox = TextBox(master=self.tabview.tab('About'), width=600, height=500, wrap='word')
        about_textbox.write(f'Version: {type(self).__version__} ({type(self).__version_date__}) \n\n\n Website: {self.url_fresnel} \n\n\n Source code available at {self.url_github} \n\n\n\n PyPOLAR is based on a code originally developed by Sophie Brasselet (Institut Fresnel, CNRS) \n\n\n To report bugs, send an email to\n     manos.mavrakis@cnrs.fr  (Manos Mavrakis, Institut Fresnel, CNRS) \n     {self.email}  (Cristel Chandre, Institut de Mathématiques de Marseille, CNRS) \n     sophie.brasselet@fresnel.fr  (Sophie Brasselet, Institut Fresnel, CNRS) \n\n\n\n BSD 2-Clause License\n\n Copyright(c) 2021, Cristel Chandre\n All rights reserved. \n\n\n  PyPOLAR was created using Python with packages Tkinter (CustomTkinter), NumPy, SciPy, OpenCV, scikit-image, Matplotlib, openpyxl, tksheet, colorcet, joblib \n\n\n  PyPOLAR uses Material Design icons by Google')
        about_textbox.grid(row=1, column=0, columnspan=4, padx=30, sticky="n")
        self.startup()

    def startup(self) -> None:
        self.method.set('1PF')
        self.option.set('Thresholding (manual)')
        self.openfile_dropdown_value.set('Open file')
        self.define_variable_table('1PF')
        self.CD = Calibration('1PF')
        self.calib_dropdown.configure(values=self.CD.list('1PF'))
        self.calib_dropdown.set(self.CD.list('1PF')[0])
        self.calib_textbox.write(self.CD.name)
        self.polar_dropdown.set('UL90-UR0-LR135-LL45')
        self.thrsh_colormap = 'hot'
        self.tabview.set('Intensity')
        self.filename_label.focus()
        self.removed_intensity = 0

    def initialize_slider(self) -> None:
        if hasattr(self, 'datastack'):
            self.stack_slider.configure(to=self.stack.nangle, number_of_steps=self.stack.nangle)
            self.ilow.set(self.stack.display.format(np.amin(self.datastack.intensity)))
            self.ilow_slider.set(float(self.ilow.get()) / float(np.amax(self.datastack.intensity)))
            self.contrast_intensity_slider.set(1)
            self.contrast_thrsh_slider.set(1)
            self.stack_slider.set(0)
            self.stack_slider_label.configure(text='T')

    def initialize_noise(self) -> None:
        vals = [1, 3, 3]
        for val, _ in zip(vals, self.noise):
            _.set(str(val))
        self.removed_intensity = 0
        self.intensity_removal_label.configure(text='Removed intensity value = 0')

    def initialize(self) -> None:
        self.initialize_slider()
        self.initialize_noise()
        if hasattr(self, 'datastack'):
            self.datastack.rois = []
        self.ontab_intensity()
        self.ontab_thrsh()

    def initialize_tables(self) -> None:
        for show, save in zip(self.show_table, self.save_table):
            show.deselect()
            save.deselect()
        if hasattr(self, 'variable_display'):
            for var in self.variable_display:
                var.set(0)
        for ext in self.extension_table:
            ext.deselect()
        self.figure_extension_optionmenu.configure(state='disabled')

    def click_save_output(self) -> None:
        vec = [val.get() for val in self.save_table]
        self.figure_extension_optionmenu.configure(state='normal' if any(vec)==1 else 'disabled')
        
    def on_closing(self) -> None:
        plt.close('all') 
        self.destroy()

    def clear_frame(self, frame:CTk.CTkFrame) -> None:
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()

    def openweb(self, url:str) -> None:
        webbrowser.open(url)

    def send_email(self) -> None:
        webbrowser.open('mailto:?to=' + type(self).email + '&subject=[PyPOLAR] question', new=1)

    def on_click_tab(self) -> None:
        self.tabview.set('About' if self.tabview.get()!='About' else 'Intensity')

    def edge_button_callback(self) -> None:
        if hasattr(self, 'stack'):
            if hasattr(self, 'edge_contours'):
                self.edge_button.configure(fg_color=orange[0])
                delattr(self, 'edge_contours')
                self.tabview.delete('Edge Detection')
                self.ontab_thrsh()
            else:
                if not hasattr(self, 'edge_window'):
                    self.edge_button.configure(fg_color=blue[0])
                    self.edge_window = ShowInfo(message=' Image for edge detection', image=self.icons['multiline_chart'], button_labels=['Download', 'Compute', 'Cancel'], geometry=(370, 140), fontsize=16)
                    self.edge_window.protocol('WM_DELETE_WINDOW', self.cancel_edge_mask)
                    self.edge_window.bind('<Command-q>', self.cancel_edge_mask)
                    self.edge_window.bind('<Command-w>', self.cancel_edge_mask)
                    buttons = self.edge_window.get_buttons()
                    buttons[0].configure(command=self.download_edge_mask)
                    buttons[1].configure(command=self.compute_edge_mask)
                    buttons[2].configure(command=self.cancel_edge_mask)
                else: 
                    self.cancel_edge_mask()

    def cancel_edge_mask(self) -> None:
        self.edge_window.withdraw()
        delattr(self, 'edge_window')
        if hasattr(self, 'edge_contours'):
            delattr(self, 'edge_contours')
        self.edge_button.configure(fg_color=orange[0])

    def download_edge_mask(self) -> None:
        self.edge_window.withdraw()
        delattr(self, 'edge_window')
        filetypes = [('PNG files', '*.png')]
        initialdir = self.stack.folder if hasattr(self, 'stack') else Path.home()
        file = fd.askopenfilename(title='Select a mask file', initialdir=initialdir, filetypes=filetypes)
        self.edge_method = 'download'
        self.edge_detection_tab()
        self.edge_mask = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
        self.compute_edges()

    def compute_edge_mask(self) -> None:
        self.edge_window.withdraw()
        delattr(self, 'edge_window')
        self.edge_method = 'compute'
        self.edge_detection_tab()
        self.compute_edges()

    def edge_detection_tab(self) -> None:
        self.tabview.insert(4, 'Edge Detection')
        adv_elts = ['Edge detection', 'Layer']
        adv_sides = [CTk.LEFT, CTk.RIGHT]
        adv = {}
        for elt, side in zip(adv_elts, adv_sides):
            adv.update({elt: CTk.CTkFrame(
            master=self.tabview.tab('Edge Detection'), fg_color=gray[0])})
            adv[elt].pack(side=side, padx=20, pady=(10, 10))
            Label(master=adv[elt], text=elt + '\n', width=230, font=CTk.CTkFont(size=16)).grid(row=0, column=0, padx=20, pady=(10,0))
        params = ['Low threshold', 'High threshold', 'Length', 'Smoothing window']
        tooltips = [' hysteresis thresholding values: edges with intensity gradients\n below this value are not edges and discarded ', ' hysteresis thresholding values: edges with intensity gradients\n larger than this value are sure to be edges', ' minimum length for a contour (in pixels)', ' number of pixels in the window used for smoothing contours (in pixels)']
        self.canny_thrsh = [CTk.StringVar(value='60'), CTk.StringVar(value='100'), CTk.StringVar(value='100'), CTk.StringVar(value='20')]
        for _, (param, tooltip) in enumerate(zip(params, tooltips)):
            entry = Entry(adv['Edge detection'], text=param, textvariable=self.canny_thrsh[_], row=_+1, tooltip=tooltip)
            entry.bind('<Return>', command=self.compute_edges)
        Label(master=adv['Edge detection'], text=' ').grid(row=5, column=0)
        params = ['Distance from contour', 'Layer width']
        tooltips = [' width of the region to be analyzed (in pixels)', ' distance from contour of the region to be analyzed (in pixels)']
        self.layer_params = [CTk.StringVar(value='0'), CTk.StringVar(value='10')]
        for _, (param, tooltip) in enumerate(zip(params, tooltips)):
            Entry(adv['Layer'], text=param, textvariable=self.layer_params[_], row=_+1, tooltip=tooltip)
        Label(master=adv['Layer'], text=' ').grid(row=3, column=0)

    def compute_edges(self, event:tkEvent=None) -> None:
        if self.edge_method == 'compute':
            field = self.stack.intensity.copy()
            thrsh = float(self.ilow.get())
            field[field <= thrsh] = 0
            field = (field / np.amax(field) * 255).astype(np.uint8)
            field = cv2.GaussianBlur(field, (5, 5), 0)
            edges = cv2.Canny(image=field, threshold1=float(self.canny_thrsh[0].get()), threshold2=float(self.canny_thrsh[1].get()))
            self.edge_contours = self.smooth_contours(cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0])
            self.ontab_thrsh()
        elif self.edge_method == 'download':
            self.edge_contours = self.smooth_contours(cv2.findContours(self.edge_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0])
            self.ontab_thrsh()

    def smooth_contours(self, contours:List) -> List:
        window_length = int(self.canny_thrsh[3].get())
        edge_contours = []
        for contour in contours:
            if (len(contour) >= int(self.canny_thrsh[2].get())):
                edge_contours += [savgol_filter(contour.reshape((-1, 2)), window_length=window_length, polyorder=3, mode='nearest', axis=0)]
        return edge_contours
    
    def define_rho_ct(self, contours:List[np.ndarray]) -> np.ndarray:
        rho_ct = np.nan * np.ones_like(self.stack.intensity)
        for contour in contours:
            angle, normal = angle_edge(contour)
            crange = chain(range(-int(self.layer_params[0].get()) - int(self.layer_params[1].get()), -int(self.layer_params[0].get()) + 1), range(int(self.layer_params[0].get()), int(self.layer_params[0].get()) + int(self.layer_params[1].get()) + 1))
            for _ in crange:
                shift_x = (contour[:, 0] + _ * normal[:, 0]).astype(np.uint16)
                shift_y = (contour[:, 1] + _ * normal[:, 1]).astype(np.uint16)
                shift_x[shift_x <= 0] = 0
                shift_y[shift_y <= 0] = 0
                shift_x[shift_x >= self.stack.width - 1] = self.stack.width - 1
                shift_y[shift_y >= self.stack.height - 1] = self.stack.height - 1
                rho_ct[shift_y, shift_x] = angle
        return rho_ct

    def change_polarization_direction(self):
        self.polar_dir.set('clockwise' if self.polar_dir.get() == 'counterclockwise' else 'counterclockwise')
        self.polarization_button.configure(image=self.icons[self.polar_dir.get()])

    def contrast_thrsh_slider_callback(self, value:float) -> None:
        self.contrast_thrsh_slider.set(0.01 if value <= 0.01 else value)
        self.ontab_thrsh()

    def contrast_intensity_slider_callback(self, value:float) -> None:
        self.contrast_intensity_slider.set(0.01 if value <= 0.01 else value)
        self.ontab_intensity()

    def contrast_intensity_button_callback(self) -> None:
        value = self.contrast_intensity_slider.get()
        self.contrast_intensity_slider.set(0.5 if value <= 0.5 else 1)
        self.ontab_intensity()

    def contrast_thrsh_button_callback(self) -> None:
        self.contrast_thrsh_slider.set(0.5 if self.contrast_thrsh_slider.get() <= 0.5 else 1)
        self.ontab_thrsh(update=True)

    def roimanager_callback(self) -> None:

        def on_closing(manager:ROIManager) -> None:
            if hasattr(self, 'datastack'):
                self.datastack.rois = manager.update_rois(self.datastack.rois)
                self.ontab_intensity()
                self.ontab_thrsh()
            manager.destroy()
            delattr(self, 'manager')

        def on_edit(manager:ROIManager, rois, event=None) -> None:
            rois = manager.update_rois(rois)
            self.ontab_intensity()
            self.ontab_thrsh()

        def delete(manager:ROIManager) -> None:
            if hasattr(self, 'datastack'):
                manager.delete(self.datastack.rois)
                self.ontab_intensity()
                self.ontab_thrsh()

        def load(manager:ROIManager) -> None:
            if hasattr(self, 'datastack'):
                self.datastack.rois = manager.load(initialdir=self.stack.folder if hasattr(self, 'stack') else Path.home())
                self.ontab_intensity()
                self.ontab_thrsh()

        if not hasattr(self, 'manager'):
            button_images = [self.icons['save'], self.icons['download'], self.icons['delete']]
            self.manager = ROIManager(rois=self.datastack.rois if hasattr(self, 'datastack') else [], button_images=button_images)
            self.manager.protocol('WM_DELETE_WINDOW', lambda:on_closing(self.manager))
            self.manager.bind('<Command-q>', lambda:on_closing(self.manager))
            self.manager.bind('<Command-w>', lambda:on_closing(self.manager))
            buttons = self.manager.get_buttons()
            buttons[0].configure(command=lambda:self.manager.save(self.datastack.rois, self.datastack.file))
            buttons[1].configure(command=lambda:load(self.manager))
            buttons[2].configure(command=lambda:delete(self.manager))
            try:
                self.manager.sheet.extra_bindings("edit_cell", func=lambda _:on_edit(self.manager, self.datastack.rois, _))
                self.manager.sheet.extra_bindings("edit_header", func=lambda _:on_edit(self.manager, self.datastack.rois, _))
            except:
                pass

    def add_axes_on_all_figures(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (fig.type in ['Composite', 'Sticks', 'Intensity']):
                if (hasattr(self, 'datastack')  and (self.datastack.name in fs)) or self.openfile_dropdown_value.get() == 'Open figure':
                    fig.axes[0].axis(self.add_axes_checkbox.get())
                    fig.canvas.draw()
            elif fig.type == 'Histogram' and (hasattr(self, 'datastack') and self.datastack.name in fs):
                fig.axes[0].tick_params(labelcolor='k' if self.add_axes_checkbox.get() else 'w')

    def colorbar_on_all_figures(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (fig.type in ['Composite', 'Sticks', 'Intensity']) :
                if (hasattr(self, 'datastack') and (self.datastack.name in fs)) or self.openfile_dropdown_value.get() == 'Open figure':
                    if self.colorbar_checkbox.get():
                        ax_divider = make_axes_locatable(fig.axes[0])
                        cax = ax_divider.append_axes('right', size='7%', pad='2%')
                        if fig.type == 'Composite':
                            fig.colorbar(fig.axes[0].images[1], cax=cax)
                        elif (fig.type == 'Sticks') or ((fig.type == 'Intensity') and hasattr(self, 'edge_contours')):
                            fig.colorbar(fig.axes[0].collections[0], cax=cax)
                        if (fig.type == 'Intensity') and (not hasattr(self, 'edge_contours')):
                            fig.axes[1].remove()
                    else:
                        if len(fig.axes) >= 2:
                            fig.axes[1].remove()
                if self.openfile_dropdown_value.get() == 'Open figure':
                    plt.show()

    def colorblind_on_all_figures(self) -> None:
            figs = list(map(plt.figure, plt.get_fignums()))
            for fig in figs:
                fs = fig.canvas.manager.get_window_title()
                if hasattr(self, 'datastack'):
                    for var in self.datastack.vars:
                        if (var.name == fig.var):
                            cmap = var.colormap[self.colorblind_checkbox.get()]
                    if fig.type == 'Intensity':
                        cmap = self.datastack.vars[0].colormap[self.colorblind_checkbox.get()]
                    if (fig.type == 'Composite') and (self.datastack.name in fs):
                        fig.axes[0].images[1].set_cmap(cmap)
                    elif ((fig.type == 'Sticks') or ((fig.type == 'Intensity') and hasattr(self, 'edge_contours'))) and (self.datastack.name in fs):
                        fig.axes[0].collections[0].set_cmap(cmap)
                if fs.startswith('Disk Cone'):
                    fig.axes[0].images[0].set_cmap('hsv' if not self.colorblind_checkbox.get() else m_colorwheel)
                    fig.axes[1].images[0].set_cmap('jet' if not self.colorblind_checkbox.get() else 'viridis')

    def options_dropdown_callback(self, option:str) -> None:
        self.options_dropdown.get_icon().configure(image=self.icons['build_fill'] if option.endswith('(auto)') else self.icons['build'])
        if option.startswith('Mask'):
            initialdir = self.stack.folder if hasattr(self, 'stack') else Path.home()
            self.maskfolder = Path(fd.askdirectory(title='Select the directory containing masks', initialdir=initialdir))
            if hasattr(self, 'datastack'):
                self.mask = self.get_mask(self.datastack)
                self.ontab_thrsh()
                self.tabview.tab('Thresholding/Mask').update()

    def open_file_callback(self, value:str) -> None:
        initialdir = self.stack.folder if hasattr(self, 'stack') else Path.home()
        if hasattr(self, 'manager'):
            self.manager.delete_manager()
        self.filelist = []
        self.edge_button.configure(fg_color=orange[0])
        if hasattr(self, 'edge_contours'):
            delattr(self, 'edge_contours')
            self.tabview.delete('Edge Detection')
        if value == 'Open file':
            filetypes = [('Tiff files', '*.tiff'), ('Tiff files', '*.tif')]
            file = Path(fd.askopenfilename(title='Select a file', initialdir=initialdir, filetypes=filetypes))
            self.openfile_dropdown.get_icon().configure(image=self.icons['photo_fill'])
            if file.suffix in ['.tiff', '.tif']:
                self.options_dropdown.get_icon().configure(image=self.icons['build'])
                self.options_dropdown.set_state('normal')
                self.options_dropdown.set_values(['Thresholding (manual)', 'Mask (manual)'])
                self.option.set('Thresholding (manual)')
                if hasattr(self, 'mask'):
                    delattr(self, 'mask')
                self.open_file(file)
        elif value == 'Open folder': 
            folder = Path(fd.askdirectory(title='Select a directory', initialdir=initialdir))
            self.openfile_dropdown.get_icon().configure(image=self.icons['folder_open'])
            self.filelist = [file for file in sorted(folder.glob('*.tif*'))]
            self.indxlist = 0
            if any(self.filelist):
                self.open_file(self.filelist[0])
                self.options_dropdown.set_state('normal')
                self.options_dropdown.set_values(['Thresholding (manual)', 'Thresholding (auto)', 'Mask (manual)', 'Mask (auto)'])
                self.option.set('Thresholding (manual)')
            else:
                ShowInfo(message=' The folder does not contain TIFF or TIF files', image=self.icons['download_folder'], button_labels=['OK'], geometry=(340, 140))
        elif value == 'Open figure':
            file = Path(fd.askopenfilename(title='Download a previous polarimetry figure', initialdir=initialdir, filetypes=[('PyPOLAR pickle figure', '*.pyfig')]))
            self.openfile_dropdown.get_icon().configure(image=self.icons['imagesmode'])
            if file.suffix == '.pyfig':
                fig = pickle.load(open(file, 'rb'))
                fig.canvas.manager.set_window_title(fig.var + ' ' + fig.type)
                fig.show()
        if hasattr(self, 'stack'):
            self.ilow.set(self.stack.display.format(np.amin(self.stack.intensity)))
            self.ontab_thrsh(update=False)

    def crop_figures_callback(self) -> None:
        if len(plt.get_fignums()) and (not hasattr(self, 'crop_window')):
            self.crop_window = CTk.CTkToplevel(self)
            self.crop_window.title('Crop Manager')
            self.crop_window.geometry(geometry_info((440, 230)))
            self.crop_window.protocol('WM_DELETE_WINDOW', self.crop_on_closing)
            self.crop_window.bind('<Command-q>', lambda:self.crop_on_closing)
            self.crop_window.bind('<Command-w>', self.crop_on_closing)
            Label(self.crop_window, text='  define xlim and ylim', image=self.icons['crop'], compound='left', font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=3, padx=30, pady=20)
            if not hasattr(self, 'xylim'):
                if hasattr(self, 'datastack'):
                    vals = [1, self.datastack.width, 1, self.datastack.height]
                elif self.openfile_dropdown_value.get() == 'Open figure':
                    fig = plt.gcf()
                    vals = [1, fig.width, 1, fig.height]
                self.xylim = [CTk.StringVar(value=str(val)) for val in vals]
            labels = [u'\u2B62 xlim', u'\u2B63 ylim']
            positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
            for _, label in enumerate(labels):
                Label(master=self.crop_window, text=label).grid(row=_+1, column=0, padx=(20, 0), pady=0)
            for var, position in zip(self.xylim, positions):
                Entry(master=self.crop_window, textvariable=var, row=position[0], column=position[1])
            banner = CTk.CTkFrame(self.crop_window)
            banner.grid(row=3, column=0, columnspan=3, padx=20)
            Button(banner, text='Crop', anchor='center', command=self.crop_figures, width=80, height=button_size[1], tooltip=' crop figures using the chosen axis limits').grid(row=0, column=0, padx=10, pady=20)
            Button(banner, text='Get', anchor='center', command=self.get_axes, width=80, height=button_size[1], tooltip=' get the axis limits of the active figure').grid(row=0, column=1, padx=10, pady=20)
            Button(banner, text='Create ROI', anchor='center', command=self.createROIfromcrop, width=80, height=button_size[1], tooltip=' create a rectangular ROI with the limits defined above').grid(row=0, column=2, padx=10, pady=20)
            Button(banner, text='Reset', anchor='center', command=self.reset_figures, width=80, height=button_size[1]).grid(row=0, column=3, padx=10, pady=20)

    def crop_on_closing(self):
        self.crop_window.destroy()
        delattr(self, 'crop_window')

    def crop_figures(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            valid = (self.datastack.name in fs) if hasattr(self, 'datastack') else False
            if (fig.type in ['Sticks', 'Composite', 'Intensity']) and (valid or self.openfile_dropdown_value.get()=='Open figure'):
                fig.axes[0].set_xlim((int(self.xylim[0].get()), int(self.xylim[1].get())))
                fig.axes[0].set_ylim((int(self.xylim[3].get()), int(self.xylim[2].get())))
                if self.openfile_dropdown_value.get()=='Open figure':
                    plt.show()

    def get_axes(self) -> None:
        fig = plt.gcf()
        if fig.type in ['Sticks', 'Composite', 'Intensity']:
            ax = fig.axes[0]
            self.xylim[0].set(int(ax.get_xlim()[0]))
            self.xylim[1].set(int(ax.get_xlim()[1]))
            self.xylim[2].set(int(ax.get_ylim()[1]))
            self.xylim[3].set(int(ax.get_ylim()[0]))
        else:
            ShowInfo(message=' Select an active figure of the type\n Composite, Sticks or Intensity', image=self.icons['crop'], button_labels=['OK'])

    def createROIfromcrop(self) -> None:
        if hasattr(self, 'datastack'):
            self.get_axes()
            roix = np.asarray([int(self.xylim[0].get()), int(self.xylim[1].get()), int(self.xylim[1].get()), int(self.xylim[0].get())])
            roiy = np.asarray([int(self.xylim[3].get()), int(self.xylim[3].get()), int(self.xylim[2].get()), int(self.xylim[2].get())])
            if (float(self.rotation[1].get()) != 0) :
                theta = -np.deg2rad(float(self.rotation[1].get()))
                cosd, sind = np.cos(theta), np.sin(theta)
                x0, y0 = self.datastack.width / 2, self.datastack.height / 2
                vertices = np.asarray([x0 + (roix - x0) * cosd + (roiy - y0) * sind, y0 - (roix - x0) * sind + (roiy - y0) * cosd])
            else:
                vertices = np.asarray([roix, roiy])
            indx = self.datastack.rois[-1]['indx'] + 1 if self.datastack.rois else 1
            self.datastack.rois += [{'indx': indx, 'label': (vertices[0][0], vertices[1][0]), 'vertices': vertices, 'ILow': self.ilow.get(), 'name': '', 'group': '', 'select': True}]
            self.thrsh_pyfig.canvas.draw()
            self.ontab_intensity()
            self.ontab_thrsh()
            if hasattr(self, 'manager'):
                self.manager.update_manager(self.datastack.rois)

    def reset_figures(self) -> None:
        if hasattr(self, 'datastack'):
            vals = [1, self.datastack.width, 1, self.datastack.height]
        elif self.openfile_dropdown_value.get() == 'Open figure':
            fig = plt.gcf()
            vals = [1, fig.width, 1, fig.height]
        if hasattr(self, 'datastack') or self.openfile_dropdown_value.get() == 'Open figure':
            for _, val in enumerate(vals):
                self.xylim[_].set(val)
            self.crop_figures()

    def clear_patches(self, ax:plt.Axes, canvas:FigureCanvasTkAgg) -> None:
        if ax.patches:
            for p in ax.patches:
                p.set_visible(False)
                p.remove()
            for txt in ax.texts:
                txt.set_visible(False)
            canvas.draw()

    def export_mask(self) -> None:
        if hasattr(self, 'datastack'):
            window = ShowInfo(message=' Select output mask type: \n\n   - ROI: export ROIs as segmentation mask \n   - Intensity: export intensity-thresholded image as segmentation mask \n   - ROI \u00D7 Intensity: export intensity-thresholded ROIs as segmentation mask', image=self.icons['open_in_new'], button_labels=['ROI', 'Intensity', 'ROI \u00D7 Intensity', 'Cancel'], geometry=(530, 200))
            buttons = window.get_buttons()
            buttons[0].configure(command=lambda:self.export_mask_callback(window, 0))
            buttons[1].configure(command=lambda:self.export_mask_callback(window, 1))
            buttons[2].configure(command=lambda:self.export_mask_callback(window, 2))
            buttons[3].configure(command=lambda:self.export_mask_callback(window, 3))

    def export_mask_callback(self, window:CTk.CTkToplevel, event:int) -> None:
        roi_map, mask = self.compute_roi_map(self.datastack)
        array = []
        if event == 0:
            array = (255 * (roi_map != 0)).astype(np.uint8)
        elif event == 1:
            array = (255 * (self.datastack.intensity >= float(self.ilow.get()))).astype(np.uint8)
        elif event == 2:
            array = (255 * mask).astype(np.uint8)
        if np.any(array):
            data = Image.fromarray(array)
            data.save(self.datastack.file.with_suffix('.png'))
        window.withdraw()

    def change_colormap(self) -> None:
        self.thrsh_colormap = 'gray' if self.thrsh_colormap == 'hot' else 'hot'
        self.ontab_thrsh()

    def no_background(self) -> None:
        if hasattr(self, 'stack'):
            if self.thrsh_fig.patch.get_facecolor() == mpl.colors.to_rgba('k', 1):
                self.thrsh_fig.patch.set_facecolor(gray[1])
                self.no_background_button.configure(image=self.icons['photo_fill'])
            else:
                self.thrsh_fig.patch.set_facecolor('k')
                self.no_background_button.configure(image=self.icons['photo'])
            self.thrsh_pyfig.canvas.draw()

    def offset_angle_switch_callback(self) -> None:
        self.offset_angle_entry.set_state('normal' if self.offset_angle_switch.get() == 'on' else 'disabled')

    def dark_switch_callback(self) -> None:
        if hasattr(self, 'stack'):
            if self.dark_switch.get() == 'on':
                self.dark_entry.set_state('normal')
                self.dark.set(self.stack.display.format(self.calculated_dark))
            else:
                self.dark_entry.set_state('disabled')
                self.dark.set(self.stack.display.format(self.calculated_dark))
                self.intensity_callback(event=1)
        else:
            self.dark.set('')

    def calib_dropdown_callback(self, label:str) -> None:
        self.CD = Calibration(self.method.get(), label=label)
        self.offset_angle.set(str(self.CD.offset_default))
        self.calib_textbox.write(self.CD.name)

    def show_individual_fit_callback(self) -> None:
        if not self.method.get().endswith('4POLAR') and hasattr(self, 'datastack'):
            figs = list(map(plt.figure, plt.get_fignums()))
            fig_ = None
            for fig in figs:
                fs = fig.canvas.manager.get_window_title()
                if fig.var == 'Rho' and fig.type == 'Composite' and (self.datastack.name in fs):
                    fig_ = fig
                    break
            if fig_ is not None:
                plt.figure(fig_)
                cfm = plt.get_current_fig_manager()
                cfm.window.attributes('-topmost', True)
                cfm.window.tkraise()
                self.click_callback(fig_.axes[0], fig_.canvas, 'individual fit')
                cfm.window.attributes('-topmost', False)
            else:
                ShowInfo(message='  provide a Rho Composite figure\n  to plot individual fits', image=self.icons['query_stats'], button_labels=['OK'])

    def diskcone_display(self) -> None:
        if self.method.get() == '1PF' and hasattr(self, 'CD'):
            self.CD.display(colorblind=self.colorblind_checkbox.get())

    def variable_table_switch_callback(self) -> None:
        state = 'normal' if self.variable_table_switch.get() == 'on' else 'disabled'
        for entry in self.variable_entries[2:]:
            entry.set_state(state)

    def click_callback(self, ax:plt.Axes, canvas:FigureCanvasTkAgg, method:str) -> None:
        if hasattr(self, 'datastack'):
            if method == 'click background':
                self.tabview.set('Intensity')
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            hlines = [plt.Line2D([(xlim[0] + xlim[1])/2, (xlim[0] + xlim[1])/2], ylim, lw=1, color='w'),
                plt.Line2D(xlim, [(ylim[0] + ylim[1])/2, (ylim[0] + ylim[1])/2], lw=1, color='w')]
            ax.add_line(hlines[0])
            ax.add_line(hlines[1])
            self.__cid1 = canvas.mpl_connect('motion_notify_event', lambda event: self.click_motion_notify_callback(event, hlines, ax, canvas))
            if method == 'click background':
                self.__cid2 = canvas.mpl_connect('button_press_event', lambda event: self.click_background_button_press_callback(event, hlines, ax, canvas))
            elif method == 'individual fit':
                self.__cid2 = canvas.mpl_connect('button_press_event', lambda event: self.individual_fit_button_press_callback(event, hlines, ax, canvas))

    def click_motion_notify_callback(self, event:MouseEvent, hlines:List[mpl.lines.Line2D], ax:plt.Axes, canvas:FigureCanvasTkAgg) -> None:
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            if event.button is None:
                hlines[0].set_data([x, x], ylim)
                hlines[1].set_data(xlim, [y, y])
                canvas.draw()

    def click_background_button_press_callback(self, event:MouseEvent, hlines:List[mpl.lines.Line2D], ax:plt.Axes, canvas:FigureCanvasTkAgg) -> None:
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                x1, x2 = int(round(x)) - int(self.noise[1].get())//2, int(round(x)) + int(self.noise[1].get())//2
                y1, y2 = int(round(y)) - int(self.noise[2].get())//2, int(round(y)) + int(self.noise[2].get())//2
                self.removed_intensity = int(np.mean(self.datastack.intensity[y1:y2, x1:x2]) / self.stack.nangle * float(self.noise[0].get()))
                self.intensity_removal_label.configure(text=f'Removed intensity value = {self.removed_intensity}')
                canvas.mpl_disconnect(self.__cid1)
                canvas.mpl_disconnect(self.__cid2)
                for line in hlines:
                    line.remove()
                canvas.draw()

    def compute_angle(self) -> None:
        if hasattr(self, 'stack'):
            self.intensity_pyfig.toolbar.mode = _Mode.NONE
            self.intensity_pyfig.toolbar._update_buttons_checked()
            self.tabview.set('Intensity')
            self.compute_angle_button.configure(fg_color=orange[1])
            hroi = ROI()
            self.__cid1 = self.intensity_pyfig.canvas.mpl_connect('motion_notify_event', lambda event: self.compute_angle_motion_notify_callback(event, hroi))
            self.__cid2 = self.intensity_pyfig.canvas.mpl_connect('button_press_event', lambda event: self.compute_angle_button_press_callback(event, hroi))

    def compute_angle_motion_notify_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.intensity_axis:
            x, y = event.xdata, event.ydata
            if ((event.button is None or event.button == 1) and roi.lines):
                roi.lines[-1].set_data([roi.previous_point[0], x], [roi.previous_point[1], y])
                self.intensity_pyfig.canvas.draw()

    def compute_angle_button_press_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.intensity_axis:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                if not roi.lines:
                    roi.lines = [plt.Line2D([x, x], [y, y], lw=3, color='w')]
                    roi.start_point = [x, y]
                    roi.previous_point = roi.start_point
                    self.intensity_axis.add_line(roi.lines[0])
                    self.intensity_pyfig.canvas.draw()
                else:
                    roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], lw=3, color='w')]
                    roi.previous_point = [x, y]
                    self.intensity_axis.add_line(roi.lines[-1])
                    self.intensity_pyfig.canvas.draw()
                    self.intensity_pyfig.canvas.mpl_disconnect(self.__cid1)
                    self.intensity_pyfig.canvas.mpl_disconnect(self.__cid2)
                    slope = 180 - np.rad2deg(np.arctan((roi.previous_point[1] - roi.start_point[1]) / (roi.previous_point[0] - roi.start_point[0])))
                    slope = np.mod(2 * slope, 360) / 2
                    dist = np.sqrt(((np.asarray(roi.previous_point) - np.asarray(roi.start_point))**2).sum())
                    message = ' Angle is {:.1f}\u00b0 \n Distance is {} pixels'.format(slope, int(dist))
                    if int(self.pixel_size.get()) != 0:
                        message += ' \n Distance is {:.1f} \xb5m'.format(int(dist) * int(self.pixel_size.get()) / 1000)
                    ShowInfo(message=message, image=self.icons['square'], button_labels = ['OK'], fontsize=14)
                    for line in roi.lines:
                        line.remove()
                    self.intensity_pyfig.canvas.draw()
                    self.compute_angle_button.configure(fg_color=orange[0])

    def define_variable_table(self, method:str) -> None:
        self.initialize_tables()
        self.clear_frame(self.variable_table_frame)
        self.variable_table_frame.configure(fg_color=gray[0])
        Label(master=self.variable_table_frame, text='Variables\n', width=250, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=4, padx=(20, 20), pady=(10, 0))
        self.variable_table_switch = CTk.CTkSwitch(master=self.variable_table_frame, text='', command=self.variable_table_switch_callback, onvalue='on', offvalue='off', width=50)
        self.variable_table_switch.grid(row=1, column=0, padx=(20, 0), sticky='w')
        labels = ['Min', 'Max']
        for _, label in enumerate(labels):
            Label(master=self.variable_table_frame, text=label, text_color=text_color, font=CTk.CTkFont(weight='bold')).grid(row=1, column=_+2, padx=(0, 40), pady=(0, 5), sticky='e')
        if method in ['1PF', '4POLAR 2D']:
            variables = ['\u03C1', '\u03C8']
            vals = [(0, 180), (40, 180)]
        elif method in ['CARS', 'SRS', '2PF']:
            variables = ['\u03C1', 'S2', 'S4']
            vals = [(0, 180), (0, 1), (-1, 1)]
        elif method == 'SHG':
            variables = ['\u03C1', 'S']
            vals = [(0, 180), (-1, 1)]
        elif method == '4POLAR 3D':
            variables = ['\u03C1', '\u03C8', '\u03B7']
            vals = [(0, 180), (40, 180), (0, 90)]
        self.variable_entries = []
        self.variable_min = [CTk.StringVar() for _ in range(len(variables))]
        self.variable_max = [CTk.StringVar() for _ in range(len(variables))]
        self.variable_display = [CTk.IntVar(value=0) for _ in range(len(variables))]
        for _, (var, val) in enumerate(zip(variables, vals)):
            self.variable_min[_].set(str(val[0]))
            self.variable_max[_].set(str(val[1]))
            CTk.CTkCheckBox(master=self.variable_table_frame, text=None, variable=self.variable_display[_], width=30).grid(row=_+2, column=0, padx=(20, 0), sticky='w')
            Label(master=self.variable_table_frame, text=var).grid(row=_+2, column=1, sticky='w')
            self.variable_entries += [Entry(self.variable_table_frame, textvariable=self.variable_min[_], row=_+2, column=2, state='disabled'), Entry(self.variable_table_frame, textvariable=self.variable_max[_], row=_+2, column=3, state='disabled')]
        Label(master=self.variable_table_frame, text=' ', height=5, width=10).grid(row=len(variables)+2, column=0, columnspan=4)

    def method_dropdown_callback(self, method:str) -> None:
        self.define_variable_table(method)
        self.CD = Calibration(method)
        self.calib_dropdown.configure(values=self.CD.list(method), state='normal')
        self.calib_dropdown.set(self.CD.list(method)[0])
        self.calib_textbox.write(self.CD.name)
        if method in ['2PF', 'SRS', 'SHG', 'CARS']:
            self.calib_dropdown.configure(state='disabled')
        if method.startswith('4POLAR'):
            self.polar_dropdown.configure(state='normal')
            window = ShowInfo(message='\n Perform: Select a beads file (*.tif)\n\n Load: Select a registration file (*.pyreg)\n\n Registration is performed with Whitelight.tif \n   which should be in the same folder as the beads file', image=self.icons['blur_circular'], button_labels=['Perform', 'Load', 'Cancel'], geometry=(420, 240))
            buttons = window.get_buttons()
            self.contrastThreshold = 0.04
            self.sigma = 1.6
            buttons[0].configure(command=lambda:self.perform_registration(window))
            buttons[1].configure(command=lambda:self.load_registration(window))
            buttons[2].configure(command=lambda:window.withdraw())
        else:
            self.polar_dropdown.configure(state='disabled')

    def pixelsperstick_spinbox_callback(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (fig.type == 'Sticks') and (self.datastack.name in fs):
                ax = fig.axes[0]
                for _, var in enumerate(self.datastack.vars):
                    if (var.name == fig.var) and ('contour' not in fs):
                        for collection in ax.collections:
                            collection.remove()
                        p = self.get_sticks(var, self.datastack)
                        vmin, vmax = self.get_variable(_)[1:]
                        p.set_clim([vmin, vmax])
                        ax.add_collection(p)
            if (fig.type == 'Sticks') and (fig.var in ['Rho_contour', 'Rho_angle']) and (self.datastack.name in fs):
                ax = fig.axes[0]
                for collection in ax.collections:
                    collection.remove()
                p = self.get_sticks(self.datastack.added_vars[-1], self.datastack)
                vmin, vmax = self.get_variable(0)[1:]
                p.set_clim([vmin, vmax])
                ax.add_collection(p)

    def perform_registration(self, window:CTk.CTkToplevel) -> None:
        window.withdraw()
        npix = 5
        initialdir = self.stack.folder if hasattr(self, 'stack') else Path.home()
        file = Path(fd.askopenfilename(title='Select a beads file', initialdir=initialdir, filetypes=[('TIFF files', '*.tiff'), ('TIF files', '*.tif')]))
        beadstack = self.define_stack(file)
        self.beads_name = beadstack.name
        self.filename_label.write('')
        dark = beadstack.compute_dark()
        intensity = np.sum((beadstack.values - dark) * (beadstack.values >= dark), axis=0)
        if Path(str(beadstack.folder / 'Whitelight.tif')).exists():
            whitelight = cv2.imread(str(beadstack.folder / 'Whitelight.tif'), cv2.IMREAD_GRAYSCALE) 
        elif Path(str(beadstack.folder / 'Whitelight.tiff')).exists():
            whitelight = cv2.imread(str(beadstack.folder / 'Whitelight.tiff'), cv2.IMREAD_GRAYSCALE)
        else:
            ShowInfo(' The file Whitelight.tif or Whitelight.tiff cannot be found\n See PyPOLAR wiki for more details', image=self.icons['blur_circular'], button_labels=['OK'], geometry=(420, 140))
            return
        whitelight = cv2.threshold(whitelight, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(whitelight, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        filter = np.asarray([len(contour) >= 200 for contour in contours])
        contours = [contour.reshape((-1, 2)) for (contour, val) in zip(contours, filter) if val]
        centers, radius = [None] * len(contours), [None] * len(contours)
        for _, contour in enumerate(contours):
            centers[_], radius[_] = cv2.minEnclosingCircle(contour)
        centers = np.asarray(centers, dtype=np.int32)
        beadstack.radius = int(round(max(radius))) + npix
        ind = np.arange(len(contours))
        Iul, Ilr = np.argmin(np.abs(centers[:, 0] + 1j * centers[:, 1])), np.argmax(np.abs(centers[:, 0] + 1j * centers[:, 1]))
        ind = np.delete(ind, [Iul, Ilr])
        Iur, Ill = np.argmin(centers[ind, 1]), np.argmax(centers[ind, 1])
        beadstack.centers = centers[[Iul, ind[Iur], Ilr, ind[Ill]], :]
        ims = []
        for _ in range(4):
            xi, yi = beadstack.centers[_, 0] - beadstack.radius, beadstack.centers[_, 1] - beadstack.radius
            xf, yf = beadstack.centers[_, 0] + beadstack.radius, beadstack.centers[_, 1] + beadstack.radius
            im = intensity[yi:yf, xi:xf]
            im = (im / np.amax(im) * 255).astype(np.uint8)
            thresh = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            ims += [im * thresh]
        self.compute_alignment(ims, beadstack)
        
    def compute_alignment(self, ims, beadstack):
        height, width = ims[0].shape
        sift=cv2.SIFT_create(contrastThreshold=self.contrastThreshold, sigma=self.sigma)
        keypoints0 = sift.detect(ims[0], None)
        points0 = np.unique(np.asarray([kp.pt for kp in keypoints0]), axis=0)
        try:
            homographies, ims_, mand, pcc = [], [ims[0]], [], []
            for im in ims[1:]:
                keypoints = sift.detect(im, None)
                points = np.unique(np.asarray([kp.pt for kp in keypoints]), axis=0)
                p, p0 = find_matches(points, points0)
                homography = cv2.findHomography(p, p0, cv2.RANSAC)[0]
                homographies += [homography]
                im_reg = cv2.warpPerspective(im, homography, (width, height))
                mand += [manders_coloc_coeff(im_reg, ims[0] > 0)]
                pcc += [pearson_corr_coeff(im_reg, ims[0])[0]]
                ims_ += [im_reg]
            reg_ims = [cv2.merge([_, ims[0], _]) for _ in ims_]
            fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)
            fig.type, fig.var = 'Calibration', None
            fig.canvas.manager.set_window_title('Quality of calibration: ' + beadstack.name)
            fig.suptitle(f'Manders = {np.amin(mand):.2f}   Pearson = {np.amin(pcc):.2f}   (for contrast = {self.contrastThreshold:.2f} and sigma = {self.sigma:.2f})', fontsize=10, x=0.45)
            reg_ims[2:4] = reg_ims[3:1:-1]
            titles = ['UL', 'UR', 'LL', 'LR']
            for im, title, ax in zip(reg_ims, titles, axs.ravel()):
                ax.imshow(im)
                ax.set_title(title)
                ax.set_axis_off()
            self.registration = {'name_beads': beadstack.name, 'radius': beadstack.radius, 'centers': beadstack.centers, 'homographies': homographies}
            message = " Are you okay with this registration?"
            state = "normal"
        except:
            message = " The registration was not successful. Try again."
            state = "disabled"
        window = ShowInfo(message=message, button_labels=['Validate', 'Save', 'Change', 'Cancel'], image=self.icons['blur_circular'], geometry=(480, 150))
        buttons = window.get_buttons()
        buttons[0].configure(command=lambda:self.validate_registration_callback(window), state=state)
        buttons[1].configure(command=lambda:self.save_registration_callback(window, beadstack.file), state=state)
        buttons[2].configure(command=lambda:self.change_registration_callback(window, ims, beadstack))
        buttons[3].configure(command=lambda:self.cancel_registration_callback(window))

    def validate_registration_callback(self, window:CTk.CTkToplevel) -> None:
        plt.close('all')
        window.withdraw()

    def save_registration_callback(self, window:CTk.CTkToplevel, file:Path) -> None:
        with file.with_suffix('.pyreg').open('wb') as f:
            joblib.dump(self.registration, f)
        self.validate_registration_callback(window)

    def change_registration_callback(self, window:CTk.CTkToplevel, ims, beadstack) -> None:
        self.registration = []
        window.withdraw()
        query_tooltips = ["The contrast threshold used to filter out weak features in semi-uniform (low-contrast) regions. The larger the threshold, the less features are produced by the detector.", "The sigma of the Gaussian applied to the input image at the octave #0. If your image is captured with a weak camera with soft lenses, you might want to reduce the number."]
        query_labels=["contrastThreshold", "sigma"]
        query_values=[self.contrastThreshold, self.sigma]
        button_labels=["Perform", "Cancel"]
        window = CTk.CTkToplevel(self)
        window.title('PyPOLAR')
        window.geometry(geometry_info((350, 200)))
        CTk.CTkLabel(window, text=" Enter new parameters for the registration", image=self.icons['blur_circular'], compound='left', width=250, justify=CTk.LEFT, font=CTk.CTkFont(size=13)).grid(row=0, column=0, padx=30, pady=10)
        buttons = []
        banner = CTk.CTkFrame(window, fg_color='transparent')
        banner.grid(row=1+len(query_labels), column=0)
        for _, label in enumerate(button_labels):
            button = Button(banner, text=label, width=80, anchor='center')
            button.grid(row=0, column=_, padx=20, pady=(20, 0))
            buttons += [button]
        self.query_vars = [CTk.StringVar(value=value) for value in query_values]
        for _, (label, tooltip) in enumerate(zip(query_labels, query_tooltips)):
            Entry(window, text=label, textvariable=self.query_vars[_], tooltip=tooltip, width=80, column=0, row=_+1, pady=(0, 10))
        buttons[0].configure(command=lambda:self.compute_changed_alignment(window, ims, beadstack))
        buttons[1].configure(command=lambda:self.cancel_registration_callback(window))

    def compute_changed_alignment(self, window:CTk.CTkToplevel, ims, beadstack) -> None:
        parameters = [var.get() for var in self.query_vars]
        window.withdraw()
        self.contrastThreshold, self.sigma = float(parameters[0]), float(parameters[1])
        self.compute_alignment(ims, beadstack)

    def cancel_registration_callback(self, window:CTk.CTkToplevel) -> None:
        self.registration = []
        self.method.set('1PF')
        self.validate_registration_callback(window)

    def load_registration(self, window:CTk.CTkToplevel) -> None:
        window.withdraw()
        initialdir = self.stack.folder if hasattr(self, 'stack') else Path.home()
        file = Path(fd.askopenfilename(title='Select a registration file (*.pyreg)', initialdir=initialdir, filetypes=[('PYREG-files', '*.pyreg')]))
        with file.open('rb') as f:
            self.registration = joblib.load(f)

    def define_stack(self, file:Path) -> Stack:
        stack_vals = cv2.imreadmulti(str(file), [], cv2.IMREAD_ANYDEPTH)[1]
        try:
            nangle, h, w = np.asarray(stack_vals).shape
        except:
            h, w = np.asarray(stack_vals).shape
        a = np.asarray(stack_vals)
        if not np.issubdtype(a.dtype, np.integer):
            stack_vals = (65535 * (a - np.amin(a)) / np.ptp(a)).astype(np.uint16)
        else:
            stack_vals = a
        dict = {'values': stack_vals, 'height': h, 'width': w, 'nangle': nangle, 'display': '{:.0f}'}
        stack = Stack(file)
        for key in dict:
            setattr(stack, key, dict[key])
        self.set_dark(stack)
        return stack

    def define_datastack(self, stack:Stack) -> DataStack:
        datastack = DataStack(stack)
        datastack.method = self.method.get()
        return datastack

    def open_file(self, file:Path) -> None:
        self.stack = self.define_stack(file)
        if self.method.get().startswith('4POLAR'):
            self.stack_unsliced = copy.deepcopy(self.stack)
            self.stack = self.slice4polar(self.stack_unsliced, self.polar_dropdown.get())
        if self.stack.nangle >= 2:
            self.stack_slider.configure(to=self.stack.nangle, number_of_steps=self.stack.nangle, state='normal')
        else:
            self.stack_slider.configure(state='disabled')
        self.filename_label.write(self.stack.name)
        self.tabview.set('Intensity')
        self.update()
        self.compute_intensity(self.stack)
        if self.option.get() != 'Thresholding (auto)': 
            self.ilow.set(self.stack.display.format(np.amin(self.stack.intensity)))
            self.ilow_slider.set(0)
        self.datastack = self.define_datastack(self.stack)
        if self.option.get().startswith('Mask'):
            self.mask = self.get_mask(self.datastack)
        self.ontab_intensity(update=False)
        self.ontab_thrsh(update=False)
        self.tabview.tab('Intensity').update()
        self.tabview.tab('Thresholding/Mask').update()

    def add_roi_callback(self) -> None:
        if hasattr(self, 'stack'):
            self.thrsh_pyfig.toolbar.mode = _Mode.NONE
            self.thrsh_pyfig.toolbar._update_buttons_checked()
            self.tabview.set('Thresholding/Mask')
            self.update()
            self.add_roi_button.configure(fg_color=orange[1])
            hroi = ROI()
            self.__cid1 = self.thrsh_pyfig.canvas.mpl_connect('motion_notify_event', lambda event: self.add_roi_motion_notify_callback(event, hroi))
            self.__cid2 = self.thrsh_pyfig.canvas.mpl_connect('button_press_event', lambda event: self.add_roi_button_press_callback(event, hroi))

    def add_roi_motion_notify_callback(self, event:MouseEvent, roi:ROI) -> None:
        self.thrsh_pyfig.toolbar.mode = _Mode.NONE
        self.thrsh_pyfig.toolbar._update_buttons_checked()
        if event.inaxes == self.thrsh_axis:
            x, y = event.xdata, event.ydata
            if (event.button is None or event.button == 1) and roi.lines:
                roi.lines[-1].set_data([roi.previous_point[0], x], [roi.previous_point[1], y])
                self.thrsh_pyfig.canvas.draw()
            elif event.button == 3 and roi.lines:
                roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], color='w')]
                roi.previous_point = [x, y]
                roi.x.append(x)
                roi.y.append(y)
                self.thrsh_axis.add_line(roi.lines[-1])
                self.thrsh_pyfig.canvas.draw()

    def add_roi_button_press_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.thrsh_axis:
            x, y = event.xdata, event.ydata
            if (event.button == 1 or event.button == 3) and not event.dblclick:
                if not roi.lines:
                    roi.lines = [plt.Line2D([x, x], [y, y], marker='o', color='w')]
                    roi.start_point = [x, y]
                    roi.previous_point = roi.start_point
                    roi.x, roi.y = [x], [y]
                    self.thrsh_axis.add_line(roi.lines[0])
                    self.thrsh_pyfig.canvas.draw()
                else:
                    roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], marker='o', color='w')]
                    roi.previous_point = [x, y]
                    roi.x.append(x)
                    roi.y.append(y)
                    self.thrsh_axis.add_line(roi.lines[-1])
                    self.thrsh_pyfig.canvas.draw()
            elif ((event.button == 1 or event.button == 3) and event.dblclick) and roi.lines:
                roi.lines += [plt.Line2D([roi.previous_point[0], roi.start_point[0]], [roi.previous_point[1], roi.start_point[1]], marker='o', color='w')]
                self.thrsh_axis.add_line(roi.lines[-1])     
                window = ShowInfo(message=' Add ROI?', image=self.icons['roi'], button_labels=['Yes', 'No'], fontsize=16)
                buttons = window.get_buttons()
                buttons[0].configure(command=lambda:self.yes_add_roi_callback(window, roi))
                buttons[1].configure(command=lambda:self.no_add_roi_callback(window, roi))
                self.add_roi_button.configure(fg_color=orange[0])
                self.thrsh_pyfig.canvas.draw()
                self.thrsh_pyfig.canvas.mpl_disconnect(self.__cid1)
                self.thrsh_pyfig.canvas.mpl_disconnect(self.__cid2)

    def yes_add_roi_callback(self, window:CTk.CTkToplevel, roi:ROI) -> None:
        vertices = np.asarray([roi.x, roi.y])
        indx = self.datastack.rois[-1]['indx'] + 1 if self.datastack.rois else 1
        self.datastack.rois += [{'indx': indx, 'label': (roi.x[0], roi.y[0]), 'vertices': vertices, 'ILow': self.ilow.get(), 'name': '', 'group': '', 'select': True}]
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_pyfig.canvas.draw()
        self.ontab_intensity()
        self.ontab_thrsh()
        if hasattr(self, 'manager'):
            self.manager.update_manager(self.datastack.rois)

    def no_add_roi_callback(self, window:CTk.CTkToplevel, roi:ROI) -> None:
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_pyfig.canvas.draw()

    def get_mask(self, datastack:DataStack) -> np.ndarray:
        mask = np.ones((datastack.height, datastack.width))
        if self.option.get().startswith('Mask'):
            maskfile = self.maskfolder / (datastack.name + '.png')
            if maskfile.exists():
                im_binarized = np.asarray(Image.open(maskfile), dtype=np.float64)
                mask = im_binarized / np.amax(im_binarized)
            else:
                ShowInfo(message=f' The corresponding mask for {datastack.name} could not be found\n Continuing without mask...', image=self.icons['layers_clear'], buttons_labels=['OK'])
            if hasattr(self, 'mask'):
                self.mask = mask
        return mask

    def analysis_callback(self) -> None:
        if hasattr(self, 'stack'):
            self.analysis_button.configure(image=self.icons['pause'])
            self.tabview.set('Intensity')
            self.update()
            if self.option.get().endswith('(manual)'):
                self.analyze_stack(self.datastack)
                if self.filelist:
                    self.indxlist += 1
                    if self.indxlist < len(self.filelist):
                        self.open_file(self.filelist[self.indxlist])
                        self.initialize_noise()
                    else:
                        self.indxlist = 0
                        self.open_file(self.filelist[0])
                        ShowInfo(message=' End of list', image=self.icons['check_circle'], button_labels=['OK'], fontsize=16)
                        self.initialize()
                self.analysis_button.configure(image=self.icons['play'])
            elif self.option.get().endswith('(auto)'):
                for file in self.filelist:
                    self.open_file(file)
                    self.analyze_stack(self.datastack)
                self.analysis_button.configure(image=self.icons['play'])
                self.open_file(self.filelist[0])
                ShowInfo(message=' End of list', image=self.icons['check_circle'], button_labels=['OK'], fontsize=16)
                self.initialize()

    def stack_slider_callback(self, value:str) -> None:
        self.stack_slider_label.configure(text=int(value))
        if value == 0:
            self.stack_slider_label.configure(text='T')
        if self.method.get().startswith('4POLAR'):
            labels = ['T', 0, 45, 90, 135]
            self.stack_slider_label.configure(text=labels[int(value)])
        self.ontab_intensity()

    def ilow_slider_callback(self, value:str) -> None:
        if hasattr(self, 'datastack'):
            self.ilow.set(self.stack.display.format(float(value) * float(np.ptp(self.datastack.intensity)) + self.datastack.intensity.min()))
            if hasattr(self, 'edge_contours'):
                self.compute_edges()
            self.ontab_thrsh()

    def ilow2slider_callback(self, event:tkEvent) -> None:
        if event and hasattr(self, 'datastack'):
            self.ilow_slider.set(float(self.ilow.get()) / float(np.amax(self.datastack.intensity)))
            if hasattr(self, 'edge_contours'):
                self.compute_edges()
            self.ontab_thrsh()

    def intensity_callback(self, event:tkEvent) -> None:
        if event and hasattr(self, 'stack'):
            if (self.method.get() == '1PF') and (float(self.dark.get()) < 480):
                self.dark.set(self.stack.display.format(self.calculated_dark))
            self.compute_intensity(self.stack)
            if hasattr(self, 'datastack'):
                self.datastack.intensity = self.stack.intensity
                self.ilow.set(self.stack.display.format(float(self.ilow_slider.get()) * float(np.ptp(self.datastack.intensity)) + self.datastack.intensity.min()))
            self.ontab_intensity(update=False)
            self.ontab_thrsh(update=False)

    def rotation_callback(self, event:tkEvent) -> None:
        if event:
            self.ontab_intensity(update=False)

    def rotation1_callback(self, event:tkEvent) -> None:
        if event:
            self.rotation[2].set('0')
            self.ontab_intensity(update=False)

    def transparency_slider_callback(self, value:float) -> None:
        self.transparency_slider.set(0.001 if value <= 0.001 else value)
        self.ontab_thrsh()

    def ontab_intensity(self, update:bool=True) -> None:
        intensity = self.stack.intensity if hasattr(self, 'stack') else self.datastack.intensity if hasattr(self, 'datastack') else []
        if hasattr(self, 'stack') or hasattr(self, 'datastack'):
            if self.stack_slider.get() == 0:
                field = intensity
                vmin, vmax = np.amin(intensity), np.amax(intensity)
            elif hasattr(self, 'stack') and (self.stack_slider.get() <= self.stack.nangle):
                field = self.stack.values[int(self.stack_slider.get())-1]
                vmin, vmax = np.amin(self.stack.values), np.amax(self.stack.values)
            field_im = adjust(field, float(self.contrast_intensity_slider.get()), vmin, vmax)
            if int(self.rotation[1].get()) != 0:
                field_im = rotate(field_im, int(self.rotation[1].get()), reshape=False, mode='constant', cval=vmin)
            if update:
                self.intensity_im.set_data(field_im)
            else:
                self.intensity_axis.clear()
                self.intensity_axis.set_axis_off()
                self.intensity_im = self.intensity_axis.imshow(field_im, cmap='gray', interpolation='nearest')
                self.tabview.tab('Intensity').update()
            self.intensity_im.set_clim(vmin, vmax)
            self.clear_patches(self.intensity_axis, self.intensity_pyfig.canvas)
            if hasattr(self, 'datastack'):
                self.add_patches(self.datastack, self.intensity_axis, self.intensity_pyfig.canvas)
            self.intensity_pyfig.canvas.draw()

    def ontab_thrsh(self, update:bool=True) -> None:
        if hasattr(self, 'stack'):
            field = self.stack.intensity.copy()
            if self.option.get().startswith('Mask'):
                field *= self.mask
            vmin, vmax = np.amin(self.stack.intensity), np.amax(self.stack.intensity)
            field_im = adjust(self.stack.intensity, self.contrast_thrsh_slider.get(), vmin, vmax)
            alphadata = np.ones(field.shape)
            thrsh = float(self.ilow.get())
            alphadata[field <= thrsh] *= self.transparency_slider.get()
            if update:
                plt.setp(self.thrsh_im, alpha=alphadata, cmap=self.thrsh_colormap)
                self.thrsh_im.set_data(field_im)
            else:
                self.thrsh_axis.clear()
                self.thrsh_axis.set_axis_off()
                self.thrsh_im = self.thrsh_axis.imshow(field_im, cmap=self.thrsh_colormap, alpha=alphadata, interpolation='nearest')
                self.tabview.tab('Thresholding/Mask').update()
            self.thrsh_im.set_clim(vmin, vmax)
            self.clear_patches(self.thrsh_axis, self.thrsh_fig.canvas)
            if hasattr(self, 'plot_edges'):
                for edge in self.plot_edges:
                    edge.pop(0).remove()
                delattr(self, 'plot_edges')
            if hasattr(self, 'datastack'):
                self.add_patches(self.datastack, self.thrsh_axis, self.thrsh_fig.canvas, rotation=False)
            if hasattr(self, 'edge_contours'):
                self.plot_edges = []
                for contour in self.edge_contours:
                    self.plot_edges += [self.thrsh_axis.plot(contour[:, 0], contour[:, 1], '-', color=blue[0], lw=1)]
            self.thrsh_pyfig.canvas.draw()

    def compute_intensity(self, stack:Stack) -> None:
        dark = float(self.dark.get())
        bin = [self.bin_spinboxes[_].get() for _ in range(2)]
        stack.intensity = stack.get_intensity(dark=dark, bin=bin)

    def set_dark(self, stack:Stack) -> int:
        dark = stack.compute_dark()
        self.calculated_dark = dark
        self.calculated_dark_label.configure(text='Calculated dark value = ' + stack.display.format(dark))
        if self.dark_switch.get() == 'off':
            self.dark.set(stack.display.format(dark))

    def get_variable(self, indx:int) -> Tuple[bool, float, float]:
        display = self.variable_display[indx].get()
        vmin, vmax = float(self.variable_min[indx].get()), float(self.variable_max[indx].get())
        return display, vmin, vmax
    
    def save_fig(self, fig, file:str) -> None:
        if self.figure_extension.get() in ['.pdf', '.png', '.jpeg', '.tif']:
            plt.savefig(file, bbox_inches='tight')
        elif self.figure_extension.get() == '.pyfig':
            pickle.dump(fig, open(file, 'wb'))

    def plot_histo(self, var:Variable, datastack:DataStack, roi_map:np.ndarray, roi:ROI=None) -> None:
        display, vmin, vmax = self.get_variable(var.indx % 10)
        if display and (self.show_table[2].get() or self.save_table[2].get()):
            for htype in var.type_histo:
                fig = plt.figure(figsize=self.figsize)
                fig.type, fig.var = 'Histogram', var.name
                suffix = 'for ROI ' + str(roi['indx']) if roi is not None else ''
                fig.canvas.manager.set_window_title(var.name + ' Histogram ' + suffix + ': ' + self.datastack.name)
                mask = (roi_map == roi['indx']) if roi is not None else (roi_map == 1)
                var.histo(mask, htype=htype, vmin=vmin, vmax=vmax, colorblind=self.colorblind_checkbox.get(), rotation=float(self.rotation[1].get()), nbins=int(self.histo_nbins.get()))
                fig.axes[0].tick_params(labelcolor='k' if self.add_axes_checkbox.get() else 'w')
                if self.save_table[2].get():
                    suffix = '_perROI_' + str(roi['indx']) if roi is not None else ''
                    histo = '(0-90)' if htype == 'polar3' else ''
                    file = datastack.file.with_name(datastack.name + '_Histo' + histo + var.name + suffix + self.figure_extension.get())
                    self.save_fig(fig, file)
                if not self.show_table[2].get():
                    plt.close(fig)

    def plot_histos(self, var:Variable, datastack:DataStack, roi_map:np.ndarray=None) -> None:
        if self.per_roi.get():
            for roi in datastack.rois:
                if roi['select']:
                    self.plot_histo(var, datastack, roi_map, roi=roi)
        else:
            self.plot_histo(var, datastack, roi_map)

    def merge_histos(self):
        self.show_table[2].select()
        initialdir = self.stack.folder if hasattr(self, 'stack') else Path.home()
        folder = Path(fd.askdirectory(title='Select a directory', initialdir=initialdir))
        goodvars = ['Rho', 'Rho_contour', 'Rho_angle', 'Psi', 'S2', 'S4', 'S_SHG', 'Eta', 'Int']
        data, vars = {}, []
        if folder.exists():
            for file in folder.glob('*.mat'):
                tempdata = loadmat(str(file))
                tempvars = list(tempdata.keys())
                tempvars = [tempvar for tempvar in tempvars if tempvar in goodvars]
                for tempvar in tempvars:
                    if (tempvar in vars):
                        data[tempvar] = np.concatenate((data[tempvar], tempdata[tempvar]), axis=None)
                    else:
                        vars += [tempvar]
                        data[tempvar] = tempdata[tempvar]
            if self.extension_table[0].get():
                dict_ = {'polarimetry': self.method.get(), 'folder': str(folder)}
                for var in vars:
                    dict_.update({var: data[var]})
                file = folder / (folder.stem + '_ConcatHisto.mat')
                savemat(str(file), dict_)
            vars.remove('Int')
            for var in vars:
                var_ = Variable(var, values=data[var])
                display, vmin, vmax = self.get_variable(var_.indx % 10)
                if display:
                    for htype in var_.type_histo:
                        fig = plt.figure(figsize=self.figsize)
                        fig.type, fig.var = 'Histogram', var_.name
                        fig.canvas.manager.set_window_title(var_.name + ' Concatenated Histogram ')
                        var_.histo(htype=htype, vmin=vmin, vmax=vmax, colorblind=self.colorblind_checkbox.get(), rotation=float(self.rotation[1].get()), nbins=int(self.histo_nbins.get()))
                        if self.save_table[2].get():
                            suffix = '(0-90)' if htype == 'polar3' else ''
                            file = folder / (folder.stem + '_ConcatHisto' + suffix + var_.name  + self.figure_extension.get()) 
                            self.save_fig(fig, file)
        if len(vars) == 0:
            ShowInfo(' Error in the selected folder', image=self.icons['blur_circular'], button_labels=['OK'])

    def add_intensity(self, intensity:np.ndarray, ax:plt.Axes) -> None:
        vmin, vmax = np.amin(intensity), np.amax(intensity)
        field = adjust(intensity, self.contrast_intensity_slider.get(), vmin, vmax)
        if int(self.rotation[1].get()) != 0:
            field = rotate(field, int(self.rotation[1].get()), reshape=False, mode='constant', cval=vmin)
        ax.imshow(field, cmap='gray', interpolation='nearest', vmin=vmin, vmax=vmax)

    def add_patches(self, datastack:DataStack, ax:plt.Axes, canvas:Union[FigureCanvasBase, FigureCanvasTkAgg], rotation:bool=True) -> None:
        if len(datastack.rois):
            for roi in datastack.rois:
                if roi['select']:
                    vertices = roi['vertices']
                    coord = roi['label'][0], roi['label'][1]
                    if (float(self.rotation[1].get()) != 0) and rotation:
                        theta = np.deg2rad(float(self.rotation[1].get()))
                        cosd, sind = np.cos(theta), np.sin(theta)
                        x0, y0 = datastack.width / 2, datastack.height / 2
                        coord = x0 + (coord[0] - x0) * cosd + (coord[1] - y0) * sind, y0 - (coord[0] - x0) * sind + (coord[1] - y0) * cosd
                        vertices = np.asarray([x0 + (vertices[0] - x0) * cosd + (vertices[1] - y0) * sind, y0 - (vertices[0] - x0) * sind + (vertices[1] - y0) * cosd])
                    ax.add_patch(Polygon(vertices.T, facecolor='none', edgecolor='white'))
                    ax.text(coord[0], coord[1], str(roi['indx']), color='w')
            canvas.draw()

    def plot_composite(self, var:Variable, datastack:DataStack) -> None:
        display, vmin, vmax = self.get_variable(var.indx % 10)
        if display and (self.show_table[0].get() or self.save_table[0].get()):
            fig = plt.figure(figsize=self.figsize)
            fig.type, fig.var, fig.width, fig.height = 'Composite', var.name, datastack.width, datastack.height
            fig.canvas.manager.set_window_title(var.name + ' Composite: ' + datastack.name)
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            datastack.plot_intensity(ax, contrast=self.contrast_intensity_slider.get(), rotation=int(self.rotation[1].get()))
            h = var.imshow(vmin, vmax, colorblind=self.colorblind_checkbox.get(), rotation=float(self.rotation[1].get()))
            if self.colorbar_checkbox.get():
                ax_divider = make_axes_locatable(ax)
                cax = ax_divider.append_axes('right', size='7%', pad='2%')
                fig.colorbar(h, cax=cax)
            if self.save_table[0].get():
                file = datastack.file.with_name(datastack.name + '_' + var.name + 'Composite' + self.figure_extension.get())
                self.save_fig(fig, file)
            if not self.show_table[0].get():
                plt.close(fig)

    def individual_fit_button_press_callback(self, event:MouseEvent, hlines:mpl.lines.Line2D, ax:plt.Axes, canvas:FigureCanvasBase) -> None:
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                if int(self.rotation[1].get()) != 0:
                    theta = np.deg2rad(float(self.rotation[1].get()))
                    x0, y0 = self.datastack.width / 2, self.datastack.height / 2
                    x, y = x0 + (x - x0) * np.cos(theta) - (y - y0) * np.sin(theta), y0 + (x - x0) * np.sin(theta) + (y - y0) * np.cos(theta)
                x, y = int(round(x)), int(round(y))
                if np.isfinite(self.datastack.vars[0].values[y, x]):
                    fig_, axs = plt.subplots(2, 1, figsize=(12, 8))
                    fig_.type, fig_.var = 'Individual Fit', None
                    fig_.canvas.manager.set_window_title('Individual Fit : ' + self.datastack.name)
                    signal = self.datastack.field[:, y, x]
                    signal_fit = self.datastack.field_fit[:, y, x]
                    indx = np.arange(1, self.stack.nangle + 1)
                    rho = np.mod(2 * (self.datastack.vars[0].values[y, x] + float(self.rotation[1].get())), 360) / 2
                    title = self.datastack.vars[0].latex + ' = ' + '{:.2f}'.format(rho) + ', '
                    for var in self.datastack.vars:
                        if var.name != 'Rho':
                            title += var.latex + ' = ' + '{:.2f}'.format(var.values[y, x]) + ', '
                    titles = [title[:-2]]
                    titles += ['$\chi_2$ = ' + '{:.2f}'.format(self.datastack.chi2[y, x]) + ',   $I$ =  ' + self.datastack.display.format(self.datastack.intensity[y, x])]
                    ylabels = ['counts', 'residuals']
                    axs[0].plot(indx, signal, '*', indx, signal_fit, 'r-', lw=2)
                    axs[1].plot(indx, signal - signal_fit, '+', indx, 2 * np.sqrt(signal_fit), 'r-', indx, -2 * np.sqrt(signal_fit), 'r-', lw=2)
                    polardir = -1 if self.polar_dir.get() == 'clockwise' else 1 
                    def indx2alpha(k):
                        return polardir * 180 / self.stack.nangle * (k - 1) + float(self.offset_angle.get())
                    def alpha2indx(a):
                        return polardir * self.stack.nangle / 180 * (a - float(self.offset_angle.get())) + 1
                    for title, ylabel, ax_ in zip(titles, ylabels, axs):
                        ax_.set_xlabel('slice', fontsize=14)
                        ax_.set_ylabel(ylabel, fontsize=14)
                        ax_.set_xlim((1, self.datastack.nangle))
                        ax_.set_xticks(indx[::2], minor=True)
                        ax_.set_title(title, fontsize=16)
                        secax = ax_.secondary_xaxis('top', functions=(indx2alpha, alpha2indx))
                        secax.set_xlabel(r'$\alpha$')
                    plt.subplots_adjust(hspace=0.9)
            canvas.mpl_disconnect(self.__cid1)
            canvas.mpl_disconnect(self.__cid2)
            for line in hlines:
                line.remove()
            canvas.draw()

    def get_sticks(self, var:Variable, datastack:DataStack) -> PolyCollection:
        L, W = 6, 0.2
        l, w = L / 2, W / 2
        rho = datastack.vars[0]
        rho_ = rho.values[::int(self.pixelsperstick_spinboxes[1].get()), ::int(self.pixelsperstick_spinboxes[0].get())]
        data_ = var.values[::int(self.pixelsperstick_spinboxes[1].get()), ::int(self.pixelsperstick_spinboxes[0].get())]
        Y, X = np.mgrid[:datastack.height:int(self.pixelsperstick_spinboxes[1].get()), :datastack.width:int(self.pixelsperstick_spinboxes[0].get())]
        X, Y = X[np.isfinite(data_)], Y[np.isfinite(data_)]
        data_, rho_ = data_[np.isfinite(data_)], rho_[np.isfinite(data_)]
        stick_colors = np.mod(2 * (data_ + float(self.rotation[1].get())), 360) / 2 if var.name in ['Rho', 'Rho_angle'] else data_
        cosd, sind = np.cos(np.deg2rad(rho_)), np.sin(np.deg2rad(rho_))
        vertices = np.array([[X + l * cosd + w * sind, X - l * cosd + w * sind, X - l * cosd - w * sind, X + l * cosd - w * sind], [Y - l * sind + w * cosd, Y + l * sind + w * cosd, Y + l * sind - w * cosd, Y - l * sind - w * cosd]])
        if float(self.rotation[1].get()) != 0:
            theta = np.deg2rad(float(self.rotation[1].get()))
            cosd, sind = np.cos(theta), np.sin(theta)
            x0, y0 = self.stack.width / 2, self.stack.height / 2
            vertices = np.asarray([x0 + (vertices[0] - x0) * cosd + (vertices[1] - y0) * sind, y0 - (vertices[0] - x0) * sind + (vertices[1] - y0) * cosd])
        vertices = np.swapaxes(vertices, 0, 2)
        return PolyCollection(vertices, cmap=var.colormap[self.colorblind_checkbox.get()], lw=2, array=stick_colors)

    def plot_sticks(self, var:Variable, datastack:DataStack) -> None:
        display, vmin, vmax = self.get_variable(var.indx % 10)
        if display and (self.show_table[1].get() or self.save_table[1].get()):
            fig = plt.figure(figsize=self.figsize)
            fig.type, fig.var, fig.width, fig.height = 'Sticks', var.name, datastack.width, datastack.height
            fig.canvas.manager.set_window_title(var.name + ' Sticks: ' + datastack.name)
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            datastack.plot_intensity(ax, contrast=self.contrast_intensity_slider.get(), rotation=int(self.rotation[1].get()))
            p = self.get_sticks(var, datastack)
            p.set_clim([vmin, vmax])
            ax.add_collection(p)
            if self.colorbar_checkbox.get():
                ax_divider = make_axes_locatable(ax)
                cax = ax_divider.append_axes('right', size='7%', pad='2%')
                fig.colorbar(p, cax=cax)
            if self.save_table[1].get():
                file = datastack.file.with_name(datastack.name + '_' + var.name + 'Sticks' + self.figure_extension.get())
                self.save_fig(fig, file)
            if not self.show_table[1].get():
                plt.close(fig)

    def plot_intensity(self, datastack:DataStack) -> None:
        if self.show_table[3].get() or self.save_table[3].get():
            fig = plt.figure(figsize=self.figsize)
            fig.type, fig.var, fig.width, fig.height = 'Intensity', None, datastack.width, datastack.height
            fig.canvas.manager.set_window_title('Intensity: ' + datastack.name)
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            p = datastack.plot_intensity(ax, contrast=self.contrast_intensity_slider.get(), rotation=int(self.rotation[1].get()))
            self.add_patches(datastack, ax, fig.canvas)
            if hasattr(self, 'edge_contours'):
                for contour in self.edge_contours:
                    angles = np.mod(2 * angle_edge(contour)[0], 360) / 2
                    cmap = m_colorwheel if self.colorblind_checkbox.get() else 'hsv'
                    if float(self.rotation[1].get()) != 0:
                        angles = np.mod(2 * (angles + float(self.rotation[1].get())), 360) / 2
                        theta = np.deg2rad(float(self.rotation[1].get()))
                        cosd, sind = np.cos(theta), np.sin(theta)
                        x0, y0 = self.stack.width / 2, self.stack.height / 2
                        contour = np.asarray([x0 + (contour[:, 0] - x0) * cosd + (contour[:, 1] - y0) * sind, y0 - (contour[:, 0] - x0) * sind + (contour[:, 1] - y0) * cosd])
                        contour = np.swapaxes(contour, 0, 1)
                    p = ax.scatter(contour[:, 0], contour[:, 1], c=angles, cmap=cmap, s=4, vmin=0, vmax=180)
            if self.colorbar_checkbox.get():
                ax_divider = make_axes_locatable(ax)
                cax = ax_divider.append_axes('right', size='7%', pad='2%')
                fig.colorbar(p, cax=cax)
                if not hasattr(self, 'edge_contours'):
                    fig.axes[1].remove()
            if self.save_table[3].get():
                file = datastack.file.with_name(datastack.name + '_Intensity' + self.figure_extension.get())
                self.save_fig(fig, file)
            if not self.show_table[3].get():
                plt.close(fig)
    
    def per_roi_callback(self):
        if hasattr(self, 'datastack'):
            if len(self.datastack.rois) >= 2:
                figs = list(map(plt.figure, plt.get_fignums()))
                redraw = False
                for fig in figs:
                    fs = fig.canvas.manager.get_window_title()
                    if (fig.type == 'Histogram') and (self.datastack.name in fs) :
                        plt.close(fig)
                        redraw = True
                if redraw:
                    roi_map = self.compute_roi_map(self.datastack)[0]
                    for var in self.datastack.vars:
                            self.plot_histos(var, self.datastack, roi_map)

    def plot_data(self, datastack:DataStack, roi_map:np.ndarray=None) -> None:
        self.plot_intensity(datastack)
        vars = copy.deepcopy(datastack.vars)
        if roi_map is None:
            roi_map, mask = self.compute_roi_map(datastack)
            for var in vars:
                var.values *= mask
                var.values[var.values==0] = np.nan
        for var in vars:
            self.plot_composite(var, datastack)
            self.plot_sticks(var, datastack)
            self.plot_histos(var, datastack, roi_map)

    def save_data(self, datastack:DataStack, roi_map:np.ndarray=[]) -> None:
        if len(roi_map) == 0:
            roi_map = self.compute_roi_map(datastack)[0]
        if self.per_roi.get():
            for roi in datastack.rois:
                if roi['select']:
                    self.save_mat(datastack, roi_map, roi=roi)
        else:
            self.save_mat(datastack, roi_map, roi=[])
        if self.extension_table[1].get():
            suffix = '_Stats.xlsx' if not hasattr(self, 'edge_contours') else '_Stats_c.xlsx'
            if self.filelist:
                file = self.stack.folder / (self.stack.folder.stem + suffix)
                title = self.stack.folder.stem
            else:
                file = self.stack.file.with_name(self.stack.name + suffix)
                title = self.stack.name
            if file.exists():
                workbook = openpyxl.load_workbook(file)
            else:
                workbook = openpyxl.Workbook()
            worksheet = workbook.active
            worksheet.title = title
            if not file.exists():
                title = ['File', 'ROI', 'name', 'group', 'MeanRho', 'StdRho', 'MeanDeltaRho']
                worksheet.append(title + self.return_vecexcel(datastack, roi_map)[1])
            if self.per_roi.get():
                for roi in datastack.rois:
                    if roi['select']:
                        worksheet.append(self.return_vecexcel(datastack, roi_map, roi=roi)[0])
            else:
                worksheet.append(self.return_vecexcel(datastack, roi_map, roi=[])[0])
            workbook.save(file)
        if self.extension_table[2].get():
            images = []
            vmin, vmax = np.amin(self.stack.values), np.amax(self.stack.values)
            for _ in range(self.stack.nangle):
                field = self.stack.values[_]
                im = adjust(field, self.contrast_intensity_slider.get(), vmin, vmax, sharpen=False)
                if int(self.rotation[1].get()) != 0:
                    im = rotate(im, int(self.rotation[1].get()), reshape=False, mode='constant', cval=vmin)
                if hasattr(self, 'xylim'):
                    im = im[int(self.xylim[2].get()):int(self.xylim[3].get()), int(self.xylim[0].get()):int(self.xylim[1].get())]
                im = (255 * im / vmax).astype(np.uint8)
                images.append(Image.fromarray(im, mode='P'))
            images[0].save(self.stack.file.with_suffix('.gif'), save_all=True, append_images=images[1:], optimize=False, duration=200, loop=0)

    def return_vecexcel(self, datastack:DataStack, roi_map:np.ndarray, roi:dict={}) -> Tuple[List[float], List[str]]:
        mask = (roi_map == roi['indx']) if roi else (roi_map == 1)
        ilow = float(roi['ILow']) if roi else float(self.ilow.get())
        rho = datastack.vars[0].values
        data_vals = np.mod(2 * (rho[mask * np.isfinite(rho)] + float(self.rotation[1].get())), 360) / 2
        n = data_vals.size
        meandata = circularmean(data_vals)
        deltarho = wrapto180(2 * (data_vals - meandata)) / 2
        title = []
        if roi:
            results = [self.stack.name, roi['indx'], roi['name'], roi['group'], meandata, np.std(deltarho), np.mean(deltarho)]
        else:
            results = [self.stack.name, 'all', '', '', meandata, np.std(deltarho), np.mean(deltarho)]
        if hasattr(self, 'edge_contours'):
            title += ['MeanRho_c_180', 'StdRho_c_180', 'MeanDeltaRho_c_180', 'MeanRho_c_90', 'StdRho_c_90', 'MeanDeltaRho_c_90']
            rho_c_180 = datastack.vars[-1].values
            rho_c_90 = rho_c_180.copy()
            rho_c_90[rho_c_90 >= 90] = 180 - rho_c_90[rho_c_90 >= 90]
            data_vals = rho_c_180[mask * np.isfinite(rho) * np.isfinite(rho_c_180)]
            meandata = circularmean(data_vals)
            deltarho = wrapto180(2 * (data_vals - meandata)) / 2
            results += [meandata, np.std(deltarho), np.mean(deltarho)]
            data_vals = rho_c_90[mask * np.isfinite(rho) * np.isfinite(rho_c_90)]
            meandata = circularmean(data_vals)
            deltarho = wrapto180(2 * (data_vals - meandata)) / 2
            results += [meandata, np.std(deltarho), np.mean(deltarho)]
        for var in datastack.vars[1:]:
            if var.name != 'Rho_contour':
                data_vals = var.values[mask * np.isfinite(rho)]
                meandata = np.mean(data_vals)
                title += ['Mean' + var.name, 'Std' + var.name]
                results += [meandata, np.std(data_vals)]
        data_vals = datastack.added_vars[2].values[mask * np.isfinite(rho)]
        meandata, stddata = np.mean(data_vals), np.std(data_vals)
        title += ['MeanInt', 'StdInt', 'TotalInt', 'ILow', 'N']
        results += [meandata, stddata, meandata * self.stack.nangle, ilow, n]
        if self.method.get() in ['1PF', '4POLAR 2D', '4POLAR 3D']:
            title += ['Calibration']
            results += [self.CD.name]
        if self.method.get().startswith('4POLAR'):
            title += ['4POLAR angles', 'beads', 'contrastThreshold', 'sigma']
            results += [self.polar_dropdown.get(), self.beads_name, self.contrastThreshold, self.sigma]
        title += ['dark', 'offset', 'polarization', 'bin width', 'bin height', 'reference angle']
        results += [float(self.dark.get()), float(self.offset_angle.get()), self.polar_dir.get(), self.bin_spinboxes[0].get(), self.bin_spinboxes[1].get(), float(self.rotation[2].get())]
        return results, title

    def save_mat(self, datastack:DataStack, roi_map:np.ndarray, roi:dict={}) -> None:
        if self.extension_table[0].get():
            mask = (roi_map == roi['indx']) if roi else (roi_map == 1)
            dict_ = {'polarimetry': self.method.get(), 'file': str(datastack.file), 'date': date.today().strftime('%B %d, %Y')}
            for var in datastack.vars:
                data = var.values[mask * np.isfinite(var.values)]
                dict_.update({var.name: data})
            for var in datastack.added_vars:
                data = var.values[mask * np.isfinite(var.values)]
                dict_.update({var.name: data})
            suffix = '_ROI' + str(roi['indx']) if roi else ''
            file = datastack.file.with_name(datastack.name + suffix + '.mat')
            savemat(file, dict_)

    def compute_roi_map(self, datastack:DataStack) -> Tuple[np.ndarray, np.ndarray]:
        shape = (datastack.height, datastack.width)
        if len(datastack.rois):
            Y, X = np.mgrid[:datastack.height, :datastack.width]
            points = np.vstack((X.flatten(), Y.flatten())).T
            roi_map = np.zeros(shape, dtype=np.int32)
            roi_ilow_map = np.zeros(shape, dtype=np.float64)
            for roi in datastack.rois:
                if roi['select']:
                    patch= Polygon(roi['vertices'].T)
                    roi_map[patch.contains_points(points).reshape(shape)] = int(roi['indx']) if self.per_roi.get() else 1
                    roi_ilow_map[patch.contains_points(points).reshape(shape)] = float(roi['ILow'])
        else:
            roi_map = np.ones(shape, dtype=np.int32)
            roi_ilow_map = np.ones(shape, dtype=np.float64) * np.float64(self.ilow.get())
            self.per_roi.deselect()
        mask = self.get_mask(datastack)
        mask *= (datastack.intensity >= roi_ilow_map) * (roi_map > 0)
        return roi_map, (mask != 0)

    def slice4polar(self, stack:Stack, str_order:str) -> Stack:
        if hasattr(self, 'registration'):
            radius = np.asarray(self.registration['radius']).item()
            centers = self.registration['centers']
            homographies = self.registration['homographies']
            stack_ = Stack(stack.file)
            stack_.display = stack.display
            stack_.nangle, stack_.height, stack_.width = 4, 2 * radius, 2 * radius
            stack_.values = np.zeros((stack_.nangle, stack_.height, stack_.width))
            ims = []
            for _ in range(stack_.nangle):
                xi, yi = centers[_, 0] - radius, centers[_, 1] - radius
                xf, yf = centers[_, 0] + radius, centers[_, 1] + radius
                xi, yi = max(1, xi), max(1, yi)
                xf, yf = min(stack.width, xf), min(stack.height, yf)
                ims += [stack.values[0, yi:yf, xi:xf].reshape((yf - yi, xf - xi))]
            ims_reg = [ims[0]]
            ims_reg += [cv2.warpPerspective(im, homography, (stack_.width, stack_.height)) for im, homography in zip(ims[1:], homographies)]
            order = self.dict_polar[str_order]
            for it in range(stack_.nangle):
                stack_.values[order[it]] = ims_reg[it]
            return stack_
        else:
            ShowInfo(message=' No registration', image=self.icons['blur_circular'], button_labels=['OK'], fontsize=16)
            self.method.set('1PF')

    def polar_dropdown_callback(self, order:str) -> None:
        if hasattr(self, 'stack') and hasattr(self, 'registration'):
            self.stack = self.slice4polar(self.stack_unsliced, order)
            self.compute_intensity(self.stack)
            self.datastack = self.define_datastack(self.stack)
            if self.option.get().startswith('Mask'):
                self.mask = self.get_mask(self.datastack)
            self.ontab_intensity(update=False)
            self.ontab_thrsh(update=False)

    def analyze_stack(self, datastack:DataStack) -> None:
        chi2threshold = 500
        shape = (self.stack.height, self.stack.width)
        roi_map, mask = self.compute_roi_map(datastack)
        datastack.dark = float(self.dark.get())
        datastack.method = self.method.get()
        field = self.stack.values - datastack.dark - float(self.removed_intensity)
        field *= (field >= 0)
        if self.method.get() == 'CARS':
            field = np.sqrt(field)
        elif self.method.get().startswith('4POLAR'):
            field[[1, 2]] = field[[2, 1]]
        bin_shape = np.asarray([self.bin_spinboxes[_].get() for _ in range(2)], dtype=np.uint8)
        if sum(bin_shape) != 2:
            bin = np.ones(bin_shape)
            for _ in range(self.stack.nangle):
                field[_] = convolve2d(field[_], bin, mode='same') / np.prod(bin_shape)
        if self.method.get() in ['1PF', 'CARS', 'SRS', 'SHG', '2PF']:
            polardir = -1 if self.polar_dir.get() == 'clockwise' else 1
            alpha = polardir * np.linspace(0, 180, self.stack.nangle, endpoint=False) + float(self.offset_angle.get())
            e2 = np.exp(2j * np.deg2rad(alpha[:, np.newaxis, np.newaxis]))
            a0 = np.mean(field, axis=0)
            a0[a0 == 0] = np.nan
            a2 = 2 * np.mean(field * e2, axis=0)
            field_fit = a0[np.newaxis] + (a2[np.newaxis] * e2.conj()).real
            a2 = divide_ext(a2, a0)
            if self.method.get() in ['CARS', 'SRS', 'SHG', '2PF']:
                e4 = e2**2
                a4 = 2 * np.mean(field * e4, axis=0)
                field_fit += (a4[np.newaxis] * e4.conj()).real
                a4 = divide_ext(a4, a0)
            chi2 = np.mean(np.divide((field - field_fit)**2, field_fit, where=np.all((field_fit!=0, np.isfinite(field_fit)), axis=0)), axis=0)
            mask *= (chi2 <= chi2threshold) * (chi2 > 0)
        elif self.method.get() == '4POLAR 3D':
            mat = np.einsum('ij,jmn->imn', self.CD.invKmat, field)
            s = mat[0] + mat[1] + mat[2]
            pxy = divide_ext(mat[0] - mat[1], s).reshape(shape)
            puv = divide_ext(2 * mat[3], s).reshape(shape)
            pzz = divide_ext(mat[2], s).reshape(shape)
            lam = ((1 - (pzz + np.sqrt(puv**2 + pxy**2))) / 2).reshape(shape)
            a0 = np.mean(field, axis=0) / 4
            a0[a0 == 0] = np.nan
        elif self.method.get() == '4POLAR 2D':
            mat = np.einsum('ij,jmn->imn', self.CD.invKmat, field)
            s = mat[0] + mat[1]
            pxy = divide_ext(mat[0] - mat[1], s).reshape(shape)
            puv = divide_ext(2 * mat[2], s).reshape(shape)
            p2d = np.sqrt(puv**2 + pxy**2)
            lam = (1 - p2d) / (3 - p2d)
            a0 = np.mean(field, axis=0) / 4
            a0[a0 == 0] = np.nan
        rho_ = Variable('Rho', datastack=datastack)
        if self.method.get() == '1PF':
            mask *= np.abs(a2) < 1
            a2_vals = np.moveaxis(np.asarray([a2.real[mask].flatten(), a2.imag[mask].flatten()]), 0, -1)
            rho, psi = np.moveaxis(interpn(self.CD.xy, self.CD.RhoPsi, a2_vals), 0, 1)
            ixgrid = mask.nonzero()
            rho_.values[ixgrid] = rho
            rho_.values[np.isfinite(rho_.values)] = np.mod(2 * (rho_.values[np.isfinite(rho_.values)] + float(self.rotation[0].get())), 360) / 2 
            psi_ = Variable('Psi', datastack=datastack)
            psi_.values[ixgrid] = psi
            mask *= np.isfinite(rho_.values) * np.isfinite(psi_.values)
            datastack.vars = [rho_, psi_]
        elif self.method.get() in ['CARS', 'SRS', '2PF']:
            mask *= (np.abs(a2) < 1) * (np.abs(a4) < 1)
            rho_.values[mask] = np.rad2deg(np.angle(a2[mask])) / 2
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            s2_ = Variable('S2', datastack=datastack)
            s2_.values[mask] = 1.5 * np.abs(a2[mask])
            s4_ = Variable('S4', datastack=datastack)
            s4_.values[mask] = 6 * np.abs(a4[mask]) * np.cos(4 * (0.25 * np.angle(a4[mask]) - np.deg2rad(rho_.values[mask])))
            datastack.vars = [rho_, s2_, s4_]
        elif self.method.get() == 'SHG':
            mask *= (np.abs(a2) < 1) * (np.abs(a4) < 1)
            rho_.values[mask] = np.rad2deg(np.angle(a2[mask])) / 2
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            s_shg_ = Variable('S_SHG', datastack=datastack)
            s_shg_.values[mask] = -0.5 * (np.abs(a4[mask]) - np.abs(a2[mask])) / (np.abs(a4[mask]) + np.abs(a2[mask])) - 0.65
            datastack.vars = [rho_, s_shg_]
        elif self.method.get() == '4POLAR 3D':
            mask *= (lam < 1/3) * (lam > 0) * (pzz > lam)
            rho_.values[mask] = 0.5 * np.rad2deg(np.arctan2(puv[mask], pxy[mask]))
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable('Psi', datastack=datastack)
            psi_.values[mask] = 2 * np.rad2deg(np.arccos((-1 + np.sqrt(9 - 24 * lam[mask])) / 2))
            eta_ = Variable('Eta', datastack=datastack)
            eta_.values[mask] = np.rad2deg(np.arccos(np.sqrt((pzz[mask] - lam[mask]) / (1 - 3 * lam[mask]))))
            datastack.vars = [rho_, psi_, eta_]
        elif self.method.get() == '4POLAR 2D':
            mask *= (lam < 3/8) * (lam > 0)
            rho_.values[mask] = 0.5 * np.rad2deg(np.arctan2(puv[mask], pxy[mask]))
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable('Psi', datastack=datastack)
            psi_.values[mask] = 2 * np.rad2deg(np.arccos((-1 + np.sqrt(9 - 24 * lam[mask])) / 2))
            datastack.vars = [rho_, psi_]
        a0[np.logical_not(mask)] = np.nan
        X, Y = np.meshgrid(np.arange(datastack.width), np.arange(datastack.height))
        X, Y = X.astype(np.float64), Y.astype(np.float64)
        X[np.logical_not(mask)] = np.nan
        Y[np.logical_not(mask)] = np.nan
        X_, Y_, Int_ = Variable('X', datastack=datastack), Variable('Y', datastack=datastack), Variable('Int', datastack=datastack)
        X_.indx, Y_.indx, Int_.indx = 1, 2, 3
        X_.values, Y_.values, Int_.values = X, Y, a0
        datastack.added_vars = [X_, Y_, Int_]
        if hasattr(self, 'edge_contours'):
            rho_ct = Variable('Rho_contour', datastack=datastack)
            vals = self.define_rho_ct(self.edge_contours)
            filter = np.isfinite(rho_.values) * np.isfinite(vals)
            rho_ct.values[filter] = np.mod(2 * (rho_.values[filter] - vals[filter]), 360) / 2
            datastack.vars += [rho_ct]
        if float(self.rotation[2].get()):
            rho_a = Variable('Rho_angle', datastack=datastack)
            rho_a.values = np.mod(2 * (rho_.values - float(self.rotation[2].get())), 360) / 2
            datastack.vars += [rho_a]
        if not self.method.get().startswith('4POLAR'):
            field[:, np.logical_not(mask)] = np.nan
            field_fit[:, np.logical_not(mask)] = np.nan
            chi2[np.logical_not(mask)] = np.nan
            datastack.field, datastack.field_fit, datastack.chi2 = field, field_fit, chi2
        self.datastack = datastack
        self.plot_data(datastack, roi_map=roi_map)
        self.save_data(datastack, roi_map=roi_map)

if __name__ == '__main__':
    app = Polarimetry()
    app.mainloop()