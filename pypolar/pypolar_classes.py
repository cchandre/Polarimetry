import tkinter as tk
import customtkinter as CTk
import tksheet
import pathlib
import os
import sys
import pickle
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import cv2
from skimage import exposure
from scipy.ndimage import rotate
from scipy.signal import convolve2d
from scipy.linalg import norm
from scipy.optimize import linear_sum_assignment
from PIL import Image, ImageTk
from tkinter import filedialog as fd
from tkinter.messagebox import showerror
from scipy.io import loadmat
import colorcet as cc
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backend_bases import NavigationToolbar2, _Mode, MouseEvent
from typing import Callable, List, Tuple, Union
import time

tab_width, tab_height = 810, 830
button_size = (160, 40)
orange = ("#FF7F4F", "#ffb295")
text_color = "black"
red = ("#B54D42", "#d5928b")
green = ("#ADD1AD", "#cee3ce")
gray = ("#7F7F7F", "#A6A6A6")

## PyPOLAR USEFUL FUNCTIONS

geometry_info = lambda dim: f"{dim[0]}x{dim[1]}+400+300"

def adjust(field:np.ndarray, contrast:float, vmin:float, vmax:float) -> np.ndarray:
    amount = 0.8
    blur = cv2.GaussianBlur(field, (5, 5), 1)
    sharpened = cv2.addWeighted(field, 1 + amount, blur, -amount, 0)
    sharpened = np.maximum(sharpened, vmin)
    sharpened = exposure.adjust_gamma((sharpened - vmin) / vmax, contrast) * vmax
    return sharpened

def circularmean(rho:np.ndarray) -> float:
    return np.mod(np.angle(np.mean(np.exp(2j * np.deg2rad(rho))), deg=True), 360) / 2

def wrapto180(rho:np.ndarray) -> np.ndarray:
    return np.angle(np.exp(1j * np.deg2rad(rho)), deg=True)

def angle_edge(edge:np.ndarray) -> Tuple[float, np.ndarray]:
    tangent = np.diff(edge, axis=0, append=edge[-1, :].reshape((1, 2)))
    norm_t = norm(tangent, axis=1)[:, np.newaxis]
    tangent = np.divide(tangent, norm_t, where=np.all((norm_t!=0, np.isfinite(norm_t)), axis=0))
    angle = np.mod(2 * np.rad2deg(np.arctan2(-tangent[:, 1], tangent[:, 0])), 360) / 2
    normal = np.einsum("ij,jk->ik", tangent, np.array([[0, -1], [1, 0]]))
    return angle, normal

def find_matches(a:np.ndarray, b:np.ndarray, tol:float=10) -> Tuple[np.ndarray, np.ndarray]:
    a_, b_ = (a, b) if len(b) >= len(a) else (b, a)
    cost = np.linalg.norm(a_[:, np.newaxis, :] - b_, axis=2)
    indices = linear_sum_assignment(cost)[1]
    a_, b_ = (a, b[indices]) if len(b) >= len(a) else (a[indices], b)
    dist = np.linalg.norm(a_ - b_, axis=1)
    return a_[dist <= tol], b_[dist <= tol]

## PyPOLAR WIDGETS

class Button(CTk.CTkButton):
    def __init__(self, master, text:str=None, image:CTk.CTkImage=None, width:int=button_size[0], height:int=button_size[1], anchor:str="w", **kwargs) -> None:
        super().__init__(master, text=text, image=image, width=width, height=height, anchor=anchor, compound=tk.LEFT, **kwargs)
        if text is None:
            self.configure(width=height)

    def bind(self, sequence=None, command=None, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)
        if self._text_label:
            self._text_label.bind(sequence, command, add=True)
        if self._image_label:
            self._image_label.bind(sequence, command, add=True)

class CheckBox(CTk.CTkCheckBox):
    def __init__(self, master, text:str=None, command:Callable=None, **kwargs) -> None:
        super().__init__(master, text=text, command=command, onvalue=True, offvalue=False, width=30, **kwargs)

class Entry(CTk.CTkFrame):
    def __init__(self, master, text:str=None, textvariable:tk.StringVar=None, state:str="normal", row:int=0, column:int=0, padx:Union[int, Tuple[int, int]]=(10, 30), pady:Union[int, Tuple[int, int]]=5, sticky:str="e", fg_color:str=gray[0], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.configure(fg_color=fg_color)
        self.grid(row=row, column=column, sticky=sticky)
        if text is not None:
            CTk.CTkLabel(self, text=text).grid(row=0, column=0, padx=(20, 10))
        self.entry = CTk.CTkEntry(self, textvariable=textvariable, width=50, justify="center", state=state)
        self.entry.grid(row=0, column=1, padx=padx, pady=pady)

    def get(self) -> int:
        return int(self.entry.get())
        
    def set_state(self, state:str) -> None:
        self.entry.configure(state=state)

    def bind(self, *args, **kwargs):
        return self.entry.bind(*args, **kwargs)

class DropDown(CTk.CTkFrame):
    def __init__(self, master, values:List[str]=[], image:CTk.CTkImage=None, command:Callable=None, variable:tk.StringVar=None, state:str="normal", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=gray[0])
        self.pack(padx=20, pady=20)
        self.icon = Button(self, image=image)
        self.icon.configure(hover=False)
        self.icon.pack(side=tk.LEFT)
        self.option_menu = CTk.CTkOptionMenu(self, values=values, width=button_size[0]-button_size[1], height=button_size[1], dynamic_resizing=False, command=command, variable=variable, state=state)
        self.option_menu.pack(side=tk.LEFT)

    def set_state(self, state:str) -> None:
        self.option_menu.configure(state=state)

    def set_values(self, values:List[str]) -> None:
        self.option_menu.configure(values=values)
    
    def get_menu(self) -> CTk.CTkOptionMenu:
        return self.option_menu
    
    def get_icon(self) -> Button:
        return self.icon
    
    def bind(self, *args, **kwargs):
        return self.option_menu.bind(*args, **kwargs)

class SpinBox(CTk.CTkFrame):
    def __init__(self, master, from_:int=1, to_:int=20, step_size:int=1, textvariable:tk.StringVar=None, command:Callable=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        width, updown_size = 40, 8
        self.from_, self.to_, self.step_size = from_, to_, step_size
        self.command = command
        self.configure(fg_color=gray[1]) 
        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.subtract_button = CTk.CTkButton(self, text=u"\u25BC", width=updown_size, height=updown_size, command=self.subtract_button_callback)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)
        self.entry = CTk.CTkEntry(self, width=width-(2*updown_size), height=updown_size, border_width=0, justify="center", textvariable=textvariable)
        self.entry.grid(row=0, column=1, columnspan=1, padx=0, pady=0, sticky="ew")
        self.add_button = CTk.CTkButton(self, text=u"\u25B2", width=updown_size, height=updown_size, command=self.add_button_callback)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)
        if textvariable is None:
            self.entry.insert(0, from_)

    def add_button_callback(self) -> None:
        value = int(self.entry.get()) + self.step_size
        value = value if value <= self.to_ else self.to_
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        if self.command is not None:
            self.command()

    def subtract_button_callback(self) -> None:
        value = int(self.entry.get()) - self.step_size
        value = value if value >= self.from_ else self.from_
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        if self.command is not None:
            self.command()
        
    def bind(self, event:tk.Event, command:Callable) -> None:
        self.entry.bind(event, command)

    def get(self) -> int:
        return int(self.entry.get())

    def set(self, value:int) -> None:
        if value <= self.from_:
            value = self.from_
        elif value >= self.to_:
            value = self.to_
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))

class ShowInfo(CTk.CTkToplevel):
    def __init__(self, message:str="", image:CTk.CTkImage=None, button_labels:List[str]=[], geometry:tuple=(300, 150), fontsize:int=13) -> None:
        super().__init__()
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
                if label == "OK":
                    button.configure(command=lambda:self.withdraw())
                button.grid(row=row_, column=_, padx=20, pady=20)
                self.buttons += [button]

    def get_buttons(self) -> List[Button]:
        return self.buttons
    
class TextBox(CTk.CTkTextbox):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.configure(state="disabled")

    def write(self, text:str) -> None:
        self.configure(state="normal")
        self.delete("0.0", "end")
        self.insert("0.0", text)
        self.configure(state="disabled")

## PyPOLAR MAIN CLASSES

class Stack:
    def __init__(self, filename) -> None:
        self.filename = os.path.splitext(filename)[0]
        self.folder = str(pathlib.Path(filename).parent)
        self.name = str(pathlib.Path(filename).stem)
        self.height, self.width, self.nangle = 0, 0, 0
        self.display = "{:.0f}"
        self.values = []
        self.intensity = []

    def get_intensity(self, dark:float=0, bin:List[int]=[1, 1]) -> np.ndarray:
        intensity = np.sum((self.values - dark) * (self.values >= dark), axis=0)
        if sum(bin) != 2:
            return convolve2d(intensity, np.ones(bin), mode="same") / (bin[0] * bin[1])
        else:
            return intensity
        
    def compute_dark(self) -> int:
        SizeCell = 20
        NCellHeight = int(np.floor(self.height / SizeCell))
        NCellWidth = int(np.floor(self.width / SizeCell))
        cropIm = self.values[:, :SizeCell * NCellHeight, :SizeCell * NCellWidth]
        cropIm = np.moveaxis(cropIm, 0, -1)
        ImCG = np.asarray(np.split(np.asarray(np.split(cropIm, NCellWidth, axis=1)), NCellHeight, axis=1))
        mImCG = np.zeros((NCellHeight, NCellWidth))
        for it in range(NCellHeight):
            for jt in range(NCellWidth):
                cell = ImCG[it, jt, :, :, 0]
                mImCG[it, jt] = np.mean(cell[cell != 0])
        IndI, IndJ = np.where(mImCG == np.amin(mImCG))
        cell = ImCG[IndI, IndJ, :, :, :]
        return np.mean(cell[cell != 0])

class DataStack:
    def __init__(self, stack) -> None:
        self.filename = stack.filename
        self.folder = stack.folder
        self.name = stack.name
        self.method = ""
        self.height, self.width, self.nangle = stack.height, stack.width, stack.nangle
        self.display = stack.display
        self.dark = 0
        self.intensity = stack.intensity
        self.field = []
        self.field_fit = []
        self.chi2 = []
        self.rois = []
        self.vars = []
        self.added_vars = []

    def plot_intensity(self, contrast:float, rotation:int=0) -> None:
        ax = plt.gca()
        vmin, vmax = np.amin(self.intensity), np.amax(self.intensity)
        field = adjust(self.intensity, contrast, vmin, vmax)
        if rotation:
            field = rotate(field, rotation, reshape=False, mode="constant", cval=vmin)
        ax.imshow(field, cmap="gray", interpolation="nearest", vmin=vmin, vmax=vmax)

class Variable:
    def __init__(self, datastack) -> None:
        self.indx = 0
        self.name = ""
        self.latex = ""
        self.values = np.nan * np.ones((datastack.height, datastack.width))
        self.type_histo = ["normal"]
        self.colormap = ["jet", "viridis"]

    def imshow(self, vmin:float, vmax:float, colorblind:bool=False, rotation:int=0) -> mpl.image.AxesImage:
        ax = plt.gca()
        field = self.values
        if rotation:
            if self.name == "Rho":
                field = np.mod(2 * (field + rotation), 360) / 2
            field = rotate(field, rotation, reshape=False, order=0, mode="constant")
            field[field == 0] = np.nan
        return ax.imshow(field, vmin=vmin, vmax=vmax, cmap=self.colormap[int(colorblind)], interpolation="nearest")

    def histo(self, mask:np.ndarray, htype:str="normal", vmin:float=0, vmax:float=180, colorblind:bool=False, rotation:float=0) -> None:
        data_vals = self.values[mask * np.isfinite(self.values)]
        vmin_, vmax_ = (0, 90) if htype == "polar3" else (vmin, vmax)
        norm = mpl.colors.Normalize(vmin_, vmax_)
        cmap = self.colormap[int(colorblind)]
        if isinstance(cmap, str):
            cmap = mpl.colormaps[cmap] 
        bins = np.linspace(vmin_, vmax_, 60)
        if htype == "normal":
            ax = plt.gca()
            n, bins, patches = ax.hist(data_vals, bins=bins, linewidth=0.5)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            for bin, patch in zip(bin_centers, patches):
                color = cmap(norm(bin))
                patch.set_facecolor(color)
                patch.set_edgecolor("k")
            ax.set_xlim((vmin_, vmax_))
            ax.set_xlabel(self.latex, fontsize=20)
            text = self.latex + " = " + "{:.2f}".format(np.mean(data_vals)) + " $\pm$ " "{:.2f}".format(np.std(data_vals))
            ax.annotate(text, xy=(0.3, 1.05), xycoords="axes fraction", fontsize=14)
        elif htype.startswith("polar"):
            ax = plt.subplot(projection="polar")
            if htype == "polar1":
                if self.name == "Rho":
                    data_vals = np.mod(2 * (data_vals + rotation), 360) / 2
                meandata = circularmean(data_vals)
                std = np.std(wrapto180(2 * (data_vals - meandata)) / 2)
            elif htype == "polar2":
                ax.set_theta_zero_location("N")
                ax.set_theta_direction(-1)
                meandata = np.mean(data_vals)
                std = np.std(data_vals)
            elif htype == "polar3":
                ax.set_theta_zero_location("E")
                data_vals[data_vals >= 90] = 180 - data_vals[data_vals >= 90]
                meandata = circularmean(data_vals)
                std = np.std(wrapto180(2 * (data_vals - meandata)) / 2)
                norm = mpl.colors.Normalize(0, 180)
            distribution, bin_edges = np.histogram(data_vals, bins=bins, range=(vmin_, vmax_))
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            width = np.deg2rad(bins[1] - bins[0])
            colors = cmap(norm(bins))
            ax.bar(np.deg2rad(bin_centers), distribution, width=width, color=colors, edgecolor="k", linewidth=0.5)
            num = 10**(len(str(np.amax(distribution))) - 2)
            ax.set_rticks(np.floor(np.linspace(0, np.max(distribution), 3) / num) * num)
            ax.set_thetamin(vmin_)
            ax.set_thetamax(vmax_)
            text = self.latex + " = " + "{:.2f}".format(meandata) + " $\pm$ " "{:.2f}".format(std)
            if htype == "polar1":
                ax.annotate(text, xy=(0.3, 0.95), xycoords="axes fraction", fontsize=14)
            else:
                ax.annotate(text, xy=(0.7, 0.95), xycoords="axes fraction", fontsize=14)

class ROI:
    def __init__(self) -> None:
        self.start_point = []
        self.end_point = []
        self.previous_point = []
        self.x = []
        self.y = []
        self.lines = []

class Calibration:

    dict_1pf = {"no distortions": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 0), "488 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 175), "561 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 120), "640 nm (no distortions)": ("Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0", 125), "488 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga0_Pa20_Ta45_Gb-0.1_Pb0_Tb0_Gc-0.1_Pc0_Tc0", 0), "561 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga-0.2_Pa0_Ta0_Gb0.1_Pb0_Tb0_Gc-0.2_Pc0_Tc0", 0), "640 nm (16/03/2020 - 12/04/2022)": ("Disk_Ga-0.2_Pa0_Ta45_Gb0.1_Pb0_Tb45_Gc-0.1_Pc0_Tc0", 0), "488 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb20_Tb45_Gc-0.2_Pc0_Tc0", 0), "561 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.2_Pa0_Ta0_Gb0.2_Pb20_Tb0_Gc-0.2_Pc0_Tc0", 0), "640 nm (13/12/2019 - 15/03/2020)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc-0.2_Pc0_Tc0", 0), "488 nm (before 13/12/2019)": ("Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc0.1_Pc0_Tc0", 0), "561 nm (before 13/12/2019)": ("Disk_Ga0.1_Pa0_Ta45_Gb-0.1_Pb20_Tb0_Gc-0.1_Pc0_Tc0", 0), "640 nm (before 13/12/2019)": ("Disk_Ga-0.1_Pa10_Ta0_Gb0.1_Pb30_Tb0_Gc0.2_Pc0_Tc0", 0), "other": (None, 0)}

    folder_1pf = os.path.join(os.path.dirname(os.path.realpath(__file__)), "diskcones")

    dict_4polar = {"Calib_20221102": ("Calib_20221102", 0), "Calib_20221011": ("Calib_20221011", 0), "other": (None, 0)}

    folder_4polar = os.path.join(os.path.dirname(os.path.realpath(__file__)), "calibration")

    def __init__(self, method:str, label:str=None) -> None:
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

    def display(self, colorblind:bool=False) -> None:
        fig, axs = plt.subplots(1, 2, figsize=(13, 8))
        fig.canvas.manager.set_window_title("Disk Cone: " + self.name)
        fig.patch.set_facecolor("w")
        cmap = cc.m_colorwheel if colorblind else "hsv"
        h = axs[0].imshow(self.RhoPsi[:, :, 0], cmap=cmap, interpolation="nearest", extent=[-1, 1, -1, 1], vmin=0, vmax=180)
        axs[0].set_title("Rho Test")
        ax_divider = make_axes_locatable(axs[0])
        cax = ax_divider.append_axes("right", size="7%", pad="2%")
        fig.colorbar(h, cax=cax)
        cmap = "viridis" if colorblind else "jet"
        h = axs[1].imshow(self.RhoPsi[:, :, 1], cmap=cmap, interpolation="nearest", extent=[-1, 1, -1, 1], vmin=0, vmax=180)
        axs[1].set_title("Psi Test")
        ax_divider = make_axes_locatable(axs[1])
        cax = ax_divider.append_axes("right", size="7%", pad="2%")
        fig.colorbar(h, cax=cax)
        plt.subplots_adjust(wspace=0.4)
        for ax in axs:
            ax.set_xlabel("$B_2$")
            ax.set_ylabel("$A_2$")

    def list(self, method:str) -> str:
        if method == "1PF":
            return [key for key in Calibration.dict_1pf.keys()]
        elif method.startswith("4POLAR"):
            return [key for key in Calibration.dict_4polar.keys()]
        else:
            return " "
    
class NToolbar2PyPOLAR(NavigationToolbar2, tk.Frame):

    folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")

    def __init__(self, canvas, window=None, **kwargs) -> None:
        
        tk.Frame.__init__(self, master=window, borderwidth=2, width=int(canvas.figure.bbox.width), height=50)

        self.canvas = canvas
        self.window = window
        self.toolitems = (
        ('Home', ' reset original view', 'home', 'home'),
        ('Back', ' back to previous view', 'backward', 'back'),
        ('Forward', ' forward to next view', 'forward', 'forward'),
        ('Pan', ' left button pans, right button zooms\n x/y fixes axis, CTRL fixes aspect', 'pan', 'pan'),
        ('Zoom', ' zoom to rectangle\n x/y fixes axis', 'zoom', 'zoom'),
        ('Save', ' save image from tab', 'save', 'save_figure'),)

        self._buttons = {}
        for text, tooltip_text, image_file, callback in self.toolitems:
            im = os.path.join(NToolbar2PyPOLAR.folder, image_file + ".png")
            self._buttons[text] = button = self._Button(text=text, image_file=im, toggle=callback in ["zoom", "pan"], command=getattr(self, callback))
            if tooltip_text is not None:
                ToolTip(button, text=tooltip_text)
        self._label_font = CTk.CTkFont(size=12)

        label = tk.Label(master=self, font=self._label_font, text='\N{NO-BREAK SPACE}\n\N{NO-BREAK SPACE}')
        label.pack(side=tk.RIGHT)
        self.message = tk.StringVar(master=self)
        self._message_label = tk.Label(master=self, font=self._label_font, textvariable=self.message, justify=tk.LEFT, fg=text_color)
        self._message_label.pack(side=tk.RIGHT)
        NavigationToolbar2.__init__(self, canvas)

        self.config(background=gray[1])
        self._message_label.config(background=gray[1])
        for button in self.winfo_children():
            button.config(background=gray[1])
        self.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=0, ipady=0)

    def _update_buttons_checked(self) -> None:
        for text, mode in [('Zoom', _Mode.ZOOM), ('Pan', _Mode.PAN)]:
            if text in self._buttons:
                if self.mode == mode:
                    self._buttons[text].select() 
                else:
                    self._buttons[text].deselect()

    def home(self, *args) -> None:
        super().home(*args)
        self.mode = _Mode.NONE
        self._update_buttons_checked()  
    
    def pan(self, *args) -> None:
        super().pan(*args)
        self._update_buttons_checked()

    def zoom(self, *args) -> None:
        super().zoom(*args)
        self._update_buttons_checked()

    def set_message(self, s:str) -> None:
        self.message.set(s)

    def draw_rubberband(self, event:MouseEvent, x0:int, y0:int, x1:int, y1:int) -> None:
        if self.canvas._rubberband_rect_white:
            self.canvas._tkcanvas.delete(self.canvas._rubberband_rect_white)
        if self.canvas._rubberband_rect_black:
            self.canvas._tkcanvas.delete(self.canvas._rubberband_rect_black)
        height = self.canvas.figure.bbox.height
        y0, y1 = height - y0, height - y1
        self.canvas._rubberband_rect_black = (self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1))
        self.canvas._rubberband_rect_white = (self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, outline='white', dash=(3, 3)))
        
    def remove_rubberband(self) -> None:
        if self.canvas._rubberband_rect_white:
            self.canvas._tkcanvas.delete(self.canvas._rubberband_rect_white)
            self.canvas._rubberband_rect_white = None
        if self.canvas._rubberband_rect_black:
            self.canvas._tkcanvas.delete(self.canvas._rubberband_rect_black)
            self.canvas._rubberband_rect_black = None

    def _set_image_for_button(self, button:Union[tk.Button, tk.Checkbutton]) -> None:
       
        def hex_to_rgb(hex:str) -> List[int]:
            h = hex.lstrip('#')
            return [int(h[_:_+2], 16) for _ in (0, 2, 4)]

        def _recolor_icon(image:Image, fg_color:str) -> Image:
            image_data = np.asarray(image).copy()
            black_mask = (image_data[..., :3] == 0).all(axis=-1)
            image_data[black_mask, :3] = hex_to_rgb(fg_color)
            return Image.fromarray(image_data, mode="RGBA")

        with Image.open(button._image_file) as im:
            size_image = 26
            im = im.convert("RGBA")
            im = _recolor_icon(im, fg_color="#00000")
            image = ImageTk.PhotoImage(im.resize((size_image, size_image)), master=self)
            im = _recolor_icon(im, fg_color=orange[0])
            image_alt = ImageTk.PhotoImage(im.resize((size_image, size_image)), master=self)
            button._ntimage = image
            button._ntimage_alt = image_alt

        image_kwargs = {"image": image}
        if (isinstance(button, tk.Checkbutton) and button.cget("selectcolor") != ""):
            image_kwargs["selectimage"] = image_alt
        
        button.configure(**image_kwargs)
        
    def _Button(self, text:str, image_file:str, toggle:bool, command:Callable) -> Union[tk.Button, tk.Checkbutton]:
        size_button = 30
        if not toggle:
            b = tk.Button(master=self, text=text, command=command, relief="flat", overrelief="flat", highlightthickness=0, height=size_button, width=size_button)
        else:
            var = tk.IntVar(master=self)
            b = tk.Checkbutton(master=self, text=text, command=command, indicatoron=False, variable=var, offrelief="flat", overrelief="flat", height=size_button+2, width=size_button+2)
            b.var = var
        b._image_file = image_file
        if image_file is not None:
            self._set_image_for_button(b)
        else:
            b.configure(font=self._label_font)
        b.configure(borderwidth=0, highlightbackground=gray[1], highlightthickness=0)
        b.pack(side=tk.LEFT, padx=3)
        return b

    def save_figure(self, *args) -> None:
        filetypes = self.canvas.get_supported_filetypes().copy()
        default_filetype = self.canvas.get_default_filetype()
        default_filetype_name = filetypes.pop(default_filetype)
        sorted_filetypes = ([(default_filetype, default_filetype_name)] + sorted(filetypes.items()))
        tk_filetypes = [(name, '*.%s' % ext) for ext, name in sorted_filetypes]
        defaultextension = ''
        initialdir = os.path.expanduser(mpl.rcParams['savefig.directory'])
        initialfile = self.canvas.get_default_filename()
        fname = fd.asksaveasfilename(master=self.canvas.get_tk_widget().master, title=f"Save image from '{self.window.master.master.get()}' tab",filetypes=tk_filetypes, defaultextension=defaultextension, initialdir=initialdir, initialfile=initialfile)
        if fname in ["", ()]:
            return
        if initialdir != "":
            mpl.rcParams['savefig.directory'] = (os.path.dirname(str(fname)))
        try:
            self.canvas.figure.savefig(fname)
        except Exception as e:
            showerror("Error saving file", str(e))

    def set_history_buttons(self) -> None:
        state_map = {True: tk.NORMAL, False: tk.DISABLED}
        can_back = self._nav_stack._pos > 0
        can_forward = self._nav_stack._pos < len(self._nav_stack._elements) - 1
        if "Back" in self._buttons:
            self._buttons['Back']['state'] = state_map[can_back]
        if "Forward" in self._buttons:
            self._buttons['Forward']['state'] = state_map[can_forward]

    def _mouse_event_to_message(self, event:MouseEvent) -> str:
        if event.inaxes and event.inaxes.get_navigate():
            try:
                s = f"(x={int(event.xdata)}, y={int(event.ydata)})"
            except (ValueError, OverflowError):
                pass
            else:
                artists = [a for a in event.inaxes._mouseover_set if a.contains(event)[0] and a.get_visible()]
                if artists:
                    a = mpl.cbook._topmost_artist(artists)
                    if a is not event.inaxes.patch:
                        data = a.get_cursor_data(event)
                        if data is not None:
                            s += f"\nI={int(np.sum(data))}"
                return s
        return ""
    
class ToolTip:
    def __init__(self, widget, *, pad=(5, 3, 5, 3), text:str='widget info', waittime=400, wraplength=250):
        self.waittime = waittime  
        self.wraplength = wraplength
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.onEnter)
        self.widget.bind("<Leave>", self.onLeave)
        self.widget.bind("<ButtonPress>", self.onLeave)
        self.pad = pad
        self.id = None
        self.tw = None

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        def tip_pos_calculator(widget, label, *, tip_delta=(10, 5), pad=(5, 3, 5, 3)):
            w = widget
            s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()
            width, height = (pad[0] + label.winfo_reqwidth() + pad[2], pad[1] + label.winfo_reqheight() + pad[3])
            mouse_x, mouse_y = w.winfo_pointerxy()
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height
            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0
            offscreen = (x_delta, y_delta) != (0, 0)
            if offscreen:
                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width
                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height
            offscreen_again = y1 < 0 
            if offscreen_again:
                y1 = 0
            return x1, y1
        
        pad = self.pad
        widget = self.widget
        self.tw = tk.Toplevel(widget)
        self.tw.wm_overrideredirect(True)
        win = tk.Frame(self.tw, borderwidth=0)
        label_font = CTk.CTkFont(size=12)
        label = tk.Label(win, text=self.text, font=label_font, justify=tk.LEFT, relief=tk.SOLID, borderwidth=0,wraplength=self.wraplength)
        label.grid(padx=(pad[0], pad[2]), pady=(pad[1], pad[3]), sticky=tk.NSEW)
        win.grid()
        x, y = tip_pos_calculator(widget, label)
        self.tw.wm_geometry(f"+{x}+{y}")

    def hide(self):
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None

class ROIManager(CTk.CTkToplevel):
    labels = ["indx", "name", "group"]
    widths = [40, 250, 90]
    button_labels = ["Commit", "Save", "Load", "Delete", "Delete All"]
    tooltips = [" commit the changes made to the labels of ROIs (name, group and select)", " save information on ROIs as a .pyroi file", " load ROIs from a .pyroi file", " permanently deletes ROIs selected in delete column", " permamently deletes all ROIs"]
    manager_size = lambda w, h: f"{w+40}x{h+84}"
    cmax = len(labels)

    def __init__(self, rois:list=[]) -> None:
        super().__init__()
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
        for _, (label, tooltip) in enumerate(zip(ROIManager.button_labels, ROIManager.tooltips)):
            button = Button(bottom_frame, text=label, anchor="center", width=80)
            ToolTip(button, text=tooltip)
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

    def add_elements(self, cmax:int) -> None:
        self.sheet.align_columns(columns=[0, cmax-1], align="center")
        self.sheet.create_checkbox(r="all", c=cmax, checked=True, state="normal", redraw=False, check_function=None, text="")
        self.sheet.create_checkbox(r="all", c=cmax+1, checked=False, state="normal", redraw=False, check_function=None, text="")
        
    def delete(self, rois:list) -> None:
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
    
    def delete_all(self) -> None:
        for _ in range(self.sheet.get_total_rows()):
            self.sheet.delete_row()
        self.sheet.set_options(height=self.sheet_height(20, []))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, [])) + f"+{x}+{y}")

    def get_buttons(self) -> list:
        return self.buttons

    def load(self, initialdir:str="/") -> List[dict]:
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

    def rois2sheet(self, rois:List[dict]):
        for it, roi in enumerate(rois):
            for jt, label in enumerate(self.labels):
                self.sheet.set_cell_data(it, jt, value=roi[label])

    def save(self, rois:List[dict]=[], filename:str="ROIs") -> None:
        if any(rois):
            rois = self.update_rois(rois)
            with open(filename + ".pyroi", "wb") as f:
                pickle.dump(rois, f, protocol=pickle.HIGHEST_PROTOCOL)

    def update_manager(self, rois:List[dict]) -> None:
        self.sheet.set_options(height=self.sheet_height(20, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(ROIManager.manager_size(self.sheet_width, self.sheet_height(20, rois)) + f"+{x}+{y}")
        roi = rois[-1]
        self.sheet.insert_row([roi[label] for label in ROIManager.labels])
        self.sheet.create_checkbox(c=ROIManager.cmax, r=len(rois)-1, checked = True)
        self.sheet.create_checkbox(c=ROIManager.cmax+1, r=len(rois)-1, checked = False)

    def update_rois(self, rois:List[dict]=[]) -> List[dict]:
        if any(rois):
            data = self.sheet.get_sheet_data()
            for _, roi in enumerate(rois):
                roi["name"] = data[_][1]
                roi["group"] = data[_][2]
                roi["select"] = data[_][-2]
            return rois
        return []
    
class TabView(CTk.CTkTabview):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.configure(width=tab_width, height=tab_height, segmented_button_selected_color=orange[0], segmented_button_unselected_color=gray[1], segmented_button_selected_hover_color=orange[1], text_color=text_color, segmented_button_fg_color=gray[0], fg_color=gray[1])
        self.pack(fill=tk.BOTH, expand=True)
        main_tabs = ["Intensity", "Thresholding/Mask"]
        option_tabs = ["Options", "Advanced", "About"]
        self.frame = {}
        for tab in main_tabs:
            self.add(tab)
        for tab in option_tabs:
            self.add(tab)