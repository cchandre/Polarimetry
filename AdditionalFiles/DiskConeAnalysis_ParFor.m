function DiskConeAnalysis_ParFor
%%
%% Last modified by Cristel Chandre (December 2, 2025)
%% Comments? cristel.chandre@cnrs.fr 
%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% parameters
params.dark = 480;
params.polardir = 'anticlockwise';      % 'clockwise' or 'anticlockwise'
params.offsetangle = 0;
excelfile = 'CD_Stats.xlsx';
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

waitfor(msgbox({'(1) Diskcone folder','(2) Stack folder'}, 'Instructions', 'help'));

%% get disk cone files
disk.folder = uigetdir;
disk.files = dir([disk.folder filesep '*.mat']);

%% get stack files
folder = uigetdir;
files = dir([folder filesep '*.tiff']);

f = waitbar(0, 'Please wait...');
disk.list = {};
if exist(excelfile, 'file')
    To = readtable(excelfile, 'ReadVariableNames', false);
    disk.list = unique(To.Var1);
end

for itdc = 1:length(disk.files)
    Tdata = [];
    f = waitbar(double(itdc/length(disk.files)), f, ['Processing ' num2str(itdc) ' Diskcone file(s)...']);
    [~, disk.name, ~] = fileparts(char(disk.files(itdc).name));
    if strncmp(disk.files(itdc).name, 'Disk', 4) && ~ismember({matlab.lang.makeValidName(disk.name)}, disk.list)
        [~, disk.name, ~] = fileparts(char(disk.files(itdc).name));
        load([disk.folder filesep disk.files(itdc).name], 'RoTest', 'PsiTest', 'NbMapValues');
        disk.rhopsi = cat(3, double(RoTest), double(PsiTest));
        disk.nb = NbMapValues;
        parfor(itst = 1:length(files))
            stack = OpenFile([folder filesep files(itst).name]);
            [~, name, ~] = fileparts(char(files(itst).name));
            mask = imbinarize(imread([folder filesep name '.png']), 0.5);
            results = PolarimetryAnalysis(stack, mask, disk, params);
            Tdata = [Tdata; [{matlab.lang.makeValidName(disk.name)} num2cell(itdc)...
                {matlab.lang.makeValidName(name)} num2cell(results)... 
                num2cell(params.dark) num2cell(params.offsetangle) {params.polardir}]];
        end
        %% save to MS Excel
        T = array2table(Tdata,'VariableNames',...
            {'Calibration', 'DiskNumber', 'File', 'MeanRho', 'StdRho', 'MeanDeltaRho', 'MeanPsi', 'StdPsi',...
            'MeanInt', 'StdInt', 'TotalInt', 'N', 'dark', 'offset', 'polarization'});
        if itdc==1
            writetable(T, excelfile, 'Sheet', 1, 'WriteRowNames', true);
        else
            writetable(T, excelfile, 'Sheet', 1, 'WriteMode', 'Append',...
                'WriteVariableNames', false, 'WriteRowNames', true);
        end
    end
end
close(f);
end

function results = PolarimetryAnalysis(stack, mask, disk, params)
    
    chi2threshold = 500;    % Define a threshold for chi-squared values
    [nangle, width, height] = size(stack);
    field = stack - params.dark;
    field(field < 0) = 0;
    polardir = 1 - 2*strcmp(params.polardir, 'clockwise');
 
    alpha = polardir * (0:nangle-1) * (180/nangle) + params.offsetangle;
    e2 = exp(2i * deg2rad(alpha));
    a0 = mean(field, 1);
    a2 = 2 * mean(field .* reshape(e2, [nangle,1,1]), 1);
    field_fit = reshape(a0, [1,width,height])...
		+ real(reshape(a2, [1,width,height]) .* conj(reshape(e2, [nangle,1,1])));
    chi2 = squeeze(mean((field - field_fit).^2 ./ field_fit, 1));
    mask = mask & squeeze(all(field_fit > 0, 1)) & (chi2 <= chi2threshold) & (chi2 > 0);
    a2 = a2 ./ a0;
    a2_vals = [real(a2(mask)), imag(a2(mask))];

    x = linspace(-1, 1, disk.nb);
    rhopsi = interpn(x, x, disk.rhopsi, a2_vals(:,1), a2_vals(:,2));
    rho = rhopsi(:,1);
    psi = rhopsi(:,2);

    rho_values = nan(width, height); 
    psi_values = nan(width, height);
	ixgrid = find(mask);
    rho_values(ixgrid) = mod(2 * rho, 360) / 2;
    psi_values(ixgrid) = psi;
    mask = mask & isfinite(rho_values) & isfinite(psi_values);
   
    mean_rho = circularmean(rho_values(mask), 'all');
    deltarho = wrapTo180(2 * (rho_values(mask) - mean_rho)) / 2;
    mean_deltarho = mean(deltarho, 'all');
    std_deltarho = std(deltarho, 0, 'all');
    mean_psi = mean(psi_values(mask), 'all');
    std_psi = std(psi_values(mask), 0, 'all');
    mean_int = mean(a0(mask), 'all');
    std_int = std(a0(mask), 0, 'all');
    results = [mean_rho, std_deltarho, mean_deltarho, mean_psi, std_psi, ...
        mean_int, std_int, mean_int * nangle, numel(psi_values(mask))];
end

function stack = OpenFile(filename)
    info = imfinfo(filename);
    nangle = numel(info);
    stack = zeros(nangle, info(1).Height, info(1).Width, 'double');
    t = Tiff(filename, 'r');
    for k = 1:nangle
        t.setDirectory(k);
        stack(k,:,:) = double(t.read());
    end
    t.close();
end

function mu = circularmean(rho, dim)
    z = mean(exp(2i * deg2rad(rho)), dim);
    mu = mod(rad2deg(angle(z)), 360) / 2;
end

% This code is part of the PyPOLAR project:
%   https://www.fresnel.fr/polarimetry/
%
% Copyright (c) 2025 Cristel Chandre.
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
