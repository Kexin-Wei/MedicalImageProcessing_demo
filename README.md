# ITKMedicalImageProcessing_demo

A repo based on ITK to processing medical images

# Main Features

1. `medical_image_registration.py`: 2D image registration to get motion displacement using OpenCV
2. `volume_image_to_png.py`: read 3D meta image and nrrd image, save every slice to png
3. `volume_image_format_convert.py`: convert 3D volume image to dicom series
4. `sam_segment_mri_prostate.py` and `SAM.ipynb` and : using [Segment-Anything](https://github.com/facebookresearch/segment-anything) pretrained model to segment prostate mri slice by slice
   - `SAM.ipynb`: try SAM on prostate
   - `MedSAM.ipynb`: try MedSAM on prostate
5. `ConstructOwnDataset.ipynb`: build dataset to feed to nnUNet2 training
6. `4d_dicom_reader.py`: test dicom reading for 4D dicom image
7. `prostate_canser_segmentation.py`: use region grow or k-means functions to find the cancer
8. `systematic_biopsy_plan.py`: plan 10/12 core systematic biopsy points


# Additional Functions

1. `f_convertToNifti.py`: reading all the medical images in the designated folder, and convert them into nifti images to
   predict for nnUNet
    - supported formats:
        - *.nrrd, "NrrdImageIO"
        - *.mha, "MetaImageIO"
2. `f_findAllT2.py`: Find all images with string "t2" inside their names, do deep into each folder, and eventually
   save all the path of each image into an Excel

3. `f_sort_data_for_erinn.py`: Sort the data in segmentation dataset in pair and put into different folders