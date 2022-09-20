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
figure(1), imagesc(imadjust(Itot/max(Itot(:)))), hold on

figure(2)
for it = 1:2
    subplot(2,1,it)
    vec = sum(Itot,it);
    plot(vec,'linewidth',3)
    xlim([1 info(1).Height])
    [~,I] = min(vec(401:600));
    pos(it) = I+400;
end
figure(1), plot(xlim,[pos(2) pos(2)],'r','linewidth',3)
plot([pos(1) pos(1)],ylim,'r','linewidth',3)

fixed = Itot(1:pos(1),1:pos(2));
moving = Itot(pos(1)+1:end,1:pos(2));
%moving(2) = Itot(1:pos(1),pos(2)+1:end);
%moving(3) = Itot(pos(1)+1:end,pos(2)+1:end);

%[optimizer,metric] = imregconfig("multimodal");
optimizer = registration.optimizer.OnePlusOneEvolutionary;
metric = registration.metric.MattesMutualInformation;
movingRegistered = imregister(moving,fixed,"affine",optimizer,metric);
figure, imshowpair(fixed,movingRegistered,"Scaling","joint")





