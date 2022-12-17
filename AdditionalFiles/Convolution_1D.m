function Convolution_1D
%%
%% Last modified by Cristel Chandre (December 7, 2021)
%% Comments? cristel.chandre@cnrs.fr 
%%

psf = 105;
min_fiber = 10;
max_fiber = 350;
step_fiber = 1;

sig = psf/(2*sqrt(2*log(2)));
mu = 500;
x = -1000:1000;
PSF = exp(-(x-mu).^2/(2*sig.^2))/exp(-1/(2*sig.^2));
diam = min_fiber:step_fiber:max_fiber;
allsizeIMAGE = zeros(1,length(diam));
for it = 1:length(diam)
    fiber = rectangularPulse(-diam(it)/2,diam(it)/2,x);
    image = conv(fiber,PSF)/diam(it);
    [~,~,allsizeIMAGE(it),~] = findpeaks(image);
end
figure
p = plot(diam,allsizeIMAGE,'k','Linewidth',2);
box off
set(gca,'linewidth',2)
%xlabel('fiber diameter (nm)');  
%ylabel('image diameter (nm)'); 
savefig('convolution.fig');
p.DataTipTemplate.DataTipRows(1).Label = 'fiber';
p.DataTipTemplate.DataTipRows(2).Label = 'image';

%
% Copyright (c) 2021 CNRS.
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