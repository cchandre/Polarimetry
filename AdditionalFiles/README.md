# Data post-processing with Matlab

- Shifted histograms: [ShiftedHisto.m](https://github.com/cchandre/Polarimetry/blob/master/AdditionalFiles/ShiftedHisto.m)

- Concatenated shifted histograms: [ConcatShiftedHisto.m](https://github.com/cchandre/Polarimetry/blob/master/AdditionalFiles/ConcatShiftedHisto.m)

- Rescaled and concatenated shifted histograms: [RescaledConcatShiftedHisto.m](https://github.com/cchandre/Polarimetry/blob/master/AdditionalFiles/RescaledConcatShiftedHisto.m)

- Horizontal boxplots of psi values: [BoxplotPsiHorizontal.m](https://github.com/cchandre/Polarimetry/blob/master/AdditionalFiles/BoxplotPsiHorizontal.m)

- Rescales figures of psi values: [RescaledPsiFigs.m](https://github.com/cchandre/Polarimetry/blob/master/AdditionalFiles/RescaledPsiFigs.m)

- Zoom over an ROI of defined size: [ZoomROI.mlx](https://github.com/cchandre/Polarimetry/blob/master/AdditionalFiles/ZoomROI.mlx)


# Data post-processing with Python

The polarimetry data are saved in a .mat (MATLAB®) file. Post-processing can be naturally done in MATLAB®. For open-source purposes, the .mat data file can be read in Python using the scipy.io library and data plotted using libraries like matplotlib, plotly, seaborn... Here is an example for plotting histograms:
```python 
from scipy.io import loadmat
import matplotlib.pyplot as plt
import seaborn as sns
data = loadmat('B16_P36.mat')
Psi = data['Psi']
Rho = data['Rho']
f, ax = plt.subplots(1,1)
ax.set_xlabel('Angle')
ax.set_ylabel('Frequency')
sns.distplot(Psi, bins=20, label='Psi Histogram', color='purple')
sns.distplot(Rho, bins=60, label='Rho Histogram', color='blue')
ax.legend(loc='upper right')
ax.set_xlim([0, 180])
plt.show()
```

___
For more information: <cristel.chandre@cnrs.fr>
