import numpy as np
import cv2
from .utility.define_class import INT_OR_FLOAT, FOUR_OR_EIGHT


class ImageProcessor:
    def __init__(self):
        pass

    @staticmethod
    def binary(image: np.ndarray, threshold: INT_OR_FLOAT = 0, dtype=None) -> np.ndarray:
        binaryImage = image > threshold
        if dtype is not None:
            binaryImage = binaryImage.astype(dtype)
        return binaryImage

    @staticmethod
    def removeIsolatedPoint(image: np.ndarray, connectionType: FOUR_OR_EIGHT = "4-point-connected") -> np.ndarray:
        """
        :param image: a numpy array
        :param connectionType: either "4-point-connected" or "4-point-connected"
        :return: image without isolated points
        """
        if connectionType == "4-point-connected":
            kernel = np.array([0, 1, 0,
                               1, -1, 1,
                               0, 1, 0, ]).reshape((3, -1))
        else:
            kernel = np.array([1, 1, 1,
                               1, -1, 1,
                               1, 1, 1]).reshape((3, -1))
        mask = cv2.filter2D(image, -1, kernel)
        mask = ImageProcessor.binary(mask, 0)
        filteredImage = image * mask
        return filteredImage

    @staticmethod
    def findBiggestConnectedComponent(image: np.ndarray) -> np.ndarray:
        """
        :param image: binary image
        :return: a binary image only with the biggest connect component
        """
        nLabel, connectedComponents = cv2.connectedComponents(image, connectivity=4, ltype=cv2.CV_16U)
        sizeConnectedComponents = []
        for i in np.arange(1, nLabel):
            sizeConnectedComponents.append(np.sum(connectedComponents == i))
        biggestComponent = connectedComponents == (np.argmax(sizeConnectedComponents) + 1)
        return biggestComponent.astype(np.uint8)

    @staticmethod
    def findCenterOfSingleContour(image: np.ndarray) -> np.ndarray:
        contours, hierarchy = cv2.findContours(image, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        hull = cv2.convexHull(contours[0])
        M = cv2.moments(hull)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        return np.array([cx, cy])
