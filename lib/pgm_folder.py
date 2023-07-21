from pathlib import Path
import natsort

from typing import Dict, Optional

from lib.utility.define_class import STR_OR_PATH, STR_OR_LIST, PATH_OR_LIST
from .pgm import PGMFile
from .folder import FolderMgBase, FolderTagMg


class PgmFolder(FolderTagMg):
    """
    A Child Class of folderMgBase to manage the pgm files inside folder, functions include:
        - all parent functions
        - list all the pgm files
        - read pgm files inside the folder
        - read one pgm file in the list of file names, eg, readNextFile()

    """

    def __init__(self, fullPath: STR_OR_PATH, tags: Optional[STR_OR_LIST] = None):
        if tags is None:
            tags = []
        super().__init__(fullPath, tags)
        self._getPGMFiles()
        self.currentFileIndex = 0
        self.currentPgm = None

    def _getPGMFiles(self):
        assert self.files is not None
        self.files = [f for f in self.files if f.suffix == ".pgm"]

    def ls(self):
        assert self.files is not None
        print(
            f"\nCurrent Folder '{self.folderName}' contains {len(self.files)} pgm files, which are:"
        )
        nListed = 0
        for f in self.files:
            print(f"  - {f.name}")
            nListed += 1
            if nListed > 20:
                print("  - ...")
                break

    def readCurrentFile(self, printOut: bool = True) -> PGMFile:
        assert self.files is not None
        if self.currentFileIndex == 0 and printOut:
            print(f"\nStart reading folder {self.fullPath}")
        self.currentPgm = PGMFile(self.files[self.currentFileIndex], printOut=False)
        if printOut:
            print(
                f"- File idx: {self.currentFileIndex}, name:{self.currentPgm.fileName}, in folder: {self.folderName}"
            )
        return self.currentPgm

    def readNextPgm(self):
        self.currentFileIndex += 1
        return self.readCurrentFile()

    def readRandomPgm(self, printOut: bool = True) -> PGMFile:
        return PGMFile(self.getRandomFile(printOut=printOut), printOut=False)

    def saveBModes(
        self,
        imageRootFolderPath: Optional[STR_OR_PATH] = None,
        upperDisplayRangeDb: Optional[int] = None,
        lowerDisplayRangeDb: Optional[int] = None,
        replace: bool = False,
    ):
        assert isinstance(self.fullPath, Path)
        if imageRootFolderPath is None:
            imageRootFolderPath = self.fullPath.parent
        imageRootFolderPath = Path(imageRootFolderPath)
        imageFolderPath = imageRootFolderPath.joinpath(f"{self.folderName}_b-mode")
        assert self.files is not None
        for f in self.files:
            pgmFile = PGMFile(f, printOut=False)
            pgmFile.saveBMode(
                imageFolderPath,
                upperDisplayRangeDb=upperDisplayRangeDb,
                lowerDisplayRangeDb=lowerDisplayRangeDb,
                replace=replace,
            )


class ParentFolderTagMg(FolderTagMg):
    """
    A Child Class of folderMgBase to manage all the pgm Folder, functions include:
        - all parent functions
        - list all the dirs
        - return any folder as pgmFolderMg in the list given index of the list
    """

    def __init__(self, fullPath: STR_OR_PATH, tags: Optional[STR_OR_LIST] = None):
        if tags is None:
            tags = []
        super().__init__(fullPath, tags)

    def createNewFolderList(self, folders: STR_OR_LIST):
        # remove all the folders, and refill with new ones
        folders = self._strToList(folders)
        self.dirs = []
        assert isinstance(self.fullPath, Path)
        for fd in folders:
            fdPath = self.fullPath.joinpath(fd)
            if fdPath.exists():
                self.dirs.append(fdPath)
            else:
                print(f"Folder {fd} doesn't exist.")

    def ls(self):
        assert self.dirs is not None
        print(
            f"\nCurrent Folder '{self.folderName}' contains {len(self.dirs)}, which are:"
        )
        for d in self.dirs:
            print(f"  - {d.name}")

    def readPgmFolder(self, idx: int) -> PgmFolder:
        assert self.dirs is not None
        return PgmFolder(self.dirs[idx])


class PgmFolderTagMg(FolderMgBase):
    """
    A Child Class of folderMgBase to manage folders by tags:
        - all parent functions
        - add list of Path() or a single one with tags to group them
        - list all the included folders with their tags
        - return a list of folder given searched tags
    """

    def __init__(self, folders: Optional[PATH_OR_LIST] = None):
        if folders is None:
            folders = []
        super().__init__()
        self.folderList: Dict[
            Path, PgmFolder
        ] = dict()  # key = path, value = store the folderMgBase type of folders
        self.tagGroup: Dict[str, list[PgmFolder]] = dict()
        folders = self._pathToList(folders)
        for fd in folders:
            self.folderList[fd] = PgmFolder(fd)

    def addTagsByFolderName(self, tags: STR_OR_LIST) -> None:
        """
        only for the folders in the self.folderList
        """
        tags = self._strToList(tags)
        for t in tags:
            if t not in self.tagGroup.keys():
                self.tagGroup[t] = []  # create new list for new tag.value
            for pgmFmg in self.folderList.values():
                if (
                    f"_{t}" in pgmFmg.folderName
                ):  # !!!HARDCODE:avoid find 7.5mhz using 5mhz
                    pgmFmg.addTags(t)
                    self.tagGroup[t].append(pgmFmg)

    def addGroup(self, folders: PATH_OR_LIST, tags: STR_OR_LIST) -> None:
        tags = self._strToList(tags)
        folders = self._pathToList(folders)

        for t in tags:
            if t not in self.tagGroup.keys():
                self.tagGroup[t] = []  # create new list for new tag.value

        for fd in folders:
            if fd not in self.folderList.keys():
                self.folderList[fd] = PgmFolder(fd)  # only create once
            self.folderList[fd].addTags(tags)
            for t in tags:
                self.tagGroup[t].append(PgmFolder(fd))

    def findByTags(self, tags: STR_OR_LIST) -> list[PgmFolder]:
        tags = self._strToList(tags)
        if len(tags) == 1:
            if tags[0] in self.tagGroup.keys():
                return self.tagGroup[tags[0]]
            else:
                print(f"No such tag '{tags}' in the list of tags")
                return []

        resultGroup = set(self.tagGroup[tags[0]])
        for ithTag in range(len(tags) - 1):
            if not resultGroup:
                print(f"No common folder found.")
                return []
            resultGroup = resultGroup.intersection(self.tagGroup[tags[ithTag + 1]])
        return list(resultGroup)

    def lsByTag(self, tag: str) -> None:
        if tag in self.tagGroup.keys():
            print(f'\nTag "{tag}" contains folders')
            for fp in self.tagGroup[tag]:
                print(f"  - {fp.fullPath}")
        else:
            print(f"No such tag '{tag}' in the list of tags")

    def ls(self) -> None:
        print(f"\nFolder Manager contains folders as following:")
        for fmg in self.folderList.values():
            print(f"- {fmg.folderName}", end="")
            if len(fmg.tags) != 0:
                print(", \ttags: ", end="")
                for t in natsort.natsorted(fmg.tags):
                    print(f"{t} ", end="")
                print()
