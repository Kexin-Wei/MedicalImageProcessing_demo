from pathlib import Path
from lib.folder.basic import FolderMg
import json
import SimpleITK as sitk
import pydicom
import numpy as np

filePath = Path("D:/Medical Image - Example/Real-Patient-Data/Patient A/t2")
folderMg = FolderMg(filePath)


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


def calculate_coordiante_of_voxel(i: int, j: int, img: pydicom.FileDataset):
    image_position_patient = np.array(img.ImagePositionPatient)
    image_orientation_patient = img.ImageOrientationPatient
    pixel_spacing = np.array(img.PixelSpacing)
    slice_thickness = img.SliceThickness

    row_x_cos = np.array(image_orientation_patient[0:3])
    column_y_cos = np.array(image_orientation_patient[3:6])
    matrix = np.zeros((4, 4))
    matrix[0:3, 0] = row_x_cos * pixel_spacing[0]
    matrix[0:3, 1] = column_y_cos * pixel_spacing[1]
    matrix[0:3, 3] = image_position_patient
    matrix[3, 3] = 1
    # print(matrix)
    pixel_position = np.array([i, j, 0, 1]).T
    actual_position = np.matmul(matrix, pixel_position)
    # print(actual_position)
    return actual_position[0:3]


def calculate_slice_distance():
    pure_files = []
    for f in folderMg.files:
        if f.name == "DIRFILE":
            continue
        pure_files.append(f)

    for ith_file in range(len(pure_files) - 1):
        f_ith = pure_files[ith_file]
        img_ith = pydicom.dcmread(f_ith)
        actual_position_ith = calculate_coordiante_of_voxel(0, 0, img_ith)
        slice_thickness = img_ith.SliceThickness
        f_i1th = pure_files[ith_file + 1]
        img_i1th = pydicom.dcmread(f_i1th)
        actual_position_i1th = calculate_coordiante_of_voxel(0, 0, img_i1th)
        distance = np.linalg.norm(actual_position_ith - actual_position_i1th)
        print(
            f"{ith_file}: distance:{distance:.3}, slice_thickness:{slice_thickness:.3}"
        )


if __name__ == "__main__":
    # storeDicomSliceTags()
    calculate_slice_distance()
