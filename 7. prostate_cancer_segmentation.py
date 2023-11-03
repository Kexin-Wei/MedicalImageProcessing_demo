"""2023.9.7 Kexin Wei
using region growing to segment prostate cancer
"""


import cv2 as cv
from pathlib import Path
from lib.folder.basic import FolderMg
from lib.utility.define_class import TwoDConnectionType
from lib.med_image.region_grow import RegionGrow, Similarity
import SimpleITK as sitk
import numpy as np


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
    folder_path = Path("data").joinpath("cancer-segmentation")
    result_path = Path("result").joinpath("cancer-segmentation")
    mg = FolderMg(folder_path)
    # mg.ls()

    # filename_og = "030_slice15.png"
    # filename_seg = "030_seg_slice15.png"
    # init_p = (115, 80)
    # threshold = 32

    filename_og = "030_slice13.png"
    filename_seg = "030_seg_slice13.png"
    init_p = (115, 80)
    threshold = 20

    file_og = mg.full_path.joinpath(filename_og)
    file_seg = mg.full_path.joinpath(filename_seg)
    file_save_img = result_path.joinpath(f"{filename_og}_threshold{threshold}.png")
    rg = RegionGrow(
        file_og,
        prompt_point=(init_p[0], init_p[1]),
        seg_rf_file=file_seg,
        threshold=threshold,
        connect_type=TwoDConnectionType.four,
        similarity_standard=Similarity.origin,
    )
    print(rg.img[init_p[0], init_p[1]])
    rg.show_prompt_point_at_start()
    rg.region_growing()
    rg.show_side_by_side(save=True, save_path=file_save_img)


def test_k_mean():
    folder_path = Path("data").joinpath("cancer-segmentation")
    result_path = Path("result").joinpath("cancer-segmentation")
    mg = FolderMg(folder_path)

    filename_og = "030_slice15.png"
    filename_seg = "030_seg_slice15.png"
    file_og = mg.full_path.joinpath(filename_og)
    file_seg = mg.full_path.joinpath(filename_seg)
    file_save_img = result_path.joinpath(f"{filename_og}.png")

    img = cv.imread(str(file_og), cv.IMREAD_GRAYSCALE)
    init_p = (115, 80)
    centroids = (img[init_p[0], init_p[1]], 150)

    iter = 1
    label_img = img.copy()
    img_float = np.array(img, dtype=np.float32)
    while iter < 100:
        print(f"Iter: {iter}, centroids: ({centroids[0]:.2f}, {centroids[1]:.2f})")
        old_centroids_float = np.array(centroids, dtype=np.float32)
        # label
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                d1 = abs(old_centroids_float[0] - img_float[i, j])
                d2 = abs(old_centroids_float[1] - img_float[i, j])
                if d1 < d2:
                    label_img[i, j] = 0
                else:
                    label_img[i, j] = 255

        # update centroids
        centroids = (
            np.mean(img_float[label_img == 0]),
            np.mean(img_float[label_img == 255]),
        )
        centroids_float = np.array(centroids, dtype=np.float32)

        if (
            abs(old_centroids_float[0] - centroids_float[0]) < 1
            and abs(old_centroids_float[1] - centroids_float[1]) < 1
        ):
            break
    cv.imshow("label_img", label_img)
    cv.waitKey(0)


if __name__ == "__main__":
    # generate_cancer_slices()
    # test_region_growing()
    test_k_mean()
