function registration_temp
close all
[filename, path] = uigetfile('*.tif','*.tiff');

info = imfinfo([path filename]);
nangle = numel(info);
Stack.Values = zeros(info(1).Height,info(1).Width,nangle,'double');
Stack.Height = info(1).Height;
Stack.Width = info(1).Width;
Stack.nangle = nangle;
TifLink = Tiff([path filename],'r');
for k = 1:nangle
    TifLink.setDirectory(k);
    Stack.Values(:,:,k) = TifLink.read();
end
TifLink.close();

%% Computation of the Dark value
SizeCell = 20;
NCellHeight = floor(Stack.Height/SizeCell);
NCellWidth = floor(Stack.Width/SizeCell);
Ncol = SizeCell*ones(1,NCellWidth);
Nrow = SizeCell*ones(1,NCellHeight);
cropIm = Stack.Values(1:SizeCell*NCellHeight,1:SizeCell*NCellWidth,1:Stack.nangle);
ImCG = mat2cell(cropIm,Nrow,Ncol,Stack.nangle);
mImCG = zeros(NCellHeight,NCellWidth);
for it = 1:NCellHeight
    for jt = 1:NCellWidth
        CellInd = ImCG{it,jt}(:,:,1);
        mImCG(it,jt) = mean(CellInd(CellInd~=0));
    end
end
val = min(mImCG,[],'all');
[IndI, IndJ] = find(mImCG==val);
CellInd = ImCG{IndI,IndJ};
Dark = mean(CellInd(CellInd~=0));
Itot = sum((Stack.Values-Dark).*(Stack.Values>=Dark),3);

%% Dowdload the Whitelight tif 
Whitelight = Tiff([path 'Whitelight.tif'],'r').read();

%% Create the 4 images
B = bwboundaries(imbinarize(Whitelight,0.1),'noholes');
%figure, imagesc(Whitelight)
%hold on
xpos = zeros(2,4);
ypos = zeros(2,4);
for k = 1:length(B)
   xpos(1:2,k) = [min(B{k}(:,2)) max(B{k}(:,2))];
   ypos(1:2,k) = [min(B{k}(:,1)) max(B{k}(:,1))];
   %plot(B{k}(:,2),B{k}(:,1),'r.')
end
dx = max(xpos(2,:)-xpos(1,:));
dy = max(ypos(2,:)-ypos(1,:));
npix = 20;
stack = zeros(dy+2*npix,dx+2*npix,4);
for k = 1:4
    ddx = xpos(2,k)-xpos(1,k);
    ddy = ypos(2,k)-ypos(1,k);
    stack(npix:npix+ddy,npix:npix+ddx,k) = Itot(ypos(1,k):ypos(2,k),xpos(1,k):xpos(2,k));
end

disp(xpos)
disp(ypos)

fixed = stack(:,:,1);
fixed = fixed/max(fixed(:));
fixed = (fixed>=0.1).*fixed;
%figure, imagesc(fixed)

imsum = fixed;
for it = 2:4
    moving = stack(:,:,it);
    moving = moving/max(moving(:));
    moving = (moving>=0.1).*moving;
    %figure, imagesc(moving)
    
    [optimizer,metric] = imregconfig('multimodal');
    optimizer.MaximumIterations = 1000;
    optimizer.InitialRadius = 5e-4;
    optimizer.Epsilon = 1.5e-6;
    optimizer.GrowthFactor = 1.01;
    
%     tform_a = imregtform(moving,fixed,'affine',optimizer,metric);
%     movingRegistered = imwarp(moving,tform_a,'OutputView',imref2d(size(fixed)));

    tform_t = imregtform(moving,fixed,'translation',optimizer,metric);
    movingRegistered = imwarp(moving,tform_t,'OutputView',imref2d(size(fixed)));

    tform_a = imregtform(movingRegistered,fixed,'affine',optimizer,metric);
    movingRegistered = imwarp(movingRegistered,tform_a,'OutputView',imref2d(size(fixed)));

    imsum = imsum+movingRegistered;
    
    %figure, imshowpair(fixed,movingRegistered,'Scaling','joint')
    %figure, imagesc(movingRegistered)
end


%figure, imagesc(imsum)



