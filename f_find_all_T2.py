"""by kx 2023.03.22
Find all images with string "t2" inside their names, do deep into each folder, and eventually
save all the path of each image into an Excel
"""
import re
import os
import natsort
import random
from pathlib import Path

import pandas as pd
import shutil

from typing import List

from lib.folder import T2FolderMg, FolderMg
from lib.utility.define_class import STR_OR_PATH


def copyT2andRecordInExcel(t2List: List[Path], destinationPath: STR_OR_PATH, excelName: str, overwriteFlag=False):
    """
    Copy file to destination path, if it finds same names add id occurred in path to distinguish it
    :type excelName: str
    :param overwriteFlag:
    :param excelName:
    :param t2List:
    :param destinationPath:
    :return: none
    """
    if isinstance(destinationPath, str):
        destinationPath = Path(destinationPath)
        os.makedirs(destinationPath, exist_ok=True)
    excelPath = destinationPath.joinpath(excelName)
    if not overwriteFlag:
        # if not verify the existing file, check if the file excelPath exists, if exists return with printing message
        if excelPath.exists():
            print(f"Excel file {excelPath} exists, skipped")
            return

    fileIdSeries = []
    pathSeries = []
    idSeries = []
    fileSizeSeries = []
    fileNamePatterns = []
    for f in t2List:
        if "算法" not in str(f).lower() and f.stat().st_size > 1e6 and "Registered" not in f.stem:
            # 算法folder has abnormal but same name data from other clinical cases
            # size less than 1MB is too small
            # "Registered" seems duplicated
            pathId = re.findall(r'(RD_.+?)\\', str(f))[0]
            hospitalName = re.findall(r'[\u4e00-\u9fff]+', str(f))[0]  # find chinese characters
            # rename
            destinationFilePath = destinationPath.joinpath(f"{f.stem}_{hospitalName}_{f.stat().st_size}size{f.suffix}")
            if destinationFilePath.exists():
                print(f"Same file {f}, skipped")
                continue
            print(f"Copying {destinationFilePath.name} to {destinationPath} from {f.parent} ")
            shutil.copy2(f, destinationFilePath)
            fileIdSeries.append(destinationFilePath.name)
            pathSeries.append(str(f))
            idSeries.append(pathId)
            fileSizeSeries.append(f.stat().st_size)
            fileNamePatterns.append(f.stem)
    fileNamePatterns = natsort.natsorted(set(fileNamePatterns))
    print(f"\nIn total, {len(fileIdSeries)} files, with {len(fileNamePatterns)} patterns")

    with pd.ExcelWriter(excelPath) as writer:
        sFileId = pd.Series(fileIdSeries, dtype="string")
        sId = pd.Series(idSeries, dtype="string")
        sPath = pd.Series(pathSeries, dtype="string")
        sFileNamePattern = pd.Series(fileNamePatterns, dtype="string")
        sFileSize = pd.Series(fileSizeSeries, dtype=int)

        df1 = pd.DataFrame({"File Name"         : sFileId,
                            "Id"                : sId,
                            "File Size(KB)"     : sFileSize,
                            "File Original Path": sPath})
        print(df1.head())
        df1.to_excel(writer, sheet_name="Summary of Images")
        df2 = pd.DataFrame({"File Name Patterns": sFileNamePattern})
        print(df2.head())
        df2.to_excel(writer, sheet_name="File Name Pattern")
    print(f"Data stored in excel {str(excelPath)}")


def findAllT2(sourcePath: STR_OR_PATH, savePath: STR_OR_PATH, excelFileName: str):
    sourcePathMg = T2FolderMg(sourcePath)
    sourcePathMg.ls()
    sourcePathMg.getT2()
    copyT2andRecordInExcel(sourcePathMg.t2List, savePath, excelFileName, overwriteFlag=False)


def splitData(savePath: STR_OR_PATH):
    if isinstance(savePath, str):
        savePath = Path(savePath)
    savePathMg = FolderMg(savePath)
    savePathMg.ls()
    randomFileList = random.sample(savePathMg.files, savePathMg.nFile)

    # split randomFileList into 10 parts
    n = 13
    splitList = [randomFileList[i::n] for i in range(n)]
    idx = 1
    for i, split in enumerate(splitList):
        folderPath = savePath.joinpath(f"DataPack{i + 1}")
        folderPath.mkdir(parents=True, exist_ok=True)
        for f in split:
            if ".mha" in f.suffix or ".nrrd" in f.suffix:
                shutil.copy2(f, folderPath)
                print(f"{idx}: Copying {f} to {folderPath}")
                idx += 1


sourcePath = "E:/1. UGU Clinical Trial Data"
savePath = "D:/GitRepos/train_nnUNet/clinical_collect_data_new"
excelFileName = "0Summary.xlsx"

# findAllT2(sourcePath, savePath, excelFileName)
splitData(savePath)

print("done")
