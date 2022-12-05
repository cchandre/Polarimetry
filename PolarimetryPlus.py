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
import matplotlib as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

CTk.set_default_color_theme("dark-blue")
CTk.set_appearance_mode("dark")

plt.use('TkAgg')

class App(CTk.CTk):

    width_l = 180
    width = 800 + width_l
    height = 800
    width_r = width - width_l
    width_tab = width_r - 40
    height_tab = height - 20
    pady_button = 25

    my_orange = ("#FF7F4F", "#ffb295")
    text_color = "black"
    my_red = ("#B54D42", "#d5928b")
    my_green = ("#ADD1AD", "#cee3ce")
    my_gray = ("#7F7F7F", "#A6A6A6")
    button_size = [160, 40]
    url_github = "https://github.com/cchandre/Polarimetry"
    url_fresnel = "https://www.fresnel.fr/polarimetry"
    email = "cristel.chandre@cnrs.fr"


    def __init__(self):
        super().__init__()

        self.title("Polarimetry Analysis")
        self.geometry(f"{App.width}x{App.height}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(fg_color="#7F7F7F")

        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Icons")
        self.icons = {}
        for file in os.listdir(image_path):
            if file.endswith('.png'):
                self.icons.update({os.path.splitext(file)[0]: CTk.CTkImage(dark_image=Image.open(image_path + "/" + file), size=(30, 30))})

        self.frame_left = CTk.CTkFrame(master=self, width=App.width_l, corner_radius=0, fg_color=App.my_gray[0])
        self.frame_left.grid(row=0, column=0, sticky="nswe")
        self.frame_right = CTk.CTkFrame(master=self, fg_color=App.my_gray[0])
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=0, pady=0)

        self.tabview = CTk.CTkTabview(master=self.frame_right, width=App.width_tab, height=App.height_tab, segmented_button_selected_color=App.my_orange[0], segmented_button_unselected_color=App.my_gray[1], segmented_button_selected_hover_color=App.my_orange[1], text_color="black", segmented_button_fg_color=App.my_gray[0], fg_color=App.my_gray[1])
        self.tabview.grid(row=0, column=0, padx=10, pady=0)
        list_tabs = ["Fluorescence", "Thresholding/Mask", "Options", "Advanced", "About"]
        self.tab = {}
        for tab in list_tabs:
            self.tabview.add(tab)

        self.PolarimetryAnalysisLogo = self.button(self.frame_left, text="POLARIMETRY \n ANALYSIS", image=self.icons['blur_circular'], command=self.on_click_tab)
        self.PolarimetryAnalysisLogo.configure(hover=False, fg_color="transparent", anchor="e")
        self.PolarimetryAnalysisLogo.grid(row=0, column=0, pady=30, padx=17)
        self.DownloadFile = self.button(self.frame_left, text="Download File", command=self.select_file, image=self.icons['download_file'])
        self.DownloadFile.grid(row=2, column=0, pady=App.pady_button, padx=17)
        self.DownloadFolder = self.button(self.frame_left, text="Download Folder", command=self.select_folder, image=self.icons['download_folder'])
        self.DownloadFolder.grid(row=3, column=0, pady=App.pady_button, padx=17)
        self.AddROI = self.button(self.frame_left, text="Add ROI", image=self.icons['roi'])
        self.AddROI.grid(row=5, column=0, pady=App.pady_button, padx=17)
        self.Analysis = self.button(self.frame_left, text="Analysis", image=self.icons['play'])
        self.Analysis.configure(fg_color=App.my_green[0], hover_color=App.my_green[1])
        self.Analysis.grid(row=6, column=0, pady=App.pady_button, padx=17)
        self.CloseFigs = self.button(self.frame_left, text="Close figures", image=self.icons['close'])
        self.CloseFigs.configure(fg_color=App.my_red[0], hover_color=App.my_red[1])
        self.CloseFigs.grid(row=7, column=0, pady=App.pady_button, padx=17)

        self.PolarimetryMethod = self.dropdown(self.frame_left, values=["1PF", "CARS", "SRS", "SHG", "2PF", "4POLAR 2D", "4POLAR 3D"], image=self.icons["microscope"], row=1, column=0)

        self.DropDownTool = self.dropdown(self.frame_left, values=["Thresholding (manual)", "Thresholding (auto)", "Mask (manual)", "Mask (auto)"], image=self.icons["build"], row=4, column=0)

        banner = CTk.CTkFrame(master=self.tabview.tab("Fluorescence"), fg_color="transparent")
        banner.grid(row=0, column=1)
        self.contrast_fluo_slider = CTk.CTkSlider(master=banner, from_=0, to=1, orientation="vertical", command=self.contrast_fluo_slider_callback, button_color=App.my_orange[0], button_hover_color=App.my_orange[1])
        self.contrast_fluo_slider.grid(row=1, column=0)

        self.stack_slider = CTk.CTkSlider(master=self.tabview.tab("Fluorescence"), from_=0, to=18, number_of_steps=18, command=self.stack_slider_callback, button_color=App.my_orange[0], button_hover_color=App.my_orange[1])
        self.stack_slider.set(0)
        self.stack_slider.place(relx=0.6, rely=0.93, anchor="w")
        self.stack_slider_label = CTk.CTkLabel(master=self.tabview.tab("Fluorescence"), width=20, height=10, fg_color="transparent", text="T", text_color="black", font=CTk.CTkFont(weight="bold"))
        self.stack_slider_label.place(relx=0.6, rely=0.96, anchor="w")

        self.filename_label = CTk.CTkLabel(master=self.tabview.tab("Fluorescence"), width=100, height=10, fg_color="transparent", text="")
        self.filename_label.place(relx=0.1, rely=0.96)

        self.contrast_thrsh_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, orientation="vertical", command=self.contrast_thrsh_slider_callback, button_color=App.my_orange[0], button_hover_color=App.my_orange[1])
        self.contrast_thrsh_slider.place(relx=1, rely=0, anchor="ne")

        self.ilow_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, command=self.ilow_slider_callback, button_color=App.my_orange[0], button_hover_color=App.my_orange[1])
        self.ilow_slider.set(0)
        self.ilow_slider.place(relx=0.2, rely=0.93, anchor="w")
        self.ilow_slider_label = CTk.CTkLabel(master=self.tabview.tab("Thresholding/Mask"), width=20, height=10, fg_color="transparent", text=0, text_color="black", font=CTk.CTkFont(weight="bold"))
        self.ilow_slider_label.place(relx=0.2, rely=0.96, anchor="w")

        self.transparency_slider = CTk.CTkSlider(master=self.tabview.tab("Thresholding/Mask"), from_=0, to=1, button_color=App.my_orange[0], button_hover_color=App.my_orange[1])
        self.transparency_slider.place(relx=0.6, rely=0.93, anchor="w")

        self.fluo_axis = CTk.CTkLabel(master=self.tabview.tab("Fluorescence"), text="")
        self.fluo_axis.grid(row=0, column=0, padx=0, pady=0)

        show_save = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=App.my_gray[0], width=400)
        show_save.grid(row=0, column=0, padx=(20, 20), pady=20)
        CTk.CTkLabel(master=show_save, text="Show", anchor="w", text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=0, column=1)
        CTk.CTkLabel(master=show_save, text="Save", anchor="w", text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=0, column=2)
        labels = ["Composite", "Sticks", "Histogram", "Fluorescence"]
        self.Show = [self.checkbox(show_save) for it in range(len(labels))]
        self.Save = [self.checkbox(show_save) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=show_save, text=labels[it], anchor="w", width=100, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=it+1, column=0, padx=(20, 0))
            self.Show[it].grid(row=it+1, column=1, pady=0, padx=20, sticky="ew")
            self.Save[it].grid(row=it+1, column=2, pady=0, padx=(20, 20))

        save_ext = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=App.my_gray[0])
        save_ext.grid(row=1, column=1, padx=(40, 20), pady=20)
        CTk.CTkLabel(master=save_ext, text="Save extension", text_color="black", font=CTk.CTkFont(weight="bold"), width=100).grid(row=0, column=1, padx=(0, 20))
        labels = ["figures (.fig)", "figures (.tif)", "data (.mat)", "mean values (.xlsx)", "stack (.mp4)"]
        self.Extension = [self.checkbox(save_ext) for it in range(len(labels))]
        for it in range(len(labels)):
            CTk.CTkLabel(master=save_ext, text=labels[it], anchor="w", width=120, text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=it+1, column=0, padx=(20, 0))
            self.Extension[it].grid(row=it+1, column=1, pady=0, padx=(20,0))

        plot_options = CTk.CTkFrame(master=self.tabview.tab("Options"), fg_color=App.my_gray[0])
        plot_options.grid(row=1, column=0, padx=20, pady=20)
        CTk.CTkLabel(master=plot_options, text="Plot options", width=160, text_color="black", font=CTk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(0, 20))
        self.axes = self.checkbox(plot_options, text="Add axes on figures")
        self.axes.grid(row=1, column=0, padx=20)
        CTk.CTkLabel(master=plot_options, text="Number of pixels separating sticks", text_color="black", font=CTk.CTkFont(weight="bold")).grid(row=2, column=0, padx=20, pady=20)
        labels = ["horizontal", "vertical"]
        self.pixelsperstick = [ttk.Spinbox(master=plot_options, from_=0, to=10, width=2, foreground=App.my_gray[1], background=App.my_gray[1]) for it in range(2)]
        for it in range(2):
            self.pixelsperstick[it].set(1)
            self.pixelsperstick[it].grid(row=it+3, column=0, padx=20, pady=10)
        self.show_individual_fit = self.checkbox(self.tabview.tab("Options"), text="Show individual fit")
        self.show_individual_fit.grid(row=2, column=0, pady=20)

        adv_elts = ["Dark", "Binning", "Offset angle", "Rotation", "Disk cone / Calibration data", "Remove background"]
        adv_loc = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        adv = {}
        for loc, elt in zip(adv_loc, adv_elts):
            adv.update({elt: CTk.CTkFrame(master=self.tabview.tab("Advanced"), fg_color=App.my_gray[0])})
            adv[elt].grid(row=loc[0], column=loc[1], padx=20, pady=20)
            CTk.CTkLabel(master=adv[elt], text=elt, width=160, text_color="black", font=CTk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(0, 20))
        self.calculated_dark_checkbox = self.checkbox(adv["Dark"], text="Calculated dark value")
        self.calculated_dark_checkbox.grid(row=1, column=0)

        banner = CTk.CTkFrame(master=self.tabview.tab("About"), fg_color="transparent")
        banner.grid(row=0, column=0, pady=20)
        self.button(banner, text="CHECK WEBSITE FOR UPDATES", image=self.icons["web"], command=lambda:self.openweb(App.url_fresnel)).grid(row=0, column=0, padx=40)
        self.button(banner, text="", image=self.icons["mail"], command=self.send_email).grid(row=0, column=1)
        self.button(banner, text="", image=self.icons["GitHub"], command=lambda:self.openweb(App.url_github)).grid(row=0, column=2, padx=40)
        self.button(banner, text="", image=self.icons["contact_support"], command=lambda:self.openweb(App.url_github + '/blob/master/README.md')).grid(row=0, column=3, padx=20)

        about_textbox = CTk.CTkTextbox(master=self.tabview.tab("About"), width=App.width_tab-30, height=500, font=CTk.CTkFont(weight="bold"), text_color="black", fg_color=App.my_orange[0])
        about_textbox.grid(row=1, column=0)
        message = '''Version: 2.1 (December 1, 2022) created with Python and customtkinter


Website: www.fresnel.fr/polarimetry/


Source code available at github.com/cchandre/Polarimetry




Based on a code originally developed by Sophie Brasselet (Institut Fresnel, CNRS)


To report bugs, send an email to
    manos.mavrakis@cnrs.fr  (Manos Mavrakis, Institut Fresnel, CNRS)
    cristel.chandre@cnrs.fr  (Cristel Chandre, Institut de Mathématiques de Marseille, CNRS)
    sophie.brasselet@fresnel.fr  (Sophie Brasselet, Institut Fresnel, CNRS)



BSD 2-Clause License

Copyright(c) 2021, Cristel Chandre
All rights reserved.


uses Material Design icons by Google'''
        about_textbox.insert("0.0", message)
        about_text = about_textbox.get("0.0", "end")
        about_textbox.configure(state="disabled")

        self.tabview.set("Fluorescence")
        self.startup()

    def startup(self):
        info = ["(1) Select a polarimetry method", "(2) Download a file or a folder", "(3) Select a method of analysis", "(4) Select one or several regions of interest", "(5) Click on Analysis"]
        self.info_window = CTk.CTkToplevel(self, fg_color=App.my_gray[1])
        self.info_window.title('Polarimetry Analysis')
        self.info_window.geometry("400x300")
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
        #self.Clickbackground.deselect()
        self.ThrshldColormap = 'hot'
        self.DiskData = ['488 nm (no distortions)', '561 nm (no distortions)', '640 nm (no distortions)', '488 nm (16/03/2020 - 12/04/2022)', '561 nm (16/03/2020 - 12/04/2022)', '640 nm (16/03/2020 - 12/04/2022)', '488 nm (13/12/2019 - 15/03/2020)', '561 nm (13/12/2019 - 15/03/2020)', '640 nm (13/12/2019 - 15/03/2020)', '488 nm (before 13/12/2019)', '561 nm (before 13/12/2019)', '640 nm (before 13/12/2019)', 'no distortions (before 12/04/2022)', 'other']
        self.DiskDataLabels = np.array2string(np.arange(len(self.DiskData)))
        self.SelectDiskCone = {'Items': self.DiskData, 'ItemsData': self.DiskDataLabels}

    def initialize_slider(self, stack=[]):
        if stack:
            self.stack_slider.configure(to=stack.nangle, number_of_steps=stack.nangle)
        self.contrast_fluo_slider.set(1)
        self.contrast_thrsh_slider.set(1)
        self.ilow_slider.set(0)

    def initialize_noise(self):
        self.Noise = {'Height': 3, 'Width': 3, 'Factor': 1, 'RemovalLevel': 0}
        self.NoiseWidth.configure(text=self.Noise.Width)
        self.NoiseHeight.configure(text=self.Noise.Height)
        self.NoiseFactor.configure(text=self.Noise.Factor)
        self.NoiseRemovallevel.configure(text=self.Noise.RemovalLevel)

    def initialize_table(self, mode='all'):
        for show, save in zip(self.Show, self.Save):
            show.deselect()
            save.deselect()
        #self.Variable[:].set(False)
        if mode == 'part':
            self.Extension[1].deselect()
        else:
            for ext in self.Extension:
                ext.deselect()
        if self.PolarimetryMethod.get().startswith("4POLAR"):
            self.show_individual_fit.deselect()
            self.show_individual_fit.configure(state=tk.DISABLED)
        else:
            self.show_individual_fit.configure(state=tk.NORMAL)
            self.show_individual_fit.deselect()

    def determine_order(self, polquad):
        self.order = {'UL0-UR45-LR90-LL135': [1, 2, 3, 4], 'UL0-UR45-LR135-LL90': [1, 2, 4, 3], 'UL0-UR90-LR45-LL135': [1, 3, 2, 4], 'UL0-UR90-LR135-LL45': [1, 3, 4, 2], 'UL0-UR135-LR45-LL90': [1, 4, 2, 3], 'UL0-UR135-LR90-LL45': [1, 4, 3, 2], 'UL45-UR0-LR90-LL135': [2, 1, 3, 4],  'UL45-UR0-LR135-LL90': [2, 1, 4, 3], 'UL45-UR90-LR0-LL135': [2, 3, 1, 4], 'UL45-UR90-LR135-LL0': [2, 3, 4, 1], 'UL45-UR135-LR0-LL90': [2, 4, 1, 3], 'UL45-UR135-LR90-LL0': [2, 4, 3, 1], 'UL90-UR0-LR45-LL135': [3, 1, 2, 4], 'UL90-UR0-LR135-LL45': [3, 1, 4, 2], 'UL90-UR45-LR0-LL135': [3, 2, 1, 4], 'UL90-UR45-LR135-LL0': [3, 2, 4, 1], 'UL90-UR135-LR0-LL45': [3, 4, 1, 2], 'UL90-UR135-LR45-LL0': [3, 4, 2, 1], 'UL135-UR0-LR45-LL90': [4, 1, 2, 3], 'UL135-UR0-LR90-LL45': [4, 1, 3, 2], 'UL135-UR45-LR0-LL90': [4, 2, 1, 3], 'UL135-UR45-LR90-LL0': [4, 2, 3, 1], 'UL135-UR90-LR0-LL45': [4, 3, 1, 2], 'UL135-UR90-LR45-LL0': [4, 3, 2, 1]}.get(polquad)

    def button(self, master, text="", image=None, command=None):
        width = App.button_size[1] if text == "" else App.button_size[0]
        return CTk.CTkButton(master=master, width=width, height=App.button_size[1], text=text, font=CTk.CTkFont(weight="bold"), text_color="black", anchor="w", image=image, compound="left", bg_color="transparent", fg_color=App.my_orange[0], hover_color=App.my_orange[1], command=command)

    def dropdown(self, master, values=[], image=None, row=0, column=0):
        menu = CTk.CTkFrame(master=master, fg_color=App.my_gray[0])
        menu.grid(row=row, column=column, padx=17, pady=App.pady_button)
        menu_icon = self.button(menu, text="", image=image)
        menu_icon.configure(hover=False)
        menu_icon.grid(row=0, column=0)
        option_menu = CTk.CTkOptionMenu(master=menu, values=values, width=App.button_size[0]-App.button_size[1], height=App.button_size[1], dynamic_resizing=False, font=CTk.CTkFont(weight="bold"), text_color="black", anchor="w", bg_color="transparent", fg_color=App.my_orange[0], button_color=App.my_orange[0], button_hover_color=App.my_orange[1], dropdown_hover_color=App.my_orange[1], dropdown_text_color="black")
        option_menu.grid(row=0, column=1)
        return option_menu

    def checkbox(self, master, text=""):
        return CTk.CTkCheckBox(master=master, onvalue=True, offvalue=False, text=text, width=30, text_color="black", font=CTk.CTkFont(weight="bold"), hover_color=App.my_orange[1], fg_color=App.my_orange[0])

    def on_closing(self, event=0):
        self.destroy()

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
            #self.represent_thrsh(self.itot, True, False);

    def contrast_fluo_slider_callback(self, value):
        if value <= 0.001:
            self.contrast_fluo_slider.set(0.001)
            #self.represent_fluo(self.itot, False)

    def select_file(self):
        filetypes = [("Tiff files", "*.tiff"), ("Tiff files", "*.tif")]
        filename = fd.askopenfilename(title='Select a file', initialdir='/', filetypes=filetypes)
        dataset = Image.open(filename)
        h, w = np.shape(dataset)
        stack_vals = np.zeros((h, w, dataset.n_frames), dtype=np.float64)
        for i in range(dataset.n_frames):
           dataset.seek(i)
           stack_vals[:, :, i] = np.array(dataset)
        self.stack = {'values': stack_vals, 'height': h, 'width': w, 'nangle': dataset.n_frames, 'mode': dataset.mode, 'display': "{:.0f}"}
        self.userdarkvalue = 480
        if self.stack.mode == "I":
            self.stack.display = ':.2f'
            self.userdarkvalue = xp.amin(stack.values)
        if self.stack.nangle >= 2:
            self.stack_slider.configure(to=dataset.n_frames)
        else:
            self.stack_slider.configure(state="disabled")
        self.ilow_slider.configure(to=np.amax(self.stack.values))
        self.ilow_slider.set(np.amax(self.stack.values))
        self.ilow_slider_label.configure(text=self.stack.display.format(np.amax(self.stack.values)))
        self.filename_label.configure(text=os.path.basename(filename))
        app.sumcor, self.itot = self.define_itot(self.stack);

    def select_folder(self):
        foldername = fd.askdirectory(title='Select a directory', initialdir='/')
        showinfo(title='Selected Folder', message=foldername)

    def stack_slider_callback(self, value):
        self.stack_slider_label.configure(text=int(value))
        if value == 0:
            self.stack_slider_label.configure(text="T")
        if self.PolarimetryMethod.get() in ['4POLAR 2D','4POLAR 3D']:
            labels = ['T', 0, 45, 90, 135]
            self.stack_slider_label.configure(text=labels[int(value)])

    def ilow_slider_callback(self, value):
        self.ilow_slider_label.configure(text=int(value))

    def define_itot(self, stack):
        dark = self.compute_dark(stack);
        sumcor = xp.sum((stack.values - dark) * (stack.values >= dark), axis=2)
        itot = sumcor
        return sumcor, itot

    def compute_dark(self, stack):
        SizeCell = 20;
        NCellHeight = np.floor(stack.height / SizeCell);
        NCellWidth = np.floor(stack.width / SizeCell);
        Ncol = SizeCell * np.ones(NCellWidth)
        Nrow = SizeCell * np.ones(NCellHeight)
        cropIm = stack.values[:SizeCell * NCellHeight, :SizeCell * NCellWidth, :]
        ImCG = np.split(cropIm, (Nrow, Ncol, stack.nangle))
        mImCG = xp.zeros(NCellHeight, NCellWidth);
        for it in range(NCellHeight):
            for jt in range(NCellWidth):
                CellInd = ImCG[it, jt][:, :, 1]
                mImCG[it, jt] = np.mean(CellInd[CellInd])
        val = np.amin(mImCG);
        IndI, IndJ = np.argmin(mImCG)
        CellInd = ImCG[IndI, IndJ]
        return xp.mean(CellInd[CellInd])

    def circularmean(self, rho):
        return np.mod(np.angle(xp.mean(np.exp(2j * rho), deg=True)), 360) / 2

if __name__ == "__main__":
    app = App()
    app.mainloop()
