"""2022.11.24, by Kexin
Read time and voltage data from oscilloscope data file written by the Janelle's oscilloscope code with format as:

    Time/s,Volts/V
    0.0,0.04
    4.001600640256103e-06,0.04
    8.003201280512205e-06,0.0
    1.2004801920768307e-05,0.04
    1.600640256102441e-05,0.04
    2.0008003201280514e-05,0.04
    2.4009603841536614e-05,0.04
    2.8011204481792718e-05,0.0

"""
import numpy as np

from lib.utility.define_class import STR_OR_PATH


def skipLines(fID, nSkipLine: int) -> None:
    for _ in range(0, nSkipLine):
        next(fID)


def readTxt(filePath: STR_OR_PATH) -> np.ndarray:
    couplerData = []
    separator = ","
    with open(filePath, "r") as f:
        skipLines(f, 1)
        allLines = f.readlines()
        for line in allLines:
            temp = line.strip("\n").split(separator)
            temp = [float(x) for x in temp]
            couplerData.append(temp)
        return np.array(couplerData)
