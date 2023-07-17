""" 2023.02.14 Kexin
test image registration of dataset from https://ultrastmedtech.feishu.cn/wiki/wikcnshQqwJm17JlOu5s0ec6Hld
"""
import matplotlib.image
import numpy as np
from pathlib import Path
import cv2
import pydicom
from lib.folder import FolderMg

testDataFolder = Path("data").joinpath("6-image-registration", "sorted_collected_data")


def getFixedAndMovingImage():
    np.set_printoptions(precision=3, suppress=True)
    dataMg = FolderMg(testDataFolder)
    assert dataMg.files is not None
    halfIdx = int(len(dataMg.files) / 2)
    fixedImagePaths = dataMg.files[:halfIdx]
    movingImagePaths = dataMg.files[halfIdx:]
    return fixedImagePaths, movingImagePaths


def saveDICOMToImages():
    fixedImagePaths, movingImagePaths = getFixedAndMovingImage()
    for fixed, moving in zip(fixedImagePaths, movingImagePaths):
        # Load the two images
        fixedDs = pydicom.dcmread(fixed)
        movingDs = pydicom.dcmread(moving)
        fixedImagePath = testDataFolder.joinpath(f"{fixed.name}.png")
        movingImagePath = testDataFolder.joinpath(f"{moving.name}.png")
        matplotlib.image.imsave(fixedImagePath, fixedDs.pixel_array)  # type: ignore
        matplotlib.image.imsave(movingImagePath, movingDs.pixel_array)  # type: ignore


def opencvSIFT():
    fixedImagePaths, movingImagePaths = getFixedAndMovingImage()
    for fixed, moving in zip(fixedImagePaths, movingImagePaths):
        # Load the two images
        fixedDs = pydicom.dcmread(fixed)
        movingDs = pydicom.dcmread(moving)
        fixedImage = fixedDs.pixel_array[:635, 340:1145]
        movingImage = movingDs.pixel_array[:635, 340:1145]

        # Convert the images to grayscale
        fixedGray = cv2.cvtColor(fixedImage, cv2.COLOR_BGR2GRAY)
        movingGray = cv2.cvtColor(movingImage, cv2.COLOR_BGR2GRAY)

        # Create a SIFT object
        sift = cv2.SIFT_create()

        # Detect keypoints and compute descriptors for the two images
        fixedKeyPoints = sift.detect(fixedGray, None)
        fixedImageKeyPoints = np.zeros_like(fixedGray)
        fixedImageKeyPoints = cv2.drawKeypoints(fixedGray, fixedKeyPoints, fixedImageKeyPoints)

        # Show the aligned images
        # cv2.imshow("Aligned Image", img_aligned)
        cv2.imshow("Fixed", fixedGray)
        cv2.imshow("Moving", movingGray)
        cv2.imshow("Fixed KeyPoints", fixedImageKeyPoints)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        break


saveDICOMToImages()
# opencvSIFT()
print("done")
