#!/usr/bin/env python3

'''Predict fiducial positions in the FIB image based on geometry

Call GUI via wrapper function predict_FIB_GUI or from command line.
Run 'python3 predict_FIB.py --help' command line usage information.

The following steps are taken to calculate the coordinates:
(1) User defines center of rotation in FIB image
(2) Find plane closest to all correlated points (fiducials and points of interest) in 3D
(3) Find user-defined center on this plane and rotate 52 degrees in X about this point
(4) Shift points to user-defined center in SEM image

Predicted coordinates are written out in CSV file for import into 3DCT.
Option to pre-load images and 3DCT paramter file in command-line

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
import csv

import argparse
import sys, os

from tools3dct.core import Param3D, QGraphicsSceneCustom, rotate, translate, scale
from tools3dct import docs

from PyQt5 import QtCore, QtGui, QtWidgets

class _QGraphicsSceneCustom(QGraphicsSceneCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pen = QtGui.QPen(QtGui.QColor(249,106,80))
        self.brush = QtGui.QBrush(QtGui.QColor(249,106,80))
        self.markerSize = 3
        self.ellipseitem = None
        self.ellipseitemlist = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            self.x = event.scenePos().x()
            self.y = event.scenePos().y()
            if self.ellipseitem is not None:
                self.removeItem(self.ellipseitem)
            self.ellipseitem = self.addEllipse(-self.markerSize, -self.markerSize, self.markerSize * 2, self.markerSize * 2, self.pen, self.brush)
            self.ellipseitem.setPos(self.x,self.y)
            self.ellipseitem.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        elif event.button() == QtCore.Qt.LeftButton and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            self.parent().setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        else:
            super(_QGraphicsSceneCustom,self).mousePressEvent(event)

# Form implementation generated from reading ui file 'predict_FIB.ui'
# Created by: PyQt5 UI code generator 5.13.2
class Ui_MainWindow(object):
    def __init__(self,paramFile=None,semFile=None,fibFile=None):
        self.paramFile = paramFile
        self.semFile = semFile
        self.fibFile = fibFile
        self.semPxSize = None
        self.fibPxSize = None
        self.angleRot = 52
        self.workdir = os.getcwd()
        self.markerSize = 3
        self.beadPen = QtGui.QPen(QtGui.QColor(127,231,229))
        self.beadBrush = QtGui.QBrush(QtGui.QColor(127,231,229))
        self.flag_param = False
        self.flag_calculated = False

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(958, 462)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_1.setObjectName("horizontalLayout_1")
        self.graphicsView_SEM = QtWidgets.QGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView_SEM.sizePolicy().hasHeightForWidth())
        self.graphicsView_SEM.setSizePolicy(sizePolicy)
        self.graphicsView_SEM.setMinimumSize(QtCore.QSize(461, 308))
        self.graphicsView_SEM.setObjectName("graphicsView_SEM")
        self.graphicsView_SEM.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView_SEM.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalLayout_1.addWidget(self.graphicsView_SEM)
        self.graphicsView_FIB = QtWidgets.QGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView_FIB.sizePolicy().hasHeightForWidth())
        self.graphicsView_FIB.setSizePolicy(sizePolicy)
        self.graphicsView_FIB.setMinimumSize(QtCore.QSize(461, 308))
        self.graphicsView_FIB.setObjectName("graphicsView_FIB")
        self.graphicsView_FIB.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView_FIB.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalLayout_1.addWidget(self.graphicsView_FIB)
        self.verticalLayout.addLayout(self.horizontalLayout_1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_SEMimage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_SEMimage.setObjectName("pushButton_SEMimage")
        self.horizontalLayout_2.addWidget(self.pushButton_SEMimage)
        self.pushButton_SEMparam = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_SEMparam.setObjectName("pushButton_SEMparam")
        self.horizontalLayout_2.addWidget(self.pushButton_SEMparam)
        self.pushButton_FIBimage = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_FIBimage.setObjectName("pushButton_FIBimage")
        self.horizontalLayout_2.addWidget(self.pushButton_FIBimage)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_SEM = QtWidgets.QLabel(self.centralwidget)
        self.label_SEM.setObjectName("label_SEM")
        self.horizontalLayout_3.addWidget(self.label_SEM)
        self.lineEdit_SEM = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_SEM.sizePolicy().hasHeightForWidth())
        self.lineEdit_SEM.setSizePolicy(sizePolicy)
        self.lineEdit_SEM.setMaximumSize(QtCore.QSize(40, 16777215))
        self.lineEdit_SEM.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_SEM.setObjectName("lineEdit_SEM")
        self.horizontalLayout_3.addWidget(self.lineEdit_SEM)
        self.label_FIB = QtWidgets.QLabel(self.centralwidget)
        self.label_FIB.setObjectName("label_FIB")
        self.horizontalLayout_3.addWidget(self.label_FIB)
        self.lineEdit_FIB = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_FIB.sizePolicy().hasHeightForWidth())
        self.lineEdit_FIB.setSizePolicy(sizePolicy)
        self.lineEdit_FIB.setMinimumSize(QtCore.QSize(0, 0))
        self.lineEdit_FIB.setMaximumSize(QtCore.QSize(40, 16777215))
        self.lineEdit_FIB.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_FIB.setObjectName("lineEdit_FIB")
        self.horizontalLayout_3.addWidget(self.lineEdit_FIB)
        self.label_angle = QtWidgets.QLabel(self.centralwidget)
        self.label_angle.setObjectName("label_angle")
        self.horizontalLayout_3.addWidget(self.label_angle)
        self.lineEdit_angle = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_angle.sizePolicy().hasHeightForWidth())
        self.lineEdit_angle.setSizePolicy(sizePolicy)
        self.lineEdit_angle.setMaximumSize(QtCore.QSize(40, 16777215))
        self.lineEdit_angle.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_angle.setObjectName("lineEdit_angle")
        self.horizontalLayout_3.addWidget(self.lineEdit_angle)
        self.pushButton_calculate = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_calculate.setObjectName("pushButton_calculate")
        self.horizontalLayout_3.addWidget(self.pushButton_calculate)
        self.pushButton_export = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_export.setObjectName("pushButton_export")
        self.horizontalLayout_3.addWidget(self.pushButton_export)
        self.checkBox_togglePoints = QtWidgets.QCheckBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_togglePoints.sizePolicy().hasHeightForWidth())
        self.checkBox_togglePoints.setSizePolicy(sizePolicy)
        self.checkBox_togglePoints.setObjectName("checkBox_togglePoints")
        self.horizontalLayout_3.addWidget(self.checkBox_togglePoints)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setNativeMenuBar(False)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 958, 22))
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

        self.scene_sem = _QGraphicsSceneCustom(self.graphicsView_SEM)
        self.scene_fib = _QGraphicsSceneCustom(self.graphicsView_FIB)
        self.pixmapitem_sem = self.scene_sem.addPixmap(QtGui.QPixmap())
        self.pixmapitem_fib = self.scene_fib.addPixmap(QtGui.QPixmap())
        self.graphicsView_SEM.setScene(self.scene_sem)
        self.graphicsView_FIB.setScene(self.scene_fib)
        self.scene_sem.ellipseitemlist = []
        self.scene_fib.ellipseitemlist = []

        self.actionDocumentation.triggered.connect(self.helpdoc.predictFIB)        
        self.pushButton_SEMimage.clicked.connect(self.choose_SEM_image)
        self.pushButton_FIBimage.clicked.connect(self.choose_FIB_image)
        self.pushButton_SEMparam.clicked.connect(self.choose_SEM_param)
        self.lineEdit_SEM.textChanged.connect(self.update_SEM_pixel_size)
        self.lineEdit_FIB.textChanged.connect(self.update_FIB_pixel_size)
        self.lineEdit_angle.textChanged.connect(self.update_angle)
        self.pushButton_calculate.clicked.connect(self.predict_points)
        self.pushButton_export.clicked.connect(self.export_points)
        self.checkBox_togglePoints.clicked.connect(self.toggle_points)

        MainWindow.show()
        if self.semFile is not None:
            self.load_SEM_image()
        if self.paramFile is not None:
            self.load_SEM_param()
        if self.fibFile is not None:
            self.load_FIB_image()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SEM -> FIB"))
        self.pushButton_SEMimage.setText(_translate("MainWindow", "Load SEM Image"))
        self.pushButton_SEMparam.setText(_translate("MainWindow", "Load SEM Parameters"))
        self.pushButton_FIBimage.setText(_translate("MainWindow", "Load FIB Image"))
        self.label_SEM.setText(_translate("MainWindow", "SEM Image, Pixel Size (nm)"))
        self.label_FIB.setText(_translate("MainWindow", "FIB Image, Pixel Size (nm)"))
        self.label_angle.setText(_translate("MainWindow", "Angle of Rotation (°)"))
        self.lineEdit_angle.setText(_translate("MainWindow", "+52"))
        self.pushButton_calculate.setText(_translate("MainWindow", "Calculate"))
        self.pushButton_export.setText(_translate("MainWindow", "Export Points"))
        self.checkBox_togglePoints.setText(_translate("MainWindow", "Show/Hide"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionDocumentation.setText(_translate("MainWindow", "Documentation"))

    def choose_SEM_image(self):
        self.semFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select an SEM image', self.workdir,'Image Files (*.tif *.tiff);; All (*.*)')[0]
        self.load_SEM_image()
    
    def choose_FIB_image(self):
        self.fibFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select a FIB image', self.workdir,'Image Files (*.tif *.tiff);; All (*.*)')[0]
        self.load_FIB_image()

    def choose_SEM_param(self):
        self.paramFile = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow,'Select 3DCT text output for the SEM image', self.workdir,'Text File (*.txt);; All (*.*)')[0]
        self.load_SEM_param()

    def load_SEM_image(self):
        if self.semFile is not None:
            try:
                with tifffile.TiffFile(self.semFile) as tif:
                    try:
                        self.semPxSize = tif.pages[0].tags['FEI_HELIOS'].value['Scan']['PixelWidth']
                        self.lineEdit_SEM.setText(f'{self.semPxSize*1E9:.1f}')
                    except KeyError:
                        self.statusbar.showMessage('SEM image: Pixel size not found',5000)
                self.workdir = os.path.dirname(self.semFile)
                self.pixmapitem_sem.setPixmap(QtGui.QPixmap(self.semFile))
                self.graphicsView_SEM.setSceneRect(self.scene_sem.sceneRect())
                self.graphicsView_SEM.fitInView(self.graphicsView_SEM.sceneRect(),QtCore.Qt.KeepAspectRatio)
            except (PermissionError,FileNotFoundError,IsADirectoryError,ValueError,tifffile.tifffile.TiffFileError):
                pass
        
    def load_SEM_param(self):
        try:
            self.param = Param3D(self.paramFile)
            if self.param.bxx.size == 0:
                self.statusbar.showMessage('Cannot extract parameters',5000)
            else:
                self.statusbar.showMessage('Parameters extracted',5000)
                self.flag_param = True
                for item in self.scene_sem.ellipseitemlist:
                    self.scene_sem.removeItem(item)
                self.scene_sem.ellipseitemlist.clear()
                for pt in zip(self.param.bxx,self.param.byy):
                    ellipseitem = self.scene_sem.addEllipse(-self.markerSize, -self.markerSize, self.markerSize * 2, self.markerSize * 2, self.beadPen, self.beadBrush)
                    ellipseitem.setPos(pt[0],pt[1])
                    ellipseitem.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
                    self.scene_sem.ellipseitemlist.append(ellipseitem)
        except (PermissionError,FileNotFoundError,IsADirectoryError,UnicodeDecodeError):
            pass
        
    def load_FIB_image(self):
        if self.fibFile is not None:
            try:
                with tifffile.TiffFile(self.fibFile) as tif:
                    try:
                        self.fibPxSize = tif.pages[0].tags['FEI_HELIOS'].value['Scan']['PixelWidth']
                        self.lineEdit_FIB.setText(f'{self.fibPxSize*1E9:.1f}')
                    except KeyError:
                        self.statusbar.showMessage('FIB image: Pixel size not found',5000)
                self.workdir = os.path.dirname(self.fibFile)
                self.pixmapitem_fib.setPixmap(QtGui.QPixmap(self.fibFile))
                self.graphicsView_FIB.setSceneRect(self.scene_fib.sceneRect())
                self.graphicsView_FIB.fitInView(self.graphicsView_FIB.sceneRect(),QtCore.Qt.KeepAspectRatio)
            except (PermissionError,FileNotFoundError,IsADirectoryError,ValueError,tifffile.tifffile.TiffFileError):
                pass

    def update_SEM_pixel_size(self):
        try:
            self.semPxSize = float(self.lineEdit_SEM.text()) * 1E-9
        except ValueError:
            pass

    def update_FIB_pixel_size(self):
        try:
            self.fibPxSize = float(self.lineEdit_FIB.text()) * 1E-9
        except ValueError:
            pass

    def update_angle(self):
        try:
            self.angleRot = float(self.lineEdit_angle.text())
        except ValueError:
            pass

    def predict_points(self):

        if self.scene_sem.ellipseitem and self.scene_fib.ellipseitem and self.flag_param and (self.param.bxx.size != 0) and isinstance(self.semPxSize,float) and isinstance(self.fibPxSize,float):

            # Closest plane of the form ax+by+c=z, overdetermined system Ax=B, solve for x
            xx = np.hstack([self.param.xx,self.param.bxx])
            yy = np.hstack([self.param.yy,self.param.byy])
            zz = np.hstack([self.param.zz,self.param.bzz])
            A = np.vstack((xx,yy,np.ones(xx.size))).T
            B = zz.T
            try:
                x = np.linalg.lstsq(A,B,rcond=None)[0]  # least squares solution by SVD decomposition
            except np.linalg.LinAlgError:
                x = np.linalg.lstsq(A,B,rcond=None)[0]  # function fails the first time occasionally after Windows 10 2004 update

            # User-defined center of rotation and equivalent point in FIB image
            rot_center_x = self.scene_sem.x
            rot_center_y = self.scene_sem.y
            rot_center = [rot_center_x, rot_center_y, x[0] * rot_center_x + x[1] * rot_center_y + x[2]]

            # Tranformation matrices
            tr1 = translate(-rot_center[0],-rot_center[1],-rot_center[2])
            rot = rotate(0,self.angleRot/180*np.pi,0)
            sca = scale(self.semPxSize/self.fibPxSize)
            tr2 = translate(self.scene_fib.x,self.scene_fib.y,0)

            # Transform and set z to 0
            pts = tr2 @ sca @ rot @ tr1 @ np.vstack((self.param.bxx,self.param.byy,self.param.bzz,np.ones(self.param.bxx.size)))
            pts[2,:] = 0

            fib_pts = pts[:-1,:].T
            self.flag_calculated = True

            # Add points to scene
            for item in self.scene_fib.ellipseitemlist:
                self.scene_fib.removeItem(item)
            self.scene_fib.ellipseitemlist.clear()
            for pt in fib_pts:
                ellipseitem = self.scene_fib.addEllipse(-self.markerSize, -self.markerSize, self.markerSize * 2, self.markerSize * 2, self.beadPen, self.beadBrush)
                ellipseitem.setPos(pt[0],pt[1])
                ellipseitem.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
                ellipseitem.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
                self.scene_fib.ellipseitemlist.append(ellipseitem)
            self.checkBox_togglePoints.setCheckState(2)

        elif not self.scene_sem.ellipseitem:            
            self.statusbar.showMessage('Center of rotation missing for SEM image',5000)
        elif not self.scene_fib.ellipseitem:
            self.statusbar.showMessage('Center of rotation missing for FIB image',5000)
        elif not self.flag_param:
            self.statusbar.showMessage('3DCT parameters for SEM image not loaded',5000)
        elif not isinstance(self.semPxSize,float):
            self.statusbar.showMessage('Pixel size missing for SEM image',5000)
        elif not isinstance(self.fibPxSize,float):
            self.statusbar.showMessage('Pixel size missing for FIB image',5000)

    def get_scenepos(self,itemlist):
        pts = np.zeros((len(itemlist),2))
        for i, item in enumerate(itemlist):
            pts[i] = [item.scenePos().x(),item.scenePos().y()]
        return pts
    
    def export_points(self):
        if self.flag_calculated:
            fib_pts = self.get_scenepos(self.scene_fib.ellipseitemlist)
            fib_pts = np.append(fib_pts, np.zeros((fib_pts.shape[0],1)), axis=1)
            outfile = os.path.normpath(os.path.join(self.workdir,'predictions.csv'))
            with open(outfile, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t')
                writer.writerows(fib_pts)
            self.statusbar.showMessage('Points written to: '+outfile)
            print('Points written to: '+outfile)

    def toggle_points(self):
        if self.flag_calculated:
            if self.checkBox_togglePoints.checkState() == 2:
                for item in self.scene_fib.ellipseitemlist:
                    item.setVisible(True)
            else:
                for item in self.scene_fib.ellipseitemlist:
                    item.setVisible(False)

# QMainWindow subclass to hold ui
class QMainWindowCustom(QtWidgets.QMainWindow):
    def __init__(self,parent=None,paramFile=None,semFile=None,fibFile=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow(paramFile,semFile,fibFile)
        self.ui.setupUi(self)  # method contains MainWindow.show(), QtWidgets.QGraphicsView.fitInView() requires visible window

def predict_FIB_GUI(paramFile=None,semFile=None,fibFile=None,parentWidget=None):
    MainWindow = QMainWindowCustom(parentWidget,paramFile,semFile,fibFile)
    return MainWindow

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Predict fiducial positions in the FIB image based on geometry')
    parser.add_argument('--corr', dest='paramFile', metavar='FILE', help='3DCT text output for the SEM image')
    parser.add_argument('--sem', dest='semFile', metavar='FILE', help='SEM image used for correlation')
    parser.add_argument('--fib', dest='fibFile', metavar='FILE', help='FIB image to be correlated')
    args = parser.parse_args()

    if args.paramFile is not None:
        args.paramFile = os.path.abspath(args.paramFile)
    if args.semFile is not None:
        semFile = os.path.abspath(args.semFile)
    if args.fibFile is not None:
        args.fibFile = os.path.abspath(args.fibFile)

    # QtWidgets.QApplication.setStyle('Fusion')
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = predict_FIB_GUI(args.paramFile,args.semFile,args.fibFile)
    sys.exit(app.exec_())

    # Suppress warning from TIFFReadDirectory library?