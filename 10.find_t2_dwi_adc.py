"""by kx 2023.03.22
Find all images with string "t2" inside their names, do deep into each folder, and eventually
save all the path of each image into an Excel
"""

import os
import random
import re
import shutil
from pathlib import Path
from typing import List

import natsort
import pandas as pd

from lib.folder.med import MedicalFolderMg, FolderMg
from lib.utility.define_class import STR_OR_PATH


def copy_img_record_in_excel(
        img_list: List[Path],
        destination_path: STR_OR_PATH,
        excel_name: str,
        overwrite_flag=False,
):
    """
    Copy file to destination path, if it finds same names add id occurred in path to distinguish it
    :type excel_name: str
    :param overwrite_flag:
    :param excel_name:
    :param img_list:
    :param destination_path:
    :return: none
    """
    if isinstance(destination_path, str):
        destination_path = Path(destination_path)
        os.makedirs(destination_path, exist_ok=True)
    excel_path = destination_path.joinpath(excel_name)
    if not overwrite_flag:
        # if not verify the existing file, check if the file excelPath exists, if exists return with printing message
        if excel_path.exists():
            print(f"Excel file {excel_path} exists, skipped")
            return

    file_id_series = []
    path_series = []
    id_series = []
    file_size_series = []
    file_name_patterns = []
    for f in img_list:
        if (
                "算法" not in str(f).lower()
                and f.stat().st_size > 1e6
                and "Registered" not in f.stem
        ):
            # 算法folder has abnormal but same name data from other clinical cases
            # size less than 1MB is too small
            # "Registered" seems duplicated
            path_id = re.findall(r"(RD_.+?)\\", str(f))[0]
            hospital_name = re.findall(r"[\u4e00-\u9fff]+", str(f))[
                0
            ]  # find chinese characters
            # rename
            destination_file_path = destination_path.joinpath(
                f"{f.stem}_{hospital_name}_{f.stat().st_size}size{f.suffix}"
            )
            if destination_file_path.exists():
                print(f"Same file {f}, skipped")
                continue
            print(
                f"Copying {destination_file_path.name} to {destination_path} from {f.parent} "
            )
            shutil.copy2(f, destination_file_path)
            file_id_series.append(destination_file_path.name)
            path_series.append(str(f))
            id_series.append(path_id)
            file_size_series.append(f.stat().st_size)
            file_name_patterns.append(f.stem)
    file_name_patterns = natsort.natsorted(set(file_name_patterns))
    print(
        f"\nIn total, {len(file_id_series)} files, with {len(file_name_patterns)} patterns"
    )
    if len(file_id_series) == 0 or len(file_name_patterns) == 0:
        return
    with pd.ExcelWriter(excel_path) as writer:
        s_file_id = pd.Series(file_id_series, dtype="string")
        s_id = pd.Series(id_series, dtype="string")
        s_path = pd.Series(path_series, dtype="string")
        s_file_name_pattern = pd.Series(file_name_patterns, dtype="string")
        s_file_size = pd.Series(file_size_series, dtype=int)

        df1 = pd.DataFrame(
            {
                "File Name": s_file_id,
                "Id": s_id,
                "File Size(KB)": s_file_size,
                "File Original Path": s_path,
            }
        )
        print(df1.head())
        df1.to_excel(writer, sheet_name="Summary of Images")
        df2 = pd.DataFrame({"File Name Patterns": s_file_name_pattern})
        print(df2.head())
        df2.to_excel(writer, sheet_name="File Name Pattern")
    print(f"Data stored in excel {str(excel_path)}")


def find_t2(source_path: STR_OR_PATH, save_path: STR_OR_PATH, excel_file_name: str):
    source_path_mg = MedicalFolderMg(source_path)
    source_path_mg.ls()
    source_path_mg.get_T2()
    copy_img_record_in_excel(
        source_path_mg.t2List, save_path, excel_file_name, overwrite_flag=False
    )


def split_data(save_path: STR_OR_PATH):
    if isinstance(save_path, str):
        save_path = Path(save_path)
    save_path_mg = FolderMg(save_path)
    save_path_mg.ls()
    random_file_list = random.sample(save_path_mg.files, save_path_mg.nFile)

    # split randomFileList into 10 parts
    n = 13
    split_list = [random_file_list[i::n] for i in range(n)]
    idx = 1
    for i, split in enumerate(split_list):
        folder_path = save_path.joinpath(f"DataPack{i + 1}")
        folder_path.mkdir(parents=True, exist_ok=True)
        for f in split:
            if ".mha" in f.suffix or ".nrrd" in f.suffix:
                shutil.copy2(f, folder_path)
                print(f"{idx}: Copying {f} to {folder_path}")
                idx += 1


def find_dwi(source_path: STR_OR_PATH, save_path: STR_OR_PATH, excel_file_name: str, overwrite: bool):
    source_path_mg = MedicalFolderMg(source_path)
    source_path_mg.ls()
    source_path_mg.get_DWI()
    copy_img_record_in_excel(
        source_path_mg.dwiList, save_path, excel_file_name, overwrite_flag=overwrite
    )


def find_adc(source_path: STR_OR_PATH, save_path: STR_OR_PATH, excel_file_name: str, overwrite: bool):
    source_path_mg = MedicalFolderMg(source_path)
    source_path_mg.ls()
    source_path_mg.get_ADC()
    copy_img_record_in_excel(
        source_path_mg.adcList, save_path, excel_file_name, overwrite_flag=overwrite
    )


if __name__ == "__main__":
    source_path = "E:/1. UGU Clinical Trial Data"
    save_path = Path("D:/Medical Image - Research")
    excel_file_name = "0Summary.xlsx"
    # t2
    # find_all_t2(sourcePath, savePath, excelFileName)
    # split_data(savePath)

    # find_dwi(source_path, save_path.joinpath("dwi"), excel_file_name, True)
    find_adc(source_path, save_path.joinpath("adc"), excel_file_name, True)
    print("Done")
