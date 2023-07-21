import pandas as pd
import numpy as np
import cv2
from pathlib import Path
import json

import matplotlib.pyplot as plt

from .utility.define_class import INT_OR_FLOAT, LIST_OR_NUMPY, NEIGHBOUR_PACKING_TYPE
from .image_processing import ImageProcessor as imgPro
from .utility.utillity import toStr


def read_xlsx(
    hifuType=1001,
    recordFileName: str = "scan_record.json",
    date=None,
    scanPlan=None,
    dataType=None,
) -> tuple[np.ndarray, pd.arrays.PandasArray, pd.arrays.PandasArray, float, float]:
    hifuType = toStr(hifuType)
    date = toStr(date)

    xlsxFolder = Path("data").joinpath("4-hydrophone")
    recordFile = Path("data").joinpath("4-hydrophone", recordFileName)
    with open(recordFile, "r+") as f:
        scanDataCollection = json.load(f)

    scanArray: np.ndarray = np.array([])
    xPoints: pd.arrays.PandasArray = pd.array([])
    yPoints: pd.arrays.PandasArray = pd.array([])
    xSpacing: float = 0
    ySpacing: float = 0

    if hifuType == "1001":
        assert date is not None and scanPlan is not None and dataType is not None
        xlsxName = scanDataCollection[hifuType][date][scanPlan][dataType]
        xlsxFile = xlsxFolder.joinpath(xlsxName)
        df = pd.read_excel(xlsxFile, skiprows=2, index_col=0)
        scanArray = df.to_numpy()  # Raw
        xPoints, yPoints = df.columns, df.index
        xSpacing, ySpacing = np.abs(
            [xPoints[0] - xPoints[1], yPoints[0] - yPoints[1]]
        ).round(decimals=1)
        print(f"File {xlsxFile.name}")
    else:
        print("Data type not supported yet")
    return scanArray, xPoints, yPoints, xSpacing, ySpacing


def findDbArea(
    scanArray: np.ndarray, dbValue: float = -6
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    :param scanArray
    :param dbValue: as the threshold for circle.
    :return: circle in the shape of ellipse, with size, centerIj (center in image coordinate) and angle
    """
    dbArray = 20 * np.log10(scanArray / np.max(scanArray))
    binaryDbArray = imgPro.binary(dbArray, dbValue, dtype=np.uint8)
    # remove single points
    denoisedDbArray = imgPro.removeIsolatedPoint(binaryDbArray)
    denoisedDbArray = imgPro.removeIsolatedPoint(denoisedDbArray)
    # find connected Points
    biggestComponent = imgPro.findBiggestConnectedComponent(denoisedDbArray)
    # find contours centerIj
    contours, hierarchy = cv2.findContours(
        biggestComponent, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE
    )
    hull = cv2.convexHull(contours[0]).squeeze()

    # find a fitted ellipse # not that good
    # ellipse = cv2.fitEllipse(hull)  # centerIj, size, angle
    # find a circle
    (x, y), radius = cv2.minEnclosingCircle(hull)
    centerIj = np.array([x, y]).astype(int)  # (center in image coordinate)
    mask = np.zeros(binaryDbArray.shape, dtype=np.uint8)
    # mask = cv2.drawContours(mask, [hull], -1, 255, cv2.FILLED)
    # cv2.ellipse(mask, ellipse, 255, thickness=cv2.FILLED)
    cv2.circle(mask, centerIj, int(radius), 1, thickness=cv2.FILLED)

    # shall be same as centerIj of the ellipse
    # M = cv2.moments(hull)
    # cx = int(M['m10'] / M['m00'])
    # cy = int(M['m01'] / M['m00'])

    # from lib.ellipse import draw_ellipse
    # fig, ax = plt.subplots()
    # ax.imshow(biggestComponent, cmap=plt.cm.gray)
    # for contour in contours:
    #     contour = contour.squeeze()
    #     ax.plot(contour[:, 0], contour[:, 1], linewidth=2)
    # ax.plot(hull[:, 0], hull[:, 1], linewidth=2)
    # # different angle representation
    # centerIj, size, angle = ellipse
    # angle -= 90
    # draw_ellipse(ax, size[0], size[1], angle=angle, xc=centerIj[0], yc=centerIj[1], linewidth=2, edgecolor='g')
    # plt.show()

    maskedArray = scanArray * mask
    return maskedArray, centerIj, radius


def singleCircleMask2D(
    scanArray: np.ndarray,
    modelRadius: INT_OR_FLOAT,
    centerIj: LIST_OR_NUMPY,
    spacings: LIST_OR_NUMPY,
) -> np.ndarray:
    """
    :param scanArray
    :param modelRadius
    :param centerIj
    :param spacings
    :return: the circle mask
    """
    centerIj = np.array(centerIj).astype(int)
    mask = np.zeros(scanArray.shape, dtype=np.uint8)
    if spacings[0] == spacings[1]:
        modelRadiusImage = modelRadius / spacings[0]
        radius = np.ceil(modelRadiusImage).astype(int)
        cv2.circle(mask, centerIj, radius, 1, thickness=cv2.FILLED)
    else:
        modelRadiusImages = modelRadius / np.array(spacings)
        axes = np.ceil(modelRadiusImages).astype(int)
        cv2.ellipse(
            mask,
            centerIj,
            axes,
            angle=0,
            startAngle=0,
            endAngle=360,
            color=1,
            thickness=cv2.FILLED,
        )
    return mask


def intensityFromVoltage(voltage: np.ndarray) -> np.ndarray:
    return np.square(voltage)


def integralXY(scanArray: np.ndarray, spacings: LIST_OR_NUMPY) -> float:
    """
    including simple intensity calculation
    :param scanArray: unit: Voltage
    :param spacings:
    :return: integral of Intensity (unit: Voltage **2 )
    """
    intensityArray = intensityFromVoltage(voltage=scanArray)
    xIntegral = intensityArray.sum(axis=1) * spacings[0]
    integral = xIntegral.sum() * spacings[1]
    return integral


def egoThermalIntegral(
    scanArray: np.ndarray,
    modelRadius: INT_OR_FLOAT,
    centerIj: LIST_OR_NUMPY,
    spacings: LIST_OR_NUMPY,
    showFlag: bool = False,
) -> float:
    """
    create an ellipse mask at the centerIj of the model and sum that area.
    :param scanArray
    :param modelRadius
    :param centerIj: centerIj of the model
    :param spacings: (xSpacing, ySpacing)
    :param showFlag
    :return: sum of the model area
    """
    mask = singleCircleMask2D(scanArray, modelRadius, centerIj, spacings)
    maskedArea = scanArray * mask
    integral = integralXY(maskedArea, spacings)
    if showFlag:
        fig, ax = plt.subplots()
        ax.imshow(maskedArea, cmap=plt.cm.gray)
        ax.plot(
            [centerIj[0]],
            [centerIj[1]],
            marker="s",
            markerfacecolor="r",
            markeredgecolor="r",
        )
        plt.title("Ego thermal area of the scan")
        plt.show()
    return integral


def packNeighbourLocation(
    modelRadiusImage: float,
    centerIj: LIST_OR_NUMPY,
    nNeighbour: int,
    packingType: NEIGHBOUR_PACKING_TYPE = "hexagonal",
) -> np.ndarray:
    """
    Packing type can refer to https://en.wikipedia.org/wiki/Circle_packing
    :param centerIj: centerIj of the analysing point, or the middle of the acoustic field
    :param modelRadiusImage
    :param nNeighbour
    :param packingType: refer to NEIGHBOUR_PLAN_TYPE
    :return: all centerIj locations of the neighbours
    """
    neighbourLocs = []
    if packingType == "hexagonal":
        twoRadius = modelRadiusImage * 2
        sqrtThreeRadius = np.sqrt(3) * modelRadiusImage
        neighbourLocs = np.array(
            [
                [twoRadius, 0],
                [-twoRadius, 0],
                [modelRadiusImage, sqrtThreeRadius],
                [-modelRadiusImage, sqrtThreeRadius],
                [-modelRadiusImage, -sqrtThreeRadius],
                [modelRadiusImage, -sqrtThreeRadius],
            ]
        )  # type: ignore
    else:
        print("Packing type not supported yet.")
    return neighbourLocs + np.array(centerIj)


def singleNeighbourThermalIntegral(
    scanArray: np.ndarray,
    modelRadius: INT_OR_FLOAT,
    neighbourCenter: LIST_OR_NUMPY,
    spacings: LIST_OR_NUMPY,
) -> np.ndarray:
    mask = singleCircleMask2D(scanArray, modelRadius, neighbourCenter, spacings)
    singleNeighbourScan = mask * scanArray
    return singleNeighbourScan


def neighbourThermalIntegral(
    scanArray: np.ndarray,
    modelRadius: INT_OR_FLOAT,
    centerIj: LIST_OR_NUMPY,
    spacings: LIST_OR_NUMPY,
    nNeighbour: int,
    packingType: NEIGHBOUR_PACKING_TYPE = "hexagonal",
    showFlag: bool = False,
) -> tuple[float, float]:
    modelRadiusImage = modelRadius / spacings[0]
    neighbourLocs = packNeighbourLocation(
        modelRadiusImage, centerIj, nNeighbour, packingType=packingType
    )
    neighbourThermal = 0
    if packingType == "hexagonal":
        if showFlag:
            fig, axes = plt.subplots(nrows=2, ncols=3)
            axes = axes.flatten()  # type: ignore
            for i in np.arange(6):
                iCenter = neighbourLocs[i, :].astype(int)
                iScan = singleNeighbourThermalIntegral(
                    scanArray, modelRadius, iCenter, spacings
                )
                axes[i].imshow(iScan, cmap="gray")
                axes[i].plot(
                    [centerIj[0]],
                    [centerIj[1]],
                    marker="s",
                    markerfacecolor="r",
                    markeredgecolor="r",
                )
                axes[i].set_title(f"{i}")
                iThermal = integralXY(iScan, spacings)
                neighbourThermal += iThermal
            fig.suptitle(f"Neighbour thermal area of the scan in {packingType} Packing")
            plt.show()
        else:
            for i in np.arange(6):
                iCenter = neighbourLocs[i, :].astype(int)
                iScan = singleNeighbourThermalIntegral(
                    scanArray, modelRadius, iCenter, spacings
                )
                iThermal = integralXY(iScan, spacings)
                neighbourThermal += iThermal
        singleThermal = neighbourThermal / 6
        return singleThermal * nNeighbour, singleThermal
    else:
        print(
            "Neighbour thermal can't be calculated due to unsupported neighbour packing type."
        )
        return 0, 0
