import numpy as np
import matplotlib.pyplot as plt
from colorcet import m_colorwheel


class Colorbar:
	
	dict_vars = {'Rho': [['normal', 'polar1'], r'\rho', ['hsv', m_colorwheel], (0, 180)], 
                'Rho_contour': [['normal', 'polar1', 'polar3'], r'$\rho_c$', ['hsv', m_colorwheel], (0, 180)],
                'Rho_angle': [['normal', 'polar1', 'polar3'], r'$\rho_a$', ['hsv', m_colorwheel], (0, 180)],
                'Psi': [['normal'], '$\psi$', ['jet', 'viridis'], (40, 180)],
                'Eta': [['normal', 'polar2'], '$\eta$', ['plasma', 'plasma'], (0, 90)],
                'S2': [['normal'], '$S_2$', ['jet', 'viridis'], (0, 1)],
                'S4': [['normal'], '$S_4$', ['jet', 'viridis'], (-1, 1)],
                'S_SHG': [['normal'], '$S_\mathrm{SHG}$', ['jet', 'viridis'], (-1, 1)]}
				
	list_vars = [key for key in dict_vars.keys()]
	
	def __init__(self, var:str, orientation:str='vertical', colorbar_type:str='normal', edge_color:str='k', colorblind:bool=False, resolution:int=300, aspect_ratio:int=10, label_orientation:str='right', font_size:int=30, font:str='Arial', font_style:str='bold', font_color:str='k', labels=None, psirange:list=[40, 180, 20]) -> None:
		if var not in type(self).list_vars:
			raise ValueError(f"Colorbar for var {var} is not available")
		data = type(self).dictvars.get(var)
		if colorbar_type not in data[0]:
			raise ValueError(f"Colorbar type {colorbar_type} for var {var} is not available")
		self.var = var
		self.colorbar_type = colorbar_type
		self.colormap = data[2][1] if colorblind else data[2][0]
        if colorbar_type.startswith('polar'):
			self.vmin, self.vmax = (0, 180) if colorbar_type == 'polar1' else (0, 90)
		else:
			self.vmin,  = 0
		self.edge_color = edge_color
		self.theta_zero_location = 'N' if colorbar_type == 'polar2' else 'E'
		self.theta_direction = -1 if colorbar_type == 'polar2' else 1
		self.orientation = orientation
		self.labels = labels
		self.font = [font, font_size, font_style, font_color]
		self.psirange = psirange
		self.var_range = 
		
	def plot_colorbar(self):
		fig, ax = plt.subplots()
		if self.colorbar_type.startswith('polar'):
			ax = plt.subplot(projection='polar')
			ax.set_theta_zero_location(self.theta_zero_location)
			ax.set_theta_direction(self.theta_direction)
			ax.set_thetamin(self.vmin)
			ax.set_thetamax(self.vmax)
		Nc = len(self.colormap)
		if self.var == 'Psi':
			psivec = np.linspace(*self.psirange)
			phi = np.ones((Nc, 1)) * psivec
			if self.orientation == 'vertical':
				phi = phi.T
			ax.pcolor(psivec, psivec, phi, shading='nearest', cmap=self.colormap, vmin=self.vmin, vmax=self.vmax)
                  

		plt.show()
            
c = colorbar; 
c.Limits = [psimin psimax];
c.Visible = 'off';
clim([40 180]);
shading flat
colormap(cmap);
set(gca, 'FontSize', font_size, 'FontName', font_type, 'Layer', 'top', 'TickLength', [0.013 0.035], ...
    'FontWeight', font_style,'color','none','XColor',font_color,'YColor',font_color);
set(gcf, 'color', 'none'); 
if orientation == 1
    set(gca, 'DataAspectRatio', [aspect_ratio, 1, 1], 'LineWidth', 2);
    set(gca, 'XTick', [], 'XTickLabels', [], 'YTick', psimin:psidelta:psimax);
    yt = get(gca,'YTick');
    for k = 1:numel(yt)
        yt1{k} = sprintf('%d°', yt(k));
    end
    if str2comp(labels, 'on')
        set(gca,'YTickLabel', yt1);
    else 
        set(gca,'YTickLabel', []);
    end
    if label_orientation == 2
        set(gca, 'YAxisLocation', 'right');
    end
else
    set(gca, 'DataAspectRatio', [1, aspect_ratio, 1], 'LineWidth', 2);
    set(gca, 'YTick', [], 'YTickLabels', [], 'XTick', psimin:psidelta:psimax);
    xt = get(gca,'XTick');
    for k = 1:numel(xt)
        xt1{k} = sprintf('%d°', xt(k));
    end
    set(gca,'XTickLabel', xt1);
    if label_orientation == 3
        set(gca, 'XAxisLocation', 'top');
    end
end