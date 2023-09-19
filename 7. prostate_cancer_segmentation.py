"""2023.9.7 Kexin Wei
using region growing to segment prostate cancer
"""


import numpy as np
from lib.folder.basic import FolderMg

from lib.med_image.region_grow import *


def test_region_growing():
    threshold = 8
    folderPath = Path("data").joinpath("mri-prostate-slices")
    mg = FolderMg(folderPath)
    # mg.ls()

    folder = FolderMg(mg.dirs[2])
    file = folder.files[11]
    img = read_preprocess(file)
    # cv.imshow("img", img)
    # cv.waitKey(0)

    input_p = tuple((np.array(img.shape) / 2).astype(int))
    print(input_p)

    init_seeds = Queue()
    init_seeds.append(input_p)
    seg_img = region_growing(
        img, init_seeds, connect_type=TwoDConnectionType.four, threshold=threshold
    )
    seg_img = fill_hole(seg_img)
    show_side_by_side(img, seg_img, input_point=input_p)


if __name__ == "__main__":
    test_region_growing()
