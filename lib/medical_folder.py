import SimpleITK as sitk
from pathlib import Path
from dataclasses import dataclass
from typing import Sequence, Optional, Union, List
from lib.folder import BaseMedicalImageFolderMg
from lib.utility.define_class import STR_OR_PATH


@dataclass
class VolumeImage:
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


class MedicalImageFolderMg(BaseMedicalImageFolderMg):
    """Add more dicom handling functions to BaseMedicalImageFolderMg

    Args:
        BaseMedicalImageFolderMg: return images path given different image formats, currently supported
            - Meta Image: *.mha, *.mhd
            - Nifti Image: *.nia, *.nii, *.nii.gz, *.hdr, *.img, *.img.gz
            - Nrrd Image: *.nrrd, *.nhdr

    """

    def __init__(self, folderFullPath: STR_OR_PATH):
        super().__init__(folderFullPath)
        self.dicomSeries: Optional[Sequence[Path]] = None

    def readDicomSeries(self, folderPath: STR_OR_PATH):
        """Read dicom series from a folder

        Args:
            folderPath (STR_OR_PATH): folder path

        Returns:
            Sequence[Path]: a list of dicom files
        """
        if not self._isADicomSeries(folderPath):
            return []
        series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(folderPath))
        series_file_name = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(
            str(folderPath), series_IDs[0]
        )
        series_reader = sitk.ImageSeriesReader()
        series_reader.SetFileNames(series_file_name)
        series_reader.MetaDataDictionaryArrayUpdateOn()
        series_reader.LoadPrivateTagsOn()
        img = series_reader.Execute()
        return

    def readSitkImageAndStoreInfo(
        self, img: sitk.Image, printOut: bool = False
    ) -> VolumeImage:
        """Read sitk image and store image information"""
        volumeImg = VolumeImage()
        volumeImg.image = img
        volumeImg.dimension = img.GetDimension()
        volumeImg.spacing = img.GetSpacing()
        volumeImg.origin = img.GetOrigin()
        volumeImg.direction = img.GetDirection()
        volumeImg.width = img.GetWidth()
        volumeImg.height = img.GetHeight()
        volumeImg.depth = img.GetDepth()
        volumeImg.pixelIDValue = img.GetPixelIDValue()
        volumeImg.pixelIDType = img.GetPixelIDType()
        volumeImg.pixelIDTypeAsString = img.GetPixelIDTypeAsString()
        for k in volumeImg.necessaryTagsValue:
            volumeImg.necessaryTags[k] = img.GetMetaData(k)
        if printOut:
            print(f"Image Dimension: {volumeImg.dimension}")
            print(f"Image Spacing: {volumeImg.spacing}")
            print(f"Image Origin: {volumeImg.origin}")
            print(f"Image Direction: {volumeImg.direction}")
            print(f"Image Width: {volumeImg.width}")
            print(f"Image Height: {volumeImg.height}")
            print(f"Image Depth: {volumeImg.depth}")
            print(f"Image PixelIDValue: {volumeImg.pixelIDValue}")
            print(f"Image PixelIDType: {volumeImg.pixelIDType}")
            print(f"Image PixelIDTypeAsString: {volumeImg.pixelIDTypeAsString}")
            for k in volumeImg.necessaryTagsValue:
                print(f"Image Necessary Tags {k}: {volumeImg.necessaryTags[k]}")
        return img

    def _isADicomSeries(self, folderPath: STR_OR_PATH) -> bool:
        series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(folderPath))
        if not series_IDs:
            print(
                f"ERROR: given directory {folderPath} does not contain a DICOM series."
            )
            return False
        return True
