#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Help documentation accessed via context menu

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

from PyQt5 import QtWidgets

class help():
    def __init__(self,parent=None):
        self.parent = parent

    def fluoProject(self):
        QtWidgets.QMessageBox.about(
            self.parent, 'Help', (
                'Select up to 4 fluorescence volumes from which to generate maximum intensity projections.\n'
                'Projections will be generated for each 3DCT text output supplied.\n'
                'If a mask is provided, volumes will be masked before projections are calculated.'
                ))

    def predictFIB(self):
        QtWidgets.QMessageBox.about(
            self.parent, 'Help', (
                'Shift + Left-click to define eucentric point in each image.\n'
                'Scroll to zoom. Ctrl + left-click to drag image.\n'
                'Beads listed in the 3DCT file are marked by blue dots.\n'
                'Click \'Calculate\' to apply rotation to beads.\n'
                'Drag to move points.\n'
                '\'Export points\' exports points in .csv format.'
                ))

    def createMask(self):
        QtWidgets.QMessageBox.about(
            self.parent, 'Help', (
                'Scroll to zoom. Ctrl/Cmd + left-click to drag image.\n\n'
                'SEM image:\n(1) Draw a polygon to outline the lamella.\n'
                '        Left-click to begin drawing.\n'
                '        Backspace to remove last point.\n'
                '        Return, Escape or right-click to finish.\n'
                '(2) Place one point within the lamella.\n        Shift + left-click to place point.\n\n'
                'FIB image:\nMark the front of the lamella in the FIB image\n'
                '        Shift + Left-click to place point.\n\n'
                'Select the corresponding 3DCT file for both images.\n'
                'Choose a reference fluorescence volume to set output dimensions.\n'
                'Valid paths to file are highlighted green. Invalid paths are red.\n'
                ))

    def findBeads(self):
        QtWidgets.QMessageBox.about(
            self.parent, 'Help', (
                'Images can be 2D or 3D.\nMaximum intensity projections are used for 3D images.\n\n'
                'Beads are detected based on:\n'
                '- cross-correlation with a simulated Gaussian\n- Hough transform based on the given radius\n- intensity-based thresholding\n\n'
                '\'Multiplier\' adjusts the radius used for calculation.\n\n'
                'Try different thresholding methods.\nE.g. \'Isodata\' often works well for SEM images.\n\n'
                '\'Number of Beads\' determines the number of peaks returned.\n\n'
                'Input pixel size in nm.\n\n'
                '\'Export mask\' writes the detected points to an image.\nThis image can be loaded as a layer in 3DCT.'
                ))
