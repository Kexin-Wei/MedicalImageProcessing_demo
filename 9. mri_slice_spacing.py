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

    for ith_slice in range(len(pure_files) - 1):
        f_i = pure_files[ith_slice]
        img_i = pydicom.dcmread(f_i)
        actual_position_i = calculate_coordiante_of_voxel(0, 0, img_i)
        slice_thickness = img_i.SliceThickness
        f_i1 = pure_files[ith_slice + 1]
        img_i1 = pydicom.dcmread(f_i1)
        actual_position_i1 = calculate_coordiante_of_voxel(0, 0, img_i1)
        distance = np.linalg.norm(actual_position_i - actual_position_i1)
        print(
            f"{ith_slice}: actual_position:{actual_position_i},distance:{distance:.3}, slice_thickness:{slice_thickness:.3}"
        )


def compare_dicom_slice_pixel_value_with_nrrd():
    nrrd_file = Path(
        "D:/Medical Image - Example/Real-Patient-Data/Patient A/Patient20201029MR_T2W_SPAIR_ax.nrrd"
    )
    nrrd_img = sitk.ReadImage(str(nrrd_file))

    pure_files = []
    for f in folderMg.files:
        if f.name == "DIRFILE":
            continue
        pure_files.append(f)

    nrrd_img_array = sitk.GetArrayFromImage(nrrd_img)
    assert nrrd_img_array.shape[0] == len(
        pure_files
    ), "Number of slices from nrrd and dicom should be the same"

    for ith_slice in range(nrrd_img_array.shape[0]):
        nrrd_slice = nrrd_img_array[ith_slice, :, :]
        slice_i = pure_files[ith_slice]
        img_i = pydicom.dcmread(slice_i)
        print(
            f"{ith_slice}: nrrd shape:{nrrd_slice.shape}, "
            f"dicom slice shape:{img_i.pixel_array.shape}, "
            f"array equal:{(img_i.pixel_array == nrrd_slice).all()}"
        )


if __name__ == "__main__":
    # storeDicomSliceTags()
    # calculate_slice_distance()
    compare_dicom_slice_pixel_value_with_nrrd()
