from pathlib import Path

import SimpleITK as sitk
import numpy as np

from lib.folder.med import BaseMedicalImageFolderMg

validation_path = Path("D:/Medical Image - Research/186Prostate_Validation")
label_path = validation_path.joinpath("labelsTs")
prediction_path = validation_path.joinpath("predictTs")
label_FMG = BaseMedicalImageFolderMg(label_path)
prediction_FMG = BaseMedicalImageFolderMg(prediction_path)

label_images = label_FMG.get_nifti_image_path()
prediction_images = prediction_FMG.get_nifti_image_path()

print(len(label_images), len(prediction_images))

for (l, p) in zip(label_images, prediction_images):
    print(l, p)
    l_img = sitk.ReadImage(str(l), imageIO="NiftiImageIO")
    l_array = sitk.GetArrayFromImage(l_img).astype(np.int32)
    p_img = sitk.ReadImage(str(p), imageIO="NiftiImageIO")
    p_array = sitk.GetArrayFromImage(p_img).astype(np.int32)
