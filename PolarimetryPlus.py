import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import webbrowser
import customtkinter as CTk
from tkinter import filedialog as fd
from tkinter.messagebox import showerror
from PIL import ImageTk, Image
import os
import pathlib
import scipy.io
import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.transforms as mtransforms
import imutils
from matplotlib.figure import Figure
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from skimage import exposure
from scipy import ndimage
import cv2
from scipy.signal import convolve2d
from apptools import NToolbar2Tk, ToolTip

CTk.set_default_color_theme("polarimetry.json")
CTk.set_appearance_mode("dark")

mpl.use("TkAgg")

plt.rcParams["font.size"] = 16
plt.rcParams["font.family"] = "Arial Rounded MT Bold"

class App(CTk.CTk):

    left_frame_width = 180
    right_frame_width = 850
    height = 850
    width = left_frame_width + right_frame_width
    tab_width = right_frame_width - 40
    height_tab = height - 20
    button_pady = 25
    axes_size = (680, 680)
    button_size = (160, 40)
    info_size = ((420, 320), (300, 150))
    figsize = (6.5, 6.5)
    geometry_info = {"large": "{}x{}+400+300".format(info_size[0][0], info_size[0][1]), "small": "{}x{}+400+300".format(info_size[1][0], info_size[1][1])}

    orange = ("#FF7F4F", "#ffb295")
    text_color = "black"
    red = ("#B54D42", "#d5928b")
    green = ("#ADD1AD", "#cee3ce")
    gray = ("#7F7F7F", "#A6A6A6")
    url_github = "https://github.com/cchandre/Polarimetry"
    url_fresnel = "https://www.fresnel.fr/polarimetry"
    email = "cristel.chandre@cnrs.fr"

    def __init__(self):
        super().__init__()

## MAIN
        delx = self.winfo_screenwidth() // 10
        dely = self.winfo_screenheight() // 10
        self.title("Polarimetry Analysis")
        self.geometry("{}x{}+{}+{}".format(App.width, App.height, delx, dely))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(fg_color=App.gray[0])

        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Icons_Python")
        self.icons = {}
        for file in os.listdir(image_path):
            if file.endswith('.png'):
                self.icons.update({os.path.splitext(file)[0]: CTk.CTkImage(dark_image=Image.open(image_path + "/" + file), size=(30, 30))})

## DEFINE FRAMES
        self.left_frame = CTk.CTkFrame(master=self, width=App.left_frame_width, corner_radius=0, fg_color=App.gray[0])
        self.left_frame.grid(row=0, column=0, sticky="nswe")
        self.right_frame = CTk.CTkFrame(master=self, width=App.right_frame_width)
        self.right_frame.grid(row=0, column=1, sticky="nswe", padx=0, pady=0)

## DEFINE TABS
        self.tabview = CTk.CTkTabview(master=self.right_frame, width=App.tab_width, height=App.height_tab, segmented_button_selected_color=App.orange[0], segmented_button_unselected_color=App.gray[1], segmented_button_selected_hover_color=App.orange[1], text_color="black", segmented_button_fg_color=App.gray[0], fg_color=App.gray[1])
        self.tabview.grid(row=0, column=0, padx=10, pady=0)
        list_tabs = ["Fluorescence", "Thresholding/Mask", "Options", "Advanced", "About"]
        for tab in list_tabs:
            self.tabview.add(tab)

## LEFT FRAME
        logo = self.button(self.left_frame, text="POLARIMETRY \n ANALYSIS", image=self.icons["blur_circular"], command=self.on_click_tab)
        logo.configure(hover=False, fg_color="transparent", anchor="e")
        logo.grid(row=0, column=0, pady=30, padx=17)
        self.button(self.left_frame, text="Download File", command=self.select_file, image=self.icons["download_file"]).grid(row=2, column=0, pady=App.button_pady, padx=17)
        self.button(self.left_frame, text="Download Folder", command=self.select_folder, image=self.icons["download_folder"]).grid(row=3, column=0, pady=App.button_pady, padx=17)
        button = self.button(self.left_frame, text="Add ROI", image=self.icons["roi"], command=self.add_roi_callback)
        ToolTip.createToolTip(button, "Add a region of interest")
        button.grid(row=5, column=0, pady=App.button_pady, padx=17)
        self.analysis_button = self.button(self.left_frame, text="Analysis", command=self.analysis_callback, image=self.icons["play"])
        ToolTip.createToolTip(self.analysis_button, "Polarimetry analysis")
        self.analysis_button.configure(fg_color=App.green[0], hover_color=App.green[1])
        self.analysis_button.grid(row=6, column=0, pady=App.button_pady, padx=17)
        button = self.button(self.left_frame, text="Close figures", command=self.close_callback, image=self.icons["close"])
        button.configure(fg_color=App.red[0], hover_color=App.red[1])
        button.grid(row=7, column=0, pady=App.button_pady, padx=17)
        self.method_dropdown = self.dropdown(self.left_frame, values=["1PF", "CARS", "SRS", "SHG", "2PF", "4POLAR 2D", "4POLAR 3D"], image=self.icons["microscope"], row=1, column=0, command=self.method_dropdown_callback)
        self.tool_dropdown = self.dropdown(self.left_frame, values=["Thresholding (manual)", "Thresholding (auto)", "Mask (manual)", "Mask (auto)"], image=self.icons["build"], row=4, column=0, command=self.tool_dropdown_callback)
        ToolTip.createToolTip(self.tool_dropdown, " Select the method of analysis: intensity thresholding or segmentation\n mask for single file analysis (manual) or batch processing (auto).\n The mask has to be binary and in a PNG format and have the same\n file name as the respective polarimetry data file.")

## RIGHT FRAME: FLUO
        self.fluo_frame = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent", width=App.axes_size[1], height=App.axes_size[0])
        self.fluo_frame.grid(row=0, column=0, padx=0, pady=0, sticky="w")
        self.fluo_fig = Figure(figsize=App.figsize, facecolor=App.gray[1])
        self.fluo_axis = self.fluo_fig.add_axes([0, 0, 1, 1])
        self.fluo_axis.set_axis_off()
        self.fluo_canvas = FigureCanvasTkAgg(self.fluo_fig, master=self.fluo_frame)
        self.fluo_canvas.draw()
        self.fluo_toolbar = NToolbar2Tk(self.fluo_canvas, self.fluo_frame, pack_toolbar=False)
        self.fluo_toolbar.update()
        banner = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent")
        banner.grid(row=0, column=1)
        self.button(banner, image=self.icons["contrast"], command=self.contrast_fluo_button_callback).grid(row=0, column=0, sticky="ne", padx=20, pady=20)
        self.contrast_fluo_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_fluo_slider_callback)
        ToolTip.createToolTip(self.contrast_fluo_slider, " The chosen contrast will be the one used\n for the fluorescence images in figures")
        self.contrast_fluo_slider.grid(row=1, column=0, padx=20, pady=20)
        button = self.button(banner, image=self.icons["square"], command=self.compute_angle)
        #ToolTip.createToolTip(button, " Left click and hold to trace a line\n segment and determine its angle")
        button.grid(row=3, column=0, padx=20, pady=20)
        banner = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent", width=App.axes_size[1], height=40)
        banner.grid(row=1, column=0, pady=20)
        self.filename_label = CTk.CTkLabel(master=banner, text=None)
        self.filename_label.place(relx=0, rely=0.2)
        self.stack_slider = CTk.CTkSlider(master=banner, from_=0, to=18, number_of_steps=18, command=self.stack_slider_callback)
        self.stack_slider.set(0)
        self.stack_slider.place(relx=0.6, rely=0.1)
        self.stack_slider_label = CTk.CTkLabel(master=banner, text="T")
        ToolTip.createToolTip(self.stack_slider_label, "Slider at T for the total intensity fluorescence, otherwise drag through the images of the stack")
        self.stack_slider_label.place(relx=0.9, rely=0.5)
        CTk.CTkLabel(master=banner, fg_color="transparent", text="Stack").place(relx=0.6, rely=0.5)

## RIGHT FRAME: THRSH
        self.thrsh_frame = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", width=App.axes_size[1], height=App.axes_size[0])
        self.thrsh_frame.grid(row=0, column=0, padx=0, pady=0, sticky="w")
        self.thrsh_axis_facecolor = App.gray[1]
        self.thrsh_fig = Figure(figsize=App.figsize, facecolor=self.thrsh_axis_facecolor)
        self.thrsh_axis = self.thrsh_fig.add_axes([0, 0, 1, 1])
        self.thrsh_axis.set_axis_off()
        self.thrsh_axis.set_facecolor(self.thrsh_axis_facecolor)
        self.thrsh_canvas = FigureCanvasTkAgg(self.thrsh_fig, master=self.thrsh_frame)
        self.thrsh_canvas.draw()
        self.thrsh_toolbar = NToolbar2Tk(self.thrsh_canvas, self.thrsh_frame, pack_toolbar=False)
        self.thrsh_toolbar.update()
        banner = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent")
        banner.grid(row=0, column=1)
        self.button(banner, image=self.icons["contrast"], command=self.contrast_thrsh_button_callback).grid(row=0, column=0, sticky="ne", padx=20, pady=20)
        self.contrast_thrsh_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_thrsh_slider_callback)
        self.contrast_thrsh_slider.grid(row=1, column=0, padx=20, pady=20)
        button = self.button(banner, image=self.icons["open_in_new"], command=self.export_mask)
        #ToolTip.createToolTip(button, " Export mask as .png")
        button.grid(row=2, column=0, padx=20, pady=20)
        button = self.button(banner, image=self.icons["palette"], command=self.change_colormap)
        #ToolTip.createToolTip(button, " Change the colormap used for thresholding ('hot' or 'gray')")
        button.grid(row=3, column=0, padx=20, pady=20)
        self.no_background_button = self.button(banner, image=self.icons["photo_fill"], command=self.no_background)
        #ToolTip.createToolTip(button, " Change background to enhance visibility")
        self.no_background_button.grid(row=4, column=0, padx=20, pady=20)
        button = self.button(banner, image=self.icons["format_list"], command=self.change_list_button_callback)
        #ToolTip.createToolTip(button, "Erase selected ROIs and reload image")
        button.grid(row=5, column=0, padx=20, pady=20)
        self.ilow = tk.StringVar()
        self.ilow_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, command=self.ilow_slider_callback)
        self.ilow_slider.set(0)
        self.ilow_slider.place(relx=0.2, rely=0.93, anchor="w")
        entry = CTk.CTkEntry(master=self.tabview.tab("Thresholding/Mask"), width=100, height=10, placeholder_text="0", textvariable=self.ilow, border_color=App.gray[1])
        entry.bind("<Return>", command=self.ilow2slider_callback)
        entry.place(relx=0.2, rely=0.96, anchor="w")
        self.transparency_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, command=self.transparency_slider_callback)
        ToolTip.createToolTip(self.transparency_slider, " Adjust the transparency of the background image")
        self.transparency_slider.set(0)
        self.transparency_slider.place(relx=0.6, rely=0.93, anchor="w")

## RIGHT FRAME: OPTIONS
        show_save = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        show_save.grid(row=0, column=0, padx=(20, 20), pady=20, sticky="nw")
        CTk.CTkLabel(master=show_save, text="Show", anchor="w").grid(row=0, column=1)
        CTk.CTkLabel(master=show_save, text="Save", anchor="w").grid(row=0, column=2)
        labels = ["Composite", "Sticks", "Histogram", "Fluorescence"]
        self.show_table = [self.checkbox(show_save) for it in range(len(labels))]
        self.save_table = [self.checkbox(show_save) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=show_save, text=labels[it], anchor="w", width=100).grid(row=it+1, column=0, padx=(20, 0))
            self.show_table[it].grid(row=it+1, column=1, pady=0, padx=20, sticky="ew")
            self.save_table[it].grid(row=it+1, column=2, pady=0, padx=(20, 20))
        banner = CTk.CTkFrame(master=self.tabview.tab("Options"))
        banner.grid(row=1, column=0)
        button = self.button(banner, image=self.icons["delete_forever"], command=lambda:self.initialize_table(mode="part"))
        #ToolTip.createToolTip(button, "Reinitialize the tables Show/Save and Variable")
        button.grid(row=0, column=0, padx=(0, 100), sticky="nw")
        self.per_roi = self.checkbox(banner, text="per ROI")
        ToolTip.createToolTip(self.per_roi, " Show and save data/figures separately for each region of interest")
        self.per_roi.grid(row=0, column=1, sticky="nw")

        plot_options = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        plot_options.grid(row=2, column=0, padx=20, pady=20, sticky="nw")
        CTk.CTkLabel(master=plot_options, text="Plot options", width=250, font=CTk.CTkFont(size=16)).grid(row=0, column=0, padx=20, pady=(0, 20))
        self.add_axes_checkbox = self.checkbox(plot_options, text="Add axes on figures")
        self.add_axes_checkbox.grid(row=1, column=0, padx=20)
        CTk.CTkLabel(master=plot_options, text="Number of pixels separating sticks").grid(row=2, column=0, padx=20, pady=20)
        labels = ["horizontal", "vertical"]
        self.pixelsperstick_spinboxes = [ttk.Spinbox(master=plot_options, from_=0, to=10, width=2, foreground=App.gray[1], background=App.gray[1]) for it in range(2)]
        for it in range(2):
            self.pixelsperstick_spinboxes[it].set(1)
            self.pixelsperstick_spinboxes[it].grid(row=it+3, column=0, padx=20, pady=10)
        self.show_individual_fit_checkbox = self.checkbox(self.tabview.tab("Options"), text="Show individual fit")
        self.show_individual_fit_checkbox.grid(row=3, column=0, pady=20)

        self.variable_table_frame = CTk.CTkFrame(master=self.tabview.tab("Options"), width=300)
        self.variable_table_frame.grid(row=0, column=1, padx=(40, 20), pady=20, sticky="nw")

        save_ext = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=self.left_frame.cget("fg_color"))
        save_ext.grid(row=2, column=1, padx=(40, 20), pady=20, sticky="nw")
        CTk.CTkLabel(master=save_ext, text="Save extension", width=100).grid(row=0, column=1, padx=(0, 20))
        labels = ["figures (.fig)", "figures (.tif)", "data (.mat)", "mean values (.xlsx)", "stack (.mp4)"]
        self.extension_table = [self.checkbox(save_ext) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=save_ext, text=labels[it], anchor="w", width=120).grid(row=it+1, column=0, padx=(20, 0))
            self.extension_table[it].grid(row=it+1, column=1, pady=0, padx=(20,0))

## RIGHT FRAME: ADV
        adv_elts = ["Dark", "Binning", "Offset angle", "Rotation", "Disk cone / Calibration data", "Remove background"]
        adv_loc = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        adv = {}
        for loc, elt in zip(adv_loc, adv_elts):
            adv.update({elt: CTk.CTkFrame(master=self.tabview.tab("Advanced"), fg_color=self.left_frame.cget("fg_color"))})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=(20, 10), sticky="nw")
            CTk.CTkLabel(master=adv[elt], text=elt + "\n", width=250, font=CTk.CTkFont(size=16)).grid(row=0, column=0, padx=20, pady=(10,0))
        self.dark_switch = CTk.CTkSwitch(master=adv["Dark"], text="", command=self.dark_switch_callback, onvalue="on", offvalue="off", width=50)
        self.dark_switch.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        self.calculated_dark_label = CTk.CTkLabel(master=adv["Dark"], text="Calculated dark value = 0")
        self.calculated_dark_label.grid(row=1, column=0)
        self.dark = tk.DoubleVar()
        self.dark_entry = self.entry(adv["Dark"], text="User dark value", textvariable=self.dark, row=2, column=0)
        self.dark_entry.bind("<Return>", command=self.itot_callback)
        self.dark_entry.configure(state="disabled")

        self.offset_angle_switch = CTk.CTkSwitch(master=adv["Offset angle"], text="", command=self.offset_angle_switch_callback, onvalue="on", offvalue="off", width=50)
        self.offset_angle_switch.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        self.offset_angle = tk.IntVar()
        self.offset_angle_entry = self.entry(adv["Offset angle"], text="\n" + "Offset angle (deg)" +"\n", textvariable=self.offset_angle, row=1)
        self.offset_angle_entry.configure(state="disabled")

        self.calib_dropdown = CTk.CTkOptionMenu(master=adv["Disk cone / Calibration data"], values="", width=App.button_size[0], height=App.button_size[1], dynamic_resizing=False, command=self.calib_dropdown_callback)
        self.calib_dropdown.grid(row=1, column=0, pady=20)
        self.button(adv["Disk cone / Calibration data"], text="Display", image=self.icons["photo"], command=self.diskcone_display).grid(row=2, column=0, pady=20)
        self.calib_textbox = CTk.CTkTextbox(master=adv["Disk cone / Calibration data"], width=250, height=50, state="disabled")
        self.calib_textbox.grid(row=3, column=0, pady=20)
        self.polar_dropdown = CTk.CTkOptionMenu(master=adv["Disk cone / Calibration data"], values="", width=App.button_size[0], height=App.button_size[1], dynamic_resizing=False, command=self.polar_dropdown_callback, state="disabled")
        self.polar_dropdown.grid(row=4, column=0, pady=20)

        labels = ["Bin width", "Bin height"]
        self.bin = [tk.IntVar(), tk.IntVar()]
        self.bin[0].set(1)
        self.bin[1].set(1)
        for it in range(2):
            entry = self.entry(adv["Binning"], text="\n" + labels[it] + "\n", text_box=1, textvariable=self.bin[it], row=it+1, column=0)
            entry.bind("<Return>", command=self.itot_callback)
        labels = ["Stick (deg)", "Figure (deg)"]
        self.rotation = [tk.IntVar(), tk.IntVar()]
        self.rotation[0].set(0)
        self.rotation[1].set(0)
        entries = [self.entry(adv["Rotation"], text="\n" + label + "\n", text_box=0, textvariable=self.rotation[it], row=it+1, column=0) for it, label in enumerate(labels)]
        entries[1].bind("<Return>", command=self.rotation_callback)
        labels = ["Noise factor", "Noise width", "Noise height", "Noise removal level"]
        self.noise = [tk.DoubleVar(), tk.IntVar(), tk.IntVar(), tk.DoubleVar()]
        vals = [1, 3, 3, 0]
        for val, _ in zip(vals, self.noise):
            _.set(val)
        rows = [1, 2, 3, 5]
        entries = [self.entry(adv["Remove background"], text="\n" + label + "\n", textvariable=self.noise[it], row=rows[it], column=0) for it, label in enumerate(labels)]
        entries[3].configure(state="disabled")
        self.button(adv["Remove background"], text="Click background", image=self.icons["exposure"], command=self.click_background_callback).grid(row=4, column=0)

## RIGHT FRAME: ABOUT
        banner = CTk.CTkFrame(master=self.tabview.tab("About"))
        banner.grid(row=0, column=0, pady=20)
        self.button(banner, text="CHECK WEBSITE FOR UPDATES", image=self.icons["web"], command=lambda:self.openweb(App.url_fresnel)).grid(row=0, column=0, padx=40)
        self.button(banner, image=self.icons["mail"], command=self.send_email).grid(row=0, column=1)
        self.button(banner, image=self.icons["GitHub"], command=lambda:self.openweb(App.url_github)).grid(row=0, column=2, padx=40)
        self.button(banner, image=self.icons["contact_support"], command=lambda:self.openweb(App.url_github + '/blob/master/README.md')).grid(row=0, column=3, padx=20)
        about_textbox = CTk.CTkTextbox(master=self.tabview.tab("About"), width=App.tab_width-30, height=500)
        about_textbox.grid(row=1, column=0)
        message = "Version: 2.1 (December 1, 2022) created with Python and CustomTkinter\n\n\n Website: www.fresnel.fr/polarimetry/ \n\n\n Source code available at github.com/cchandre/Polarimetry \n\n\n\n Based on a code originally developed by Sophie Brasselet (Institut Fresnel, CNRS) \n\n\n To report bugs, send an email to\n     manos.mavrakis@cnrs.fr  (Manos Mavrakis, Institut Fresnel, CNRS) \n     cristel.chandre@cnrs.fr  (Cristel Chandre, Institut de Mathématiques de Marseille, CNRS) \n     sophie.brasselet@fresnel.fr  (Sophie Brasselet, Institut Fresnel, CNRS) \n\n\n\n BSD 2-Clause License\n\n Copyright(c) 2021, Cristel Chandre\n All rights reserved. \n\n\n uses Material Design icons by Google"
        about_textbox.insert("0.0", message)
        about_text = about_textbox.get("0.0", "end")
        about_textbox.configure(state="disabled")

        self.tabview.set("Fluorescence")
        self.startup()

    def startup(self):
        info = " (1) Select a polarimetry method\n\n (2) Download a file or a folder\n\n (3) Select a method of analysis\n\n (4) Select one or several regions of interest\n\n (5) Click on Analysis"
        self.info_window = CTk.CTkToplevel(self)
        self.info_window.attributes('-topmost', 'true')
        self.info_window.title('Polarimetry Analysis')
        self.info_window.geometry(App.geometry_info["large"])
        CTk.CTkLabel(self.info_window, text="  Welcome to Polarimetry Analysis", font=CTk.CTkFont(size=20), image=self.icons['blur_circular'], compound="left").grid(row=0, column=0, padx=30, pady=20)
        textbox = CTk.CTkTextbox(self.info_window, width=320, height=150, fg_color=App.gray[1])
        textbox.grid(row=1, column=0)
        textbox.insert("0.0", info)
        link = CTk.CTkLabel(self.info_window, text="For more information, visit the GitHub page", text_color="blue", font=CTk.CTkFont(underline=True), cursor="hand2")
        link.grid(row=2, column=0, padx=50, pady=10, sticky="w")
        link.bind("<Button-1>", lambda e: webbrowser.open_new_tab(App.url_github))
        ok_button = self.button(master=self.info_window, text="       OK", command=lambda:self.info_window.withdraw())
        ok_button.configure(width=80, height=App.button_size[1])
        ok_button.grid(row=7, column=0, padx=20, pady=0)
        self.define_variable_table("1PF")
        self.thrsh_colormap = "hot"
        self.CD = Calibration("1PF")
        self.calib_dropdown.configure(values=self.CD.list("1PF"))
        self.calib_dropdown.set(self.CD.list("1PF")[0])
        self.calib_textbox.configure(state="normal")
        self.calib_textbox.delete("0.0", "end")
        self.calib_textbox.insert("0.0", self.CD.name)
        self.calib_textbox.configure(state="disabled")
        self.offset_angle.set(85)
        self.dict_polar = {'UL0-UR45-LR90-LL135': [1, 2, 3, 4], 'UL0-UR45-LR135-LL90': [1, 2, 4, 3], 'UL0-UR90-LR45-LL135': [1, 3, 2, 4], 'UL0-UR90-LR135-LL45': [1, 3, 4, 2], 'UL0-UR135-LR45-LL90': [1, 4, 2, 3], 'UL0-UR135-LR90-LL45': [1, 4, 3, 2], 'UL45-UR0-LR90-LL135': [2, 1, 3, 4],  'UL45-UR0-LR135-LL90': [2, 1, 4, 3], 'UL45-UR90-LR0-LL135': [2, 3, 1, 4], 'UL45-UR90-LR135-LL0': [2, 3, 4, 1], 'UL45-UR135-LR0-LL90': [2, 4, 1, 3], 'UL45-UR135-LR90-LL0': [2, 4, 3, 1], 'UL90-UR0-LR45-LL135': [3, 1, 2, 4], 'UL90-UR0-LR135-LL45': [3, 1, 4, 2], 'UL90-UR45-LR0-LL135': [3, 2, 1, 4], 'UL90-UR45-LR135-LL0': [3, 2, 4, 1], 'UL90-UR135-LR0-LL45': [3, 4, 1, 2], 'UL90-UR135-LR45-LL0': [3, 4, 2, 1], 'UL135-UR0-LR45-LL90': [4, 1, 2, 3], 'UL135-UR0-LR90-LL45': [4, 1, 3, 2], 'UL135-UR45-LR0-LL90': [4, 2, 1, 3], 'UL135-UR45-LR90-LL0': [4, 2, 3, 1], 'UL135-UR90-LR0-LL45': [4, 3, 1, 2], 'UL135-UR90-LR45-LL0': [4, 3, 2, 1]}
        self.polar_dropdown.configure(values=list(self.dict_polar.keys()))
        self.polar_dropdown.set(list(self.dict_polar.keys())[0])

    def initialize_slider(self):
        if hasattr(self, "stack"):
            self.stack_slider.configure(to=stack.nangle, number_of_steps=stack.nangle)
            self.ilow.set(stack.display.format(np.amin(stack.itot)))
        else:
            self.ilow.set("0")
        self.contrast_fluo_slider.set(0.5)
        self.contrast_thrsh_slider.set(0.5)
        self.stack_slider.set(0)
        self.stack_slider_label.configure(text="T")

    def initialize_noise(self):
        vals = [1, 3, 3, 0]
        for val, _ in zip(vals, self.noise):
            _.set(val)

    def initialize_data(self):
        self.initialize_slider()
        self.initialize_noise()

    def initialize_table(self, mode='all'):
        for show, save in zip(self.show_table, self.save_table):
            show.deselect()
            save.deselect()
        #self.Variable[:].set(False)
        if mode == 'part':
            self.extension_table[0].deselect()
        else:
            for ext in self.extension_table:
                ext.deselect()
        if self.method_dropdown.get().startswith("4POLAR"):
            self.show_individual_fit_checkbox.deselect()
            self.show_individual_fit_checkbox.configure(state=tk.DISABLED)
        else:
            self.show_individual_fit_checkbox.configure(state=tk.NORMAL)
            self.show_individual_fit_checkbox.deselect()

    def button(self, master, text=None, image=None, command=None, width=None, height=None):
        if width == None:
            width = App.button_size[0]
        if height == None:
            height = App.button_size[1]
        if text is not None:
            button = CTk.CTkButton(master=master, width=width, height=height, text=text, anchor="w", image=image, compound=tk.LEFT, command=command)
        else:
            button = CTk.CTkButton(master=master, text=None, width=height, height=height, anchor="w", image=image, command=command)
        return button

    def dropdown(self, master, values=[], image=None, row=0, column=0, command=None):
        menu = CTk.CTkFrame(master=master, fg_color=self.left_frame.cget("fg_color"))
        menu.grid(row=row, column=column, padx=17, pady=App.button_pady)
        menu_icon = self.button(menu, image=image)
        menu_icon.configure(hover=False)
        menu_icon.grid(row=0, column=0)
        option_menu = CTk.CTkOptionMenu(master=menu, values=values, width=App.button_size[0]-App.button_size[1], height=App.button_size[1], dynamic_resizing=False, anchor="w", command=command)
        option_menu.grid(row=0, column=1)
        return option_menu

    def checkbox(self, master, text=None):
        return CTk.CTkCheckBox(master=master, onvalue=True, offvalue=False, text=text, width=30)

    def entry(self, master, text=None, text_box=None, textvariable=None, row=0, column=0):
        banner = CTk.CTkFrame(master=master, fg_color=self.left_frame.cget("fg_color"))
        banner.grid(row=row, column=column, sticky="e")
        CTk.CTkLabel(master=banner, text=text).grid(row=0, column=0, padx=(20, 10))
        entry = CTk.CTkEntry(master=banner, placeholder_text=text_box, textvariable=textvariable, width=50)
        entry.grid(row=0, column=1, padx=(10, 20), pady=5)
        return entry

    def double_entry(self, master, text=None, text_box=(None, None), row=0, column=0):
        banner = CTk.CTkFrame(master=master, fg_color=self.left_frame.cget("fg_color"))
        banner.grid(row=row, column=column, sticky="e")
        CTk.CTkLabel(master=banner, text=text).grid(row=0, column=0, padx=20)
        entry = [CTk.CTkEntry(master=banner, placeholder_text=text_box[it], width=50) for it in range(2)]
        for it in range(2):
            entry[it].grid(row=0, column=it+1, padx=20, pady=10)
            entry[it].configure(state="disabled")
        return entry

    def showinfo(self, message="", image=None, button_labels=[]):
        info_window = CTk.CTkToplevel(self)
        info_window.attributes('-topmost', 'true')
        info_window.title('Polarimetry Analysis')
        info_window.geometry(App.geometry_info["small"])
        CTk.CTkLabel(info_window, text=message, image=image, compound="left", width=250).grid(row=0, column=0, padx=30, pady=20)
        buttons = []
        if button_labels:
            if len(button_labels) >= 2:
                banner = CTk.CTkFrame(master=info_window, fg_color="transparent")
                banner.grid(row=1, column=0)
                master, row_ = banner, 0
            else:
                master, row_ = info_window, 1
            for it, label in enumerate(button_labels):
                button = self.button(master, text="       " + label, width=80, height=App.button_size[1])
                buttons += [button]
                button.grid(row=row_, column=it, padx=20, pady=20)
            return info_window, buttons

    def on_closing(self):
        self.destroy()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()

    def openweb(self, url):
        webbrowser.open(url)

    def send_email(self):
        webbrowser.open('mailto:?to=' + App.email + '&subject=[Polarimetry Analysis] question', new=1)

    def on_click_tab(self):
        if self.tabview.get() != "About":
            self.tabview.set("About")
        else:
            self.tabview.set("Fluorescence")

    def contrast_thrsh_slider_callback(self, value):
        if value <= 0.001:
            self.contrast_thrsh_slider.set(0.001)
        if hasattr(self, 'stack'):
            self.represent_thrsh(self.stack, drawnow=True)

    def contrast_fluo_slider_callback(self, value):
        if value <= 0.001:
            self.contrast_fluo_slider.set(0.001)
        if hasattr(self, 'stack'):
            self.represent_fluo(self.stack)

    def contrast_fluo_button_callback(self):
        if self.contrast_fluo_slider.get() <= 0.5:
            self.contrast_fluo_slider.set(0.5)
        else:
            self.contrast_fluo_slider.set(1)
        if hasattr(self, 'stack'):
            self.represent_fluo(self.stack)

    def contrast_thrsh_button_callback(self):
        if self.contrast_thrsh_slider.get() <= 0.5:
            self.contrast_thrsh_slider.set(0.5)
        else:
            self.contrast_thrsh_slider.set(1)
        if hasattr(self, 'stack'):
            self.represent_thrsh(self.stack, drawnow=True)

    def change_list_button_callback(self):
        if hasattr(self, 'stack'):
            if len(self.stack.rois):
                window = CTk.CTkToplevel(self)
                window.attributes('-topmost', 'true')
                window.title('Polarimetry Analysis')
                window.geometry(App.geometry_info["large"])
                CTk.CTkLabel(window, text="  Select ROIs to be removed ", font=CTk.CTkFont(size=20), image=self.icons["format_list"], compound="left").grid(row=0, column=0, padx=30, pady=20)
                variable = tk.StringVar()
                variable.set("all")
                values = ["all"] + [str(_ + 1) for _ in range(len(self.stack.rois))]
                menu = CTk.CTkOptionMenu(master=window, values=values, variable=variable)
                menu.grid(row=1, column=0, padx=20, pady=20)
                ok_button = self.button(master=window, text="       OK", command=lambda:self.remove_roi(window, variable.get()))
                ok_button.configure(width=80, height=App.button_size[1])
                ok_button.grid(row=2, column=0, padx=20, pady=20)

    def remove_roi(self, window, variable):
        if variable == "all":
            self.stack.rois.clear()
        else:
            self.fluo_axis.texts.pop()
            self.fluo_axis.patches.pop()
            self.fluo_fig.canvas.draw()
            self.thrsh_axis.texts.pop()
            self.thrsh_axis.patches.pop()
            self.thrsh_fig.canvas.draw()
            indx = int(variable)
            del self.stack.rois[indx - 1]
            for roi in self.stack.rois:
                if roi["indx"] > indx:
                    roi["indx"] -= 1
        self.represent_fluo(self.stack, drawnow=True, update=False)
        self.represent_thrsh(self.stack, drawnow=True, update=False)
        window.withdraw()

    def export_mask(self):
        if hasattr(self, 'stack'):
            window = CTk.CTkToplevel(self)
            window.attributes('-topmost', 'true')
            window.title('Polarimetry Analysis')
            window.geometry(App.geometry_info["large"])
            CTk.CTkLabel(window, text="  Create Mask by ROI or by Intensity", font=CTk.CTkFont(size=20), image=self.icons['open_in_new'], compound="left").grid(row=0, column=0, padx=30, pady=20)
            CTk.CTkLabel(window, text="  select an output variable ").grid(row=1, column=0, padx=50, pady=20)
            button = CTk.CTkSegmentedButton(master=window, values=["ROI", "Intensity", "ROI x Intensity"], width=300)
            button.grid(row=2, column=0, padx=50, pady=20)
            ok_button = self.button(master=window, text="       OK", command=lambda:self.export_mask_callback(button.get(), window))
            ok_button.configure(width=80, height=App.button_size[1])
            ok_button.grid(row=3, column=0, padx=20, pady=0)

    def export_mask_callback(self, value, window):
        roi_map, mask = self.compute_roi_map(self.stack)
        if value == "ROI":
            array = np.int32(roi_map != 0)
        elif value == "Intensity":
            array = np.int32(self.stack.itot >= float(self.ilow.get()))
        elif value == "ROI x Intensity":
            array = mask
        if np.any(array):
            plt.imsave(str(self.stack.folder) + "/" + self.stack.filename + '.png', array, cmap="gray")
        window.withdraw()

    def change_colormap(self):
        if self.thrsh_colormap == "hot":
            self.thrsh_colormap = "gray"
        else:
            self.thrsh_colormap = "hot"
        if hasattr(self, 'stack'):
            self.represent_thrsh(self.stack, drawnow=True)

    def no_background(self):
        if self.thrsh_fig.patch.get_facecolor() == mpl.colors.to_rgba("k", 1):
            self.thrsh_fig.patch.set_facecolor(App.gray[1])
            self.no_background_button.configure(image=self.icons["photo_fill"])
        else:
            self.thrsh_fig.patch.set_facecolor("k")
            self.no_background_button.configure(image=self.icons["photo"])
        self.thrsh_canvas.draw()
        if hasattr(self, 'stack'):
            self.represent_thrsh(self.stack)

    def offset_angle_switch_callback(self):
        if self.offset_angle_switch.get() == "on":
            self.offset_angle_entry.configure(state="normal")
        else:
            self.offset_angle_entry.configure(state="disabled")

    def dark_switch_callback(self):
        if hasattr(self, "stack"):
            if self.dark_switch.get() == "on":
                self.dark_entry.configure(state="normal")
                self.dark.set(self.stack.display.format(self.stack.calculated_dark))
            else:
                self.dark_entry.configure(state="disabled")
                self.dark.set(self.stack.display.format(self.stack.calculated_dark))
        else:
            self.dark.set(0)

    def calib_dropdown_callback(self, value):
        self.CD = Calibration(self.method_dropdown.get(), label=value)
        self.offset_angle.set(self.CD.offset_default)
        self.calib_textbox.configure(state="normal")
        self.calib_textbox.delete("0.0", "end")
        self.calib_textbox.insert("0.0", self.CD.name)
        self.calib_textbox.configure(state="disabled")

    def polar_dropdown_callback(self, value):
        self.order = self.dict_polar.get(value)

    def diskcone_display(self):
        if self.method_dropdown.get() == "1PF" and hasattr(self, "CD"):
            fig, axs = plt.subplots(1, 2)
            fig.canvas.manager.set_window_title("Disk Cone: " + self.CD.name)
            fig.patch.set_facecolor(App.gray[0])
            axs[0].imshow(self.CD.Rho, cmap="jet")
            axs[0].set_title("Rho Test")
            axs[0].set_facecolor(App.gray[0])
            axs[1].imshow(self.CD.Psi, cmap="jet")
            axs[1].set_title("Psi Test")
            axs[1].set_facecolor(App.gray[0])
            plt.show()

    def variable_table_switch_callback(self):
        state = "normal" if self.variable_table_switch.get() == "on" else "disabled"
        for entry in self.variable_entries:
            entry.configure(state=state)

    def click_background_callback(self):
        if hasattr(self, "stack"):
            self.tabview.set("Fluorescence")
            xlim, ylim = self.fluo_axis.get_xlim(), self.fluo_axis.get_ylim()
            hlines = [plt.Line2D([xlim[0]/2, xlim[1]/2], ylim, lw=1, color="w"), plt.Line2D(xlim, [ylim[0]/2, ylim[1]/2], lw=1, color="w")]
            self.fluo_axis.add_line(hlines[0])
            self.fluo_axis.add_line(hlines[1])
            self.__cid1 = self.fluo_canvas.mpl_connect('motion_notify_event', lambda event: self.click_background_motion_notify_callback(event, hlines))
            self.__cid2 = self.fluo_canvas.mpl_connect('button_press_event', lambda event: self.click_background_button_press_callback(event, hlines))

    def click_background_motion_notify_callback(self, event, hlines):
        if event.inaxes == self.fluo_axis:
            x, y = event.xdata, event.ydata
            xlim, ylim = self.fluo_axis.get_xlim(), self.fluo_axis.get_ylim()
            if event.button is None:
                hlines[0].set_data([x, x], ylim)
                hlines[1].set_data(xlim, [y, y])
                self.fluo_canvas.draw()

    def click_background_button_press_callback(self, event, hlines):
        if event.inaxes == self.fluo_axis:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                x1 = round(x) - self.noise[1].get()//2
                x2 = round(x) + self.noise[1].get()//2
                y1 = round(y) - self.noise[2].get()//2
                y2 = round(y) + self.noise[2].get()//2
                self.noise[3].set(np.mean(self.stack.itot[y1:y2, x1:x2]) / self.stack.nangle * self.noise[0].get())
                self.fluo_canvas.mpl_disconnect(self.__cid1)
                self.fluo_canvas.mpl_disconnect(self.__cid2)
                for line in hlines:
                    line.remove()
                self.fluo_canvas.draw()

    def compute_angle(self):
        self.tabview.set("Fluorescence")
        hroi = ROI()
        self.__cid1 = self.fluo_canvas.mpl_connect('motion_notify_event', lambda event: self.compute_angle_motion_notify_callback(event, hroi))
        self.__cid2 = self.fluo_canvas.mpl_connect('button_press_event', lambda event: self.compute_angle_button_press_callback(event, hroi))

    def compute_angle_motion_notify_callback(self, event, roi):
        if event.inaxes == self.fluo_axis:
            x, y = event.xdata, event.ydata
            if ((event.button is None or event.button == 1) and roi.lines):
                roi.lines[-1].set_data([roi.previous_point[0], x], [roi.previous_point[1], y])
                self.fluo_canvas.draw()

    def compute_angle_button_press_callback(self, event, roi):
        if event.inaxes == self.fluo_axis:
            x, y = event.xdata, event.ydata
            if event.button == 1:
                if not roi.lines:
                    roi.lines = [plt.Line2D([x, x], [y, y], lw=3, color="w")]
                    roi.start_point = [x, y]
                    roi.previous_point = roi.start_point
                    self.fluo_axis.add_line(roi.lines[0])
                    self.fluo_canvas.draw()
                else:
                    roi.lines += [plt.Line2D([roi.previous_point[0], x], [roi.previous_point[1], y], lw=3, color="w")]
                    roi.previous_point = [x, y]
                    self.fluo_axis.add_line(roi.lines[-1])
                    self.fluo_canvas.draw()
                    self.fluo_canvas.mpl_disconnect(self.__cid1)
                    self.fluo_canvas.mpl_disconnect(self.__cid2)
                    slope = 180 - np.rad2deg(np.arctan((roi.previous_point[1] - roi.start_point[1]) / (roi.previous_point[0] - roi.start_point[0])))
                    slope = np.mod(2 * slope, 360) / 2
                    dist = np.sqrt(((np.asarray(roi.previous_point) - np.asarray(roi.start_point))**2).sum())
                    window, buttons = self.showinfo(message="The value of the angle is {:.2f} \u00b0 \n The value of the distance is {} px".format(slope, int(dist)), image=self.icons["square"], button_labels = ["OK"])
                    buttons[0].configure(command=lambda:window.withdraw())
                    for line in roi.lines:
                        line.remove()
                    self.fluo_canvas.draw()

    def define_variable_table(self, method):
        self.initialize_table(mode="all")
        self.clear_frame(self.variable_table_frame)
        self.variable_table_frame.configure(fg_color=self.left_frame.cget("fg_color"))
        CTk.CTkLabel(master=self.variable_table_frame, text="      Min                   Max", text_color="black", font=CTk.CTkFont(weight="bold"), width=200).grid(row=0, column=0, padx=20, pady=10, sticky="e")
        self.variable_table_switch = CTk.CTkSwitch(master=self.variable_table_frame, text="", progress_color=App.orange[0], command=self.variable_table_switch_callback, onvalue="on", offvalue="off", width=50)
        self.variable_table_switch.grid(row=0, column=0, padx=(10, 40), sticky="w")
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
        self.variable_table = [tk.StringVar() for _ in range(len(variables))]
        for it, (var, val) in enumerate(zip(variables, vals)):
            frame = CTk.CTkFrame(master=self.variable_table_frame, fg_color=self.left_frame.cget("fg_color"))
            frame.grid(row=it+1, column=0)
            CTk.CTkCheckBox(master=frame, text=None, variable=self.variable_table[it], width=30).grid(row=0, column=0, padx=(20, 0))
            self.variable_entries += self.double_entry(frame, text=var, text_box=val, row=0, column=1)

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
            window, buttons = self.showinfo(message="Perform: Select a beads file (*.tif)\n Load: Select a registration file (*_reg.mat)\n Registration is performed with Whitelight.tif which should be in the same folder as the beads file", image=self.icons["blur_circular"], button_labels=["Perform", "Load", "Cancel"])
            buttons[0].configure(command=lambda:self.perform_registration(window))
            buttons[1].configure(command=lambda:self.load_registration(window))
            buttons[2].configure(command=lambda:window.withdraw())
        else:
            self.polar_dropdown.configure(state="disabled")

    def perform_registration(self, window):
        self.npix = 5
        filename = fd.askopenfilename(title="Select a beads file", initialdir="/", filetypes=[("Tiff files", "*.tiff"), ("Tiff files", "*.tif")])
        beadstack = self.open_file(filename)
        dark = self.compute_dark(beadstack);
        itot = np.sum((beadstack.values - dark) * (beadstack.values >= dark), 3)
        whitelight = self.open_file(beadstack.folder + "/" + "Whitelight.tif")
        whitelight = whitelight / np.amax(whitelight) * 255
        ret, thrsh = cv2.threshold(whitelight, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, hierarchy = cv2.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        lengths = [len(contour) for contour in contours]
        del contours[lengths <= 200]
        xpos_ = np.zeros((2, 4))
        ypos_ = np.zeros((2, 4))
        for _, contour in enumerate(contours):
            xpos_[:, _] = [np.amin(contour[:, 1]), np.amax(contour[:, 1])]
            ypos_[:, _] = [np.amin(contour[:, 1]), np.amax(contour[:, 1])]
        dx = np.amax(xpos_[1, :] - xpos_[0, :])
        dy = np.amax(ypos_[1, :] - ypos_[0, :])
        ind = np.arange(4)
        Iul = np.argmin(xpos_[0, :] + 1j * ypos_[0, :])
        Ilr = np.argmax(xpos_[0, :] + 1j * ypos_[0, :])
        ind[ind==Iul or ind==Ilr] = [];
        Iur = np.amin(ypos_[0, ind])
        Ill = np.amax(ypos_[0, ind])
        self.xpos[:, 0:3] = xpos_[:, [Iul, ind[Iur], Ilr, ind[Ill]]]
        self.ypos[:, 0:3] = ypos_[:, [Iul, ind[Iur], Ilr, ind[Ill]]]
        for it in range(4):
            ddx = dx + self.npix + self.xpos[0, it] - 1
            ddy = dy + self.npix + self.ypos[0, it] - 1
            im = itot[self.ypos[0, it]-self.npix:ddy, self.xpos[0, it]-app.npix:ddx]
            im = im / np.amax(im) * 255
            ret, im = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            ims += [im]

                            [optimizer,metric] = imregconfig('multimodal');
                            optimizer.MaximumIterations = 1000;
                            optimizer.InitialRadius = 1e-3;
                            optimizer.Epsilon = 1.5e-6;
                            optimizer.GrowthFactor = 1.0001;
                            ims_reg = ims;
                            tform_ = cell(2,length(ims));
                            tform_{1,1} = rigid2d;
                            tform_{2,1} = rigid2d;
                            for it = 2:length(ims)
                                tform_{1,it} = imregtform(ims{it},ims{1},'translation',optimizer,metric);
                                ims_reg{it} = imwarp(ims{it},tform_{1,it},'OutputView',imref2d(size(ims{1})));
                                tform_{2,it} = imregtform(ims_reg{it},ims{1},'affine',optimizer,metric);
                                ims_reg{it} = imwarp(ims_reg{it},tform_{2,it},'OutputView',imref2d(size(ims{1})));
                            end
                            fig = figure('Name','Quality of calibration');
                            titles = {'UL','UR','LR','LL'};
                            panel = [1 2 4 3];
                            for it = 2:length(ims)
                                subplot(2,2,panel(it));
                                imshowpair(ims{1},ims_reg{it},'Scaling','joint'); axis image;
                                set(gca,'visible','off');
                                title(titles{it})
                            end
                            ok_reg = uiconfirm(app.PolarimetryAnalysisUIFigure,'Are you okay with this registration?', ...
                                'Registration','Options',{'Yes','Yes and Save','No'},'DefaultOption',2,'Icon','Icons/round_blur_circular_black_48dp.png');
                            switch ok_reg
                                case 'Yes'
                                    close(fig)
                                    app.tform = tform_;
                                case 'Yes and Save'
                                    close(fig)
                                    [~,name,~] = fileparts([path_ filename]);
                                    xpos_ = app.xpos;
                                    ypos_ = app.ypos;
                                    npix_ = app.npix;
                                    save([path_ name '_reg.mat'],'tform_','xpos_','ypos_','npix_');
                                    app.tform = tform_;
                                case 'No'
                                    close(fig)
                                    app.PolarimetryMethod.Value = '1PF';
                                    app.PolarimetryMethod.ValueChangedFcn(app,event)
                                    app.tform = [];
                            end

    def load_registration(self, window):
        filename = fd.askopenfilename(title="Select a registration file", initialdir="/", filetypes=[("MAT-files", "*.mat")])
        file = h5py.File(filename, "r")
        self.tform = file.get("tform_")
        self.xpos = file.get("xpos_")
        self.ypos = file.get("ypos_")
        self.npix = file.get("npix_")
        window.withdraw()

    def open_file(self, filename):
        dataset = Image.open(filename, mode="r")
        h, w = np.shape(dataset)
        stack_vals = np.zeros((h, w, dataset.n_frames), dtype=np.float64)
        for _ in range(dataset.n_frames):
           dataset.seek(_)
           stack_vals[:, :, _] = np.array(dataset)
        dict = {"values": stack_vals, "height": h, "width": w, "nangle": dataset.n_frames, "mode": dataset.mode, "display": "{:.2f}" if dataset.mode == "I" else "{:.0f}"}
        stack = Stack(filename)
        for key in dict:
            setattr(stack, key, dict[key])
        stack = self.define_itot(stack)
        return stack

    def select_file(self):
        filetypes = [("Tiff files", "*.tiff"), ("Tiff files", "*.tif")]
        filename = fd.askopenfilename(title="Select a file", initialdir="/", filetypes=filetypes)
        self.single_file = True
        if filename:
            self.tabview.set("Fluorescence")
            self.stack = self.open_file(filename)
            if self.stack.nangle >= 2:
                self.stack_slider.configure(to=self.stack.nangle)
            else:
                self.stack_slider.configure(state="disabled")
            self.filename_label.configure(text=os.path.basename(filename).split('.')[0])
            self.represent_fluo(self.stack, drawnow=True, update=False)
            self.represent_thrsh(self.stack, drawnow=True, update=False)
            self.tabview.set("Fluorescence")

    def select_folder(self):
        self.single_file = False
        folder = fd.askdirectory(title="Select a directory", initialdir="/")
        list_file = [filename.endswith(('.tif', '.tiff')) for filename in os.listdir(folder)]
        if folder and any(list_file):
            self.tabview.set("Fluorescence")
            for filename in list_file:
                self.stack = Stack(filename)
                dataset = Image.open(filename)

    def tool_dropdown_callback(self, method):
        self.advance_file = True if method.endswith("(auto)") else False
        if hasattr(self, "stack"):
            if method.startswith("Mask"):
                self.ilow.set(self.stack.display.format(np.amin(self.stack.itot)))
                self.represent_thrsh(self.stack)

    def add_roi_callback(self):
        if hasattr(self, "stack"):
            self.tabview.set("Thresholding/Mask")
            hroi = ROI()
            self.__cid1 = self.thrsh_canvas.mpl_connect('motion_notify_event', lambda event: self.add_roi_motion_notify_callback(event, hroi))
            self.__cid2 = self.thrsh_canvas.mpl_connect('button_press_event', lambda event: self.add_roi_button_press_callback(event, hroi))

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
            if event.button == 1 and not event.dblclick:
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
            elif (event.button == 1 and event.dblclick) and roi.lines:
                roi.lines += [plt.Line2D([roi.previous_point[0], roi.start_point[0]], [roi.previous_point[1], roi.start_point[1]], marker='o', color="w")]
                self.thrsh_axis.add_line(roi.lines[-1])
                self.thrsh_canvas.mpl_disconnect(self.__cid1)
                self.thrsh_canvas.mpl_disconnect(self.__cid2)
                self.thrsh_canvas.draw()
                window, buttons = self.showinfo(message="Add ROI?", image=self.icons["roi"], button_labels=["Yes", "No"])
                buttons[0].configure(command=lambda:self.yes_add_roi_callback(window, roi))
                buttons[1].configure(command=lambda:self.no_add_roi_callback(window, roi))

    def yes_add_roi_callback(self, window, roi):
        roi_path = Path(([(roi.x[0], roi.y[0])] + list(zip(reversed(roi.x), reversed(roi.y)))))
        if self.stack.rois:
            indx = self.stack.rois[-1]["indx"] + 1
        else:
            indx = 1
        self.stack.rois += [{"indx": indx, "label": (roi.x[0], roi.y[0]), "Path": roi_path, "ILow": self.ilow.get()}]
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_canvas.draw()
        self.represent_fluo(self.stack)
        self.represent_thrsh(self.stack)

    def no_add_roi_callback(self, window, roi):
        window.withdraw()
        for line in roi.lines:
            line.remove()
        roi.lines = []
        self.thrsh_canvas.draw()

    def get_mask(self):
        mask = np.ones((self.stack.height, self.stack.width))
        if self.method_dropdown.get().startswith("Mask"):
            mask_name = self.stack.folder + "/" + self.stack.filename + ".png"
            if os.path.isfile(mask_name):
                im_binarized = np.asarray(plt.imread(mask_name), dtype=np.float64)
                mask = im_binarized / np.amax(im_binarized)
        return mask

    def analysis_callback(self):
        if hasattr(self, "stack"):
            self.tabview.set("Fluorescence")
            self.analysis_button.configure(image=self.icons["pause"])
            if not self.advance_file:
                self.analyze(self.stack)

    def close_callback(self):
        plt.close("all")

    def stack_slider_callback(self, value):
        self.stack_slider_label.configure(text=int(value))
        if value == 0:
            self.stack_slider_label.configure(text="T")
        if self.method_dropdown.get().startswith("4POLAR"):
            labels = ["T", 0, 45, 90, 135]
            self.stack_slider_label.configure(text=labels[int(value)])
        if hasattr(self, "stack"):
            self.represent_fluo(self.stack)

    def ilow_slider_callback(self, value):
        if hasattr(self, "stack"):
            self.ilow.set(self.stack.display.format(value))
            self.represent_thrsh(self.stack)

    def ilow2slider_callback(self, event):
        if event and hasattr(self, "stack"):
            self.ilow_slider.set(float(self.ilow.get()))
            self.represent_thrsh(self.stack)

    def itot_callback(self, event):
        if event and hasattr(self, "stack"):
            self.stack = self.define_itot(self.stack)
            self.represent_fluo(self.stack, update=False)
            self.represent_thrsh(self.stack, update=False)

    def rotation_callback(self, event):
        if event and hasattr(self, "stack"):
            self.represent_fluo(self.stack, update=False)

    def transparency_slider_callback(self, value):
        if value <= 0.001:
            self.transparency_slider.set(0.001)
        if hasattr(self, "stack"):
            self.represent_thrsh(self.stack)

    def adjust(self, field, contrast, vmin, vmax):
        amount = 0.8
        gaussian_3 = cv2.GaussianBlur(field, (0, 0), 1)
        field = cv2.addWeighted(field, 1 + amount, gaussian_3, -amount, 0)
        field = np.maximum(field, vmin)
        field = exposure.adjust_gamma((field - vmin) / vmax, contrast) * vmax
        return field

    def represent_fluo(self, stack, drawnow=False, update=True):
        if not drawnow:
            xlim_fluo = self.fluo_axis.get_xlim()
            ylim_fluo = self.fluo_axis.get_ylim()
        if self.stack_slider.get() == 0:
            field = stack.itot
            vmin, vmax = np.amin(stack.itot), np.amax(stack.itot)
        elif self.stack_slider.get() <= self.stack.nangle:
            field = stack.values[:, :, int(self.stack_slider.get())-1]
            vmin, vmax = np.amin(stack.values), np.amax(stack.values)
        field = self.adjust(field, self.contrast_fluo_slider.get(), vmin, vmax)
        if self.rotation[1].get() != 0:
            field = imutils.rotate(field, int(self.rotation[1].get()))
            ts = self.fluo_axis.transData
            coords = ts.transform([stack.width/2, stack.height/2])
            tr = mpl.transforms.Affine2D().rotate_deg_around(coords[0], coords[1], int(self.rotation[1].get()))
            transform = ts + tr
            mat = cv2.getRotationMatrix2D((stack.width/2, stack.height/2), int(self.rotation[1].get()), 1.0)
        if update:
            self.fluo_im.set_data(field)
        else:
            self.fluo_im = self.fluo_axis.imshow(field, cmap=mpl.colormaps["gray"], interpolation="nearest")
            self.fluo_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.fluo_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
        if not drawnow:
            self.fluo_axis.set_xlim(xlim_fluo)
            self.fluo_axis.set_ylim(ylim_fluo)
        self.fluo_im.set_clim(vmin, vmax)
        if self.fluo_axis.patches:
            self.fluo_axis.texts.pop()
            self.fluo_axis.patches.pop()
            self.fluo_fig.canvas.draw()
        if len(stack.rois):
            for roi in stack.rois:
                hpatch = PathPatch(roi["Path"], facecolor="none", edgecolor="white")
                htext = self.fluo_axis.text(roi["label"][0], roi["label"][1], str(roi["indx"]), color="w", transform_rotates_text=False)
                if self.rotation[1].get() != 0:
                    hpatch.set_transform(transform)
                    htext.set_transform(transform)
                self.fluo_axis.add_patch(hpatch)
        self.fluo_fig.canvas.draw()

    def represent_thrsh(self, stack, drawnow=False, update=True):
        field = stack.itot
        if self.method_dropdown.get().startswith("Mask"):
            mask_name = os.path.basename(self.stack.filename) + ".png"
            if os.path.isfile(mask_name):
                im_binarized = cv2.imread(mask_name)
                mask = np.asarray(im_binarized, dtype=np.float64)
                mask = mask / np.amax(mask)
                field =field * mask
        vmin, vmax = np.amin(field), np.amax(field)
        field = self.adjust(field, self.contrast_thrsh_slider.get(), vmin, vmax)
        alphadata = np.ones(field.shape)
        thrsh = float(self.ilow.get())
        alphadata[field <= thrsh] *= self.transparency_slider.get()
        if update:
            plt.setp(self.thrsh_im, alpha=alphadata, cmap=self.thrsh_colormap)
            self.thrsh_im.set_data(field)
        else:
            self.thrsh_im = self.thrsh_axis.imshow(field, cmap=self.thrsh_colormap, alpha=alphadata)
            self.thrsh_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.thrsh_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
        self.thrsh_im.set_clim(vmin, vmax)
        if self.thrsh_axis.patches:
            self.thrsh_axis.texts.pop()
            self.thrsh_axis.patches.pop()
            self.thrsh_fig.canvas.draw()
        if len(stack.rois):
            for roi in stack.rois:
                self.thrsh_axis.add_patch(PathPatch(roi["Path"], facecolor="none", edgecolor="white"))
                self.thrsh_axis.text(roi["label"][0], roi["label"][1], str(roi["indx"]), color="w")
        self.thrsh_fig.canvas.draw()

    def define_itot(self, stack):
        stack.calculated_dark = self.compute_dark(stack)
        self.calculated_dark_label.configure(text="Calculated dark value = " + stack.display.format(stack.calculated_dark))
        if self.dark_switch.get() == "on":
            self.calculated_dark_label.configure(font=CTk.CTkFont(weight="normal"))
            dark = self.dark.get()
        else:
            self.calculated_dark_label.configure(font=CTk.CTkFont(weight="bold"))
            dark = stack.calculated_dark
        sumcor = np.sum((stack.values - dark) * (stack.values >= dark), axis=2)
        bin_shape = [self.bin[_].get() for _ in range(2)]
        if sum(bin_shape) != 2:
            stack.itot = convolve2d(sumcor, np.ones(bin_shape), mode="same") / (bin_shape[0] * bin_shape[1])
        else:
            stack.itot = sumcor
        self.ilow_slider.configure(from_=np.amin(stack.itot), to=np.amax(stack.itot))
        self.ilow_slider.set(np.amin(stack.itot))
        self.ilow.set(stack.display.format(np.amin(stack.itot)))
        return stack

    def compute_dark(self, stack):
        SizeCell = 20
        NCellHeight = int(np.floor(stack.height / SizeCell))
        NCellWidth = int(np.floor(stack.width / SizeCell))
        cropIm = stack.values[:SizeCell * NCellHeight, :SizeCell * NCellWidth, :]
        ImCG = np.asarray(np.split(np.asarray(np.split(cropIm, NCellHeight, axis=0)), NCellWidth, axis=2))
        mImCG = np.zeros((NCellHeight, NCellWidth))
        for it in range(NCellHeight):
            for jt in range(NCellWidth):
                cell = ImCG[it, jt, :, :, 0]
                mImCG[it, jt] = np.mean(cell[cell != 0])
        IndI, IndJ = np.where(mImCG == np.amin(mImCG))
        cell = ImCG[IndI, IndJ, :, :, :]
        dark = np.mean(cell[cell != 0])
        return dark

    def circularmean(self, rho):
        return np.mod(np.angle(np.mean(np.exp(2j * rho), deg=True)), 360) / 2

    def get_variable(self, i):
        display = self.variable_table[i].get()
        min, max = [self.variable_entries[i][_] for _ in range(2)]
        return display, min, max

    def plot_histo(self, data, type="normal", roi=[]):
        suffix = "for ROI " + str(roi) if roi else ""
        fig, ax = plt.figure(figsize=App.figsize)
        fig.canvas.manager.set_window_title(data.name + "histogram" + suffix)
        fig.patch.set_facecolor(App.gray[0])
        if not roi:
            roi = 1
        data_vals = data.values((roi_map == roi) * (~np.isnan(data.values)))
        if type == "normal":
            bins = np.linspace(np.amin(data), np.amax(data), np.amax(data)/60)
            n, bins, patches = ax.hist(data.values, bins)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            norm = mpl.colors.Normalize(data.min, data.max)
            for bin, patch in zip(bin_centers, patches):
                patch.set_facecolor(norm[bin])
            ax.set_xlim(np.amin(data), np.amax(data))
            ax.set_xlabel(data.latex, usetex=True, fontsize=20)
            ax.set_title(data.filename, fontsize=14)
            text = data.latex + " = " + "{:.2f}".format(np.mean(data_vals)) + " $\pm$ " "{:.2f}".format(np.std(data_vals))
            ax.annotate(text, (0.2, 0.91), textcoords="figure fraction", fontsize=20, usetex=True)
        elif type == "polar1":
            data_vals = np.mod(2 * (data_vals + float(self.rotation[1].get())), 360) / 2
            meandata = self.circularmean(data_vals)
            delta_rho = np.mod(2 * (data_vals - meandata), 180) / 2
        elif type == "polar2":
            print("in progress...")

    def compute_roi_map(self, stack):
        shape = (stack.height, stack.width)
        if len(stack.rois):
            roi_map = np.zeros(shape)
            roi_ilow_map = np.zeros(shape)
            for roi in stack.rois:
                roi_map[roi["Path"].contains_points(points).reshape(shape)] = roi["indx"]
                roi_ilow_map[roi["Path"].contains_points(points).reshape(shape)] = roi["ILow"]
        else:
            roi_map = np.ones(shape)
            roi_ilow_map = np.ones(shape) * self.ilow.get()
        mask = self.get_mask()
        return roi_map, (stack.itot >= roi_ilow_map) * mask

    def slice4polar(self, stack, xpos, ypos, npix):
        stack_ = Stack(stack.filename)
        stack_.display = stack.display
        stack_.nangle = 4
        stack_.height = np.amax(ypos[1, :] - ypos[0, :]) + 2 * npix
        stack_.width = np.amax(xpos[1, :] - xpos[0, :]) + 2 * npix
        stack_.values = np.zeros((stack_.height, stack_.width, 4))
        ims = []
        for it in range(4):
            ddx = stack_.width - npix + xpos[0, it] - 1
            ddy = stack_.height - npix + ypos[0, it] - 1
            ims += [stack.values[ypos[0, it] - npix:ddy, xpos[0, it] - npix:ddx, 0]]
        ims_reg = ims
        #for it in range(1, 4):
        #    ims_reg[it] = imwarp(ims[it], app.tform{1,it}, 'OutputView', imref2d(size(ims[0])))
        #    ims_reg[it] = imwarp(ims_reg{it},app.tform{2,it},'OutputView',imref2d(size(ims[0])))
        for it in range(4):
            stack_.values[:, :, self.order[it]] = ims_reg[it]

    def analyze_stack(self, stack):
        chi2threshold = 500
        shape = (stack.height, stack.width)
        roi_map, mask = self.compute_roi_map(stack)
        if self.dark_switch.get() == "on":
            dark = self.dark.get()
        else:
            dark = stack.calculated_dark
        Y, X = np.mgrid[0:stack.width, 0:stack.height]
        points = np.vstack((X.flatten(), Y.flatten())).T
        field = stack.values - dark - float(self.noise[3].get())
        field = field * (field >= 0)
        if self.method_dropdown.get() == "1PF":
            field = sqrt(field)
        elif self.method_dropdown.get() in ["4POLAR 2D", "4POLAR 3D"]:
            field[:, :, [2, 3]] = field[:, :, [3, 2]]
        bin_shape = [self.bin[_].get() for _ in range(2)]
        if sum(bin_shape) != 2:
            bin = np.ones(int(_) for _ in bin_shape)
            field = convolve2d(field, bin, mode="same") / (bin_shape[0] * bin_shape[1])
        if self.method_dropdown.get() in ["1PF", "CARS", "SRS", "SHG", "2PF"]:
            angle3d = (np.linspace(0, 180, stack.nangle + 1) + 180 - self.offset_angle.get()).reshape(1, 1, -1)
            e2 = exp(2j * np.deg2rad(angle3d))
            a0 = np.mean(field, axis=2)
            a2 = 2 * np.mean(field * e2, axis=2)
            field_fit = a0 + (a2 * e2.conj()).real
            a2 = a2 / a0
            if self.method_dropdown.get() in ["CARS", "SRS", "SHG", "2PF"]:
                e4 = e2**2
                a4 = 2 * np.mean(field * e4, axis=2)
                field_fit += (a4 * e4.conj()).real
                a4 = a4 / a0
            chi2 = np.mean((field - field_fit)**2 / field_fit, axis=2)
        elif self.method_dropdown.get() == "4POLAR 3D":
            mat = np.einsum("ij,mnj->imn", app.invKmat_3D, field)
            s = mat[0, :, :] + mat[1, :, :] + mat[2, :, :]
            pxy = ((mat[0, :, :] - mat[1, :, :]) / s).reshape(shape)
            puv = (2 * mat[3, :, :] / s).reshape(shape)
            pzz = (mat[2, :, :] / s).reshape(shape)
            lam = ((1 - (pzz + np.sqrt(puv**2 + pxy**2))) / 2).reshape(shape)
            a0 = np.mean(field, axis=2) / 4
        elif self.method_dropdown.get() == '4POLAR 2D':
            mat = np.einsum("ij,mnj->imn", app.invKmat_2D, field)
            s = mat[0, :, :] + mat[1, :, :] + mat[2, :, :]
            pxy = ((mat[0, :, :] - mat[1, :, :]) / s).reshape(shape)
            puv = (2 * mat[3, :, :] / s).reshape(shape)
            lam = ((1 - (pzz + np.sqrt(puv**2 + pxy**2))) / 2).reshape(shape)
            a0 = np.mean(field, axis=2) / 4
        rho_ = Variable(stack)
        rho_.name, rho_.latex = "Rho", "$\rho$"
        rho_.display, rho_.min, rho_.max = self.get_variable(0)
        rho_.colormap = hsv
        ind = (roi_map > 0) * (mask != 0)
        if self.method_dropdown.get() == "1PF":
            ind *= (np.abs(a2) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho = np.empty(shape)
            rho[ind] = app.CD.Rho[np.round_((a2.real[ind] + 1) * self.CD.h), np.round_((a2.imag[ind] + 1) * self.CD.h)] + 90
            rho[np.logical_not(ind)] = np.nan
            psi = np.empty(shape)
            psi[ind] = app.CD.Psi[np.round_((a2.real[ind] + 1) * self.CD.h), np.round_((a2.imag[ind] + 1) * self.CD.h)]
            psi[np.logical_not(ind)] = np.nan
            ind *= (rho == np.nan) * (psi == np.nan)
            rho_.value[ind] = np.mod(2 * (180 - rho[ind] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable(stack)
            psi_.name, psi_.latex = "Psi", "$\psi$"
            psi_.value[ind] = psi[ind]
            psi_.display, psi_.min, psi_.max = self.get_variable(1)
            psi_.colormap = jet
        elif self.method_dropdown.get() in ["CARS", "SRS", "2PF"]:
            ind *= (np.abs(a2) < 1) * (np.abs(a4) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho_.value[ind] = np.rad2deg(np.angle(a2[ind])) / 2
            rho_.value[ind] = np.mod(2 * (180 - rho_.value[ind] + float(self.rotation[0].get())), 360) / 2
            s2_ = Variable(stack)
            s2_.name, s2_.latex = "S2", "$S_2$"
            s2_.value[ind] = 1.5 * np.abs(a2[ind])
            s2_.display, s2_.min, s2_.max = self.get_variable(1)
            s2_.colormap = jet
            s4_ = Variable(shape)
            s4_.name, s4_.latex = "S4", "$S_4$"
            s4_.value[ind] = 6 * np.abs(a4[ind]) * np.cos(4 * (0.25 * np.angle(a4[ind]) - np.deg2rad(rho_.value[ind])))
            s4_.display, s4_.min, s4_.max = self.get_variable(2)
            s4_.colormap = jet
        elif self.method_dropdown.get() == 'SHG':
            ind *= (np.abs(a2) < 1) * (np.abs(a4) < 1) * (chi2 <= chi2threshold) * (chi2 > 0)
            rho_.value[ind] = np.rad2deg(np.angle(a2[ind])) / 2
            rho_.value[ind] = np.mod(2 * (180 - rho_.value[ind] + float(self.rotation[0].get())), 360) / 2
            s_shg_ = Variable(stack)
            s_shg_.name, s_shg_.latex = "S_SHG", "$S_\mathrm{SHG}$"
            s_shg_.value[ind] = -0.5 * (np.abs(a4[ind]) - np.abs(a2[ind])) / (np.abs(a4[ind]) + np.abs(a2[ind])) - 0.65
            s_shg_.display, s_shg_.min, s_shg_.max = self.get_variable(1)
            s_shg_.colormap = jet
        elif self.method_dropdown.get() == "4POLAR 3D":
            ind *= (lam < 1/3) * (lam > 0) * (pzz > lam)
            rho_.value[ind] = 0.5 * np.rad2deg(np.atan2(puv[ind], pxy[ind]))
            rho_.value[ind] = np.mod(2 * (180 - rho_.value[ind] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable(stack)
            psi_.name, psi_.latex = "Psi", "$\psi$"
            psi_.value[ind] = 2 * np.rad2deg(np.acos((-1 + np.sqrt(9 - 24 * lam[ind])) / 2))
            psi_.display, psi_.min, psi_.max = self.get_variable(1)
            psi_.colormap = jet
            eta_ = Variable(shape)
            eta_.name, eta_.latex = "Eta", "$\eta$"
            eta_.value[ind] = np.rad2deg(np.acos(np.sqrt((pzz[ind] - lam[ind]) / (1 - 3 * lam[ind]))))
            eta_.display, eta_.min, eta_.max = self.get_variable(2)
            eta_.colormap = parula
        elif self.method_dropdown.get() == "4POLAR 2D":
            ind *= (lam < 1/3) * (lam > 0)
            rho_.value[ind] = 0.5 * np.rad2deg(np.atan2(puv[ind], pxy[ind]))
            rho_.value[ind] = np.mod(2 * (180 - rho_.value[ind] + float(self.rotation[0].get())), 360) / 2
            psi_ = Variable(stack)
            psi_.name, psi_.latex = "Psi", "$\psi$"
            psi_.value[ind] = 2 * np.rad2deg(np.acos((-1 + np.sqrt(9 - 24 * lam[ind])) / 2))
            psi_.display, psi_.min, psi_.max = self.get_variable(2)
            psi_.colormap = jet
        a0[np.logical_not(ind)] = np.nan
        X[np.logical_not(ind)] = np.nan
        Y[np.logical_not(ind)] = np.nan
        if self.method_dropdown.get() in ["1PF", "CARS", "SRS", "SHG", "2PF"]:
            chi2[np.logical_not(ind)] = np.nan

class Stack():
    def __init__(self, filename):
        self.filename = pathlib.Path(filename).stem
        self.folder = pathlib.Path(filename).parent
        self.values = []
        self.height, self.width, self.nangle = 0, 0, 0
        self.calculated_dark = 0
        self.mode = "I"
        self.display = []
        self.itot = []
        self.rois = []

class Variable():
    def __init__(self, stack):
        self.name = ""
        self.latex = ""
        self.value = np.empty((stack.height, stack.width))
        self.value[:] = np.nan
        self.display = []
        self.min = []
        self.max = []
        self.colormap = []
        self.filename = stack.filename

class ROI:
    def __init__(self):
        self.start_point = []
        self.end_point = []
        self.previous_point = []
        self.x = []
        self.y = []
        self.lines = []

class Calibration():

    dict_1pf = {"488 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 85), "561 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 30), "640 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 35), "488 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga0_Pa20_Ta45_Gb-0.1_Pb0_Tb0_Gc-0.1_Pc0_Tc0", 100), "561 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga-0.2_Pa0_Ta0_Gb0.1_Pb0_Tb0_Gc-0.2_Pc0_Tc0", 100), "640 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga-0.2_Pa0_Ta45_Gb0.1_Pb0_Tb45_Gc-0.1_Pc0_Tc0", 100), "488 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb20_Tb45_Gc-0.2_Pc0_Tc0", 100), "561 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.2_Pa0_Ta0_Gb0.2_Pb20_Tb0_Gc-0.2_Pc0_Tc0", 100), "640 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc-0.2_Pc0_Tc0", 100), "488 nm (before 13/12/2019)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc0.1_Pc0_Tc0", 100), "561 nm (before 13/12/2019)": ("Disk_Ga0.1_Pa0_Ta45_Gb-0.1_Pb20_Tb0_Gc-0.1_Pc0_Tc0", 100), "640 nm (before 13/12/2019)": ("Disk_Ga-0.1_Pa10_Ta0_Gb0.1_Pb30_Tb0_Gc0.2_Pc0_Tc0", 100), "no distortions (before 12/04/2022)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 100), "other": (None, 0)}

    folder_1pf = os.path.join(os.path.dirname(os.path.realpath(__file__)), "DiskCones")

    dict_4polar = {"Calib_20221102": ("Calib_20221102", 0), "Calib_20221011": ("Calib_20221011", 0), "other": (None, 0)}

    folder_4polar = os.path.join(os.path.dirname(os.path.realpath(__file__)), "CalibrationData")

    def __init__(self, method, label=None):
        if label is None:
            if method == "1PF":
                label = "488 nm (no distortions)"
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
                file = pathlib.Path(fd.askopenfilename(title='Select file', initialdir='/', filetypes=[("MAT-files", "*.mat")]))
                folder = str(file.parent)
                vars = (str(file.stem), 0)
            disk = scipy.io.loadmat(folder + "/" + vars[0] + ".mat")
            if method == "1PF" and vars[0].startswith("Disk"):
                self.Rho = np.array(disk["RoTest"], dtype=np.float64)
                self.Psi = np.array(disk["PsiTest"], dtype=np.float64)
                self.h = float((disk["NbMapValues"] - 1) / 2)
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

if __name__ == "__main__":
    app = App()
    app.mainloop()
