import tkinter as tk
from tkinter import filedialog as fd
import customtkinter as CTk
import os
import sys
import bz2
import pickle
import _pickle as cPickle
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
import colorcet as cc
from PIL import Image
import cv2
import openpyxl
from itertools import permutations, chain
from datetime import date
import copy
from typing import List, Tuple, Union
from pypolar_classes import Stack, DataStack, Variable, ROI, Calibration, NToolbar2PyPOLAR, ToolTip, ROIManager, TabView
from pypolar_classes import Button, CheckBox, Entry, DropDown, SpinBox, ShowInfo, TextBox
from pypolar_classes import adjust, circularmean, wrapto180, angle_edge, find_matches
from pypolar_classes import button_size, orange, gray, red, green, text_color, geometry_info

try:
    from ctypes import windll 
    myappid = "fr.cnrs.fresnel.pypolar"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

CTk.set_default_color_theme(os.path.join(os.path.dirname(os.path.realpath(__file__)), "polarimetry.json"))
CTk.set_appearance_mode("dark")
mpl.use("TkAgg")
plt.rcParams["font.size"] = 16
if sys.platform == "darwin":
    plt.rcParams["font.family"] = "Arial Rounded MT Bold"
elif sys.platform == "win32":
    plt.rcParams["font.family"] = "Arial Rounded MT"
plt.rcParams["image.origin"] = "upper"
plt.rcParams["figure.max_open_warning"] = 100
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.bbox"] = "tight"
plt.ion()

class Polarimetry(CTk.CTk):
    __version__ = "2.4.4"

    dict_versions = {"2.1": "December 5, 2022", "2.2": "January 22, 2023", "2.3": "January 28, 2023", "2.4": "February 2, 2023", "2.4.1": "February 25, 2023", "2.4.2": "March 2, 2023", "2.4.3": "March 13, 2023", "2.4.4": "March 16, 2023"}

    try:
        __version_date__ = dict_versions[__version__]
    except:
        __version_date__ = date.today().strftime("%B %d, %Y")    

    left_frame_width = 180
    right_frame_width = 850
    height = 850
    width = left_frame_width + right_frame_width
    tab_width = right_frame_width - 40
    tab_height = height - 20
    axes_size = (680, 680)
    figsize = (450, 450)

    url_github = "https://github.com/cchandre/Polarimetry"
    url_fresnel = "https://www.fresnel.fr/polarimetry"
    email = "cristel.chandre@cnrs.fr"

    def __init__(self) -> None:
        super().__init__()

## MAIN
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        delx, dely = self.winfo_screenwidth() // 10, self.winfo_screenheight() // 10
        dpi = self.winfo_fpixels("1i")
        self.figsize = (Polarimetry.figsize[0] / dpi, Polarimetry.figsize[1] / dpi)
        self.title("Polarimetry Analysis")
        self.geometry(f"{Polarimetry.width}x{Polarimetry.height}+{delx}+{dely}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand("tk::mac::Quit", self.on_closing)
        self.configure(fg_color=gray[0])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        image_path = os.path.join(self.base_dir, "icons")
        self.icons = {}
        for file in os.listdir(image_path):
            if file.endswith(".png"):
                im = Image.open(os.path.join(image_path, file))
                self.icons.update({os.path.splitext(file)[0]: CTk.CTkImage(dark_image=im, size=(30, 30))})
        if sys.platform == "win32":
            self.iconbitmap(os.path.join(self.base_dir, "main_icon.ico"))
            import winreg
            EXTS = [".pyroi", ".pyreg", ".pykl"]
            TYPES = ["PyPOLAR ROI", "PyPOLAR Registration", "PyPOLAR Pickle"]
            ICONS = ["pyrois.ico", "pyreg.ico", "pykl.ico"]
            try:
                for EXT, TYPE, ICON in zip(EXTS, TYPES, ICONS):
                    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, EXT)
                    winreg.SetValue(key, None, winreg.REG_SZ, TYPE)
                    iconkey = winreg.CreateKey(key, "DefaultIcon")
                    winreg.SetValue(iconkey, None, winreg.REG_SZ, os.path.join(image_path, ICON))
                    winreg.CloseKey(iconkey)
                    winreg.CloseKey(key)
            except WindowsError:
                pass

## DEFINE FRAMES
        self.left_frame = CTk.CTkFrame(master=self, width=Polarimetry.left_frame_width, corner_radius=0, fg_color=gray[0])
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.right_frame = CTk.CTkFrame(master=self, width=Polarimetry.right_frame_width)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.tabview = TabView(self.right_frame)

## LEFT FRAME
        logo = Button(self.left_frame, text=" PyPOLAR", image=self.icons["blur_circular"], command=self.on_click_tab)
        ToolTip(logo, text=" - select a polarimetry method\n - download a .tiff file or a folder or a previous analysis (.pykl)\n - select an option of analysis\n - select one or several regions of interest (ROI)\n - click on Analysis")
        logo.configure(hover=False, fg_color="transparent", font=CTk.CTkFont(size=20))
        logo.pack(padx=20, pady=(10, 40))
        self.method = tk.StringVar()
        dropdown = DropDown(self.left_frame, values=["1PF", "CARS", "SRS", "SHG", "2PF", "4POLAR 2D", "4POLAR 3D"], image=self.icons["microscope"], command=self.method_dropdown_callback, variable=self.method)
        ToolTip(dropdown, text=" - 1PF: one-photon fluorescence\n - CARS: coherent anti-Stokes Raman scattering\n - SRS: stimulated Raman scattering\n - SHG: second-harmonic generation\n - 2PF: two-photon fluorescence\n - 4POLAR 2D: 2D 4POLAR fluorescence (not yet implemented)\n - 4POLAR 3D: 3D 4POLAR fluorescence")
        self.openfile_dropdown = DropDown(self.left_frame, values=["Open file", "Open folder", "Previous analysis"], image=self.icons["download_file"], command=self.open_file_callback)
        self.option = tk.StringVar()
        self.options_dropdown = DropDown(self.left_frame, values=["Thresholding (manual)", "Mask (manual)"], image=self.icons["build"], variable=self.option, state="disabled", command=self.options_dropdown_callback)
        ToolTip(self.options_dropdown, text=" select the method of analysis\n - intensity thresholding or segmentation mask for single file analysis (manual) or batch processing (auto)\n - the mask has to be binary and in PNG format and have the same file name as the respective polarimetry data file")
        self.add_roi_button = Button(self.left_frame, text="Add ROI", image=self.icons["roi"], command=self.add_roi_callback)
        ToolTip(self.add_roi_button, text=" add a region of interest: polygon (left button), freehand (right button)")
        self.add_roi_button.pack(padx=20, pady=20)
        self.analysis_button = Button(self.left_frame, text="Analysis", command=self.analysis_callback, image=self.icons["play"])
        ToolTip(self.analysis_button, text=" perform polarimetry analysis")
        self.analysis_button.configure(fg_color=green[0], hover_color=green[1])
        self.analysis_button.pack(padx=20, pady=20)
        button = Button(self.left_frame, text="Close figures", command=lambda:plt.close("all"), image=self.icons["close"])
        ToolTip(button, text=" close all open figures")
        button.configure(fg_color=red[0], hover_color=red[1])
        button.pack(padx=20, pady=20)

## RIGHT FRAME: INTENSITY
        bottomframe = CTk.CTkFrame(master=self.tabview.tab("Intensity"), fg_color="transparent", height=40, width=Polarimetry.axes_size[1])
        bottomframe.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.intensity_frame = CTk.CTkFrame(master=self.tabview.tab("Intensity"), fg_color="transparent", height=Polarimetry.axes_size[0], width=Polarimetry.axes_size[1])
        self.intensity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.intensity_fig = Figure(figsize=(self.intensity_frame.winfo_width() / dpi, self.intensity_frame.winfo_height() / dpi), facecolor=gray[1])
        self.intensity_axis = self.intensity_fig.add_axes([0, 0, 1, 1])
        self.intensity_axis.set_axis_off()
        self.intensity_canvas = FigureCanvasTkAgg(self.intensity_fig, master=self.intensity_frame)
        background = plt.imread(os.path.join(image_path, "blur_circular-512.png"))
        self.intensity_axis.imshow(background, cmap="gray", interpolation="bicubic", alpha=0.1)
        self.intensity_canvas.draw()

        self.intensity_toolbar = NToolbar2PyPOLAR(canvas=self.intensity_canvas, window=self.intensity_frame)

        banner = CTk.CTkFrame(master=self.tabview.tab("Intensity"), fg_color="transparent", height=Polarimetry.axes_size[0], width=40)
        banner.pack(side=tk.RIGHT, fill=tk.Y)
        Button(banner, image=self.icons["contrast"], command=self.contrast_intensity_button_callback).pack(side=tk.TOP, padx=20, pady=(20, 0))
        self.contrast_intensity_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_intensity_slider_callback)
        self.contrast_intensity_slider.set(1)
        ToolTip(self.contrast_intensity_slider, text=" adjust contrast\n - the chosen contrast will be the one used\n for the intensity images in figures\n - the contrast changes the intensity value displayed in the navigation toolbar\n - the chosen contrast does not affect the analysis")
        self.contrast_intensity_slider.pack(padx=20, pady=(0, 20))
        self.compute_angle_button = Button(banner, image=self.icons["square"], command=self.compute_angle)
        ToolTip(self.compute_angle_button, text=" left click to trace a line segment\n and determine its length and angle")
        self.compute_angle_button.pack(padx=20, pady=20)

        self.filename_label = TextBox(master=bottomframe, width=400, height=50)
        ToolTip(self.filename_label, text=" name of file currently analyzed")
        self.filename_label.pack(side=tk.LEFT)
        sliderframe = CTk.CTkFrame(master=bottomframe, fg_color="transparent")
        sliderframe.pack(side=tk.RIGHT, padx=100)
        self.stack_slider = CTk.CTkSlider(master=sliderframe, from_=0, to=18, number_of_steps=18, command=self.stack_slider_callback, state="disabled")
        self.stack_slider.set(0)
        self.stack_slider.grid(row=0, column=0, columnspan=2)
        self.stack_slider_label = CTk.CTkLabel(master=sliderframe, text="T")
        ToolTip(self.stack_slider, text=" slider at T for the total intensity, otherwise scroll through the images of the stack")
        self.stack_slider_label.grid(row=1, column=0, sticky="w")
        CTk.CTkLabel(master=sliderframe, fg_color="transparent", text="Stack").grid(row=1, column=1, sticky="e")

## RIGHT FRAME: THRSH
        bottomframe = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", height=40, width=Polarimetry.axes_size[1])
        bottomframe.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.thrsh_frame = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", height=Polarimetry.axes_size[0], width=Polarimetry.axes_size[1])
        self.thrsh_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thrsh_axis_facecolor = gray[1]
        self.thrsh_fig = Figure(figsize=(self.thrsh_frame.winfo_width() / dpi, self.thrsh_frame.winfo_height() / dpi), facecolor=self.thrsh_axis_facecolor)
        self.thrsh_axis = self.thrsh_fig.add_axes([0, 0, 1, 1])
        self.thrsh_axis.set_axis_off()
        self.thrsh_axis.set_facecolor(self.thrsh_axis_facecolor)
        self.thrsh_canvas = FigureCanvasTkAgg(self.thrsh_fig, master=self.thrsh_frame)
        self.thrsh_axis.imshow(background, cmap="gray", interpolation="bicubic", alpha=0.1)
        self.thrsh_canvas.draw()

        self.thrsh_toolbar = NToolbar2PyPOLAR(canvas=self.thrsh_canvas, window=self.thrsh_frame)

        banner = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", height=Polarimetry.axes_size[0], width=40)
        banner.pack(side=tk.RIGHT, fill=tk.Y)
        Button(banner, image=self.icons["contrast"], command=self.contrast_thrsh_button_callback).pack(side=tk.TOP, padx=20, pady=(20, 0))
        self.contrast_thrsh_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_thrsh_slider_callback)
        self.contrast_thrsh_slider.set(1)
        ToolTip(self.contrast_thrsh_slider, text=" adjust contrast\n - the contrast changes the intensity value displayed in the navigation toolbar\n - the chosen contrast does not affect the analysis")
        self.contrast_thrsh_slider.pack(padx=20, pady=(0, 20))
        button = Button(banner, image=self.icons["palette"], command=self.change_colormap)
        ToolTip(button, text=" change the colormap used for thresholding ('hot' or 'gray')")
        button.pack(padx=20, pady=10)
        self.no_background_button = Button(banner, image=self.icons["photo_fill"], command=self.no_background)
        ToolTip(self.no_background_button, text=" change background to enhance visibility")
        self.no_background_button.pack(padx=20, pady=10)
        button = Button(banner, image=self.icons["open_in_new"], command=self.export_mask)
        ToolTip(button, text=" export mask as .png")
        button.pack(padx=20, pady=10)
        button = Button(banner, image=self.icons["format_list"], command=self.roimanager_callback)
        ToolTip(button, text=" open ROI Manager")
        button.pack(padx=20, pady=10)

        self.ilow = tk.StringVar(value="0")
        self.ilow_slider = CTk.CTkSlider(master=bottomframe, from_=0, to=1, command=self.ilow_slider_callback)
        self.ilow_slider.set(0)
        self.ilow_slider.grid(row=0, column=0, columnspan=2, padx=20, pady=0)
        self.transparency_slider = CTk.CTkSlider(master=bottomframe, from_=0, to=1, command=self.transparency_slider_callback)
        ToolTip(self.transparency_slider, text=" adjust the transparency of the background image")
        self.transparency_slider.set(0)
        self.transparency_slider.grid(row=0, column=2, padx=(100, 20), pady=0)
        CTk.CTkLabel(master=bottomframe, text="Ilow", anchor="e").grid(row=1, column=0)
        entry = CTk.CTkEntry(master=bottomframe, width=100, textvariable=self.ilow, border_color=gray[1], justify=tk.LEFT)
        entry.bind("<Return>", command=self.ilow2slider_callback)
        entry.grid(row=1, column=1, padx=(0, 20))
        CTk.CTkLabel(master=bottomframe, text="Transparency").grid(row=1, column=2, padx=(10, 0))
        self.edge_detection_switch = CTk.CTkSwitch(master=bottomframe, text="Edge detection", onvalue="on", offvalue="off", command=self.edge_detection_callback)
        self.edge_detection_switch.grid(row=0, column=3, padx=(50, 0))

## RIGHT FRAME: OPTIONS
        show_save = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        show_save.grid(row=0, column=0, padx=20, pady=10, sticky="nw")
        CTk.CTkLabel(master=show_save, text="\nFigures\n", font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=3, padx=20, pady=0)
        CTk.CTkLabel(master=show_save, text="Show", width=30, anchor="w").grid(row=1, column=1, padx=(0, 30), pady=(0, 10))
        CTk.CTkLabel(master=show_save, text="Save", width=30, anchor="w").grid(row=1, column=2, padx=(0, 20), pady=(0, 10))
        labels = ["Composite", "Sticks", "Histogram", "Intensity"]
        self.show_table = [CheckBox(show_save) for _ in range(len(labels))]
        self.save_table = [CheckBox(show_save) for _ in range(len(labels))]
        for _ in range(len(labels)):
            CTk.CTkLabel(master=show_save, text=labels[_], anchor="w", width=80, height=30).grid(row=_+2, column=0, padx=(20, 0))
            self.save_table[_].configure(command=self.click_save_output)
            self.show_table[_].grid(row=_+2, column=1, pady=0, padx=10, sticky="ew")
            self.save_table[_].grid(row=_+2, column=2, pady=0, padx=(10, 20))
        CTk.CTkLabel(master=show_save, text=" ").grid(row=len(labels)+2, column=0, padx=0, pady=0)

        preferences = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        preferences.grid(row=2, column=0, padx=20, pady=10)
        CTk.CTkLabel(master=preferences, text="\nPreferences\n", font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=2, padx=20, pady=0, sticky="nw")
        self.add_axes_checkbox = CheckBox(preferences, text="\n Axes on figures\n", command=self.add_axes_on_all_figures)
        self.add_axes_checkbox.select()
        self.add_axes_checkbox.grid(row=1, column=0, columnspan=2, padx=40, pady=(0, 0), sticky="ew")
        self.colorbar_checkbox = CheckBox(preferences, text="\n Colorbar on figures\n", command=self.colorbar_on_all_figures)
        self.colorbar_checkbox.select()
        self.colorbar_checkbox.grid(row=2, column=0, columnspan=2, padx=40, pady=(0, 0), sticky="ew")
        self.colorblind_checkbox = CheckBox(preferences, text="\n Colorblind-friendly\n", command=self.colorblind_on_all_figures)
        self.colorblind_checkbox.grid(row=3, column=0, columnspan=2, padx=40, pady=(0, 10), sticky="ew")
        labels = [" pixels per stick (horizontal)", " pixels per stick (vertical)"]
        self.pixelsperstick_spinboxes = [SpinBox(master=preferences, command=self.pixelsperstick_spinbox_callback) for it in range(2)]
        for _ in range(2):
            self.pixelsperstick_spinboxes[_].grid(row=_+4, column=0, padx=(20, 0), pady=(0, 20))
            label = CTk.CTkLabel(master=preferences, text=labels[_], anchor="w")
            label.grid(row=_+4, column=1, padx=(0, 20), pady=(0, 20), sticky="w")
            ToolTip(label, text=" controls the density of sticks to be plotted")
        self.histo_nbins = tk.StringVar(value="60")
        SpinBox(master=preferences, from_=10, to_=90, step_size=10, textvariable=self.histo_nbins).grid(row=6, column=0, padx=(20, 0), pady=(0, 20))
        label = CTk.CTkLabel(master=preferences, text=" bins for histograms", anchor="w")
        label.grid(row=6, column=1, padx=(0, 20), pady=(0, 20), sticky="w")
        ToolTip(label, text=" controls the number of bins used in histograms")
        button = Button(preferences, image=self.icons["crop"], command=self.crop_figures_callback)
        button.grid(row=7, column=0, columnspan=2, padx=40, pady=(0, 20), sticky="w")
        ToolTip(button, text=" click button to define region and crop figures")
        button = Button(preferences, image=self.icons["query_stats"], command=self.show_individual_fit_callback)
        ToolTip(button, text=" show an individual fit\n - zoom into the region of interest in the Rho composite\n - click this button\n - select a pixel with the crosshair on the Rho composite then click")
        button.grid(row=7, column=0, columnspan=2, padx=40, pady=(0, 20), sticky="e")
        
        self.variable_table_frame = CTk.CTkFrame(master=self.tabview.tab("Options"), width=300)
        self.variable_table_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nw")

        banner = CTk.CTkFrame(master=self.tabview.tab("Options"))
        banner.grid(row=2, column=1, padx=20, pady=10, sticky="nw")
        button = Button(banner, image=self.icons["delete_forever"], command=self.initialize_tables)
        ToolTip(button, text=" reinitialize Figures, Save output and Variables tables")
        button.grid(row=0, column=0, padx=(0, 100), pady=0, sticky="w")
        self.per_roi = CheckBox(banner, text="per ROI", command=self.per_roi_callback)
        ToolTip(self.per_roi, text=" show and save data/figures separately for each region of interest")
        self.per_roi.grid(row=0, column=1, sticky="w")

        save_ext = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        CTk.CTkLabel(master=save_ext, text="\nSave output\n", font=CTk.CTkFont(size=16), width=230).grid(row=0, column=0, columnspan=2, padx=(20, 20), pady=(0, 0))
        save_ext.grid(row=2, column=1, padx=20, pady=(20, 90), sticky="sw")
        labels = ["Data (.pykl)", "Figures (.tif)", "Data (.mat)", "Mean values (.xlsx)", "Movie (.gif)"]
        self.extension_table = [CheckBox(save_ext) for _ in range(len(labels))]
        self.extension_table[1].configure(state="disabled")
        for _ in range(len(labels)):
            CTk.CTkLabel(master=save_ext, text=labels[_], anchor="w").grid(row=_+1, column=0, padx=(40, 0), sticky="w")
            self.extension_table[_].grid(row=_+1, column=1, pady=0, padx=(0,0))
        CTk.CTkLabel(master=save_ext, text=" ").grid(row=len(labels)+1, column=0)

        button = Button(self.tabview.tab("Options"), image=self.icons["merge"], command=self.merge_histos)
        ToolTip(button, text=" concatenate histograms\n - choose variables in the Variables table\n - click button to select the folder containing the .mat files")
        button.grid(row=2, column=1, padx=20, pady=30, sticky="sw")

## RIGHT FRAME: ADV
        adv_elts = ["Dark", "Binning", "Polarization", "Rotation", "Disk cone / Calibration data", "Intensity removal"]
        adv_loc = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        columnspan = [1, 2, 1, 2, 1, 2]
        adv = {}
        for loc, elt, cspan in zip(adv_loc, adv_elts, columnspan):
            adv.update({elt: CTk.CTkFrame(
            master=self.tabview.tab("Advanced"), fg_color=self.left_frame.cget("fg_color"))})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=10, sticky="nw")
            CTk.CTkLabel(master=adv[elt], text=elt + "\n", width=230, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=cspan, padx=20, pady=(10,0))

        self.dark_switch = CTk.CTkSwitch(master=adv["Dark"], text="", command=self.dark_switch_callback, onvalue="on", offvalue="off", width=50)
        self.dark_switch.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        self.calculated_dark_label = CTk.CTkLabel(master=adv["Dark"], text="Calculated dark value = 0")
        self.calculated_dark_label.grid(row=2, column=0, sticky="w", padx=40)
        self.dark = tk.StringVar()
        self.dark_entry = Entry(adv["Dark"], text="Used dark value", textvariable=self.dark, row=1, column=0)
        ToolTip(self.dark_entry, text=" for 1PF, use a dark value greater than 480\n - raw images correspond to a dark value 0")
        self.dark_entry.bind("<Return>", command=self.intensity_callback)
        self.dark_entry.set_state("disabled")
        CTk.CTkLabel(master=adv["Dark"], text=" ", height=5).grid(row=3, column=0, pady=5)

        self.offset_angle_switch = CTk.CTkSwitch(master=adv["Polarization"], text="", command=self.offset_angle_switch_callback, onvalue="on", offvalue="off", width=50)
        self.offset_angle_switch.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        self.offset_angle = tk.StringVar(value="0")
        self.offset_angle_entry = Entry(adv["Polarization"], text="\nOffset angle (deg)\n", textvariable=self.offset_angle, row=1)
        self.offset_angle_entry.set_state("disabled")
        CTk.CTkLabel(master=adv["Polarization"], text=" ").grid(row=2, column=0)
        self.polar_dir = tk.StringVar(value="clockwise")
        self.polarization_button = Button(adv["Polarization"], image=self.icons[self.polar_dir.get()], command=self.change_polarization_direction)
        self.polarization_button.grid(row=2, column=0, pady=10)
        ToolTip(self.polarization_button, text=" change polarization direction")

        button = Button(adv["Disk cone / Calibration data"], image=self.icons["photo"], command=self.diskcone_display)
        button.grid(row=1, column=0, padx=(52, 0), pady=10, sticky="w")
        ToolTip(button, text=" display the selected disk cone (for 1PF)")
        self.calib_dropdown = CTk.CTkOptionMenu(master=adv["Disk cone / Calibration data"], values="", width=button_size[0]-button_size[1], height=button_size[1], dynamic_resizing=False, command=self.calib_dropdown_callback)
        self.calib_dropdown.grid(row=1, column=0, padx=(0, 52), pady=10, sticky="e")
        ToolTip(self.calib_dropdown, text=" 1PF: select disk cone depending on wavelength and acquisition date\n 4POLAR: select .mat file containing the calibration data")
        self.calib_textbox = TextBox(master=adv["Disk cone / Calibration data"], width=250, height=50, state="disabled")
        self.calib_textbox.grid(row=3, column=0, pady=10)
        self.polar_dropdown = CTk.CTkOptionMenu(master=adv["Disk cone / Calibration data"], width=button_size[0], height=button_size[1], dynamic_resizing=False, command=self.polar_dropdown_callback, state="disabled")
        angles = [0, 45, 90, 135]
        self.dict_polar = {}
        for p in list(permutations([0, 1, 2, 3])):
            a = [angles[_] for _ in p]
            self.dict_polar.update({f"UL{a[0]}-UR{a[1]}-LR{a[2]}-LL{a[3]}": p})
        self.polar_dropdown.configure(values=list(self.dict_polar.keys()))
        self.polar_dropdown.grid(row=4, column=0, pady=10)
        ToolTip(self.polar_dropdown, text=" 4POLAR: select the distribution of polarizations (0,45,90,135) among quadrants clockwise\n Upper Left (UL), Upper Right (UR), Lower Right (LR), Lower Left (LL)")

        labels = ["Bin width", "Bin height"]
        self.bin_spinboxes = [SpinBox(adv["Binning"], command=lambda:self.intensity_callback(event=1)) for _ in range(2)]
        for _ in range(2):
            self.bin_spinboxes[_].bind("<Return>", command=self.intensity_callback)
            self.bin_spinboxes[_].grid(row=_+1, column=0, padx=(30, 10), pady=10, sticky="e")
            label = CTk.CTkLabel(master=adv["Binning"], text="\n" + labels[_] + "\n")
            label.grid(row=_+1, column=1, padx=(10, 60), pady=0, sticky="w")
            ToolTip(label, text=" height and width of the bin used for data binning")

        labels = ["Stick (deg)", "Figure (deg)"]
        self.rotation = [tk.StringVar(value="0"), tk.StringVar(value="0")]
        for _ in range(len(labels)):
            label = CTk.CTkLabel(adv["Rotation"], text="\n" + labels[_] + "\n")
            ToolTip(label, text=" positive value for counter-clockwise rotation\n negative value for clockwise rotation")
            label.grid(row=_+1, column=1, padx=(0, 10), sticky="w")
            entry = CTk.CTkEntry(adv["Rotation"], textvariable=self.rotation[_], width=50, justify="center")
            entry.grid(row=_+1, column=0, padx=20, sticky="e")
            entry.bind("<Return>", command=self.rotation_callback)
        CTk.CTkLabel(master=adv["Rotation"], text=" ", height=5).grid(row=3, column=0, pady=5)

        self.noise = [tk.StringVar(value="1"), tk.StringVar(value="3"), tk.StringVar(value="3")]
        labels = ["Bin width", "Bin height"]
        for _ in range(2):
            SpinBox(adv["Intensity removal"], from_=3, to_=19, step_size=2, textvariable=self.noise[_+1]).grid(row=_+1, column=0, padx=(30, 10), pady=10, sticky="e")
            label = CTk.CTkLabel(master=adv["Intensity removal"], text="\n" + labels[_] + "\n")
            label.grid(row=_+1, column=1, padx=(10, 60), pady=0, sticky="w")
            ToolTip(label, text=" height and width of the bin used for intensity removal")
        label = CTk.CTkLabel(master=adv["Intensity removal"], text="\nPick center of bin\n")
        label.grid(row=3, column=1, padx=10, pady=0, sticky="w")
        ToolTip(label, text=" pick center of the bin used for intensity removal")
        button = Button(adv["Intensity removal"], image=self.icons["removal"], command=lambda:self.click_callback(self.intensity_axis, self.intensity_canvas, "click background"))
        button.grid(row=3, column=0, pady=10, padx=25, sticky="e")
        ToolTip(button, text=" click button and select a point on the intensity image")
        CTk.CTkEntry(adv["Intensity removal"], textvariable=self.noise[0], width=50, justify="center").grid(row=4, column=0, sticky="e", padx=23)
        label = CTk.CTkLabel(adv["Intensity removal"], text="\nFactor\n")
        ToolTip(label, text=" fraction of the mean intensity value to be substracted\n value between 0 and 1")
        label.grid(row=4, column=1, padx=10, sticky="w")
        self.intensity_removal_label = CTk.CTkLabel(master=adv["Intensity removal"], text="Removed intensity value = 0")
        self.intensity_removal_label.grid(row=5, column=0, columnspan=2, padx=(40, 10), pady=(0, 0), sticky="w")
        CTk.CTkLabel(master=adv["Intensity removal"], text=" ", height=5).grid(row=6, column=0, pady=5)

## RIGHT FRAME: ABOUT
        banner = CTk.CTkFrame(master=self.tabview.tab("About"))
        banner.grid(row=0, column=0, pady=20, sticky="w")
        button = Button(banner, image=self.icons["web"], command=lambda:self.openweb(Polarimetry.url_fresnel))
        ToolTip(button, text=" visit the polarimetry website")
        button.pack(side=tk.LEFT, padx=40)
        button = Button(banner, image=self.icons["mail"], command=self.send_email)
        ToolTip(button, text=" send an email to report bugs and/or send suggestions")
        button.pack(side=tk.LEFT, padx=40)
        button = Button(banner, image=self.icons["GitHub"], command=lambda:self.openweb(Polarimetry.url_github))
        ToolTip(button, text=" visit the PyPOLAR GitHub page")
        button.pack(side=tk.LEFT, padx=40)
        button = Button(banner, image=self.icons["contact_support"], command=lambda:self.openweb(Polarimetry.url_github + "/blob/master/README.md"))
        ToolTip(button, text=" visit the online help")
        button.pack(side=tk.LEFT, padx=40)
        about_textbox = TextBox(master=self.tabview.tab("About"), width=Polarimetry.tab_width-30, height=500)
        about_textbox.write(f"Version: {Polarimetry.__version__} ({Polarimetry.__version_date__}) \n\n\n Website: www.fresnel.fr/polarimetry/ \n\n\n Source code available at github.com/cchandre/Polarimetry \n\n\n\n Based on a code originally developed by Sophie Brasselet (Institut Fresnel, CNRS) \n\n\n To report bugs, send an email to\n     manos.mavrakis@cnrs.fr  (Manos Mavrakis, Institut Fresnel, CNRS) \n     cristel.chandre@cnrs.fr  (Cristel Chandre, Institut de Mathématiques de Marseille, CNRS) \n     sophie.brasselet@fresnel.fr  (Sophie Brasselet, Institut Fresnel, CNRS) \n\n\n\n BSD 2-Clause License\n\n Copyright(c) 2021, Cristel Chandre\n All rights reserved. \n\n\n  created using Python with packages Tkinter (CustomTkinter), NumPy, SciPy, OpenCV,\n Matplotlib, openpyxl, tksheet, colorcet \n\n\n  uses Material Design icons by Google")
        about_textbox.grid(row=1, column=0, padx=30)
        self.startup()

    def startup(self) -> None:
        self.method.set("1PF")
        self.option.set("Thresholding (manual)")
        self.define_variable_table("1PF")
        self.CD = Calibration("1PF")
        self.calib_dropdown.configure(values=self.CD.list("1PF"))
        self.calib_dropdown.set(self.CD.list("1PF")[0])
        self.calib_textbox.write(self.CD.name)
        self.polar_dropdown.set("UL90-UR0-LR45-LL135")
        self.thrsh_colormap = "hot"
        self.tabview.set("Intensity")
        self.filename_label.focus()
        self.removed_intensity = 0

    def initialize_slider(self) -> None:
        if hasattr(self, "stack"):
            self.stack_slider.configure(to=self.stack.nangle, number_of_steps=self.stack.nangle)
            self.ilow.set(self.stack.display.format(np.amin(self.datastack.intensity)))
            self.ilow_slider.set(float(self.ilow.get()))
            self.contrast_intensity_slider.set(1)
            self.contrast_thrsh_slider.set(1)
            self.stack_slider.set(0)
            self.stack_slider_label.configure(text="T")

    def initialize_noise(self) -> None:
        vals = [1, 3, 3]
        for val, _ in zip(vals, self.noise):
            _.set(str(val))
        self.removed_intensity = 0
        self.intensity_removal_label.configure(text="Removed intensity value = 0")

    def initialize(self) -> None:
        self.initialize_slider()
        self.initialize_noise()
        if hasattr(self, "datastack"):
            self.datastack.rois = []
        self.ontab_intensity()
        self.ontab_thrsh()

    def initialize_tables(self) -> None:
        for show, save in zip(self.show_table, self.save_table):
            show.deselect()
            save.deselect()
        if hasattr(self, "variable_display"):
            for var in self.variable_display:
                var.set(0)
        for ext in self.extension_table:
            ext.deselect()

    def click_save_output(self) -> None:
        vec = [val.get() for val in self.save_table]
        if any(vec) == 1:
            self.extension_table[1].select()
        else:
            self.extension_table[1].deselect()

    def on_closing(self) -> None:
        plt.close("all") 
        self.destroy()

    def clear_frame(self, frame:CTk.CTkFrame) -> None:
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()

    def openweb(self, url:str) -> None:
        webbrowser.open(url)

    def send_email(self) -> None:
        webbrowser.open("mailto:?to=" + Polarimetry.email + "&subject=[Polarimetry Analysis] question", new=1)

    def on_click_tab(self) -> None:
        if self.tabview.get() != "About":
            self.tabview.set("About")
        else:
            self.tabview.set("Intensity")

    def edge_detection_callback(self) -> None:
        if hasattr(self, "stack"):
            if self.edge_detection_switch.get() == "on":
                window = ShowInfo(message=" Mask for edge detection", image=self.icons["multiline_chart"], button_labels=["Download", "Compute", "Cancel"], geometry=(370, 140), fontsize=16)
                buttons = window.get_buttons()
                buttons[0].configure(command=lambda:self.download_edge_mask(window))
                buttons[1].configure(command=lambda:self.compute_edge_mask(window))
                buttons[2].configure(command=lambda:self.delete_edge_mask(window))
            elif self.edge_detection_switch.get() == "off":
                if hasattr(self, "edge_contours"):
                    delattr(self, "edge_contours")
                self.tabview.delete("Edge Detection")
                self.ontab_thrsh()
        else:
            self.edge_detection_switch.deselect()

    def delete_edge_mask(self, window:CTk.CTkToplevel) -> None:
        window.withdraw()
        if hasattr(self, "edge_contours"):
            delattr(self, "edge_contours")
        self.edge_detection_switch.deselect()

    def download_edge_mask(self, window:CTk.CTkToplevel) -> None:
        window.withdraw()
        filetypes = [("PNG files", "*.png")]
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        filename = fd.askopenfilename(title="Select a mask file", initialdir=initialdir, filetypes=filetypes)
        self.edge_method = "download"
        self.edge_detection_tab()
        self.edge_mask = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        self.compute_edges()

    def compute_edge_mask(self, window:CTk.CTkToplevel) -> None:
        window.withdraw()
        if hasattr(self, "stack"):
            self.edge_method = "compute"
            self.edge_detection_tab()
            self.compute_edges()

    def edge_detection_tab(self) -> None:
        self.tabview.insert(4, "Edge Detection")
        adv_elts = ["Edge detection", "Layer"]
        adv_loc = [(0, 0), (0, 1)]
        adv = {}
        for loc, elt in zip(adv_loc, adv_elts):
            adv.update({elt: CTk.CTkFrame(
            master=self.tabview.tab("Edge Detection"), fg_color=gray[0])})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=(10, 10), sticky="nw")
            CTk.CTkLabel(master=adv[elt], text=elt + "\n", width=230, font=CTk.CTkFont(size=16)).grid(row=0, column=0, padx=20, pady=(10,0))
        params = ["Low threshold", "High threshold", "Length", "Smoothing window"]
        tooltips = [" hysteresis thresholding values: edges with intensity gradients\n below this value are not edges and discarded ", " hysteresis thresholding values: edges with intensity gradients\n larger than this value are sure to be edges", " minimum length for a contour (in pixels)", " number of pixels in the window used for smoothing contours (in pixels)"]
        self.canny_thrsh = [tk.StringVar(value="60"), tk.StringVar(value="100"), tk.StringVar(value="100"), tk.StringVar(value="20")]
        for _, (param, tooltip) in enumerate(zip(params, tooltips)):
            entry = Entry(adv["Edge detection"], text=param, textvariable=self.canny_thrsh[_], row=_+1)
            entry.bind("<Return>", command=self.compute_edges)
            ToolTip(entry, text=tooltip)
        CTk.CTkLabel(master=adv["Edge detection"], text=" ").grid(row=5, column=0)
        params = ["Distance from contour", "Layer width"]
        tooltips = [" width of the region to be analyzed (in pixels)", " distance from contour of the region to be analyzed (in pixels)"]
        self.layer_params = [tk.StringVar(value="0"), tk.StringVar(value="10")]
        for _, (param, tooltip) in enumerate(zip(params, tooltips)):
            entry = Entry(adv["Layer"], text=param, textvariable=self.layer_params[_], row=_+1)
            ToolTip(entry, text=tooltip)
        CTk.CTkLabel(master=adv["Layer"], text=" ").grid(row=3, column=0)

    def compute_edges(self, event:tk.Event=None) -> None:
        if self.edge_method == "compute":
            field = self.stack.intensity.copy()
            thrsh = float(self.ilow.get())
            field[field <= thrsh] = 0
            field = (field / np.amax(field) * 255).astype(np.uint8)
            field = cv2.GaussianBlur(field, (5, 5), 0)
            edges = cv2.Canny(image=field, threshold1=float(self.canny_thrsh[0].get()), threshold2=float(self.canny_thrsh[1].get()))
            contours = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
        elif self.edge_method == "download":
            contours = cv2.findContours(self.edge_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
        filter = np.asarray([len(contour) >= int(self.canny_thrsh[2].get()) for contour in contours])
        self.edge_contours = [self.smooth_edge(contour.reshape((-1, 2))) for (contour, val) in zip(contours, filter) if val]
        self.ontab_thrsh()

    def smooth_edge(self, edge:np.ndarray) -> np.ndarray:
        window_length = int(self.canny_thrsh[3].get())
        return savgol_filter(edge, window_length=window_length, polyorder=3, mode="nearest", axis=0)
    
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
        self.polar_dir.set("clockwise" if self.polar_dir.get() == "counterclockwise" else "counterclockwise")
        self.polarization_button.configure(image=self.icons[self.polar_dir.get()])

    def contrast_thrsh_slider_callback(self, value:float) -> None:
        if value <= 0.001:
            self.contrast_thrsh_slider.set(0.001)
        self.ontab_thrsh()

    def contrast_intensity_slider_callback(self, value:float) -> None:
        if value <= 0.001:
            self.contrast_intensity_slider.set(0.001)
        self.ontab_intensity()

    def contrast_intensity_button_callback(self) -> None:
        if self.contrast_intensity_slider.get() <= 0.5:
            self.contrast_intensity_slider.set(0.5)
        else:
            self.contrast_intensity_slider.set(1)
        self.ontab_intensity()

    def contrast_thrsh_button_callback(self) -> None:
        if self.contrast_thrsh_slider.get() <= 0.5:
            self.contrast_thrsh_slider.set(0.5)
        else:
            self.contrast_thrsh_slider.set(1)
        self.ontab_thrsh(update=True)

    def roimanager_callback(self) -> None:

        def on_closing(manager:ROIManager) -> None:
            if hasattr(self, "datastack"):
                for roi in self.datastack.rois:
                    roi["select"] = True
                self.ontab_intensity()
                self.ontab_thrsh()
            manager.destroy()
            delattr(self, "manager")

        def commit(manager:ROIManager) -> None:
            if hasattr(self, "datastack"):
                if any(self.datastack.rois):
                    self.datastack.rois = manager.update_rois(self.datastack.rois)
                    self.ontab_intensity()
                    self.ontab_thrsh()

        def delete(manager:ROIManager) -> None:
            if hasattr(self, "datastack"):
                manager.delete(self.datastack.rois)
                self.ontab_intensity()
                self.ontab_thrsh()

        def delete_all(manager:ROIManager) -> None:
            if hasattr(self, "datastack"):
                if any(self.datastack.rois):
                    self.datastack.rois = []
                    manager.delete_all()
                    self.ontab_intensity()
                    self.ontab_thrsh()

        def load(manager:ROIManager) -> None:
            if hasattr(self, "datastack"):
                self.datastack.rois = manager.load(initialdir=self.stack.folder if hasattr(self, "stack") else "/")
                self.ontab_intensity()
                self.ontab_thrsh()
        if not hasattr(self, "manager"):
            if hasattr(self, "datastack"):
                self.manager = ROIManager(rois=self.datastack.rois)
            else:
                self.manager = ROIManager(rois=[])
            self.manager.protocol("WM_DELETE_WINDOW", lambda:on_closing(self.manager))
            self.manager.bind("<Command-q>", lambda:on_closing(self.manager))
            self.manager.bind("<Command-w>", lambda:on_closing(self.manager))
            buttons = self.manager.get_buttons()
            buttons[0].configure(command=lambda:commit(self.manager))
            buttons[1].configure(command=lambda:self.manager.save(self.datastack.rois, self.datastack.filename))
            buttons[2].configure(command=lambda:load(self.manager))
            buttons[-1].configure(command=lambda:delete_all(self.manager))
            buttons[-2].configure(command=lambda:delete(self.manager))

    def add_axes_on_all_figures(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if hasattr(self, "datastack"):
                if (fig.type in ["Composite", "Sticks", "Intensity"]) and (self.datastack.name in fs):
                    fig.axes[0].axis(self.add_axes_checkbox.get())
                    fig.canvas.draw()

    def colorbar_on_all_figures(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if hasattr(self, "datastack"):
                if (fig.type in ["Composite", "Sticks", "Intensity"]) and (self.datastack.name in fs):
                    if self.colorbar_checkbox.get():
                        ax_divider = make_axes_locatable(fig.axes[0])
                        cax = ax_divider.append_axes("right", size="7%", pad="2%")
                        if fig.type == "Composite":
                            fig.colorbar(fig.axes[0].images[1], cax=cax)
                        elif (fig.type == "Sticks") or ((fig.type == "Intensity") and (self.edge_detection_switch.get() == "on")):
                            fig.colorbar(fig.axes[0].collections[0], cax=cax)
                        if (fig.type == "Intensity") and (self.edge_detection_switch.get() == "off"):
                            fig.axes[1].remove()
                    else:
                        if len(fig.axes) >= 2:
                            fig.axes[1].remove()

    def colorblind_on_all_figures(self) -> None:
            figs = list(map(plt.figure, plt.get_fignums()))
            for fig in figs:
                fs = fig.canvas.manager.get_window_title()
                if hasattr(self, "datastack"):
                    for var in self.datastack.vars:
                        if (var.name == fig.var):
                            cmap = var.colormap[self.colorblind_checkbox.get()]
                    if fig.type == "Intensity":
                        cmap = self.datastack.vars[0].colormap[self.colorblind_checkbox.get()]
                    if (fig.type == "Composite") and (self.datastack.name in fs):
                        fig.axes[0].images[1].set_cmap(cmap)
                    elif ((fig.type == "Sticks") or ((fig.type == "Intensity") and (self.edge_detection_switch.get() == "on"))) and (self.datastack.name in fs):
                        fig.axes[0].collections[0].set_cmap(cmap)
                if fs.startswith("Disk Cone"):
                    fig.axes[0].images[0].set_cmap("hsv" if not self.colorblind_checkbox.get() else cc.m_colorwheel)
                    fig.axes[1].images[0].set_cmap("jet" if not self.colorblind_checkbox.get() else "viridis")

    def options_dropdown_callback(self, option:str) -> None:
        if option.endswith("(auto)"):
            self.options_dropdown.get_icon().configure(image=self.icons["build_fill"])
        else:
            self.options_dropdown.get_icon().configure(image=self.icons["build"])
        if option.startswith("Mask"):
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            self.maskfolder = fd.askdirectory(title="Select the directory containing masks", initialdir=initialdir)
            if hasattr(self, "datastack"):
                self.mask = self.get_mask(self.datastack)
                self.ontab_thrsh()
                self.thrsh_frame.update()

    def open_file_callback(self, value:str) -> None:
        self.edge_detection_switch.deselect()
        self.filelist = []
        if hasattr(self, "edge_contours"):
            delattr(self, "edge_contours")
            self.tabview.delete("Edge Detection")
        if hasattr(self, "manager_window"):
            self.manager_window.destroy()
        if value == "Open file":
            filetypes = [("Tiff files", "*.tiff"), ("Tiff files", "*.tif")]
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            filename = fd.askopenfilename(title="Select a file", initialdir=initialdir, filetypes=filetypes)
            if filename:
                self.options_dropdown.get_icon().configure(image=self.icons["build"])
                self.openfile_dropdown.get_icon().configure(image=self.icons["photo_fill"])
                self.options_dropdown.set_state("normal")
                self.options_dropdown.set_values(["Thresholding (manual)", "Mask (manual)"])
                self.option.set("Thresholding (manual)")
                if hasattr(self, "mask"):
                    delattr(self, "mask")
                self.open_file(filename)
        elif value == "Open folder": 
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            folder = fd.askdirectory(title="Select a directory", initialdir=initialdir)
            if folder:
                self.openfile_dropdown.get_icon().configure(image=self.icons["folder_open"])
                for filename in os.listdir(folder):
                    if filename.endswith((".tif", ".tiff")):
                        self.filelist += [os.path.join(folder, filename)]
            self.indxlist = 0
            if any(self.filelist):
                self.open_file(self.filelist[0])
                self.options_dropdown.set_state("normal")
                self.options_dropdown.set_values(["Thresholding (manual)", "Thresholding (auto)", "Mask (manual)", "Mask (auto)"])
                self.option.set("Thresholding (manual)")
            else:
                ShowInfo(message=" The folder does not contain TIFF or TIF files", image=self.icons["download_folder"], button_labels=["OK"], geometry=(340, 140))
        elif value == "Previous analysis":
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            filename = fd.askopenfilename(title="Download a previous polarimetry analysis", initialdir=initialdir, filetypes=[("PyPOLAR pickle files", "*.pykl")])
            if filename:
                window = ShowInfo(message=" Downloading and decompressing data...", image=self.icons["download"], geometry=(350, 80))
                window.update()
                with bz2.BZ2File(filename, "rb") as f:
                    if hasattr(self, "stack"):
                        delattr(self, "stack")
                    self.openfile_dropdown.get_icon().configure(image=self.icons["analytics"])
                    self.datastack = cPickle.load(f)
                    self.method.set(self.datastack.method)
                    self.define_variable_table(self.datastack.method)
                    self.options_dropdown.set_state("disabled")
                    self.option.set("Previous analysis")
                    self.intensity_axis.clear()
                    self.intensity_axis.set_axis_off()
                    self.intensity_canvas.draw()
                    self.thrsh_axis.clear()
                    self.thrsh_axis.set_axis_off()
                    self.thrsh_canvas.draw()
                    self.filename_label.write(self.datastack.name)
                    self.ontab_intensity(update=False)
                window.withdraw()
        if hasattr(self, "stack"):
            self.ilow_slider.configure(from_=np.amin(self.stack.intensity), to=np.amax(self.stack.intensity))
            self.ilow_slider.set(np.amin(self.stack.intensity))
            self.ilow.set(self.stack.display.format(np.amin(self.stack.intensity)))
            self.ontab_thrsh(update=False)

    def crop_figures_callback(self) -> None:
        if len(plt.get_fignums()) and hasattr(self, "datastack") and (not hasattr(self, "crop_window")):
            self.crop_window = CTk.CTkToplevel(self)
            self.crop_window.title(f"Crop figures for {self.datastack.name}")
            self.crop_window.geometry(geometry_info((300, 230)))
            self.crop_window.protocol("WM_DELETE_WINDOW", self.crop_on_closing)
            self.crop_window.bind("<Command-q>", lambda:self.crop_on_closing)
            self.crop_window.bind("<Command-w>", self.crop_on_closing)
            CTk.CTkLabel(self.crop_window, text="  define xlim and ylim", image=self.icons["crop"], compound="left", font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=3, padx=30, pady=20)
            if not hasattr(self, "xylim"):
                self.xylim = []
                vals = [1, self.datastack.width, 1, self.datastack.height]
                for val in vals:
                    self.xylim += [tk.StringVar(value=str(val))]
            labels = [u"\u2B62 xlim", u"\u2B63 ylim"]
            positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
            for _, label in enumerate(labels):
                CTk.CTkLabel(master=self.crop_window, text=label).grid(row=_+1, column=0, padx=(40, 0), pady=0)
            for var, position in zip(self.xylim, positions):
                Entry(master=self.crop_window, textvariable=var, row=position[0], column=position[1], fg_color=gray[1])
            banner = CTk.CTkFrame(self.crop_window)
            banner.grid(row=3, column=0, columnspan=3)
            button = Button(banner, text="Crop", anchor="center", command=lambda:self.crop_figures(self.crop_window), width=80, height=button_size[1])
            ToolTip(button, text=" crop figures using the chosen axis limits")
            button.grid(row=0, column=0, padx=10, pady=20)
            button = Button(banner, text="Get", anchor="center", command=self.get_axes, width=80, height=button_size[1])
            ToolTip(button, text=" get the axis limits of the active figure")
            button.grid(row=0, column=1, padx=10, pady=20)
            Button(banner, text="Reset", anchor="center", command=lambda:self.reset_figures(self.crop_window), width=80, height=button_size[1]).grid(row=0, column=2, padx=10, pady=20)

    def crop_on_closing(self):
        self.crop_window.destroy()
        delattr(self, "crop_window")

    def crop_figures(self, window:CTk.CTkToplevel) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (fig.type in ["Sticks", "Composite", "Intensity"]) and (self.datastack.name in fs):
                fig.axes[0].set_xlim((int(self.xylim[0].get()), int(self.xylim[1].get())))
                fig.axes[0].set_ylim((int(self.xylim[3].get()), int(self.xylim[2].get())))

    def get_axes(self) -> None:
        fig = plt.gcf()
        if fig.type in ["Sticks", "Composite", "Intensity"]:
            ax = fig.axes[0]
            self.xylim[0].set(int(ax.get_xlim()[0]))
            self.xylim[1].set(int(ax.get_xlim()[1]))
            self.xylim[2].set(int(ax.get_ylim()[1]))
            self.xylim[3].set(int(ax.get_ylim()[0]))
        else:
            ShowInfo(message=" Select an active figure of the type\n Composite, Sticks or Intensity", image=self.icons["crop"], button_labels=["OK"])

    def reset_figures(self, window:CTk.CTkToplevel) -> None:
        vals = [1, self.datastack.width, 1, self.datastack.height]
        for _, val in enumerate(vals):
            self.xylim[_].set(val)
        self.crop_figures(window)

    def clear_patches(self, ax:plt.Axes, canvas:FigureCanvasTkAgg) -> None:
        if ax.patches:
            for p in ax.patches:
                p.set_visible(False)
                p.remove()
            for txt in ax.texts:
                txt.set_visible(False)
            canvas.draw()

    def export_mask(self) -> None:
        if hasattr(self, "datastack"):
            window = ShowInfo(message=" Select output mask type: \n\n   - ROI: export ROIs as segmentation mask \n   - Intensity: export intensity-thresholded image as segmentation mask \n   - ROI \u00D7 Intensity: export intensity-thresholded ROIs as segmentation mask", image=self.icons['open_in_new'], button_labels=["ROI", "Intensity", "ROI \u00D7 Intensity", "Cancel"], geometry=(530, 200))
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
            data.save(self.datastack.filename + ".png")
        window.withdraw()

    def change_colormap(self) -> None:
        self.thrsh_colormap = "gray" if self.thrsh_colormap == "hot" else "hot"
        self.ontab_thrsh()

    def no_background(self) -> None:
        if hasattr(self, "stack"):
            if self.thrsh_fig.patch.get_facecolor() == mpl.colors.to_rgba("k", 1):
                self.thrsh_fig.patch.set_facecolor(gray[1])
                self.no_background_button.configure(image=self.icons["photo_fill"])
            else:
                self.thrsh_fig.patch.set_facecolor("k")
                self.no_background_button.configure(image=self.icons["photo"])
            self.thrsh_canvas.draw()

    def offset_angle_switch_callback(self) -> None:
        self.offset_angle_entry.set_state("normal" if self.offset_angle_switch.get() == "on" else "disabled")

    def dark_switch_callback(self) -> None:
        if hasattr(self, "stack"):
            if self.dark_switch.get() == "on":
                self.dark_entry.set_state("normal")
                self.dark.set(self.stack.display.format(self.calculated_dark))
            else:
                self.dark_entry.set_state("disabled")
                self.dark.set(self.stack.display.format(self.calculated_dark))
                self.intensity_callback(event=1)
        else:
            self.dark.set("")

    def calib_dropdown_callback(self, label:str) -> None:
        self.CD = Calibration(self.method.get(), label=label)
        self.offset_angle.set(str(self.CD.offset_default))
        self.calib_textbox.write(self.CD.name)

    def polar_dropdown_callback(self, label:str) -> None:
        self.order = self.dict_polar.get(label)

    def show_individual_fit_callback(self) -> None:
        if not self.method.get().endswith("4POLAR") and hasattr(self, "datastack"):
            figs = list(map(plt.figure, plt.get_fignums()))
            fig_ = None
            for fig in figs:
                fs = fig.canvas.manager.get_window_title()
                if fig.var == "Rho" and fig.type == "Composite" and (self.datastack.name in fs):
                    fig_ = fig
                    break
            if fig_ is not None:
                plt.figure(fig_)
                cfm = plt.get_current_fig_manager()
                cfm.window.attributes("-topmost", True)
                cfm.window.tkraise()
                self.click_callback(fig_.axes[0], fig_.canvas, "individual fit")
                cfm.window.attributes("-topmost", False)
            else:
                ShowInfo(message="  provide a Rho Composite figure\n  to plot individual fits", image=self.icons["query_stats"], button_labels=["OK"])

    def diskcone_display(self) -> None:
        if self.method.get() == "1PF" and hasattr(self, "CD"):
            self.CD.display(colorblind=self.colorblind_checkbox.get())

    def variable_table_switch_callback(self) -> None:
        state = "normal" if self.variable_table_switch.get() == "on" else "disabled"
        for entry in self.variable_entries[2:]:
            entry.set_state(state)

    def click_callback(self, ax:plt.Axes, canvas:FigureCanvasTkAgg, method:str) -> None:
        if hasattr(self, "datastack"):
            if method == "click background":
                self.tabview.set("Intensity")
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            hlines = [plt.Line2D([(xlim[0] + xlim[1])/2, (xlim[0] + xlim[1])/2], ylim, lw=1, color="w"),
                plt.Line2D(xlim, [(ylim[0] + ylim[1])/2, (ylim[0] + ylim[1])/2], lw=1, color="w")]
            ax.add_line(hlines[0])
            ax.add_line(hlines[1])
            self.__cid1 = canvas.mpl_connect("motion_notify_event", lambda event: self.click_motion_notify_callback(event, hlines, ax, canvas))
            if method == "click background":
                self.__cid2 = canvas.mpl_connect("button_press_event", lambda event: self.click_background_button_press_callback(event, hlines, ax, canvas))
            elif method == "individual fit":
                self.__cid2 = canvas.mpl_connect("button_press_event", lambda event: self.individual_fit_button_press_callback(event, hlines, ax, canvas))

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
                self.intensity_removal_label.configure(text=f"Removed intensity value = {self.removed_intensity}")
                canvas.mpl_disconnect(self.__cid1)
                canvas.mpl_disconnect(self.__cid2)
                for line in hlines:
                    line.remove()
                canvas.draw()

    def compute_angle(self) -> None:
        if hasattr(self, "stack"):
            self.tabview.set("Intensity")
            self.compute_angle_button.configure(fg_color=orange[1])
            hroi = ROI()
            self.__cid1 = self.intensity_canvas.mpl_connect("motion_notify_event", lambda event: self.compute_angle_motion_notify_callback(event, hroi))
            self.__cid2 = self.intensity_canvas.mpl_connect("button_press_event", lambda event: self.compute_angle_button_press_callback(event, hroi))

    def compute_angle_motion_notify_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.intensity_axis:
            x, y = event.xdata, event.ydata
            if ((event.button is None or event.button == 1) and roi.lines):
                roi.lines[-1].set_data([roi.previous_point[0], x], [roi.previous_point[1], y])
                self.intensity_canvas.draw()

    def compute_angle_button_press_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.intensity_axis:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                if not roi.lines:
                    roi.lines = [plt.Line2D([x, x], [y, y], lw=3, color="w")]
                    roi.start_point = [x, y]
                    roi.previous_point = roi.start_point
                    self.intensity_axis.add_line(roi.lines[0])
                    self.intensity_canvas.draw()
                else:
                    roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], lw=3, color="w")]
                    roi.previous_point = [x, y]
                    self.intensity_axis.add_line(roi.lines[-1])
                    self.intensity_canvas.draw()
                    self.intensity_canvas.mpl_disconnect(self.__cid1)
                    self.intensity_canvas.mpl_disconnect(self.__cid2)
                    slope = 180 - np.rad2deg(np.arctan((roi.previous_point[1] - roi.start_point[1]) / (roi.previous_point[0] - roi.start_point[0])))
                    slope = np.mod(2 * slope, 360) / 2
                    dist = np.sqrt(((np.asarray(roi.previous_point) - np.asarray(roi.start_point))**2).sum())
                    ShowInfo(message=" Angle is {:.2f} \u00b0 \n Distance is {} pixels".format(slope, int(dist)), image=self.icons["square"], button_labels = ["OK"], fontsize=16)
                    for line in roi.lines:
                        line.remove()
                    self.intensity_canvas.draw()
                    self.compute_angle_button.configure(fg_color=orange[0])

    def define_variable_table(self, method:str) -> None:
        self.initialize_tables()
        self.clear_frame(self.variable_table_frame)
        self.variable_table_frame.configure(fg_color=gray[0])
        CTk.CTkLabel(master=self.variable_table_frame, text="\nVariables\n", width=230, font=CTk.CTkFont(size=16)).grid(row=0, column=0, columnspan=4, padx=(20, 20), pady=0)
        self.variable_table_switch = CTk.CTkSwitch(master=self.variable_table_frame, text="", progress_color=orange[0], command=self.variable_table_switch_callback, onvalue="on", offvalue="off", width=50)
        self.variable_table_switch.grid(row=1, column=0, padx=(20, 0), sticky="w")
        labels = ["Min", "Max"]
        for _, label in enumerate(labels):
            CTk.CTkLabel(master=self.variable_table_frame, text=label, text_color=text_color, font=CTk.CTkFont(weight="bold")).grid(row=1, column=_+2, padx=(0, 40), pady=(0, 5), sticky="e")
        if method in ["1PF", "4POLAR 2D"]:
            variables = ["\u03C1", "\u03C8"]
            vals = [(0, 180), (40, 180)]
        elif method in ["CARS", "SRS", "2PF"]:
            variables = ["\u03C1", "S2", "S4"]
            vals = [(0, 180), (0, 1), (-1, 1)]
        elif method == "SHG":
            variables = ["\u03C1", "S"]
            vals = [(0, 180), (-1, 1)]
        elif method == "4POLAR 3D":
            variables = ["\u03C1", "\u03C8", "\u03B7"]
            vals = [(0, 180), (40, 180), (0, 90)]
        self.variable_entries = []
        self.variable_min = [tk.StringVar() for _ in range(len(variables))]
        self.variable_max = [tk.StringVar() for _ in range(len(variables))]
        self.variable_display = [tk.IntVar(value=0) for _ in range(len(variables))]
        for _, (var, val) in enumerate(zip(variables, vals)):
            self.variable_min[_].set(str(val[0]))
            self.variable_max[_].set(str(val[1]))
            CTk.CTkCheckBox(master=self.variable_table_frame, text=None, variable=self.variable_display[_], width=30).grid(row=_+2, column=0, padx=(20, 0), sticky="w")
            CTk.CTkLabel(master=self.variable_table_frame, text=var).grid(row=_+2, column=1, sticky="w")
            self.variable_entries += [Entry(self.variable_table_frame, textvariable=self.variable_min[_], row=_+2, column=2, state="disabled"), Entry(self.variable_table_frame, textvariable=self.variable_max[_], row=_+2, column=3, state="disabled")]
        CTk.CTkLabel(master=self.variable_table_frame, text=" ", height=5, width=10).grid(row=len(variables)+2, column=0, columnspan=4)

    def method_dropdown_callback(self, method:str) -> None:
        self.define_variable_table(method)
        self.CD = Calibration(method)
        self.calib_dropdown.configure(values=self.CD.list(method), state="normal")
        self.calib_dropdown.set(self.CD.list(method)[0])
        self.calib_textbox.write(self.CD.name)
        if method in ["2PF", "SRS", "SHG", "CARS"]:
            self.calib_dropdown.configure(state="disabled")
        if method.startswith("4POLAR"):
            self.polar_dropdown.configure(state="normal")
            self.order = self.dict_polar[self.polar_dropdown.get()]
            window = ShowInfo(message="\n Perform: Select a beads file (*.tif)\n\n Load: Select a registration file (*.pyreg)\n\n Registration is performed with Whitelight.tif \n   which should be in the same folder as the beads file", image=self.icons["blur_circular"], button_labels=["Perform", "Load", "Cancel"], geometry=(420, 240))
            buttons = window.get_buttons()
            buttons[0].configure(command=lambda:self.perform_registration(window))
            buttons[1].configure(command=lambda:self.load_registration(window))
            buttons[2].configure(command=lambda:window.withdraw())
        else:
            self.polar_dropdown.configure(state="disabled")

    def pixelsperstick_spinbox_callback(self) -> None:
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (fig.type == "Sticks") and (self.datastack.name in fs):
                ax = fig.axes[0]
                for _, var in enumerate(self.datastack.vars):
                    if (var.name == fig.var) and ("contour" not in fs):
                        for collection in ax.collections:
                            collection.remove()
                        p = self.get_sticks(var, self.datastack)
                        vmin, vmax = self.get_variable(_)[1:]
                        p.set_clim([vmin, vmax])
                        ax.add_collection(p)
            if (fig.type == "Sticks") and (fig.var == "Rho_contour") and (self.datastack.name in fs):
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
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        filename = fd.askopenfilename(title="Select a beads file", initialdir=initialdir, filetypes=[("TIFF files", "*.tiff"), ("TIF files", "*.tif")])
        beadstack = self.define_stack(filename)
        self.filename_label.write("")
        dark = beadstack.compute_dark()
        intensity = np.sum((beadstack.values - dark) * (beadstack.values >= dark), axis=0)
        whitelight = cv2.imread(os.path.join(beadstack.folder, "Whitelight.tif"), cv2.IMREAD_GRAYSCALE)
        whitelight = cv2.threshold(whitelight, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(whitelight, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        filter = np.asarray([len(contour) >= 200 for contour in contours])
        contours = [contour.reshape((-1, 2)) for (contour, val) in zip(contours, filter) if val]
        centers, radius = [None] * len(contours), [None] * len(contours)
        for _, contour in enumerate(contours):
            centers[_], radius[_] = cv2.minEnclosingCircle(contour)
        centers = np.asarray(centers, dtype=np.int32)
        radius = int(round(max(radius))) + npix
        ind = np.arange(len(contours))
        Iul, Ilr = np.argmin(np.abs(centers[:, 0] + 1j * centers[:, 1])), np.argmax(np.abs(centers[:, 0] + 1j * centers[:, 1]))
        ind = np.delete(ind, [Iul, Ilr])
        Iur, Ill = np.argmin(centers[ind, 1]), np.argmax(centers[ind, 1])
        centers = centers[[Iul, ind[Iur], Ilr, ind[Ill]], :]
        ims = []
        for _ in range(4):
            xi, yi = centers[_, 0] - radius, centers[_, 1] - radius
            xf, yf = centers[_, 0] + radius, centers[_, 1] + radius
            im = intensity[yi:yf, xi:xf]
            im = (im / np.amax(im) * 255).astype(np.uint8)
            thresh = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            ims += [im * thresh]
        height, width = ims[0].shape
        sift=cv2.SIFT_create(500)
        keypoints0 = sift.detect(ims[0], None)
        points0 = np.asarray([kp.pt for kp in keypoints0])
        homographies, ims_ = [], [ims[0]]
        for im in ims[1:]:
            keypoints = sift.detect(im, None)
            points = np.asarray([kp.pt for kp in keypoints])
            p, p0 = find_matches(points, points0)
            homography = cv2.findHomography(p, p0, cv2.RANSAC)[0]
            homographies += [homography]
            ims_ += [cv2.warpPerspective(im, homography, (width, height))]
        reg_ims = [cv2.merge([_, ims[0], _]) for _ in ims_]
        fig, axs = plt.subplots(2, 2)
        fig.type, fig.var = "Calibration", None
        fig.canvas.manager.set_window_title("Quality of calibration: " + beadstack.name)
        reg_ims[2:4] = reg_ims[3:1:-1]
        titles = ["UL", "UR", "LL", "LR"]
        for im, title, ax in zip(reg_ims, titles, axs.ravel()):
            ax.imshow(im)
            ax.set_title(title)
            ax.set_axis_off()
        self.registration = {"name_beads": beadstack.name, "radius": radius, "centers": centers, "homographies": homographies}
        window = ShowInfo(message=" Are you okay with this registration?", button_labels=["Yes", u"Yes \u0026 Save", "No"], image=self.icons["blur_circular"], geometry=(380, 150))
        buttons = window.get_buttons()
        buttons[0].configure(command=lambda:self.yes_registration_callback(window, fig))
        buttons[1].configure(command=lambda:self.yes_save_registration_callback(window, fig, filename))
        buttons[2].configure(command=lambda:self.no_registration_callback(window, fig))

    def yes_registration_callback(self, window:CTk.CTkToplevel, fig:plt.Figure) -> None:
        plt.close(fig)
        window.withdraw()

    def yes_save_registration_callback(self, window:CTk.CTkToplevel, fig:plt.Figure, filename:str) -> None:
        with open(os.path.splitext(filename)[0] + ".pyreg", "wb") as f:
            pickle.dump(self.registration, f, protocol=pickle.HIGHEST_PROTOCOL)
        plt.close(fig)
        window.withdraw()

    def no_registration_callback(self, window:CTk.CTkToplevel, fig:plt.Figure) -> None:
        self.tform = []
        self.method.set("1PF")
        plt.close(fig)
        window.withdraw()

    def load_registration(self, window:CTk.CTkToplevel) -> None:
        window.withdraw()
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        filename = fd.askopenfilename(title="Select a registration file (*.pyreg)", initialdir=initialdir, filetypes=[("PYREG-files", "*.pyreg")])
        with open(filename, "rb") as f:
            self.registration = pickle.load(f)

    def define_stack(self, filename:str) -> Stack:
        stack_vals = cv2.imreadmulti(filename, [], cv2.IMREAD_ANYDEPTH)[1]
        nangle, h, w = np.asarray(stack_vals).shape
        a = np.asarray(stack_vals)
        if not np.issubdtype(a.dtype, np.integer):
            stack_vals = (65535 * (a - np.amin(a)) / np.ptp(a)).astype(np.uint16)
        else:
            stack_vals = a
        dict = {"values": stack_vals, "height": h, "width": w, "nangle": nangle, "display": "{:.0f}"}
        stack = Stack(filename)
        for key in dict:
            setattr(stack, key, dict[key])
        self.set_dark(stack)
        return stack

    def define_datastack(self, stack:Stack) -> DataStack:
        datastack = DataStack(stack)
        datastack.method = self.method.get()
        return datastack

    def open_file(self, filename:str) -> None:
        self.stack = self.define_stack(filename)
        if self.method.get().startswith("4POLAR"):
            self.stack = self.slice4polar(self.stack)
        if self.stack.nangle >= 2:
            self.stack_slider.configure(to=self.stack.nangle, number_of_steps=self.stack.nangle, state="normal")
        else:
            self.stack_slider.configure(state="disabled")
        self.filename_label.write(self.stack.name)
        self.tabview.set("Intensity")
        self.update()
        self.compute_intensity(self.stack)
        self.ilow_slider.configure(from_=np.amin(self.stack.intensity), to=np.amax(self.stack.intensity))
        self.ilow_slider.set(np.amin(self.stack.intensity))
        self.ilow.set(self.stack.display.format(np.amin(self.stack.intensity)))
        self.datastack = self.define_datastack(self.stack)
        if self.option.get().startswith("Mask"):
            self.mask = self.get_mask(self.datastack)
        self.ontab_intensity(update=False)
        self.ontab_thrsh(update=False)
        self.intensity_frame.update()
        self.thrsh_frame.update()

    def add_roi_callback(self) -> None:
        if hasattr(self, "stack"):
            self.thrsh_toolbar.mode = _Mode.NONE
            self.thrsh_toolbar._update_buttons_checked()
            self.tabview.set("Thresholding/Mask")
            self.update()
            self.add_roi_button.configure(fg_color=orange[1])
            hroi = ROI()
            self.__cid1 = self.thrsh_canvas.mpl_connect("motion_notify_event", lambda event: self.add_roi_motion_notify_callback(event, hroi))
            self.__cid2 = self.thrsh_canvas.mpl_connect("button_press_event", lambda event: self.add_roi_button_press_callback(event, hroi))

    def add_roi_motion_notify_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.thrsh_axis:
            x, y = event.xdata, event.ydata
            if (event.button is None or event.button == 1) and roi.lines:
                roi.lines[-1].set_data([roi.previous_point[0], x], [roi.previous_point[1], y])
                self.thrsh_canvas.draw()
            elif event.button == 3 and roi.lines:
                roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], color="w")]
                roi.previous_point = [x, y]
                roi.x.append(x)
                roi.y.append(y)
                self.thrsh_axis.add_line(roi.lines[-1])
                self.thrsh_canvas.draw()

    def add_roi_button_press_callback(self, event:MouseEvent, roi:ROI) -> None:
        if event.inaxes == self.thrsh_axis:
            x, y = event.xdata, event.ydata
            if (event.button == 1 or event.button == 3) and not event.dblclick:
                if not roi.lines:
                    roi.lines = [plt.Line2D([x, x], [y, y], marker='o', color="w")]
                    roi.start_point = [x, y]
                    roi.previous_point = roi.start_point
                    roi.x, roi.y = [x], [y]
                    self.thrsh_axis.add_line(roi.lines[0])
                    self.thrsh_canvas.draw()
                else:
                    roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], marker='o', color="w")]
                    roi.previous_point = [x, y]
                    roi.x.append(x)
                    roi.y.append(y)
                    self.thrsh_axis.add_line(roi.lines[-1])
                    self.thrsh_canvas.draw()
            elif ((event.button == 1 or event.button == 3) and event.dblclick) and roi.lines:
                roi.lines += [plt.Line2D([roi.previous_point[0], roi.start_point[0]], [roi.previous_point[1], roi.start_point[1]], marker='o', color="w")]
                self.thrsh_axis.add_line(roi.lines[-1])
                self.thrsh_canvas.mpl_disconnect(self.__cid1)
                self.thrsh_canvas.mpl_disconnect(self.__cid2)
                self.thrsh_canvas.draw()
                window = ShowInfo(message=" Add ROI?", image=self.icons["roi"], button_labels=["Yes", "No"], fontsize=16)
                buttons = window.get_buttons()
                buttons[0].configure(command=lambda:self.yes_add_roi_callback(window, roi))
                buttons[1].configure(command=lambda:self.no_add_roi_callback(window, roi))
                self.add_roi_button.configure(fg_color=orange[0])

    def yes_add_roi_callback(self, window:CTk.CTkToplevel, roi:ROI) -> None:
        vertices = np.asarray([roi.x, roi.y])
        indx = self.datastack.rois[-1]["indx"] + 1 if self.datastack.rois else 1
        self.datastack.rois += [{"indx": indx, "label": (roi.x[0], roi.y[0]), "vertices": vertices, "ILow": self.ilow.get(), "name": "", "group": "", "select": True}]
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_canvas.draw()
        self.ontab_intensity()
        self.ontab_thrsh()
        if hasattr(self, "manager"):
            self.manager.update_manager(self.datastack.rois)

    def no_add_roi_callback(self, window:CTk.CTkToplevel, roi:ROI) -> None:
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_canvas.draw()

    def get_mask(self, datastack:DataStack) -> np.ndarray:
        mask = np.ones((datastack.height, datastack.width))
        if self.option.get().startswith("Mask"):
            mask_name = os.path.join(self.maskfolder, datastack.name + ".png")
            if os.path.isfile(mask_name):
                im_binarized = np.asarray(Image.open(mask_name), dtype=np.float64)
                mask = im_binarized / np.amax(im_binarized)
            else:
                ShowInfo(message=f" The corresponding mask for {datastack.name} could not be found\n Continuing without mask...", image=self.icons["layers_clear"], buttons_labels=["OK"])
            if hasattr(self, "mask"):
                self.mask = mask
        return mask

    def analysis_callback(self) -> None:
        if self.option.get() == "Previous analysis":
            self.analysis_button.configure(image=self.icons["pause"])
            self.plot_data(self.datastack)
            self.analysis_button.configure(image=self.icons["play"])
        elif hasattr(self, "stack"):
            self.analysis_button.configure(image=self.icons["pause"])
            self.tabview.set("Intensity")
            self.update()
            if self.option.get().endswith("(manual)"):
                self.analyze_stack(self.datastack)
                if self.filelist:
                    self.indxlist += 1
                    if self.indxlist < len(self.filelist):
                        self.open_file(self.filelist[self.indxlist])
                        self.initialize_noise()
                    else:
                        self.indxlist = 0
                        self.open_file(self.filelist[0])
                        ShowInfo(message=" End of list", image=self.icons["check_circle"], button_labels=["OK"], fontsize=16)
                        self.initialize()
                self.analysis_button.configure(image=self.icons["play"])
            elif self.option.get().endswith("(auto)"):
                for file in self.filelist:
                    self.open_file(file)
                    self.analyze_stack(self.datastack)
                self.analysis_button.configure(image=self.icons["play"])
                self.open_file(self.filelist[0])
                ShowInfo(message=" End of list", image=self.icons["check_circle"], button_labels=["OK"], fontsize=16)
                self.initialize()

    def stack_slider_callback(self, value:str) -> None:
        self.stack_slider_label.configure(text=int(value))
        if value == 0:
            self.stack_slider_label.configure(text="T")
        if self.method.get().startswith("4POLAR"):
            labels = ["T", 0, 45, 90, 135]
            self.stack_slider_label.configure(text=labels[int(value)])
        self.ontab_intensity()

    def ilow_slider_callback(self, value:str) -> None:
        if hasattr(self, "stack"):
            self.ilow.set(self.stack.display.format(value))
            if hasattr(self, "edge_contours"):
                self.compute_edges()
            self.ontab_thrsh()

    def ilow2slider_callback(self, event:tk.Event) -> None:
        if event and hasattr(self, "stack"):
            self.ilow_slider.set(float(self.ilow.get()))
            if hasattr(self, "edge_contours"):
                self.compute_edges()
            self.ontab_thrsh()

    def intensity_callback(self, event:tk.Event) -> None:
        if event and hasattr(self, "stack"):
            if (self.method.get() == "1PF") and (float(self.dark.get()) < 480):
                self.dark.set(self.stack.display.format(self.calculated_dark))
            self.compute_intensity(self.stack)
            if hasattr(self, "datastack"):
                self.datastack.intensity = self.stack.intensity
            self.ontab_intensity(update=False)
            self.ontab_thrsh(update=False)

    def rotation_callback(self, event:tk.Event) -> None:
        if event:
            self.ontab_intensity(update=False)

    def transparency_slider_callback(self, value:float) -> None:
        if value <= 0.001:
            self.transparency_slider.set(0.001)
        self.ontab_thrsh()

    def ontab_intensity(self, update:bool=True) -> None:
        intensity = self.stack.intensity if hasattr(self, "stack") else self.datastack.intensity if hasattr(self, "datastack") else []
        if hasattr(self, "stack") or hasattr(self, "datastack"):
            if self.stack_slider.get() == 0:
                field = intensity
                vmin, vmax = np.amin(intensity), np.amax(intensity)
            elif hasattr(self, "stack") and (self.stack_slider.get() <= self.stack.nangle):
                field = self.stack.values[int(self.stack_slider.get())-1]
                vmin, vmax = np.amin(self.stack.values), np.amax(self.stack.values)
            field_im = adjust(field, self.contrast_intensity_slider.get(), vmin, vmax)
            if int(self.rotation[1].get()) != 0:
                field_im = rotate(field_im, int(self.rotation[1].get()), reshape=False, mode="constant", cval=vmin)
            if update:
                self.intensity_im.set_data(field_im)
            else:
                self.intensity_axis.clear()
                self.intensity_axis.set_axis_off()
                self.intensity_im = self.intensity_axis.imshow(field_im, cmap="gray", interpolation="nearest")
                self.intensity_frame.update()
            self.intensity_im.set_clim(vmin, vmax)
            self.clear_patches(self.intensity_axis, self.intensity_canvas)
            if hasattr(self, "datastack"):
                self.add_patches(self.datastack, self.intensity_axis, self.intensity_canvas)
            self.intensity_canvas.draw()

    def ontab_thrsh(self, update:bool=True) -> None:
        if hasattr(self, "stack"):
            field = self.stack.intensity.copy()
            if self.option.get().startswith("Mask"):
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
                self.thrsh_im = self.thrsh_axis.imshow(field_im, cmap=self.thrsh_colormap, alpha=alphadata, interpolation="nearest")
                self.thrsh_frame.update()
            self.thrsh_im.set_clim(vmin, vmax)
            self.clear_patches(self.thrsh_axis, self.thrsh_fig.canvas)
            if hasattr(self, "plot_edges"):
                for edge in self.plot_edges:
                    edge.pop(0).remove()
                delattr(self, "plot_edges")
            if hasattr(self, "datastack"):
                self.add_patches(self.datastack, self.thrsh_axis, self.thrsh_fig.canvas, rotation=False)
            if hasattr(self, "edge_contours"):
                self.plot_edges = []
                for contour in self.edge_contours:
                    self.plot_edges += [self.thrsh_axis.plot(contour[:, 0], contour[:, 1], 'b-', lw=1)]
            self.thrsh_canvas.draw()

    def compute_intensity(self, stack:Stack) -> None:
        dark = float(self.dark.get())
        bin = [self.bin_spinboxes[_].get() for _ in range(2)]
        stack.intensity = stack.get_intensity(dark=dark, bin=bin)

    def set_dark(self, stack:Stack) -> int:
        dark = stack.compute_dark()
        self.calculated_dark = dark
        self.calculated_dark_label.configure(text="Calculated dark value = " + stack.display.format(dark))
        if self.dark_switch.get() == "off":
            self.dark.set(stack.display.format(dark))

    def get_variable(self, indx:int) -> Tuple[bool, float, float]:
        display = self.variable_display[indx].get()
        vmin, vmax = float(self.variable_min[indx].get()), float(self.variable_max[indx].get())
        return display, vmin, vmax

    def plot_histo(self, var:Variable, datastack:DataStack, roi_map:np.ndarray, roi:ROI=None) -> None:
        display, vmin, vmax = self.get_variable(var.indx % 10)
        if display and (self.show_table[2].get() or self.save_table[2].get()):
            for htype in var.type_histo:
                fig = plt.figure(figsize=self.figsize)
                fig.type, fig.var = "Histogram", var.name
                suffix = "for ROI " + str(roi["indx"]) if roi is not None else ""
                fig.canvas.manager.set_window_title(var.name + " Histogram " + suffix + ": " + self.datastack.name)
                mask = (roi_map == roi["indx"]) if roi is not None else (roi_map == 1)
                var.histo(mask, htype=htype, vmin=vmin, vmax=vmax, colorblind=self.colorblind_checkbox.get(), rotation=float(self.rotation[1].get()), nbins=int(self.histo_nbins.get()))
                if self.save_table[2].get():
                    suffix = "_perROI_" + str(roi["indx"]) if roi is not None else ""
                    filename = datastack.filename + "_Histo" + var.name + suffix
                    plt.savefig(filename + ".tif", bbox_inches="tight")
                if not self.show_table[2].get():
                    plt.close(fig)

    def plot_histos(self, var:Variable, datastack:DataStack, roi_map:np.ndarray=None) -> None:
        if self.per_roi.get():
            for roi in datastack.rois:
                if roi["select"]:
                    self.plot_histo(var, datastack, roi_map, roi=roi)
        else:
            self.plot_histo(var, datastack, roi_map)

    def merge_histos(self):
        self.show_table[2].select()
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        folder = fd.askdirectory(title="Select a directory", initialdir=initialdir)
        goodvars = ["Rho", "Rho_contour", "Psi", "S2", "S4", "S_SHG", "Eta", "Int"]
        data, vars = {}, []
        if folder:
            foldername = os.path.basename(folder)
            for filename in os.listdir(folder):
                if filename.endswith((".mat")):
                    tempdata = loadmat(os.path.join(folder, filename))
                    tempvars = list(tempdata.keys())
                    tempvars = [tempvar for tempvar in tempvars if tempvar in goodvars]
                    for tempvar in tempvars:
                        if (tempvar in vars):
                            data[tempvar] = np.concatenate((data[tempvar], tempdata[tempvar]), axis=None)
                        else:
                            vars += [tempvar]
                            data[tempvar] = tempdata[tempvar]
            if self.extension_table[2].get():
                dict_ = {"polarimetry": self.method.get(), "folder": folder}
                for var in vars:
                    dict_.update({var: data[var]})
                filename = os.path.join(folder, foldername + "_ConcatHisto.mat")
                savemat(filename, dict_)
            vars.remove("Int")
            for var in vars:
                var_ = Variable(var, values=data[var])
                display, vmin, vmax = self.get_variable(var_.indx % 10)
                if display:
                    for htype in var_.type_histo:
                        fig = plt.figure(figsize=self.figsize)
                        fig.type, fig.var = "Histogram", var_.name
                        fig.canvas.manager.set_window_title(var_.name + " Concatenated Histogram ")
                        var_.histo(htype=htype, vmin=vmin, vmax=vmax, colorblind=self.colorblind_checkbox.get(), rotation=float(self.rotation[1].get()), nbins=int(self.histo_nbins.get()))
                        if self.save_table[2].get():
                            suffix = "(0-90)" if htype == "polar3" else ""
                            filename = os.path.join(folder, foldername + "_ConcatHisto" + suffix + var_.name) 
                            plt.savefig(filename + ".tif", bbox_inches="tight")
        if len(vars) == 0:
            ShowInfo(" Error in the selected folder", image=self.icons["blur_circular"], button_labels=["OK"])

    def add_intensity(self, intensity:np.ndarray, ax:plt.Axes) -> None:
        vmin, vmax = np.amin(intensity), np.amax(intensity)
        field = adjust(intensity, self.contrast_intensity_slider.get(), vmin, vmax)
        if int(self.rotation[1].get()) != 0:
            field = rotate(field, int(self.rotation[1].get()), reshape=False, mode="constant", cval=vmin)
        ax.imshow(field, cmap="gray", interpolation="nearest", vmin=vmin, vmax=vmax)

    def add_patches(self, datastack:DataStack, ax:plt.Axes, canvas:Union[FigureCanvasBase, FigureCanvasTkAgg], rotation:bool=True) -> None:
        if len(datastack.rois):
            for roi in datastack.rois:
                if roi["select"]:
                    vertices = roi["vertices"]
                    coord = roi["label"][0], roi["label"][1]
                    if (float(self.rotation[1].get()) != 0) and rotation:
                        theta = np.deg2rad(float(self.rotation[1].get()))
                        cosd, sind = np.cos(theta), np.sin(theta)
                        x0, y0 = datastack.width / 2, datastack.height / 2
                        coord = x0 + (coord[0] - x0) * cosd + (coord[1] - y0) * sind, y0 - (coord[0] - x0) * sind + (coord[1] - y0) * cosd
                        vertices = np.asarray([x0 + (vertices[0] - x0) * cosd + (vertices[1] - y0) * sind, y0 - (vertices[0] - x0) * sind + (vertices[1] - y0) * cosd])
                    ax.add_patch(Polygon(vertices.T, facecolor="none", edgecolor="white"))
                    ax.text(coord[0], coord[1], str(roi["indx"]), color="w")
            canvas.draw()

    def plot_composite(self, var:Variable, datastack:DataStack) -> None:
        display, vmin, vmax = self.get_variable(var.indx % 10)
        if display and (self.show_table[0].get() or self.save_table[0].get()):
            fig = plt.figure(figsize=self.figsize)
            fig.type, fig.var = "Composite", var.name
            fig.canvas.manager.set_window_title(var.name + " Composite: " + datastack.name)
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            datastack.plot_intensity(contrast=self.contrast_intensity_slider.get(), rotation=int(self.rotation[1].get()))
            h = var.imshow(vmin, vmax, colorblind=self.colorblind_checkbox.get(), rotation=int(self.rotation[1].get()))
            if self.colorbar_checkbox.get():
                ax_divider = make_axes_locatable(ax)
                cax = ax_divider.append_axes("right", size="7%", pad="2%")
                fig.colorbar(h, cax=cax)
            if self.save_table[0].get():
                suffix = "_" + var.name + "Composite"
                plt.savefig(datastack.filename + suffix + ".tif", bbox_inches='tight')
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
                    fig_.type, fig_.var = "Individual Fit", None
                    fig_.canvas.manager.set_window_title("Individual Fit : " + self.datastack.name)
                    signal = self.datastack.field[:, y, x]
                    signal_fit = self.datastack.field_fit[:, y, x]
                    indx = np.arange(1, self.stack.nangle + 1)
                    rho = np.mod(2 * (self.datastack.vars[0].values[y, x] + float(self.rotation[1].get())), 360) / 2
                    title = self.datastack.vars[0].latex + " = " + "{:.2f}".format(rho) + ", "
                    for var in self.datastack.vars:
                        if var.name != "Rho":
                            title += var.latex + " = " + "{:.2f}".format(var.values[y, x]) + ", "
                    titles = [title[:-2]]
                    titles += ["$\chi_2$ = " + "{:.2f}".format(self.datastack.chi2[y, x]) + ",   $I$ =  " + self.datastack.display.format(self.datastack.intensity[y, x])]
                    ylabels = ["counts", "residuals"]
                    axs[0].plot(indx, signal, "*", indx, signal_fit, "r-", lw=2)
                    axs[1].plot(indx, signal - signal_fit, "+", indx, 2 * np.sqrt(signal_fit), "r-", indx, -2 * np.sqrt(signal_fit), "r-", lw=2)
                    polardir = -1 if self.polar_dir.get() == "clockwise" else 1 
                    def indx2alpha(k):
                        return polardir * 180 / self.stack.nangle * (k - 1) + float(self.offset_angle.get())
                    def alpha2indx(a):
                        return polardir * self.stack.nangle / 180 * (a - float(self.offset_angle.get())) + 1
                    for title, ylabel, ax_ in zip(titles, ylabels, axs):
                        ax_.set_xlabel("slice", fontsize=14)
                        ax_.set_ylabel(ylabel, fontsize=14)
                        ax_.set_xlim((1, self.datastack.nangle))
                        ax_.set_xticks(indx[::2], minor=True)
                        ax_.set_title(title, fontsize=16)
                        secax = ax_.secondary_xaxis("top", functions=(indx2alpha, alpha2indx))
                        secax.set_xlabel(r"$\alpha$")
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
        stick_colors = np.mod(2 * (data_ + float(self.rotation[1].get())), 360) / 2 if var.name == "Rho" else data_
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
            fig.type, fig.var = "Sticks", var.name
            fig.canvas.manager.set_window_title(var.name + " Sticks: " + datastack.name)
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            datastack.plot_intensity(contrast=self.contrast_intensity_slider.get(), rotation=int(self.rotation[1].get()))
            p = self.get_sticks(var, datastack)
            p.set_clim([vmin, vmax])
            ax.add_collection(p)
            if self.colorbar_checkbox.get():
                ax_divider = make_axes_locatable(ax)
                cax = ax_divider.append_axes("right", size="7%", pad="2%")
                fig.colorbar(p, cax=cax)
            if self.save_table[1].get():
                suffix = "_" + var.name + "Sticks"
                plt.savefig(datastack.filename + suffix + ".tif", bbox_inches='tight')
            if not self.show_table[1].get():
                plt.close(fig)

    def plot_intensity(self, datastack:DataStack) -> None:
        if self.show_table[3].get() or self.save_table[3].get():
            fig = plt.figure(figsize=self.figsize)
            fig.type, fig.var = "Intensity", None
            fig.canvas.manager.set_window_title("Intensity: " + datastack.name)
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            datastack.plot_intensity(contrast=self.contrast_intensity_slider.get(), rotation=int(self.rotation[1].get()))
            self.add_patches(datastack, ax, fig.canvas)
            if self.edge_detection_switch.get() == "on":
                for contour in self.edge_contours:
                    angles = np.mod(2 * angle_edge(contour)[0], 360) / 2
                    cmap = cc.m_colorwheel if self.colorblind_checkbox.get() else "hsv"
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
                    cax = ax_divider.append_axes("right", size="7%", pad="2%")
                    fig.colorbar(p, cax=cax)
            if self.save_table[3].get():
                suffix = "_Intensity"
                plt.savefig(datastack.filename + suffix + ".tif", bbox_inches='tight')
            if not self.show_table[3].get():
                plt.close(fig)
    
    def per_roi_callback(self):
        if hasattr(self, "datastack"):
            if len(self.datastack.rois) >= 2:
                figs = list(map(plt.figure, plt.get_fignums()))
                redraw = False
                for fig in figs:
                    fs = fig.canvas.manager.get_window_title()
                    if (fig.type == "Histogram") and (self.datastack.name in fs) :
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
                if roi["select"]:
                    self.save_mat(datastack, roi_map, roi=roi)
        else:
            self.save_mat(datastack, roi_map, roi=[])
        if self.extension_table[0].get():
            filename = self.stack.filename + ".pykl"
            datastack_ = copy.copy(datastack)
            delattr(datastack_, "added_vars")
            for roi in datastack_.rois:
                roi["select"] = True
            window = ShowInfo(message=" Compressing and saving data...", image=self.icons["save"], geometry=(350, 80))
            window.update()
            with bz2.BZ2File(filename, "wb") as f:
                cPickle.dump(datastack_, f)
            window.withdraw()
        if self.extension_table[3].get():
            suffix_excel = "_Stats.xlsx" if self.edge_detection_switch.get() == "off" else "_Stats_c.xlsx"
            if self.filelist:
                filename = os.path.join(self.stack.folder, os.path.basename(self.stack.folder) + suffix_excel)
                title = os.path.basename(self.stack.folder)
            else:
                filename = self.stack.filename + suffix_excel
                title = self.stack.name
            if os.path.exists(filename):
                workbook = openpyxl.load_workbook(filename = filename)
            else:
                workbook = openpyxl.Workbook()
            worksheet = workbook.active
            worksheet.title = title
            if not os.path.exists(filename):
                title = ["File", "ROI", "name", "group", "MeanRho", "StdRho", "MeanDeltaRho"]
                worksheet.append(title + self.return_vecexcel(datastack, roi_map)[1])
            if self.per_roi.get():
                for roi in datastack.rois:
                    if roi["select"]:
                        worksheet.append(self.return_vecexcel(datastack, roi_map, roi=roi)[0])
            else:
                worksheet.append(self.return_vecexcel(datastack, roi_map, roi=[])[0])
            workbook.save(filename)
        if self.extension_table[4].get():
            filename = self.stack.filename + ".gif"
            images = []
            vmin, vmax = np.amin(self.stack.values), np.amax(self.stack.values)
            for _ in range(self.stack.nangle):
                field = self.stack.values[_]
                im = adjust(field, self.contrast_intensity_slider.get(), vmin, vmax)
                if int(self.rotation[1].get()) != 0:
                    im = rotate(im, int(self.rotation[1].get()), reshape=False, mode="constant", cval=vmin)
                if hasattr(self, "xylim"):
                    im = im[int(self.xylim[2].get()):int(self.xylim[3].get()), int(self.xylim[0].get()):int(self.xylim[1].get())]
                im = (255 * im / vmax).astype(np.uint8)
                images.append(Image.fromarray(im, mode='P'))
            images[0].save(filename, save_all=True, append_images=images[1:], optimize=False, duration=200, loop=0)

    def return_vecexcel(self, datastack:DataStack, roi_map:np.ndarray, roi:dict={}) -> Tuple[List[float], List[str]]:
        mask = (roi_map == roi["indx"]) if roi else (roi_map == 1)
        ilow = float(roi["ILow"]) if roi else float(self.ilow.get())
        rho = datastack.vars[0].values
        data_vals = np.mod(2 * (rho[mask * np.isfinite(rho)] + float(self.rotation[1].get())), 360) / 2
        n = data_vals.size
        meandata = circularmean(data_vals)
        deltarho = wrapto180(2 * (data_vals - meandata)) / 2
        title = []
        if roi:
            results = [self.stack.name, roi["indx"], roi["name"], roi["group"], meandata, np.std(deltarho), np.mean(deltarho)]
        else:
            results = [self.stack.name, "all", "", "", meandata, np.std(deltarho), np.mean(deltarho)]
        if self.edge_detection_switch.get() == "on":
            title += ["MeanRho_c_180", "StdRho_c_180", "MeanDeltaRho_c_180", "MeanRho_c_90", "StdRho_c_90", "MeanDeltaRho_c_90"]
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
            if var.name != "Rho_contour":
                data_vals = var.values[mask * np.isfinite(rho)]
                meandata = np.mean(data_vals)
                title += ["Mean" + var.name, "Std" + var.name]
                results += [meandata, np.std(data_vals)]
        data_vals = datastack.added_vars[2].values[mask * np.isfinite(rho)]
        meandata, stddata = np.mean(data_vals), np.std(data_vals)
        title += ["MeanInt", "StdInt", "TotalInt", "ILow", "N"]
        results += [meandata, stddata, meandata * self.stack.nangle, ilow, n]
        if self.method.get() in ["1PF", "4POLAR 2D", "4POLAR 3D"]:
            title += ["Calibration"]
            results += [self.CD.name]
        if self.method.get().startswith("4POLAR"):
            title += ["4POLAR angles"]
            results += [self.polar_dropdown.get()]
        title += ["dark", "offset", "polarization", "bin width", "bin height"]
        results += [float(self.dark.get()), float(self.offset_angle.get()), self.polar_dir.get(), self.bin_spinboxes[0].get(), self.bin_spinboxes[1].get()]
        return results, title

    def save_mat(self, datastack:DataStack, roi_map:np.ndarray, roi:dict={}) -> None:
        if self.extension_table[2].get():
            mask = (roi_map == roi["indx"]) if roi else (roi_map == 1)
            dict_ = {"polarimetry": self.method.get(), "file": datastack.filename, "dark": datastack.dark}
            for var in datastack.vars:
                data = var.values[mask * np.isfinite(var.values)]
                dict_.update({var.name: data})
            for var in datastack.added_vars:
                data = var.values[mask * np.isfinite(var.values)]
                dict_.update({var.name: data})
            suffix = "_ROI" + str(roi["indx"]) if roi else ""
            filename = datastack.filename + suffix + ".mat"
            savemat(filename, dict_)

    def compute_roi_map(self, datastack:DataStack) -> Tuple[np.ndarray, np.ndarray]:
        shape = (datastack.height, datastack.width)
        if len(datastack.rois):
            Y, X = np.mgrid[:datastack.height, :datastack.width]
            points = np.vstack((X.flatten(), Y.flatten())).T
            roi_map = np.zeros(shape, dtype=np.int32)
            roi_ilow_map = np.zeros(shape, dtype=np.float64)
            for roi in datastack.rois:
                if roi["select"]:
                    patch= Polygon(roi["vertices"].T)
                    roi_map[patch.contains_points(points).reshape(shape)] = int(roi["indx"]) if self.per_roi.get() else 1
                    roi_ilow_map[patch.contains_points(points).reshape(shape)] = float(roi["ILow"])
        else:
            roi_map = np.ones(shape, dtype=np.int32)
            roi_ilow_map = np.ones(shape, dtype=np.float64) * np.float64(self.ilow.get())
            self.per_roi.deselect()
        mask = self.get_mask(datastack)
        if self.edge_detection_switch.get() == "on" and self.edge_method == "download":
            mask *= self.edge_mask
        mask *= (datastack.intensity >= roi_ilow_map) * (roi_map > 0)
        return roi_map, (mask != 0)

    def slice4polar(self, stack:Stack) -> Stack:
        if hasattr(self, "registration"):
            radius = np.asarray(self.registration["radius"]).item()
            centers = self.registration["centers"]
            homographies = self.registration["homographies"]
            stack_ = Stack(stack.filename)
            stack_.display = stack.display
            stack_.nangle, stack_.height, stack_.width = 4, 2 * radius, 2 * radius
            stack_.values = np.zeros((stack_.nangle, stack_.height, stack_.width))
            ims = []
            for _ in range(stack_.nangle):
                xi, yi = centers[_, 0] - radius, centers[_, 1] - radius
                xf, yf = centers[_, 0] + radius, centers[_, 1] + radius
                ims += [stack.values[0, yi:yf, xi:xf].reshape((stack_.height, stack_.width))]
            ims_reg = [ims[0]]
            ims_reg += [cv2.warpPerspective(im, homography, (stack_.width, stack_.height)) for im, homography in zip(ims[1:], homographies)]
            for it in range(stack_.nangle):
                stack_.values[self.order[it]] = ims_reg[it]
            return stack_
        else:
            ShowInfo(message=" No registration", image=self.icons["blur_circular"], button_labels=["OK"], fontsize=16)
            self.method.set("1PF")

    def analyze_stack(self, datastack:DataStack) -> None:
        chi2threshold = 500
        shape = (self.stack.height, self.stack.width)
        roi_map, mask = self.compute_roi_map(datastack)
        datastack.dark = float(self.dark.get())
        datastack.method = self.method.get()
        field = self.stack.values - datastack.dark - float(self.removed_intensity)
        field = field * (field >= 0)
        if self.method.get() == "CARS":
            field = np.sqrt(field)
        elif self.method.get().startswith("4POLAR"):
            field[[1, 2]] = field[[2, 1]]
        bin_shape = np.asarray([self.bin_spinboxes[_].get() for _ in range(2)], dtype=np.uint8)
        if sum(bin_shape) != 2:
            bin = np.ones(bin_shape)
            for _ in range(self.stack.nangle):
                field[_] = convolve2d(field[_], bin, mode="same") / (bin_shape[0] * bin_shape[1])
        if self.method.get() in ["1PF", "CARS", "SRS", "SHG", "2PF"]:
            polardir = -1 if self.polar_dir.get() == "clockwise" else 1
            alpha = polardir * np.linspace(0, 180, self.stack.nangle, endpoint=False) + float(self.offset_angle.get())
            e2 = np.exp(2j * np.deg2rad(alpha[:, np.newaxis, np.newaxis]))
            a0 = np.mean(field, axis=0)
            a0[a0 == 0] = np.nan
            a2 = 2 * np.mean(field * e2, axis=0)
            field_fit = a0[np.newaxis, :, :] + (a2[np.newaxis, :, :] * e2.conj()).real
            a2 = np.divide(a2, a0, where=np.all((a0!=0, np.isfinite(a0)), axis=0))
            if self.method.get() in ["CARS", "SRS", "SHG", "2PF"]:
                e4 = e2**2
                a4 = 2 * np.mean(field * e4, axis=0)
                field_fit += (a4[np.newaxis, :, :] * e4.conj()).real
                a4 = np.divide(a4, a0, where=np.all((a0!=0, np.isfinite(a0)), axis=0))
            chi2 = np.mean(np.divide((field - field_fit)**2, field_fit, where=np.all((field_fit!=0, np.isfinite(field_fit)), axis=0)), axis=0)
        elif self.method.get() == "4POLAR 3D":
            mat = np.einsum("ij,jmn->imn", self.CD.invKmat_3D, field)
            s = mat[0] + mat[1] + mat[2]
            pxy = np.divide(mat[0] - mat[1], s, where=np.all((s!=0, np.isfinite(s)), axis=0)).reshape(shape)
            puv = np.divide(2 * mat[3], s, where=np.all((s!=0, np.isfinite(s)), axis=0)).reshape(shape)
            pzz = np.divide(mat[2], s, where=np.all((s!=0, np.isfinite(s)), axis=0)).reshape(shape)
            lam = ((1 - (pzz + np.sqrt(puv**2 + pxy**2))) / 2).reshape(shape)
            a0 = np.mean(field, axis=0) / 4
            a0[a0 == 0] = np.nan
        elif self.method.get() == "4POLAR 2D":
            mat = np.einsum("ij,jmn->imn", self.CD.invKmat_2D, field)
            s = mat[0] + mat[1] + mat[2]
            pxy = np.divide(mat[0] - mat[1], s, where=np.all((s!=0, np.isfinite(s)), axis=0)).reshape(shape)
            puv = np.divide(2 * mat[3], s, where=np.all((s!=0, np.isfinite(s)), axis=0)).reshape(shape)
            lam = ((1 - (pzz + np.sqrt(puv**2 + pxy**2))) / 2).reshape(shape)
            a0 = np.mean(field, axis=0) / 4
            a0[a0 == 0] = np.nan
        rho_ = Variable("Rho", datastack=datastack)
        if self.method.get() == "1PF":
            mask *= (np.abs(a2) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            a2_vals = np.moveaxis(np.asarray([a2.real[mask].flatten(), a2.imag[mask].flatten()]), 0, -1)
            rho, psi = np.moveaxis(interpn(self.CD.xy, self.CD.RhoPsi, a2_vals), 0, 1)
            ixgrid = mask.nonzero()
            rho_.values[ixgrid] = rho
            rho_.values[np.isfinite(rho_.values)] = np.mod(2 * (rho_.values[np.isfinite(rho_.values)] + float(self.rotation[0].get())), 360) / 2 
            psi_ = Variable("Psi", datastack=datastack)
            psi_.values[ixgrid] = psi
            mask *= np.isfinite(rho_.values) * np.isfinite(psi_.values)
            datastack.vars = [rho_, psi_]
        elif self.method.get() in ["CARS", "SRS", "2PF"]:
            mask *= (np.abs(a2) < 1) * (np.abs(a4) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho_.values[mask] = np.rad2deg(np.angle(a2[mask])) / 2
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            s2_ = Variable("S2", datastack=datastack)
            s2_.values[mask] = 1.5 * np.abs(a2[mask])
            s4_ = Variable("S4", datastack=datastack)
            s4_.values[mask] = 6 * np.abs(a4[mask]) * np.cos(4 * (0.25 * np.angle(a4[mask]) - np.deg2rad(rho_.values[mask])))
            datastack.vars = [rho_, s2_, s4_]
        elif self.method.get() == "SHG":
            mask *= (np.abs(a2) < 1) * (np.abs(a4) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho_.values[mask] = np.rad2deg(np.angle(a2[mask])) / 2
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            s_shg_ = Variable("S_SHG", datastack=datastack)
            s_shg_.values[mask] = -0.5 * (np.abs(a4[mask]) - np.abs(a2[mask])) / (np.abs(a4[mask]) + np.abs(a2[mask])) - 0.65
            datastack.vars = [rho_, s_shg_]
        elif self.method.get() == "4POLAR 3D":
            mask *= (lam < 1/3) * (lam > 0) * (pzz > lam)
            rho_.values[mask] = 0.5 * np.rad2deg(np.arctan2(puv[mask], pxy[mask]))
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable("Psi", datastack=datastack)
            psi_.values[mask] = 2 * np.rad2deg(np.arccos((-1 + np.sqrt(9 - 24 * lam[mask])) / 2))
            eta_ = Variable("Eta", datastack=datastack)
            eta_.values[mask] = np.rad2deg(np.arccos(np.sqrt((pzz[mask] - lam[mask]) / (1 - 3 * lam[mask]))))
            datastack.vars = [rho_, psi_, eta_]
        elif self.method.get() == "4POLAR 2D":
            mask *= (lam < 1/3) * (lam > 0)
            rho_.values[mask] = 0.5 * np.rad2deg(np.arctan2(puv[mask], pxy[mask]))
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable("Psi", datastack=datastack)
            psi_.values[mask] = 2 * np.rad2deg(np.arccos((-1 + np.sqrt(9 - 24 * lam[mask])) / 2))
            datastack.vars = [rho_, psi_]
        a0[np.logical_not(mask)] = np.nan
        X, Y = np.meshgrid(np.arange(datastack.width), np.arange(datastack.height))
        X, Y = X.astype(np.float64), Y.astype(np.float64)
        X[np.logical_not(mask)] = np.nan
        Y[np.logical_not(mask)] = np.nan
        X_, Y_, Int_ = Variable("X", datastack=datastack), Variable("Y", datastack=datastack), Variable("Int", datastack=datastack)
        X_.indx, Y_.indx, Int_.indx = 1, 2, 3
        X_.values, Y_.values, Int_.values = X, Y, a0
        datastack.added_vars = [X_, Y_, Int_]
        if self.edge_detection_switch.get() == "on":
            rho_ct = Variable("Rho_contour", datastack=datastack)
            vals = self.define_rho_ct(self.edge_contours)
            filter = np.isfinite(rho_.values) * np.isfinite(vals)
            rho_ct.values[filter] = np.mod(2 * (rho_.values[filter] - vals[filter]), 360) / 2
            datastack.vars += [rho_ct]
        if not self.method.get().startswith("4POLAR"):
            field[:, np.logical_not(mask)] = np.nan
            field_fit[:, np.logical_not(mask)] = np.nan
            chi2[np.logical_not(mask)] = np.nan
            datastack.field = field
            datastack.field_fit = field_fit
            datastack.chi2 = chi2
        self.datastack = datastack
        self.plot_data(datastack, roi_map=roi_map)
        self.save_data(datastack, roi_map=roi_map)

if __name__ == "__main__":
    app = Polarimetry()
    app.mainloop()