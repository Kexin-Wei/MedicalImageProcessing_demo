"""2023.9.7 Kexin Wei
using region growing to segment prostate cancer
"""


import cv2 as cv
from pathlib import Path
from lib.folder.basic import FolderMg
from lib.utility.define_class import TwoDConnectionType
from lib.med_image.region_grow import RegionGrow, Similarity
import SimpleITK as sitk


def generate_cancer_slices():
    dataPath = Path(
        "D:/Medical Image - Research/Training Dataset/Prostate158 Cancer/prostate158_train/train"
    )
    mg = FolderMg(dataPath)
    mg.ls()
    folder_with_tumor = "030"

    t2_filename = "t2.nii.gz"
    t2_tumor_filename = "t2_tumor_reader1.nii.gz"
    t2_image = sitk.ReadImage(
        dataPath.joinpath(folder_with_tumor, t2_filename),
        imageIO="NiftiImageIO",
    )
    t2_tumor_image = sitk.ReadImage(
        dataPath.joinpath(folder_with_tumor, t2_tumor_filename),
        imageIO="NiftiImageIO",
    )

    outputFolderPath = Path("data").joinpath("cancer-segmentation")

    sitk.WriteImage(
        sitk.Cast(sitk.RescaleIntensity(t2_image), sitk.sitkUInt8),
        [
            outputFolderPath.joinpath(f"{folder_with_tumor}_slice{i}.png")
            for i in range(t2_image.GetSize()[-1])
        ],
    )

    sitk.WriteImage(
        sitk.Cast(sitk.RescaleIntensity(t2_tumor_image), sitk.sitkUInt8),
        [
            outputFolderPath.joinpath(f"{folder_with_tumor}_seg_slice{i}.png")
            for i in range(t2_tumor_image.GetSize()[-1])
        ],
    )


def test_region_growing():
    threshold = 32
    folderPath = Path("data").joinpath("cancer-segmentation")
    mg = FolderMg(folderPath)
    # mg.ls()

    filename_og = "030_slice15.png"
    filename_seg = "030_seg_slice15.png"
    file_og = mg.fullPath.joinpath(filename_og)
    file_seg = mg.fullPath.joinpath(filename_seg)

    init_p = (115, 80)
    rg = RegionGrow(
        file_og,
        prompt_point=(init_p[0], init_p[1]),
        # seg_rf_file=file_seg,
        threshold=threshold,
        connect_type=TwoDConnectionType.four,
        similarity_standard=Similarity.origin,
    )
    print(rg.img[init_p[0], init_p[1]])
    rg.show_prompt_point_at_start()
    rg.region_growing()
    rg.show_side_by_side()


def test_k_mean():
    pass


if __name__ == "__main__":
    # generate_cancer_slices()
    test_region_growing()
    # test_k_mean()
