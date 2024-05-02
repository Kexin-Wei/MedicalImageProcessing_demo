"""kx 2024.1.19
sort data for erinn in each pair in each folder
"""

import os
import shutil


def sort_old_dataset_for_erinn():
    from pathlib import Path
    from lib.folder.basic import FolderMg

    imgPath = Path(
        "D:\Medical Image - Research\Clinical Data Prostate Segmentation Image Packages\Dataset078_UltrastProstate"
    )
    labelPath = imgPath.joinpath("labels")
    destPath = imgPath.parent.joinpath("Dataset078_UltrastProstate_erinn")

    imgFolderMg = FolderMg(imgPath)
    labelFolderMg = FolderMg(labelPath)

    imgFolderMg.ls()
    labelFolderMg.ls()

    index = 0
    for img, label in zip(imgFolderMg.files, labelFolderMg.files):
        if img.name == label.name:  # check if the file names are the same
            print(f"{index}.{img.name}")
            index += 1

            # Create a new directory
            folder_i = destPath.joinpath(f"{index}.{img.name}")
            if not folder_i.exists():
                folder_i.mkdir(parents=True)

            # Move the files to the new directory, with new name
            new_label = folder_i.joinpath(f"label_{label.name}")
            shutil.copy(label, new_label)
            shutil.copy(img, folder_i.joinpath(img.name))


if __name__ == "__main__":
    sort_old_dataset_for_erinn()
