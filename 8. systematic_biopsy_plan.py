import cv2
import numpy as np
from enum import Enum
from pathlib import Path
from lib.folder.basic import FolderMg
from lib.ultrasound.biopsy import BiopsyPlanWithBox, BiopsyPlanWithBoundary


class PlanMethod(Enum):
    Box = 1
    Boundary = 2


def test_biopsy_plan(plan_method=PlanMethod.Boundary):
    data_path = Path("data").joinpath("biopsy-plan")
    mg = FolderMg(data_path)
    mg.ls()

    prostate_files = []
    specimen_file = None
    for f in mg.files:
        if "t2" in f.name.lower():
            prostate_files.append(f)
        else:
            specimen_file = f

    if plan_method == PlanMethod.Box:
        result_path = Path("result").joinpath("biopsy-plan", "box")
        bp = BiopsyPlanWithBox(
            prostate_file=prostate_files[0],
            specimen_file=specimen_file,
            result_path=result_path,
        )
        bp.plan()
    else:
        result_path = Path("result").joinpath("biopsy-plan", "boundary")
        bp = BiopsyPlanWithBoundary(
            prostate_file=prostate_files[0],
            specimen_file=specimen_file,
            result_path=result_path,
        )
        bp.plan()


def combine_result_img_into_one(
    folder_name="boundary", group_name=["ten_core", "twelve_core"]
):
    result_folder = Path("result").joinpath("biopsy-plan", folder_name)
    rf_mg = FolderMg(result_folder)
    rf_mg.ls()

    group_img = {group_name[0]: [], group_name[1]: []}
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
    # test_biopsy_plan(plan_method=PlanMethod.Boundary)
    # combine_result_img_into_one(
    #     folder_name="boundary", group_name=["ten_core", "twelve_core"]
    # )
    combine_result_img_into_one(
        folder_name="new-boundary", group_name=["twelve_core", "twentyfour_core"]
    )
