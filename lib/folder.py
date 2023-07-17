"""created by kx 20221104
Several folder Managers based on folderMeg, including:
    - pgmFolderMg: manage the pgm files inside the folder
    - parentFolderMg: manage the child directories inside the folder
"""
import pathlib
import natsort
import numpy as np
from typing import Sequence, Optional, Union, List

from lib.utility.define_class import STR_OR_PATH, STR_OR_LIST, PATH_OR_LIST, DIR_OR_FILE


class FolderMgBase:
    """
    A Base Class to manage files and folders inside a parent folder, functions include:
        - set path 
        - get a list of file names and another list of directories name
        - tags function:
            - add tag to the pgmFolder, eg, "f3.5","lowAttention"
            - check whether a tag is inside pgmFolder
            - list all the tags
    """

    def __init__(self):
        self.fullPath: Optional[pathlib.Path] = None
        self.parentFolder = None
        self.folderName = None
        self.tags = None
        self.dirs: Optional[Sequence[pathlib.Path]] = None
        self.files: Optional[Sequence[pathlib.Path]] = None

    @staticmethod
    def _strToList(anyStr: STR_OR_LIST) -> list:
        if isinstance(anyStr, str):
            return [anyStr]
        if isinstance(anyStr, list):
            return anyStr
        print("Input is not a str or list.")
        return []

    @staticmethod
    def _pathToList(anyPath: PATH_OR_LIST) -> list:
        if isinstance(anyPath, pathlib.Path):
            return [anyPath]
        if isinstance(anyPath, list):
            return anyPath
        print("Input is not a pathlib.Path or list.")
        return []

    def _getFilesDirs(self):
        if self.fullPath is not None:
            self.dirs = [p for p in self.fullPath.iterdir() if p.is_dir()]
            self.files = [f for f in self.fullPath.iterdir() if f.is_file()]
            self.dirs = natsort.natsorted(self.dirs)
            self.files = natsort.natsorted(self.files)

    def _getFilePathByExtension(self, extension: str) -> List[pathlib.Path]:
        # put extension in a pure string without . and *, e.g. python file input "py"
        assert self.fullPath is not None
        return natsort.natsorted(self.fullPath.glob(f"*.{extension}"))

    def _getFilePathByExtensionList(self, extensions: list) -> List[pathlib.Path]:
        assert self.fullPath is not None
        files = []
        for e in extensions:
            files.extend(natsort.natsorted(self.fullPath.glob(f"*.{e}")))
        return files

    def getRandomFile(self, printOut: bool = True) -> pathlib.Path:

        if self.files is not None and len(self.files) != 0:
            randomIdx = np.random.randint(low=0, high=len(self.files))
            if printOut:
                print(
                    f"Get File with idx: {randomIdx}, name: {self.files[randomIdx].name}, in folder: {self.folderName}")
            return self.files[randomIdx]
        print(f"{self.folderName} contains NO files\n")
        return pathlib.Path()

    @property
    def nFile(self) -> Optional[int]:
        if self.files is not None:
            return len(self.files)

    @property
    def nDirs(self) -> Optional[int]:
        if self.dirs is not None:
            return len(self.dirs)


class FolderMg(FolderMgBase):
    """
    functions:
        1. sort files by types
        2. ls files and dirs
    """

    def __init__(self, folderFullPath: STR_OR_PATH = pathlib.Path()):
        super().__init__()
        self.fullPath = pathlib.Path(folderFullPath)
        self.parentFolder = self.fullPath.parent
        self.folderName = self.fullPath.name
        self._getFilesDirs()

    def ls(self, lsOption: Optional[DIR_OR_FILE] = None) -> None:
        if lsOption == "dir" or lsOption is None:
            if self.dirs is None or len(self.dirs) == 0:
                print(f"\nCurrent Folder '{self.folderName}' contains NO folders\n")
            else:
                print(f"\nCurrent Folder '{self.folderName}' contains {len(self.dirs)} folders, which are:")
                for d in self.dirs[:5]:
                    print(f"  - {d.name}")
                print(f"  - ...")
        if lsOption == "file" or lsOption is None:
            if self.files is None or len(self.files) == 0:
                print(f"\nCurrent Folder '{self.folderName}' contains NO files\n")
            else:
                print(f"\nCurrent Folder '{self.folderName}' contains {len(self.files)} files, which are:")
                for f in self.files[:5]:
                    print(f"  - {f.name}")
                print(f"  - ...")


class FolderTagMg(FolderMgBase):
    """
    add tags to list of folders manually
    """

    def __init__(self, fullPath: STR_OR_PATH = pathlib.Path(), tags: Optional[STR_OR_LIST] = None):
        if tags is None:
            tags = []
        super().__init__()
        self.fullPath = pathlib.Path(fullPath)
        self.parentFolder = self.fullPath.parent
        self.folderName = self.fullPath.name
        self._getFilesDirs()
        self.tags = set(self._strToList(tags))

    def addTags(self, tags: STR_OR_LIST):
        tags = self._strToList(tags)
        for t in tags:
            self.tags.add(t)

    def containsTag(self, tag: str) -> bool:
        return tag in self.tags

    def lsTags(self):
        print(f"\nCurrent Folder '{self.folderName}' contains tags:")
        for t in self.tags:
            print(f"  - {t}")


class MedicalImageFolderMg(FolderMg):
    """
    return images path given different image formats, currently supported
        - Meta Image: *.mha, *.mhd
        - Nifti Image: *.nia, *.nii, *.nii.gz, *.hdr, *.img, *.img.gz
        - Nrrd Image: *.nrrd, *.nhdr
    """

    def __init__(self, folderFullPath: STR_OR_PATH = pathlib.Path()):
        super().__init__(folderFullPath)

    def getNrrdImagePath(self) -> List[pathlib.Path]:
        # *.nrrd, *.nhdr
        return self._getFilePathByExtensionList(["nrrd", "nhdr"])

    def getMetaImagePath(self) -> List[pathlib.Path]:
        # *.mha, *.mhd
        return self._getFilePathByExtensionList(["mha", "mhd"])

    def getNiftiImagePath(self) -> List[pathlib.Path]:
        # *.nia, *.nii, *.nii.gz, *.hdr, *.img, *.img.gz
        return self._getFilePathByExtensionList(["nia", "nii", "nii.gz", "hdr", "img", "img.gz"])


FOLDERMG_OR_PATH_OR_STR = Union[FolderMg, pathlib.Path, str]


class T2FolderMg(FolderMg):
    """
    Find certain file in a net-structure folder, which has multiple folders that contain their own folders inside them
    """

    def __init__(self, folderFullPath: STR_OR_PATH = pathlib.Path()):
        super().__init__(folderFullPath)
        self.t2List = []

    def getT2(self):
        self.t2List.extend(self.searchT2inCurrentFolder())
        if self.nDirs:
            for d in self.dirs:
                # print("\n--------------------------------------------")
                # print(f"In folder {d}")
                cMg = T2FolderMg(d)
                cMg.getT2()
                self.t2List.extend(cMg.t2List)

    def searchT2inCurrentFolder(self):
        if self.nFile:
            t2List = []
            for f in self.files:
                if "t2" in f.name.lower() and ("mha" in f.suffix or "nrrd" in f.suffix):
                    if "_cor" not in f.name.lower() and "_sag" not in f.name.lower():
                        t2List.append(f)
                        print(f)
            return t2List
        return []
