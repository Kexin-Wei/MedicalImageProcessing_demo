"""2023.9.7 Kexin Wei
using region growing to segment prostate cancer
"""
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from lib.folder.basic import FolderMg
from lib.utility.define_class import TwoDConnectionType
from pathlib import Path

THRESHOLD = 0.5


def connect_points(connect_type: TwoDConnectionType):
    if connect_type == TwoDConnectionType.EIGHT_NEIGHBOUR:
        return np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
    else:  # connect_type == TwoDConnectionType.FOUR_NEIGHBOUR:
        return np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])


def location_matrx(i: int, j: int):
    x_m = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]) + i
    y_m = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]]) + j
    return np.moveaxis(np.array([x_m, y_m]), 0, -1)


def intensity_matrix(img: np.ndarray, i: int, j: int) -> np.ndarray:
    if i < 1 or j < 1 or i > img.shape[0] - 1 or j > img.shape[1] - 1:
        return None
    return img[i - 1 : i + 2, j - 1 : j + 2]


def check_similarity(
    i_m: np.ndarray, connect_m: np.ndarray, threshold=0.5
) -> np.ndarray:
    i_m_diff = np.abs(i_m - i_m[1][1])
    valid_diff = i_m_diff[connect_m == 1]
    return valid_diff > THRESHOLD


def get_new_seeds(
    img: np.ndarray, i: int, j: int, connect_type: TwoDConnectionType, threshold=0.5
):
    c_m = connect_points(connect_type)
    i_m = intensity_matrix(img, i, j)
    new_seeds_condition = check_similarity(i_m, c_m, threshold=threshold)
    l_m = location_matrx(i, j)
    new_seeds = l_m[new_seeds_condition]
    return new_seeds


def grow_region(seeds: np.ndarray):
    """
    seeds: [n x 2], each seeds[k] = [i,j]
    """
    for k in range(seeds.shape[0]):
        i = seeds[k, 0]
        j = seeds[k, 1]
        img_i = intensity_matrix(img, i, j)
        if img_i is None:
            continue
        else:
            pass


def normalize(img: np.ndarray) -> np.ndarray:
    """normalize image"""
    img = img.astype(np.float32)
    img = img - img.min()
    img = img / img.max()
    img = img * 255
    return img.astype(np.uint8)


def show_side_by_side(img1: np.ndarray, img2: np.ndarray):
    """show two images side by side"""
    new_img = np.concatenate((img1, img2), axis=1)
    cv.imshow("new_img", new_img)
    cv.waitKey(0)


def show_img_from_file(file: Path) -> np.ndarray:
    img = cv.imread(str(file))
    cv.imshow("{file.name}", img)
    cv.waitKey(0)
    return img


if __name__ == "__main__":
    # 2d region growing
    folderPath = Path("data").joinpath("mri-prostate-slices")
    mg = FolderMg(folderPath)
    # mg.ls()

    folder = FolderMg(mg.dirs[2])
    file = folder.files[11]
    img = cv.imread(str(file))
    normalized_img = normalize(img)
    # show_side_by_side(img, normalized_img)
    
    init_seed = np.array(normalized_img.shape)/2
    print(init_seed)
