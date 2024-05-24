import numpy as np
import matplotlib.pyplot as plt
from colorcet import m_colorwheel


class Colorbar:
	
	dict_vars = {'Rho': [['normal', 'polar1'], r'\rho', ['hsv', m_colorwheel]], 
                'Rho_contour': [['normal', 'polar1', 'polar3'], r'$\rho_c$', ['hsv', m_colorwheel]],
                'Rho_angle': [['normal', 'polar1', 'polar3'], r'$\rho_a$', ['hsv', m_colorwheel]],
                'Psi': [['normal'], '$\psi$', ['jet', 'viridis']],
                'Eta': [['normal', 'polar2'], '$\eta$', ['plasma', 'plasma']],
                'S2': [['normal'], '$S_2$', ['jet', 'viridis']],
                'S4': [['normal'], '$S_4$', ['jet', 'viridis']],
                'S_SHG': [['normal'], '$S_\mathrm{SHG}$', ['jet', 'viridis']]}
				
	list_vars = [key for key in type(self).dict_vars.keys()]
	
	def __init__(self, var:str, colorbar_type:str='normal', edge_color:str='k', colorblind:bool=False) -> None:
		if var not in type(self).list_vars:
			raise ValueError(f"Colorbar for var {var} is not available")
		data = type(self).dictvars.get(var)
		if colorbar_type is not in data[0]:
			raise ValueError(f"Colorbar type {colorbar_type} for var {var} is not available")
		self.colorbar_type = colorbar_type
		self.colormap = data[2][1] if colorblind else data[2][0]
		self.vmin, self.vmax = (0, 180) if type_colorbar == 'polar1' else (0, 90)
		self.edge_color = edge_color
		self.theta_zero_location = 'N' if colorbar_type == 'polar2' else 'E'
        self.theta_direction = -1 if colorbar_type == 'polar2' else 1
		
	def plot_colorbar(self):
		if self.colorbar_type.startswith('polar'):
			ax = plt.subplot(projection='polar')
			ax.set_theta_zero_location(self.theta_zero_location)
        	ax.set_theta_direction(self.theta_direction)
			ax.set_thetamin(self.vmin)
            ax.set_thetamax(self.vmax)
		else:
			ax = plt.gca()
