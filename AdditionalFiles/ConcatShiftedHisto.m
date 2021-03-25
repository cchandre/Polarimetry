function ConcatShiftedHisto
%%
%% Last modified by Cristel Chandre (April 10, 2020)
%% Comments? cristel.chandre@univ-amu.fr 
%%

Folder = uigetdir;
[~, name] = fileparts(Folder);
files = dir([Folder filesep '*.mat']);

Rho_t_cat = [];
for it = 1:length(files)
    load([Folder filesep files(it).name], 'Rho_t'); 
    Rho_t_cat = [Rho_t_cat; Rho_t(:)];
end
    
%% Concatenated Shifted Polar Histogram Rho (0-90)
avgRho = mean(Rho_t_cat);
figPolarHistoRhoT = figure('Name', 'Polar Histogram (0-90): shifted Rho');
pax = polaraxes(figPolarHistoRhoT);
polarhistogram(pax, Rho_t_cat*pi/180, (0:3:90)*pi/180);
pax.ThetaDir = 'clockwise';
pax.ThetaLim = [0 90];
pax.ThetaZeroLocation = 'left';
annotation(figPolarHistoRhoT, 'textbox', [0.12 0.99 0 0], 'String', name, 'LineStyle', 'none', 'FontSize', 14, 'FitBoxToText', 'on', 'Interpreter', 'none');
annotation(figPolarHistoRhoT, 'textbox', [0.65 0.99 0 0], 'String', ['\rho - \rho_0 = ' num2str(avgRho, '%.1f') '\pm' num2str(std(Rho_t_cat), '%.1f')], 'LineStyle', 'none', 'FontSize', 14, 'FitBoxToText', 'on');

savefig(figPolarHistoRhoT, [Folder filesep name '_ConcatShiftedPolarHistoRho90.fig']);
save([Folder filesep name '_ConcatShiftedHistoRho90.mat'], 'Rho_t_cat');

% The data (.mat) used in this code are produced using the software
% Polarimetry Analysis https://www.fresnel.fr/polarimetry/
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