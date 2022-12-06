import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import webbrowser
import customtkinter as CTk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from PIL import ImageTk, Image
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from skimage import exposure
from scipy import ndimage

CTk.set_default_color_theme("dark-blue")
CTk.set_appearance_mode("dark")

mpl.use('TkAgg')

class App(CTk.CTk):

    left_frame_width = 180
    right_frame_width = 800
    height = 800
    width = left_frame_width + right_frame_width
    tab_width = right_frame_width - 40
    height_tab = height - 20
    button_pady = 25
    axes_size = (650, 650)
    button_size = (160, 40)
    geometry_info = "400x300+400+300"

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
        self.right_frame = CTk.CTkFrame(master=self, fg_color=App.gray[0], width=App.right_frame_width)
        self.right_frame.grid(row=0, column=1, sticky="nswe", padx=0, pady=0)

## DEFINE TABS
        self.tabview = CTk.CTkTabview(master=self.right_frame, width=App.tab_width, height=App.height_tab, segmented_button_selected_color=App.orange[0], segmented_button_unselected_color=App.gray[1], segmented_button_selected_hover_color=App.orange[1], text_color="black", segmented_button_fg_color=App.gray[0], fg_color=App.gray[1])
        self.tabview.grid(row=0, column=0, padx=10, pady=0)
        list_tabs = ["Fluorescence", "Thresholding/Mask", "Options", "Advanced", "About"]
        for tab in list_tabs:
            self.tabview.add(tab)

## LEFT FRAME
        logo = self.button(self.left_frame, text="POLARIMETRY \n ANALYSIS", image=self.icons['blur_circular'], command=self.on_click_tab)
        logo.configure(hover=False, fg_color="transparent", anchor="e")
        logo.grid(row=0, column=0, pady=30, padx=17)
        self.button(self.left_frame, text="Download File", command=self.select_file, image=self.icons['download_file']).grid(row=2, column=0, pady=App.button_pady, padx=17)
        self.button(self.left_frame, text="Download Folder", command=self.select_folder, image=self.icons['download_folder']).grid(row=3, column=0, pady=App.button_pady, padx=17)
        self.button(self.left_frame, text="Add ROI", image=self.icons['roi']).grid(row=5, column=0, pady=App.button_pady, padx=17)
        self.analysis_button = self.button(self.left_frame, text="Analysis", image=self.icons['play'])
        self.analysis_button.configure(fg_color=App.green[0], hover_color=App.green[1])
        self.analysis_button.grid(row=6, column=0, pady=App.button_pady, padx=17)
        button = self.button(self.left_frame, text="Close figures", image=self.icons['close'])
        button.configure(fg_color=App.red[0], hover_color=App.red[1])
        button.grid(row=7, column=0, pady=App.button_pady, padx=17)
        self.method_dropdown = self.dropdown(self.left_frame, values=["1PF", "CARS", "SRS", "SHG", "2PF", "4POLAR 2D", "4POLAR 3D"], image=self.icons["microscope"], row=1, column=0, command=self.method_dropdown_callback)
        self.tool_dropdown = self.dropdown(self.left_frame, values=["Thresholding (manual)", "Thresholding (auto)", "Mask (manual)", "Mask (auto)"], image=self.icons["build"], row=4, column=0, command=self.tool_dropdown_callback)

## RIGHT FRAME: FLUO
        self.fluo_frame = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent", width=App.axes_size[1], height=App.axes_size[0])
        self.fluo_frame.grid(row=0, column=0, padx=0, pady=0)
        self.fluo_fig = Figure(figsize=(6.5, 6.5), facecolor=App.gray[1])
        self.fluo_axis = self.fluo_fig.add_axes([0, 0, 1, 1])
        self.fluo_axis.set_axis_off()
        self.fluo_canvas = FigureCanvasTkAgg(self.fluo_fig, master=self.fluo_frame)
        self.fluo_canvas.draw()
        self.fluo_toolbar = NavigationToolbar2Tk(self.fluo_canvas, self.fluo_frame, pack_toolbar=False)
        self.fluo_toolbar.update()
        self.fluo_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)
        banner = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent")
        banner.grid(row=0, column=1)
        self.button(banner, text="", image=self.icons["contrast"], command=self.contrast_fluo_button_callback).grid(row=0, column=0, sticky="ne", padx=20, pady=20)
        self.contrast_fluo_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_fluo_slider_callback, button_color=App.orange[0], button_hover_color=App.orange[1])
        self.contrast_fluo_slider.grid(row=1, column=0, padx=20, pady=20)
        self.button(banner, text="", image=self.icons["refresh"], command=self.reload_button_callback).grid(row=2, column=0, padx=20, pady=20)
        self.button(banner, text="", image=self.icons["square"], command=self.compute_angle).grid(row=3, column=0, padx=20, pady=20)
        banner = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent", width=App.axes_size[1], height=40)
        banner.grid(row=1, column=0, pady=20)
        self.filename_label = CTk.CTkLabel(master=banner, fg_color="transparent", text="", text_color="black", font=CTk.CTkFont(weight="bold"))
        self.filename_label.place(relx=0, rely=0.2)
        self.stack_slider = CTk.CTkSlider(master=banner, from_=0, to=18, number_of_steps=18, command=self.stack_slider_callback, button_color=App.orange[0], button_hover_color=App.orange[1])
        self.stack_slider.set(0)
        self.stack_slider.place(relx=0.68, rely=0.1)
        self.stack_slider_label = CTk.CTkLabel(master=banner, fg_color="transparent", text="T", text_color="black", font=CTk.CTkFont(weight="bold"))
        self.stack_slider_label.place(relx=0.95, rely=0.5)
        CTk.CTkLabel(master=banner, fg_color="transparent", text="Stack", text_color="black", font=CTk.CTkFont(weight="bold")).place(relx=0.7, rely=0.5)

## RIGHT FRAME: THRSH
        self.thrsh_axis = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent", width=App.axes_size[1], height=App.axes_size[0])
        self.thrsh_axis.grid(row=0, column=0, padx=0, pady=0)
        banner = CTk.CTkFrame(master=self.tabview.tab("Thresholding/Mask"), fg_color="transparent")
        banner.grid(row=0, column=1)
        self.button(banner, text="", image=self.icons["contrast"], command=self.contrast_thrsh_button_callback).grid(row=0, column=0, sticky="ne", padx=20, pady=20)
        self.contrast_thrsh_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_thrsh_slider_callback, button_color=App.orange[0], button_hover_color=App.orange[1])
        self.contrast_thrsh_slider.grid(row=1, column=0, padx=20, pady=20)
        self.button(banner, text="", image=self.icons["open_in_new"], command=self.export_mask).grid(row=2, column=0, padx=20, pady=20)
        self.button(banner, text="", image=self.icons["palette"], command=self.change_colormap).grid(row=3, column=0, padx=20, pady=20)
        self.button(banner, text="", image=self.icons["photo"], command=self.no_background).grid(row=4, column=0, padx=20, pady=20)

        self.ilow_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, command=self.ilow_slider_callback, button_color=App.orange[0], button_hover_color=App.orange[1])
        self.ilow_slider.set(0)
        self.ilow_slider.place(relx=0.2, rely=0.93, anchor="w")
        self.ilow_slider_label = CTk.CTkLabel(master=self.tabview.tab("Thresholding/Mask"), width=20, height=10, fg_color="transparent", text=0, text_color="black", font=CTk.CTkFont(weight="bold"))
        self.ilow_slider_label.place(relx=0.2, rely=0.96, anchor="w")
        self.transparency_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, button_color=App.orange[0], button_hover_color=App.orange[1])
        self.transparency_slider.place(relx=0.6, rely=0.93, anchor="w")

## RIGHT FRAME: OPTIONS
        show_save = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=App.gray[0], width=400)
        show_save.grid(row=0, column=0, padx=(20, 20), pady=20, sticky="nw")
        CTk.CTkLabel(master=show_save, text="Show", anchor="w", text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=0, column=1)
        CTk.CTkLabel(master=show_save, text="Save", anchor="w", text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=0, column=2)
        labels = ["Composite", "Sticks", "Histogram", "Fluorescence"]
        self.show_table = [self.checkbox(show_save) for it in range(len(labels))]
        self.save_table = [self.checkbox(show_save) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=show_save, text=labels[it], anchor="w", width=100, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=it+1, column=0, padx=(20, 0))
            self.show_table[it].grid(row=it+1, column=1, pady=0, padx=20, sticky="ew")
            self.save_table[it].grid(row=it+1, column=2, pady=0, padx=(20, 20))
        banner = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color="transparent")
        banner.grid(row=1, column=0)
        self.button(banner, image=self.icons["delete_forever"], command=lambda:self.initialize_table(mode="part")).grid(row=0, column=0, padx=(0, 100), sticky="nw")
        self.per_roi = self.checkbox(banner, text="per ROI")
        self.per_roi.grid(row=0, column=1, sticky="nw")

        plot_options = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=App.gray[0])
        plot_options.grid(row=2, column=0, padx=20, pady=20, sticky="nw")
        CTk.CTkLabel(master=plot_options, text="Plot options", width=160, text_color="black", font=CTk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(0, 20))
        self.add_axes_checkbox = self.checkbox(plot_options, text="Add axes on figures")
        self.add_axes_checkbox.grid(row=1, column=0, padx=20)
        CTk.CTkLabel(master=plot_options, text="Number of pixels separating sticks", text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=2, column=0, padx=20, pady=20)
        labels = ["horizontal", "vertical"]
        self.pixelsperstick_spinboxes = [ttk.Spinbox(master=plot_options, from_=0, to=10, width=2, foreground=App.gray[1], background=App.gray[1]) for it in range(2)]
        for it in range(2):
            self.pixelsperstick_spinboxes[it].set(1)
            self.pixelsperstick_spinboxes[it].grid(row=it+3, column=0, padx=20, pady=10)
        self.show_individual_fit_checkbox = self.checkbox(self.tabview.tab("Options"), text="Show individual fit")
        self.show_individual_fit_checkbox.grid(row=3, column=0, pady=20)

        self.variable_table_frame = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color="transparent")
        self.variable_table_frame.grid(row=0, column=1, padx=(40, 20), pady=20, sticky="nw")

        save_ext = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=App.gray[0])
        save_ext.grid(row=2, column=1, padx=(40, 20), pady=20, sticky="nw")
        CTk.CTkLabel(master=save_ext, text="Save extension", text_color="black", font=CTk.CTkFont(weight="bold"), width=100).grid(row=0, column=1, padx=(0, 20))
        labels = ["figures (.fig)", "figures (.tif)", "data (.mat)", "mean values (.xlsx)", "stack (.mp4)"]
        self.extension_table = [self.checkbox(save_ext) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=save_ext, text=labels[it], anchor="w", width=120, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=it+1, column=0, padx=(20, 0))
            self.extension_table[it].grid(row=it+1, column=1, pady=0, padx=(20,0))

## RIGHT FRAME: ADV
        adv_elts = ["Dark", "Binning", "Offset angle", "Rotation", "Disk cone / Calibration data", "Remove background"]
        adv_loc = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        adv = {}
        for loc, elt in zip(adv_loc, adv_elts):
            adv.update({elt: CTk.CTkFrame(master=self.tabview.tab("Advanced"), fg_color=App.gray[0])})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=20, sticky="nw")
            CTk.CTkLabel(master=adv[elt], text=elt, width=230, text_color="black", font=CTk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 10))
        self.dark_switch = CTk.CTkSwitch(master=adv["Dark"], text="", progress_color=App.orange[0], command=self.dark_switch_callback, onvalue="on", offvalue="off", width=50)
        self.dark_switch.grid(row=0, column=0, padx=20, pady=20, sticky="ne")
        self.calculated_dark_value = 480
        self.calculated_dark_label = CTk.CTkLabel(master=adv["Dark"], text="Calculated dark value = " + str(self.calculated_dark_value), text_color="black")
        self.calculated_dark_label.grid(row=1, column=0)
        self.dark_entry = self.entry(adv["Dark"], text="User dark value", text_box="480", row=2, column=0)
        self.dark_entry.configure(state="disabled")

        self.offset_angle_switch = CTk.CTkSwitch(master=adv["Offset angle"], text="", progress_color=App.orange[0], command=self.offset_angle_switch_callback, onvalue="on", offvalue="off", width=50)
        self.offset_angle_switch.grid(row=0, column=0, padx=20, pady=20, sticky="ne")
        self.offset_angle_entry = self.entry(adv["Offset angle"], text="Offset angle (deg)", text_box=str(85), row=1)
        self.offset_angle_entry.configure(state="disabled")

        labels = ["Bin width", "Bin height"]
        self.binning_entries = [self.entry(adv["Binning"], text=label, text_box="1", row=it+1, column=0) for it, label in enumerate(labels)]
        labels = ["Stick (deg)", "Figure (deg)"]
        self.rotation_entries = [self.entry(adv["Rotation"], text=label, text_box="0", row=it+1, column=0) for it, label in enumerate(labels)]
        labels = ["Noise factor", "Noise width", "Noise height", "Noise removal level"]
        vals = [1, 3, 3, 0]
        rows = [1, 2, 3, 5]
        self.remove_background_entries = [self.entry(adv["Remove background"], text=label, text_box=vals[it], row=rows[it], column=0) for it, label in enumerate(labels)]
        self.remove_background_entries[3].configure(state="disabled")
        self.button(adv["Remove background"], text="Click background", image=self.icons["exposure"], command=self.click_background_callback).grid(row=4, column=0)

## RIGHT FRAME: ABOUT
        banner = CTk.CTkFrame(master=self.tabview.tab("About"), fg_color="transparent")
        banner.grid(row=0, column=0, pady=20)
        self.button(banner, text="CHECK WEBSITE FOR UPDATES", image=self.icons["web"], command=lambda:self.openweb(App.url_fresnel)).grid(row=0, column=0, padx=40)
        self.button(banner, text="", image=self.icons["mail"], command=self.send_email).grid(row=0, column=1)
        self.button(banner, text="", image=self.icons["GitHub"], command=lambda:self.openweb(App.url_github)).grid(row=0, column=2, padx=40)
        self.button(banner, text="", image=self.icons["contact_support"], command=lambda:self.openweb(App.url_github + '/blob/master/README.md')).grid(row=0, column=3, padx=20)
        about_textbox = CTk.CTkTextbox(master=self.tabview.tab("About"), width=App.tab_width-30, height=500, font=CTk.CTkFont(weight="bold"), text_color="black", fg_color=App.orange[0])
        about_textbox.grid(row=1, column=0)
        message = "Version: 2.1 (December 1, 2022) created with Python and customtkinter\n\n\n Website: www.fresnel.fr/polarimetry/ \n\n\n Source code available at github.com/cchandre/Polarimetry \n\n\n\n Based on a code originally developed by Sophie Brasselet (Institut Fresnel, CNRS) \n\n\n To report bugs, send an email to\n     manos.mavrakis@cnrs.fr  (Manos Mavrakis, Institut Fresnel, CNRS) \n     cristel.chandre@cnrs.fr  (Cristel Chandre, Institut de Mathématiques de Marseille, CNRS) \n     sophie.brasselet@fresnel.fr  (Sophie Brasselet, Institut Fresnel, CNRS) \n\n\n\n BSD 2-Clause License\n\n Copyright(c) 2021, Cristel Chandre\n All rights reserved. \n\n\n uses Material Design icons by Google"
        about_textbox.insert("0.0", message)
        about_text = about_textbox.get("0.0", "end")
        about_textbox.configure(state="disabled")

        self.tabview.set("Fluorescence")
        self.startup()

    def startup(self):
        info = ["(1) Select a polarimetry method", "(2) Download a file or a folder", "(3) Select a method of analysis", "(4) Select one or several regions of interest", "(5) Click on Analysis"]
        self.info_window = CTk.CTkToplevel(self, fg_color=App.gray[1])
        self.info_window.attributes('-topmost', 'true')
        self.info_window.title('Polarimetry Analysis')
        self.info_window.geometry(App.geometry_info)
        CTk.CTkLabel(self.info_window, text="  Welcome to Polarimetry Analysis", text_color="black", font=CTk.CTkFont(size=20, weight="bold"), image=self.icons['blur_circular'], compound="left").grid(row=0, column=0, padx=30, pady=(10, 0), sticky="w")
        for it, el in enumerate(info):
            CTk.CTkLabel(self.info_window, text=el, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=it+1, column=0, padx=70, pady=(5, 0), sticky="w")
        link = CTk.CTkLabel(self.info_window, text="For more information, visit the GitHub page", text_color="blue", font=CTk.CTkFont(underline=True, weight="bold"), cursor="hand2")
        link.grid(row=6, column=0, padx=30, pady=(10, 0), sticky="w")
        link.bind("<Button-1>", lambda e: webbrowser.open_new_tab(App.url_github))
        ok_button = self.button(master=self.info_window, text="       OK", command=self.on_click)
        ok_button.configure(width=80, height=App.button_size[1])
        ok_button.grid(row=7, column=0, padx=20, pady=10)
        self.initialize_table()
        #self.initialize_variables()
        #self.initialize_diskcone()
        self.thrsh_colormap = 'hot'
        self.disk_data = {'1': '488 nm (no distortions)', '2': '561 nm (no distortions)', '3': '640 nm (no distortions)', '4': '488 nm (16/03/2020 - 12/04/2022)', '5': '561 nm (16/03/2020 - 12/04/2022)', '6': '640 nm (16/03/2020 - 12/04/2022)', '7': '488 nm (13/12/2019 - 15/03/2020)', '8': '561 nm (13/12/2019 - 15/03/2020)', '9': '640 nm (13/12/2019 - 15/03/2020)', '10': '488 nm (before 13/12/2019)', '11': '561 nm (before 13/12/2019)', '12': '640 nm (before 13/12/2019)', '13': 'no distortions (before 12/04/2022)', '14': 'other'}

    def initialize_slider(self, stack=[]):
        if stack:
            self.stack_slider.configure(to=stack.nangle, number_of_steps=stack.nangle)
            self.stack_slider.set(0)
            self.ilow_slider.set(xp.amin(stack.values))
        self.contrast_fluo_slider.set(0.5)
        self.contrast_thrsh_slider.set(0.5)

    def initialize_noise(self):
        self.noise = {'Height': 3, 'Width': 3, 'Factor': 1, 'RemovalLevel': 0}
        self.noise_width.configure(text=self.noise["Width"])
        self.hoise_height.configure(text=self.noise["Height"])
        self.noise_factor.configure(text=self.noise["Factor"])
        self.noise_removallevel.configure(text=self.noise["RemovalLevel"])

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

    def determine_order(self, polquad):
        self.order = {'UL0-UR45-LR90-LL135': [1, 2, 3, 4], 'UL0-UR45-LR135-LL90': [1, 2, 4, 3], 'UL0-UR90-LR45-LL135': [1, 3, 2, 4], 'UL0-UR90-LR135-LL45': [1, 3, 4, 2], 'UL0-UR135-LR45-LL90': [1, 4, 2, 3], 'UL0-UR135-LR90-LL45': [1, 4, 3, 2], 'UL45-UR0-LR90-LL135': [2, 1, 3, 4],  'UL45-UR0-LR135-LL90': [2, 1, 4, 3], 'UL45-UR90-LR0-LL135': [2, 3, 1, 4], 'UL45-UR90-LR135-LL0': [2, 3, 4, 1], 'UL45-UR135-LR0-LL90': [2, 4, 1, 3], 'UL45-UR135-LR90-LL0': [2, 4, 3, 1], 'UL90-UR0-LR45-LL135': [3, 1, 2, 4], 'UL90-UR0-LR135-LL45': [3, 1, 4, 2], 'UL90-UR45-LR0-LL135': [3, 2, 1, 4], 'UL90-UR45-LR135-LL0': [3, 2, 4, 1], 'UL90-UR135-LR0-LL45': [3, 4, 1, 2], 'UL90-UR135-LR45-LL0': [3, 4, 2, 1], 'UL135-UR0-LR45-LL90': [4, 1, 2, 3], 'UL135-UR0-LR90-LL45': [4, 1, 3, 2], 'UL135-UR45-LR0-LL90': [4, 2, 1, 3], 'UL135-UR45-LR90-LL0': [4, 2, 3, 1], 'UL135-UR90-LR0-LL45': [4, 3, 1, 2], 'UL135-UR90-LR45-LL0': [4, 3, 2, 1]}.get(polquad)

    def button(self, master, text="", image=None, command=None):
        width = App.button_size[1] if text == "" else App.button_size[0]
        return CTk.CTkButton(master=master, width=width, height=App.button_size[1], text=text, font=CTk.CTkFont(weight="bold"), text_color="black", anchor="w", image=image, compound="left", bg_color="transparent", fg_color=App.orange[0], hover_color=App.orange[1], command=command)

    def dropdown(self, master, values=[], image=None, row=0, column=0, command=None):
        menu = CTk.CTkFrame(master=master, fg_color=App.gray[0])
        menu.grid(row=row, column=column, padx=17, pady=App.button_pady)
        menu_icon = self.button(menu, text="", image=image)
        menu_icon.configure(hover=False)
        menu_icon.grid(row=0, column=0)
        option_menu = CTk.CTkOptionMenu(master=menu, values=values, width=App.button_size[0]-App.button_size[1], height=App.button_size[1], dynamic_resizing=False, font=CTk.CTkFont(weight="bold"), text_color="black", anchor="w", bg_color="transparent", fg_color=App.orange[0], button_color=App.orange[0], button_hover_color=App.orange[1], dropdown_hover_color=App.orange[1], dropdown_text_color="black", command=command)
        option_menu.grid(row=0, column=1)
        return option_menu

    def checkbox(self, master, text=""):
        return CTk.CTkCheckBox(master=master, onvalue=True, offvalue=False, text=text, width=30, text_color="black", font=CTk.CTkFont(weight="bold"), hover_color=App.orange[1], fg_color=App.orange[0])

    def entry(self, master, text="", text_box="", row=0, column=0):
        banner = CTk.CTkFrame(master=master, fg_color="transparent")
        banner.grid(row=row, column=column, sticky="e")
        CTk.CTkLabel(master=banner, text=text, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20)
        entry = CTk.CTkEntry(master=banner, placeholder_text=text_box, text_color="black", width=50, fg_color="transparent", placeholder_text_color="black")
        entry.grid(row=0, column=1, padx=20, pady=10)
        return entry

    def double_entry(self, master, text="", text_box=("", ""), row=0, column=0):
        banner = CTk.CTkFrame(master=master, fg_color="transparent")
        banner.grid(row=row, column=column, sticky="e")
        CTk.CTkLabel(master=banner, text=text, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20)
        entry = [CTk.CTkEntry(master=banner, placeholder_text=text_box[it], text_color="black", width=50, fg_color="transparent", placeholder_text_color="black") for it in range(2)]
        for it in range(2):
            entry[it].grid(row=0, column=it+1, padx=20, pady=10)
            entry[it].configure(state="disabled")
        return entry

    def on_closing(self):
        self.destroy()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()

    def on_click(self):
        self.info_window.withdraw()

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
            #self.represent_thrsh(self.stack, True, False);

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
        #self.represent_thrsh(self.stack, True, False)

    def reload_button_callback(self):
        self.int_roi = 0
        self.patch = {}
        self.represent_fluo(self.stack, drawnow=True, update=False)
        #self.represent_thrsh(self.stack, True, True)
        self.roi = np.zeros(self.stack.itot.shape)
        self.roi_ilow = np.zeros(self.stack.itot.shape)
        self.mask = np.zeros(self.stack.itot.shape)

    def export_mask(self):
        filename = os.path.basename(self.filename)[0]
        print("Not yet implemented... Stay tuned!")

    def change_colormap(self):
        if self.thrsh_colormap == "hot":
            self.thrsh_colormap == "gray"
        else:
            self.thrsh_colormap == "hot"
        #self.represent_thrsh(self.stack, True, False)

    def no_background(self):
        if self.thrsh_axis.cget("fg_color") == "black":
            self.thrsh_axis.configure(fg_color="transparent")
        else:
            self.thrsh_axis.configure(fg_color="black")
        #self.represent_thrsh(self.stack, False, False)

    def offset_angle_switch_callback(self):
        if self.offset_angle_switch.get() == "on":
            self.offset_angle_entry.configure(state="normal")
        else:
            self.offset_angle_entry.configure(state="disabled")

    def dark_switch_callback(self):
        if self.dark_switch.get() == "on":
            self.dark_entry.configure(state="normal")
        else:
            self.dark_entry.configure(state="disabled")

    def variable_table_switch_callback(self):
        state = "normal" if self.variable_table_switch.get() == "on" else "disabled"
        for entry in self.variable_entries:
            entry.configure(state=state)

    def click_background_callback(self):
        print("Not yet implemented... Stay tuned!")

    def compute_angle(self):
        print("Not yet implemented... Stay tuned!")

    def method_dropdown_callback(self, method):
        self.initialize_table(mode="all")
        self.offset_angle_entry.configure(placeholder_text=str(0))
        self.clear_frame(self.variable_table)
        self.variable_table.configure(fg_color=App.gray[0])
        CTk.CTkLabel(master=self.variable_table_frame, text="      Min                   Max", text_color="black", font=CTk.CTkFont(weight="bold"), width=200).grid(row=0, column=0, padx=20, pady=10, sticky="e")
        self.variable_table_switch = CTk.CTkSwitch(master=self.variable_table_frame, text="", progress_color=App.orange[0], command=self.variable_table_switch_callback, onvalue="on", offvalue="off", width=50)
        self.variable_table_switch.grid(row=0, column=0, padx=(10, 40), sticky="w")
        if method in ["1PF", "4POLAR 2D"]:
            self.offset_angle_entry.configure(placeholder_text=str(85))
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
        for it, (var, val) in enumerate(zip(variables, vals)):
            self.variable_entries += self.double_entry(self.variable_table_frame, text=var, text_box=val, row=it+1)

    def select_file(self):
        filetypes = [("Tiff files", "*.tiff"), ("Tiff files", "*.tif")]
        filename = fd.askopenfilename(title='Select a file', initialdir='/', filetypes=filetypes)
        dataset = Image.open(filename)
        h, w = np.shape(dataset)
        stack_vals = np.zeros((h, w, dataset.n_frames), dtype=np.float64)
        for i in range(dataset.n_frames):
           dataset.seek(i)
           stack_vals[:, :, i] = np.array(dataset)
        dict = {'values': stack_vals, 'height': h, 'width': w, 'nangle': dataset.n_frames, 'mode': dataset.mode, 'display': "{:.0f}"}
        self.stack = Stack()
        for key in dict:
            setattr(self.stack, key, dict[key])
        self.userdarkvalue = 480
        if self.stack.mode == "I":
            self.stack.display = ":.2f"
            self.userdarkvalue = xp.amin(self.stack.values)
        if self.stack.nangle >= 2:
            self.stack_slider.configure(to=dataset.n_frames)
        else:
            self.stack_slider.configure(state="disabled")
        self.ilow_slider.configure(from_=np.amin(self.stack.values), to=np.amax(self.stack.values))
        self.ilow_slider.set(np.amin(self.stack.values))
        self.ilow_slider_label.configure(text=self.stack.display.format(np.amin(self.stack.values)))
        self.filename_label.configure(text=os.path.basename(filename).split('.')[0])
        self.folder = os.path.dirname(filename)
        self.stack = self.define_itot(self.stack)
        self.represent_fluo(self.stack, drawnow=True, update=False)

    def select_folder(self):
        self.folder = fd.askdirectory(title='Select a directory', initialdir='/')

    def tool_dropdown_callback(self, method):
        self.advance_file = True if method.endswith('(auto)') else False
        if method.startswith('Mask'):
            self.ilow_slider.set(np.amin(self.stack.itot))
            self.mask_folder = self.folder
            #self.represent_thrsh(self.stack, False, False)

    def stack_slider_callback(self, value):
        self.stack_slider_label.configure(text=int(value))
        if value == 0:
            self.stack_slider_label.configure(text="T")
        if self.method_dropdown.get() in ['4POLAR 2D','4POLAR 3D']:
            labels = ['T', 0, 45, 90, 135]
            self.stack_slider_label.configure(text=labels[int(value)])
        if hasattr(self, 'stack'):
            self.represent_fluo(self.stack)

    def ilow_slider_callback(self, value):
        self.ilow_slider_label.configure(text=int(value))

    def represent_fluo(self, stack, drawnow=False, update=True):
        if not drawnow:
            xlim_fluo = self.fluo_axis.get_xlim()
            ylim_fluo = self.fluo_axis.get_ylim()
        if self.stack_slider.get() == 0:
            field = (stack.itot - np.amin(stack.itot)) / (np.amax(stack.itot) - np.amin(stack.itot))
        elif self.stack_slider.get() <= self.stack.nangle:
            field = (stack.values[:, :, int(self.stack_slider.get())-1] - np.amin(stack.values)) / (np.amax(stack.values) - np.amin(stack.values))
        field = exposure.adjust_gamma(field, self.contrast_fluo_slider.get())
        field = ndimage.rotate(field, self.rotation_entries[1].get())
        if update:
            self.fluo_im.set_data(field)
        else:
            self.fluo_im = self.fluo_axis.imshow(field, cmap=mpl.colormaps["gray"], extent=[0, 1, 0, 1])
        if not drawnow:
            self.fluo_axis.set_xlim(xlim_fluo)
            self.fluo_axis.set_ylim(ylim_fluo)
        self.fluo_fig.canvas.draw()
        #if self.int_roi and hasattr(self.patch, "XData"):
        #    for it in range(self.int_roi):
        #        prot = self.fluo_axis.add_patch('XData', self.patch["XData"][it], 'YData', self.patch["YData"][it])
        #        rotate(prot, [0 0 -1], self.FigureRotationEditField.Value, [self.stack.width / 2, self.stack.height / 2, 0])
        #        htext = self.fluo_axis.text(self.patch["XData"][it][0], self.patch["YData"][it][0], str(it), fontsize=20, color="w")
        #        rotate(htext,[0 0 -1],app.FigureRotationEditField.Value,[app.Stack.Width/2,app.Stack.Height/2,0]);

    def define_itot(self, stack):
        dark = self.compute_dark(stack);
        stack.sumcor = np.sum((stack.values - dark) * (stack.values >= dark), axis=2)
        stack.itot = stack.sumcor
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
        return np.mean(cell[cell != 0])

    def circularmean(self, rho):
        return np.mod(np.angle(xp.mean(np.exp(2j * rho), deg=True)), 360) / 2

class Stack():
    def __init__(self):
        self.values = []
        self.height, self.width, self.nangle = 0, 0, 0
        self.mode = "I"
        self.display = []
        self.itot = []


if __name__ == "__main__":
    app = App()
    app.mainloop()
