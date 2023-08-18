import json
import SimpleITK as sitk

from pathlib import Path
from lib.folder import FolderMg

filePath = Path("C:/Users/weike/Downloads/DWI-sTRA")
folderMg = FolderMg(filePath)


# folderMg.ls()
def getInfo():
    basic_info = {}
    different_info = {}
    for f in folderMg.files:
        # read each slice and their meta data
        reader = sitk.ImageFileReader()
        reader.SetFileName(str(f))
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()
        img = reader.Execute()
        metaData = reader.GetMetaDataKeys()
        for key in metaData:
            key_value = img.GetMetaData(key)
            if key not in basic_info.keys():
                basic_info[key] = key_value
            else:
                if basic_info[key] != key_value:
                    if key not in different_info.keys():
                        different_info[key] = [key_value]
                    else:
                        if key_value not in different_info[key]:
                            different_info[key].append(key_value)
    print(different_info)
    print(basic_info)

    with open("basic_info.json", "w") as f:
        json.dump(basic_info, f, indent=4)
    with open("different_info.json", "w") as f:
        json.dump(different_info, f, indent=4)


def checkContentTime():
    import matplotlib.pyplot as plt
    import numpy as np

    different_info = json.load(open("different_info.json"))
    contentTime = different_info["0008|0013"]
    for i in range(len(contentTime)):
        times = float(contentTime[i])
        hh = np.modf(times / 10000)
        mm = hh[0]
        hh = hh[-1]
        mm = np.modf(mm * 100)
        ss = mm[0] * 100
        mm = mm[-1]
        mm = np.modf((times - hh * 10000) / 100)[1]
        times = hh * 3600 + mm * 60 + ss
        print(f"{i}: {contentTime[i]} - {times}")


def readNumberofComponents():
    nops = {}
    for f in folderMg.files:
        # read each slice and their meta data
        reader = sitk.ImageFileReader()
        reader.SetFileName(str(f))
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()
        img = reader.Execute()
        # metaData = reader.GetMetaDataKeys()
        nop = img.GetNumberOfComponentsPerPixel()
        gdt = img.GetCom
        if nop not in nops.keys():
            nops[nop] = 1
        else:
            nops[nop] += 1
    print(nops)


if __name__ == "__main__":
    # getInfo()
    # checkContentTime()
    readNumberofComponents()
