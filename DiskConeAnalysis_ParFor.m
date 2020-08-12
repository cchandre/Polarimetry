function DiskConeAnalysis_ParFor 
%%
%% Last modified by Cristel Chandre (June 4, 2020)
%% Comments? cristel.chandre@univ-amu.fr 
%%

nproc = 4; % Number of processors to be used

waitfor(msgbox({'(1) Disk Cone folder','(2) Stack folder'}, 'Instructions', 'help'));

%% Get DiskCone files
DC.Folder = uigetdir;
DC.files = dir([DC.Folder filesep '*.mat']);

%% Get STack files
STFolder = uigetdir;
STfiles = dir([STFolder filesep '*.tiff']);

f = waitbar(0, 'Please wait...');
ListDC = {};
if exist('DC_Stats.xlsx', 'file')
    To = readtable('DC_Stats.xlsx', 'ReadVariableNames', false);
    ListDC = unique(To.Var1);
end

for itdc = 1:length(DC.files)
    Tdata = [];
    f = waitbar(double(itdc/length(DC.files)), f, ['Processing ' num2str(itdc) ' Disk Cone file(s)...']);
    [~, DC.Name, ~] = fileparts(char(DC.files(itdc).name));
    if strncmp(DC.files(itdc).name, 'Disk', 4) && ~ismember({matlab.lang.makeValidName(DC.Name)}, ListDC)
        [~, DC.Name, ~] = fileparts(char(DC.files(itdc).name));
        load([DC.Folder filesep DC.files(itdc).name], 'RoTest', 'PsiTest', 'NbMapValues');
        DC.RoTest = double(RoTest);
        DC.PsiTest = double(PsiTest);
        DC.NbMapValues = NbMapValues;
        parfor(itst = 1:length(STfiles), nproc)
            Im = OpenFile([STFolder filesep STfiles(itst).name]);
            [~, STName, ~] = fileparts(char(STfiles(itst).name));
            BinarizedIm = imread([STFolder filesep STName '.png']);
            Mask = double(BinarizedIm/max(BinarizedIm(:)));
            Results = PolarimetryAnalysis(Im, Mask, DC);
            Tdata = [Tdata; [{matlab.lang.makeValidName(DC.Name)} num2cell(Results) {matlab.lang.makeValidName(STName)} num2cell(itdc)]];
        end
        %% Saving to Microsoft Excel
        if itdc==1
            T = array2table(Tdata,'VariableNames',...
                {'Disk Cone', 'MeanPsi', 'StdPsi', 'MeanRho', 'StdRho', 'MeanDeltaRho', 'MeanInt', 'StdInt','TotalInt', 'N', 'Stack', 'Disk #'});
            writetable(T, 'DC_Stats.xlsx', 'Sheet', 1, 'WriteRowNames', true);
        else
            T = array2table(Tdata,'VariableNames',...
                {'Disk Cone', 'MeanPsi', 'StdPsi', 'MeanRho', 'StdRho', 'MeanDeltaRho', 'MeanInt', 'StdInt','TotalInt', 'N', 'Stack', 'Disk #'});
            writetable(T, 'DC_Stats.xlsx', 'Sheet', 1, 'WriteMode', 'Append', 'WriteVariableNames', false, 'WriteRowNames', true);
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
    [ImageWidth, ImageHeight, ImageAngle] = size(Im);
    Angle_deg = (0:ImageAngle-1)/ImageAngle*180;
    Angle_rad = Angle_deg*pi/180;
    OffsetAngle_rad = OffsetAngleDeg*pi/180;
    Angle3D = permute(repmat(Angle_rad+OffsetAngle_rad, [ImageWidth 1 ImageHeight]), [1 3 2]);
    C2 = cos(2*Angle3D);
    S2 = sin(2*Angle3D);
    Im_cor = Im-Dark;
    TheStack = Im_cor.*(Im_cor>=0); 
    A0Map = mean(TheStack, 3);
    A2Map = 2*mean(TheStack.*C2, 3)./A0Map;
    B2Map = 2*mean(TheStack.*S2, 3)./A0Map;
    TheFitStack = repmat(A0Map, [1 1 ImageAngle]).*(1+repmat(A2Map, [1 1 ImageAngle]).*C2...
            + repmat(B2Map, [1 1 ImageAngle]).*S2);
    Chi2Map = mean((TheStack-TheFitStack).^2./TheFitStack, 3);
    [X_center, Y_center] = find((Mask~=0).*(A2Map<1).*(A2Map>-1).*(B2Map<1).*(B2Map>-1).*...
        (Chi2Map<=Chi2Threshold).*(Chi2Map>0));
    Rho = DC.RoTest(sub2ind(size(DC.RoTest), 1+round((A2Map(sub2ind(size(A2Map), X_center,Y_center))+1)*(DC.NbMapValues-1)/2),...
            1+round((B2Map(sub2ind(size(B2Map),X_center,Y_center))+1)*(DC.NbMapValues-1)/2)));
    Psi = DC.PsiTest(sub2ind(size(DC.RoTest), 1+round((A2Map(sub2ind(size(A2Map), X_center,Y_center))+1)*(DC.NbMapValues-1)/2),...
            1+round((B2Map(sub2ind(size(B2Map),X_center,Y_center))+1)*(DC.NbMapValues-1)/2)));    
    Intensity = A0Map(sub2ind(size(A0Map), X_center, Y_center));
    Filter = find((~isnan(Rho))&(~isnan(Psi)));
    Rho_Filt = wrapTo360(2*(Rho(Filter)+90))/2;
    Psi_Filt = Psi(Filter);
    Int_Filt = Intensity(Filter);
    MeanInt = mean(Int_Filt);
    TotalInt = MeanInt*ImageAngle;
    StdInt = std(Int_Filt);
    MeanPsi = mean(Psi_Filt);
    StdPsi = std(Psi_Filt);
    avgCRho = mean(exp(-2i*wrapTo360(2*Rho_Filt)/2*pi/180));
    meanCangle = wrapTo360(2*(180-angle(avgCRho)*180/pi/2))/2;
    DeltaRho = wrapTo360(2*Rho_Filt)/2 - meanCangle;
    DeltaRho = wrapTo180(2*DeltaRho)/2;
    MeanDeltaRho = mean(DeltaRho);
    MeanRho = wrapTo360(2*meanCangle)/2;
    StdRho = std(DeltaRho);
    N = numel(Psi_Filt);
    Results = [MeanPsi, StdPsi, MeanRho, StdRho, MeanDeltaRho, MeanInt, StdInt, TotalInt, N];

function Im = OpenFile(filename)
    info = imfinfo(filename);
    nangle = numel(info);
    Im = zeros(info(1).Height, info(1).Width, nangle, 'double');
    TifLink = Tiff(filename, 'r');
    for k = 1:nangle
       TifLink.setDirectory(k);
       Im(:,:,k) = TifLink.read();
    end
    TifLink.close();
