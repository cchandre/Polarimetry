function ShiftedHisto
%%
%% Last modified by Cristel Chandre (July 18, 2020)
%% Comments? cristel.chandre@univ-amu.fr 
%%

[file, filepath] = uigetfile('*.mat');
[~,name,~] = fileparts([filepath file]);
load([filepath file], 'Rho');
prompt = {'Enter angle value:'};
dlgtitle = 'Input';
dims = [1 20];
definput = {'0'};
answer = inputdlg(prompt,dlgtitle,dims,definput);
rho_val = str2double(answer{1}); % ring axis angle
DiffRho =wrapTo360(2*(Rho-rho_val))/2;

%% Shifted Polar Histogram Rho (0-180)
avgRho = mean(DiffRho);
figPolarHisto180 = figure('Name', 'Polar Histogram (0-180)');
pax = polaraxes;
polarhistogram(pax, DiffRho*pi/180, (0:3:180)*pi/180);
pax.ThetaDir = 'clockwise';
pax.ThetaLim = [0 180];
pax.ThetaZeroLocation = 'left';
annotation(figPolarHisto180, 'textbox', [0.22 1 0 0], 'String', name, 'LineStyle', 'none', 'FontSize', 14, 'FitBoxToText', 'on', 'Interpreter', 'none');
annotation(figPolarHisto180, 'textbox', [0.6 0.91 0 0], 'String', ['\rho - \rho_0 = ' num2str(avgRho, '%.1f') '\pm' num2str(std(DiffRho), '%.1f')], 'LineStyle', 'none', 'FontSize', 14, 'FitBoxToText', 'on');

savefig(figPolarHisto180, [filepath name '_ShiftedPolarHistoRho180.fig']);
save([filepath name '_ShiftedHistoRho180.mat'], 'DiffRho');

%% Shifted Polar Histogram Rho (0-90)
Rho_t(DiffRho<=90) = DiffRho(DiffRho<=90);
Rho_t(DiffRho>=90) = 180-DiffRho(DiffRho>=90);
avgRho = mean(Rho_t);
figPolarHisto90 = figure('Name', 'Polar Histogram (0-90)');
pax = polaraxes;
polarhistogram(pax, Rho_t*pi/180, (0:3:90)*pi/180);
pax.ThetaDir = 'clockwise';
pax.ThetaLim = [0 90];
pax.ThetaZeroLocation = 'left';
annotation(figPolarHisto90, 'textbox', [0.22 1 0 0], 'String', name, 'LineStyle', 'none', 'FontSize', 14, 'FitBoxToText', 'on', 'Interpreter', 'none');
annotation(figPolarHisto90, 'textbox', [0.6 0.91 0 0], 'String', ['\rho - \rho_0 = ' num2str(avgRho, '%.1f') '\pm' num2str(std(Rho_t), '%.1f')], 'LineStyle', 'none', 'FontSize', 14, 'FitBoxToText', 'on');

savefig(figPolarHisto90, [filepath name '_ShiftedPolarHistoRho90.fig']);
save([filepath name '_ShiftedHistoRho90.mat'], 'Rho_t');

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
