"""2023.9.7 Kexin Wei
using region growing to segment prostate cancer
"""


import numpy as np
import cv2 as cv
from pathlib import Path
from lib.folder.basic import FolderMg
from lib.utility.define_class import TwoDConnectionType
from lib.med_image.region_grow import RegionGrow


def test_region_growing():
    threshold = 8
    folderPath = Path("data").joinpath("mri-prostate-slices")
    mg = FolderMg(folderPath)
    # mg.ls()

    folder = FolderMg(mg.dirs[2])
    file = folder.files[11]

    img = cv.imread(str(file))
    init_p = (np.array(img.shape) / 2).astype(int)
    rg = RegionGrow(
        file,
        prompt_point=(init_p[0], init_p[1]),
        threshold=threshold,
        connect_type=TwoDConnectionType.four,
    )

    rg.region_growing()
    rg.show_side_by_side()


if __name__ == "__main__":
    test_region_growing()
