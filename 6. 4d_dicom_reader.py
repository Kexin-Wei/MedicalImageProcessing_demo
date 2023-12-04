import json
import os
import SimpleITK as sitk

from pathlib import Path
from lib.folder.basic import FolderMg

filePath = Path("data").joinpath("4d-dicom", "LIXIANGQIAN", "20231104115402", "802")
# filePath = Path("data").joinpath("4d-dicom", "bug")
folderMg = FolderMg(filePath)


# folderMg.ls()
def storeDicomSliceTags():
    storePath = filePath.joinpath("json_tags")
    if storePath.exists():
        storePath.rmdir()
    else:
        storePath.mkdir()

    for i, f in enumerate(folderMg.files):
        sliceTags = {}
        if f.name == "DIRFILE":
            continue
        # read each slice and their meta data
        print(f"reading {i}.{f} ...")
        reader = sitk.ImageFileReader()
        reader.SetFileName(str(f))
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()
        img = reader.Execute()
        metaData = reader.GetMetaDataKeys()
        for key in metaData:
            key_value = img.GetMetaData(key)
            sliceTags[key] = key_value

        with open(storePath.joinpath(f"info_slice{i}.json"), "w") as f:
            json.dump(sliceTags, f, indent=4)


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
        if nop not in nops.keys():
            nops[nop] = 1
        else:
            nops[nop] += 1
    print(nops)


def checkImagePositionAndGroupThem():
    img_groups = {}
    pos_groups = {}
    for i, f in enumerate(folderMg.files):
        add_to_next_group = True
        if f.name == "DIRFILE":
            continue
        # read each slice and their meta data
        print(f"reading {i}.{f} ...")
        reader = sitk.ImageFileReader()
        reader.SetFileName(str(f))
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()
        img = reader.Execute()

        key = "0020|0032"
        key_value = img.GetMetaData(key)
        position = key_value.split("\\")
        position = [float(p) for p in position]
        position = tuple(position)

        # check if the position is already in one of the groups
        len_groups = len(img_groups.keys())
        for k_group in range(len_groups):
            if position not in pos_groups[k_group]:
                add_to_next_group = False
                img_groups[k_group].append(str(f))
                pos_groups[k_group].append(position)
                # print(f"adding in group {k_group}: {position} - {f.name}")
                break

        if add_to_next_group:
            img_groups[len_groups] = [str(f)]
            pos_groups[len_groups] = [position]
            # print(f"adding in group {len_groups}: {position} - {f.name}")

    for k_group in img_groups.keys():
        print(
            f"groupd: {k_group} - len: {len(img_groups[k_group])}, imgs: {img_groups[k_group]}"
        )
        # show image
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(img_groups[k_group])

        temp_dicom_img = reader.Execute()
        write_path = Path("result").joinpath(
            "4d-dicom", filePath.name, f"img{k_group}.dcm"
        )
        write_path.parent.mkdir(parents=True, exist_ok=True)
        sitk.WriteImage(temp_dicom_img, str(write_path))
        # if "SITK_NOSHOW" not in os.environ:
        #     sitk.Show(temp_dicom_img, "Dicom Series")


if __name__ == "__main__":
    # getInfo()
    # storeDicomSliceTags()
    # checkContentTime()
    checkImagePositionAndGroupThem()
