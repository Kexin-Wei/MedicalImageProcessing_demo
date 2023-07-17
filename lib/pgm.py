"""created by kx 2022.10.27
define the class PGMFile

an example of pgm file head:
        
        analog curve: 00.0 , 14 | 01.8 , 54
        angle/distance offset: 0.0872664600610733
        axial length: 1787
        channel number: 128
        collection version: 1.0.0.0
        depth(cm): 4
        duty: 0
        focus(cm): 2
        frequency compound enable: false
        frequency(mhz): 5.699999809265137
        global gain: 0.699999988079071
        lateral width: 608
        mode: BRF
        parallel mode: 2
        power duration: 0
        power end: 0
        power init: 0
        power interval: 0
        power ratio: 0
        prf: 0
        probe model: 3
        pulse count: 0
        pulse length: 1.5
        rx fNum: 0.800000011920929
        spatial compound enable: true
        system version: 0.10.9.106
        tgc slider: 0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5
        thi mode: 1
        time stamp: 11:21:57
        tx fNum: 3
        width/angle: 3.809999942779541
        cavitation intensity:
        rf:
"""
import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy import ndimage, signal
from typing import Optional, Sequence

from lib.utility.define_class import STR_OR_PATH, INT_OR_FLOAT


class PGMFile:
    """
    Class for single PGM file, containing member functions:
    1. readPGM, rf = depth * scanline
    2. changeFileName, the container folder remains the same
    3. B-mode show and generate png file
    4. calibration bbn detection related functions ( stft calculation )
    
    and hidden functions:
    1. _getStringAfter
    2. _skipLines
    
    """

    def __init__(self, fileFullPath: STR_OR_PATH, printOut: bool = True):
        self.fileFullPath = Path(fileFullPath)
        self.path = self.fileFullPath.parent
        self.fileName = self.fileFullPath.name

        # pgm files attributes
        self.frameNo = None
        self.analogCurveString = None
        self.angleOrDistanceOffset = None
        self.axialLength = None
        self.channelNumber = None
        self.collectionVersionString = None
        self.depthCm = None
        self.duty = None
        self.focus = None
        self.frequencyCompound = None
        self.frequency = None
        self.globalGain = None
        self.lateralWidth = None
        self.modeString = None
        self.parallelMode = None
        self.powerDuration = None
        self.powerEnd = None
        self.powerInit = None
        self.powerInterval = None
        self.powerRatio = None
        self.prf = None
        self.probeModelString = None
        self.pulseCount = None
        self.pulseLength = None
        self.rxFNum = None
        self.spatialCompound = None
        self.systemVersion = None
        self.tgcSlider = None
        self.thiMode = None
        self.timeStampString = None
        self.txFNum = None
        self.widthAngle = None
        self.cavitationIntensity = None
        self.rfRaw = None
        self.rf = None
        self.fsMhz = None
        self.fDemodMhzPerSample = None
        self.IS_RF_OR_IQ = None

        self.readPGM(printOut=printOut)
        self.envData = None
        self.bModeData = None
        self.lowerDisplayRangeDb = None
        self.upperDisplayRangeDb = None
        self.defaultDynamicRange = [30, 90]

        self.fftLength = None
        self.overlapLength = None
        self.hannWindowLength = None
        self.stftMagnitudeDb = None
        self.stftMagnitudeDbMean = None
        self.defaultStftParameters = {"fftLength": 1024, "overlapLength": 896, "hannWindowLength": 1024}
        self.lastUserStftParameters = None

        self.hifuScanLine = None
        self.isHifu = None
        self.bbnIntervals = None

    @staticmethod
    def _getStringAfter(fID, separator: str = ":") -> str:
        """
        Description: get the string after the separator in the new line of fID
        """
        line = fID.readline().decode('utf-8').split(separator, maxsplit=1)
        return line[-1]

    @staticmethod
    def _skipLines(fID, nSkipLine: int) -> None:
        for _ in range(0, nSkipLine):
            next(fID)

    def readPGM(self, DEINTERLEAVE: bool = False, SAMPLE_AT_60MHZ: bool = True, printOut: bool = True):
        if self.fileFullPath.suffix != '.pgm':  # if found out not python
            print("Currently only support .pgm file")
            return

        else:
            with self.fileFullPath.open(mode='rb') as f:
                self.frameNo = int(re.findall(r"\d+", self.fileName)[0])
                if "hifu" in self.fileName:
                    self.isHifu = True
                self.analogCurveString = self._getStringAfter(f).strip()
                self.angleOrDistanceOffset = float(self._getStringAfter(f))
                self.axialLength = int(self._getStringAfter(f))
                self.channelNumber = int(self._getStringAfter(f))
                self.collectionVersionString = self._getStringAfter(f).strip()
                self.depthCm = float(self._getStringAfter(f))
                self.duty = float(self._getStringAfter(f))
                self.focus = float(self._getStringAfter(f))
                self.frequencyCompound = "true" in self._getStringAfter(f).lower()
                self.frequency = float(self._getStringAfter(f))
                self.globalGain = float(self._getStringAfter(f))
                self.lateralWidth = int(self._getStringAfter(f))
                self.modeString = self._getStringAfter(f).strip()
                self.parallelMode = int(self._getStringAfter(f))
                self.powerDuration = float(self._getStringAfter(f))
                self.powerEnd = float(self._getStringAfter(f))
                self.powerInit = float(self._getStringAfter(f))
                self.powerInterval = float(self._getStringAfter(f))
                self.powerRatio = float(self._getStringAfter(f))
                self.prf = float(self._getStringAfter(f))
                self.probeModelString = self._getStringAfter(f).strip()
                self.pulseCount = int(self._getStringAfter(f))
                self.pulseLength = float(self._getStringAfter(f))
                self.rxFNum = float(self._getStringAfter(f))
                self.spatialCompound = "true" in self._getStringAfter(f).lower()
                self.systemVersion = self._getStringAfter(f).strip()
                self.tgcSlider = [float(item) for item in self._getStringAfter(f).split(',')]
                self.thiMode = int(self._getStringAfter(f))
                self.timeStampString = self._getStringAfter(f).strip()
                self.txFNum = float(self._getStringAfter(f))
                self.widthAngle = float(self._getStringAfter(f))
                # read cavitation intensity matrix
                self._skipLines(f, 1)  # cavitation intensity head
                cavitationIntensity = []
                line = f.readline()
                while "rf" not in line.decode('utf-8'):
                    cavitationIntensity.append([float(item) for item in line.decode().split(',')])
                    line = f.readline()
                self.cavitationIntensity = np.array(cavitationIntensity)
                # read RF data
                # !copy from stork loadfile()-start
                if self.parallelMode == 2 and DEINTERLEAVE:
                    self.lateralWidth *= 2
                    # !copy from stork loadfile()-end
                self.rf = np.reshape(np.fromfile(f, dtype=np.int32),
                                     (self.lateralWidth, -1)).T  # matlab read in col, python in row

                # !copy from stork loadfile()-start # not test after moving from matlab, 221031
                if self.parallelMode == 2 and DEINTERLEAVE:
                    # rfRaw = self.rf.copy()
                    self.rf = self.rf[:, ::2]
                    rfL, rfW = self.rf.shape
                    assert rfL / 2 == np.ceil(rfW / 2)
                    rfDeint = np.zeros((int(rfL / 2), 2 * rfW))
                    for col in range(0, rfW):
                        rfDeint[:, 2 * col - 0] = self.rf[::2, col]  # odd col
                        rfDeint[:, 2 * col + 1] = self.rf[1::2, col]  # even col
                    self.axialLength /= 2
                    self.rf = rfDeint.copy()
                # !copy from stork loadfile()-end

                # phase inversion THI
                if self.thiMode:
                    self.rfRaw = self.rf.copy()
                    rfData0 = self.rf[:, ::2]
                    rfData180 = self.rf[:, 1::2]
                    self.rf = rfData0 + rfData180

                # Load the sampling frequency
                #  added 2015-03-20 Paul
                #  this is to support importing data from other sources, such as the
                #  velocimeter, which may have variable sampling frequency
                # try
                #    test = self.fsMHz
                # except
                if SAMPLE_AT_60MHZ:  # ADC runs at 60 MHz
                    # for cases that require us to find the sampling frequency, i.e. the c21 system
                    if self.parallelMode == 1:
                        self.fsMhz = 60
                    if self.parallelMode == 2:
                        self.fsMhz = 30
                    if self.parallelMode == 3:
                        self.fsMhz = 20
                    if self.parallelMode == 4:
                        self.fsMhz = 15
                else:  # ADC runs at 40 MHz
                    if self.parallelMode == 1:
                        self.fsMhz = 40
                    if self.parallelMode == 2:
                        self.fsMhz = 20
                    if self.parallelMode == 3:
                        self.fsMhz = 12
                    if self.parallelMode == 4:
                        self.fsMhz = 10

                # RF data depth adjustment. UI written depth is the depth AFTER MP
                # processing, which will throw away points at the end. Hence, the actual
                # SCAN depth is different from the UI written depth. This code's purpose is
                # to find the actual SCAN depth
                # if strcmp(my_frame.mode_string,'BRF')
                # if strcmp(my_frame.mode_string,'BRF') || strcmp(my_frame.mode_string,'CRF') %CRF added 2013-03-27
                # sound speed
                # c_cm_s = 1568e2  # vascular general
                c_cm_s = 1550e2  # abdomen general
                # c_cm_s = 1540e2;
                # fs_Hz = 40e6/my_frame.parallel_mode; %this line only works for parallel =1  or 2
                # adjusted depth_cm for RF data
                assert self.fsMhz is not None
                self.depthCm = self.rf.shape[0] / (self.fsMhz * 1e6) * c_cm_s / 2
            if printOut:
                print(f"\tRead {self.fileFullPath} done")

    def changeFileName(self, newName: str):
        self.fileFullPath = self.path.joinpath(newName)
        self.fileName = self.fileFullPath.name

    def envelopExtraction(self):
        if self.modeString == "BRF":
            # amplitude extraction

            # a.1. rf to intensity, refer to stork simplified_load.m
            # if self.parallelMode == 1: self.fsMhz = 60 #included in rflib.pgm
            # if self.parallelMode == 2: self.fsMhz = 30
            # if self.parallelMode == 3: self.fsMhz = 20
            # if self.parallelMode == 4: self.fsMhz = 15
            assert isinstance(self.rf, np.ndarray) and self.fsMhz is not None
            self.fDemodMhzPerSample = 10
            n_ = np.arange(0, self.rf.shape[0])
            iqDemod = np.einsum(
                "ij,i->ij",
                self.rf,  # np.einsum("ij,i->ij") == np.multiply(2d array, column vector)
                np.exp(-2j * np.pi * self.fDemodMhzPerSample / self.fsMhz * n_))

            # a.2. low pass filter
            # REMARK: matlab.firls(30,...) = signal.firls(31,...)
            hLength = 30
            hPassbandMhz = 4
            hStopbandMhz = 6
            hLowPassFilter = signal.firls(hLength + 1,
                                          np.array([0, hPassbandMhz, hStopbandMhz, self.fsMhz / 2]), [1, 1, 0, 0],
                                          fs=self.fsMhz)
            iq = ndimage.correlate(iqDemod, hLowPassFilter.reshape(-1, 1), mode="nearest")

            self.envData = np.abs(iq)
            self.IS_RF_OR_IQ = 1
        else:
            print(f"{self.modeString} Mode of the PGM file not supported yet in the Envelop Extraction")

    def _updateDynamicRange(self,
                            upperDisplayRangeDb: Optional[INT_OR_FLOAT] = None,
                            lowerDisplayRangeDb: Optional[INT_OR_FLOAT] = None) -> bool:
        if lowerDisplayRangeDb is None:
            lowerDisplayRangeDb = self.defaultDynamicRange[0]
        if upperDisplayRangeDb is None:
            upperDisplayRangeDb = self.defaultDynamicRange[1]
        if upperDisplayRangeDb < lowerDisplayRangeDb:
            temp = upperDisplayRangeDb
            upperDisplayRangeDb = lowerDisplayRangeDb
            lowerDisplayRangeDb = temp
            print("Lower range is larger than upper range, and hence they are swapped.")
        self.upperDisplayRangeDb, self.lowerDisplayRangeDb = upperDisplayRangeDb, lowerDisplayRangeDb
        if upperDisplayRangeDb is not None or lowerDisplayRangeDb is not None:
            return True
        return False

    def _getBMode(self,
                  upperDisplayRangeDb: Optional[INT_OR_FLOAT] = None,
                  lowerDisplayRangeDb: Optional[INT_OR_FLOAT] = None):
        """
        calculate the b mode image array, show it by default
        """
        if self._updateDynamicRange(upperDisplayRangeDb=upperDisplayRangeDb,
                                    lowerDisplayRangeDb=lowerDisplayRangeDb) or self.bModeData is None:
            assert self.upperDisplayRangeDb is not None and self.lowerDisplayRangeDb is not None
            temp = np.clip(self.safe_log10(self.env), a_min=0, a_max=np.inf)
            self.bModeData = np.clip(20 * temp, a_min=self.lowerDisplayRangeDb, a_max=self.upperDisplayRangeDb)
            self.bModeData = np.round((self.bModeData - self.lowerDisplayRangeDb) /
                                      (self.upperDisplayRangeDb - self.lowerDisplayRangeDb) * 255)

    def _plotBMode(self,
                   upperDisplayRangeDb: Optional[int] = None,
                   lowerDisplayRangeDb: Optional[int] = None,
                   saveFig: bool = False,
                   imagePath: Optional[STR_OR_PATH] = None):
        assert self.bModeData is not None
        self._getBMode(upperDisplayRangeDb=upperDisplayRangeDb, lowerDisplayRangeDb=lowerDisplayRangeDb)
        plt.figure()
        plt.imshow(self.bModeData, cmap='gray', aspect='auto')
        plt.title(self._bModeTitle)
        if saveFig:
            if imagePath is None:
                imagePath = self.fileFullPath.parent.joinpath(f"{self.fileName}.png")
                imagePath.parent.mkdir(parents=True)
            plt.savefig(imagePath)
        else:
            plt.show()
        plt.close()

    def showBMode(self,
                  ax: Optional[plt.Axes] = None,
                  upperDisplayRangeDb: Optional[int] = None,
                  lowerDisplayRangeDb: Optional[int] = None):
        self._getBMode(upperDisplayRangeDb=upperDisplayRangeDb, lowerDisplayRangeDb=lowerDisplayRangeDb)
        if ax is None:
            self._plotBMode(upperDisplayRangeDb=upperDisplayRangeDb, lowerDisplayRangeDb=lowerDisplayRangeDb)
        else:
            assert self.bModeData is not None
            ax.imshow(self.bModeData, cmap='gray', aspect='auto')
            ax.set_title(self._bModeTitle)

    def saveBMode(self,
                  imageFolderPath: STR_OR_PATH,
                  upperDisplayRangeDb: Optional[int] = None,
                  lowerDisplayRangeDb: Optional[int] = None,
                  replace: bool = False):
        imageFolderPath = Path(imageFolderPath)
        imagePath = imageFolderPath.joinpath(f"{self.fileFullPath.stem}.png")
        if not imagePath.exists() or replace:
            self._plotBMode(upperDisplayRangeDb=upperDisplayRangeDb,
                            lowerDisplayRangeDb=lowerDisplayRangeDb,
                            saveFig=True,
                            imagePath=imagePath)
            print(f"\t saved {self.fileFullPath.absolute()} in to {imageFolderPath.absolute()}")
        else:
            print(f"\t skipped {self.fileFullPath.absolute()} in to {imageFolderPath.absolute()}")

    def updateStftParameters(self,
                             fftLength: Optional[int] = None,
                             hannWindowLength: Optional[int] = None,
                             overlapLength: Optional[int] = None) -> bool:
        localsItemsCopy = locals().copy()
        changed = False
        # assign
        for k, v in localsItemsCopy.items():
            if k != "self":
                if v is not None:
                    setattr(self, k, v)
                    changed = True
                else:
                    if self.lastUserStftParameters is not None and k in self.lastUserStftParameters.keys():
                        setattr(self, k, self.lastUserStftParameters[k])
                    else:
                        setattr(self, k, self.defaultStftParameters[k])
        # keep changes
        for k, v in localsItemsCopy.items():
            if k != "self" and v is not None:
                if self.defaultStftParameters is None:
                    self.defaultStftParameters = {}
                self.defaultStftParameters[k] = v
        return changed

    def getStftMagnitudeDb(self,
                           fftLength: Optional[int] = None,
                           hannWindowLength: Optional[int] = None,
                           overlapLength: Optional[int] = None) -> np.ndarray:
        """
        stftMagnitudeDb = nFFT x nScanline x nStep
        """
        if self.updateStftParameters(fftLength=fftLength,
                                     hannWindowLength=hannWindowLength,
                                     overlapLength=overlapLength) \
                or self.stftMagnitudeDb is None:
            assert self.fsMhz is not None and self.hannWindowLength is not None
            f, t, stftData = signal.stft(
                self.rf,
                self.fsMhz,
                window="hann",
                nperseg=self.hannWindowLength,
                noverlap=self.overlapLength,
                nfft=self.fftLength,
                boundary=None,  # type: ignore
                padded=False,
                return_onesided=True,
                axis=0)  # verified with matlab using `test_f2_scipy_stft.py`
            win = signal.get_window("hann", self.hannWindowLength)
            scale = np.sqrt(win.sum() ** 2)
            stftData *= scale
            stftMagnitude = np.absolute(stftData)  # +-0.001 error compared to matlab
            self.stftMagnitudeDb = self.safe_log10(stftMagnitude)
        return self.stftMagnitudeDb

    def getStftMagnitudeDbMean(self,
                               fftLength: Optional[int] = None,
                               hannWindowLength: Optional[int] = None,
                               overlapLength: Optional[int] = None) -> np.ndarray:
        """
        self.stftMagnitudeDb = nFFT x rf_scanline x stft_t
        self.stftMagnitudeDbMean = nFFT x rf_scanline
        """
        if self.updateStftParameters(fftLength=fftLength,
                                     hannWindowLength=hannWindowLength,
                                     overlapLength=overlapLength) \
                or self.stftMagnitudeDbMean is None:
            self.getStftMagnitudeDb(fftLength=fftLength, hannWindowLength=hannWindowLength, overlapLength=overlapLength)
            # mean for all steps
            assert isinstance(self.stftMagnitudeDb, np.ndarray)
            self.stftMagnitudeDbMean = self.stftMagnitudeDb.mean(axis=-1)
        return self.stftMagnitudeDbMean

    def getStftMagnitudeDbScanlineMean(self) -> np.ndarray:
        """
        stftMagnitudeDbScanlineMean = nFFTx1
        """
        if self.stftMagnitudeDbMean is None:
            self.getStftMagnitudeDbMean()
        assert isinstance(self.stftMagnitudeDbMean, np.ndarray)
        if self.hifuScanLine is None:
            print("This is not a hifu frame, return stftMagnitudeDbMean instead")
            return self.stftMagnitudeDbMean.mean(axis=-1)
        return self.stftMagnitudeDbMean[:, self.hifuScanLine[0]:self.hifuScanLine[1]].mean(axis=-1)

    def showStft(self,
                 fig: Optional[Figure] = None,
                 ax: Optional[plt.Axes] = None,
                 saveFig: bool = False,
                 imagePath: Optional[STR_OR_PATH] = None):
        assert isinstance(self.rf, np.ndarray) and self.fsMhz is not None and self.hannWindowLength is not None
        if self.hifuScanLine is None:
            stftSource = self.rf.T.flatten()
        else:
            stftSource = self.rf[:, self.hifuScanLine[0]:self.hifuScanLine[1]].T.flatten()
        f, t, stftData = signal.stft(
            stftSource,
            self.fsMhz,
            window="hann",
            nperseg=self.hannWindowLength,
            noverlap=self.overlapLength,
            nfft=self.fftLength,
            boundary=None,  # type: ignore
            padded=False,
            return_onesided=True)  # verified with matlab using `test_f2_scipy_stft.py`

        stftDataMagnitude = np.absolute(stftData)
        if ax is None:
            plt.figure()
            plt.pcolormesh(t, f, stftDataMagnitude, shading='gouraud', vmin=85, vmax=110)
            plt.colorbar()
            plt.title(f"STFT of the {self.fileName}")
            plt.xticks(ticks=np.linspace(0, t.max(), 5), labels=np.linspace(0, t.size, 5, dtype=np.int32))
            plt.xlabel("Scanline")
            plt.ylabel("Frequency / mHz")
            if saveFig:
                if imagePath is None:
                    imagePath = Path("results").joinpath("2-stft-figures", "temp", f"{self.fileName}_stft.png")
                    imagePath.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(imagePath)
            else:
                plt.show()
            plt.close()
        else:
            c = ax.pcolor(t, f, stftDataMagnitude, shading='flat', vmin=85, vmax=110)
            assert isinstance(fig, Figure)
            fig.colorbar(c, ax=ax)

    @staticmethod
    def safe_log10(x, eps=1e-10) -> np.ndarray:
        # numpy.log10 can't handle 0
        # https://stackoverflow.com/questions/21610198/runtimewarning-divide-by-zero-encountered-in-log
        result = np.where(x > eps, x, -10)
        np.log10(result, out=result, where=result > 0)
        return result

    @property
    def env(self) -> np.ndarray:
        if self.envData is None:
            self.envelopExtraction()
        assert self.envData is not None
        return self.envData

    @property
    def stftMagnitudeDbScanlineMean(self) -> np.ndarray:
        return self.getStftMagnitudeDbScanlineMean()

    @property
    def _bModeTitle(self) -> str:
        return f"B-mode, freq: {self.frequency:.1f}, " + \
            f"Dynamic Range: {self.lowerDisplayRangeDb}-{self.upperDisplayRangeDb}"
