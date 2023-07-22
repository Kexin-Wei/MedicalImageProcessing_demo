import SimpleITK as sitk
from pathlib import Path
from typing import Sequence, Optional
from lib.folder import BaseMedicalImageFolderMg
from lib.utility.define_class import STR_OR_PATH
from lib.medical_image import VolumeImage


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
        self.dicomSeriesFolder: Optional[Sequence[Path]] = None
        self.dicomSeries: Optional[Sequence[VolumeImage]] = None
        self.findDicomSeriesFolder()
        self.readAllDicomSeries()

    def readAllDicomSeries(self) -> Sequence[VolumeImage]:
        """Read all dicom series from a folder

        Returns:
            Sequence[VolumeImage]: a list of dicom series
        """
        if self.dicomSeriesFolder is not None:
            print("No dicom series found, please read dicom series first")
            return []
        print("read all dicom series")
        for dicomFolder in self.dicomSeriesFolder:
            self.dicomSeries.append(self.readDicomSeries(dicomFolder))
            print(f"- {dicomFolder.name} read")
        return [self.readDicomSeries(folder) for folder in self.dicomSeriesFolder]

    def readDicomSeries(self, folderPath: STR_OR_PATH) -> VolumeImage:
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
        volumeImg = VolumeImage(img)
        return volumeImg

    def findDicomSeriesFolder(self):
        if self.dicomSeriesFolder is None:
            for folder in self.dirs:
                if self._isADicomSeries(folder):
                    print(f"- {folder.name} is a dicom series")
                    self.dicomSeriesFolder.append(folder)
                print(f"- {folder.name} is not a dicom series")
        print(
            f"found {len(self.dicomSeriesFolder)} dicom series already, skip this time"
        )

    def deleteDicomSeries(self):
        if self.dicomSeriesFolder is not None:
            self.dicomSeriesFolder = None
            print("delete dicom series")

    def _isADicomSeries(self, folderPath: STR_OR_PATH) -> bool:
        series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(folderPath))
        if not series_IDs:
            print(
                f"ERROR: given directory {folderPath} does not contain a DICOM series."
            )
            return False
        return True
