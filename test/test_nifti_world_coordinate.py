import nibabel as nib
import numpy as np


# Load the nifti file
def test_load_nifti_file():
    nifti_file = nib.load(
        "D:/Medical Image - Example/Real-Patient-Data/PatientA.nii.gz"
    )
    assert nifti_file is not None
