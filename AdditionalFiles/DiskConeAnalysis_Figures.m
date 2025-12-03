function DiskConeAnalysis_Figures
%%
%% Last modified by Cristel Chandre (November 29, 2025)
%% Comments? cristel.chandre@cnrs.fr 
%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% parameters
DiskRange = 1:1:30;     % format: FirstDisk:DeltaDisk:LastDisk
klowest = 10;
output_file = "output";
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

close all
warning('OFF', 'MATLAB:table:ModifiedAndSavedVarnames')

[file, path] = uigetfile('*.xlsx');
T = readtable([path file], 'FileType', 'spreadsheet');
ListDC = unique(T.Calibration);
ListDCn = unique(T.DiskNumber);
ListDCn = ListDCn(ismember(ListDCn,DiskRange));

if isempty(ListDCn)
    disp('No Disk cones found in this range...');
    return
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Figure StdPsi
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% StdPsi function of Disk Cone
figure('Name', 'StdPsi function of Disk Cone');
Colors = colormap(hsv(length(ListDC)));
StdPsi = zeros(1,length(ListDC));
NameOfFile = cell(1,length(ListDC));
hold on
for it = 1:length(ListDC)
    T1 = T(T.DiskNumber == it,:);
    NameOfFile(it) = T1{1,1};
    StdPsi(it) = std(T1{:,8});
    s = plot(it, StdPsi(it), 'o', 'MarkerFaceColor', Colors(it,:), 'MarkerEdgeColor', Colors(it,:));
    s.DataTipTemplate.DataTipRows(end+1) = ['Disk Cone Name :  ' char(T1{1,1})];
    s.DataTipTemplate.Interpreter = 'none';
end
xlabel('Disk #', 'FontSize', 25);
ylabel('Std \psi', 'FontSize', 30);
% set(gca, 'XTick', 1:length(ListDC), 'XTickLabel', matlab.lang.makeValidName(ListDC),...
%     'XTickLabelRotation', 90, 'TickLabelInterpreter', 'none', 'Box', 'on');
set(gca, 'XTick', 1:length(ListDC), 'Box', 'on');
xlim([-0.1+1 length(ListDC)+0.1])
hold off

%% k-lowest StdPsi
[OStdPsi, Index] = sort(StdPsi);
LowIndex = Index(1:klowest);
fid = fopen(output_file + ".txt","w"); 
for it = 1:klowest
    disp(['StdPsi = ' num2str(OStdPsi(it))   '   # ' num2str(LowIndex(it))   '   file = ' char(NameOfFile(LowIndex(it)))])
    fprintf(fid, 'StdPsi = %g   # %d   file = %s\n', ...
        OStdPsi(it), LowIndex(it), char(NameOfFile(LowIndex(it))));
end
fclose(fid);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Figures for lowest StdPsi disks
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Psi function of Disk Cone
figure('Name', 'Psi function of Disk Cone');
Colors = colormap(hsv(length(ListDC)));
hold on
for it = 1:klowest
    T1 = T(T.DiskNumber == LowIndex(it),:);
    plot(it, T1{:,8}, 'o', 'MarkerFaceColor', Colors(LowIndex(it),:), 'MarkerEdgeColor', Colors(LowIndex(it),:));
end
xlabel('Disk #', 'FontSize', 25);
ylabel('\psi', 'FontSize', 30);
set(gca, 'XTick', 1:klowest, 'Box', 'on');
xlim([-0.1+1 klowest+0.1])
hold off

%% Rho function of Disk Cone
figure('Name', 'Rho function of Disk Cone');
Colors = colormap(hsv(length(ListDC)));
hold on
for it = 1:klowest
    T1 = T(T.DiskNumber == LowIndex(it),:);
    plot(it, T1{:,4}, 'o', 'MarkerFaceColor', Colors(LowIndex(it),:), 'MarkerEdgeColor', Colors(LowIndex(it),:));
end
xlabel('Disk #', 'FontSize', 25);
ylabel('\rho', 'FontSize', 30);
set(gca, 'XTick', 1:klowest, 'Box', 'on');
xlim([-0.1+1 klowest+0.1])
hold off

%% Psi function of Rho
figure('Name', 'Psi function of Rho');
hold on
for it = 1:klowest
    T1 = T(T.DiskNumber == LowIndex(it),:);
    [Rho, I] = sort(T1{:,4});
    Psi = T1{I,7};
    s = plot(Rho, Psi, '-o', 'LineWidth', 2, 'Color', Colors(LowIndex(it),:), 'MarkerFaceColor', Colors(LowIndex(it),:), 'MarkerEdgeColor', Colors(LowIndex(it),:));
    s.DataTipTemplate.DataTipRows(end+1) = ['Disk Cone ' num2str(LowIndex(it))];
end
xlabel('\rho', 'FontSize', 30);
ylabel('\psi', 'FontSize', 30);
set(gca, 'Box', 'on');
hold off

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Figures for DiskMin:DiskDelta:DiskMax disks
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% %% Psi function of Disk Cone
% figure('Name', 'Psi function of Disk Cone');
% Colors = colormap(hsv(length(ListDC)));
% hold on
% for it = ListDCn'
%     T1 = T(T.Disk_ == it,:);
%     plot(it, T1{:,7}, 'o', 'MarkerFaceColor', Colors(it,:), 'MarkerEdgeColor', Colors(it,:));
% end
% xlabel('Disk #', 'FontSize', 25);
% ylabel('\psi', 'FontSize', 30);
% % set(gca, 'XTick', 1:length(ListDC), 'XTickLabel', matlab.lang.makeValidName(ListDC),...
% %     'XTickLabelRotation', 90, 'TickLabelInterpreter', 'none', 'Box', 'on');
% set(gca, 'XTick', ListDCn, 'Box', 'on');
% xlim([-0.1+min(ListDCn) max(ListDCn)+0.1])
% hold off
% 
% %% Rho function of Disk Cone
% figure('Name', 'Rho function of Disk Cone');
% Colors = colormap(hsv(length(ListDC)));
% hold on
% for it = ListDCn'
%     T1 = T(T.Disk_ == it,:);
%     plot(it, T1{:,4}, 'o', 'MarkerFaceColor', Colors(it,:), 'MarkerEdgeColor', Colors(it,:));
% end
% xlabel('Disk #', 'FontSize', 25);
% ylabel('\rho', 'FontSize', 30);
% % set(gca, 'XTick', 1:length(ListDC), 'XTickLabel', matlab.lang.makeValidName(ListDC),...
% %     'XTickLabelRotation', 90, 'TickLabelInterpreter', 'none', 'Box', 'on');
% set(gca, 'XTick', ListDCn, 'Box', 'on');
% xlim([-0.1+min(ListDCn) max(ListDCn)+0.1])
% hold off
% 
% %% Psi function of Rho
% figure('Name', 'Psi function of Rho');
% hold on
% for it = ListDCn'
%     T1 = T(T.Disk_ == it,:);
%     [Rho, I] = sort(T1{:,4});
%     Psi = T1{I,7};
%     s = plot(Rho, Psi, '-o', 'LineWidth', 2, 'Color', Colors(it,:), 'MarkerFaceColor', Colors(it,:), 'MarkerEdgeColor', Colors(it,:));
%     s.DataTipTemplate.DataTipRows(end+1) = ['Disk Cone ' num2str(it)];
% end
% xlabel('\rho', 'FontSize', 30);
% ylabel('\psi', 'FontSize', 30);
% set(gca, 'Box', 'on');
% hold off

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
