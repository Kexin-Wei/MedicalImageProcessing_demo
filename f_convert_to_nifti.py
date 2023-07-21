"""by Kexin, 2023.3.14
reading all the medical images in the designated folder, and convert them into nifti images to predict for nnUNet
- supported formats: 
    - *.nrrd, "NrrdImageIO"
    - *.mha, "MetaImageIO"
"""
import SimpleITK as sitk
from pathlib import Path

from lib.folder import BaseMedicalImageFolderMg

# endLetters = "_0001"
endLetters = ""

sourceDataPath = Path("D:/GitRepos/train_nnUNet/clinical_collect_data")
destinationDataPath = Path("D:/GitRepos/train_nnUNet/clinical_collect_data_nifti")

if not destinationDataPath.exists():
    destinationDataPath.mkdir()
sourceMg = BaseMedicalImageFolderMg(sourceDataPath)
sourceMg.ls()

metaImageFiles = sourceMg.getMetaImagePath()
nrrdImageFiles = sourceMg.getNrrdImagePath()

for m in metaImageFiles:
    outFileName = destinationDataPath.joinpath(f"{m.stem}{endLetters}.nii.gz")
    if not outFileName.exists():
        mImg = sitk.ReadImage(m, imageIO="MetaImageIO")
        sitk.WriteImage(mImg, fileName=outFileName)
        print(f"Writing file to {outFileName}")

for m in nrrdImageFiles:
    outFileName = destinationDataPath.joinpath(f"{m.stem}{endLetters}.nii.gz")
    if not outFileName.exists():
        mImg = sitk.ReadImage(m, imageIO="NrrdImageIO")
        sitk.WriteImage(mImg, fileName=outFileName)
        print(f"Writing file to {outFileName}")

print("Done")
