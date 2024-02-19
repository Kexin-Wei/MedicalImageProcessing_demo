"""2023.07.18 Kexin
convert 3D volume image to dicom series
"""
import time
import natsort
import SimpleITK as sitk
import numpy as np
from pathlib import Path
from lib.folder.basic import FolderMg
from lib.folder.med import DicomImageFolderMg, BaseMedicalImageFolderMg


def fromDicomSeriesToDicomSeries():
    sourceDataPath = Path("D:/medical images/2D Segmentation/1-dicom slices")
    sourceMg = FolderMg(sourceDataPath)
    destinationPath = Path("data").joinpath("mri-prostate-slices-unsigned")
    sourceMg.ls()

    reader = sitk.ImageSeriesReader()
    for dicomFolder in sourceMg.dirs:
        dicomNames = reader.GetGDCMSeriesFileNames(str(dicomFolder))
        reader.SetFileNames(dicomNames)
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        dicomFile = reader.Execute()
        spacing = dicomFile.GetSpacing()
        print(f"- dicom folder:{dicomFolder.name}", end="")

        max, min = 0, 0
        for slice in range(dicomFile.GetDepth()):
            sliceImage = dicomFile[:, :, slice]
            sliceImageArray = sitk.GetArrayFromImage(sliceImage).astype(np.int32)
            sliceImageArray = sliceImageArray + 32768
            sliceImageArray = sliceImageArray.astype(np.uint16)
            if slice == 0:
                print(
                    f"sliceImage Type:{sliceImage.GetPixelIDTypeAsString()}, slice type:{sliceImageArray.dtype}"
                )
            if sliceImageArray.max() > max:
                max = sliceImageArray.max()
            if sliceImageArray.min() < min:
                min = sliceImageArray.min()

            # sliceNewImage = sitk.Cast(sliceImage, sitk.sitkUInt16)
            sliceNewImage = sitk.GetImageFromArray(sliceImageArray)
            sliceNewImage.SetSpacing(spacing)
            metaData = reader.GetMetaDataKeys(slice)
            for key in metaData:
                # print(f"key:{key}, value:{reader.GetMetaData(slice, key)}")
                sliceNewImage.SetMetaData(key, reader.GetMetaData(slice, key))

            outputPath = destinationPath.joinpath(dicomFolder.name)
            if not outputPath.exists():
                outputPath.mkdir(parents=True)
            writer = sitk.ImageFileWriter()
            writer.SetFileName(str(outputPath.joinpath(f"Slice{slice}.dcm")))
            writer.KeepOriginalImageUIDOn()
            writer.Execute(sliceNewImage)
        print(f", max:{max}, min:{min}")
        print(
            f", pixel type:{dicomFile.GetPixelIDTypeAsString()}, cast to {sliceImage.GetPixelIDTypeAsString()}"
        )


def writeSlices(writer, series_tag_values, new_img, out_dir, i):
    image_slice = new_img[:, :, i]

    # Tags shared by the series.
    list(
        map(
            lambda tag_value: image_slice.SetMetaData(tag_value[0], tag_value[1]),
            series_tag_values,
        )
    )

    # Slice specific tags.
    #   Instance Creation Date
    image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))
    #   Instance Creation Time
    image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))

    # Setting the type to CT so that the slice location is preserved and
    # the thickness is carried over.
    image_slice.SetMetaData("0008|0060", "CT")

    # (0020, 0032) image position patient determines the 3D spacing between
    # slices.
    #   Image Position (Patient)
    image_slice.SetMetaData(
        "0020|0032",
        "\\".join(map(str, new_img.TransformIndexToPhysicalPoint((0, 0, i)))),
    )
    #   Instance Number
    image_slice.SetMetaData("0020|0013", str(i))

    # Write to the output directory and add the extension dcm, to force
    # writing in DICOM format.
    writer.SetFileName(str(Path(out_dir).joinpath(f"{i}.dcm")))
    writer.Execute(image_slice)


def checkOverflow(array: np.ndarray, type: np.dtype) -> bool:
    if array.max() > np.iinfo(type).max:
        print(f"Overflow! max:{array.max()}, type:{type}")
        return True
    if array.min() < np.iinfo(type).min:
        print(f"Overflow! min:{array.min()}, type:{type}")
        return True
    return False


def fromNrrdMetaFileToDicomSeries():
    sourceDataPath = Path("D:/medical images/2D Segmentation/0-og volume images")
    destinationPath = Path("data").joinpath(
        "mri-prostate-slices-unsigned-og-normalized"
    )
    sourceMg = BaseMedicalImageFolderMg(sourceDataPath)
    nrrdFiles = sourceMg.get_nrrd_image_path()
    metaFiles = sourceMg.getMetaImagePath()
    # sourceMg.ls()
    print(
        f"Start processing {len(nrrdFiles)} nrrd files and {len(metaFiles)} meta files"
    )
    allFiles = natsort.natsorted(nrrdFiles + metaFiles)
    for file in allFiles:
        img = sitk.ReadImage(str(file))
        print(
            f"- {file.name}, type:{img.GetPixelIDTypeAsString()}, type:{img.GetPixelIDValue()}",
            end="...",
        )

        og_size = img.GetSize()
        og_spacing = img.GetSpacing()
        new_spacing = [og_spacing[0], og_spacing[1], og_spacing[2] * 2]
        new_size = [og_size[0], og_size[1], int(og_size[2] / 2)]
        resampleImg = sitk.Resample(
            image1=img,
            size=new_size,
            outputSpacing=new_spacing,
            outputOrigin=img.GetOrigin(),
            outputDirection=img.GetDirection(),
            outputPixelType=img.GetPixelID(),
        )

        outputPath = destinationPath.joinpath(file.stem)
        if not outputPath.exists():
            outputPath.mkdir(parents=True)
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()

        direction = img.GetDirection()
        modification_time = time.strftime("%H%M%S")
        modification_date = time.strftime("%Y%m%d")
        series_tag_values = [
            ("0008|0031", modification_time),  # Series Time
            ("0008|0021", modification_date),  # Series Date
            ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
            (
                "0020|000e",
                "1.2.826.0.1.3680043.2.1125."
                + modification_date
                + ".1"
                + modification_time,
            ),  # Series Instance UID
            (
                "0020|0037",
                "\\".join(
                    map(
                        str,
                        (
                            direction[0],
                            direction[3],
                            direction[6],
                            direction[1],
                            direction[4],
                            direction[7],
                        ),
                    )
                ),
            ),  # Image Orientation
            # (Patient)
            ("0008|103e", "Created-SimpleITK"),  # Series Description
        ]

        imgArray = sitk.GetArrayFromImage(resampleImg).astype(np.int64)
        # normalize to 0 to 1899
        imgArray = imgArray - imgArray.min()
        imgArray = imgArray * 1.0 / imgArray.max() * 1899
        if checkOverflow(imgArray, np.uint16):
            continue
        imgArray = imgArray.astype(np.uint16)
        new_img = sitk.GetImageFromArray(imgArray)
        new_img.SetSpacing(new_spacing)
        new_img.SetOrigin(img.GetOrigin())
        new_img.SetDirection(img.GetDirection())

        # Write slices to output directory
        list(
            map(
                lambda i: writeSlices(
                    writer, series_tag_values, new_img, outputPath, i
                ),
                range(new_img.GetDepth()),
            )
        )
        print(f"finished!")


if __name__ == "__main__":
    # fromDicomSeriesToDicomSeries()
    # fromNrrdMetaFileToDicomSeries()

    # from dicom series to dicom series
    sourceDataPath = Path("D:/medical images/2D Segmentation/1-dicom slices")
    sourceMg = DicomImageFolderMg(sourceDataPath)
    print("Finished!")
