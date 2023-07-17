"""
Open a Qt Widget to display the b-mode of a certain pgm file interactively
"""
import sys

from PySide6 import QtWidgets
from PySide6.QtCore import Slot, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from .pgm import PGMFile


class BModeWidget(QtWidgets.QWidget):
    def __init__(self, pgmFile: PGMFile):
        super().__init__()

        self.pgmFile = pgmFile
        self.setWindowTitle(f"PGM File: {pgmFile.fileFullPath}")

        # b mode display
        self.plotCanvas = FigureCanvasQTAgg(Figure(figsize=(5, 3)))
        self.axes = self.plotCanvas.figure.subplots()
        self.toolbar = NavigationToolbar2QT(self.plotCanvas, self)

        self.dynamicText = QtWidgets.QLabel(f"# Dynamic Range")
        self.dynamicText.setTextFormat(Qt.TextFormat.MarkdownText)
        self.lowerDynamicRange = QtWidgets.QDoubleSpinBox()
        self.lowerDynamicRange.setPrefix("Lower: ")
        self.lowerDynamicRange.setDecimals(0)
        self.lowerDynamicRange.setRange(0, 250)
        self.lowerDynamicRange.setSingleStep(5)
        self.lowerDynamicRange.setValue(pgmFile.defaultDynamicRange[0])
        self.upperDynamicRange = QtWidgets.QDoubleSpinBox()
        self.upperDynamicRange.setPrefix("Higher: ")
        self.upperDynamicRange.setDecimals(0)
        self.upperDynamicRange.setRange(0, 250)
        self.upperDynamicRange.setSingleStep(5)
        self.upperDynamicRange.setValue(pgmFile.defaultDynamicRange[1])

        # layout
        self.inputLayout = QtWidgets.QVBoxLayout()
        self.inputLayout.addWidget(self.dynamicText)
        self.inputLayout.addWidget(self.lowerDynamicRange)
        self.inputLayout.addWidget(self.upperDynamicRange)
        self.canvasLayout = QtWidgets.QVBoxLayout()
        self.canvasLayout.addWidget(self.toolbar)
        self.canvasLayout.addWidget(self.plotCanvas)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.inputLayout)
        self.layout.addLayout(self.canvasLayout)
        self.setLayout(self.layout)

        # link to update function
        self.lowerDynamicRange.valueChanged.connect(self.showBMode)
        self.upperDynamicRange.valueChanged.connect(self.showBMode)
        self.showBMode()

    @Slot()
    def showBMode(self):
        self.pgmFile._getBMode(upperDisplayRangeDb=self.upperDynamicRange.value(),
                               lowerDisplayRangeDb=self.lowerDynamicRange.value())
        self.axes.clear()
        self.axes.imshow(self.pgmFile.bModeData, cmap='gray', aspect='auto')
        self.plotCanvas.draw()
        self.resize(self.sizeHint())


class BModeWindow:
    def __init__(self, pgmFile: PGMFile):
        qApp = QtWidgets.QApplication.instance()
        if not qApp:
            qApp = QtWidgets.QApplication(sys.argv)
        self.bModeWidget = BModeWidget(pgmFile=pgmFile)
        self.bModeWidget.show()
        qApp.exec()
        print(f"Final chosen dynamic range is "
              f"[{self.bModeWidget.lowerDynamicRange.value():.0f},{self.bModeWidget.upperDynamicRange.value():.0f}]")
