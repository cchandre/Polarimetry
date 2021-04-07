function BoxplotPsiHorizontal
%%
%% Last modified by Cristel Chandre (April 7, 2021)
%% Comments? cristel.chandre@univ-amu.fr 
%%

psiminaxis = 100;
psimaxaxis = 180;
psimincolorbar = 40;
psimaxcolorbar = 180;
scatter_in_color_psi = false;
scatter_in_color_cell = true;

width = 0.7; % affects the spacing between boxplots

[filename, path] = uigetfile('*.xlsx');
T = readtable([path filename]);
X = table2array(T(:, 2:2:end));
Nc = eraseBetween(table2array(T(:, 1:2:end)), 1, 'cell', 'Boundaries', 'inclusive');
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
hc = boxplot(X, name_boxes, 'Notch', 'off', 'BoxStyle', 'outline', 'Colors', 'k', 'Symbol', 'kx', 'orientation', 'horizontal', 'Widths', width);
set(hc, 'LineWidth', 2)
set(gca, 'YTickLabel', name_boxes, 'FontSize', 25, 'FontName', 'Arial')
bx = findobj('Tag', 'boxplot');
set(bx.Children(end-2*number_boxes:end), 'LineStyle', '-')
for it = 1:number_boxes
    x = it + (rand(size(X(:, it)))-0.5)/10;
    if scatter_in_color_psi
        f = scatter(X(:, it), x, [], X(:, it), 'filled', 'MarkerEdgeColor', 'k'); f.MarkerFaceAlpha = 0.5;
    elseif scatter_in_color_cell
        f = scatter(X(:, it), x, [], Nc(:, it), 'filled', 'MarkerEdgeColor', 'k'); f.MarkerFaceAlpha = 0.5;
    else
        f = scatter(X(:, it), x, [], 'k', 'filled'); f.MarkerFaceAlpha = 0.5;
    end
    vecdim(it) = sum(~isnan(X(:, it)));
end
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
pbaspect([1 number_boxes/24 1])
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
