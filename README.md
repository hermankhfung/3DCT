# README #

This Toolbox is built for 3D correlative microscopy. It helps with 3D to 2D correlation of three dimensional confocal image stacks to two dimensional SEM/FIB dual beam microscope images. Though it is not limited to that.

The 3D Correlation Toolbox was developed at the Max Planck Institute of Biochemistry, Department of Molecular Structural Biology on the basis of the paper [Site-Specific Cryo-focused Ion Beam Sample Preparation Guided by 3D Correlative Microscopy](http://dx.doi.org/10.1016/j.bpj.2015.10.053). 3DCT uses code from 3D rigid transformation from [Pyto](https://github.com/vladanl/Pyto.git).

Further information can be found on [http://www.biochem.mpg.de/en/rd/baumeister](http://www.biochem.mpg.de/en/rd/baumeister) and [http://3dct.semper.space](http://3dct.semper.space)

The Toolbox is written in Python 3.8 and comes with a PyQt5 GUI. Further dependencies as of now are:

+ PyQt5 [1]
+ numpy [1]
+ scipy [1]
+ matplotlib [1]
+ opencv-python [1]
+ tifffile 2021.4.8 [1]  (Christoph Gohlke)
+ colorama [1]  (optional for colored stdout when debugging)
+ qimage2ndarray [1]
+ tools3dct [2]

[1]: available via pip or your favourite package manager  
[2]: available via [https://github.com/hermankhfung/tools3dct](https://github.com/hermankhfung/tools3dct)

A test dataset can be downloaded here: [https://3dct.semper.space/download/3D_correlation_test_dataset.zip](https://3dct.semper.space/download/3D_correlation_test_dataset.zip)

An introduction video can be viewed here: [https://www.youtube.com/watch?v=nZnUZ877-TU](https://www.youtube.com/watch?v=nZnUZ877-TU)

### License ###

Copyright (C) 2016  Jan Arnold  
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
	along with this program.  If not, see <http://www.gnu.org/licenses/>.

### Versions ###

Version 2.0 was the first public release, by Jan Arnold, the orignal author, in Python 2.7.  
Version 2.4 contains bugfixes and documentation updates by Vladan Lucic, 2020.  
Version 3.0 contains modifications by Herman Fung, 2021, including the porting of Version 2.4 to Python 3.8 and the addition of functions from [tools3dct](https://github.com/hermankhfung/tools3dct) for fiducial position determination and post-correlation 3D transformations.

The most recent stable release version is 3.0.0.

### Binaries ###

Binaries for macOS, Windows 7 and Windows 10, built using [PyInstaller](https://www.pyinstaller.org), are available at [https://github.com/hermankhfung/3DCT/releases](https://github.com/hermankhfung/3DCT/releases).

Past releases are available at [https://3dct.semper.space/](https://3dct.semper.space/#download)

### Citing ###

We ask users to cite:

* The general [paper](http://dx.doi.org/10.1016/j.bpj.2015.10.053) that forms the basis of the 3D Correlation Toolbox
+ When using independent modules/scripts from the source code, any [specific](http://3dct.semper.space/documentation.html#citable) publications of modules/scripts used in this software
+ Check the header of the module/script in question for more detailed information

If journal reference limits interfere, the module/script-specific publications should take precedence.

In general, please cite this project and the modules/scripts used in it.

Thank you for your support!

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
