function PsiColorbar
%%
%% Last modified by Cristel Chandre (March 25, 2021)
%% Comments? cristel.chandre@cnrs.fr 
%%

psimin = 80;
psimax = 180;

close all
[file, path] = uigetfile('*.fig');
openfig([path file], 'visible');

c = colorbar;
c.Limits = [psimin psimax];

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
