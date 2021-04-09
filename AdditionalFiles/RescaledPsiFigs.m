function RescaledPsiFigs
%%
%% Last modified by Cristel Chandre (April 9, 2021)
%% Comments? cristel.chandre@univ-amu.fr 
%%

psimin = 60;

Folder = uigetdir;
files = dir([Folder filesep '*_PsiSticks.fig']);

for it = 1:length(files)
    [~, name, ~] = fileparts(files(it).name);
    openfig([Folder filesep files(it).name]);
    caxis([psimin 180]);
    savefig(gcf, [Folder filesep name 'Rescaled' num2str(psimin) '.fig'])
    close(gcf)
end

% The data (.mat, .fig) used in this code are produced using the software
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
