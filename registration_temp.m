function registration_temp
close all
[filename, path] = uigetfile('fbeads*.tif','fbeads*.tiff');

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
figure(1), imagesc(imadjust(Itot/max(Itot(:))))

%BW = medfilt2(Itot>15);
BW =  medfilt2(imadjust(Itot/max(Itot(:)))>0.08);
B = bwboundaries(BW,'holes');
figure(2), imshow(BW); hold on
for k=1:length(B)
    boundary = B{k};
    plot(boundary(:,2),boundary(:,1),'r','LineWidth',2);
end



