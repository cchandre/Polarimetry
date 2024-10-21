import tkinter as tk
import customtkinter as CTk
import tksheet
from pathlib import Path
import sys
import pickle
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import cv2
from skimage.exposure import adjust_gamma
from scipy.ndimage import rotate
from scipy.signal import convolve2d
from scipy.linalg import norm
from scipy.optimize import linear_sum_assignment
from PIL import Image, ImageTk
from tkinter import filedialog as fd
from tkinter.messagebox import showerror
from scipy.io import loadmat
from colorcet import m_colorwheel
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_pdf
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backend_bases import NavigationToolbar2, _Mode, MouseEvent
from typing import Callable, List, Tuple, Union
from generate_json import font_macosx, font_windows, orange, red, gray, text_color

button_size = (160, 40)

## PyPOLAR USEFUL FUNCTIONS

geometry_info = lambda dim: f'{dim[0]}x{dim[1]}+400+300'

def adjust(field:np.ndarray, contrast:float, vmin:float, vmax:float, sharpen:bool=True) -> np.ndarray:
    if sharpen:
        amount = 0.8
        blur = cv2.GaussianBlur(field, (5, 5), 1)
        sharpened = cv2.addWeighted(field, 1 + amount, blur, -amount, 0)
        sharpened = np.maximum(sharpened, vmin)
    else:
        sharpened = field.copy()
    return adjust_gamma((sharpened - vmin) / (vmax - vmin), contrast) * (vmax - vmin) + vmin

def angle_edge(edge:np.ndarray) -> Tuple[float, np.ndarray]:
    tangent = np.diff(edge, axis=0, append=edge[-1, :].reshape((1, 2)))
    norm_t = norm(tangent, axis=1)[:, np.newaxis]
    tangent = np.divide(tangent, norm_t, where=np.all((norm_t!=0, np.isfinite(norm_t)), axis=0))
    angle = np.mod(2 * np.rad2deg(np.arctan2(-tangent[:, 1], tangent[:, 0])), 360) / 2
    normal = np.einsum('ij,jk->ik', tangent, np.array([[0, -1], [1, 0]]))
    return angle, normal

def circularmean(rho:np.ndarray) -> float:
    return np.mod(np.angle(np.mean(np.exp(2j * np.deg2rad(rho))), deg=True), 360) / 2

def divide_ext(a:np.ndarray, b:np.ndarray) -> np.ndarray:
    return np.divide(a, b, where=np.all((b!=0, np.isfinite(b)), axis=0))

def find_matches(a:np.ndarray, b:np.ndarray, tol:float=10) -> Tuple[np.ndarray, np.ndarray]:
    a_, b_ = (a, b) if len(b) >= len(a) else (b, a)
    cost = np.linalg.norm(a_[:, np.newaxis, :] - b_, axis=2)
    indices = linear_sum_assignment(cost)[1]
    a_, b_ = (a, b[indices]) if len(b) >= len(a) else (a[indices], b)
    dist = np.linalg.norm(a_ - b_, axis=1)
    return a_[dist <= tol], b_[dist <= tol]

def wrapto180(rho:np.ndarray) -> np.ndarray:
    return np.angle(np.exp(1j * np.deg2rad(rho)), deg=True)

## PyPOLAR WIDGETS

class Button(CTk.CTkButton):
    def __init__(self, master, text:str=None, image:CTk.CTkImage=None, tooltip:str=None, width:int=button_size[0], height:int=button_size[1], anchor:str='w', **kwargs) -> None:
        super().__init__(master, text=text, image=image, width=width, height=height, anchor=anchor, compound=tk.LEFT, **kwargs)
        if text is None:
            self.configure(width=height)
        if tooltip is not None:
            ToolTip(self, text=tooltip)

    def bind(self, sequence=None, command=None, add=True):
        if not (add == '+' or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)
        if self._text_label:
            self._text_label.bind(sequence, command, add=True)
        if self._image_label:
            self._image_label.bind(sequence, command, add=True)

class CheckBox(CTk.CTkCheckBox):
    def __init__(self, master, text:str=None, tooltip:str=None, command:Callable=None, **kwargs) -> None:
        super().__init__(master, text=text, command=command, onvalue=True, offvalue=False, width=30, **kwargs)
        if tooltip is not None:
            ToolTip(self, text=tooltip)

class Entry(CTk.CTkFrame):
    def __init__(self, master, text:str=None, textvariable:tk.StringVar=None, tooltip:str=None, state:str='normal', row:int=0, column:int=0, padx:Union[int, Tuple[int, int]]=(10, 30), pady:Union[int, Tuple[int, int]]=5, sticky:str='e', fg_color:str=gray[0], width:int=50, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.configure(fg_color=fg_color)
        self.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)
        if text is not None:
            Label(self, text=text, tooltip=tooltip).grid(row=0, column=0, padx=(0, 10))
        self.entry = CTk.CTkEntry(self, textvariable=textvariable, width=width, justify='center', state=state)
        self.entry.grid(row=0, column=1)

    def get(self) -> int:
        return int(self.entry.get())
        
    def set_state(self, state:str) -> None:
        self.entry.configure(state=state)

    def bind(self, *args, **kwargs):
        return self.entry.bind(*args, **kwargs)

class DropDown(CTk.CTkFrame):
    def __init__(self, master, values:List[str]=[], image:CTk.CTkImage=None, tooltip:str=None, command:Callable=None, variable:tk.StringVar=None, state:str='normal', **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg_color=orange[0], background_corner_colors=[gray[0], gray[0], gray[0], gray[0]])
        self.variable = variable
        self.icon = Button(self, image=image, tooltip=tooltip, hover=False, width=button_size[1])
        self.icon.grid(row=0, column=0)
        self.option_menu = CTk.CTkOptionMenu(self, values=values, width=button_size[0]-button_size[1]-5, height=button_size[1], dynamic_resizing=False, command=command, variable=variable, state=state)
        self.option_menu.grid(row=0, column=1)

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
    
class Label(CTk.CTkLabel):
    def __init__(self, master, tooltip:str=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        if tooltip is not None:
            ToolTip(self, text=tooltip)

class OptionMenu(CTk.CTkOptionMenu):
    def __init__(self, master, tooltip:str=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        if tooltip is not None:
            ToolTip(self, text=tooltip)

class SpinBox(CTk.CTkFrame):
    def __init__(self, master, from_:int=1, to_:int=20, step_size:int=1, textvariable:tk.StringVar=None, command:Callable=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        width, updown_size = 40, 8
        self.from_, self.to_, self.step_size = from_, to_, step_size
        self.command = command
        self.configure(fg_color=gray[1]) 
        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.subtract_button = CTk.CTkButton(self, text=u'\u25BC', width=updown_size, height=updown_size, command=self.subtract_button_callback)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)
        self.entry = CTk.CTkEntry(self, width=width-(2*updown_size), height=updown_size, border_width=0, justify='center', textvariable=textvariable)
        self.entry.grid(row=0, column=1, columnspan=1, padx=0, pady=0, sticky='ew')
        self.add_button = CTk.CTkButton(self, text=u'\u25B2', width=updown_size, height=updown_size, command=self.add_button_callback)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)
        if textvariable is None:
            self.entry.insert(0, from_)

    def add_button_callback(self) -> None:
        value = int(self.entry.get()) + self.step_size
        self.entry.delete(0, 'end')
        self.entry.insert(0, value if value <= self.to_ else self.to_)
        if self.command is not None:
            self.command()

    def subtract_button_callback(self) -> None:
        value = int(self.entry.get()) - self.step_size
        self.entry.delete(0, 'end')
        self.entry.insert(0, value if value >= self.from_ else self.from_)
        if self.command is not None:
            self.command()
        
    def bind(self, event:tk.Event, command:Callable) -> None:
        self.entry.bind(event, command)

    def get(self) -> int:
        return int(self.entry.get())

    def set(self, value:int) -> None:
        self.entry.delete(0, 'end')
        self.entry.insert(0, str(sorted([self.from_, value, self.to_])[1]))

class ShowInfo(CTk.CTkToplevel):
    def __init__(self, message:str='', image:CTk.CTkImage=None, button_labels:List[str]=[], geometry:tuple=(300, 150), fontsize:int=13) -> None:
        super().__init__()
        self.attributes('-topmost', 'true')
        self.title('PyPOLAR')
        self.geometry(geometry_info(geometry))
        CTk.CTkLabel(self, text=message, image=image, compound='left', width=250, justify=tk.LEFT, font=CTk.CTkFont(size=fontsize)).grid(row=0, column=0, padx=30, pady=20)
        self.buttons = []
        if button_labels:
            if len(button_labels) >= 2:
                banner = CTk.CTkFrame(self, fg_color='transparent')
                banner.grid(row=1, column=0)
                master, row_ = banner, 0
            else:
                master, row_ = self, 1
            for _, label in enumerate(button_labels):
                button = Button(master, text=label, width=80, anchor='center')
                if label == 'OK':
                    button.configure(command=lambda:self.withdraw())
                button.grid(row=row_, column=_, padx=20, pady=20)
                self.buttons += [button]

    def get_buttons(self) -> List[Button]:
        return self.buttons
    
class Switch(CTk.CTkSwitch):
    def __init__(self, master, tooltip:str=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        if tooltip is not None:
            ToolTip(self, text=tooltip)
    
class TextBox(CTk.CTkTextbox):
    def __init__(self, master, tooltip:str=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.configure(state='disabled')
        if tooltip is not None:
            ToolTip(self, text=tooltip)

    def write(self, text:str) -> None:
        self.configure(state='normal')
        self.delete('0.0', 'end')
        self.insert('0.0', text)
        self.configure(state='disabled')

## PyPOLAR MAIN CLASSES

class Stack:
    def __init__(self, file:Path) -> None:
        self.file = file
        self.folder = file.parent
        self.name = file.stem
        self.height, self.width, self.nangle = 0, 0, 0
        self.display = '{:.0f}'
        self.values = []
        self.intensity = []

    def get_intensity(self, dark:float=0, bin:List[int]=[1, 1]) -> np.ndarray:
        intensity = np.sum((self.values - dark) * (self.values >= dark), axis=0)
        if sum(bin) != 2:
            return convolve2d(intensity, np.ones(bin), mode='same') / (bin[0] * bin[1])
        else:
            return intensity
        
    def compute_dark(self, size_cell:int=20) -> int:
        n_height, n_width = int(np.floor(self.height / size_cell)), int(np.floor(self.width / size_cell))
        crop_im = np.moveaxis(self.values[:, :size_cell * n_height, :size_cell * n_width], 0, -1)
        im_cg = np.asarray(np.split(np.asarray(np.split(crop_im, n_width, axis=1)), n_height, axis=1))
        m_im_cg = np.mean(im_cg[..., 0], axis=(2, 3), where=im_cg[..., 0]!=0)
        ind_i, ind_j = np.unravel_index(np.argmin(m_im_cg), m_im_cg.shape)
        if np.all(im_cg[ind_i, ind_j, ...]) == 0:
            return 0
        return np.mean(im_cg[ind_i, ind_j, ...], where=im_cg[ind_i, ind_j, ...]!=0)

class DataStack:
    def __init__(self, stack:Stack) -> None:
        self.file = stack.file
        self.folder = stack.folder
        self.name = stack.name
        self.method = ''
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

    def plot_intensity(self, ax, contrast:float, rotation:int=0):
        vmin, vmax = np.amin(self.intensity), np.amax(self.intensity)
        field = adjust(self.intensity, contrast, vmin, vmax)
        if rotation:
            field = rotate(field, rotation, reshape=False, mode='constant', cval=vmin)
        return ax.imshow(field, cmap='gray', interpolation='nearest', vmin=vmin, vmax=vmax)

class Variable:
    def __init__(self, name:str='', values:np.ndarray=None, datastack:DataStack=None) -> None:
        var = {'Rho': [0, ['polar1'], r'$\rho$', ['hsv', m_colorwheel]], 
                'Rho_contour': [10, ['polar1', 'polar3'], r'$\rho_c$', ['hsv', m_colorwheel]],
                'Rho_angle': [10, ['polar1', 'polar3'], r'$\rho_a$', ['hsv', m_colorwheel]],
                'Psi': [1, ['normal'], '$\psi$', ['jet', 'viridis']],
                'Eta': [2, ['polar2'], '$\eta$', ['plasma', 'plasma']],
                'S2': [1, ['normal'], '$S_2$', ['jet', 'viridis']],
                'S4': [2, ['normal'], '$S_4$', ['jet', 'viridis']],
                'S_SHG': [1, ['normal'], '$S_\mathrm{SHG}$', ['jet', 'viridis']]}.get(name)
        self.indx = var[0] if var is not None else 0
        self.name = name
        self.latex = var[2] if var is not None else ''
        self.values = values if values is not None else np.nan * np.ones((datastack.height, datastack.width)) if datastack is not None else []
        self.type_histo = var[1] if var is not None else ['normal']
        self.colormap = var[3] if var is not None else ['jet', 'viridis']

    def imshow(self, vmin:float, vmax:float, colorblind:bool=False, rotation:float=0) -> mpl.image.AxesImage:
        ax = plt.gca()
        field = self.values.copy()
        if self.name == 'Rho':
            field = np.mod(2 * (field + rotation), 360) / 2
        if rotation:
            field = rotate(field, rotation, reshape=False, order=0, mode='constant')
            field[field == 0] = np.nan
        return ax.imshow(field, vmin=vmin, vmax=vmax, cmap=self.colormap[int(colorblind)], interpolation='nearest')

    def histo(self, mask:np.ndarray=None, htype:str='normal', vmin:float=0, vmax:float=180, colorblind:bool=False, rotation:float=0, nbins:int=60) -> None:
        data_vals = self.values[mask * np.isfinite(self.values)] if mask is not None else self.values[np.isfinite(self.values)]
        if self.name in ['Rho', 'Rho_angle']:
            data_vals = np.mod(2 * (data_vals + rotation), 360) / 2   
        vmin_, vmax_ = (0, 90) if htype == 'polar3' else (vmin, vmax)
        norm = mpl.colors.Normalize(vmin_, vmax_)
        cmap = self.colormap[int(colorblind)]
        if isinstance(cmap, str):
            cmap = mpl.colormaps[cmap] 
        bins = np.linspace(vmin_, vmax_, nbins)
        if htype == 'normal':
            ax = plt.gca()
            n, bins, patches = ax.hist(data_vals, bins=bins, linewidth=0.5)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            for bin, patch in zip(bin_centers, patches):
                color = cmap(norm(bin))
                patch.set_facecolor(color)
                patch.set_edgecolor('k')
            ax.set_xlim((vmin_, vmax_))
            ax.set_xlabel(self.latex, fontsize=20)
            text = self.latex + ' = ' + '{:.2f}'.format(np.mean(data_vals)) + ' $\pm$ ' '{:.2f}'.format(np.std(data_vals))
            ax.annotate(text, xy=(0.3, 1.05), xycoords='axes fraction', fontsize=14)
        elif htype.startswith('polar'):
            ax = plt.subplot(projection='polar')
            if htype == 'polar1':
                meandata = circularmean(data_vals)
                std = np.std(wrapto180(2 * (data_vals - meandata)) / 2)
            elif htype == 'polar2':
                ax.set_theta_zero_location('N')
                ax.set_theta_direction(-1)
                meandata = np.mean(data_vals)
                std = np.std(data_vals)
            elif htype == 'polar3':
                ax.set_theta_zero_location('E')
                data_vals[data_vals >= 90] = 180 - data_vals[data_vals >= 90]
                meandata = circularmean(data_vals)
                std = np.std(wrapto180(2 * (data_vals - meandata)) / 2)
                norm = mpl.colors.Normalize(0, 180)
            distribution, bin_edges = np.histogram(data_vals, bins=bins, range=(vmin_, vmax_))
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            width = np.deg2rad(bins[1] - bins[0])
            colors = cmap(norm(bins))
            ax.bar(np.deg2rad(bin_centers), distribution, width=width, color=colors, edgecolor='k', linewidth=0.5)
            num = 10**(len(str(np.amax(distribution))) - 2)
            ax.set_rticks(np.floor(np.linspace(0, np.max(distribution), 3) / num) * num)
            ax.set_thetamin(vmin_)
            ax.set_thetamax(vmax_)
            text = self.latex + ' = ' + '{:.2f}'.format(meandata) + ' $\pm$ ' '{:.2f}'.format(std)
            if htype == 'polar1':
                ax.annotate(text, xy=(0.3, 0.95), xycoords='axes fraction', fontsize=14)
            else:
                ax.annotate(text, xy=(0.7, 0.95), xycoords='axes fraction', fontsize=14)

class ROI:
    def __init__(self) -> None:
        self.start_point = []
        self.end_point = []
        self.previous_point = []
        self.x = []
        self.y = []
        self.lines = []

class Calibration:

    dict_1pf = {'no distortions': ['Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0', 0], '488 nm (no distortions)': ['Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0', 175], '561 nm (no distortions)': ['Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0', 120], '640 nm (no distortions)': ['Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0', 125], '488 nm (16/03/2020 - 12/04/2022)': ['Disk_Ga0_Pa20_Ta45_Gb-0.1_Pb0_Tb0_Gc-0.1_Pc0_Tc0', 0], '561 nm (16/03/2020 - 12/04/2022)': ['Disk_Ga-0.2_Pa0_Ta0_Gb0.1_Pb0_Tb0_Gc-0.2_Pc0_Tc0', 0], '640 nm (16/03/2020 - 12/04/2022)': ['Disk_Ga-0.2_Pa0_Ta45_Gb0.1_Pb0_Tb45_Gc-0.1_Pc0_Tc0', 0], '488 nm (13/12/2019 - 15/03/2020)': ['Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb20_Tb45_Gc-0.2_Pc0_Tc0', 0], '561 nm (13/12/2019 - 15/03/2020)': ['Disk_Ga-0.2_Pa0_Ta0_Gb0.2_Pb20_Tb0_Gc-0.2_Pc0_Tc0', 0], '640 nm (13/12/2019 - 15/03/2020)': ['Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc-0.2_Pc0_Tc0', 0], '488 nm (before 13/12/2019)': ['Disk_Ga-0.1_Pa20_Ta0_Gb-0.1_Pb10_Tb45_Gc0.1_Pc0_Tc0', 0], '561 nm (before 13/12/2019)': ['Disk_Ga0.1_Pa0_Ta45_Gb-0.1_Pb20_Tb0_Gc-0.1_Pc0_Tc0', 0], '640 nm (before 13/12/2019)': ['Disk_Ga-0.1_Pa10_Ta0_Gb0.1_Pb30_Tb0_Gc0.2_Pc0_Tc0', 0], 'other': ['Disk_Ga0_Pa0_Ta0_Gb0_Pb0_Tb0_Gc0_Pc0_Tc0', 0]}
    folder_1pf = Path(__file__).parent / 'diskcones'

    dict_4polar = {'no distortions': ['Calib_th', 0], 'Calib_20231009_2D': ['Calib_20231009_2D', 0], 'other': ['Calib_th', 0]}
    folder_4polar = Path(__file__).parent / 'calibration'

    def __init__(self, method:str, label:str='no distortions') -> None:
        if method == '1PF':
            vars = type(self).dict_1pf.get(label)
            folder = type(self).folder_1pf
        elif method.startswith('4POLAR'):
            vars = type(self).dict_4polar.get(label)
            folder = type(self).folder_4polar
        if method == '1PF':
            if label == 'other':
                file = Path(fd.askopenfilename(title='Select file', initialdir=Path.home(), filetypes=[('MAT-files', '*.mat')]))
                folder = file.parent
                vars = [file.stem, 0]
            disk = loadmat(str(folder / (vars[0] + '.mat')))
            try:
                self.RhoPsi = np.moveaxis(np.stack((np.array(disk['RoTest'], dtype=np.float64), np.array(disk['PsiTest'], dtype=np.float64))), 0, -1)
                self.xy = 2 * (np.linspace(-1, 1, int(disk['NbMapValues']), dtype=np.float64),)
            except:
                showerror('Calibration data', 'Incorrect disk cone\n Download another file', icon='error')
                vars = [' ', 0]
        elif method.startswith('4POLAR'):
            if label == 'no distortions':
                vars[0] = 'Calib_th_' + method[-2] + 'D'
            if label == 'other':
                file = Path(fd.askopenfilename(title='Select file', initialdir=Path.home(), filetypes=[('TXT-files', '*.txt')]))
                folder = file.parent
                vars = [file.stem, 0]
            try:
                self.invKmat = np.linalg.pinv(np.genfromtxt(str(folder / (vars[0] + '.txt')), dtype=np.float64))
                if self.invKmat.shape != (int(method[-2]) + 1, 4):
                    raise ValueError('Error in the dimension of the calibration matrix')
            except:
                showerror('Calibration data', 'Incorrect calibration data\n Download another file')
                vars = [' ', 0]
        else:
            vars = [' ', 0]
        self.name, self.offset_default = vars

    def display(self, colorblind:bool=False) -> None:
        fig, axs = plt.subplots(ncols=2, figsize=(13, 8))
        fig.canvas.manager.set_window_title('Disk Cone: ' + self.name)
        labels = ['Rho Test', 'Psi Test']
        cmaps = [m_colorwheel, 'viridis'] if colorblind else ['hsv', 'jet']
        for _, (label, cmap, ax) in enumerate(zip(labels, cmaps, axs)):
            h = ax.imshow(self.RhoPsi[:, :, _], cmap=cmap, interpolation='nearest', extent=[-1, 1, -1, 1], vmin=0, vmax=180)
            ax.set_title(label)
            ax.set_xlabel('$B_2$')
            ax.set_ylabel('$A_2$')
            fig.colorbar(h, cax=make_axes_locatable(ax).append_axes('right', size='7%', pad='2%'))
        plt.subplots_adjust(wspace=0.4)

    def list(self, method:str) -> str:
        if method == '1PF':
            return [key for key in type(self).dict_1pf.keys()]
        elif method.startswith('4POLAR'):
            return [key for key in type(self).dict_4polar.keys()]
        else:
            return ' '
    
class NToolbar2PyPOLAR(NavigationToolbar2, tk.Frame):

    folder = Path(__file__).parent / 'icons'

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
            im = NToolbar2PyPOLAR.folder / (image_file + '.png')
            self._buttons[text] = button = self._Button(text=text, image_file=str(im), toggle=callback in ['zoom', 'pan'], command=getattr(self, callback))
            if tooltip_text is not None:
                ToolTip(button, text=tooltip_text)
                
        if sys.platform == 'darwin':
            self._label_font = CTk.CTkFont(family=font_macosx, size=11, weight='normal')
        elif sys.platform == 'win32':
            self._label_font = CTk.CTkFont(family=font_windows, size=13, weight='bold')

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
        self.canvas._rubberband_rect_white = (self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, outline=orange[0], dash=(3, 3)))
        
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
            return Image.fromarray(image_data, mode='RGBA')

        with Image.open(button._image_file) as im:
            size_image = 26
            im = im.convert('RGBA')
            im = _recolor_icon(im, fg_color='#00000')
            image = ImageTk.PhotoImage(im.resize((size_image, size_image)), master=self)
            im = _recolor_icon(im, fg_color=orange[0])
            image_alt = ImageTk.PhotoImage(im.resize((size_image, size_image)), master=self)
            button._ntimage = image
            button._ntimage_alt = image_alt

        image_kwargs = {'image': image}
        if (isinstance(button, tk.Checkbutton) and button.cget('selectcolor') != ''):
            image_kwargs['selectimage'] = image_alt
        
        button.configure(**image_kwargs)
        
    def _Button(self, text:str, image_file:str, toggle:bool, command:Callable) -> Union[tk.Button, tk.Checkbutton]:
        size_button = 30
        if not toggle:
            b = tk.Button(master=self, text=text, command=command, relief='flat', overrelief='flat', highlightthickness=0, height=size_button, width=size_button)
        else:
            var = tk.IntVar(master=self)
            b = tk.Checkbutton(master=self, text=text, command=command, indicatoron=False, variable=var, offrelief='flat', overrelief='flat', height=size_button+2, width=size_button+2)
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
        initialdir = Path(mpl.rcParams['savefig.directory']).expanduser()
        initialfile = self.canvas.get_default_filename()
        title = f"Save image from '{self.window.master.get()}' tab" if self.window is not None else "Save image"
        fname = fd.asksaveasfilename(master=self.canvas.get_tk_widget().master, title=title, filetypes=tk_filetypes, defaultextension=defaultextension, initialdir=initialdir, initialfile=initialfile)
        if fname in ['', ()]:
            return
        if initialdir != '':
            mpl.rcParams['savefig.directory'] = str(Path(fname).parent)
        try:
            self.canvas.figure.savefig(fname)
        except Exception as e:
            showerror('Error saving file', str(e))

    def set_history_buttons(self) -> None:
        state_map = {True: tk.NORMAL, False: tk.DISABLED}
        can_back = self._nav_stack._pos > 0
        can_forward = self._nav_stack._pos < len(self._nav_stack._elements) - 1
        if 'Back' in self._buttons:
            self._buttons['Back']['state'] = state_map[can_back]
        if 'Forward' in self._buttons:
            self._buttons['Forward']['state'] = state_map[can_forward]

    def _mouse_event_to_message(self, event:MouseEvent) -> str:
        if event.inaxes and event.inaxes.get_navigate():
            try:
                s = f'(x={int(event.xdata)}, y={int(event.ydata)})'
            except (ValueError, OverflowError):
                pass
            else:
                artists = [a for a in event.inaxes._mouseover_set if a.contains(event)[0] and a.get_visible()]
                if artists:
                    a = mpl.cbook._topmost_artist(artists)
                    if a is not event.inaxes.patch:
                        data = a.get_cursor_data(event)
                        if data is not None:
                            s += f'\nI={int(np.sum(data))}'
                return s
        return ''
    
class PyPOLARfigure:
    def __init__(self, fig, master=None):
        self.canvas = FigureCanvasTkAgg(fig, master=master)
        self.canvas.draw()
        self.toolbar = NToolbar2PyPOLAR(canvas=self.canvas, window=master)
        self.canvas.get_tk_widget().pack(side=CTk.TOP, fill=CTk.BOTH, expand=True)
        self.toolbar.pack(side=CTk.TOP, fill=CTk.X)
    
class ToolTip:
    def __init__(self, widget, *, pad=(5, 3, 5, 3), text:str='widget info', waittime:int=300, wraplength:int=250) -> None:
        self.waittime = waittime  
        self.wraplength = wraplength
        self.widget = widget
        self.text = text
        self.widget.bind('<Enter>', self.onEnter)
        self.widget.bind('<Leave>', self.onLeave)
        self.pad = pad
        self.id = None
        self.tw = None

    def onEnter(self, event=None) -> None:
        self.schedule()

    def onLeave(self, event=None) -> None:
        self.unschedule()
        self.hide()

    def schedule(self) -> None:
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self) -> None:
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self) -> None:
        def tip_pos_calculator(widget, label, *, tip_delta=(10, 5), pad=(5, 3, 5, 3)):
            s_width, s_height = widget.winfo_screenwidth(), widget.winfo_screenheight()
            width, height = (pad[0] + label.winfo_reqwidth() + pad[2], pad[1] + label.winfo_reqheight() + pad[3])
            mouse_x, mouse_y = widget.winfo_pointerxy()
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height
            x_delta = x2 - s_width if x2 > s_width else 0
            y_delta = y2 - s_height if y2 > s_height else 0
            offscreen = (x_delta, y_delta) != (0, 0)
            if offscreen:
                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width
                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height
            y1 = y1 if y1 > 0 else 0
            return x1, y1
        
        pad = self.pad
        widget = self.widget
        self.tw = tk.Toplevel(widget)
        self.tw.wm_overrideredirect(True)
        win = tk.Frame(self.tw, borderwidth=0)
        if sys.platform == 'darwin':
            label_font = CTk.CTkFont(family=font_macosx, size=11, weight='normal')
        elif sys.platform == 'win32':
            label_font = CTk.CTkFont(family=font_windows, size=13, weight='bold')
        label = tk.Label(win, text=self.text, font=label_font, justify=tk.LEFT, relief=tk.SOLID, borderwidth=0, wraplength=self.wraplength)
        label.grid(padx=(pad[0], pad[2]), pady=(pad[1], pad[3]), sticky=tk.NSEW)
        win.grid()
        x, y = tip_pos_calculator(widget, label)
        self.tw.wm_geometry(f'+{x}+{y}')

    def hide(self) -> None:
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None

class ROIManager(CTk.CTkToplevel):
    labels = ['indx', 'name', 'group']
    widths = [40, 250, 90]
    button_labels = ['Save', 'Load', 'Delete']
    tooltips = [' save information on ROIs as a .pyroi file', ' load ROIs from a .pyroi file', ' permanently deletes ROIs selected in delete column']
    manager_size = lambda w, h: f'{w+40}x{h+84}'
    cmax = len(labels)
    cell_height = 25

    def __init__(self, rois:list=[], button_images:list=[]) -> None:
        super().__init__(fg_color=gray[1])
        self.title('ROI Manager')
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sheet_height = lambda cell_h, rois_: self.cell_height + (cell_h + 2) * (len(rois_) + 1)
        widths = type(self).widths + [95, 95]
        self.sheet_width = sum(widths) + 2

        self.geometry(type(self).manager_size(self.sheet_width, self.sheet_height(self.cell_height, rois)) + f'+1200+200')

        if sys.platform == 'darwin':
            font = (font_macosx, 14, 'normal')
            header_font = (font_macosx, 16, 'bold')
        elif sys.platform == 'win32':
            font = (font_windows, 14, 'normal')
            header_font = (font_windows, 16, 'bold')

        labels_ = type(self).labels + ['select', 'delete']
        labels_[0] = 'ROI'
        data = [[roi[label] for label in type(self).labels] for roi in rois]
        self.sheet = tksheet.Sheet(self, data=data, headers=labels_, font=font, header_font=header_font, align='w', show_row_index=False, width=self.sheet_width, height=self.sheet_height(self.cell_height, rois), frame_bg=text_color, table_bg=gray[1], top_left_bg=text_color, header_hidden_columns_expander_bg=gray[1], header_fg=text_color, header_bg=gray[1], outline_thickness=0, header_border_fg=text_color, header_grid_fg=text_color, table_grid_fg=text_color, header_selected_cells_bg=gray[1], table_selected_cells_border_fg=orange[0], table_selected_columns_bg=gray[1], table_selected_columns_border_fg=orange[0], header_selected_columns_bg=gray[1], header_selected_columns_fg=text_color, show_x_scrollbar=False, show_y_scrollbar=False, show_top_left=False, enable_edit_cell_auto_resize=False, auto_resize_default_row_index=False, show_default_header_for_empty=False, empty_horizontal=0, empty_vertical=0, total_columns=type(self).cmax+2)
        self.sheet.set_options(edit_cell_validation=False)
        self.sheet.grid(row=0, column=0, sticky='nswe', padx=20, pady=(20, 0))
        bottom_frame = CTk.CTkFrame(self, fg_color=gray[1])
        bottom_frame.grid(row=1, column=0, sticky='nswe', padx=20, pady=(0, 20))
        self.buttons = []
        for _, (label, tooltip, image) in enumerate(zip(type(self).button_labels, type(self).tooltips, button_images)):
            button = Button(bottom_frame, text=label, width=110, image=image)
            ToolTip(button, text=tooltip)
            self.buttons += [button]
            button.grid(row=0, column=_, padx=10, pady=10, sticky='nswe')
        self.add_elements(type(self).cmax, rois)
        self.sheet.enable_bindings()
        self.sheet.disable_bindings(['rc_insert_column', 'rc_delete_column', 'rc_insert_row', 'rc_delete_row', 'hide_columns', 'row_height_resize','row_width_resize', 'column_height_resize', 'column_width_resize', 'edit_header', 'arrowkeys'])
        self.sheet.default_row_height(self.cell_height)
        for _, width in enumerate(widths):
            self.sheet.column_width(column=_, width=width)
        self.sheet.create_header_checkbox(c=3, checked=True, text="select", check_function=self.select_all)
        self.sheet.create_header_checkbox(c=4, checked=False, text="delete", check_function=self.delete_all)

    def add_elements(self, cmax:int, rois) -> None:
        self.sheet.align_columns(columns=[0, cmax-1], align='center')
        for _, roi in enumerate(rois):
            self.sheet.create_checkbox(r=_, c=cmax, checked=roi['select'], state='normal', redraw=False, check_function=None, text='')
        self.sheet.create_checkbox(r='all', c=cmax+1, checked=False, state='normal', redraw=False, check_function=None, text='')
        self.sheet.highlight_columns(columns=[cmax, cmax+1], fg=orange[0], highlight_header=False)

    def select_all(self, value:bool) -> None:
        try:
            for _ in range(self.sheet.get_total_rows()):
                self.sheet.MT.data[_][3] = bool(value[3])
        except:
            pass
    
    def delete_all(self, value:bool) -> None:
        try:
            for _ in range(self.sheet.get_total_rows()):
                self.sheet.MT.data[_][4] = bool(value[3])
        except:
            pass
        
    def delete(self, rois:list) -> None:
        vec = [_ for _, x in enumerate(self.sheet.get_column_data(c=-1)) if x==True]
        if len(vec) >= 1:
            self.sheet.MT._headers[-1] = False
        while len(vec) >= 1:
            self.sheet.delete_row(idx=vec[0])
            del rois[vec[0]]
            for _, roi in enumerate(rois):
                roi['indx'] = _ + 1
            self.sheet.set_column_data(0, values=tuple(roi['indx'] for roi in rois), add_rows=False)
            vec = [_ for _, x in enumerate(self.sheet.get_column_data(c=-1)) if x==True]
        self.sheet.set_options(height=self.sheet_height(self.cell_height, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(type(self).manager_size(self.sheet_width, self.sheet_height(self.cell_height, rois)) + f'+{x}+{y}')
    
    def delete_manager(self) -> None:
        try:
            for _ in range(self.sheet.get_total_rows()):
                self.sheet.delete_row()
            self.sheet.set_options(height=self.sheet_height(self.cell_height, []))
            x, y = self.winfo_x(), self.winfo_y()
            self.geometry(type(self).manager_size(self.sheet_width, self.sheet_height(self.cell_height, [])) + f'+{x}+{y}')
        except:
            pass

    def get_buttons(self) -> list:
        return self.buttons

    def load(self, initialdir:Path=Path.home()) -> List[dict]:
        self.delete_manager()
        filetypes = [('PyROI files', '*.pyroi')]
        file = fd.askopenfilename(title='Select a PyROI file', initialdir=initialdir, filetypes=filetypes)
        with open(file, 'rb') as f:
            rois = pickle.load(f)
        self.sheet.set_options(height=self.sheet_height(self.cell_height, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(type(self).manager_size(self.sheet_width, self.sheet_height(self.cell_height, rois)) + f'+{x}+{y}')
        self.sheet.insert_rows(rows=len(rois))
        self.add_elements(len(type(self).labels), rois)
        self.rois2sheet(rois)
        return rois

    def rois2sheet(self, rois:List[dict]):
        for it, roi in enumerate(rois):
            for jt, label in enumerate(self.labels):
                self.sheet.set_cell_data(it, jt, value=roi[label])

    def save(self, rois:List[dict]=[], file:Path=Path.home() / 'ROIs') -> None:
        if any(rois):
            rois = self.update_rois(rois)
            with file.with_suffix('.pyroi').open('wb') as f:
                pickle.dump(rois, f, protocol=pickle.HIGHEST_PROTOCOL)

    def update_manager(self, rois:List[dict]) -> None:
        self.sheet.set_options(height=self.sheet_height(self.cell_height, rois))
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(type(self).manager_size(self.sheet_width, self.sheet_height(self.cell_height, rois)) + f'+{x}+{y}')
        roi = rois[-1]
        self.sheet.insert_row([roi[label] for label in type(self).labels])
        self.sheet.create_checkbox(c=type(self).cmax, r=len(rois)-1, checked = roi['select'])
        self.sheet.create_checkbox(c=type(self).cmax+1, r=len(rois)-1, checked = False)

    def update_rois(self, rois:List[dict]=[]) -> List[dict]:
        if any(rois):
            data = self.sheet.get_sheet_data()
            for _, roi in enumerate(rois):
                roi['name'] = data[_][1]
                roi['group'] = data[_][2]
                roi['select'] = data[_][-2]
            return rois
        return []
    
class TabView(CTk.CTkTabview):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.configure(segmented_button_selected_color=orange[0], segmented_button_unselected_color=gray[1], segmented_button_selected_hover_color=orange[1], text_color=text_color, segmented_button_fg_color=gray[0], fg_color=gray[1])
        tabs = ['Intensity', 'Thresholding/Mask', 'Options', 'Advanced', 'About']
        for tab in tabs:
            self.add(tab)
        self.pack(fill=tk.BOTH, expand=True)