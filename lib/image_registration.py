import pydicom
import numpy as np
from lib.utility.define_class import STR_OR_PATH, PROBE_OR_IMAGE


def readTransformMatrixFromDICOM(file: STR_OR_PATH, readType: PROBE_OR_IMAGE) -> np.ndarray:
    ds = pydicom.dcmread(file)
    if readType == "probe":
        ele = ds[0x0013, 0x0036]
        matrix = np.fromstring(ele.value, sep=",").reshape((4, 4))
    elif readType == "image":
        ele1 = ds[0x0013, 0x0034]
        ele2 = ds[0x0013, 0x0035]
        matrix = np.fromstring(ele1.value + ele2.value, sep=",").reshape((4, 4))
    else:
        print(f"This reading type is not supported yet")
        matrix = np.identity(4)
    return matrix


def getTransformMatrixFromFixedMoving(fixedImagePath: STR_OR_PATH, movingImagePath: STR_OR_PATH,
                                      readType: PROBE_OR_IMAGE) -> np.ndarray:
    """
    :param fixedImagePath:
    :param movingImagePath:
    :param readType: either "probe" or "image"
    :return: two transform matrices of fixed and moving image
    """
    fixedMatrix = readTransformMatrixFromDICOM(fixedImagePath, readType=readType)
    movingMatrix = readTransformMatrixFromDICOM(movingImagePath, readType=readType)
    # Tmoving = Tfixed * Ttransform
    transformMatrix = np.linalg.solve(fixedMatrix, movingMatrix)
    transformMatrix[np.abs(transformMatrix) < 1e-3] = 0
    return transformMatrix
