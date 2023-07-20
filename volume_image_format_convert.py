"""2023.07.18 Kexin
convert 3D volume image to dicom series
"""
import SimpleITK as sitk
import numpy as np
from pathlib import Path
from lib.folder import FolderMg

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
        print(f", pixel type:{dicomFile.GetPixelIDTypeAsString()}, cast to {sliceImage.GetPixelIDTypeAsString()}")

if __name__ == "__main__":
    fromDicomSeriesToDicomSeries()
    print("Finished!")
