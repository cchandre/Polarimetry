import tkinter as tk
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import customtkinter as CTk

class NToolbar2Tk(NavigationToolbar2Tk):

    folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Icons_Python/toolbar")

    def __init__(self, canvas, window, pack_toolbar):
        super().__init__(canvas=canvas, window=window, pack_toolbar=pack_toolbar)
        self._buttons = {}
        self.toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'backward', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan', 'Left button pans, Right button zooms\n x/y fixes axis, CTRL fixes aspect', 'pan', 'pan'),
        ('Zoom', 'Zoom to rectangle\n x/y fixes axis', 'zoom', 'zoom'),
        (None, None, None, None),
        ('Save', 'Save the figure', 'save', 'save_figure'),)
        tk.Frame.__init__(self, master=window)
        for num, (text, tooltip_text, image_file, callback) in enumerate(self.toolitems):
            if text is None:
                self._Spacer()
            else:
                im = NToolbar2Tk.folder + "/" + image_file + ".png"
                self._buttons[text] = button = self._Button(text=text, image_file=im, toggle=callback in ["zoom", "pan"], command=getattr(self, callback),)
                if tooltip_text is not None:
                    ToolTip.createToolTip(button, tooltip_text)
        self._label_font = CTk.CTkFont(size=10)
        label = tk.Label(master=self, font=self._label_font, text='\N{NO-BREAK SPACE}\n\N{NO-BREAK SPACE}')
        label.pack(side=tk.RIGHT)
        self.message = tk.StringVar(master=self)
        self._message_label = tk.Label(master=self, font=self._label_font, textvariable=self.message, justify=tk.RIGHT)
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
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + self.widget.winfo_width()
        y = y + self.widget.winfo_rooty()
        self.tipwindow = tw = tk.Toplevel(self.widget)
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



#    def get_roi_coordinates(self):
#        return list(zip(self.x, self.y))
