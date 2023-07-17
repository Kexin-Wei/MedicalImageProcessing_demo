import numpy as np
from typing import Optional
from .pgm import PGMFile
from .utility.define_class import STR_OR_PATH


class PgmType:
    BASE_LINE = 0
    HIFU = 1
    NON_HIFU = 2


class CalibrationManager:
    """
    detect bbn by feeding in the new pgm (or RF data), need to reset everytime before using.

    Algorithm logic:
        1. set 1st as baseline, into baseline phase
        2. new pgm compare to baseline:
            a. if not baseline, end baseline phase
            b. if is baseline, update baseline every 5 pgm, repeat this step
        3.  enter hifu calculation phase, new pgm compare to baseline
            a. if is hifu, calculate bbn
            b. if not hifu, continue
        4. repeat step 3. till the end

    """

    def __init__(self):
        # phase recorder
        self.isBaseLine = None
        self.phaseCheckStartCount = None  # modifiable
        self.baseLineCount = None
        self.baseLineUpdateFreq = None  # modifiable
        self.pulseCount = None
        self.baseLineMean = None
        self.backgroundRfSect = None
        self.cavitationIntensityList = None
        self.pgmType = PgmType
        self.pgmFile = None

        # scanline detection
        self.scanLineRowIndexStart = None  # modifiable
        self.scanLineRowIndexEnd = None  # modifiable
        self.scanLineThreshold = None  # modifiable

        # stft parameters
        self.hannWindowLength = None  # modifiable
        self.fftLength = None  # modifiable
        self.overLapLength = None  # modifiable

        # bbn calculation
        self.hifuFreqMhz = None  # modifiable
        self.bbnIntervalDropLeft = None  # modifiable
        self.bbnIntervalDropRight = None  # modifiable
        self.harmonicFreqSectionIndexes = None

        # parameter setting
        self.lastUserParameters = None
        self.defaultParameters = {
            "startDetectionCount": 2,
            "phaseCheckStartCount": 3,
            "baseLineUpdateFreq": 5,
            "scanLineRowIndexStart": 200,
            "scanLineRowIndexEnd": 500,
            "scanLineThreshold": 100,
            "hannWindowLength": 1024,
            "fftLength": 1024,
            "overLapLength": 896,
            "hifuFreqMhz": 1.3,
            "bbnIntervalDropLeft": 0.25,
            "bbnIntervalDropRight": 0.25
        }

        self.reset(toDefault=True)

    def reset(self, toDefault: bool = True):
        self.isBaseLine = True
        self.baseLineCount = 0
        self.pulseCount = 0
        self.baseLineMean = None
        self.backgroundRfSect = np.array([])
        self.cavitationIntensityList = np.array([])

        if toDefault or self.lastUserParameters is None:
            self.lastUserParameters = None
            for k, v in self.defaultParameters.items():
                setattr(self, k, self.defaultParameters[k])
        else:
            for k, v in self.lastUserParameters.items():
                setattr(self, k, self.lastUserParameters[k])

    def changeSetting(self,
                      baseLineUpdateFreq: Optional[int] = None,
                      scanLineRowIndexStart: Optional[int] = None,
                      scanLineRowIndexEnd: Optional[int] = None,
                      scanLineThreshold: Optional[float] = None,
                      hannWindowLength: Optional[int] = None,
                      fftLength: Optional[int] = None,
                      overLapLength: Optional[int] = None,
                      hifuFreqMhz: Optional[float] = None,
                      bbnIntervalDropLeft: Optional[float] = None,
                      bbnIntervalDropRight: Optional[float] = None):
        localsItemsCopy = locals().copy()
        # assign
        for k, v in localsItemsCopy.items():
            if k != "self":
                if v is not None:
                    setattr(self, k, v)
                else:
                    if self.lastUserParameters is not None and k in self.lastUserParameters.keys():
                        setattr(self, k, self.lastUserParameters[k])
                    else:
                        setattr(self, k, self.defaultParameters[k])
        # keep changes
        for k, v in localsItemsCopy.items():
            if k != "self" and v is not None:
                if self.lastUserParameters is None:
                    self.lastUserParameters = {}
                self.lastUserParameters[k] = v

    def lsSetting(self):
        print(f"Current setting is:")
        for k in self.defaultParameters.keys():
            print(f"  - self.{k} = {getattr(self, k)}")

    def getPgmCavitationBbn(self, pgmFile: STR_OR_PATH) -> dict:
        """
        1. determine the phase
        2. if baseline, update baseline
        3. if hifu, change to calculation phase
            a. if hifu, calc
            b. if not hifu, continue
        """
        result = dict.fromkeys(["type", "bbn", "scanline"], None)
        self._receivePgmFile(pgmFile)
        # In baseline phase
        if self.isBaseLine:
            self._updateBaseLineMean()  # update baseLineMean and backgroundRfData
            self._phaseCheck()  # phase check
            assert isinstance(self.baseLineCount, int)
            self.baseLineCount += 1
            result["type"] = self.pgmType.BASE_LINE
        # in hifu calculation phase
        else:
            if self._isHifu():
                bbnIntervals = self._getBbnIntervals()
                result["type"] = self.pgmType.HIFU
                result["bbn"] = bbnIntervals
                if self.cavitationIntensityList is None:
                    self.cavitationIntensityList = {}
                assert self.pgmFile is not None
                self.cavitationIntensityList[self.pgmFile.frameNo] = bbnIntervals
            else:
                result["type"] = self.pgmType.NON_HIFU
        self._updateBackgroundRfDataSect()
        self.pgmFile = None
        return result

    def _receivePgmFile(self, pgmFilePath: STR_OR_PATH):
        self.pgmFile = PGMFile(pgmFilePath)
        self.pgmFile.updateStftParameters(fftLength=self.fftLength,
                                          hannWindowLength=self.hannWindowLength,
                                          overlapLength=self.overLapLength)

    def _phaseCheck(self):
        """
        check whether go to hifu phase, if enough baselines are received
            1. if found hifu, calc HifuScanLine
            2. else continue
        """
        assert self.baseLineCount is not None and self.phaseCheckStartCount is not None
        if self.baseLineCount >= self.phaseCheckStartCount:
            if self._isHifu():  # find hifuScanLine if possible
                self.isBaseLine = False

    def _updateBaseLineMean(self):
        assert self.baseLineCount is not None and self.baseLineUpdateFreq is not None
        if self.baseLineCount % self.baseLineUpdateFreq == 0:
            assert self.pgmFile is not None
            stftMagnitudeDbMean = self.pgmFile.getStftMagnitudeDbMean().mean(axis=-1)
            if self.baseLineMean is None:
                self.baseLineMean = stftMagnitudeDbMean
            else:
                assert self.baseLineMean.shape == stftMagnitudeDbMean.shape
                self.baseLineMean = np.vstack([self.baseLineMean, stftMagnitudeDbMean]).mean(axis=0)

    def _isHifu(self) -> bool:
        """
        return isHifu flag from PGMFile Class,
        if is None, calculate it
        """
        assert self.pgmFile is not None and isinstance(self.pgmFile.rf, np.ndarray) and isinstance(
            self.backgroundRfSect, np.ndarray)
        if self.pgmFile.isHifu is None:
            rfSection = self.pgmFile.rf[self.scanLineRowRange, :]
            rfSectionDiffAbs = np.absolute(np.mean(rfSection - self.backgroundRfSect, axis=0))  # mean along the depth
            overThresholdIndex: np.ndarray = np.argwhere(rfSectionDiffAbs > self.scanLineThreshold)
            if overThresholdIndex.size:
                indexRange = overThresholdIndex[-1] - overThresholdIndex[0]
                self.pgmFile.hifuScanLine = np.array(  # type: ignore
                    [overThresholdIndex[0] + int(0.1 * indexRange),
                     overThresholdIndex[-1] - int(0.3 * indexRange)]).squeeze()
                assert self.pgmFile.hifuScanLine[0] < self.pgmFile.hifuScanLine[1]
                self.pgmFile.isHifu = True
            else:
                self.pgmFile.isHifu = False
        return self.pgmFile.isHifu

    def _getBbnIntervals(self) -> np.ndarray:
        """
        bbnIntervals = nInterval x 1
        """
        assert self.pgmFile is not None
        stftMagnitudeDbScanlineMeanDenoise = self.pgmFile.stftMagnitudeDbScanlineMean - self.baseLineMean
        scanLineBbnIntervals = stftMagnitudeDbScanlineMeanDenoise[self._getHarmonicsIndexes()]
        self.pgmFile.bbnIntervals = scanLineBbnIntervals.mean(axis=0)
        return self.pgmFile.bbnIntervals

    def _getHarmonicsIndexes(self) -> np.ndarray:
        assert self.pgmFile is not None and self.pgmFile.fsMhz is not None and self.hifuFreqMhz is not None and isinstance(
            self.baseLineMean, np.ndarray)
        if self.harmonicFreqSectionIndexes is None:
            scanFreq = self.pgmFile.fsMhz / 2
            nHarmonics = np.floor(scanFreq / self.hifuFreqMhz).astype(int)
            nFFT = self.baseLineMean.size
            harmonicFreqSectionIndexes = (nFFT * self.hifuFreqMhz /
                                          scanFreq) * np.c_[np.arange(nHarmonics) + 0.25,
                                                            (np.arange(nHarmonics) + 1) - 0.25]
            minRange = np.min(np.absolute(harmonicFreqSectionIndexes[:, 0] -
                                          harmonicFreqSectionIndexes[:, 1])).astype(int)
            harmonicFreqSectionIndexes = np.vstack(
                (harmonicFreqSectionIndexes[:, 0], harmonicFreqSectionIndexes[:, 0] + minRange)).astype(int).T
            self.harmonicFreqSectionIndexes = np.linspace(harmonicFreqSectionIndexes[:, 0],
                                                          harmonicFreqSectionIndexes[:, 1],
                                                          num=minRange,
                                                          dtype=np.int32)
        return self.harmonicFreqSectionIndexes

    def _updateBackgroundRfDataSect(self):
        assert self.pgmFile is not None and isinstance(self.pgmFile.rf, np.ndarray)
        if not self.pgmFile.isHifu:
            self.backgroundRfSect = self.pgmFile.rf[self.scanLineRowRange, :]

    @property
    def scanLineRowRange(self) -> np.ndarray:
        return np.arange(self.scanLineRowIndexStart, self.scanLineRowIndexEnd)
