function DiskConeAnalysis_ParFor 
%%
%% Last modified by Cristel Chandre (April 5, 2022)
%% Comments? cristel.chandre@cnrs.fr 
%%

waitfor(msgbox({'(1) Disk Cone folder','(2) Stack folder'},'Instructions','help'));

%% Get DiskCone files
DC.Folder = uigetdir;
DC.files = dir([DC.Folder filesep '*.mat']);

%% Get STack files
STFolder = uigetdir;
STfiles = dir([STFolder filesep '*.tiff']);

f = waitbar(0,'Please wait...');
ListDC = {};
if exist('DC_Stats.xlsx','file')
    To = readtable('DC_Stats.xlsx','ReadVariableNames',false);
    ListDC = unique(To.Var1);
end

for itdc = 1:length(DC.files)
    Tdata = [];
    f = waitbar(double(itdc/length(DC.files)),f,['Processing ' num2str(itdc) ' Disk Cone file(s)...']);
    [~,DC.Name,~] = fileparts(char(DC.files(itdc).name));
    if strncmp(DC.files(itdc).name,'Disk',4) && ~ismember({matlab.lang.makeValidName(DC.Name)},ListDC)
        [~,DC.Name,~] = fileparts(char(DC.files(itdc).name));
        load([DC.Folder filesep DC.files(itdc).name],'RoTest','PsiTest','NbMapValues');
        DC.RoTest = double(RoTest);
        DC.PsiTest = double(PsiTest);
        DC.NbMapValues = NbMapValues;
        parfor(itst = 1:length(STfiles))
            Im = OpenFile([STFolder filesep STfiles(itst).name]);
            [~,STName,~] = fileparts(char(STfiles(itst).name));
            BinarizedIm = imread([STFolder filesep STName '.png']);
            Mask = double(BinarizedIm/max(BinarizedIm(:)));
            Results = PolarimetryAnalysis(Im,Mask,DC);
            Tdata = [Tdata; [{matlab.lang.makeValidName(DC.Name)} num2cell(Results) {matlab.lang.makeValidName(STName)} num2cell(itdc)]];
        end
        %% Saving to Microsoft Excel
        if itdc==1
            T = array2table(Tdata,'VariableNames',...
                {'Disk Cone','MeanPsi','StdPsi','MeanRho','StdRho','MeanDeltaRho','MeanInt','StdInt','TotalInt','N','Stack','Disk #'});
            writetable(T,'DC_Stats.xlsx','Sheet',1,'WriteRowNames',true);
        else
            T = array2table(Tdata,'VariableNames',...
                {'Disk Cone','MeanPsi','StdPsi','MeanRho','StdRho','MeanDeltaRho','MeanInt','StdInt','TotalInt','N','Stack','Disk #'});
            writetable(T,'DC_Stats.xlsx','Sheet',1,'WriteMode','Append','WriteVariableNames',false,'WriteRowNames',true);
        end
    end
end
close(f);

function Results = PolarimetryAnalysis(Im, Mask, DC)
    %% Parameters
    Chi2Threshold = 500; 
    Dark = 480;
    OffsetAngleDeg = 100;
    %% Data analysis
    [~,~,ImageAngle] = size(Im);
    Angle1D = linspace(0,pi,ImageAngle+1)+OffsetAngleDeg*pi/180;
    Angle3D = reshape(Angle1D,1,1,[]);
    E2 = exp(2i*Angle3D);
    Im_rel = (Im-Dark).*(Im>=Dark);
    field = padarray(Im_rel,[0 0 1],'circular','post');
    A0 = trapz(Angle1D,field,3)/pi;
    A2 = 2*trapz(Angle1D,field.*E2,3)/pi;
    field_fit = A0+real(A2.*conj(E2));
    Chi2 = mean((field-field_fit).^2./field_fit,3);
    A2n = real(A2)./A0;
    B2n = imag(A2)./A0;
    [X,Y] = find((Mask~=0).*(abs(A2n)<1).*(abs(B2n)<1).*(Chi2<=Chi2Threshold).*(Chi2>0));
    ind = sub2ind(size(A0),X,Y);
    Int = A0(ind);
    Rho_DC = DC.RoTest(sub2ind(size(DC.RoTest), 1+round((A2n(ind)+1)*(DC.NbMapValues-1)/2),...
        1+round((B2n(ind)+1)*(DC.NbMapValues-1)/2)));
    Psi_DC = DC.PsiTest(sub2ind(size(DC.RoTest), 1+round((A2n(ind)+1)*(DC.NbMapValues-1)/2),...
        1+round((B2n(ind)+1)*(DC.NbMapValues-1)/2)));
    Filter = find((~isnan(Rho_DC))&(~isnan(Psi_DC)));
    Rho = wrapTo360(2*(Rho_DC(Filter)+90))/2;
    Psi = Psi_DC(Filter);
    MeanInt = mean(Int);
    TotalInt = MeanInt*ImageAngle;
    StdInt = std(Int);
    avgCRho = mean(exp(-2i*Rho*pi/180));
    meanCangle = wrapTo2Pi(2*(pi-angle(avgCRho)/2))/2;
    DeltaRho = Rho-meanCangle*180/pi;
    DeltaRho = wrapTo360(2*DeltaRho)/2;
    MeanDeltaRho = mean(DeltaRho);
    MeanRho = wrapTo360(2*meanCangle*180/pi)/2;
    StdRho = std(DeltaRho);
    MeanPsi = mean(Psi);
    StdPsi = std(Psi);
    N = numel(Rho);
    Results = [MeanPsi, StdPsi, MeanRho, StdRho, MeanDeltaRho, MeanInt, StdInt, TotalInt, N];

function Im = OpenFile(filename)
    info = imfinfo(filename);
    nangle = numel(info);
    Im = zeros(info(1).Height,info(1).Width,nangle,'double');
    TifLink = Tiff(filename,'r');
    for k = 1:nangle
       TifLink.setDirectory(k);
       Im(:,:,k) = TifLink.read();
    end
    TifLink.close();

%
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
