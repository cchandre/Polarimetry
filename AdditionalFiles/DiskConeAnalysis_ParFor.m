function DiskConeAnalysis_ParFor
%%
%% Last modified by Cristel Chandre (November 29, 2025)
%% Comments? cristel.chandre@cnrs.fr 
%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% parameters
params.dark = 480;
params.polardir = 'clockwise';      % 'clockwise' or 'anticlockwise'
params.offsetangle = 0;
excelfile = 'CD_Stats.xlsx';
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

waitfor(msgbox({'(1) Diskcone folder','(2) Stack folder'}, 'Instructions', 'help'));

%% get disk cone files
CD.folder = uigetdir;
CD.files = dir([CD.folder filesep '*.mat']);

%% get stack files
STfolder = uigetdir;
STfiles = dir([STfolder filesep '*.tiff']);

f = waitbar(0, 'Please wait...');
listCD = {};
if exist(excelfile, 'file')
    To = readtable(excelfile, 'ReadVariableNames', false);
    listCD = unique(To.Var1);
end

for itdc = 1:length(CD.files)
    Tdata = [];
    f = waitbar(double(itdc/length(CD.files)), f, ['Processing ' num2str(itdc) ' Diskcone file(s)...']);
    [~, CD.name, ~] = fileparts(char(CD.files(itdc).name));
    if strncmp(CD.files(itdc).name, 'Disk', 4) && ~ismember({matlab.lang.makeValidName(CD.name)}, listCD)
        [~, CD.name, ~] = fileparts(char(CD.files(itdc).name));
        load([CD.folder filesep CD.files(itdc).name], 'RoTest', 'PsiTest', 'NbMapValues');
        CD.RhoPsi = cat(3, double(RoTest), double(PsiTest));
        CD.NbMapValues = NbMapValues;
        parfor(itst = 1:length(STfiles))
            stack = OpenFile([STfolder filesep STfiles(itst).name]);
            [~, STname, ~] = fileparts(char(STfiles(itst).name));
            binarized = imread([STfolder filesep STname '.png']);
            mask = double(binarized/max(binarized(:)));
            results = PolarimetryAnalysis(stack, mask, CD, params);
            Tdata = [Tdata; [{matlab.lang.makeValidName(CD.name)} num2cell(itdc)...
                {matlab.lang.makeValidName(STname)} num2cell(results)... 
                num2cell(params.dark) num2cell(params.offsetangle) {params.polardir}]];
        end
        %% save to MS Excel
        T = array2table(Tdata,'VariableNames',...
            {'Calibration', 'Disk #', 'File', 'MeanRho', 'StdRho', 'MeanDeltaRho', 'MeanPsi', 'StdPsi', ...
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

function results = PolarimetryAnalysis(stack, mask, CD, params)
    
    chi2threshold = 500; % Define a threshold for chi-squared values
    [nangle, width, height] = size(stack);
    field = stack - params.dark;
    field(field < 0) = 0;
    polardir = 1 - 2*strcmp(params.polardir, 'clockwise');
 
    alpha = polardir * (0:nangle-1) * (180/nangle) + params.offsetangle;
    e2 = exp(2i * deg2rad(alpha));
    a0 = mean(field, 1);
    a0(a0 == 0) = NaN;
    a2 = 2 * mean(field .* e2, 1);
    field_fit = a0 + real(a2 .*conj(e2));
    a2 = divide_ext(a2, a0);
    valid = all(field_fit ~= 0 & isfinite(field_fit), 1);
    num = (field - field_fit).^2;
    safe_div = nan(size(field), 'like', field); 
    safe_div(valid) = num(valid) ./ field_fit(valid);
    chi2 = mean(safe_div, 1);
    mask = mask & all(field_fit > 0, 1) & (chi2 <= chi2threshold) & (chi2 > 0);
    a2_vals = [real(a2(mask)), imag(a2(mask))];
    a0(~mask) = NaN;

    x = linspace(-1, 1, CD.NbMapValues);
    CD.xy = {x, x};
    rhopsi = interpn(CD.xy{:}, CD.RhoPsi, a2_vals(:,1), a2_vals(:,2));
    rho = rhopsi(:,1);
    psi = rhopsi(:,2);
    ixgrid = find(mask);

    rho_values = nan(height, width); 
    psi_values = nan(height, width);
    rho_values(ixgrid) = rho;
    psi_values(ixgrid) = psi;
    finite_idx = isfinite(rho_values);
    rho_values(finite_idx) = mod(2 * rho_values(finite_idx), 360) / 2;
    mask = mask & isfinite(rho_values) & isfinite(psi_values);
    a0(~mask) = NaN;
   
    mean_rho = circularmean(rho_values);
    deltarho = wrapto180(2 * (rho_values - mean_rho)) / 2;
    mean_deltarho = mean(deltarho, 'all', 'omitnan');
    std_deltarho = std(deltarho, 0, 'all', 'omitnan');
    mean_psi = mean(psi_values, 'all', 'omitnan');
    std_psi = std(psi_values, 0, 'all', 'omitnan');
    mean_int = mean(a0, 'all', 'omitnan');
    std_int = std(a0, 0, 'all', 'omitnan');
    total_int = mean_int * nangle;
    N = numel(psi_values);
    results = [mean_psi, std_psi, mean_rho, std_rho, mean_deltarho,...
        std_deltarho, mean_int, std_int, total_int, N];
end

function result = divide_ext(a, b)
    result = nan(size(a), 'like', a);
    mask = (b ~= 0) & isfinite(b);
    result(mask) = a(mask) ./ b(mask);
end

function stack = OpenFile(filename)
    info = imfinfo(filename);
    nangle = numel(info);
    stack = zeros(nangle, info(1).Height, info(1).Width, 'double');
    t = Tiff(filename, 'r');
    for k = 1:nangle
        t.setDirectory(k);
        stack(k,:,:) = t.read();
    end
    t.close();
end

function mu = circularmean(rho)
    z = mean(exp(2i * deg2rad(rho)));
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
