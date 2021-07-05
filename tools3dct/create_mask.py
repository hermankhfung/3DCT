#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Create mask to fluorescence volume based on FIB and SEM images

Call GUI via wrapper function create_mask_GUI or from command line.
Run 'python3 create_mask.py --help' for command line usage information.

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
import cv2
import re

import argparse
import os, sys

from tools3dct.core import Param3D, QGraphicsSceneCustom, rotate, corr_transform
from tools3dct import docs

from PyQt5 import QtCore, QtGui, QtWidgets



class QGraphicsSceneCustom_FIB(QGraphicsSceneCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pen = QtGui.QPen(QtGui.QColor(249,106,80))
        self.brush = QtGui.QBrush(QtGui.QColor(249,106,80))
        self.ellipseitem = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            x = event.scenePos().x()
            y = event.scenePos().y()
            if self.ellipseitem is not None:
                self.removeItem(self.ellipseitem)
            markerSize = int(2 / 1536 * self.width())
            self.ellipseitem = self.addEllipse(-markerSize, -markerSize, markerSize * 2, markerSize * 2, self.pen, self.brush)
            self.ellipseitem.setPos(x,y)
            self.ellipseitem.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        elif event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            self.parent().setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            super(QGraphicsSceneCustom_FIB,self).mousePressEvent(event)
    
class QGraphicsSceneCustom_SEM(QGraphicsSceneCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.boundaryPen = QtGui.QPen(QtGui.QColor(249,106,80))
        self.boundaryBrush = QtGui.QBrush(QtCore.Qt.transparent)
        self.interiorPen = QtGui.QPen(QtGui.QColor(127,231,229))
        self.interiorBrush = QtGui.QBrush(QtGui.QColor(127,231,229))
        self.polygon = QtGui.QPolygonF()
        self.graphicspathitem = QtWidgets.QGraphicsPathItem()
        self.graphicspathitem.setPen(self.boundaryPen)
        self.graphicspathitem.setBrush(self.boundaryBrush)
        self.ellipseitem = None
        self.ellipseitem_interior = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.NoModifier:
            if self.polygon.size() > 1 and self.polygon.isClosed():
                self.polygon.clear()
            self.polygon << event.scenePos()
            self.update_polygon()
        elif event.button() == QtCore.Qt.RightButton:
            if self.polygon.size() > 0 and not self.polygon.isClosed():
                self.polygon.append(self.polygon[0])
                self.update_polygon()
        elif event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            x = event.scenePos().x()
            y = event.scenePos().y()
            if self.ellipseitem_interior is not None:
                self.removeItem(self.ellipseitem_interior)
            markerSize = int(2 / 1536 * self.width())
            self.ellipseitem_interior = self.addEllipse(-markerSize, -markerSize, markerSize * 2, markerSize * 2, self.interiorPen, self.interiorBrush)
            self.ellipseitem_interior.setPos(x,y)
            self.ellipseitem_interior.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        elif event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            self.parent().setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            super(QGraphicsSceneCustom_SEM,self).mousePressEvent(event)

    def keyPressEvent(self, event):
        super(QGraphicsSceneCustom_SEM,self).keyPressEvent(event)
        if self.hasFocus() and event.key() == QtCore.Qt.Key_Backspace and self.polygon.size() > 0:
            self.polygon.remove(self.polygon.size()-1)
            self.update_polygon()
        elif self.hasFocus() and event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape]:
            if not self.polygon.isClosed():
                self.polygon.append(self.polygon[0])
                self.update_polygon()

    def update_polygon(self):
        painterpath = QtGui.QPainterPath()
        painterpath.addPolygon(self.polygon)
        self.graphicspathitem.setPath(painterpath)
        if self.graphicspathitem not in self.items():
            self.addItem(self.graphicspathitem)


# Form implementation generated from reading ui file 'create_mask.ui'
# Created by: PyQt5 UI code generator 5.13.2
class Ui_MainWindow(object):

    def __init__(self,fibFile=None,fibparamFile=None,semFile=None,semparamFile=None,lmThickness=None,cfPxSize=None,cfFile=None):
        self.fibFile = fibFile
        self.fibparamFile = fibparamFile
        self.semFile= semFile
        self.semparamFile = semparamFile
        try:
            self.lmThickness = float(lmThickness) * 1E-9
        except (ValueError, TypeError):
            self.lmThickness = None
        try:
            self.cfPxSize = float(cfPxSize) * 1E-9
        except (ValueError, TypeError):
            self.cfPxSize = None
        self.cfFile = cfFile
        self.fibParam = None
        self.semParam = None
        self.nX = None
        self.flag_skipSEM = False
        self.workdir = os.getcwd()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(804, 512)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_graphicsViews = QtWidgets.QHBoxLayout()
        self.horizontalLayout_graphicsViews.setObjectName("horizontalLayout_graphicsViews")
        self.graphicsView_SEM = QtWidgets.QGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView_SEM.sizePolicy().hasHeightForWidth())
        self.graphicsView_SEM.setSizePolicy(sizePolicy)
        self.graphicsView_SEM.setMinimumSize(QtCore.QSize(384, 256))
        self.graphicsView_SEM.setObjectName("graphicsView_SEM")
        self.graphicsView_SEM.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView_SEM.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalLayout_graphicsViews.addWidget(self.graphicsView_SEM)
        self.graphicsView_FIB = QtWidgets.QGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView_FIB.sizePolicy().hasHeightForWidth())
        self.graphicsView_FIB.setSizePolicy(sizePolicy)
        self.graphicsView_FIB.setMinimumSize(QtCore.QSize(384, 256))
        self.graphicsView_FIB.setObjectName("graphicsView_FIB")
        self.graphicsView_FIB.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView_FIB.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalLayout_graphicsViews.addWidget(self.graphicsView_FIB)
        self.verticalLayout.addLayout(self.horizontalLayout_graphicsViews)
        self.horizontalLayout_buttons = QtWidgets.QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName("horizontalLayout_buttons")
        self.pushButton_SEMimage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_SEMimage.setObjectName("pushButton_SEMimage")
        self.horizontalLayout_buttons.addWidget(self.pushButton_SEMimage)
        self.pushButton_FIBimage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_FIBimage.setObjectName("pushButton_FIBimage")
        self.horizontalLayout_buttons.addWidget(self.pushButton_FIBimage)
        self.verticalLayout.addLayout(self.horizontalLayout_buttons)
        self.horizontalLayout_SEMparam = QtWidgets.QHBoxLayout()
        self.horizontalLayout_SEMparam.setObjectName("horizontalLayout_SEMparam")
        self.label_SEMparam = QtWidgets.QLabel(self.centralwidget)
        self.label_SEMparam.setObjectName("label_SEMparam")
        self.horizontalLayout_SEMparam.addWidget(self.label_SEMparam)
        self.lineEdit_SEMparam = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_SEMparam.setObjectName("lineEdit_SEMparam")
        self.horizontalLayout_SEMparam.addWidget(self.lineEdit_SEMparam)
        self.toolButton_SEMparam = QtWidgets.QToolButton(self.centralwidget)
        self.toolButton_SEMparam.setObjectName("toolButton_SEMparam")
        self.horizontalLayout_SEMparam.addWidget(self.toolButton_SEMparam)
        self.verticalLayout.addLayout(self.horizontalLayout_SEMparam)
        self.horizontalLayout_FIBparam = QtWidgets.QHBoxLayout()
        self.horizontalLayout_FIBparam.setObjectName("horizontalLayout_FIBparam")
        self.label_FIBparam = QtWidgets.QLabel(self.centralwidget)
        self.label_FIBparam.setObjectName("label_FIBparam")
        self.horizontalLayout_FIBparam.addWidget(self.label_FIBparam)
        self.lineEdit_FIBparam = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_FIBparam.setObjectName("lineEdit_FIBparam")
        self.horizontalLayout_FIBparam.addWidget(self.lineEdit_FIBparam)
        self.toolButton_FIBparam = QtWidgets.QToolButton(self.centralwidget)
        self.toolButton_FIBparam.setObjectName("toolButton_FIBparam")
        self.horizontalLayout_FIBparam.addWidget(self.toolButton_FIBparam)
        self.verticalLayout.addLayout(self.horizontalLayout_FIBparam)
        self.horizontalLayout_fluoVolume = QtWidgets.QHBoxLayout()
        self.horizontalLayout_fluoVolume.setObjectName("horizontalLayout_fluoVolume")
        self.label_fluoVolume = QtWidgets.QLabel(self.centralwidget)
        self.label_fluoVolume.setObjectName("label_fluoVolume")
        self.horizontalLayout_fluoVolume.addWidget(self.label_fluoVolume)
        self.lineEdit_fluoVolume = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_fluoVolume.setObjectName("lineEdit_fluoVolume")
        self.horizontalLayout_fluoVolume.addWidget(self.lineEdit_fluoVolume)
        self.toolButton_fluoVolume = QtWidgets.QToolButton(self.centralwidget)
        self.toolButton_fluoVolume.setObjectName("toolButton_fluoVolume")
        self.horizontalLayout_fluoVolume.addWidget(self.toolButton_fluoVolume)
        self.verticalLayout.addLayout(self.horizontalLayout_fluoVolume)
        self.horizontalLayout_maskParam = QtWidgets.QHBoxLayout()
        self.horizontalLayout_maskParam.setObjectName("horizontalLayout_maskParam")
        self.label_lmThickness = QtWidgets.QLabel(self.centralwidget)
        self.label_lmThickness.setObjectName("label_lmThickness")
        self.horizontalLayout_maskParam.addWidget(self.label_lmThickness)
        self.lineEdit_thickness = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_thickness.sizePolicy().hasHeightForWidth())
        self.lineEdit_thickness.setSizePolicy(sizePolicy)
        self.lineEdit_thickness.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit_thickness.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_thickness.setObjectName("lineEdit_thickness")
        self.horizontalLayout_maskParam.addWidget(self.lineEdit_thickness)
        self.label_fluoPxSize = QtWidgets.QLabel(self.centralwidget)
        self.label_fluoPxSize.setObjectName("label_fluoPxSize")
        self.horizontalLayout_maskParam.addWidget(self.label_fluoPxSize)
        self.lineEdit_fluoPxSize = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_fluoPxSize.sizePolicy().hasHeightForWidth())
        self.lineEdit_fluoPxSize.setSizePolicy(sizePolicy)
        self.lineEdit_fluoPxSize.setMaximumSize(QtCore.QSize(50, 16777215))
        self.lineEdit_fluoPxSize.setObjectName("lineEdit_fluoPxSize")
        self.horizontalLayout_maskParam.addWidget(self.lineEdit_fluoPxSize)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_maskParam.addItem(spacerItem)
        self.checkBox_skipSEM = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_skipSEM.setObjectName("checkBox_skipSEM")
        self.horizontalLayout_maskParam.addWidget(self.checkBox_skipSEM)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_maskParam.addItem(spacerItem1)
        self.pushButton_createMask = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_createMask.setObjectName("pushButton_createMask")
        self.horizontalLayout_maskParam.addWidget(self.pushButton_createMask)
        self.verticalLayout.addLayout(self.horizontalLayout_maskParam)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setNativeMenuBar(False)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 804, 22))
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
        
        self.scene_sem = QGraphicsSceneCustom_SEM(self.graphicsView_SEM)
        self.scene_fib = QGraphicsSceneCustom_FIB(self.graphicsView_FIB)
        self.pixmapitem_sem = self.scene_sem.addPixmap(QtGui.QPixmap())
        self.pixmapitem_fib = self.scene_fib.addPixmap(QtGui.QPixmap())
        self.graphicsView_SEM.setScene(self.scene_sem)
        self.graphicsView_FIB.setScene(self.scene_fib)

        self.actionDocumentation.triggered.connect(self.helpdoc.createMask)        
        self.pushButton_SEMimage.clicked.connect(self.choose_SEM_image)
        self.pushButton_FIBimage.clicked.connect(self.choose_FIB_image)
        self.toolButton_SEMparam.clicked.connect(self.choose_SEM_param)
        self.toolButton_FIBparam.clicked.connect(self.choose_FIB_param)
        self.toolButton_fluoVolume.clicked.connect(self.choose_fluo_volume)
        self.lineEdit_thickness.textChanged.connect(self.update_lmThickness)
        self.lineEdit_fluoPxSize.textChanged.connect(self.update_cfPxSize)
        self.checkBox_skipSEM.clicked.connect(self.toggle_SEM)
        self.pushButton_createMask.clicked.connect(self.create_mask)

        MainWindow.show()
        if self.semFile is not None:
            self.load_SEM_image()
        if self.fibFile is not None:
            self.load_FIB_image()
        if self.semparamFile is not None:
            self.load_SEM_param()
        if self.fibparamFile is not None:
            self.load_FIB_param()
        if self.cfFile is not None:
            self.load_fluo_volume()
        if self.lmThickness is not None:
            self.lineEdit_thickness.setText(f'{self.lmThickness*1E9:.1f}')
        if self.cfPxSize is not None:
            self.lineEdit_fluoPxSize.setText(f'{self.cfPxSize*1E9:.1f}')

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Create Mask"))
        self.pushButton_SEMimage.setText(_translate("MainWindow", "Load SEM Image"))
        self.pushButton_FIBimage.setText(_translate("MainWindow", "Load FIB Image"))
        self.label_SEMparam.setText(_translate("MainWindow", "SEM Parameters"))
        self.toolButton_SEMparam.setText(_translate("MainWindow", "..."))
        self.label_FIBparam.setText(_translate("MainWindow", "FIB Parameters"))
        self.toolButton_FIBparam.setText(_translate("MainWindow", "..."))
        self.label_fluoVolume.setText(_translate("MainWindow", "Fluorescence Volume"))
        self.toolButton_fluoVolume.setText(_translate("MainWindow", "..."))
        self.label_lmThickness.setText(_translate("MainWindow", "Lamella Thickness (nm)"))
        self.label_fluoPxSize.setText(_translate("MainWindow", "Fluorescence Volume, Pixel Size (nm)"))
        self.checkBox_skipSEM.setText(_translate("MainWindow", "Skip SEM Masking"))
        self.pushButton_createMask.setText(_translate("MainWindow", "Create Mask"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionDocumentation.setText(_translate("MainWindow", "Documentation"))


    def choose_SEM_image(self):
        self.semFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select an SEM image', self.workdir,'Image Files (*.tif *.tiff);; All (*.*)')[0]
        self.load_SEM_image()
    
    def choose_FIB_image(self):
        self.fibFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select a FIB image', self.workdir,'Image Files (*.tif *.tiff);; All (*.*)')[0]
        self.load_FIB_image()

    def load_SEM_image(self):
        if self.semFile is not None:
            try:
                self.workdir = os.path.dirname(self.semFile)
                self.pixmapitem_sem.setPixmap(QtGui.QPixmap(self.semFile))
                self.graphicsView_SEM.setSceneRect(self.scene_sem.sceneRect())
                self.graphicsView_SEM.fitInView(self.graphicsView_SEM.sceneRect(),QtCore.Qt.KeepAspectRatio)
            except (PermissionError,FileNotFoundError,IsADirectoryError,ValueError,tifffile.tifffile.TiffFileError):
                pass
        
    def load_FIB_image(self):
        if self.fibFile is not None:
            try:
                self.workdir = os.path.dirname(self.fibFile)
                self.pixmapitem_fib.setPixmap(QtGui.QPixmap(self.fibFile))
                self.graphicsView_FIB.setSceneRect(self.scene_fib.sceneRect())
                self.graphicsView_FIB.fitInView(self.graphicsView_FIB.sceneRect(),QtCore.Qt.KeepAspectRatio)
            except (PermissionError,FileNotFoundError,IsADirectoryError,ValueError,tifffile.tifffile.TiffFileError):
                pass

    def choose_SEM_param(self):
        self.semparamFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select 3DCT text output for the SEM image', self.workdir,'Text File (*.txt);; All (*.*)')[0]
        self.load_SEM_param()

    def choose_FIB_param(self):
        self.fibparamFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select 3DCT text output for the FIB image', self.workdir,'Text File (*.txt);; All (*.*)')[0]
        self.load_FIB_param()

    def load_SEM_param(self):
        self.lineEdit_SEMparam.setText(self.semparamFile)
        try:
            self.semParam = Param3D(self.semparamFile)
            if self.semParam.bxx.size == 0:
                self.lineEdit_SEMparam.setStyleSheet("QLineEdit{background-color: rgba(255,0,0,80);}")
            else:
                self.lineEdit_SEMparam.setStyleSheet("QLineEdit{background-color: rgba(0,255,0,80);}")
        except UnicodeDecodeError:
            self.semParam = None
            self.lineEdit_SEMparam.setText(self.semparamFile)
            self.lineEdit_SEMparam.setStyleSheet("QLineEdit{background-color: rgba(255,0,0,80);}")
        except (PermissionError,FileNotFoundError,IsADirectoryError):
            self.semParam = None
            self.lineEdit_SEMparam.setText('')
            self.lineEdit_SEMparam.setStyleSheet("QLineEdit{background-color: white;}")

    def load_FIB_param(self):
        self.lineEdit_FIBparam.setText(self.fibparamFile)
        try:
            self.fibParam = Param3D(self.fibparamFile)
            if self.fibParam.bxx.size == 0:
                self.lineEdit_FIBparam.setStyleSheet("QLineEdit{background-color: rgba(255,0,0,80);}")
            else:
                self.lineEdit_FIBparam.setStyleSheet("QLineEdit{background-color: rgba(0,255,0,80);}")
        except UnicodeDecodeError:
            self.fibParam = None
            self.lineEdit_FIBparam.setText(self.fibparamFile)
            self.lineEdit_FIBparam.setStyleSheet("QLineEdit{background-color: rgba(255,0,0,80);}")
        except (PermissionError,FileNotFoundError,IsADirectoryError):
            self.fibParam = None
            self.lineEdit_FIBparam.setText('')
            self.lineEdit_FIBparam.setStyleSheet("QLineEdit{background-color: white;}")

    def choose_fluo_volume(self):
        self.cfFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select reference resliced fluorescence volume', self.workdir,'Image Files (*.tif *.tiff);; All (*.*)')[0]
        self.load_fluo_volume()

    def load_fluo_volume(self):
        self.lineEdit_fluoVolume.setText(self.cfFile)
        if self.cfFile is not None:
            try:
                vol = tifffile.imread(self.cfFile)
                self.nZ, self.nY, self.nX = vol.shape
                self.lineEdit_fluoVolume.setStyleSheet("QLineEdit{background-color: rgba(0,255,0,80);}")
            except (tifffile.tifffile.TiffFileError):  # non-TIFF image or 2D TIFF image
                self.nX = None
                self.lineEdit_fluoVolume.setStyleSheet("QLineEdit{background-color: rgba(255,0,0,80);}")
            except (ValueError,PermissionError,FileNotFoundError,IsADirectoryError):
                self.nX = None
                self.lineEdit_fluoVolume.setText('')
                self.lineEdit_fluoVolume.setStyleSheet("QLineEdit{background-color: white;}")

    def update_lmThickness(self):
        try:
            self.lmThickness = float(self.lineEdit_thickness.text()) * 1E-9
        except ValueError:
            pass

    def update_cfPxSize(self):
        try:
            self.cfPxSize = float(self.lineEdit_fluoPxSize.text()) * 1E-9
        except ValueError:
            pass

    def toggle_SEM(self):
        if self.checkBox_skipSEM.checkState() == 2:
            self.flag_skipSEM = True
        else:
            self.flag_skipSEM = False

    def get_scenepos(self,itemlist):
        pts = np.zeros((len(itemlist),2))
        for i, item in enumerate(itemlist):
            pts[i] = [item.scenePos().x(),item.scenePos().y()]
        return pts

    def create_mask(self):

        if self.nX and self.cfPxSize and self.lmThickness and self.fibParam and self.scene_fib.ellipseitem and (self.flag_skipSEM or (self.semParam and self.scene_sem.polygon.size() > 2 and self.scene_sem.ellipseitem_interior)):

            # Determine lamella plane from IB image
            pts = self.get_scenepos([self.scene_fib.ellipseitem])
            IBnorm, IBpt = find_IB_plane(pts,self.fibParam)

            if not self.flag_skipSEM:
                # Determine lamella boundary points from EB image
                pts = [ [pt.x(), pt.y()] for pt in self.scene_sem.polygon ]
                EBcnrs = find_EB_points_on_plane(pts,self.semParam,IBnorm,IBpt)
                # Choose interior point for filling
                pts = self.get_scenepos([self.scene_sem.ellipseitem_interior])
                EBpt = find_EB_points_on_plane(pts,self.semParam,IBnorm,IBpt)[0]
            else:
                EBcnrs = None
                EBpt = None

            # Draw lamella of a given thickness
            lmVol = drawLamella(self.nX,self.nY,self.nZ,self.cfPxSize,self.lmThickness,IBnorm,IBpt,EBcnrs,EBpt)

            # Write mask
            savepath = os.path.normpath(os.path.join(self.workdir,'.'.join(os.path.basename(self.cfFile).split('.')[0:-1])+'_mask.tif'))
            tifffile.imwrite(savepath,lmVol,photometric='minisblack',compress=0)
            self.statusbar.showMessage('Mask written to file: '+savepath)
            print('Mask written to file: '+savepath)

        elif not self.fibParam:
            self.statusbar.showMessage('FIB correlation: undefined',5000)
        elif not self.scene_fib.ellipseitem:
            self.statusbar.showMessage('FIB image: lamella front not defined',5000)
        elif not self.flag_skipSEM:
            if not self.semParam:
                self.statusbar.showMessage('SEM correlation: undefined',5000)
            elif self.scene_sem.polygon.size() <= 2:            
                self.statusbar.showMessage('SEM image: lamella outline not defined',5000)
            elif not self.scene_sem.ellipseitem_interior:
                self.statusbar.showMessage('SEM image: interior point not defined',5000)


class QMainWindowCustom(QtWidgets.QMainWindow):
    def __init__(self,parent=None,fibFile=None,fibparamFile=None,semFile=None,semparamFile=None,lmThickness=None,cfPxSize=None,cfFile=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow(fibFile,fibparamFile,semFile,semparamFile,lmThickness,cfPxSize,cfFile)
        self.ui.setupUi(self)  # method contains MainWindow.show(), QtWidgets.QGraphicsView.fitInView() requires visible window

### Base functions ###

def find_IB_plane(pts,param):
    IBnorm = rotate(param.phi,param.theta,param.psi).T @ [0,1,0,1]  # normal to lamella plane in confocal space
    IBnorm = IBnorm[:-1]
    m_inv = corr_transform(param.s,param.tx,param.ty,param.tz,param.phi,param.theta,param.psi)[1]
    IBpt = m_inv @ np.array([pts[0][0], pts[0][1], 0, 1])  # point on plane in confocal coordinates
    IBpt = IBpt[:-1]
    return IBnorm, IBpt

def find_EB_points_on_plane(pts,param,plnNorm,plnPt):
    EBvec = rotate(param.phi,param.theta,param.psi).T @ [0,0,-1,1]  # unit vector along view in confocal space
    EBvec = EBvec[:-1]
    m_inv = corr_transform(param.s,param.tx,param.ty,param.tz,param.phi,param.theta,param.psi)[1]
    EBpts = []
    for pt in pts:
        transPt = m_inv @ np.array([pt[0], pt[1], 0, 1])  # point on line in confocal space
        transPt = transPt[:-1]
        EBpts.append(np.dot((plnPt-transPt),plnNorm)/np.dot(EBvec,plnNorm) * EBvec + transPt)  # intersection of line and plane
    return EBpts

def drawLamella(nX,nY,nZ,pxSize,lmThickness,plnNorm,plnPt,EBcnrs,EBpt):

    # Initialize volume
    lmVol = np.zeros([nZ,nY,nX],np.uint8)

    # Create projection of lamella in fluorescence XY plane
    lmProj = np.zeros([nY,nX],np.uint8)
    if EBcnrs is not None:
        # Draw contour of lamella
        EBcnrs = [x.astype(int) for x in EBcnrs]
        for pt1, pt2 in zip(EBcnrs,EBcnrs[1:]):
            lmProj = cv2.line(lmProj, tuple(pt1[:-1]), tuple(pt2[:-1]), 255, 1)
        # Fill projection
        cv2.floodFill(lmProj,np.zeros([nY+2,nX+2],np.uint8),tuple(EBpt.astype(int)[:-1]),255)
    else:
        lmProj = lmProj + 255  # whole XY in the absence of SEM masking

    # Indices of voxels on lamella plane
    y,x = np.nonzero(lmProj)
    z = (np.dot(plnNorm,plnPt) - plnNorm[0]*x - plnNorm[1]*y)/plnNorm[2] # find z on lamella plane

    # Indices walking from plane half a unit vector at a time, calculate with preallocated arrays
    ind = np.vstack([z,y,x]).T
    half_range = lmThickness/pxSize/2
    steps = np.append(np.arange(0.5,half_range,0.5),half_range)
    increments = np.repeat(np.array([plnNorm[[2,1,0]]]),len(ind)*len(steps),0) * np.tile(steps,[3,len(ind)]).T
    ind = np.vstack([ind, np.repeat(ind,len(steps),0) - increments, np.repeat(ind,len(steps),0) + increments])
    ind = np.unique(ind.astype(int),axis=0)  # floor and find unique indices
    ind = ind[(ind[:,0]>=0) & (ind[:,0]<nZ) & (ind[:,1]>=0) & (ind[:,1]<nY) & (ind[:,2]>=0) & (ind[:,2]<nX),:].T  # remove indices out of bounds and transpose for coloring in

    # Color in by indices
    lmVol[ind[0],ind[1],ind[2]] = 1

    return lmVol

### Wrapper function ###

def create_mask_GUI(fibFile=None,fibparamFile=None,semFile=None,semparamFile=None,lmThickness=None,cfPxSize=None,cfFile=None,parentWidget=None):
    MainWindow = QMainWindowCustom(parentWidget,fibFile,fibparamFile,semFile,semparamFile,lmThickness,cfPxSize,cfFile)
    return MainWindow

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create mask to fluorescence volume based on FIB and SEM images')
    parser.add_argument('--fib', dest='fibFile', metavar='FILE', help='FIB image to be correlated')
    parser.add_argument('--fcorr', dest='fibparamFile', metavar='FILE', help='3DCT text output for the SEM image')
    parser.add_argument('--sem', dest='semFile', metavar='FILE', help='SEM image used for correlation')
    parser.add_argument('--scorr', dest='semparamFile', metavar='FILE', help='3DCT text output for the SEM image')
    parser.add_argument('--thickness', dest='lmThickness', type=float, default=200, metavar='NUMBER', help='lamella thickness in nm',)
    parser.add_argument('--px', dest='cfPxSize', type=float, metavar='NUMBER', help='pixel size of fluorescence volume in nm')
    parser.add_argument('--fluo', dest='cfFile', metavar='FILE', help='reference fluorescence volume for output dimensions')

    args = parser.parse_args()
    
    if args.semFile is not None:
        semFile = os.path.abspath(args.semFile)
    if args.fibFile is not None:
        args.fibFile = os.path.abspath(args.fibFile)
    if args.semparamFile is not None:
        args.semparamFile = os.path.abspath(args.semparamFile)
    if args.fibparamFile is not None:
        args.fibparamFile = os.path.abspath(args.fibparamFile)
    if args.cfFile is not None:
        args.cfFile = os.path.abspath(args.cfFile)

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = create_mask_GUI(args.fibFile,args.fibparamFile,args.semFile,args.semparamFile,args.lmThickness,args.cfPxSize,args.cfFile)
    sys.exit(app.exec_())

    # python3 create_mask.py --sem ../../tests/EB_038.tif --fcorr ../../tests/FIB_after_2019-01-24_17-31-19_correlation.txt --fib ../../tests/IB_012.tif --scorr ../../tests/SEM_after_2019-01-24_16-37-23_correlation.txt --thickness 300 --px 110 --fluo ../../tests/Project_S5_ch01_resliced.tif 