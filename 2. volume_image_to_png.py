"""2023.07.17 Kexin
read 3D meta image and nrrd image, save every slice to png
"""
from pathlib import Path
import SimpleITK as sitk
from lib.folder.med import BaseMedicalImageFolderMg, FolderMg


def transferMetaNrrdToPng():
    sourceDataPath = Path("D:/medical images/2D Segmentation/0-og volume images")
    sourceMg = BaseMedicalImageFolderMg(sourceDataPath)
    destinationPath = Path("data").joinpath("mri-prostate-slices")
    # sourceMg.ls()

    metaFile = sourceMg.getMetaImagePath()
    nrrdFile = sourceMg.get_nrrd_image_path()

    for f in nrrdFile:
        outputFolderPath = destinationPath.joinpath(f"{f.stem}")
        if not outputFolderPath.exists():
            outputFolderPath.mkdir(parents=True)
        print(f"- {f.name}")
        nrrdImg = sitk.ReadImage(f, imageIO="NrrdImageIO")
        sitk.WriteImage(
            sitk.Cast(sitk.RescaleIntensity(nrrdImg), sitk.sitkUInt8),
            [
                outputFolderPath.joinpath(f"slice{i}.png")
                for i in range(nrrdImg.GetSize()[-1])
            ],
        )

    for f in metaFile:
        print(f"- {f.name}")
        outputFolderPath = destinationPath.joinpath(f"{f.stem}")
        if not outputFolderPath.exists():
            outputFolderPath.mkdir(parents=True)
        metaImg = sitk.ReadImage(f, imageIO="MetaImageIO")
        sitk.WriteImage(
            sitk.Cast(sitk.RescaleIntensity(metaImg), sitk.sitkUInt8),
            [
                outputFolderPath.joinpath(f"slice{i}.png")
                for i in range(metaImg.GetSize()[-1])
            ],
        )
    print("Done")


def transferDicomSeriesToPng():
    sourceDataPath = Path("D:/medical images/2D Segmentation/1-dicom slices")
    sourceMg = FolderMg(sourceDataPath)
    destinationPath = Path("data").joinpath("mri-prostate-slices-resample")
    # sourceMg.ls()
    reader = sitk.ImageSeriesReader()
    for dicomFolder in sourceMg.dirs:
        dicomNames = reader.GetGDCMSeriesFileNames(str(dicomFolder))
        reader.SetFileNames(dicomNames)
        dicomFile = reader.Execute()
        size = dicomFile.GetSize()
        outputFolderPath = destinationPath.joinpath(f"{dicomFolder.name}")
        if not outputFolderPath.exists():
            outputFolderPath.mkdir(parents=True)
        sitk.WriteImage(
            sitk.Cast(sitk.RescaleIntensity(dicomFile), sitk.sitkUInt8),
            [
                outputFolderPath.joinpath(f"slice{i}.png")
                for i in range(dicomFile.GetSize()[-1])
            ],
        )


if __name__ == "__main__":
    # transferMetaNrrdToPng()
    transferDicomSeriesToPng()
