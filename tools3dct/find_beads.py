#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Detect beads based on cross-correlation, hough-transform and intensity-based thresholding

Call GUI via wrapper function find_beads_GUI or from command line.
Run 'python3 find_beads.py --help' command line usage information.

Detected bead coordinates are returned by the underlying find_beads function.
Option to pre-load images and specify pixel size in command line.

Copyright (C) 2021  EMBL/Herman Fung, EMBL/Julia Mahamid

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import numpy as np
import tifffile

import argparse
import sys, os

from skimage import filters, draw, morphology, feature
from skimage.transform import hough_circle
from scipy import signal
import cv2

from tools3dct import docs

from PyQt5 import QtCore, QtGui, QtWidgets

class QGraphicsSceneCustom(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        if event.delta() > 0:
            scalingFactor = 1.15
        else:
            scalingFactor = 1 / 1.15
        mouse_position = event.scenePos()
        view_center = self.parent().mapToScene(QtCore.QPoint(self.parent().width()//2,self.parent().height()//2))
        new_center = mouse_position+(view_center-mouse_position)/scalingFactor
        self.parent().scale(scalingFactor, scalingFactor)
        self.parent().centerOn(new_center)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            self.parent().setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
    
    def mouseReleaseEvent(self, event):
        self.parent().setDragMode(QtWidgets.QGraphicsView.NoDrag)

# Form implementation generated from reading ui file 'find_beads.ui'
# Created by: PyQt5 UI code generator 5.13.2
class Ui_MainWindow(object):
    def __init__(self, imgFile=None, pxSize=None):
        self.imgFile = imgFile
        try:
            self.pxSize = float(pxSize) * 1E-9
        except (ValueError, TypeError):
            self.pxSize = None
        self.workdir = os.getcwd()
        self.beadPen = QtGui.QPen(QtGui.QColor(127,231,229))
        self.beadBrush = QtGui.QBrush(QtGui.QColor(127,231,229))
        self.ellipseitemlist = []
        self.numBeads = 100
        self.beadSize = 1E-6
        self.ccMultiplier = 1.0
        self.houghMultiplier = 1.2
        self.thresholdMethod = 'isodata'
        self.flag_calculated = False
        self.flag_cc = True
        self.flag_hough = True
        self.img_3D = None
        self.pts = np.array([])
        self.ellipseitemlist = []

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(998, 579)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy)
        self.graphicsView.setMinimumSize(QtCore.QSize(768, 512))
        self.graphicsView.setObjectName("graphicsView")
        self.horizontalLayout.addWidget(self.graphicsView)
        self.verticalLayout_options = QtWidgets.QVBoxLayout()
        self.verticalLayout_options.setObjectName("verticalLayout_options")
        self.horizontalLayout_pxSize = QtWidgets.QHBoxLayout()
        self.horizontalLayout_pxSize.setObjectName("horizontalLayout_pxSize")
        spacerItem = QtWidgets.QSpacerItem(0, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_pxSize.addItem(spacerItem)
        self.label_pxSize = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_pxSize.sizePolicy().hasHeightForWidth())
        self.label_pxSize.setSizePolicy(sizePolicy)
        self.label_pxSize.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_pxSize.setObjectName("label_pxSize")
        self.horizontalLayout_pxSize.addWidget(self.label_pxSize)
        self.lineEdit_pxSize = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_pxSize.sizePolicy().hasHeightForWidth())
        self.lineEdit_pxSize.setSizePolicy(sizePolicy)
        self.lineEdit_pxSize.setMaximumSize(QtCore.QSize(56, 16777215))
        self.lineEdit_pxSize.setObjectName("lineEdit_pxSize")
        self.horizontalLayout_pxSize.addWidget(self.lineEdit_pxSize, 0, QtCore.Qt.AlignRight)
        self.verticalLayout_options.addLayout(self.horizontalLayout_pxSize)
        self.horizontalLayout_numBeads = QtWidgets.QHBoxLayout()
        self.horizontalLayout_numBeads.setObjectName("horizontalLayout_numBeads")
        self.label_numBeads = QtWidgets.QLabel(self.centralwidget)
        self.label_numBeads.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_numBeads.setObjectName("label_numBeads")
        self.horizontalLayout_numBeads.addWidget(self.label_numBeads)
        self.spinBox_numBeads = QtWidgets.QSpinBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_numBeads.sizePolicy().hasHeightForWidth())
        self.spinBox_numBeads.setSizePolicy(sizePolicy)
        self.spinBox_numBeads.setMaximumSize(QtCore.QSize(56, 16777215))
        self.spinBox_numBeads.setAlignment(QtCore.Qt.AlignCenter)
        self.spinBox_numBeads.setMaximum(500)
        self.spinBox_numBeads.setSingleStep(50)
        self.spinBox_numBeads.setProperty("value", 100)
        self.spinBox_numBeads.setObjectName("spinBox_numBeads")
        self.horizontalLayout_numBeads.addWidget(self.spinBox_numBeads)
        self.verticalLayout_options.addLayout(self.horizontalLayout_numBeads)
        self.horizontalLayout_beadSize = QtWidgets.QHBoxLayout()
        self.horizontalLayout_beadSize.setObjectName("horizontalLayout_beadSize")
        self.label_beadSize = QtWidgets.QLabel(self.centralwidget)
        self.label_beadSize.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_beadSize.setObjectName("label_beadSize")
        self.horizontalLayout_beadSize.addWidget(self.label_beadSize)
        self.doubleSpinBox_beadSize = QtWidgets.QDoubleSpinBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_beadSize.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_beadSize.setSizePolicy(sizePolicy)
        self.doubleSpinBox_beadSize.setMaximumSize(QtCore.QSize(56, 16777215))
        self.doubleSpinBox_beadSize.setAlignment(QtCore.Qt.AlignCenter)
        self.doubleSpinBox_beadSize.setMaximum(5.0)
        self.doubleSpinBox_beadSize.setSingleStep(0.1)
        self.doubleSpinBox_beadSize.setProperty("value", 1.0)
        self.doubleSpinBox_beadSize.setObjectName("doubleSpinBox_beadSize")
        self.horizontalLayout_beadSize.addWidget(self.doubleSpinBox_beadSize)
        self.verticalLayout_options.addLayout(self.horizontalLayout_beadSize)
        self.checkBox_cc = QtWidgets.QCheckBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_cc.sizePolicy().hasHeightForWidth())
        self.checkBox_cc.setSizePolicy(sizePolicy)
        self.checkBox_cc.setChecked(True)
        self.checkBox_cc.setObjectName("checkBox_cc")
        self.verticalLayout_options.addWidget(self.checkBox_cc, 0, QtCore.Qt.AlignLeft)
        self.horizontalLayout_cc = QtWidgets.QHBoxLayout()
        self.horizontalLayout_cc.setObjectName("horizontalLayout_cc")
        self.label_multiplier_cc = QtWidgets.QLabel(self.centralwidget)
        self.label_multiplier_cc.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_multiplier_cc.setObjectName("label_multiplier_cc")
        self.horizontalLayout_cc.addWidget(self.label_multiplier_cc)
        self.doubleSpinBox_cc = QtWidgets.QDoubleSpinBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_cc.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_cc.setSizePolicy(sizePolicy)
        self.doubleSpinBox_cc.setMaximumSize(QtCore.QSize(56, 16777215))
        self.doubleSpinBox_cc.setAlignment(QtCore.Qt.AlignCenter)
        self.doubleSpinBox_cc.setMaximum(5.0)
        self.doubleSpinBox_cc.setSingleStep(0.1)
        self.doubleSpinBox_cc.setProperty("value", 1.0)
        self.doubleSpinBox_cc.setObjectName("doubleSpinBox_cc")
        self.horizontalLayout_cc.addWidget(self.doubleSpinBox_cc)
        self.verticalLayout_options.addLayout(self.horizontalLayout_cc)
        self.checkBox_hough = QtWidgets.QCheckBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_hough.sizePolicy().hasHeightForWidth())
        self.checkBox_hough.setSizePolicy(sizePolicy)
        self.checkBox_hough.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.checkBox_hough.setChecked(True)
        self.checkBox_hough.setObjectName("checkBox_hough")
        self.verticalLayout_options.addWidget(self.checkBox_hough, 0, QtCore.Qt.AlignLeft)
        self.horizontalLayout_hough = QtWidgets.QHBoxLayout()
        self.horizontalLayout_hough.setObjectName("horizontalLayout_hough")
        self.label_multiplier_hough = QtWidgets.QLabel(self.centralwidget)
        self.label_multiplier_hough.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_multiplier_hough.setObjectName("label_multiplier_hough")
        self.horizontalLayout_hough.addWidget(self.label_multiplier_hough)
        self.doubleSpinBox_hough = QtWidgets.QDoubleSpinBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_hough.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_hough.setSizePolicy(sizePolicy)
        self.doubleSpinBox_hough.setMaximumSize(QtCore.QSize(56, 16777215))
        self.doubleSpinBox_hough.setAlignment(QtCore.Qt.AlignCenter)
        self.doubleSpinBox_hough.setDecimals(2)
        self.doubleSpinBox_hough.setMaximum(5.0)
        self.doubleSpinBox_hough.setSingleStep(0.1)
        self.doubleSpinBox_hough.setProperty("value", 1.2)
        self.doubleSpinBox_hough.setObjectName("doubleSpinBox_hough")
        self.horizontalLayout_hough.addWidget(self.doubleSpinBox_hough)
        self.verticalLayout_options.addLayout(self.horizontalLayout_hough)
        self.label_thresholdMethod = QtWidgets.QLabel(self.centralwidget)
        self.label_thresholdMethod.setObjectName("label_thresholdMethod")
        self.verticalLayout_options.addWidget(self.label_thresholdMethod)
        self.verticalLayout_radioButtons = QtWidgets.QVBoxLayout()
        self.verticalLayout_radioButtons.setContentsMargins(35, -1, -1, -1)
        self.verticalLayout_radioButtons.setObjectName("verticalLayout_radioButtons")
        self.radioButton_isodata = QtWidgets.QRadioButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.radioButton_isodata.sizePolicy().hasHeightForWidth())
        self.radioButton_isodata.setSizePolicy(sizePolicy)
        self.radioButton_isodata.setChecked(True)
        self.radioButton_isodata.setObjectName("radioButton_isodata")
        self.verticalLayout_radioButtons.addWidget(self.radioButton_isodata)
        self.radioButton_otsu = QtWidgets.QRadioButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.radioButton_otsu.sizePolicy().hasHeightForWidth())
        self.radioButton_otsu.setSizePolicy(sizePolicy)
        self.radioButton_otsu.setChecked(False)
        self.radioButton_otsu.setObjectName("radioButton_otsu")
        self.verticalLayout_radioButtons.addWidget(self.radioButton_otsu)
        self.radioButton_mean = QtWidgets.QRadioButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.radioButton_mean.sizePolicy().hasHeightForWidth())
        self.radioButton_mean.setSizePolicy(sizePolicy)
        self.radioButton_mean.setObjectName("radioButton_mean")
        self.verticalLayout_radioButtons.addWidget(self.radioButton_mean)
        self.verticalLayout_options.addLayout(self.verticalLayout_radioButtons)
        self.pushButton_loadImage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_loadImage.setObjectName("pushButton_loadImage")
        self.verticalLayout_options.addWidget(self.pushButton_loadImage)
        self.pushButton_detectBeads = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_detectBeads.setObjectName("pushButton_detectBeads")
        self.verticalLayout_options.addWidget(self.pushButton_detectBeads)
        self.pushButton_exportMask = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_exportMask.setObjectName("pushButton_exportMask")
        self.verticalLayout_options.addWidget(self.pushButton_exportMask)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_options.addItem(spacerItem1)
        self.checkBox_togglePoints = QtWidgets.QCheckBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_togglePoints.sizePolicy().hasHeightForWidth())
        self.checkBox_togglePoints.setSizePolicy(sizePolicy)
        self.checkBox_togglePoints.setObjectName("checkBox_togglePoints")
        self.verticalLayout_options.addWidget(self.checkBox_togglePoints)
        self.horizontalLayout.addLayout(self.verticalLayout_options)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setNativeMenuBar(False)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 998, 22))
        self.menuBar.setObjectName("menuBar")
        self.menuHelp = QtWidgets.QMenu(self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menuBar)
        self.actionDocumentation = QtWidgets.QAction(MainWindow)
        self.actionDocumentation.setObjectName("actionDocumentation")
        self.menuHelp.addAction(self.actionDocumentation)
        self.menuBar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.MainWindow = MainWindow
        self.helpdoc = docs.help(MainWindow)

        self.scene = QGraphicsSceneCustom(self.graphicsView)
        self.pixmapitem = self.scene.addPixmap(QtGui.QPixmap())
        self.graphicsView.setScene(self.scene)

        self.actionDocumentation.triggered.connect(self.helpdoc.findBeads)        
        self.lineEdit_pxSize.textChanged.connect(self.update_pixel_size)
        self.spinBox_numBeads.valueChanged.connect(self.update_num_beads)
        self.doubleSpinBox_beadSize.valueChanged.connect(self.update_bead_radius)
        self.checkBox_cc.clicked.connect(self.toggle_cc)
        self.doubleSpinBox_cc.valueChanged.connect(self.update_cc_multiplier)
        self.checkBox_hough.clicked.connect(self.toggle_hough)
        self.doubleSpinBox_hough.valueChanged.connect(self.update_hough_multiplier)
        self.radioButton_isodata.toggled.connect(self.set_threshold_method)
        self.radioButton_otsu.toggled.connect(self.set_threshold_method)
        self.radioButton_mean.toggled.connect(self.set_threshold_method)
        self.pushButton_loadImage.clicked.connect(self.choose_image)
        self.pushButton_detectBeads.clicked.connect(self.detect_beads)
        self.pushButton_exportMask.clicked.connect(self.export_mask)
        self.checkBox_togglePoints.clicked.connect(self.toggle_points)

        MainWindow.show()
        if self.imgFile is not None:
            self.load_image()
        if self.pxSize is not None:
            self.lineEdit_pxSize.setText(f'{self.pxSize*1E9:.1f}')

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Detect Beads"))
        self.label_pxSize.setText(_translate("MainWindow", "Pixel Size (nm)"))
        self.label_numBeads.setText(_translate("MainWindow", "Number of Beads"))
        self.label_beadSize.setText(_translate("MainWindow", "Bead Size (μm)"))
        self.checkBox_cc.setText(_translate("MainWindow", "Cross-Correlation"))
        self.label_multiplier_cc.setText(_translate("MainWindow", "Multiplier"))
        self.checkBox_hough.setText(_translate("MainWindow", "Hough Transform"))
        self.label_multiplier_hough.setText(_translate("MainWindow", "Multiplier"))
        self.label_thresholdMethod.setText(_translate("MainWindow", "Thresholding Method"))
        self.radioButton_isodata.setText(_translate("MainWindow", "Isodata"))
        self.radioButton_otsu.setText(_translate("MainWindow", "Otsu"))
        self.radioButton_mean.setText(_translate("MainWindow", "Mean"))
        self.pushButton_loadImage.setText(_translate("MainWindow", "Load Image"))
        self.pushButton_detectBeads.setText(_translate("MainWindow", "Detect Beads"))
        self.pushButton_exportMask.setText(_translate("MainWindow", "Export Mask"))
        self.checkBox_togglePoints.setText(_translate("MainWindow", "Show/Hide"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionDocumentation.setText(_translate("MainWindow", "Documentation"))

    def choose_image(self):
        self.imgFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select an image', self.workdir,'Image Files (*.tif *.tiff);; All (*.*)')[0]
        self.load_image()

    def load_image(self):
        if self.imgFile is not None:
            try:
                img = tifffile.imread(self.imgFile)
                if img.ndim == 2:
                    self.img = normalized_uint8(img)
                elif img.ndim == 3:
                    is_3D = QtWidgets.QMessageBox.question(self.MainWindow,'Image Check','Is the image 3D?')
                    if is_3D == QtWidgets.QMessageBox.Yes:
                        self.img_3D = img
                        self.img = normalized_uint8(np.amax(img,0))

                    else:
                        self.img = normalized_uint8(img)
            except:
                if self.imgFile != '':
                    self.statusbar.showMessage('File has unexpected format',5000)
                return
            with tifffile.TiffFile(self.imgFile) as tif:
                try:
                    self.pxSize = tif.pages[0].tags['FEI_HELIOS'].value['Scan']['PixelWidth']
                    self.lineEdit_pxSize.setText(f'{self.pxSize*1E9:.1f}')
                except KeyError:
                    self.statusbar.showMessage('Pixel size not found',5000)
            self.workdir = os.path.dirname(self.imgFile)
            self.pixmapitem.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(self.img,self.img.shape[1],self.img.shape[0],QtGui.QImage.Format_Grayscale8)))
            self.graphicsView.setSceneRect(self.scene.sceneRect())
            self.graphicsView.fitInView(self.graphicsView.sceneRect(),QtCore.Qt.KeepAspectRatio)

    def update_pixel_size(self):
        try:
            self.pxSize = float(self.lineEdit_pxSize.text()) * 1E-9
        except ValueError:
            pass

    def update_num_beads(self):
        try:
            self.numBeads = int(self.spinBox_numBeads.text())
        except ValueError:
            pass
    
    def update_bead_radius(self):
        try:
            self.beadSize = float(self.doubleSpinBox_beadSize.text()) * 1E-6
        except ValueError:
            pass

    def update_cc_multiplier(self):
        try:
            self.ccMultiplier = float(self.doubleSpinBox_cc.text())
        except ValueError:
            pass

    def update_hough_multiplier(self):
        try:
            self.houghMultiplier = float(self.doubleSpinBox_hough.text())
        except ValueError:
            pass

    def set_threshold_method(self):
        if self.radioButton_isodata.isChecked():
            self.thresholdMethod = 'isodata'
        elif self.radioButton_otsu.isChecked():
            self.thresholdMethod = 'otsu'
        elif self.radioButton_mean.isChecked():
            self.thresholdMethod = 'mean'        

    def toggle_cc(self):
        if self.checkBox_cc.checkState() == 2:
            self.flag_cc = True
        else:
            self.flag_cc = False

    def toggle_hough(self):
        if self.checkBox_hough.checkState() == 2:
            self.flag_hough = True
        else:
            self.flag_hough = False

    def detect_beads(self):
        if self.pxSize is not None:
            self.pts = find_beads(self.img, self.pxSize, self.numBeads, self.beadSize, self.flag_cc, self.ccMultiplier, self.flag_hough, self.houghMultiplier, self.thresholdMethod)
            self.plot_points()
            self.checkBox_togglePoints.setCheckState(2)

    def plot_points(self):
        if self.pts.size > 0:
            markerSize = int(4 / 1536 * self.scene.width())
            for item in self.ellipseitemlist:
                self.scene.removeItem(item)
            self.ellipseitemlist = []
            for pt in self.pts:
                ellipseitem = self.scene.addEllipse(pt[0]-markerSize, pt[1]-markerSize, markerSize * 2, markerSize * 2, self.beadPen, self.beadBrush)
                self.ellipseitemlist.append(ellipseitem)

    def export_mask(self):
        if self.pts.size > 0:
            r = int(self.beadSize/self.pxSize/1.5)
            circle = draw_circle(r)
            if self.img_3D is None:
                mask = np.zeros(self.img.shape,dtype='uint8')
                for pt in self.pts:
                    mask[int(pt[1])-r:int(pt[1])+r+2, int(pt[0])-r:int(pt[0])+r+2] = circle
            else:
                mask = np.zeros(self.img_3D.shape,dtype='uint8')
                for pt in self.pts:
                    z = np.argmax(self.img_3D[:,pt[1],pt[0]],0)  # brightest pixel in z
                    mask[z, int(pt[1])-r:int(pt[1])+r+2, int(pt[0])-r:int(pt[0])+r+2] = circle
            outfile = os.path.normpath(os.path.join(self.workdir,'predictions.tif'))
            tifffile.imwrite(outfile,mask)
            self.statusbar.showMessage('Mask written: '+outfile)
            print('Mask written: '+outfile)

    def toggle_points(self):
        if len(self.ellipseitemlist) > 0:
            if self.checkBox_togglePoints.checkState() == 2:
                for item in self.ellipseitemlist:
                    item.setVisible(True)
            else:
                for item in self.ellipseitemlist:
                    item.setVisible(False)

# QMainWindow subclass to hold ui
class QMainWindowCustom(QtWidgets.QMainWindow):
    def __init__(self,parent=None,imgFile=None,pxSize=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow(imgFile,pxSize)
        self.ui.setupUi(self)  # method contains MainWindow.show(), QtWidgets.QGraphicsView.fitInView() requires visible window

### Base functions ###

# Construct numpy.ndarray with a filled circle in the middle
def draw_circle(r):
    image = np.zeros([2*(r+1),2*(r+1)])
    coord = draw.circle(r+0.5,r+0.5,r)
    image[coord] = 255
    return image

# Construct 2D Gaussian kernel
def gaussian_kernel(kernlen, std):
    """Returns a 2D Gaussian kernel array."""
    gkern1d = signal.gaussian(kernlen, std=std).reshape(kernlen, 1)
    gkern2d = np.outer(gkern1d, gkern1d) * 255
    return gkern2d.astype(np.uint8)

# Convert to grayscale if coloured, assuming RGB, and return normalized 8-bit image
def normalized_uint8(image):
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    lower_bound = np.min(gray)
    upper_bound = np.max(gray)
    lut = np.concatenate([
        np.zeros(lower_bound, dtype=np.uint16),
        np.linspace(0, 255, upper_bound - lower_bound).astype(np.uint16),
        np.ones(2 ** 16 - upper_bound, dtype=np.uint16) * 255
    ])
    return lut[gray].astype(np.uint8)

# Actual function, requires 8-bit 2D image and pixel size, returns xy-coordinates of detected beads
def find_beads(image, pxSize, numBeads=100, beadSize=1E-6, flag_cc=True, ccMultiplier=1.0, flag_hough=True, houghMultiplier=1.2, thresholdMethod='isodata'):

    bead_radius = beadSize/pxSize/2

    # Automatic thresholding
    if thresholdMethod == 'isodata':
        threshold = filters.threshold_isodata(image)
    elif thresholdMethod == 'otsu':
        threshold = filters.threshold_otsu(image)
    elif thresholdMethod == 'mean':
        threshold = filters.threshold_mean(image)
    else:
        print('Unknown thresholding method')
        return None
    
    # Soft mask from thresholded image
    selem = draw_circle(int(np.around(bead_radius*2)))
    softmask = filters.gaussian(morphology.dilation(image>threshold,selem),sigma=2)

    # Cross-correlation
    if flag_cc:
        # Construct Gaussain kernel
        cc_bead_radius = int(np.around(bead_radius*ccMultiplier))
        cc_bead_diameter = cc_bead_radius * 2
        bead = gaussian_kernel(cc_bead_diameter*2,cc_bead_radius)
        # Calculate CC
        res = cv2.matchTemplate(image,bead,cv2.TM_CCOEFF_NORMED)
        cc_map = np.zeros(image.shape)
        cc_map[cc_bead_diameter:-1*cc_bead_diameter+1,cc_bead_diameter:-1*cc_bead_diameter+1] = res
    else:
        cc_map = np.ones(image.shape)

    # Hough transform
    if flag_hough:
        edges = feature.canny(image,1,threshold,threshold)  # edge detection in non-thresholded image
        # hough_radii = np.arange(bead_radius, bead_radius*2, 1)
        hough_transform = hough_circle(edges, int(bead_radius*houghMultiplier))  # find circles of given radius/radii
        hough_transform_max = np.amax(hough_transform,axis=0)  # maximum projection
    else:
        hough_transform_max = np.ones(image.shape)

    metric = cc_map * cc_map * hough_transform_max * softmask
    coord = feature.peak.peak_local_max(metric, min_distance=int(bead_radius*2),num_peaks=numBeads,threshold_rel=0.2)

    coord = np.flip(coord,axis=1)  # y,x to x,y

    return coord

def find_beads_GUI(imgFile=None,pxSize=None,parentWidget=None):
    MainWindow = QMainWindowCustom(parentWidget,imgFile,pxSize)
    return MainWindow


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Detect beads based on cross-correlation and Hough transform')
    parser.add_argument('--img', dest='imgFile', metavar='FILE', help='2D or 3D image of TIFF format')
    parser.add_argument('--px', dest='pxSize', type=float, metavar='NUMBER', help='pixel size in nm')
    args = parser.parse_args()

    if args.imgFile is not None:
        args.imgFile = os.path.abspath(args.imgFile)

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = find_beads_GUI(args.imgFile,args.pxSize)
    sys.exit(app.exec_())
