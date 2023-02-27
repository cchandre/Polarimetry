import tkinter as tk
import tksheet
from tkinter import filedialog as fd
from tkinter.messagebox import showerror
import customtkinter as CTk
import os
import sys
import pathlib
import bz2
import pickle
import _pickle as cPickle
import copy
import webbrowser
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.signal import convolve2d, savgol_filter
from scipy.interpolate import interpn
from scipy.ndimage import rotate
from scipy.linalg import norm
from scipy.io import savemat, loadmat
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.collections import PolyCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.axes_grid1 import make_axes_locatable
import colorcet as cc
from PIL import Image
from skimage import exposure
import cv2
import openpyxl
from itertools import permutations, chain
from datetime import date
import copy

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

button_size = (160, 40)
orange = ("#FF7F4F", "#ffb295")
text_color = "black"
red = ("#B54D42", "#d5928b")
green = ("#ADD1AD", "#cee3ce")
gray = ("#7F7F7F", "#A6A6A6")

geometry_info = lambda dim: f"{dim[0]}x{dim[1]}+400+300"

class Polarimetry(CTk.CTk):
    __version__ = "2.4.2"

    dict_versions = {"2.1": "December 5, 2022", "2.2": "January 22, 2023", "2.3": "January 28, 2023", "2.4": "February 2, 2023", "2.4.1": "February 25, 2023", "2.4.2": "February 27, 2023"}

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

    def __init__(self):
        super().__init__()

## MAIN
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        delx = self.winfo_screenwidth() // 10
        dely = self.winfo_screenheight() // 10
        self.dpi = self.winfo_fpixels("1i")
        self.figsize = (Polarimetry.figsize[0] / self.dpi, Polarimetry.figsize[1] / self.dpi)
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
                self.icons.update({os.path.splitext(file)[0]: CTk.CTkImage(dark_image=Image.open(os.path.join(image_path, file)), size=(30, 30))})
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
                    winreg.CloseKey(EXT)
            except WindowsError:
                pass

## DEFINE FRAMES
        self.left_frame = CTk.CTkFrame(master=self, width=Polarimetry.left_frame_width, corner_radius=0, fg_color=gray[0])
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.right_frame = CTk.CTkFrame(master=self, width=Polarimetry.right_frame_width)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=0)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

## DEFINE TABS
        self.tabview = CTk.CTkTabview(master=self.right_frame, width=Polarimetry.tab_width, height=Polarimetry.tab_height, segmented_button_selected_color=orange[0], segmented_button_unselected_color=gray[1], segmented_button_selected_hover_color=orange[1], text_color=text_color, segmented_button_fg_color=gray[0], fg_color=gray[1])
        self.tabview.pack(fill=tk.BOTH, expand=True)
        list_tabs = ["Intensity", "Thresholding/Mask", "Options", "Advanced", "About"]
        for tab in list_tabs:
            self.tabview.add(tab)

## LEFT FRAME
        logo = Button(self.left_frame, text=" PyPOLAR", image=self.icons["blur_circular"], command=self.on_click_tab)
        logo.configure(hover=False, fg_color="transparent", font=CTk.CTkFont(size=20))
        logo.pack(padx=20, pady=(10, 40))
        self.method = tk.StringVar()
        DropDown(self.left_frame, values=["1PF", "CARS", "SRS", "SHG", "2PF", "4POLAR 2D", "4POLAR 3D"], image=self.icons["microscope"], command=self.method_dropdown_callback, variable=self.method)
        self.openfile_dropdown = DropDown(self.left_frame, values=["Open file", "Open folder", "Previous analysis"], image=self.icons["download_file"], command=self.open_file_callback)
        self.option = tk.StringVar()
        self.options_dropdown = DropDown(self.left_frame, values=["Thresholding (manual)", "Mask (manual)"], image=self.icons["build"], variable=self.option, state="disabled", command=self.options_dropdown_callback)
        ToolTip.createToolTip(self.options_dropdown, " Select the method of analysis: intensity thresholding or segmentation\n mask for single file analysis (manual) or batch processing (auto).\n The mask has to be binary and in PNG format and have the same\n file name as the respective polarimetry data file.")
        self.add_roi_button = Button(self.left_frame, text="Add ROI", image=self.icons["roi"], command=self.add_roi_callback)
        ToolTip.createToolTip(self.add_roi_button, "Add a region of interest: polygon (left button), freehand (right button)")
        self.add_roi_button.pack(padx=20, pady=20)
        self.analysis_button = Button(self.left_frame, text="Analysis", command=self.analysis_callback, image=self.icons["play"])
        ToolTip.createToolTip(self.analysis_button, "Polarimetry analysis")
        self.analysis_button.configure(fg_color=green[0], hover_color=green[1])
        self.analysis_button.pack(padx=20, pady=20)
        button = Button(self.left_frame, text="Close figures", command=self.close_callback, image=self.icons["close"])
        ToolTip.createToolTip(button, "Close all open figures")
        button.configure(fg_color=red[0], hover_color=red[1])
        button.pack(padx=20, pady=20)

## RIGHT FRAME: INTENSITY
        bottomframe = CTk.CTkFrame(master=self.tabview.tab("Intensity"), fg_color="transparent", height=40, width=Polarimetry.axes_size[1])
        bottomframe.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        self.intensity_frame = CTk.CTkFrame(master=self.tabview.tab("Intensity"), fg_color="transparent", height=Polarimetry.axes_size[0], width=Polarimetry.axes_size[1])
        self.intensity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.intensity_fig = Figure(figsize=(self.intensity_frame.winfo_width() / self.dpi, self.intensity_frame.winfo_height() / self.dpi), facecolor=gray[1])
        self.intensity_axis = self.intensity_fig.add_axes([0, 0, 1, 1])
        self.intensity_axis.set_axis_off()
        self.intensity_canvas = FigureCanvasTkAgg(self.intensity_fig, master=self.intensity_frame)
        background = plt.imread(os.path.join(image_path, "blur_circular-512.png"))
        self.intensity_axis.imshow(background, cmap="gray", interpolation="bicubic", alpha=0.1)
        self.intensity_canvas.draw()
        self.intensity_toolbar = NToolbar2Tk(self.intensity_canvas, self.intensity_frame, pack_toolbar=False)
        self.intensity_toolbar.config(background=gray[1])
        self.intensity_toolbar._message_label.config(background=gray[1])
        for button in self.intensity_toolbar.winfo_children():
            button.config(background=gray[1])
        self.intensity_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.intensity_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
        banner = CTk.CTkFrame(master=self.tabview.tab("Intensity"), fg_color="transparent", height=Polarimetry.axes_size[0], width=40)
        banner.pack(side=tk.RIGHT, fill=tk.Y)
        Button(banner, image=self.icons["contrast"], command=self.contrast_intensity_button_callback).pack(side=tk.TOP, padx=20, pady=20)
        self.contrast_intensity_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_intensity_slider_callback)
        self.contrast_intensity_slider.set(1)
        ToolTip.createToolTip(self.contrast_intensity_slider, " Adjust contrast\n The chosen contrast will be the one used\n for the intensity images in figures")
        self.contrast_intensity_slider.pack(padx=20, pady=20)
        self.compute_angle_button = Button(banner, image=self.icons["square"], command=self.compute_angle)
        #ToolTip.createToolTip(self.compute_angle_button, " Left click and hold to trace a line\n segment and determine its angle")
        self.compute_angle_button.pack(padx=20, pady=20)
        self.filename_label = CTk.CTkTextbox(master=bottomframe, width=400, height=50)
        self.filename_label.configure(state="disabled")
        self.filename_label.pack(side=tk.LEFT)
        sliderframe = CTk.CTkFrame(master=bottomframe, fg_color="transparent")
        sliderframe.pack(side=tk.RIGHT, padx=100)
        self.stack_slider = CTk.CTkSlider(master=sliderframe, from_=0, to=18, number_of_steps=18, command=self.stack_slider_callback, state="disabled")
        self.stack_slider.set(0)
        self.stack_slider.grid(row=0, column=0, columnspan=2)
        self.stack_slider_label = CTk.CTkLabel(master=sliderframe, text="T")
        ToolTip.createToolTip(self.stack_slider, "Slider at T for the total intensity, otherwise scroll through the images of the stack")
        self.stack_slider_label.grid(row=1, column=0, sticky="w")
        CTk.CTkLabel(master=sliderframe, fg_color="transparent", text="Stack").grid(row=1, column=1, sticky="e")

## RIGHT FRAME: THRSH
        bottomframe = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", height=40, width=Polarimetry.axes_size[1])
        bottomframe.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        self.thrsh_frame = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", height=Polarimetry.axes_size[0], width=Polarimetry.axes_size[1])
        self.thrsh_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thrsh_axis_facecolor = gray[1]
        self.thrsh_fig = Figure(figsize=(self.thrsh_frame.winfo_width() / self.dpi, self.thrsh_frame.winfo_height() / self.dpi), facecolor=self.thrsh_axis_facecolor)
        self.thrsh_axis = self.thrsh_fig.add_axes([0, 0, 1, 1])
        self.thrsh_axis.set_axis_off()
        self.thrsh_axis.set_facecolor(self.thrsh_axis_facecolor)
        self.thrsh_canvas = FigureCanvasTkAgg(self.thrsh_fig, master=self.thrsh_frame)
        self.thrsh_axis.imshow(background, cmap="gray", interpolation="bicubic", alpha=0.1)
        self.thrsh_canvas.draw()
        self.thrsh_toolbar = NToolbar2Tk(self.thrsh_canvas, self.thrsh_frame, pack_toolbar=False)
        self.thrsh_toolbar.config(background=gray[1])
        self.thrsh_toolbar._message_label.config(background=gray[1])
        for button in self.thrsh_toolbar.winfo_children():
            button.config(background=gray[1])
        self.thrsh_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.thrsh_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
        banner = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", height=Polarimetry.axes_size[0], width=40)
        banner.pack(side=tk.RIGHT, fill=tk.Y)
        Button(banner, image=self.icons["contrast"], command=self.contrast_thrsh_button_callback).pack(side=tk.TOP, padx=20, pady=20)
        self.contrast_thrsh_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_thrsh_slider_callback)
        self.contrast_thrsh_slider.set(1)
        ToolTip.createToolTip(self.contrast_thrsh_slider, " Adjust contrast\n The chosen contrast does not affect the analysis")
        self.contrast_thrsh_slider.pack(padx=20, pady=20)
        button = Button(banner, image=self.icons["palette"], command=self.change_colormap)
        #ToolTip.createToolTip(button, " Change the colormap used for thresholding ('hot' or 'gray')")
        button.pack(padx=20, pady=10)
        self.no_background_button = Button(banner, image=self.icons["photo_fill"], command=self.no_background)
        #ToolTip.createToolTip(button, " Change background to enhance visibility")
        self.no_background_button.pack(padx=20, pady=10)
        button = Button(banner, image=self.icons["open_in_new"], command=self.export_mask)
        #ToolTip.createToolTip(button, " Export mask as .png")
        button.pack(padx=20, pady=10)
        button = Button(banner, image=self.icons["format_list"], command=self.roimanager_callback)
        #ToolTip.createToolTip(button, "Erase selected ROIs and reload image")
        button.pack(padx=20, pady=10)
        self.ilow = tk.StringVar(value="0")
        self.ilow_slider = CTk.CTkSlider(master=bottomframe, from_=0, to=1, command=self.ilow_slider_callback)
        self.ilow_slider.set(0)
        self.ilow_slider.grid(row=0, column=0, columnspan=2, padx=20, pady=0)
        self.transparency_slider = CTk.CTkSlider(master=bottomframe, from_=0, to=1, command=self.transparency_slider_callback)
        ToolTip.createToolTip(self.transparency_slider, " Adjust the transparency of the background image")
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
        show_save.grid(row=0, column=0, padx=(20, 20), pady=10, sticky="nw")
        CTk.CTkLabel(master=show_save, text="\nFigures\n", font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=3, padx=20, pady=0)
        CTk.CTkLabel(master=show_save, text="Show", anchor="w").grid(row=1, column=1, pady=(0, 10))
        CTk.CTkLabel(master=show_save, text="Save", anchor="w").grid(row=1, column=2, pady=(0, 10))
        labels = ["Composite", "Sticks", "Histogram", "Intensity"]
        self.show_table = [CheckBox(show_save) for it in range(len(labels))]
        self.save_table = [CheckBox(show_save) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=show_save, text=labels[it], anchor="w", width=100, height=30).grid(row=it+2, column=0, padx=(20, 0))
            self.save_table[it].configure(command=self.click_save_output)
            self.show_table[it].grid(row=it+2, column=1, pady=0, padx=20, sticky="ew")
            self.save_table[it].grid(row=it+2, column=2, pady=0, padx=(20, 20))
        CTk.CTkLabel(master=show_save, text=" ").grid(row=len(labels)+2, column=0, padx=0, pady=0)
        banner = CTk.CTkFrame(master=self.tabview.tab("Options"))
        banner.grid(row=2, column=1, padx=20, pady=50, sticky="n")
        button = Button(banner, image=self.icons["delete_forever"], command=self.initialize_tables)
        #ToolTip.createToolTip(button, "Reinitialize the tables Show/Save and Variable")
        button.grid(row=0, column=0, padx=(0, 100), pady=0, sticky="nw")
        self.per_roi = CheckBox(banner, text="per ROI")
        ToolTip.createToolTip(self.per_roi, " Show and save data/figures separately for each region of interest")
        self.per_roi.grid(row=0, column=1, sticky="nw")
        preferences = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        preferences.grid(row=2, column=0, padx=20, pady=10)
        CTk.CTkLabel(master=preferences, text="\nPreferences\n", font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=2, padx=20, pady=0)
        self.add_axes_checkbox = CheckBox(preferences, text="\n Axes on figures\n", command=self.add_axes_on_all_figures)
        self.add_axes_checkbox.select()
        self.add_axes_checkbox.grid(row=1, column=0, columnspan=2, padx=40, pady=(0, 0), sticky="ew")
        self.colorbar_checkbox = CheckBox(preferences, text="\n Colorbar on figures\n", command=self.colorbar_on_all_figures)
        self.colorbar_checkbox.select()
        self.colorbar_checkbox.grid(row=2, column=0, columnspan=2, padx=40, pady=(0, 0), sticky="ew")
        self.colorblind_checkbox = CheckBox(preferences, text="\n Colorblind-friendly\n", command=self.colorblind_on_all_figures)
        self.colorblind_checkbox.grid(row=3, column=0, columnspan=2, padx=40, pady=(0, 20), sticky="ew")
        Button(preferences, text="Crop figures", image=self.icons["crop"], command=self.crop_figures_callback).grid(row=4, column=0, columnspan=2, padx=20, pady=0)
        button = Button(preferences, text="Show individual fit", image=self.icons["query_stats"], command=self.show_individual_fit_callback)
        ToolTip.createToolTip(button, "Zoom into the region of interest\nthen click using the crosshair")
        button.grid(row=5, column=0, columnspan=2, padx=20, pady=20)
        labels = [" pixels per stick (horizontal)", "pixels per stick (vertical)"]
        self.pixelsperstick_spinboxes = [SpinBox(master=preferences, command=self.pixelsperstick_spinbox_callback) for it in range(2)]
        for it in range(2):
            self.pixelsperstick_spinboxes[it].grid(row=it+7, column=0, padx=(20, 0), pady=(0, 20))
            label = CTk.CTkLabel(master=preferences, text=labels[it], anchor="w")
            label.grid(row=it+7, column=1, padx=(0, 20), pady=(0, 20))
            ToolTip.createToolTip(label, "Controls the density of sticks to be plotted")
        self.variable_table_frame = CTk.CTkFrame(master=self.tabview.tab("Options"), width=300)
        self.variable_table_frame.grid(row=0, column=1, padx=(40, 20), pady=10, sticky="nw")
        save_ext = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        CTk.CTkLabel(master=save_ext, text="\nSave output\n", font=CTk.CTkFont(size=16), width=250).grid(row=0, column=0, columnspan=2, padx=(20, 20), pady=(0, 0))
        save_ext.grid(row=2, column=1, padx=(40, 20), pady=100, sticky="sw")
        labels = ["data (.pykl)", "figures (.tif)", "data (.mat)", "mean values (.xlsx)", "movie (.gif)"]
        self.extension_table = [CheckBox(save_ext) for it in range(len(labels))]
        self.extension_table[1].configure(state="disabled")
        for it in range(len(labels)):
            CTk.CTkLabel(master=save_ext, text=labels[it], anchor="w", width=120).grid(row=it+1, column=0, padx=(20, 0))
            self.extension_table[it].grid(row=it+1, column=1, pady=0, padx=(20,0))
        CTk.CTkLabel(master=save_ext, text=" ").grid(row=len(labels)+1, column=0)

## RIGHT FRAME: ADV
        adv_elts = ["Dark", "Binning", "Polarization", "Rotation", "Disk cone / Calibration data", "Remove background"]
        adv_loc = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        adv = {}
        for loc, elt in zip(adv_loc, adv_elts):
            adv.update({elt: CTk.CTkFrame(
            master=self.tabview.tab("Advanced"), fg_color=self.left_frame.cget("fg_color"))})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=(10, 10), sticky="nw")
            CTk.CTkLabel(master=adv[elt], text=elt + "\n", width=230, font=CTk.CTkFont(size=16)).grid(row=0, column=0, padx=20, pady=(10,0))
        self.dark_switch = CTk.CTkSwitch(master=adv["Dark"], text="", command=self.dark_switch_callback, onvalue="on", offvalue="off", width=50)
        self.dark_switch.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        self.calculated_dark_label = CTk.CTkLabel(master=adv["Dark"], text="Calculated dark value = 0")
        self.calculated_dark_label.grid(row=1, column=0)
        self.dark = tk.StringVar()
        self.dark_entry = Entry(adv["Dark"], text="Used dark value", textvariable=self.dark, row=2, column=0)
        ToolTip.createToolTip(self.dark_entry, "For 1PF, use a dark value greater than 480\nRaw images correspond to a dark value 0")
        self.dark_entry.bind("<Return>", command=self.itot_callback)
        self.dark_entry.state("disabled")
        CTk.CTkLabel(master=adv["Dark"], text=" ").grid(row=3, column=0)
        self.offset_angle_switch = CTk.CTkSwitch(master=adv["Polarization"], text="", command=self.offset_angle_switch_callback, onvalue="on", offvalue="off", width=50)
        self.offset_angle_switch.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        self.offset_angle = tk.IntVar()
        self.offset_angle_entry = Entry(adv["Polarization"], text="\nOffset angle (deg)\n", textvariable=self.offset_angle, row=1)
        self.offset_angle_entry.state("disabled")
        CTk.CTkLabel(master=adv["Polarization"], text=" ").grid(row=2, column=0)
        self.polar_dir = tk.StringVar(value="clockwise")
        CTk.CTkOptionMenu(master=adv["Polarization"], values=["clockwise", "counterclockwise"], width=button_size[0], height=button_size[1], dynamic_resizing=False, variable=self.polar_dir).grid(row=3, column=0, pady=(0, 10))
        self.calib_dropdown = CTk.CTkOptionMenu(master=adv["Disk cone / Calibration data"], values="", width=button_size[0], height=button_size[1], dynamic_resizing=False, command=self.calib_dropdown_callback)
        self.calib_dropdown.grid(row=1, column=0, pady=10)
        ToolTip.createToolTip(self.calib_dropdown, " 1PF: Select disk cone depending on wavelength and acquisition date\n 4POLAR: Select .mat file containing the calibration data")
        button = Button(adv["Disk cone / Calibration data"], text="Display", image=self.icons["photo"], command=self.diskcone_display)
        button.grid(row=2, column=0, pady=10)
        ToolTip.createToolTip(button, "Display the selected disk cone (for 1PF)")
        self.calib_textbox = CTk.CTkTextbox(master=adv["Disk cone / Calibration data"], width=250, height=50, state="disabled")
        self.calib_textbox.grid(row=3, column=0, pady=10)
        self.polar_dropdown = CTk.CTkOptionMenu(master=adv["Disk cone / Calibration data"], values="", width=button_size[0], height=button_size[1], dynamic_resizing=False, command=self.polar_dropdown_callback, state="disabled")
        self.polar_dropdown.grid(row=4, column=0, pady=10)
        ToolTip.createToolTip(self.polar_dropdown, "4POLAR: Select the distribution of polarizations (0,45,90,135) among quadrants clockwise\n Upper Left (UL), Upper Right (UR), Lower Right (LR), Lower Left (LL)")
        labels = ["Bin width", "Bin height"]
        self.bin_spinboxes = [SpinBox(adv["Binning"], command=lambda:self.itot_callback(event=1)) for _ in range(2)]
        for it in range(2):
            self.bin_spinboxes[it].bind("<Return>", command=self.itot_callback)
            self.bin_spinboxes[it].grid(row=it+1, column=0, padx=(60, 20), pady=(0, 0), sticky="w")
            label = CTk.CTkLabel(master=adv["Binning"], text="\n" + labels[it] + "\n")
            label.grid(row=it+1, column=0, padx=(0, 60), pady=(0, 0), sticky="e")
            ToolTip.createToolTip(label, "Height and width of the bin used for data binning")
        labels = ["Stick (deg)", "Figure (deg)"]
        self.rotation = [tk.IntVar(value=0), tk.IntVar(value=0)]
        entries = [Entry(adv["Rotation"], text="\n" + label + "\n", text_box=0, textvariable=self.rotation[it], row=it+1, column=0) for it, label in enumerate(labels)]
        entries[1].bind("<Return>", command=self.rotation_callback)
        for entry in entries:
            ToolTip.createToolTip(entry, "positive value for counter-clockwise rotation / negative value for clockwise rotation")
        labels = ["Noise factor", "Noise width", "Noise height", "Noise removal level"]
        self.noise = [tk.DoubleVar(value=1), tk.IntVar(value=3), tk.IntVar(value=3), tk.DoubleVar(value=0)]
        rows = [1, 2, 3, 5]
        entries = [Entry(adv["Remove background"], text="\n" + label + "\n", textvariable=self.noise[it], row=rows[it], column=0) for it, label in enumerate(labels)]
        entries[3].state("disabled")
        button = Button(adv["Remove background"], text="Click background", image=self.icons["exposure"], command=lambda:self.click_callback(self.intensity_axis, self.intensity_canvas, "click background"))
        button.grid(row=4, column=0)
        ToolTip.createToolTip(button, "Click and select a point on the intensity image")

## RIGHT FRAME: ABOUT
        banner = CTk.CTkFrame(master=self.tabview.tab("About"))
        banner.grid(row=0, column=0, pady=20)
        Button(banner, image=self.icons["web"], command=lambda:self.openweb(Polarimetry.url_fresnel)).pack(side=tk.LEFT, padx=40)
        Button(banner, image=self.icons["mail"], command=self.send_email).pack(side=tk.LEFT, padx=40)
        Button(banner, image=self.icons["GitHub"], command=lambda:self.openweb(Polarimetry.url_github)).pack(side=tk.LEFT, padx=40)
        Button(banner, image=self.icons["contact_support"], command=lambda:self.openweb(Polarimetry.url_github + "/blob/master/README.md")).pack(side=tk.LEFT, padx=40)
        about_textbox = CTk.CTkTextbox(master=self.tabview.tab("About"), width=Polarimetry.tab_width-30, height=500)
        about_textbox.grid(row=1, column=0, padx=30)
        message = f"Version: {Polarimetry.__version__} ({Polarimetry.__version_date__}) \n\n\n Website: www.fresnel.fr/polarimetry/ \n\n\n Source code available at github.com/cchandre/Polarimetry \n\n\n\n Based on a code originally developed by Sophie Brasselet (Institut Fresnel, CNRS) \n\n\n To report bugs, send an email to\n     manos.mavrakis@cnrs.fr  (Manos Mavrakis, Institut Fresnel, CNRS) \n     cristel.chandre@cnrs.fr  (Cristel Chandre, Institut de Mathématiques de Marseille, CNRS) \n     sophie.brasselet@fresnel.fr  (Sophie Brasselet, Institut Fresnel, CNRS) \n\n\n\n BSD 2-Clause License\n\n Copyright(c) 2021, Cristel Chandre\n All rights reserved. \n\n\n  created using Python with packages Tkinter (CustomTkinter), NumPy, SciPy, OpenCV,\n Matplotlib, openpyxl, tksheet, colorcet \n\n\n  uses Material Design icons by Google"
        about_textbox.insert("0.0", message)
        about_textbox.configure(state="disabled")
        self.tabview.set("Intensity")
        self.startup()

    def startup(self):
        info = " (1) Select a polarimetry method\n\n (2) Download a file or a folder\n        or a previous PyPOLAR analysis\n\n (3) Select a method of analysis\n\n (4) Select one or several regions of interest\n\n (5) Click on Analysis"
        info_window = CTk.CTkToplevel(self)
        info_window.attributes("-topmost", "true")
        info_window.title("Polarimetry Analysis")
        info_window.geometry(geometry_info((380, 350)))
        CTk.CTkLabel(info_window, text="  PyPOLAR", font=CTk.CTkFont(size=20), image=self.icons['blur_circular'], compound="left").grid(row=0, column=0, padx=0, pady=20)
        textbox = CTk.CTkTextbox(info_window, width=320, height=170, fg_color=gray[1])
        textbox.grid(row=1, column=0, padx=40)
        textbox.insert("0.0", info)
        link = CTk.CTkLabel(info_window, text="For more information, visit the GitHub page", text_color="blue", font=CTk.CTkFont(underline=True), cursor="hand2")
        link.grid(row=2, column=0, padx=50, pady=10, sticky="w")
        link.bind("<Button-1>", lambda e:webbrowser.open_new_tab(Polarimetry.url_github))
        Button(master=info_window, text="OK", anchor="center", command=lambda:info_window.withdraw(), width=80).grid(row=7, column=0, padx=20, pady=0)

        self.method.set("1PF")
        self.option.set("Thresholding (manual)")
        self.define_variable_table("1PF")
        self.CD = Calibration("1PF")
        self.calib_dropdown.configure(values=self.CD.list("1PF"))
        self.calib_dropdown.set(self.CD.list("1PF")[0])
        self.calib_textbox.configure(state="normal")
        self.calib_textbox.delete("0.0", "end")
        self.calib_textbox.insert("0.0", self.CD.name)
        self.calib_textbox.configure(state="disabled")
        self.offset_angle.set(0)
        angles = [0, 45, 90, 135]
        self.dict_polar = {}
        for p in list(permutations([0, 1, 2, 3])):
            a = [angles[_] for _ in p]
            self.dict_polar.update({f"UL{a[0]}-UR{a[1]}-LR{a[2]}-LL{a[3]}": p})
        self.polar_dropdown.configure(values=list(self.dict_polar.keys()))
        self.polar_dropdown.set("UL90-UR0-LR45-LL135")
        self.order = self.dict_polar["UL90-UR0-LR45-LL135"]
        self.thrsh_colormap = "hot"

    def initialize_slider(self):
        if hasattr(self, "stack"):
            self.stack_slider.configure(to=self.stack.nangle, number_of_steps=self.stack.nangle)
            self.ilow.set(self.stack.display.format(np.amin(self.datastack.itot)))
            self.ilow_slider.set(float(self.ilow.get()))
            self.contrast_intensity_slider.set(1)
            self.contrast_thrsh_slider.set(1)
            self.stack_slider.set(0)
            self.stack_slider_label.configure(text="T")

    def initialize_noise(self):
        vals = [1, 3, 3, 0]
        for val, _ in zip(vals, self.noise):
            _.set(val)

    def initialize(self):
        self.initialize_slider()
        self.initialize_noise()
        if hasattr(self, "datastack"):
            self.datastack.rois = []
        self.represent_intensity()
        self.represent_thrsh()

    def initialize_tables(self):
        for show, save in zip(self.show_table, self.save_table):
            show.deselect()
            save.deselect()
        if hasattr(self, "variable_display"):
            for var in self.variable_display:
                var.set(0)
        for ext in self.extension_table:
            ext.deselect()

    def click_save_output(self):
        vec = [val.get() for val in self.save_table]
        if any(vec) == 1:
            self.extension_table[1].select()
        else:
            self.extension_table[1].deselect()

    def on_closing(self):
        plt.close("all")
        super().destroy()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()

    def openweb(self, url):
        webbrowser.open(url)

    def send_email(self):
        webbrowser.open("mailto:?to=" + Polarimetry.email + "&subject=[Polarimetry Analysis] question", new=1)

    def on_click_tab(self):
        if self.tabview.get() != "About":
            self.tabview.set("About")
        else:
            self.tabview.set("Intensity")

    def edge_detection_callback(self):
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
            self.represent_thrsh()

    def delete_edge_mask(self, window):
        window.withdraw()
        if hasattr(self, "edge_contours"):
            delattr(self, "edge_contours")
        self.edge_detection_switch.deselect()

    def download_edge_mask(self, window):
        window.withdraw()
        filetypes = [("PNG files", "*.png")]
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        filename = fd.askopenfilename(title="Select a mask file", initialdir=initialdir, filetypes=filetypes)
        self.edge_method = "download"
        self.edge_detection_tab()
        self.edge_mask = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        self.compute_edges()

    def compute_edge_mask(self, window):
        window.withdraw()
        if hasattr(self, "stack"):
            self.edge_method = "compute"
            self.edge_detection_tab()
            self.compute_edges()

    def edge_detection_tab(self):
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
        tooltips = [" hysteresis thresholding values: edges with intensity gradients\n below this value are not edges and discarded ", " hysteresis thresholding values: edges with intensity gradients\n larger than this value are sure to be edges", " minimum length for a contour (in px)", " number of pixels in the window used for smoothing contours"]
        self.canny_thrsh = [tk.DoubleVar(value=60), tk.DoubleVar(value=100), tk.IntVar(value=100), tk.IntVar(value=20)]
        for _, (param, tooltip) in enumerate(zip(params, tooltips)):
            entry = Entry(adv["Edge detection"], text=param, textvariable=self.canny_thrsh[_], row=_+1)
            entry.bind("<Return>", command=self.compute_edges)
            ToolTip.createToolTip(entry, tooltip)
        params = ["Distance from contour", "Layer width"]
        self.layer_params = [tk.IntVar(value=0), tk.IntVar(value=10)]
        for _, param in enumerate(params):
            Entry(adv["Layer"], text=param, textvariable=self.layer_params[_], row=_+1)

    def compute_edges(self, event=[]):
        if self.edge_method == "compute":
            field = self.stack.itot.copy()
            thrsh = float(self.ilow.get())
            field[field <= thrsh] = 0
            field = (field / np.amax(field) * 255).astype(np.uint8)
            field = cv2.GaussianBlur(field, (5, 5), 0)
            edges = cv2.Canny(image=field, threshold1=self.canny_thrsh[0].get(), threshold2=self.canny_thrsh[1].get())
            contours = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
        elif self.edge_method == "download":
            contours = cv2.findContours(self.edge_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[0]
        filter = np.asarray([len(contour) >= self.canny_thrsh[2].get() for contour in contours])
        self.edge_contours = [self.smooth_edge(contour.reshape((-1, 2))) for (contour, val) in zip(contours, filter) if val]
        self.represent_thrsh()

    def smooth_edge(self, edge):
        window_length = self.canny_thrsh[3].get()
        polyorder = 3
        return savgol_filter(edge, window_length=window_length, polyorder=polyorder, mode="nearest", axis=0)
    
    def define_rho_ct(self, contours):
        rho_ct = np.nan * np.ones_like(self.stack.itot)
        for contour in contours:
            angle, normal = self.angle_edge(contour)
            crange = chain(range(-self.layer_params[0].get() - self.layer_params[1].get(), -self.layer_params[0].get() + 1), range(self.layer_params[0].get(), self.layer_params[0].get() + self.layer_params[1].get() + 1))
            for _ in crange:
                shift_x = (contour[:, 0] + _ * normal[:, 0]).astype(np.uint16)
                shift_y = (contour[:, 1] + _ * normal[:, 1]).astype(np.uint16)
                shift_x[shift_x <= 0] = 0
                shift_y[shift_y <= 0] = 0
                shift_x[shift_x >= self.stack.width - 1] = self.stack.width - 1
                shift_y[shift_y >= self.stack.height - 1] = self.stack.height - 1
                rho_ct[shift_y, shift_x] = angle
        return rho_ct
    
    def angle_edge(self, edge):
        tangent = np.diff(edge, axis=0, append=edge[-1, :].reshape((1, 2)))
        norm_t = norm(tangent, axis=1)[:, np.newaxis]
        tangent = np.divide(tangent, norm_t, where=np.all((norm_t!=0, np.isfinite(norm_t)), axis=0))
        angle = np.mod(2 * np.rad2deg(np.arctan2(-tangent[:, 1], tangent[:, 0])), 360) / 2
        normal = np.einsum("ij,jk->ik", tangent, np.array([[0, -1], [1, 0]]))
        return angle, normal

    def contrast_thrsh_slider_callback(self, value):
        if value <= 0.001:
            self.contrast_thrsh_slider.set(0.001)
        self.represent_thrsh()

    def contrast_intensity_slider_callback(self, value):
        if value <= 0.001:
            self.contrast_intensity_slider.set(0.001)
        self.represent_intensity()

    def contrast_intensity_button_callback(self):
        if self.contrast_intensity_slider.get() <= 0.5:
            self.contrast_intensity_slider.set(0.5)
        else:
            self.contrast_intensity_slider.set(1)
        self.represent_intensity()

    def contrast_thrsh_button_callback(self):
        if self.contrast_thrsh_slider.get() <= 0.5:
            self.contrast_thrsh_slider.set(0.5)
        else:
            self.contrast_thrsh_slider.set(1)
        self.represent_thrsh(update=True)

    def roimanager_callback(self):

        def on_closing(manager: ROIManager):
            if hasattr(self, "datastack"):
                for roi in self.datastack.rois:
                    roi["select"] = True
                self.represent_intensity()
                self.represent_thrsh()
            manager.destroy()

        def commit(manager: ROIManager):
            if hasattr(self, "datastack"):
                if any(self.datastack.rois):
                    self.datastack.rois = manager.update_sheet(self.datastack.rois)
                    self.represent_intensity()
                    self.represent_thrsh()

        def delete(manager: ROIManager):
            if hasattr(self, "datastack"):
                manager.delete(self.datastack.rois)
                self.represent_intensity()
                self.represent_thrsh()

        def delete_all(manager: ROIManager):
            if hasattr(self, "datastack"):
                if any(self.datastack.rois):
                    self.datastack.rois = []
                    manager.delete_all()
                    self.represent_intensity()
                    self.represent_thrsh()

        def load(manager: ROIManager):
            if hasattr(self, "datastack"):
                self.datastack.rois = manager.load(initialdir=self.stack.folder if hasattr(self, "stack") else "/")
                self.represent_intensity()
                self.represent_thrsh()

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

    def add_axes_on_all_figures(self):
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (("Composite" in fs) or ("Sticks" in fs) or ("Intensity" in fs)) and (self.datastack.name in fs):
                fig.axes[0].axis(self.add_axes_checkbox.get())
                fig.canvas.draw()

    def colorbar_on_all_figures(self):
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if (("Composite" in fs) or ("Sticks" in fs) or ("Intensity" in fs)) and (self.datastack.name in fs):
                if self.colorbar_checkbox.get():
                    ax_divider = make_axes_locatable(fig.axes[0])
                    cax = ax_divider.append_axes("right", size="7%", pad="2%")
                    if ("Composite" in fs):
                        fig.colorbar(fig.axes[0].images[1], cax=cax)
                    elif ("Sticks" in fs) or (("Intensity" in fs) and (self.edge_detection_switch.get() == "on")):
                        fig.colorbar(fig.axes[0].collections[0], cax=cax)
                    if ("Intensity" in fs) and (self.edge_detection_switch.get() == "off"):
                        fig.axes[1].remove()
                else:
                    if len(fig.axes) >= 2:
                        fig.axes[1].remove()

    def colorblind_on_all_figures(self):
        if hasattr(self, "datastack"):
            figs = list(map(plt.figure, plt.get_fignums()))
            for fig in figs:
                fs = fig.canvas.manager.get_window_title()
                for var in self.datastack.vars:
                    if (var.name == fs.split()[0]):
                        cmap = var.colormap[self.colorblind_checkbox.get()]
                if "Intensity" in fs.split()[0]:
                    cmap = self.datastack.vars[0].colormap[self.colorblind_checkbox.get()]
                if ("Composite" in fs) and (self.datastack.name in fs):
                    fig.axes[0].images[1].set_cmap(cmap)
                elif (("Sticks" in fs) or (("Intensity" in fs) and (self.edge_detection_switch.get() == "on"))) and (self.datastack.name in fs):
                    fig.axes[0].collections[0].set_cmap(cmap)

    def options_dropdown_callback(self, value):
        if value.endswith("(auto)"):
            self.options_dropdown.get_icon().configure(image=self.icons["build_fill"])
        else:
            self.options_dropdown.get_icon().configure(image=self.icons["build"])
        if value.startswith("Mask"):
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            self.maskfolder = fd.askdirectory(title="Select the directory containing masks", initialdir=initialdir)
            if hasattr(self, "datastack"):
                self.mask = self.get_mask(self.datastack)
                self.represent_thrsh()
                self.thrsh_frame.update()

    def open_file_callback(self, value):
        self.edge_detection_switch.deselect()
        if hasattr(self, "edge_contours"):
            delattr(self, "edge_contours")
            self.tabview.delete("Edge Detection")
        if hasattr(self, "manager_window"):
            self.manager_window.destroy()
        if value == "Open file":
            self.openfile_dropdown.get_icon().configure(image=self.icons["photo_fill"])
            self.options_dropdown.get_icon().configure(image=self.icons["build"])
            filetypes = [("Tiff files", "*.tiff"), ("Tiff files", "*.tif")]
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            filename = fd.askopenfilename(title="Select a file", initialdir=initialdir, filetypes=filetypes)
            self.filelist = []
            if filename:
                self.options_dropdown.set_state("normal")
                self.options_dropdown.set_values(["Thresholding (manual)", "Mask (manual)"])
                self.option.set("Thresholding (manual)")
                if hasattr(self, "mask"):
                    delattr(self, "mask")
                self.open_file(filename)
        elif value == "Open folder":
            self.openfile_dropdown.get_icon().configure(image=self.icons["folder_open"])
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            folder = fd.askdirectory(title="Select a directory", initialdir=initialdir)
            self.filelist = []
            if folder:
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
                window = ShowInfo(message=" The folder does not contain TIFF or TIF files", image=self.icons["download_folder"], button_labels=["OK"], geometry=(340, 140))
                window.get_buttons()[0].configure(command=lambda:window.withdraw())
        elif value == "Previous analysis":
            initialdir = self.stack.folder if hasattr(self, "stack") else "/"
            filename = fd.askopenfilename(title="Download a previous polarimetry analysis", initialdir=initialdir, filetypes=[("PyPOLAR pickle files", "*.pykl")])
            if filename:
                window = ShowInfo(message=" Downloading and decompressing data...", image=self.icons["download"], geometry=(350, 80))[0]
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
                self.filename_label.configure(state="normal")
                self.filename_label.delete("0.0", "end")
                self.filename_label.insert("0.0", self.datastack.name)
                self.filename_label.configure(state="disabled")
                self.represent_intensity(update=False)
            window.withdraw()
        if hasattr(self, "stack"):
            self.ilow_slider.configure(from_=np.amin(self.stack.itot), to=np.amax(self.stack.itot))
            self.ilow_slider.set(np.amin(self.stack.itot))
            self.ilow.set(self.stack.display.format(np.amin(self.stack.itot)))
            self.represent_thrsh(update=False)

    def crop_figures_callback(self):
        if len(plt.get_fignums()):
            info_window = CTk.CTkToplevel(self)
            info_window.attributes("-topmost", "true")
            info_window.title("Polarimetry Analysis")
            info_window.geometry(geometry_info((360, 240)))
            CTk.CTkLabel(info_window, text="Define xlim and ylim", image=self.icons["crop"], compound="left", width=250).grid(row=0, column=0, padx=30, pady=20)
            self.xlim = [tk.IntVar() for _ in range(2)]
            self.ylim = [tk.IntVar() for _ in range(2)]
            if not hasattr(self, "xlim") and hasattr(self, "datastack"):
                self.xlim[0].set(1)
                self.xlim[1].set(self.datastack.width)
                self.ylim[0].set(1)
                self.ylim[1].set(self.datastack.height)
            DoubleEntry(info_window, text="xlim", variables=self.xlim, row=1, state="normal")
            DoubleEntry(info_window, text="ylim", variables=self.ylim, row=2, state="normal")
            button = Button(info_window, text="OK", anchor="center", command=lambda:self.crop_figures(info_window))
            button.configure(width=80, height=button_size[1])
            button.grid(row=3, column=0, pady=20)

    def crop_figures(self, window):
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if ("Sticks" in fs) or ("Composite" in fs) or ("Intensity" in fs):
                fig.axes[0].set_xlim((self.xlim[0].get(), self.xlim[1].get()))
                fig.axes[0].set_ylim((self.ylim[1].get(), self.ylim[0].get()))
        window.withdraw()

    def clear_patches(self, ax, fig):
        if ax.patches:
            for p in ax.patches:
                p.set_visible(False)
                p.remove()
            for txt in ax.texts:
                txt.set_visible(False)
            fig.draw()

    def remove_roi(self, window, variable):
        if variable == "all":
            self.datastack.rois = []
        else:
            self.clear_patches(self.intensity_axis, self.intensity_canvas)
            self.clear_patches(self.thrsh_axis, self.thrsh_canvas)
            indx = int(variable)
            del self.datastack.rois[indx - 1]
            for roi in self.datastack.rois:
                if roi["indx"] > indx:
                    roi["indx"] -= 1
        self.represent_intensity(update=False)
        self.represent_thrsh(update=False)
        window.withdraw()

    def export_mask(self):
        if hasattr(self, "datastack"):
            window = ShowInfo(message=" Select output mask type: \n\n   - ROI: export ROIs as segmentation mask \n   - Intensity: export intensity-thresholded image as segmentation mask \n   - ROI \u00D7 Intensity: export intensity-thresholded ROIs as segmentation mask", image=self.icons['open_in_new'], button_labels=["ROI", "Intensity", "ROI \u00D7 Intensity", "Cancel"], geometry=(530, 200))
            buttons = window.get_buttons()
            buttons[0].configure(command=lambda:self.export_mask_callback(window, 0))
            buttons[1].configure(command=lambda:self.export_mask_callback(window, 1))
            buttons[2].configure(command=lambda:self.export_mask_callback(window, 2))
            buttons[3].configure(command=lambda:self.export_mask_callback(window, 3))

    def export_mask_callback(self, window, event):
        roi_map, mask = self.compute_roi_map(self.datastack)
        array = []
        if event == 0:
            array = (255 * (roi_map != 0)).astype(np.uint8)
        elif event == 1:
            array = (255 * (self.datastack.itot >= float(self.ilow.get()))).astype(np.uint8)
        elif event == 2:
            array = (255 * mask).astype(np.uint8)
        if np.any(array):
            data = Image.fromarray(array)
            data.save(self.datastack.filename + ".png")
        window.withdraw()

    def change_colormap(self):
        if self.thrsh_colormap == "hot":
            self.thrsh_colormap = "gray"
        else:
            self.thrsh_colormap = "hot"
        self.represent_thrsh()

    def no_background(self):
        if hasattr(self, "stack"):
            if self.thrsh_fig.patch.get_facecolor() == mpl.colors.to_rgba("k", 1):
                self.thrsh_fig.patch.set_facecolor(gray[1])
                self.no_background_button.configure(image=self.icons["photo_fill"])
            else:
                self.thrsh_fig.patch.set_facecolor("k")
                self.no_background_button.configure(image=self.icons["photo"])
            self.thrsh_canvas.draw()

    def offset_angle_switch_callback(self):
        if self.offset_angle_switch.get() == "on":
            self.offset_angle_entry.state("normal")
        else:
            self.offset_angle_entry.state("disabled")

    def dark_switch_callback(self):
        if hasattr(self, "stack"):
            if self.dark_switch.get() == "on":
                self.dark_entry.state("normal")
                self.dark.set(self.stack.display.format(self.calculated_dark))
            else:
                self.dark_entry.state("disabled")
                self.dark.set(self.stack.display.format(self.calculated_dark))
                self.itot_callback(event=1)
        else:
            self.dark.set("")

    def calib_dropdown_callback(self, value):
        self.CD = Calibration(self.method.get(), label=value)
        self.offset_angle.set(self.CD.offset_default)
        self.calib_textbox.configure(state="normal")
        self.calib_textbox.delete("0.0", "end")
        self.calib_textbox.insert("0.0", self.CD.name)
        self.calib_textbox.configure(state="disabled")

    def polar_dropdown_callback(self, value):
        self.order = self.dict_polar.get(value)

    def show_individual_fit_callback(self):
        figs = list(map(plt.figure, plt.get_fignums()))
        fig_ = []
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if ("Rho Composite" in fs) and (not self.method.get().endswith("4POLAR")):
                fig_ = fig
                break
        if fig_:
            plt.figure(fig_)
            cfm = plt.get_current_fig_manager()
            cfm.window.attributes("-topmost", True)
            cfm.window.tkraise()
            self.click_callback(fig_.axes[0], fig_.canvas, "individual fit")
            cfm.window.attributes("-topmost", False)
        else:
            window = ShowInfo(message=" Provide a Rho Composite figure\n to plot individual fits", image=self.icons["query_stats"], button_labels=["OK"])
            window.get_buttons()[0].configure(command=lambda:window.withdraw())

    def diskcone_display(self):
        if self.method.get() == "1PF" and hasattr(self, "CD"):
            fig, axs = plt.subplots(1, 2, figsize=(13, 8))
            fig.canvas.manager.set_window_title("Disk Cone: " + self.CD.name)
            fig.patch.set_facecolor("w")
            cmap = cc.m_colorwheel if self.colorblind_checkbox.get() else "hsv"
            h = axs[0].imshow(self.CD.RhoPsi[:, :, 0], cmap=cmap, interpolation="nearest", extent=[-1, 1, -1, 1], vmin=0, vmax=180)
            axs[0].set_title("Rho Test")
            ax_divider = make_axes_locatable(axs[0])
            cax = ax_divider.append_axes("right", size="7%", pad="2%")
            fig.colorbar(h, cax=cax)
            cmap = "viridis" if self.colorblind_checkbox.get() else "jet"
            h = axs[1].imshow(self.CD.RhoPsi[:, :, 1], cmap=cmap, interpolation="nearest", extent=[-1, 1, -1, 1], vmin=0, vmax=180)
            axs[1].set_title("Psi Test")
            ax_divider = make_axes_locatable(axs[1])
            cax = ax_divider.append_axes("right", size="7%", pad="2%")
            fig.colorbar(h, cax=cax)
            plt.subplots_adjust(wspace=0.4)
            for ax in axs:
                ax.set_xlabel("$B_2$")
                ax.set_ylabel("$A_2$")

    def variable_table_switch_callback(self):
        state = "normal" if self.variable_table_switch.get() == "on" else "disabled"
        for entries in self.variable_entries:
            entries.state(state)
        self.variable_entries[0].state("disabled")

    def click_callback(self, ax, canvas, method):
        if method == "click background":
            self.tabview.set("Intensity")
        if hasattr(self, "datastack"):
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

    def click_motion_notify_callback(self, event, hlines, ax, canvas):
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            if event.button is None:
                hlines[0].set_data([x, x], ylim)
                hlines[1].set_data(xlim, [y, y])
                canvas.draw()

    def click_background_button_press_callback(self, event, hlines, ax, canvas):
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                x1, x2 = round(x) - self.noise[1].get()//2, round(x) + self.noise[1].get()//2
                y1, y2 = round(y) - self.noise[2].get()//2, round(y) + self.noise[2].get()//2
                self.noise[3].set(np.mean(self.datastack.itot[y1:y2, x1:x2]) / self.stack.nangle * self.noise[0].get())
                canvas.mpl_disconnect(self.__cid1)
                canvas.mpl_disconnect(self.__cid2)
                for line in hlines:
                    line.remove()
                canvas.draw()

    def compute_angle(self):
        if hasattr(self, "stack"):
            self.tabview.set("Intensity")
            self.compute_angle_button.configure(fg_color=orange[1])
            hroi = ROI()
            self.__cid1 = self.intensity_canvas.mpl_connect("motion_notify_event", lambda event: self.compute_angle_motion_notify_callback(event, hroi))
            self.__cid2 = self.intensity_canvas.mpl_connect("button_press_event", lambda event: self.compute_angle_button_press_callback(event, hroi))

    def compute_angle_motion_notify_callback(self, event, roi):
        if event.inaxes == self.intensity_axis:
            x, y = event.xdata, event.ydata
            if ((event.button is None or event.button == 1) and roi.lines):
                roi.lines[-1].set_data([roi.previous_point[0], x], [roi.previous_point[1], y])
                self.intensity_canvas.draw()

    def compute_angle_button_press_callback(self, event, roi):
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
                    window = ShowInfo(message=" Angle is {:.2f} \u00b0 \n Distance is {} px".format(slope, int(dist)), image=self.icons["square"], button_labels = ["OK"])
                    window.get_buttons()[0].configure(command=lambda:window.withdraw())
                    for line in roi.lines:
                        line.remove()
                    self.intensity_canvas.draw()
                    self.compute_angle_button.configure(fg_color=orange[0])

    def define_variable_table(self, method):
        self.initialize_tables()
        self.clear_frame(self.variable_table_frame)
        self.variable_table_frame.configure(fg_color=self.left_frame.cget("fg_color"))
        CTk.CTkLabel(master=self.variable_table_frame, text="\nVariables\n", font=CTk.CTkFont(size=16)).grid(row=0, column=0, padx=0, pady=0)
        CTk.CTkLabel(master=self.variable_table_frame, text="      Min                         Max", text_color=text_color, font=CTk.CTkFont(weight="bold"), width=200).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="e")
        self.variable_table_switch = CTk.CTkSwitch(master=self.variable_table_frame, text="", progress_color=orange[0], command=self.variable_table_switch_callback, onvalue="on", offvalue="off", width=50)
        self.variable_table_switch.grid(row=1, column=0, padx=(10, 40), sticky="w")
        if method in ["1PF", "4POLAR 2D"]:
            variables = ["\u03C1 ", "\u03C8 "]
            vals = [(0, 180), (40, 180)]
        elif method in ["CARS", "SRS", "2PF"]:
            variables = ["\u03C1 ", "S2", "S4"]
            vals = [(0, 180), (0, 1), (-1, 1)]
        elif method == "SHG":
            variables = ["\u03C1 ", "S "]
            vals = [(0, 180), (-1, 1)]
        elif method == "4POLAR 3D":
            variables = ["\u03C1 ", "\u03C8 ", "\u03B7 "]
            vals = [(0, 180), (40, 180), (0, 90)]
        self.variable_entries = []
        self.variable_min = [tk.StringVar() for _ in range(len(variables))]
        self.variable_max = [tk.StringVar() for _ in range(len(variables))]
        self.variable_display = [tk.IntVar() for _ in range(len(variables))]
        for it, (var, val) in enumerate(zip(variables, vals)):
            self.variable_min[it].set(str(val[0]))
            self.variable_max[it].set(str(val[1]))
            frame = CTk.CTkFrame(master=self.variable_table_frame, fg_color=self.left_frame.cget("fg_color"))
            frame.grid(row=it+2, column=0)
            CTk.CTkCheckBox(master=frame, text=None, variable=self.variable_display[it], width=30).grid(row=0, column=0, padx=(20, 0))
            self.variable_entries += [DoubleEntry(frame, text=var, variables=(self.variable_min[it], self.variable_max[it]), row=0, column=1)]
        CTk.CTkLabel(master=frame, text=" ").grid(row=len(variables)+2, column=0)

    def method_dropdown_callback(self, method):
        self.define_variable_table(method)
        self.CD = Calibration(method)
        self.calib_dropdown.configure(values=self.CD.list(method), state="normal")
        self.calib_dropdown.set(self.CD.list(method)[0])
        self.calib_textbox.configure(state="normal")
        self.calib_textbox.delete("0.0", "end")
        self.calib_textbox.insert("0.0", self.CD.name)
        self.calib_textbox.configure(state="disabled")
        if method in ["2PF", "SRS", "SHG", "CARS"]:
            self.calib_dropdown.configure(state="disabled")
        if method.startswith("4POLAR"):
            self.polar_dropdown.configure(state="normal")
            window = ShowInfo(message="\n Perform: Select a beads file (*.tif)\n\n Load: Select a registration file (*.pyreg)\n\n Registration is performed with Whitelight.tif \n   which should be in the same folder as the beads file", image=self.icons["blur_circular"], button_labels=["Perform", "Load", "Cancel"], geometry=(420, 240))
            buttons = window.get_buttons()
            buttons[0].configure(command=lambda:self.perform_registration(window))
            buttons[1].configure(command=lambda:self.load_registration(window))
            buttons[2].configure(command=lambda:window.withdraw())
        else:
            self.polar_dropdown.configure(state="disabled")

    def pixelsperstick_spinbox_callback(self):
        figs = list(map(plt.figure, plt.get_fignums()))
        for fig in figs:
            fs = fig.canvas.manager.get_window_title()
            if ("Sticks" in fs) and (self.datastack.name in fs):
                ax = fig.axes[0]
                for _, var in enumerate(self.datastack.vars):
                    if (var.name == fs.split()[0]) and ("contour" not in fs):
                        for collection in ax.collections:
                            collection.remove()
                        p = self.get_sticks(var, self.datastack)
                        vmin, vmax = self.get_variable(_)[1:]
                        p.set_clim([vmin, vmax])
                        ax.add_collection(p)
            if ("Rho (vs contour) Sticks" in fs) and (self.datastack.name in fs):
                ax = fig.axes[0]
                for collection in ax.collections:
                    collection.remove()
                    p = self.get_sticks(self.datastack.added_vars[-1], self.datastack)
                    vmin, vmax = self.get_variable(0)[1:]
                    p.set_clim([vmin, vmax])
                    ax.add_collection(p)

    def perform_registration(self, window):
        window.withdraw()
        npix = 5
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        filename = fd.askopenfilename(title="Select a beads file", initialdir=initialdir, filetypes=[("TIFF files", "*.tiff"), ("TIF files", "*.tif")])
        beadstack = self.define_stack(filename)
        self.filename_label.configure(state="normal")
        self.filename_label.delete("0.0", "end")
        self.filename_label.insert("0.0", "")
        self.filename_label.configure(state="disabled")
        dark = self.compute_dark(beadstack, display=False)
        itot = np.sum((beadstack.values - dark) * (beadstack.values >= dark), axis=0)
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
        Iul = np.argmin(np.abs(centers[:, 0] + 1j * centers[:, 1]))
        Ilr = np.argmax(np.abs(centers[:, 0] + 1j * centers[:, 1]))
        ind = np.delete(ind, [Iul, Ilr])
        Iur = np.argmin(centers[ind, 1])
        Ill = np.argmax(centers[ind, 1])
        centers = centers[[Iul, ind[Iur], Ilr, ind[Ill]], :]
        ims = []
        for _ in range(4):
            xi, yi = centers[_, 0] - radius, centers[_, 1] - radius
            xf, yf = centers[_, 0] + radius, centers[_, 1] + radius
            im = itot[yi:yf, xi:xf]
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
            p, p0 = self.find_matches(points, points0)
            homography = cv2.findHomography(p, p0, cv2.RANSAC)[0]
            homographies += [homography]
            ims_ += [cv2.warpPerspective(im, homography, (width, height))]
        reg_ims = [cv2.merge([_, ims[0], _]) for _ in ims_]
        fig, axs = plt.subplots(2, 2)
        fig.canvas.manager.set_window_title("Quality of calibration: " + beadstack.name)
        fig.patch.set_facecolor("w")
        reg_ims[2:4] = reg_ims[3:1:-1]
        titles = ["UL", "UR", "LL", "LR"]
        for im, title, ax in zip(reg_ims, titles, axs.ravel()):
            ax.imshow(im)
            ax.set_title(title)
            ax.set_axis_off()
        self.registration = {"name_beads": beadstack.name, "radius": radius, "centers": centers, "homographies": homographies}
        window = ShowInfo(message=" Are you okay with this registration?", button_labels=["Yes", "Yes and Save", "No"], image=self.icons["blur_circular"], geometry=(380, 150))
        buttons = window.get_buttons()
        buttons[0].configure(command=lambda:self.yes_registration_callback(window, fig))
        buttons[1].configure(command=lambda:self.yes_save_registration_callback(window, fig, filename))
        buttons[2].configure(command=lambda:self.no_registration_callback(window, fig))

    def find_matches(self, a, b, tol=10):
        a_, b_ = (a, b) if len(b) >= len(a) else (b, a)
        cost = np.linalg.norm(a_[:, np.newaxis, :] - b_, axis=2)
        indices = linear_sum_assignment(cost)[1]
        a_, b_ = (a, b[indices]) if len(b) >= len(a) else (a[indices], b)
        dist = np.linalg.norm(a_ - b_, axis=1)
        return a_[dist <= tol], b_[dist <= tol]

    def yes_registration_callback(self, window, fig):
        plt.close(fig)
        window.withdraw()

    def yes_save_registration_callback(self, window, fig, filename):
        with open(os.path.splitext(filename)[0] + ".pyreg", "wb") as f:
            pickle.dump(self.registration, f, protocol=pickle.HIGHEST_PROTOCOL)
        plt.close(fig)
        window.withdraw()

    def no_registration_callback(self, window, fig):
        self.tform = []
        self.method.set("1PF")
        plt.close(fig)
        window.withdraw()

    def load_registration(self, window):
        window.withdraw()
        initialdir = self.stack.folder if hasattr(self, "stack") else "/"
        filename = fd.askopenfilename(title="Select a registration file (*.pyreg)", initialdir=initialdir, filetypes=[("PYREG-files", "*.pyreg")])
        with open(filename, "rb") as f:
            self.registration = pickle.load(f)

    def define_stack(self, filename, data=True):
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
        self.compute_dark(stack)
        return stack

    def define_datastack(self, stack):
        datastack = DataStack(stack)
        datastack.method = self.method.get()
        return datastack

    def open_file(self, filename):
        self.stack = self.define_stack(filename)
        if self.method.get().startswith("4POLAR"):
            self.stack = self.slice4polar(self.stack)
        if self.stack.nangle >= 2:
            self.stack_slider.configure(to=self.stack.nangle, number_of_steps=self.stack.nangle, state="normal")
        else:
            self.stack_slider.configure(state="disabled")
        self.filename_label.configure(state="normal")
        self.filename_label.delete("0.0", "end")
        self.filename_label.insert("0.0", self.stack.name)
        self.filename_label.configure(state="disabled")
        self.tabview.set("Intensity")
        self.compute_itot(self.stack)
        self.ilow_slider.configure(from_=np.amin(self.stack.itot), to=np.amax(self.stack.itot))
        self.ilow_slider.set(np.amin(self.stack.itot))
        self.ilow.set(self.stack.display.format(np.amin(self.stack.itot)))
        self.datastack = self.define_datastack(self.stack)
        self.datastack.itot = self.stack.itot
        if self.option.get().startswith("Mask"):
            self.mask = self.get_mask(self.datastack)
        self.represent_intensity(update=False)
        self.represent_thrsh(update=False)
        self.intensity_frame.update()
        self.thrsh_frame.update()

    def add_roi_callback(self):
        if hasattr(self, "stack"):
            self.tabview.set("Thresholding/Mask")
            self.add_roi_button.configure(fg_color=orange[1])
            hroi = ROI()
            self.__cid1 = self.thrsh_canvas.mpl_connect("motion_notify_event", lambda event: self.add_roi_motion_notify_callback(event, hroi))
            self.__cid2 = self.thrsh_canvas.mpl_connect("button_press_event", lambda event: self.add_roi_button_press_callback(event, hroi))

    def add_roi_motion_notify_callback(self, event, roi):
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

    def add_roi_button_press_callback(self, event, roi):
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

    def yes_add_roi_callback(self, window, roi):
        vertices = np.asarray([roi.x, roi.y])
        if self.datastack.rois:
            indx = self.datastack.rois[-1]["indx"] + 1
        else:
            indx = 1
        self.datastack.rois += [{"indx": indx, "label": (roi.x[0], roi.y[0]), "vertices": vertices, "ILow": self.ilow.get(), "name": "", "group": "", "select": True}]
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_canvas.draw()
        self.represent_intensity()
        self.represent_thrsh()
        if hasattr(self, "manager"):
            self.manager.update_manager(self.datastack.rois)

    def no_add_roi_callback(self, window, roi):
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_canvas.draw()

    def get_mask(self, datastack):
        mask = np.ones((datastack.height, datastack.width))
        if self.option.get().startswith("Mask"):
            mask_name = os.path.join(self.maskfolder, datastack.name + ".png")
            if os.path.isfile(mask_name):
                im_binarized = np.asarray(Image.open(mask_name), dtype=np.float64)
                mask = im_binarized / np.amax(im_binarized)
            else:
                window = ShowInfo(message=f" The corresponding mask for {datastack.name} could not be found\n Continuing without mask...", image=self.icons["layers_clear"], buttons_labels=["OK"])
                window.get_buttons()[0].configure(command=lambda:window.withdraw())
            if hasattr(self, "mask"):
                self.mask = mask
        return mask

    def analysis_callback(self):
        if self.option.get() == "Previous analysis":
            self.analysis_button.configure(image=self.icons["pause"])
            self.plot_data(self.datastack)
            self.analysis_button.configure(image=self.icons["play"])
        elif hasattr(self, "stack"):
            self.analysis_button.configure(image=self.icons["pause"])
            self.tabview.set("Intensity")
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
                        window = ShowInfo(message=" End of list", image=self.icons["check_circle"], button_labels=["OK"], fontsize=16)
                        window.get_buttons()[0].configure(command=lambda:window.withdraw())
                        self.initialize()
                self.analysis_button.configure(image=self.icons["play"])
            elif self.option.get().endswith("(auto)"):
                for file in self.filelist:
                    self.open_file(file)
                    self.analyze_stack(self.datastack)
                self.analysis_button.configure(image=self.icons["play"])
                self.open_file(self.filelist[0])
                window = ShowInfo(message=" End of list", image=self.icons["check_circle"], button_labels=["OK"], fontsize=16)
                window.get_buttons()[0].configure(command=lambda:window.withdraw())
                self.initialize()

    def close_callback(self):
        plt.close("all")

    def stack_slider_callback(self, value):
        self.stack_slider_label.configure(text=int(value))
        if value == 0:
            self.stack_slider_label.configure(text="T")
        if self.method.get().startswith("4POLAR"):
            labels = ["T", 0, 45, 90, 135]
            self.stack_slider_label.configure(text=labels[int(value)])
        self.represent_intensity()

    def ilow_slider_callback(self, value):
        if hasattr(self, "stack"):
            self.ilow.set(self.stack.display.format(value))
            if hasattr(self, "edge_contours"):
                self.compute_edges()
            self.represent_thrsh()

    def ilow2slider_callback(self, event):
        if event and hasattr(self, "stack"):
            self.ilow_slider.set(float(self.ilow.get()))
            if hasattr(self, "edge_contours"):
                self.compute_edges()
            self.represent_thrsh()

    def itot_callback(self, event):
        if event and hasattr(self, "stack"):
            if (self.method.get() == "1PF") and (float(self.dark.get()) < 480):
                self.dark.set(self.stack.display.format(self.calculated_dark))
            self.compute_itot(self.stack)
            if hasattr(self, "datastack"):
                self.datastack.itot = self.stack.itot
            self.represent_intensity(update=False)
            self.represent_thrsh(update=False)

    def rotation_callback(self, event):
        if event:
            self.represent_intensity(update=False)

    def transparency_slider_callback(self, value):
        if value <= 0.001:
            self.transparency_slider.set(0.001)
        self.represent_thrsh()

    def adjust(self, field, contrast, vmin, vmax):
        amount = 0.8
        blur = cv2.GaussianBlur(field, (5, 5), 1)
        sharpened = cv2.addWeighted(field, 1 + amount, blur, -amount, 0)
        sharpened = np.maximum(sharpened, vmin)
        sharpened = exposure.adjust_gamma((sharpened - vmin) / vmax, contrast) * vmax
        return sharpened

    def represent_intensity(self, update=True):
        itot = self.stack.itot if hasattr(self, "stack") else self.datastack.itot if hasattr(self, "datastack") else []
        if hasattr(self, "stack") or hasattr(self, "datastack"):
            if self.stack_slider.get() == 0:
                field = itot
                vmin, vmax = np.amin(itot), np.amax(itot)
            elif hasattr(self, "stack") and (self.stack_slider.get() <= self.stack.nangle):
                field = self.stack.values[int(self.stack_slider.get())-1]
                vmin, vmax = np.amin(self.stack.values), np.amax(self.stack.values)
            field_im = self.adjust(field, self.contrast_intensity_slider.get(), vmin, vmax)
            if int(self.rotation[1].get()) != 0:
                field_im = rotate(field_im, int(self.rotation[1].get()), reshape=False, mode="constant", cval=vmin)
            if update:
                self.intensity_im.set_data(field_im)
            else:
                self.intensity_axis.clear()
                self.intensity_axis.set_axis_off()
                self.intensity_im = self.intensity_axis.imshow(field_im, cmap="gray", interpolation="nearest")
                self.intensity_frame.update()
                self.intensity_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
                self.intensity_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
            self.intensity_im.set_clim(vmin, vmax)
            self.clear_patches(self.intensity_axis, self.intensity_fig.canvas)
            if hasattr(self, "datastack"):
                self.add_patches(self.datastack, self.intensity_axis, self.intensity_fig.canvas)
            self.intensity_canvas.draw()

    def represent_thrsh(self, update=True):
        if hasattr(self, "stack"):
            field = self.stack.itot.copy()
            if self.option.get().startswith("Mask"):
                field *= self.mask
            vmin, vmax = np.amin(self.stack.itot), np.amax(self.stack.itot)
            field_im = self.adjust(self.stack.itot, self.contrast_thrsh_slider.get(), vmin, vmax)
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
                self.thrsh_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
                self.thrsh_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
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

    def compute_itot(self, stack):
        dark = float(self.dark.get())
        sumcor = np.sum((stack.values - dark) * (stack.values >= dark), axis=0)
        bin_shape = [self.bin_spinboxes[_].get() for _ in range(2)]
        if sum(bin_shape) != 2:
            stack.itot = convolve2d(sumcor, np.ones(bin_shape), mode="same") / (bin_shape[0] * bin_shape[1])
        else:
            stack.itot = sumcor

    def compute_dark(self, stack, display=True):
        SizeCell = 20
        NCellHeight = int(np.floor(stack.height / SizeCell))
        NCellWidth = int(np.floor(stack.width / SizeCell))
        cropIm = stack.values[:, :SizeCell * NCellHeight, :SizeCell * NCellWidth]
        cropIm = np.moveaxis(cropIm, 0, -1)
        ImCG = np.asarray(np.split(np.asarray(np.split(cropIm, NCellWidth, axis=1)), NCellHeight, axis=1))
        mImCG = np.zeros((NCellHeight, NCellWidth))
        for it in range(NCellHeight):
            for jt in range(NCellWidth):
                cell = ImCG[it, jt, :, :, 0]
                mImCG[it, jt] = np.mean(cell[cell != 0])
        IndI, IndJ = np.where(mImCG == np.amin(mImCG))
        cell = ImCG[IndI, IndJ, :, :, :]
        dark = np.mean(cell[cell != 0])
        if display:
            self.calculated_dark = dark
            self.calculated_dark_label.configure(text="Calculated dark value = " + stack.display.format(dark))
            if self.dark_switch.get() == "off":
                self.dark.set(stack.display.format(dark))
        else:
            return dark

    def circularmean(self, rho):
        return np.mod(np.angle(np.mean(np.exp(2j * np.deg2rad(rho))), deg=True), 360) / 2

    def wrapto180(self, rho):
        return np.angle(np.exp(1j * np.deg2rad(rho)), deg=True)

    def get_variable(self, indx):
        display = self.variable_display[indx].get()
        vmin, vmax = float(self.variable_min[indx].get()), float(self.variable_max[indx].get())
        return display, vmin, vmax

    def plot_histo(self, var, datastack, vmin, vmax, roi_map, roi=[]):
        if self.show_table[2].get() or self.save_table[2].get():
            suffix = "for ROI " + str(roi["indx"]) if roi else ""
            fig = plt.figure(figsize=self.figsize)
            fig.canvas.manager.set_window_title(var.name + " Histogram" + suffix + ": " + self.datastack.name)
            mask = (roi_map == roi["indx"]) if roi else (roi_map == 1)
            data_vals = var.values[mask * np.isfinite(var.values)]
            norm = mpl.colors.Normalize(vmin, vmax)
            cmap = var.colormap[self.colorblind_checkbox.get()]
            if isinstance(cmap, str):
                cmap = mpl.colormaps[cmap] 
            bins = np.linspace(vmin, vmax, 60)
            if var.type_histo == "normal":
                ax = plt.gca()
                n, bins, patches = ax.hist(data_vals, bins=bins, linewidth=0.5)
                bin_centers = (bins[:-1] + bins[1:]) / 2
                for bin, patch in zip(bin_centers, patches):
                    color = cmap(norm(bin))
                    patch.set_facecolor(color)
                    patch.set_edgecolor("k")
                ax.set_xlim((vmin, vmax))
                ax.set_xlabel(var.latex, fontsize=20)
                text = var.latex + " = " + "{:.2f}".format(np.mean(data_vals)) + " $\pm$ " "{:.2f}".format(np.std(data_vals))
                ax.annotate(text, xy=(0.3, 1.05), xycoords="axes fraction", fontsize=14)
            elif var.type_histo.startswith("polar"):
                ax = plt.subplot(projection="polar")
                if var.type_histo == "polar1":
                    if var.name == "Rho":
                        data_vals = np.mod(2 * (data_vals + float(self.rotation[1].get())), 360) / 2
                    meandata = self.circularmean(data_vals)
                    std = np.std(self.wrapto180(2 * (data_vals - meandata)) / 2)
                elif var.type_histo == "polar2":
                    ax.set_theta_zero_location("N")
                    ax.set_theta_direction(-1)
                    meandata = np.mean(data_vals)
                    std = np.std(data_vals)
                elif var.type_histo == "polar3":
                    ax.set_theta_zero_location("E")
                    data_vals[data_vals >= 90] = 180 - data_vals[data_vals >= 90]
                    meandata = self.circularmean(data_vals)
                    std = np.std(self.wrapto180(2 * (data_vals - meandata)) / 2)
                    norm = mpl.colors.Normalize(0, 180)
                distribution, bin_edges = np.histogram(data_vals, bins=bins, range=(vmin, vmax))
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                width = np.deg2rad(bins[1] - bins[0])
                colors = cmap(norm(bins))
                ax.bar(np.deg2rad(bin_centers), distribution, width=width, color=colors, edgecolor="k", linewidth=0.5)
                num = 10**(len(str(np.amax(distribution))) - 2)
                ax.set_rticks(np.floor(np.linspace(0, np.max(distribution), 3) / num) * num)
                ax.set_thetamin(vmin)
                ax.set_thetamax(vmax)
                text = var.latex + " = " + "{:.2f}".format(meandata) + " $\pm$ " "{:.2f}".format(std)
                if var.type_histo == "polar1":
                    ax.annotate(text, xy=(0.3, 0.95), xycoords="axes fraction", fontsize=14)
                else:
                    ax.annotate(text, xy=(0.7, 0.95), xycoords="axes fraction", fontsize=14)
            if self.save_table[2].get():
                suffix = "_perROI_" + str(roi["indx"]) if roi else ""
                filename = datastack.filename + "_Histo" + var.name + suffix
                plt.savefig(filename + ".tif", bbox_inches="tight")
            if not self.show_table[2].get():
                plt.close(fig)

    def add_intensity(self, intensity, ax):
        vmin, vmax = np.amin(intensity), np.amax(intensity)
        field = self.adjust(intensity, self.contrast_intensity_slider.get(), vmin, vmax)
        if int(self.rotation[1].get()) != 0:
            field = rotate(field, int(self.rotation[1].get()), reshape=False, mode="constant", cval=vmin)
        h = ax.imshow(field, cmap="gray", interpolation="nearest", vmin=vmin, vmax=vmax)

    def add_patches(self, datastack, ax, fig, rotation=True):
        if len(datastack.rois):
            for roi in datastack.rois:
                if roi["select"]:
                    vertices = roi["vertices"]
                    coord = roi["label"][0], roi["label"][1]
                    if (float(self.rotation[1].get()) != 0) and rotation:
                        theta = np.deg2rad(float(self.rotation[1].get()))
                        x0, y0 = datastack.width / 2, datastack.height / 2
                        coord = x0 + (coord[0] - x0) * np.cos(theta) + (coord[1] - y0) * np.sin(theta), y0 - (coord[0] - x0) * np.sin(theta) + (coord[1] - y0) * np.cos(theta)
                        vertices = np.asarray([x0 + (vertices[0] - x0) * np.cos(theta) + (vertices[1] - y0) * np.sin(theta), y0 - (vertices[0] - x0) * np.sin(theta) + (vertices[1] - y0) * np.cos(theta)])
                    ax.add_patch(Polygon(vertices.T, facecolor="none", edgecolor="white"))
                    ax.text(coord[0], coord[1], str(roi["indx"]), color="w")
            fig.draw()

    def plot_composite(self, var, datastack, vmin, vmax):
        if self.show_table[0].get() or self.save_table[0].get():
            fig = plt.figure(figsize=self.figsize)
            fig.canvas.manager.set_window_title(var.name + " Composite: " + datastack.name)
            fig.patch.set_facecolor("w")
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            self.add_intensity(datastack.itot, ax)
            field = var.values
            if int(self.rotation[1].get()) != 0:
                if var.name == "Rho":
                    field = np.mod(2 * (field + int(self.rotation[1].get())), 360) / 2
                field = rotate(field, int(self.rotation[1].get()), reshape=False, order=0, mode="constant")
                field[field == 0] = np.nan
            h = ax.imshow(field, vmin=vmin, vmax=vmax, cmap=var.colormap[self.colorblind_checkbox.get()], interpolation="nearest")
            if self.colorbar_checkbox.get():
                ax_divider = make_axes_locatable(ax)
                cax = ax_divider.append_axes("right", size="7%", pad="2%")
                fig.colorbar(h, cax=cax)
            if self.save_table[0].get():
                suffix = "_" + var.name + "Composite"
                plt.savefig(datastack.filename + suffix + ".tif", bbox_inches='tight')
            if not self.show_table[0].get():
                plt.close(fig)

    def individual_fit_button_press_callback(self, event, hlines, ax, canvas):
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                x, y = int(round(x)), int(round(y))
                if np.isfinite(self.datastack.vars[0].values[y, x]):
                    fig_, axs = plt.subplots(2, 1, figsize=(12, 8))
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
                    titles += ["$\chi_2$ = " + "{:.2f}".format(self.datastack.chi2[y, x]) + ",   $I$ =  " + self.datastack.display.format(self.datastack.itot[y, x])]
                    ylabels = ["counts", "residuals"]
                    axs[0].plot(indx, signal, "*", indx, signal_fit, "r-", lw=2)
                    axs[1].plot(indx, signal - signal_fit, "+", indx, 2 * np.sqrt(signal_fit), "r-", indx, -2 * np.sqrt(signal_fit), "r-", lw=2)
                    polardir = -1 if self.polar_dir.get() == "clockwise" else 1 
                    def indx2alpha(k):
                        return polardir * 180 / self.stack.nangle * (k - 1) + self.offset_angle.get()
                    def alpha2indx(a):
                        return polardir * self.stack.nangle / 180 * (a - self.offset_angle.get()) + 1
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

    def get_sticks(self, var, datastack):
        L, W = 6, 0.2
        l, w = L / 2, W / 2
        rho = datastack.vars[0]
        rho_ = rho.values[::int(self.pixelsperstick_spinboxes[1].get()), ::int(self.pixelsperstick_spinboxes[0].get())]
        data_ = var.values[::int(self.pixelsperstick_spinboxes[1].get()), ::int(self.pixelsperstick_spinboxes[0].get())]
        Y, X = np.mgrid[:datastack.height:int(self.pixelsperstick_spinboxes[1].get()), :datastack.width:int(self.pixelsperstick_spinboxes[0].get())]
        X, Y = X[np.isfinite(data_)], Y[np.isfinite(data_)]
        data_, rho_ = data_[np.isfinite(data_)], rho_[np.isfinite(data_)]
        if var.name == "Rho":
            stick_colors = np.mod(2 * (data_ + float(self.rotation[1].get())), 360) / 2
        else:
            stick_colors = data_
        cosd = np.cos(np.deg2rad(rho_))
        sind = np.sin(np.deg2rad(rho_))
        vertices = np.array([[X + l * cosd + w * sind, X - l * cosd + w * sind, X - l * cosd - w * sind, X + l * cosd - w * sind], [Y - l * sind + w * cosd, Y + l * sind + w * cosd, Y + l * sind - w * cosd, Y - l * sind - w * cosd]])
        if float(self.rotation[1].get()) != 0:
            theta = np.deg2rad(float(self.rotation[1].get()))
            x0, y0 = self.stack.width / 2, self.stack.height / 2
            vertices = np.asarray([x0 + (vertices[0] - x0) * np.cos(theta) + (vertices[1] - y0) * np.sin(theta), y0 - (vertices[0] - x0) * np.sin(theta) + (vertices[1] - y0) * np.cos(theta)])
        vertices = np.swapaxes(vertices, 0, 2)
        return PolyCollection(vertices, cmap=var.colormap[self.colorblind_checkbox.get()], lw=2, array=stick_colors)

    def plot_sticks(self, var, datastack, vmin, vmax):
        if self.show_table[1].get() or self.save_table[1].get():
            fig = plt.figure(figsize=self.figsize)
            fig.canvas.manager.set_window_title(var.name + " Sticks: " + datastack.name)
            fig.patch.set_facecolor("w")
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            self.add_intensity(datastack.itot, ax)
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

    def plot_intensity(self, datastack):
        if self.show_table[3].get() or self.save_table[3].get():
            fig = plt.figure(figsize=self.figsize)
            fig.canvas.manager.set_window_title("Intensity: " + datastack.name)
            fig.patch.set_facecolor("w")
            ax = plt.gca()
            ax.axis(self.add_axes_checkbox.get())
            self.add_intensity(datastack.itot, ax)
            self.add_patches(datastack, ax, fig.canvas)
            if self.edge_detection_switch.get() == "on":
                for contour in self.edge_contours:
                    angles = np.mod(2 * self.angle_edge(contour)[0], 360) / 2
                    cmap = cc.m_colorwheel if self.colorblind_checkbox.get() else "hsv"
                    if float(self.rotation[1].get()) != 0:
                        angles = np.mod(2 * (angles + float(self.rotation[1].get())), 360) / 2
                        theta = np.deg2rad(float(self.rotation[1].get()))
                        x0, y0 = self.stack.width / 2, self.stack.height / 2
                        contour = np.asarray([x0 + (contour[:, 0] - x0) * np.cos(theta) + (contour[:, 1] - y0) * np.sin(theta), y0 - (contour[:, 0] - x0) * np.sin(theta) + (contour[:, 1] - y0) * np.cos(theta)])
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

    def plot_data(self, datastack, roi_map=[]):
        self.plot_intensity(datastack)
        vars = copy.deepcopy(datastack.vars)
        if len(roi_map) == 0:
            roi_map, mask = self.compute_roi_map(datastack)
            for var in vars:
                var.values *= mask
                var.values[var.values==0] = np.nan
        for _, var in enumerate(vars):
            display, vmin, vmax = self.get_variable(_)
            if display:
                self.plot_composite(var, datastack, vmin, vmax)
                self.plot_sticks(var, datastack, vmin, vmax)
                if self.per_roi.get():
                    for roi in datastack.rois:
                        if roi["select"]:
                            self.plot_histo(var, datastack, vmin, vmax, roi_map, roi=roi)
                else:
                    self.plot_histo(var, datastack, vmin, vmax, roi_map, roi=[])
        if self.edge_detection_switch.get() == "on":
            display, vmin, vmax = self.get_variable(0)
            var = datastack.added_vars[-1]
            if display:
                self.plot_composite(var, datastack, vmin, vmax)
                self.plot_sticks(var, datastack, vmin, vmax)
                if self.per_roi.get():
                    for roi in datastack.rois:
                        if roi["select"]:
                            self.plot_histo(var, datastack, vmin, vmax, roi_map, roi=roi)
                            var.type_histo = "polar3"
                            self.plot_histo(var, datastack, 0, 90, roi_map, roi=roi)
                else:
                    self.plot_histo(var, datastack, vmin, vmax, roi_map, roi=[])
                    var.type_histo = "polar3"
                    self.plot_histo(var, datastack, 0, 90, roi_map, roi=[])

    def save_data(self, datastack, roi_map=[]):
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
            window = ShowInfo(message=" Compressing and saving data...", image=self.icons["save"], geometry=(350, 80))[0]
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
                im = self.adjust(field, self.contrast_intensity_slider.get(), vmin, vmax)
                if int(self.rotation[1].get()) != 0:
                    im = rotate(im, int(self.rotation[1].get()), reshape=False, mode="constant", cval=vmin)
                if hasattr(self, "xlim"):
                    im = im[self.ylim[0].get():self.ylim[1].get(), self.xlim[0].get():self.xlim[1].get()]
                im = (255 * im / vmax).astype(np.uint8)
                images.append(Image.fromarray(im, mode='P'))
            images[0].save(filename, save_all=True, append_images=images[1:], optimize=False, duration=200, loop=0)

    def return_vecexcel(self, datastack, roi_map, roi=[]):
        mask = (roi_map == roi["indx"]) if roi else (roi_map == 1)
        ilow = float(roi["ILow"]) if roi else float(self.ilow.get())
        rho = datastack.vars[0].values
        data_vals = np.mod(2 * (rho[mask * np.isfinite(rho)] + float(self.rotation[1].get())), 360) / 2
        n = data_vals.size
        meandata = self.circularmean(data_vals)
        deltarho = self.wrapto180(2 * (data_vals - meandata)) / 2
        title = []
        if roi:
            results = [self.stack.name, roi["indx"], roi["name"], roi["group"], meandata, np.std(deltarho), np.mean(deltarho)]
        else:
            results = [self.stack.name, "all", "", "", meandata, np.std(deltarho), np.mean(deltarho)]
        if self.edge_detection_switch.get() == "on":
            title += ["MeanRho_c_180", "StdRho_c_180", "MeanDeltaRho_c_180", "MeanRho_c_90", "StdRho_c_90", "MeanDeltaRho_c_90"]
            rho_c_180 = datastack.added_vars[-1].values
            rho_c_90 = rho_c_180.copy()
            rho_c_90[rho_c_90 >= 90] = 180 - rho_c_90[rho_c_90 >= 90]
            data_vals = rho_c_180[mask * np.isfinite(rho) * np.isfinite(rho_c_180)]
            meandata = self.circularmean(data_vals)
            deltarho = self.wrapto180(2 * (data_vals - meandata)) / 2
            results += [meandata, np.std(deltarho), np.mean(deltarho)]
            data_vals = rho_c_90[mask * np.isfinite(rho) * np.isfinite(rho_c_90)]
            meandata = self.circularmean(data_vals)
            deltarho = self.wrapto180(2 * (data_vals - meandata)) / 2
            results += [meandata, np.std(deltarho), np.mean(deltarho)]
        for var in datastack.vars[1:]:
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
        results += [float(self.dark.get()), self.offset_angle.get(), self.polar_dir.get(), self.bin_spinboxes[0].get(), self.bin_spinboxes[1].get()]
        return results, title

    def save_mat(self, datastack, roi_map, roi=[]):
        if self.extension_table[2].get():
            mask = (roi_map == roi["indx"]) if roi else (roi_map == 1)
            dict_ = {"dark": datastack.dark}
            for var in datastack.vars:
                data = var.values[mask * np.isfinite(var.values)]
                dict_.update({var.name: data})
            for var in datastack.added_vars:
                data = var.values[mask * np.isfinite(var.values)]
                dict_.update({var.name: data})
            suffix = "_ROI" + str(roi["indx"]) if roi else ""
            filename = datastack.filename + suffix + ".mat"
            savemat(filename, dict_)

    def compute_roi_map(self, datastack):
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
        mask *= (datastack.itot >= roi_ilow_map) * (roi_map > 0)
        return roi_map, (mask != 0)

    def slice4polar(self, stack):
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
            window = ShowInfo(message=" No registration", image=self.icons["blur_circular"], button_labels=["OK"], fontsize=16)
            window.get_buttons()[0].configure(command=lambda:window.withdraw())
            self.method.set("1PF")

    def analyze_stack(self, datastack):
        chi2threshold = 500
        shape = (self.stack.height, self.stack.width)
        roi_map, mask = self.compute_roi_map(datastack)
        datastack.dark = float(self.dark.get())
        field = self.stack.values - datastack.dark - float(self.noise[3].get())
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
            alpha = polardir * np.linspace(0, 180, self.stack.nangle, endpoint=False) + self.offset_angle.get()
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
        rho_ = Variable(datastack)
        rho_.name, rho_.latex = "Rho", r"$\rho$"
        rho_.type_histo = "polar1"
        rho_.colormap = ["hsv", cc.m_colorwheel]
        if self.method.get() == "1PF":
            mask *= (np.abs(a2) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            a2_vals = np.moveaxis(np.asarray([a2.real[mask].flatten(), a2.imag[mask].flatten()]), 0, -1)
            rho, psi = np.moveaxis(interpn(self.CD.xy, self.CD.RhoPsi, a2_vals), 0, 1)
            ixgrid = mask.nonzero()
            rho_.values[ixgrid] = rho
            rho_.values[np.isfinite(rho_.values)] = np.mod(2 * (rho_.values[np.isfinite(rho_.values)] + float(self.rotation[0].get())), 360) / 2 
            psi_ = Variable(datastack)
            psi_.name, psi_.latex = "Psi", "$\psi$"
            psi_.values[ixgrid] = psi
            mask *= np.isfinite(rho_.values) * np.isfinite(psi_.values)
            datastack.vars = [rho_, psi_]
        elif self.method.get() in ["CARS", "SRS", "2PF"]:
            mask *= (np.abs(a2) < 1) * (np.abs(a4) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho_.values[mask] = np.rad2deg(np.angle(a2[mask])) / 2
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            s2_ = Variable(datastack)
            s2_.name, s2_.latex = "S2", "$S_2$"
            s2_.values[mask] = 1.5 * np.abs(a2[mask])
            s4_ = Variable(datastack)
            s4_.name, s4_.latex = "S4", "$S_4$"
            s4_.values[mask] = 6 * np.abs(a4[mask]) * np.cos(4 * (0.25 * np.angle(a4[mask]) - np.deg2rad(rho_.values[mask])))
            datastack.vars = [rho_, s2_, s4_]
        elif self.method.get() == "SHG":
            mask *= (np.abs(a2) < 1) * (np.abs(a4) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho_.values[mask] = np.rad2deg(np.angle(a2[mask])) / 2
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            s_shg_ = Variable(datastack)
            s_shg_.name, s_shg_.latex = "S_SHG", "$S_\mathrm{SHG}$"
            s_shg_.values[mask] = -0.5 * (np.abs(a4[mask]) - np.abs(a2[mask])) / (np.abs(a4[mask]) + np.abs(a2[mask])) - 0.65
            datastack.vars = [rho_, s_shg_]
        elif self.method.get() == "4POLAR 3D":
            mask *= (lam < 1/3) * (lam > 0) * (pzz > lam)
            rho_.values[mask] = 0.5 * np.rad2deg(np.arctan2(puv[mask], pxy[mask]))
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable(datastack)
            psi_.name, psi_.latex = "Psi", "$\psi$"
            psi_.values[mask] = 2 * np.rad2deg(np.arccos((-1 + np.sqrt(9 - 24 * lam[mask])) / 2))
            eta_ = Variable(datastack)
            eta_.name, eta_.latex = "Eta", "$\eta$"
            eta_.values[mask] = np.rad2deg(np.arccos(np.sqrt((pzz[mask] - lam[mask]) / (1 - 3 * lam[mask]))))
            eta_.type_histo = "polar2"
            eta_.colormap = ["plasma", "plasma"]
            datastack.vars = [rho_, psi_, eta_]
        elif self.method.get() == "4POLAR 2D":
            mask *= (lam < 1/3) * (lam > 0)
            rho_.values[mask] = 0.5 * np.rad2deg(np.arctan2(puv[mask], pxy[mask]))
            rho_.values[mask] = np.mod(2 * (rho_.values[mask] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable(datastack)
            psi_.name, psi_.latex = "Psi", "$\psi$"
            psi_.values[mask] = 2 * np.rad2deg(np.arccos((-1 + np.sqrt(9 - 24 * lam[mask])) / 2))
            datastack.vars = [rho_, psi_]
        a0[np.logical_not(mask)] = np.nan
        X, Y = np.meshgrid(np.arange(datastack.width), np.arange(datastack.height))
        X, Y = X.astype(np.float64), Y.astype(np.float64)
        X[np.logical_not(mask)] = np.nan
        Y[np.logical_not(mask)] = np.nan
        X_, Y_, Int_ = Variable(datastack), Variable(datastack), Variable(datastack)
        X_.name, Y_.name, Int_.name = "X", "Y", "Int"
        X_.values, Y_.values, Int_.values = X, Y, a0
        datastack.added_vars = [X_, Y_, Int_]
        if self.edge_detection_switch.get() == "on":
            rho_ct = Variable(datastack)
            rho_ct.name, rho_ct.latex = "Rho (vs contour)", r"$\rho_c$"
            rho_ct.type_histo = "polar1"
            rho_ct.colormap = ["hsv", cc.m_colorwheel]
            vals = self.define_rho_ct(self.edge_contours)
            filter = np.isfinite(rho_.values) * np.isfinite(vals)
            rho_ct.values[filter] = np.mod(2 * (rho_.values[filter] - vals[filter]), 360) / 2
            datastack.added_vars += [rho_ct]
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

class Stack():
    def __init__(self, filename):
        self.filename = os.path.splitext(filename)[0]
        self.folder = str(pathlib.Path(filename).parent)
        self.name = str(pathlib.Path(filename).stem)
        self.height, self.width, self.nangle = 0, 0, 0
        self.display = "{:.0f}"
        self.values = []
        self.itot = []

class DataStack():
    def __init__(self, stack):
        self.filename = stack.filename
        self.folder = stack.folder
        self.name = stack.name
        self.method = ""
        self.height, self.width, self.nangle = stack.height, stack.width, stack.nangle
        self.display = stack.display
        self.dark = 0
        self.itot = stack.itot
        self.field = []
        self.field_fit = []
        self.chi2 = []
        self.rois = []
        self.vars = []
        self.added_vars = []

class Variable():
    def __init__(self, datastack):
        self.name = ""
        self.latex = ""
        self.values = np.nan * np.ones((datastack.height, datastack.width))
        self.type_histo = "normal"
        self.colormap = ["jet", "viridis"]

class ROI:
    def __init__(self):
        self.start_point = []
        self.end_point = []
        self.previous_point = []
        self.x = []
        self.y = []
        self.lines = []

class Calibration():

    dict_1pf = {"no distortions": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 0), "488 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 175), "561 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 120), "640 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 125), "488 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga0_Pa20_Ta45_Gb-0.1_Pb0_Tb0_Gc-0.1_Pc0_Tc0", 0), "561 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga-0.2_Pa0_Ta0_Gb0.1_Pb0_Tb0_Gc-0.2_Pc0_Tc0", 0), "640 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga-0.2_Pa0_Ta45_Gb0.1_Pb0_Tb45_Gc-0.1_Pc0_Tc0", 0), "488 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb20_Tb45_Gc-0.2_Pc0_Tc0", 0), "561 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.2_Pa0_Ta0_Gb0.2_Pb20_Tb0_Gc-0.2_Pc0_Tc0", 0), "640 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc-0.2_Pc0_Tc0", 0), "488 nm (before 13/12/2019)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc0.1_Pc0_Tc0", 0), "561 nm (before 13/12/2019)": ("Disk_Ga0.1_Pa0_Ta45_Gb-0.1_Pb20_Tb0_Gc-0.1_Pc0_Tc0", 0), "640 nm (before 13/12/2019)": ("Disk_Ga-0.1_Pa10_Ta0_Gb0.1_Pb30_Tb0_Gc0.2_Pc0_Tc0", 0), "other": (None, 0)}

    folder_1pf = os.path.join(os.path.dirname(os.path.realpath(__file__)), "diskcones")

    dict_4polar = {"Calib_20221102": ("Calib_20221102", 0), "Calib_20221011": ("Calib_20221011", 0), "other": (None, 0)}

    folder_4polar = os.path.join(os.path.dirname(os.path.realpath(__file__)), "calibration")

    def __init__(self, method, label=None):
        if label is None:
            if method == "1PF":
                label = "no distortions"
            elif method.startswith("4POLAR"):
                label = "Calib_20221102"
        if method == "1PF":
            vars = Calibration.dict_1pf.get(label, (None, 0))
            folder = Calibration.folder_1pf
        elif method.startswith("4POLAR"):
            vars = Calibration.dict_4polar.get(label, (None, 0))
            folder = Calibration.folder_4polar
        if method in ["1PF", "4POLAR 2D", "4POLAR 3D"]:
            if label == "other":
                initialdir = self.stack.folder if hasattr(self, "stack") else "/"
                file = pathlib.Path(fd.askopenfilename(title='Select file', initialdir=initialdir, filetypes=[("MAT-files", "*.mat")]))
                folder = str(file.parent)
                vars = (str(file.stem), 0)
            disk = loadmat(os.path.join(folder, vars[0] + ".mat"))
            if method == "1PF" and vars[0].startswith("Disk"):
                self.RhoPsi = np.moveaxis(np.stack((np.array(disk["RoTest"], dtype=np.float64), np.array(disk["PsiTest"], dtype=np.float64))), 0, -1)
                self.xy = 2 * (np.linspace(-1, 1, int(disk["NbMapValues"]), dtype=np.float64),)
            elif method.startswith("4POLAR") and vars[0].startswith("Calib"):
                self.invKmat_2D = np.linalg.inv(np.array(disk["K2D"], dtype=np.float64))
                self.invKmat_3D = np.linalg.inv(np.array(disk["K3D"], dtype=np.float64))
            else:
                showerror("Calibration data", "Incorrect disk cone or calibration data\n Download another file", icon="error")
                vars = (" ", 0)
        else:
            vars = (" ", 0)
        self.name = vars[0]
        self.offset_default = vars[1]

    def list(self, method):
        if method == "1PF":
            return [key for key in Calibration.dict_1pf.keys()]
        elif method.startswith("4POLAR"):
            return [key for key in Calibration.dict_4polar.keys()]
        else:
            return " "

class NToolbar2Tk(NavigationToolbar2Tk):

    folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")

    def __init__(self, canvas, window, pack_toolbar):
        super().__init__(canvas=canvas, window=window, pack_toolbar=pack_toolbar)
        self._buttons = {}
        self.toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        (None, None, None, None),
        ('Back', 'Back to previous view', 'backward', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        (None, None, None, None),
        ('Pan', 'Left button pans, Right button zooms\n x/y fixes axis, CTRL fixes aspect', 'pan', 'pan'),
        ('Zoom', 'Zoom to rectangle\n x/y fixes axis', 'zoom', 'zoom'),
        (None, None, None, None),
        ('Save', 'Save the figure', 'save', 'save_figure'),)
        tk.Frame.__init__(self, master=window)
        for text, tooltip_text, image_file, callback in self.toolitems:
            if text is None:
                self._Spacer()
            else:
                im = os.path.join(NToolbar2Tk.folder, image_file + ".png")
                self._buttons[text] = button = self._Button(text=text, image_file=im, toggle=callback in ["zoom", "pan"], command=getattr(self, callback),)
                if tooltip_text is not None:
                    ToolTip.createToolTip(button, tooltip_text)
        self._label_font = CTk.CTkFont(size=12)
        label = tk.Label(master=self, font=self._label_font, text='\N{NO-BREAK SPACE}\n\N{NO-BREAK SPACE}')
        label.pack(side=tk.RIGHT)
        self.message = tk.StringVar(master=self)
        self._message_label = tk.Label(master=self, font=self._label_font, textvariable=self.message, justify=tk.RIGHT, fg=text_color)
        self._message_label.pack(side=tk.RIGHT)

    def _Button(self, text, image_file, toggle, command):
        b = super()._Button(text=text, image_file=image_file, toggle=toggle, command=command)
        if image_file is not None:
            NavigationToolbar2Tk._set_image_for_button(self, b)
        else:
            b.configure(font=self._label_font)
        b.pack(side=tk.LEFT)
        return b

    def destroy(self, *args):
        tk.Frame.destroy(self)

class ToolTip:
    @staticmethod
    def createToolTip(widget, text):
        tooltip = ToolTip(widget)
        def enter(event):
            tooltip.showtip(text)
        def leave(event):
            tooltip.hidetip()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + self.widget.winfo_width()
        y = y + self.widget.winfo_rooty()
        self.tipwindow = tw = CTk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            tw.tk.call("::tk::unsupported::MacWindowStyle", "style", tw._w, "help", "noActivates")
        except tk.TclError:
            pass
        label_font = CTk.CTkFont(size=12)
        label = tk.Label(tw, text=self.text, font=label_font, justify=tk.LEFT, relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ROIManager(CTk.CTkToplevel):
    labels = ["indx", "name", "group"]
    widths = [40, 250, 90]
    button_labels = ["Commit", "Save", "Load", "Delete", "Delete All"]
    manager_size = lambda w, h: f"{w+40}x{h+84}"
    cmax = len(labels)

    def __init__(self, *args, rois=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes("-topmost", "true")
        self.title("ROI Manager")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        cell_height = 20
        self.sheet_height = lambda cell_h, rois_: 20 + (cell_h + 3) * (len(rois_) + 1)
        widths = ROIManager.widths + [70, 70]
        self.sheet_width = sum(widths) + 2

        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, rois)) + f"+1200+200")

        if sys.platform == "darwin":
            font = ("Arial Rounded MT Bold", 14, "normal")
            header_font = ("Arial Rounded MT Bold", 16, "bold")
        elif sys.platform == "win32":
            font = ("Arial Rounded MT", 14, "normal")
            header_font = ("Arial Rounded MT", 16, "bold")

        labels_ = ROIManager.labels + ["select", "delete"]
        labels_[0] = "ROI"
        data = [[roi[label] for label in ROIManager.labels] for roi in rois]
        self.sheet = tksheet.Sheet(self, data=data, headers=labels_, font=font, header_font=header_font, align="w", show_row_index=False, width=self.sheet_width, height=self.sheet_height(cell_height, rois), frame_bg=text_color, table_bg=gray[1], top_left_bg=gray[1], header_hidden_columns_expander_bg=gray[1], header_fg=text_color, header_bg=orange[0], header_grid_fg=gray[1], table_grid_fg=text_color, header_selected_cells_bg=orange[1], table_selected_cells_border_fg=orange[0], show_x_scrollbar=False, show_y_scrollbar=False, show_top_left=False, enable_edit_cell_auto_resize=False, auto_resize_default_row_index=False, show_default_header_for_empty=False, empty_horizontal=0, empty_vertical=0, total_columns=ROIManager.cmax+2)
        self.sheet.grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 0))
        bottom_frame = CTk.CTkFrame(self)
        bottom_frame.grid(row=1, column=0, sticky="nswe", padx=20, pady=(0, 20))
        self.buttons = []
        for _, label in enumerate(ROIManager.button_labels):
            button = Button(bottom_frame, text=label, anchor="center", width=80)
            self.buttons += [button]
            button.grid(row=0, column=_, padx=10, pady=10, sticky="nswe")
        self.buttons[0].configure(width=80, fg_color=green[0], hover_color=green[1])
        self.buttons[-1].configure(fg_color=red[0], hover_color=red[1])
        self.buttons[-2].configure(fg_color=red[0], hover_color=red[1])
        self.add_elements(ROIManager.cmax)
        self.sheet.enable_bindings()
        self.sheet.disable_bindings(["rc_insert_column", "rc_delete_column", "rc_insert_row", "rc_delete_row", "hide_columns",  "row_height_resize","row_width_resize", "column_height_resize", "column_width_resize", "edit_header", "arrowkeys"])
        self.sheet.default_row_height(cell_height)
        for _, width in enumerate(widths):
            self.sheet.column_width(column=_, width=width)

    def add_elements(self, cmax):
        self.sheet.align_columns(columns=[0, cmax-1], align="center")
        self.sheet.create_checkbox(r="all", c=cmax, checked=True, state="normal", redraw=False, check_function=None, text="")
        self.sheet.create_checkbox(r="all", c=cmax+1, checked=False, state="normal", redraw=False, check_function=None, text="")
        
    def delete(self, rois):
        vec = [_ for _, x in enumerate(self.sheet.get_column_data(c=-1)) if x == "True"]
        while len(vec) >= 1:
            self.sheet.delete_row(idx=vec[0])
            del rois[vec[0]]
            for _, roi in enumerate(rois):
                roi["indx"] = _ + 1
            self.sheet.set_column_data(0, values=tuple(roi["indx"] for roi in rois), add_rows=False)
            vec = [_ for _, x in enumerate(self.sheet.get_column_data(c=-1)) if x == "True"]
        self.sheet.set_options(height=self.sheet_height(20, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, rois)) + f"+{x}+{y}")
    
    def delete_all(self):
        for _ in range(self.sheet.get_total_rows()):
            self.sheet.delete_row()
        self.sheet.set_options(height=self.sheet_height(20, []))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, [])) + f"+{x}+{y}")

    def get_buttons(self):
        return self.buttons

    def load(self, initialdir="/"):
        self.delete_all()
        filetypes = [("PyROI files", "*.pyroi")]
        filename = fd.askopenfilename(title="Select a PyROI file", initialdir=initialdir, filetypes=filetypes)
        with open(filename, "rb") as f:
            rois = pickle.load(f)
        self.sheet.set_options(height=self.sheet_height(20, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, rois)) + f"+{x}+{y}")
        self.sheet.insert_rows(rows=len(rois))
        self.add_elements(len(ROIManager.labels))
        self.rois2sheet(rois)
        return rois

    def rois2sheet(self, rois):
        for it, roi in enumerate(rois):
            for jt, label in enumerate(self.labels):
                self.sheet.set_cell_data(it, jt, value=roi[label])

    def save(self, rois=[], filename="ROIs"):
        if any(rois):
            rois = self.update_sheet(rois)
            with open(filename + ".pyroi", "wb") as f:
                pickle.dump(rois, f, protocol=pickle.HIGHEST_PROTOCOL)

    def update_manager(self, rois):
        self.sheet.set_options(height=self.sheet_height(20, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, rois)) + f"+{x}+{y}")
        roi = rois[-1]
        self.sheet.insert_row([roi[label] for label in ROIManager.labels])
        self.sheet.create_checkbox(c=ROIManager.cmax, r=len(rois)-1, checked = True)
        self.sheet.create_checkbox(c=ROIManager.cmax+1, r=len(rois)-1, checked = False)

    def update_sheet(self, rois=[]):
        if any(rois):
            data = self.sheet.get_sheet_data()
            for _, roi in enumerate(rois):
                roi["name"] = data[_][1]
                roi["group"] = data[_][2]
                roi["select"] = data[_][-2]
            return rois
        return []

class Button(CTk.CTkButton):
    def __init__(self, *args, text=None, image=None, width=button_size[0], height=button_size[1], anchor="w", **kwargs):
        super().__init__(*args, text=text, image=image, width=width, height=height, anchor=anchor, compound=tk.LEFT, **kwargs)
        if text is None:
            self.configure(width=height)

class CheckBox(CTk.CTkCheckBox):
    def __init__(self, *args, text=None, command=None, **kwargs):
        super().__init__(*args, text=text, command=command, onvalue=True, offvalue=False, **kwargs)
        self.configure(text=text, command=command, width=30)

class Entry(CTk.CTkFrame):
    def __init__(self, *args, text=None, text_box=None, textvariable=None, state="normal", row=0, column=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(fg_color=gray[0])
        self.grid(row=row, column=column, sticky="e")
        CTk.CTkLabel(self, text=text).grid(row=0, column=0, padx=(20, 10))
        self.entry = CTk.CTkEntry(self, placeholder_text=text_box, textvariable=textvariable, width=50, state=state)
        self.entry.grid(row=0, column=1, padx=(10, 30), pady=5)

    def get(self):
        try:
            return int(self.entry.get())
        except ValueError:
            return None
        
    def state(self, state):
        self.entry.configure(state=state)

    def bind(self, *args, **kwargs):
        return self.entry.bind(*args, **kwargs)
    
class DoubleEntry(CTk.CTkFrame):
    def __init__(self, *args, text=None, variables=(None, None), row=0, column=0, state="disabled", **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(fg_color=gray[0])
        self.grid(row=row, column=column, sticky="e")
        CTk.CTkLabel(self, text=text).grid(row=0, column=0, padx=20)
        self.entries = [CTk.CTkEntry(self, textvariable=variables[_], width=50) for _ in range(2)]
        for _, entry in enumerate(self.entries):
            entry.grid(row=0, column=_+1, padx=20, pady=10)
            entry.configure(state=state)
        
    def state(self, state):
        for entry in self.entries:
            entry.configure(state=state)

class DropDown(CTk.CTkFrame):
    def __init__(self, *args, values=[], image=None, command=None, variable=None, state="normal", **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(fg_color=gray[0])
        self.pack(padx=20, pady=20)
        self.icon = Button(self, image=image)
        self.icon.configure(hover=False)
        self.icon.pack(side=tk.LEFT)
        self.option_menu = CTk.CTkOptionMenu(self, values=values, width=button_size[0]-button_size[1], height=button_size[1], dynamic_resizing=False, command=command, variable=variable, state=state)
        self.option_menu.pack(side=tk.LEFT)

    def set_state(self, state):
        self.option_menu.configure(state=state)

    def set_values(self, values):
        self.option_menu.configure(values=values)
    
    def get_menu(self):
        return self.option_menu
    
    def get_icon(self):
        return self.icon

class SpinBox(CTk.CTkFrame):
    def __init__(self, *args, width=40, height=15, step_size=1, from_=1, to_=20, command=None, **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)
        updown_size = 8
        self.step_size = step_size
        self.from_, self.to_ = from_, to_
        self.command = command
        self.configure(fg_color=gray[1]) 
        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.subtract_button = CTk.CTkButton(self, text=u"\u25BC", width=updown_size, height=updown_size, command=self.subtract_button_callback)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)
        self.entry = CTk.CTkEntry(self, width=width-(2*updown_size), height=updown_size, border_width=0)
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.add_button = CTk.CTkButton(self, text=u"\u25B2", width=updown_size, height=updown_size, command=self.add_button_callback)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)
        self.entry.insert(0, "1")

    def add_button_callback(self):
        try:
            value = int(self.entry.get()) + self.step_size
            value = value if value <= self.to_ else self.to_
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
            if self.command is not None:
                self.command()
        except ValueError:
            return

    def subtract_button_callback(self):
        try:
            value = int(self.entry.get()) - self.step_size
            value = value if value >= self.from_ else self.from_
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
            if self.command is not None:
                self.command()
        except ValueError:
            return
        
    def bind(self, event, command):
        self.entry.bind(event, command)

    def get(self):
        try:
            return int(self.entry.get())
        except ValueError:
            return None

    def set(self, value):
        if value <= self.from_:
            value = self.from_
        elif value >= self.to_:
            value = self.to_
        self.entry.delete(0, "end")
        self.entry.insert(0, str(int(value)))

class ShowInfo(CTk.CTkToplevel):
    def __init__(self, *args, message="", image=None, button_labels=[], geometry=(300, 150), fontsize=13, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes("-topmost", "true")
        self.title("Polarimetry Analysis")
        self.geometry(geometry_info(geometry))
        CTk.CTkLabel(self, text=message, image=image, compound="left", width=250, justify=tk.LEFT, font=CTk.CTkFont(size=fontsize)).grid(row=0, column=0, padx=30, pady=20)
        self.buttons = []
        if button_labels:
            if len(button_labels) >= 2:
                banner = CTk.CTkFrame(self, fg_color="transparent")
                banner.grid(row=1, column=0)
                master, row_ = banner, 0
            else:
                master, row_ = self, 1
            for _, label in enumerate(button_labels):
                button = Button(master, text=label, width=80, anchor="center")
                self.buttons += [button]
                button.grid(row=row_, column=_, padx=20, pady=20)
    
    def get_buttons(self):
        return self.buttons

if __name__ == "__main__":
    app = Polarimetry()
    app.mainloop()