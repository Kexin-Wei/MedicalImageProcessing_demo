"""2023.07.17 Kexin
read 3D meta image and nrrd image, save every slice to png
"""
from pathlib import Path

import SimpleITK as sitk

from lib.folder import MedicalImageFolderMg

sourceDataPath = Path("D:/GoogleDrive/Ultrast/5 Image - Image Segmentation/2D Segmentation/0-og volume images")
sourceMg = MedicalImageFolderMg(sourceDataPath)
destinationPath = Path("data").joinpath("mri-prostate-slices-resample")
# sourceMg.ls()

metaFile = sourceMg.getMetaImagePath()
nrrdFile = sourceMg.getNrrdImagePath()

for f in nrrdFile:
    outputFolderPath = destinationPath.joinpath(f"{f.stem}")
    if not outputFolderPath.exists():
        outputFolderPath.mkdir(parents=True)
    print(f"- {f.name}")
    nrrdImg = sitk.ReadImage(f, imageIO="NrrdImageIO")
    sitk.WriteImage(sitk.Cast(sitk.RescaleIntensity(nrrdImg), sitk.sitkUInt8),
                    [outputFolderPath.joinpath(f"slice{i}.png") for i in range(nrrdImg.GetSize()[-1])])

for f in metaFile:
    print(f"- {f.name}")
    outputFolderPath = destinationPath.joinpath(f"{f.stem}")
    if not outputFolderPath.exists():
        outputFolderPath.mkdir(parents=True)
    metaImg = sitk.ReadImage(f, imageIO="MetaImageIO")
    sitk.WriteImage(sitk.Cast(sitk.RescaleIntensity(metaImg), sitk.sitkUInt8),
                    [outputFolderPath.joinpath(f"slice{i}.png") for i in range(metaImg.GetSize()[-1])])
print("Done")
