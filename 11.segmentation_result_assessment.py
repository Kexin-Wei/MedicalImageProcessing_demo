from pathlib import Path

import SimpleITK as sitk
import numpy as np
import pandas as pd

from lib.folder.med import BaseMedicalImageFolderMg
from lib.med_image.accuracy_verify import calc_dice_similarity_coefficient, calc_hausdorff_distance, calc_accuracy, \
    calc_relative_volume_difference

validation_path = Path("D:/Medical Image - Research/186Prostate_Validation")
label_path = validation_path.joinpath("labelsTs")
prediction_path = validation_path.joinpath("predictTs")
correction_path = validation_path.joinpath("predictTs_correct")

label_FMG = BaseMedicalImageFolderMg(label_path)
prediction_FMG = BaseMedicalImageFolderMg(prediction_path)
correction_FMG = BaseMedicalImageFolderMg(correction_path)

label_images = label_FMG.get_nifti_image_path()
prediction_images = prediction_FMG.get_nifti_image_path()
correction_images = correction_FMG.get_nifti_image_path()

print(len(label_images), len(prediction_images), len(correction_images))


def assess_predict(assess_images, save_path: Path):
    df = pd.DataFrame(columns=["Image Name", "DSC (%)", "HD (mm)", "RVD (%)", "Accuracy (%)"])

    for (l, p) in zip(label_images, assess_images):
        print(f"Processing label {l.name} and prediction {p.name}", end="")
        l_img = sitk.ReadImage(str(l), imageIO="NiftiImageIO")
        l_array = sitk.GetArrayFromImage(l_img).astype(np.int32)
        p_img = sitk.ReadImage(str(p), imageIO="NiftiImageIO")
        p_array = sitk.GetArrayFromImage(p_img).astype(np.int32)
        assert l_array.shape == p_array.shape, f"label shape:{l_array.shape}, prediction shape:{p_array.shape}"
        assert l_array.max() == 1 == p_array.max(), f"label max:{l_array.max()}, prediction max:{p_array.max()}"
        assert l_array.min() == 0 == p_array.min(), f"label min:{l_array.min()}, prediction min:{p_array.min()}"
        dice = calc_dice_similarity_coefficient(l_array, p_array)
        hausdorff = calc_hausdorff_distance(l_array, p_array, l_img.GetSpacing())
        accuracy = calc_accuracy(l_array, p_array)
        relative_volume_difference = calc_relative_volume_difference(l_array, p_array)
        print(
            f" - dice:{dice:.2f}, hausdorff:{hausdorff:.2f}, "
            f"rvd:{relative_volume_difference:.2f}, accu:{accuracy:.2f}")
        df.loc[-1] = [l.name, dice, hausdorff, relative_volume_difference, accuracy]
        df.index = df.index + 1
        df.sort_index(ascending=False)

    # add average row
    df.loc[-1] = ["Average", df["DSC (%)"].mean(), df["HD (mm)"].mean(),
                  df["RVD (%)"].mean(), df["Accuracy (%)"].mean()]

    df.to_excel(save_path.joinpath("result.xlsx"), index=False)
    print("Done")


if __name__ == "__main__":
    assess_predict(prediction_images, prediction_path)
    assess_predict(correction_images, correction_path)
