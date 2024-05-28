import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from colorcet import m_colorwheel

def main() -> None:

	## COLORBAR PARAMETERS

	variable = 'S2'  				## 'Rho', 'Rho_contour', 'Rho_angle', 'Psi', 'Eta', 'S2', 'S4', 'S_SHG'
	colorbar_type = 'vertical'		## 'vertical', 'horizontal', 'polar180', 'polar90'
	color = 'k'						## 'k', 'w'
	label_side = 'left'				## None, 'left', 'right', 'top', 'bottom'
	colorblind = False				## True, False
	nbr_ticks = 5					## any integer
	aspect_ratio = 20				## any integer
	font_size = 20					## any integer
	font = 'Arial'					## see https://matplotlib.org/stable/users/explain/customizing.html
	font_style = 'bold'				## see https://matplotlib.org/stable/users/explain/customizing.html
	save_extension = '.png'			## '.png', '.pdf', '.jpg', '.tif'
	resolution = 300				## 150, 300, 600

	###################################################################################################################
	##                                          DO NOT EDIT BELOW THIS LINE                                          ##
	###################################################################################################################
	mpl.rcParams['axes.linewidth'] = 2
	mpl.rcParams['axes.labelsize'] = font_size
	mpl.rcParams['xtick.labelsize'] = font_size
	mpl.rcParams['ytick.labelsize'] = font_size
	mpl.rcParams['axes.edgecolor'] = color
	mpl.rcParams['font.sans-serif'] = font
	mpl.rcParams['font.weight'] = font_style
	Colorbar(variable, colorbar_type=colorbar_type, aspect_ratio=aspect_ratio, color=color, colorblind=colorblind,\
		   		label_side=label_side, nbr_ticks=nbr_ticks).plot_colorbar()
	plt.savefig(variable + "Colorbar" + save_extension, dpi=resolution, transparent=True, bbox_inches='tight')
	plt.show()

class Colorbar:

	dict_vars = {'Rho': [['vertical', 'horizontal', 'polar180'], r'\rho', ['hsv', m_colorwheel], (0, 180)], 
                'Rho_contour': [['vertical', 'horizontal', 'polar180', 'polar90'], r'$\rho_c$', ['hsv', m_colorwheel], (0, 180)],
                'Rho_angle': [['vertical', 'horizontal', 'polar180', 'polar90'], r'$\rho_a$', ['hsv', m_colorwheel], (0, 180)],
                'Psi': [['vertical', 'horizontal'], '$\psi$', ['jet', 'viridis'], (40, 180)],
                'Eta': [['vertical', 'horizontal', 'polar90'], '$\eta$', ['plasma', 'plasma'], (0, 90)],
                'S2': [['vertical', 'horizontal'], '$S_2$', ['jet', 'viridis'], (0, 1)],
                'S4': [['vertical', 'horizontal'], '$S_4$', ['jet', 'viridis'], (-1, 1)],
                'S_SHG': [['vertical', 'horizontal'], '$S_\mathrm{SHG}$', ['jet', 'viridis'], (-1, 1)]}
				
	list_vars = [key for key in dict_vars.keys()]
	
	def __init__(self, var:str, colorbar_type:str='vertical', aspect_ratio:int=20, color:str='k', colorblind:bool=False,\
			   		label_side:str='right', nbr_ticks:int=8) -> None:
		if var not in type(self).list_vars:
			raise ValueError(f"Colorbar for var {var} is not available")
		data = type(self).dict_vars.get(var)
		if colorbar_type not in data[0]:
			raise ValueError(f"Colorbar type {colorbar_type} for var {var} is not available")
		self.var = var
		self.colorbar_type = colorbar_type
		self.colormap = data[2][1] if colorblind else data[2][0]
		self.color = color
		self.theta_setup = ('N', -1) if var == 'Eta' else ('E', 1)
		self.label_side = label_side
		self.var_range = data[3]
		if colorbar_type == 'polar90':
			self.var_range = (0, 90)
		if colorbar_type.startswith('polar'):
			self.aspect_ratio = 1
		else:
			self.aspect_ratio = aspect_ratio if colorbar_type=='vertical' else 1 / aspect_ratio
		ticks = np.linspace(*self.var_range, nbr_ticks)
		if not var.startswith('S'):
			labels = [str(int(_)) + u"\u00b0" for _ in ticks]
		else:
			labels = [f"{_:.1f}" for _ in ticks]
		self.ticks  = [ticks, [] if label_side is None else labels]
		
	def plot_colorbar(self) -> None:
		if not self.colorbar_type.startswith('polar'):
			fig, ax = plt.subplots(figsize=(5, 5))
			gradient = np.linspace(0, 1, 256)
			gradient = np.vstack((gradient, gradient))
			ax.tick_params('both', colors=self.color, width=2, length=6, direction='in')
		if self.colorbar_type == 'vertical':
			if self.label_side == 'right':
				ax.tick_params(labelright=True, labelleft=False)
			gradient = gradient.T  
			ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False, labeltop=False)
			ax.tick_params(axis='y', which='both', right=True, left=True)
			extent = (0, 1 if self.var.startswith('S') else 255, self.var_range[0], self.var_range[1])
			ax.set_yticks(self.ticks[0], labels=self.ticks[1])
			ax.imshow(gradient, aspect=self.aspect_ratio, cmap=self.colormap, extent=extent)
			#ax.pcolormesh(gradient, aspect=self.aspect_ratio, cmap=self.colormap, extent=extent)
		elif self.colorbar_type == 'horizontal':
			if self.label_side == 'top':
				ax.tick_params(labeltop=True, labelbottom=False)
			ax.tick_params(axis='x', which='both', bottom=True, top=True)
			ax.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
			extent = (self.var_range[0], self.var_range[1], 0, 255)
			ax.set_xticks(self.ticks[0], labels=self.ticks[1])
			ax.imshow(gradient, aspect=self.aspect_ratio, cmap=self.colormap, extent=extent)
		elif self.colorbar_type.startswith('polar'):
			fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(projection="polar"))
			ax.set_theta_zero_location(self.theta_setup[0])
			ax.set_theta_direction(self.theta_setup[1])
			ax.set_thetamin(self.var_range[0])
			ax.set_thetamax(self.var_range[1])
			outer_radius, rorigin = 20, -10
			x, y = np.meshgrid(np.linspace(outer_radius, -outer_radius, 2**10), np.linspace(0, outer_radius, 2**10))
			theta, rho = np.arctan2(y, x), np.sqrt(x**2 + y**2)
			ax.pcolormesh(theta, rho, theta, cmap=self.colormap)
			ax.set_rticks([])
			ax.set_rorigin(rorigin)
			if self.colorbar_type == 'polar180' and self.label_side is not None:
				self.ticks[1][-1] = self.ticks[1][-1] + "   "
			if self.theta_setup[1] == -1 and self.label_side is not None:
				self.ticks[1][-1] = "   " + self.ticks[1][-1]
			ax.set_thetagrids(self.ticks[0], labels=self.ticks[1], color=self.color, horizontalalignment='center')
			ax.grid(False)
			for t in np.deg2rad(self.ticks[0]):
				ax.plot([t, t], [outer_radius, outer_radius - 5], lw=2, color=self.color)
				ax.plot([t, t], [0, 5], lw=2, color=self.color)
			ax.set_rmax(outer_radius)

if __name__ == '__main__':
	main()