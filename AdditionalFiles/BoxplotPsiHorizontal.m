function BoxplotPsiHorizontal
%%
%% Last modified by Cristel Chandre (May 8, 2021)
%% Comments? cristel.chandre@cnrs.fr 
%%

psiminaxis = 100;
psimaxaxis = 180;
psimincolorbar = 40;
psimaxcolorbar = 180;
scatter_in_color_psi = true;
scatter_in_color_cell = false;

boxplot_aspect_ratio = 24; % number of boxplots for 1:1 aspect ratio
width = 0.7; % affects the spacing between boxplots
width_scatter = 0.1; % changes the width of scatter plots per boxplot

[filename, path] = uigetfile('*.xlsx');
T = readtable([path filename]);
X = table2array(T(:, 2:2:end));
name_fics = table2cell(T(:, 1:2:end));
name_fics = name_fics(cellfun('isclass', name_fics, 'char'));
Nc = eraseBetween(name_fics, 1, 'cell', 'Boundaries', 'inclusive');
Nc = str2double(Nc);
nbr_cells = length(unique(Nc(~isnan(Nc(:)))));
label_cells = randperm(nbr_cells);
for itcell = 1:nbr_cells
    Nc(Nc==itcell) = label_cells(itcell);
end

name_boxes = char(T.Properties.VariableNames(2:2:end));
number_boxes = numel(X(1,:));

close all
figure, hold on
for it = 1:number_boxes
    x = it + (rand(size(X(:, it)))-0.5) * width_scatter;
    if scatter_in_color_psi
        f = scatter(X(:, it), x, [], X(:, it), 'filled', 'MarkerEdgeColor', 'k'); f.MarkerFaceAlpha = 0.5;
    elseif scatter_in_color_cell
        f = scatter(X(:, it), x, [], Nc(:, it), 'filled', 'MarkerEdgeColor', 'k'); f.MarkerFaceAlpha = 0.5;
    else
        f = scatter(X(:, it), x, [], 'k', 'filled'); f.MarkerFaceAlpha = 0.5;
    end
    vecdim(it) = sum(~isnan(X(:, it)));
end
hc = boxplot(X, name_boxes, 'Notch', 'off', 'BoxStyle', 'outline', 'Colors', 'k', 'Symbol', 'kx', 'orientation', 'horizontal', 'Widths', width);
set(hc, 'LineWidth', 2)
set(gca, 'YTickLabel', name_boxes, 'FontSize', 25, 'FontName', 'Arial')
bx = findobj('Tag', 'boxplot');
set(bx.Children(end-2*number_boxes:end), 'LineStyle', '-')
xlim([psiminaxis psimaxaxis])
xticks(psiminaxis:20:psimaxaxis)
if scatter_in_color_psi 
    colormap('jet')
    c = colorbar;
    caxis([psimincolorbar psimaxcolorbar])
    c.Visible = 'off';
elseif scatter_in_color_cell
    colormap(hsv(nbr_cells))
end
set(gca, 'Box', 'off', 'LineWidth', 2, 'YDir', 'reverse')
pbaspect([1 number_boxes/boxplot_aspect_ratio 1])
disp(vecdim)

% The data (.mat, .fig, .xlsx) used in this code are produced using the 
% software Polarimetry Analysis https://www.fresnel.fr/polarimetry/
%
% Copyright (c) 2020 Cristel Chandre.
% All rights reserved.
%
% Redistribution and use in source and binary forms are permitted provided 
% that the above copyright notice and this paragraph are duplicated in all 
% such forms and that any documentation, advertising materials, and other 
% materials related to such distribution and use acknowledge that the
% software was developed by the CNRS. The name of the CNRS may not be used 
% to endorse or promote products derived from this software without 
% specific prior written permission.

% THIS SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED 
% WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF 
% MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
