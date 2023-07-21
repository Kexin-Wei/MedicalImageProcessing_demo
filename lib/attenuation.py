from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional

# from .rflib_math import findClosestNum, possibleFactor
from lib.utility.define_class import AC_METHOD, INT_OR_FLOAT, INT_OR_NUMPY, STR_OR_PATH


def calACValue(intensity: np.ndarray, method: AC_METHOD = "average") -> np.ndarray:
    """
    input: Intensity (dB)
    return ac value for each row, method to calculate
    """
    intensity[intensity == 0] += 1e-10
    intensityDb = 10 * np.log10(intensity)  # intensity to dB
    if method == "median":
        return np.median(intensityDb, axis=1)
    if method == "average":
        return np.average(intensityDb, axis=1)
    print(f"Method: {method} is not supported yet")
    return np.empty(intensityDb.shape)


def blockPlaner(length: int, blockSize: int = 10) -> INT_OR_NUMPY:
    """
    return idx and the blockNum based on length and blockSize
        - logic: finding the biggest blockNum that with blockSize and total is less than length
        - REMARK: idx at the front is in minor priority
    """
    blockNum = int(np.floor(length / blockSize))
    idx = np.arange(0, length)[-blockSize * blockNum :]
    return idx, blockNum


def singleFreqAttenuationAssessment(
    freq: INT_OR_FLOAT,
    acDb: np.ndarray,
    depth: INT_OR_FLOAT,
    goalAttenuation: Optional[float] = None,
    blockSize: int = 10,
    showOrNot: bool = False,
    figPathName: Optional[STR_OR_PATH] = None,
) -> np.ndarray:
    """
    determine the attenuation by block comparison
    """
    if type(figPathName) is Path:
        figPathName = figPathName.absolute()
    acDb[acDb == 0] += 1e-10

    # average av in the block
    """ Method 1 (Deprecated)
    possibleBlockNum = possibleFactor(acDb.shape[0]) # deprecated method
    realBlockNum = findClosestNum(blockNum, possibleBlockNum[possibleBlockNum > 4])
    acDbModified = np.mean(acDb.reshape(realBlockNum, -1), axis=1)
    """
    # Method 2
    modifiedIdx, blockNum = blockPlaner(acDb.shape[0], blockSize=blockSize)
    acDbModified = np.mean(acDb[modifiedIdx].reshape(blockNum, -1), axis=1)

    # Attenuation Assessment
    # computed element-wise divide
    # dB_0 - dB_depth = 10log10(I_0 / I_depth) = 20 * attenuation * freq * depth * log10(e)
    at = (
        (acDbModified[0] - acDbModified)
        / 20
        / freq
        / np.log10(np.e)
        / np.linspace(1e-10, depth, num=acDbModified.shape[0])
    )

    blockMed = np.mean(modifiedIdx.reshape(blockNum, -1), axis=1)
    xTicksLabel = np.linspace(0, depth, num=5)
    xTicks = xTicksLabel / 5 * acDb.shape[0]

    fig, (ax0, ax1) = plt.subplots(2)
    if goalAttenuation is not None:
        fig.suptitle(
            f"Single Freq Attenuation Assessment - {freq:.0f}Mhz - Goal {goalAttenuation:.2f}"
        )
    else:
        fig.suptitle(f"Single Freq Attenuation Assessment - {freq:.0f}Mhz")
    ax0.plot(acDb, label="All AC")
    ax0.plot(blockMed, acDbModified, "^", label="Block Ave AC")
    ax0.set_title("AC Value Along Depth")
    ax0.set_ylabel("Intensity (dB)")
    ax0.set_xticks(xTicks, labels=[str(x) for x in xTicksLabel])
    ax0.legend()
    ax0.grid()

    ax1.plot(blockMed, at, label="Attenuation Value")
    ax1.plot(blockMed, np.ones_like(at) * np.mean(at), label=f"mean:{np.mean(at):.2f}")
    ax1.set_ylabel("Attenuation (MHz-1*cm-1)")
    ax1.grid()
    ax1.legend()
    ax1.set_xticks(xTicks, labels=[str(x) for x in xTicksLabel])
    ax1.set_xlabel("Depth (cm)")

    if showOrNot:
        fig.show()
    if figPathName is not None:
        fig.savefig(figPathName)  # type: ignore
    plt.close()
    return at


def multiFreqAttenuationAssessment(
    freqs: list[float],
    acDbs: list[np.ndarray],
    depth: INT_OR_FLOAT,
    goalAttenuation: Optional[float] = None,
    blockSize: int = 10,
    showOrNot: bool = False,
    figPathName: Optional[STR_OR_PATH] = None,
) -> np.ndarray:
    """
    determine the attenuation by frequency comparison
    """
    if type(figPathName) is Path:
        figPathName = figPathName.absolute()
    assert acDbs[0].shape[0] == acDbs[1].shape[0]
    acDbs[0][acDbs[0] == 0] += 1e-10
    acDbs[1][acDbs[1] == 0] += 1e-10

    modifiedIdx, blockNum = blockPlaner(acDbs[0].shape[0], blockSize=blockSize)
    acDbModified0 = np.mean(acDbs[0][modifiedIdx].reshape(blockNum, -1), axis=1)
    modifiedIdx, blockNum = blockPlaner(acDbs[1].shape[0], blockSize=blockSize)
    acDbModified1 = np.mean(acDbs[1][modifiedIdx].reshape(blockNum, -1), axis=1)

    # Attenuation Assessment
    # computed element-wise divide
    # delta_dB = dB_0 - dB_depth = 10log10(I_0 / I_depth) = 20 * attenuation * freq * depth * log10(e)
    # delta_dB_f1 - delta_dB_f2 = 20 * attenuation * (f1 - f2) * depth * log10(e)
    deltaDbFreq0 = acDbModified0[0] - acDbModified0
    deltaDbFreq1 = acDbModified1[0] - acDbModified1
    at = (
        (deltaDbFreq0 - deltaDbFreq1)
        / 20
        / (freqs[0] - freqs[1])
        / np.log10(np.e)
        / np.linspace(1e-10, depth, num=acDbModified1.shape[0])
    )

    blockMed = np.mean(modifiedIdx.reshape(blockNum, -1), axis=1)
    xTicksLabel = np.linspace(0, depth, num=5)
    xTicks = xTicksLabel / 5 * acDbs[0].shape[0]

    fig, axes = plt.subplots(2, 2)
    fig.set_size_inches(10, 8)
    if goalAttenuation is not None:
        fig.suptitle(
            f"Multi-Freq Attenuation Assessment"
            f" - {freqs[0]:.0f}-{freqs[1]:.0f}Mhz - Goal {goalAttenuation:.2f}"
        )
    else:
        fig.suptitle(
            f"Multi-Freq Attenuation Assessment - {freqs[0]:.0f}-{freqs[1]:.0f}Mhz"
        )
    axes[0][0].plot(acDbs[1], label=f"All AC")
    axes[0][0].plot(blockMed, acDbModified0, "^", label=f"Block Ave AC")
    axes[0][0].set_title(f"AC Value along {depth} cm of {freqs[0]} mHz")
    axes[0][0].set_ylabel("Intensity (dB)")
    axes[0][0].set_xticks(xTicks, labels=[str(x) for x in xTicksLabel])
    axes[0][0].legend()
    axes[0][0].grid()

    axes[1][0].plot(acDbs[1], label=f"All AC")
    axes[1][0].plot(blockMed, acDbModified1, "^", label=f"Block Ave AC")
    axes[1][0].set_title(f"AC Value along {depth} cm of {freqs[1]} mHz")
    axes[1][0].set_ylabel("Intensity (dB)")
    axes[1][0].set_xticks(xTicks, labels=[str(x) for x in xTicksLabel])
    axes[1][0].set_xlabel("Depth (cm)")
    axes[1][0].legend()
    axes[1][0].grid()

    axes[0][1].plot(acDbs[0] - acDbs[1], label="Delta Attenuation of All AC")
    axes[0][1].plot(
        blockMed, deltaDbFreq0 - deltaDbFreq1, "^", label="Delta Attenuation"
    )
    axes[0][1].set_title(f"Delta AC freq {freqs[0]} - {freqs[1]}")
    axes[0][1].set_ylabel("Attenuation (MHz-1*cm-1)")
    axes[0][1].grid()
    axes[0][1].legend()
    axes[0][1].set_xticks(xTicks, labels=[str(x) for x in xTicksLabel])

    axes[1][1].plot(blockMed, at, label="Attenuation Value")
    axes[1][1].plot(
        blockMed, np.ones_like(at) * np.mean(at), label=f"mean:{np.mean(at):.2f}"
    )
    axes[1][1].set_title(f"Attenuation Assessment freq {freqs[0]} - {freqs[1]}")
    axes[1][1].set_ylabel("Attenuation (MHz-1*cm-1)")
    axes[1][1].grid()
    axes[1][1].legend()
    axes[1][1].set_xticks(xTicks, labels=[str(x) for x in xTicksLabel])
    axes[1][1].set_xlabel("Depth (cm)")

    if showOrNot:
        fig.show()
    if figPathName is not None:
        fig.savefig(figPathName)  # type: ignore
    plt.close()
    return at
