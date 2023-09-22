import cv2
import numpy as np
from pathlib import Path
from lib.folder.basic import FolderMg
from lib.ultrasound.biopsy import BiopsyPlanWithBox


def test_biopsy_plan():
    data_path = Path("data").joinpath("biopsy-plan")
    result_path = Path("result").joinpath("biopsy-plan", "boundary_box")
    mg = FolderMg(data_path)
    mg.ls()

    prostate_files = []
    specimen_file = None
    for f in mg.files:
        if "t2" in f.name.lower():
            prostate_files.append(f)
        else:
            specimen_file = f

    bp = BiopsyPlanWithBox(
        prostate_file=prostate_files[0],
        specimen_file=specimen_file,
        result_path=result_path,
    )
    bp.plan()


def combine_result_img_into_one():
    result_folder = Path("result").joinpath("biopsy-plan", "boundary_box")
    rf_mg = FolderMg(result_folder)
    rf_mg.ls()

    group_img = {"ten_core": [], "twelve_core": []}
    for f in rf_mg.files:
        for k in group_img.keys():
            if k in f.name.lower():
                img = cv2.imread(str(f))
                group_img[k].append(img)

    # print(group_img)
    for k in group_img.keys():
        row1 = np.hstack((group_img[k][0], group_img[k][1], group_img[k][2]))
        row2 = np.hstack((group_img[k][3], group_img[k][4], group_img[k][5]))
        row3 = np.hstack((group_img[k][6], group_img[k][7], group_img[k][8]))
        final = np.vstack((row1, row2, row3))
        cv2.imwrite(str(result_folder.joinpath(f"{k}.png")), final)


if __name__ == "__main__":
    test_biopsy_plan()
    # combine_result_img_into_one()
