#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3D Correlation Toolbox - 3DCT

This Toolbox is build for 3D correlative microscopy. It helps with 3D to 2D correlation of three
dimensional confocal image stacks to two dimensional SEM/FIB dual beam microscope images.
But it is not limited to that.

The Toolbox comes with a PyQt4 GUI. Further dependencies as of now are:

	- PyQt4
	- numpy
	- scipy
	- matplotlib
	- cv2 (opencv)
	- tifffile (Christoph Gohlke)

A test dataset can be downloaded from the "testdata" folder:
	https://bitbucket.org/splo0sh/3dctv2/src/ab8914cf71aea77949bc5037ba090df42cfa3abc/testdata/?at=master

# @Title			: TDCT_main
# @Project			: 3DCTv2
# @Description		: 3D Correlation Toolbox - 3DCT
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Credits			: Vladan Lucic for the 3D to 2D correlation code
# 					: and the stackoverflow community for all the bits and pieces
# @Maintainer		: Jan Arnold
# 					  Max-Planck-Instute of Biochemistry
# 					  Department of Molecular Structural Biology
# @Date				: 2015/08
# @Version			: 3DCT 2.0.0
# @Status			: developement
# @Usage			: python -u TDCT_main.py
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================

import sys
import os
import tempfile
# from functools import partial
from subprocess import call
from PyQt4 import QtCore, QtGui, uic
from tdct import clrmsg, helpdoc, stackProcessing
import TDCT_correlation
# add working directory temporarily to PYTHONPATH
execdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(execdir)

__version__ = 'v2.0.0'

debug = True
########## GUI layout file #######################################################
##################################################################################
qtCreatorFile_main = os.path.join(execdir, "TDCT_main.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile_main)

########## Main Application Class ################################################
##################################################################################


class APP(QtGui.QMainWindow, Ui_MainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		# DEL self.stackProcessStatus.setVisible(False)
		self.menuDebug.menuAction().setVisible(False)
		# Menu, set shortcuts
		self.actionQuit.triggered.connect(self.close)
		self.actionQuit.setShortcuts(['Ctrl+Q','Esc'])
		self.actionQuit.setStatusTip('Exit application')
		self.helpdoc = helpdoc.help(self)

		QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_0), self, self.showDebugMenu)
		self.actionLoad_Test_Dataset.triggered.connect(self.loadTestDataset)

		self.actionAbout.triggered.connect(self.about)

		# Open Buttons
		self.toolButton_WorkingDirOpen.clicked.connect(lambda: self.openDirectoy(self.lineEdit_WorkingDirPath.text()))
		self.toolButton_ImageStackOpen.clicked.connect(lambda: self.openDirectoy(self.lineEdit_ImageStackPath.text()))
		self.toolButton_ImageSequenceOpen.clicked.connect(lambda: self.openDirectoy(self.lineEdit_ImageSequencePath.text()))
		self.toolButton_NormalizeOpen.clicked.connect(lambda: self.openDirectoy(self.lineEdit_NormalizePath.text()))
		self.toolButton_MipOpen.clicked.connect(lambda: self.openDirectoy(self.lineEdit_MipPath.text()))
		## Select Buttons
		self.toolButton_WorkingDirSelect.clicked.connect(lambda: self.selectPath(self.lineEdit_WorkingDirPath))
		self.toolButton_ImageStackSelect.clicked.connect(lambda: self.selectFile(self.lineEdit_ImageStackPath))
		self.toolButton_ImageSequenceSelect.clicked.connect(lambda: self.selectPath(self.lineEdit_ImageSequencePath))
		self.toolButton_NormalizeSelect.clicked.connect(lambda: self.selectFile(self.lineEdit_NormalizePath))
		self.toolButton_MipSelect.clicked.connect(lambda: self.selectFile(self.lineEdit_MipPath))
		self.toolButton_selectImage1.clicked.connect(self.selectImage1)
		self.toolButton_selectImage2.clicked.connect(self.selectImage2)
		## Command Buttons
		self.commandLinkButton_correlate.clicked.connect(self.runCorrelationModule)
		self.commandLinkButton_Reslice.clicked.connect(self.imageStack)
		self.commandLinkButton_CreateStackFile.clicked.connect(self.imageSequence)
		self.commandLinkButton_Normalize.clicked.connect(self.normalize)
		self.commandLinkButton_Mip.clicked.connect(self.mip)
		## Help Buttons
		self.toolButton_WorkingDirHelp.clicked.connect(self.helpdoc.WorkingDir)
		self.toolButton_ImageStackHelp.clicked.connect(self.helpdoc.ImageStack)
		self.toolButton_ImageSequenceHelp.clicked.connect(self.helpdoc.ImageSequence)
		self.toolButton_NormalizeHelp.clicked.connect(self.helpdoc.Normalize)
		self.toolButton_FileListHelp.clicked.connect(self.helpdoc.FileList)
		self.toolButton_MipHelp.clicked.connect(self.helpdoc.Mip)
		self.toolButton_CorrelationHelp.clicked.connect(self.helpdoc.Correlation)
		## Misc buttons
		self.toolButton_FileListReload.clicked.connect(self.reloadFileList)
		self.toolButton_ImageStackGetPixelSize.clicked.connect(self.getPixelSize)
		self.toolButton_ImageSequenceGetPixelSize.clicked.connect(self.getPixelSize)
		self.testButton.clicked.connect(self.tester)

		## QLineEdits
		self.lineEdit_WorkingDirPath.textChanged.connect(lambda: self.isValidPath(self.lineEdit_WorkingDirPath))
		self.lineEdit_ImageStackPath.textChanged.connect(lambda: self.isValidFile(self.lineEdit_ImageStackPath))
		self.lineEdit_ImageSequencePath.textChanged.connect(lambda: self.isValidPath(self.lineEdit_ImageSequencePath))
		self.lineEdit_NormalizePath.textChanged.connect(lambda: self.isValidFile(self.lineEdit_NormalizePath))
		self.lineEdit_MipPath.textChanged.connect(lambda: self.isValidFile(self.lineEdit_MipPath))
		self.lineEdit_selectImage1.textChanged.connect(lambda: self.isValidFile(self.lineEdit_selectImage1))
		self.lineEdit_selectImage2.textChanged.connect(lambda: self.isValidFile(self.lineEdit_selectImage2))

		## Progressbars
		self.progressBar_ImageStack.setVisible(False)
		self.progressBar_ImageSequence.setVisible(False)
		self.progressBar_Normalize.setVisible(False)
		self.progressBar_Mip.setVisible(False)

		# Checkbox
		# DEL self.checkBox_cubeVoxels.stateChanged.connect(lambda: self.cubeVoxelsState(self.checkBox_cubeVoxels.isChecked()))

		# Init Working directory
		self.workingdir = os.path.expanduser("~")
		self.lineEdit_WorkingDirPath.setText(self.workingdir)
		self.populate_filelist(self.workingdir)

	def printLOL(self):
		print 'LOL'

	def isValidFile(self,lineEdit):
		if lineEdit.text() == "":
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: white;} QLineEdit:hover{border: 1px solid grey; background-color white;}")
			lineEdit.fileIsValid = False
			lineEdit.fileIsTiff = False
		elif os.path.isfile(lineEdit.text()):
			if os.path.splitext(str(lineEdit.text()))[1] in ['.tif','.tiff']:
				lineEdit.setStyleSheet(
					"QLineEdit{background-color: rgb(0,255,0,80);}\
					QLineEdit:hover{border: 1px solid grey; background-color rgb(0,255,0,80);}")
				lineEdit.fileIsValid = True
				lineEdit.fileIsTiff = True
			else:
				lineEdit.setStyleSheet(
					"QLineEdit{background-color: rgb(255,120,0,80);}\
					QLineEdit:hover{border: 1px solid grey; background-color rgb(255,120,0,80);}")
				lineEdit.fileIsValid = True
				lineEdit.fileIsTiff = False
		else:
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: rgb(255,0,0,80);}\
				QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,80);}")
			lineEdit.fileIsValid = False
			lineEdit.fileIsTiff = False

	def isValidPath(self,lineEdit):
		if lineEdit.text() == "":
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: white;} QLineEdit:hover{border: 1px solid grey; background-color white;}")
			if lineEdit.objectName() == 'lineEdit_WorkingDirPath':
				self.listWidget_WorkingDir.clear()
		elif os.path.isdir(lineEdit.text()):
			if lineEdit.objectName() == 'lineEdit_WorkingDirPath':
				workingdir = self.checkDirectoryPrivileges(str(self.lineEdit_WorkingDirPath.text()))
				if workingdir:
					lineEdit.setStyleSheet(
						"QLineEdit{background-color: rgb(0,255,0,80);}\
						QLineEdit:hover{border: 1px solid grey; background-color rgb(0,255,0,80);}")
					self.workingdir = workingdir
					self.populate_filelist(self.workingdir)
					lineEdit.setText(self.workingdir)
				else:
					lineEdit.setStyleSheet(
						"QLineEdit{background-color: rgb(255,0,0,80);}\
						QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,80);}")
			else:
				lineEdit.setStyleSheet(
					"QLineEdit{background-color: rgb(0,255,0,80);}\
					QLineEdit:hover{border: 1px solid grey; background-color rgb(0,255,0,80);}")
		else:
			lineEdit.setStyleSheet(
				"QLineEdit{background-color: rgb(255,0,0,80);} QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,80);}")

	def focusInEvent(self, event):
		if debug is True: print clrmsg.DEBUG, 'Got focus'

		# List Widget Test
		# self.listWidget_coordEx_LMfiles.itemSelectionChanged.connect(self.dostuff)

	# def dostuff(self):
	# 	print self.listWidget_coordEx_LMfiles.itempath+"/"+self.listWidget_coordEx_LMfiles.selectedItems()[0].text()
	# 	print os.path.join(self.listWidget_coordEx_LMfiles.itempath, str(self.listWidget_coordEx_LMfiles.selectedItems()[0].text()))

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def showDebugMenu(self):
		self.menuDebug.menuAction().setVisible(True)
		self.loadTestDataset()

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def loadTestDataset(self):
		print 'nope'

	## only for quick load of test datasets - REMOVE FROM FINAL VERSION
	def tester(self):
		testpath = '/Users/jan/Desktop/'
		testpath = 'F:/jan_temp/'
		leftImage = testpath+'correlation_test_dataset/IB_030.tif'
		rightImage = testpath+'correlation_test_dataset/LM_green_reslized.tif'
		import TDCT_correlation
		self.correlationModul = TDCT_correlation.Main(leftImage=leftImage,rightImage=rightImage,nosplash=False,workingdir=self.workingdir)

	## About
	def about(self):
		QtGui.QMessageBox.about(
								self, "About 3DCT",
								"3D Correlation Toolbox v2.0.0\n\ndeveloped by:\n\nMax-Planck-Institute of Biochemistry\n\n" +
								"3D Correlation Toolbox:	Jan Arnold\nCorrelation Algorithm:	Vladan Lucic"
								)

	def checkDirectoryPrivileges(self,path,question="Do you want to select another directory?"):
		try:
			testfile = tempfile.TemporaryFile(dir=path)
			testfile.close()
			return path
		except Exception:
			reply = QtGui.QMessageBox.critical(
				self,"Warning",
				"I cannot write to the folder: {0}\n\nDo you want to select another directory?".format(path),
				QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
			pathValid = False
			if reply == QtGui.QMessageBox.Yes:
				while True:
					newpath = str(QtGui.QFileDialog.getExistingDirectory(self, "Select directory", path))
					if newpath != "":
						try:
							testfile = tempfile.TemporaryFile(dir=newpath)
							testfile.close()
							pathValid = True
							break
						except:
							reply = QtGui.QMessageBox.critical(
								self,"Warning",
								"I cannot write to the folder: {0}\n\n{1}".format(newpath,question),
								QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
							if reply == QtGui.QMessageBox.No:
								pathValid = False
								break
					else:
						pathValid = False
						break
			if pathValid is False:
				return None
			else:
				return newpath

	## Open directory
	def openDirectoy(self,path):
		if debug is True: print clrmsg.DEBUG, 'Passed path value:', path
		directory, file = os.path.split(str(path))
		if debug is True: print clrmsg.DEBUG, 'os split (directory, file):', directory, file
		if os.path.isdir(directory):
			if sys.platform == 'darwin':
				call(['open', '-R', directory])
			elif sys.platform == 'linux2':
				call(['gnome-open', '--', directory])
			elif sys.platform == 'win32':
				call(['explorer', directory])

	## Exit Warning
	def closeEvent(self, event):
		quit_msg = "Are you sure you want to exit the\n3D Correlation Toolbox?\n\nUnsaved data will be lost!"
		reply = QtGui.QMessageBox.question(self, 'Message', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
		if reply == QtGui.QMessageBox.Yes:
			# if loaded, close pointselection tool widget and sub windows
			if hasattr(self, "correlationModul"):
				if hasattr(self.correlationModul, "widget"):
					exitstatus = self.correlationModul.close()
					if exitstatus == 1:
						event.ignore()
					else:
						event.accept()
		else:
			event.ignore()

	def selectPath(self, pathLine):
		sender = self.sender()
		path = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", self.workingdir))
		if path:
			if sender == self.toolButton_WorkingDirSelect:
				workingdir = self.checkDirectoryPrivileges(path)
				if workingdir:
					self.workingdir = workingdir
					self.populate_filelist(self.workingdir)
					pathLine.setText(self.workingdir)
			else:
				pathLine.setText(path)

	def selectFile(self, pathLine):
		path = str(QtGui.QFileDialog.getOpenFileName(
			None,"Select tiff image file", self.workingdir,"Image Files (*.tif *.tiff);; All (*.*)"))
		if path:
			pathLine.setText(path)

	def getPixelSize(self):
		sender = self.sender()
		if sender == self.toolButton_ImageStackGetPixelSize:
			try:
				pixelSize = stackProcessing.pxSize(str(self.lineEdit_ImageStackPath.text()))
				if debug is True: print clrmsg.DEBUG, pixelSize
				if pixelSize:
					self.doubleSpinBox_ImageStackFocusStepSizeOrig.setValue(pixelSize*1000)
					self.doubleSpinBox_ImageStackFocusStepSizeReslized.setValue(pixelSize*1000)
				else:
					raise Exception('No pixel size information found!')
			except Exception as e:
				QtGui.QMessageBox.warning(
						self,"Warning",
						"Unable to extract pixel size.\n\n{0}".format(e))
		elif sender == self.toolButton_ImageSequenceGetPixelSize:
			try:
				pixelSize = stackProcessing.pxSize(os.path.join(str(self.lineEdit_ImageSequencePath.text()),"Tile_001-001-000_0-000.tif"))
				if debug is True: print clrmsg.DEBUG, pixelSize
				if pixelSize:
					self.doubleSpinBox_ImageSequenceFocusStepSizeOrig.setValue(pixelSize*1000)
					self.doubleSpinBox_ImageSequenceFocusStepSizeReslized.setValue(pixelSize*1000)
				else:
					raise Exception('No pixel size information found!')
			except Exception as e:
				QtGui.QMessageBox.warning(
						self,"Warning",
						"Unable to extract pixel size.\n\n{0}".format(e))

	## Cube Voxels button state handling
	def cubeVoxelsState(self, checkstate):
		if checkstate is True:
			self.doubleSpinBox_focusStepsize.setEnabled(True)
			self.radioButton_20x.setEnabled(True)
			self.radioButton_40x.setEnabled(True)
			self.radioButton_63x.setEnabled(True)
			self.radioButton_customFocusStepsize.setEnabled(True)
			self.doubleSpinBox_customFocusStepsize.setEnabled(True)

		else:
			self.doubleSpinBox_focusStepsize.setEnabled(False)
			self.radioButton_20x.setEnabled(False)
			self.radioButton_40x.setEnabled(False)
			self.radioButton_63x.setEnabled(False)
			self.radioButton_customFocusStepsize.setEnabled(False)
			self.doubleSpinBox_customFocusStepsize.setEnabled(False)

	## Populate List widget for listing files needed for coordinate extraction
	def populate_filelist(self,path):
		self.listWidget_WorkingDir.clear()
		self.listWidget_WorkingDir.itempath = path
		for fname in os.listdir(path):
			checkdir = os.path.join(path, fname)
			if (
				os.path.isdir(checkdir) is False and
				fname.startswith(".") is False and
				fname.startswith("$") is False
				):
				item = QtGui.QListWidgetItem()
				item.setText(fname)
				# item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
				# item.setCheckState(QtCore.Qt.Unchecked)
				self.listWidget_WorkingDir.addItem(item)

	def reloadFileList(self):
		if hasattr(self, "workingdir"):
			self.populate_filelist(self.workingdir)
			if debug is True: print clrmsg.DEBUG, 'Working directory file list reloaded'

	def selectImage1(self):
		self.lineEdit_selectImage1.setText(
			os.path.join(self.listWidget_WorkingDir.itempath, str(self.listWidget_WorkingDir.selectedItems()[0].text())))

	def selectImage2(self):
		self.lineEdit_selectImage2.setText(
			os.path.join(self.listWidget_WorkingDir.itempath, str(self.listWidget_WorkingDir.selectedItems()[0].text())))

	def runCorrelationModule(self):
		if self.lineEdit_selectImage1.text() != "" and self.lineEdit_selectImage2.text() != "":
			if self.lineEdit_selectImage1.fileIsTiff is True and self.lineEdit_selectImage2.fileIsTiff is True:
				self.correlationModul = TDCT_correlation.Main(
					leftImage=str(self.lineEdit_selectImage1.text()),
					rightImage=str(self.lineEdit_selectImage2.text()),
					nosplash=False,
					workingdir=self.workingdir)
			else:
				if self.lineEdit_selectImage1.fileIsValid is False or self.lineEdit_selectImage2.fileIsValid is False:
					QtGui.QMessageBox.warning(
						self,"Warning",
						"Invalid file path detected. Please check the file paths.")
				elif self.lineEdit_selectImage1.fileIsTiff is False or self.lineEdit_selectImage2.fileIsTiff is False:
					QtGui.QMessageBox.warning(
						self,"Warning",
						"Only *.tif and *.tiff files are supported at the moment")
		else:
			if self.lineEdit_selectImage1.text() == "":
				self.lineEdit_selectImage1.setStyleSheet(
					"QLineEdit{background-color: rgb(255,0,0,80);}\
					QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,80);}")
			if self.lineEdit_selectImage2.text() == "":
				self.lineEdit_selectImage2.setStyleSheet(
					"QLineEdit{background-color: rgb(255,0,0,80);}\
					QLineEdit:hover{border: 1px solid grey; background-color rgb(255,0,0,80);}")

	def imageStack(self):
		self.progressBar_ImageStack.setVisible(True)
		self.progressBar_ImageStack.setMaximum(0)
		QtGui.QApplication.processEvents()
		img_path = str(self.lineEdit_ImageStackPath.text())
		customSaveDir = self.checkDirectoryPrivileges(os.path.split(img_path)[0],question="Do you want me to save the data to another directory?")
		if img_path and self.lineEdit_ImageStackPath.fileIsTiff is True and customSaveDir:
			ss_in = self.doubleSpinBox_ImageStackFocusStepSizeOrig.value()
			ss_out = self.doubleSpinBox_ImageStackFocusStepSizeReslized.value()
			if debug is True: print clrmsg.DEBUG, img_path, ss_in, ss_out, customSaveDir
			self.progressBar_ImageStack.setMaximum(100)
			QtGui.QApplication.processEvents()
			stackProcessing.main(
				img_path, ss_in, ss_out, qtprocessbar=self.progressBar_ImageStack,
				interpolationmethod='linear', saveorigstack=False, showgraph=False, customSaveDir=customSaveDir)
			self.progressBar_ImageStack.reset()
			self.progressBar_ImageStack.setVisible(False)
		else:
			self.progressBar_ImageStack.setMaximum(100)
			self.progressBar_ImageStack.reset()
			self.progressBar_ImageStack.setVisible(False)

	def imageSequence(self):
		self.progressBar_ImageSequence.setVisible(True)
		self.progressBar_ImageSequence.setMaximum(0)
		QtGui.QApplication.processEvents()
		dirPath = str(self.lineEdit_ImageSequencePath.text())
		customSaveDir = self.checkDirectoryPrivileges(dirPath,question="Do you want me to save the data to another directory?")
		if os.path.isdir(dirPath) and customSaveDir:
			if self.checkBox_ImageSequenceCube.isChecked():
				ss_in = self.doubleSpinBox_ImageSequenceFocusStepSizeOrig.value()
				ss_out = self.doubleSpinBox_ImageSequenceFocusStepSizeReslized.value()
				if debug is True: print clrmsg.DEBUG, dirPath, ss_in, ss_out, str(self.checkBox_ImageSequenceSaveOrigStack.isChecked()), customSaveDir
				self.progressBar_ImageSequence.setMaximum(100)
				QtGui.QApplication.processEvents()
				stackProcessing.main(
					dirPath, ss_in, ss_out, qtprocessbar=self.progressBar_ImageSequence, interpolationmethod='linear',
					saveorigstack=self.checkBox_ImageSequenceSaveOrigStack.isChecked(), showgraph=False, customSaveDir=customSaveDir)
				self.progressBar_ImageSequence.reset()
			else:
				if debug is True: print clrmsg.DEBUG, 'no reslicing'
				self.progressBar_ImageSequence.setMaximum(100)
				QtGui.QApplication.processEvents()
				stackProcessing.main(dirPath, 0, 0, qtprocessbar=self.progressBar_ImageSequence, saveorigstack=True, interpolationmethod='none', customSaveDir=customSaveDir)
				self.progressBar_ImageSequence.reset()
				self.progressBar_ImageSequence.setVisible(False)
		else:
			self.progressBar_ImageSequence.setMaximum(100)
			self.progressBar_ImageSequence.reset()
			self.progressBar_ImageSequence.setVisible(False)

	def normalize(self):
		self.progressBar_Normalize.setVisible(True)
		self.progressBar_Normalize.setMaximum(0)
		QtGui.QApplication.processEvents()
		img_path = str(self.lineEdit_NormalizePath.text())
		customSaveDir = self.checkDirectoryPrivileges(os.path.split(img_path)[0],question="Do you want me to save the data to another directory?")
		if img_path and self.lineEdit_NormalizePath.fileIsTiff is True and customSaveDir:
			if debug is True: print clrmsg.DEBUG, 'In/out:', img_path, customSaveDir
			self.progressBar_Normalize.setMaximum(100)
			QtGui.QApplication.processEvents()
			stackProcessing.normalize(img_path, qtprocessbar=self.progressBar_Normalize, customSaveDir=customSaveDir)
			self.progressBar_Normalize.reset()
			self.progressBar_Normalize.setVisible(False)
		else:
			self.progressBar_Normalize.setMaximum(100)
			self.progressBar_Normalize.reset()
			self.progressBar_Normalize.setVisible(False)

	def mip(self):
		self.progressBar_Mip.setVisible(True)
		self.progressBar_Mip.setMaximum(0)
		QtGui.QApplication.processEvents()
		img_path = str(self.lineEdit_MipPath.text())
		customSaveDir = self.checkDirectoryPrivileges(os.path.split(img_path)[0],question="Do you want me to save the data to another directory?")
		if img_path and self.lineEdit_MipPath.fileIsTiff is True and customSaveDir:
			if debug is True: print clrmsg.DEBUG, 'In/out/normalize:', img_path, customSaveDir, self.checkBox_MipNormalize.isChecked()
			self.progressBar_Mip.setMaximum(100)
			QtGui.QApplication.processEvents()
			stackProcessing.mip(img_path, qtprocessbar=self.progressBar_Mip, customSaveDir=customSaveDir, normalize=self.checkBox_MipNormalize.isChecked())
			self.progressBar_Mip.reset()
			self.progressBar_Mip.setVisible(False)
		else:
			self.progressBar_Mip.setMaximum(100)
			self.progressBar_Mip.reset()
			self.progressBar_Mip.setVisible(False)


## Class to outsource work to an independant thread. Not used anymore at the moment.
class GenericThread(QtCore.QThread):
	def __init__(self, function, *args, **kwargs):
		QtCore.QThread.__init__(self)
		self.function = function
		self.args = args
		self.kwargs = kwargs

	def __del__(self):
		self.wait()

	def run(self):
		self.function(*self.args,**self.kwargs)
		return


if debug is True: print clrmsg.DEBUG, 'Debug Test'
if debug is True: print clrmsg.OK + 'OK Test'
if debug is True: print clrmsg.ERROR + 'Error Test'
if debug is True: print clrmsg.INFO + 'Info Test'
if debug is True: print clrmsg.WARNING + 'Warning Test'
########## Executed when running in standalone ###################################
##################################################################################

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = APP()
	window.show()
	sys.exit(app.exec_())