"""2023.07.17 Kexin
using [Segment-Anything](https://github.com/facebookresearch/segment-anything) pretrained model to segment prostate mri slice by slice
"""

import torch
import torchvision
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from lib.folder import FolderMg
from lib.sam_base import BasicSAM

print("PyTorch version:", torch.__version__)
print("Torchvision version:", torchvision.__version__)
print("CUDA is available:", torch.cuda.is_available())

sourceFolderName = "mri-prostate-slices-resample"
sourceDataPath = Path("data").joinpath(sourceFolderName)
destinationPath = Path("result").joinpath(sourceFolderName)

samModel = BasicSAM("vit_h")

print("Processing folders:")
sourceMg = FolderMg(sourceDataPath)
for fd in sourceMg.dirs:
    print(f"- {fd.name}")
    fdMg = FolderMg(fd)

    outputFolderPath = destinationPath.joinpath(f"{fd.name}")
    if not outputFolderPath.exists():
        outputFolderPath.mkdir(parents=True)

    # middleFile = fdMg.files[int(fdMg.nFile / 2)]
    # figSavePath = outputFolderPath.joinpath(f"{middleFile.name}_mask_")
    # masks, scores = predictOneImg(middleFile, predictor, figSavePath, False)
    sliceSegResult = []
    for slice in fdMg.files:
        figSavePath = outputFolderPath.joinpath(f"{slice.name}_mask_")
        masks, scores = samModel.predictOneImg(slice, figSavePath, onlyFirstMask=True)
        sliceSegResult.append(masks[0])

    imgSize = (masks.shape[0], masks.shape[1], fdMg.nFile)  # x,y,z
    # imgSegResult = sitk.Image(masks[0].shape[0],masks[0].shape[1], fdMg.nFile, sitk.sitkUInt8)
    segImgArray = np.array([sliceSegResult]).astype(int).squeeze()
    segImg = sitk.GetImageFromArray(segImgArray)
    imgSavePath = destinationPath.joinpath(f"seg_{fd.name}.nii.gz")
    sitk.WriteImage(segImg, imgSavePath)
print("Finished")
