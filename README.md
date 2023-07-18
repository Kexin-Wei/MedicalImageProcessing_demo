# ITKMedicalImageProcessing_demo

A repo based on ITK to processing medical images

# Main Features

1. `medical_image_registration.py`: 2D image registration to get motion displacement using OpenCV
2. `volume_image_to_png.py`: read 3D meta image and nrrd image, save every slice to png
3. `sam_segment_mri_prostate.py`: using [Segment-Anything](https://github.com/facebookresearch/segment-anything) pretrained model to segment prostate mri slice by slice

# Additional Functions

1. `f_convertToNifti.py`: reading all the medical images in the designated folder, and convert them into nifti images to
   predict for nnUNet
    - supported formats:
        - *.nrrd, "NrrdImageIO"
        - *.mha, "MetaImageIO"
2. `f_findAllT2.py`: Find all images with string "t2" inside their names, do deep into each folder, and eventually
   save all the path of each image into an Excel