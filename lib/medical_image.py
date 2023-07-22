import time
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from dataclasses import dataclass
from lib.utility.define_class import STR_OR_PATH


class VolumeImageInfo:
    """Volume image information for fast and simple access

    Attributes:
        image (sitk.Image): sitk image
        imageType (str): image type, e.g. MetaImage, NiftiImage, NrrdImage
        dimension (int): image dimension, e.g. 2, 3
        spacing (tuple): image spacing, e.g. (1.0, 1.0, 1.0)
        origin (tuple): image origin, e.g. (0.0, 0.0, 0.0)
        direction (tuple): image direction, e.g. (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        width (int): image width, e.g. 512
        height (int): image height, e.g. 512
        depth (int): image depth, e.g. 512
        pixelIDValue (int): pixel ID value, e.g. 8, 16, 32
        pixelIDType (str): pixel ID type, e.g. scalar, vector, offset
        pixelIDTypeAsString (str): pixel ID type as string, e.g. unsigned char, unsigned short, float

    """

    image: sitk.Image
    dimension: int
    spacing: tuple
    origin: tuple
    direction: tuple
    width: int
    height: int
    depth: int
    pixelIDValue: int
    pixelIDType: str
    pixelIDTypeAsString: str
    necessaryTags: dict
    necessaryTagsValue: list[str] = [
        "0010|0010",  # Patient Name
        "0010|0020",  # Patient ID
        "0010|0030",  # Patient Birth Date
        "0020|000D",  # Study Instance UID, for machine consumption
        "0020|0010",  # Study ID, for human consumption
        "0008|0008",  # Image Type
        "0008|0020",  # Study Date
        "0008|0030",  # Study Time
        "0008|0050",  # Accession Number
        "0008|0060",  # Modality
    ]
    path: Path


@dataclass(init=False)
class VolumeImage(VolumeImageInfo):
    def __init__(self, image: sitk.Image, path: STR_OR_PATH) -> None:
        super().__init__()
        self.image = image
        self.dimension = image.GetDimension()
        self.spacing = image.GetSpacing()
        self.origin = image.GetOrigin()
        self.direction = image.GetDirection()
        self.width = image.GetWidth()
        self.height = image.GetHeight()
        self.depth = image.GetDepth()
        self.pixelIDValue = image.GetPixelIDValue()
        self.pixelIDType = image.GetPixelIDType()
        self.pixelIDTypeAsString = image.GetPixelIDTypeAsString()
        for k in self.necessaryTagsValue:
            self.necessaryTags[k] = image.GetMetaData(k)
        self.path = Path(path)

    def printOut(self):
        print(f"Image Dimension: {self.dimension}")
        print(f"Image Spacing: {self.spacing}")
        print(f"Image Origin: {self.origin}")
        print(f"Image Direction: {self.direction}")
        print(f"Image Width: {self.width}")
        print(f"Image Height: {self.height}")
        print(f"Image Depth: {self.depth}")
        print(f"Image PixelIDValue: {self.pixelIDValue}")
        print(f"Image PixelIDType: {self.pixelIDType}")
        print(f"Image PixelIDTypeAsString: {self.pixelIDTypeAsString}")
        for k in self.necessaryTagsValue:
            print(f"Image Necessary Tags {k}: {self.necessaryTags[k]}")
        print(f"Image Path: {self.path}")

    def writeSlicesToDicom(self, outputPath: STR_OR_PATH):
        if not outputPath.exists():
            outputPath.mkdir(parents=True)
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()
        for slice in range(self.depth):
            sliceImage = self.image[:, :, slice]
            sliceImage.SetMetaData("0008|0012", time.strftime("%Y%m%d"))
            sliceImage.SetMetaData("0008|0013", time.strftime("%H%M%S"))
            writer.SetFileName(str(outputPath.joinpath(f"Slice{slice}.dcm")))
            writer.Execute(self.image[:, :, slice])
        print(f"write {self.depth} slices to {outputPath}")

    def writeToPng(self, outputPath: STR_OR_PATH, pngFormat=sitk.sitkUInt16):
        if not outputPath.exists():
            outputPath.mkdir(parents=True)
        sitk.WriteImage(
            sitk.Cast(sitk.RescaleIntensity(self.image), pngFormat),
            [outputPath.joinpath(f"slice{i}.png") for i in range(self.depth)],
        )

    def convertImageType(self, newImageType: sitk.Image) -> sitk.Image:
        return sitk.Cast(self.image, newImageType)

    def changeToUInt16(self, rescale: int = None) -> sitk.Image:
        newImageArray = sitk.GetArrayFromImage(self.image).astype(np.int64)
        for slice in range(self.depth):
            sliceImage = self.image[:, :, slice]
            sliceImageArray = sitk.GetArrayFromImage(sliceImage).astype(np.int64)
            sliceImageArray = sliceImageArray - sliceImageArray.min()
            if rescale is not None:
                sliceImageArray = sliceImageArray * rescale / sliceImageArray.max()
            sliceImageArray = sliceImageArray.astype(np.uint16)
            if slice == 0:
                print(
                    f"sliceImage Type:{sliceImage.GetPixelIDTypeAsString()}, slice type:{sliceImageArray.dtype}"
                )
            if sliceImageArray.max() > max:
                max = sliceImageArray.max()
            if sliceImageArray.min() < min:
                min = sliceImageArray.min()
            newImageArray[slice] = sliceImageArray

        newImage = sitk.GetImageFromArray(newImageArray)
        newImage.SetSpacing(self.spacing)
        newImage.SetOrigin(self.origin)
        newImage.SetDirection(self.direction)
        newImage.SetMetaData("0008|0012", time.strftime("%Y%m%d"))
        newImage.SetMetaData("0008|0013", time.strftime("%H%M%S"))
        # TODO metaData vs necessaryTagsValue
        # for key in self.metaData:
        # print(f"key:{key}, value:{reader.GetMetaData(slice, key)}")
        # sliceNewImage.SetMetaData(key, reader.GetMetaData(slice, key))
        return newImage
