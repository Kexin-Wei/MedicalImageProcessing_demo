import shutil
from pathlib import Path

from lib.folder.basic import FolderMg


def convert_real_patient_to_test_result():
    source_path = Path("D:/Medical Image - Research/Segmentation_test_image").joinpath("real_patient")
    target_path = Path("D:/Medical Image - Research/Segmentation_test_image").joinpath("test_result")

    folder_mg = FolderMg(source_path)
    folder_mg.ls()

    start_number = 200
    # open a  file
    with open(target_path.joinpath("mapping.txt"), "w") as file:
        for i, f in enumerate(folder_mg.files):
            target_file = target_path.joinpath(f"Ultrast_{str(start_number + i).zfill(3)}_0000.nii.gz")
            shutil.copy2(f, target_file)
            print(f"{i} - Copying {f} to {target_file}", file=file)


def real_stem(file: Path):
    return file.name.split(".")[0]


def combine_old_new_model_result():
    source_path = Path(
        "D:/Medical Image - Research/Clinical Data Prostate Segmentation Image Packages/Comparison test data")
    old_result_path = source_path.joinpath("old_comparison_result")
    new_result_path = source_path.joinpath("new_comparison_result")
    source_folder_mg = FolderMg(source_path)
    old_folder_mg = FolderMg(old_result_path)
    new_folder_mg = FolderMg(new_result_path)
    old_folder_mg.ls()
    new_folder_mg.ls()
    target_path = source_path.joinpath("sorted_data")

    for i, og_file in enumerate(source_folder_mg.files):
        file_folder = target_path.joinpath(real_stem(Path(og_file)))
        file_folder.mkdir(parents=True, exist_ok=True)
        old_result = old_folder_mg.files[i]
        new_result = new_folder_mg.files[i]
        shutil.copy2(og_file, file_folder.joinpath(og_file.name))
        shutil.copy2(old_result, file_folder.joinpath(f"{real_stem(old_result)}_old{''.join(old_result.suffixes)}"))
        shutil.copy2(new_result, file_folder.joinpath(f"{real_stem(new_result)}_new{''.join(new_result.suffixes)}"))
        assert real_stem(old_result) == real_stem(new_result)


if __name__ == "__main__":
    # convert_real_patient_to_test_result()
    combine_old_new_model_result()
