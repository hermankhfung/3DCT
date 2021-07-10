#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get z axis position of spherical markers from 3D image stacks (tiff z-stack)
import beadPos.py and call z = beadPos.getz(x,y,img,n=None,optimize=False) to get z position
at the given x and y pixel coordinate or call x,y,z = beadPos.getz(x,y,img,n=None,optimize=True)
to get an optimized bead position (optimization of x, y and z)

# @Title			: beadPos
# @Project			: 3DCTv2
# @Description		: Get bead z axis position from 3D image stacks (tiff z-stack)
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			: endolith https://gist.github.com/endolith/255291 for parabolic fitting function
# 					  2D Gaussian fit from http://scipy.github.io/old-wiki/pages/Cookbook/FittingData
# @Date				: 2021/04
# @Version			: 3DCT 3.0.0 module rev. 2
# @Status			: stable
# @Usage			: import beadPos.py and call z = beadPos.getz(x,y,img,n=None,optimize=False) to get z position
# 					  at the given x and y pixel coordinate or call x,y,z = beadPos.getz(x,y,img,n=None,optimize=True)
# 					  to get an optimized bead position (optimization of x, y and z)
# @Notes			: stable, but problems with low SNR <- needs revisiting
# @Python_version	: 3.8.9
"""
# ======================================================================================================================

import time
import math
import numpy as np
from scipy.optimize import curve_fit, leastsq
import matplotlib.pyplot as plt
import tifffile as tf
from . import parabolic

try:
    from . import clrmsg
    from . import TDCT_debug
except:
    pass

repeat = 0
debug = TDCT_debug.debug


def getzPoly(x,y,img,n=None,optimize=False):
    """x and y are coordinates
    img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
    n is the number of points around the max value that are used in the polyfit
    leave n to use the maximum amount of points
    If optimize is set to True, the algorithm will try to optimize the x,y,z position
    !! if optimize is True, 3 values are returned: x,y,z"""

    if not isinstance(img, str) and not isinstance(img, np.ndarray):
        if clrmsg and debug is True: print(clrmsg.ERROR)
        raise TypeError('I can only handle an image path as string or an image volume as numpy.ndarray imported from tifffile.py')
    elif isinstance(img, str):
        img = tf.imread(img)

    data_z = img[:,y,x]

    if n is None:
        n = getn(data_z)

    data_z_xp_poly, data_z_yp_poly = parabolic.parabolic_polyfit(data_z, np.argmax(data_z), n)

    if math.isnan(data_z_xp_poly):
        if clrmsg and debug is True: print(clrmsg.ERROR)
        print(TypeError('Failed: Probably due to low SNR'))
        if optimize is True:
            return x,y,'failed'
        else:
            return 'failed'

    if debug is True:
        f, ax = plt.subplots()
        ax.plot(list(range(0,len(data_z))), data_z, color='blue')
        ax.plot(data_z_xp_poly, data_z_yp_poly, 'o', color='black')
        ax.set_title("mid: "+str(data_z_xp_poly))

        plt.draw()
        plt.pause(1)
        plt.close()

    if optimize is True:
        x_opt_vals, y_opt_vals, z_opt_vals = optimize_z(x,y,data_z_xp_poly,img,n=None)
        return x_opt_vals[-1], y_opt_vals[-1], z_opt_vals[-1]
    else:
        return data_z_xp_poly


def getzGauss(x,y,img,parent=None,optimize=False,threshold=None,threshVal=0.6,cutout=15):
    """x and y are coordinates
    img is the path to the z-stack tiff file or a numpy.ndarray from tifffile.py imread function
    optimize == True kicks off the 2D Gaussian fit and this function will return x,y,z
    threshold == True filters the image where it cuts off at max - min * threshVal (threshVal between 0.1 and 1)
    cutout specifies the FOV for the 2D Gaussian fit"""

    #Optimizes a gaussian in z direction first
    #Then it optimizes a 2D gaussian in the xy plane

    if not isinstance(img, str) and not isinstance(img, np.ndarray):
        if clrmsg and debug is True: print(clrmsg.ERROR)
        raise TypeError('I can only handle an image path as string or an image volume as numpy.ndarray imported from tifffile.py')
    elif isinstance(img, str): #TODO: This is very strange that the image can be passed as a path rather than an already opened image/volume data
        img = tf.imread(img)
    
    #List of x and y coordinates of beads/POI are converted to integer type so that they can be used as indexes
    ix = np.round(x).astype(int)
    iy = np.round(y).astype(int)
    if 0 <= ix < img.shape[-1] and 0 <= iy < img.shape[-2]: #Checks the approximate x and y coordinates of the bead are inside the volume
        data_z = img[:,iy,ix] #Gets data vs z (1D plot) at the approximate x,y locations
        data = np.array([np.arange(len(data_z)), data_z])

        #Fits a gaussian in the z axis direction
        poptZ, pcov = gaussfit(data,parent)
    else:
        #approximate (x,y) coordinates of the bead are outside image boundaries
        #set the gaussian parameters to following
        poptZ = [None, -1.0, None]

    #popt - gaussian optimized parameters in format A, mu, sigma
    if optimize is False:
        return poptZ[1] #Optimization along z at (x,y) completed. Do not try to fit gaussian on x-y plane.
    else:
        repeats = 5 #Repeats optimization 5 times
        if clrmsg and debug is True: print(clrmsg.DEBUG + '2D Gaussian xy optimization running %.f at z = %.f' % (repeats,round(poptZ[1])))
        for repeat in range(repeats):
            if (cutout <= ix < img.shape[-1]-cutout and
                    cutout <= iy < img.shape[-2]-cutout and
                    0 <= poptZ[1] < img.shape[-3]-0.5):
                
                #Gets 2D XY plane data from image, only around the region of interest
                #at z=zmean (determined from the previous gaussian fit)
                data = np.copy(img[
                            int(round(poptZ[1])),
                            int(iy-cutout):int(iy+cutout),
                            int(ix-cutout):int(ix+cutout)])
            else:
                print("Point(s) too close to edge or out of bounds.")
                return ix, iy, poptZ[1]
            if threshold is not None:
                threshold = data < data.max()-(data.max()-data.min())*threshVal
                data[threshold] = 0
            
            #TODO: Testing new function
            #poptXY = fitgaussian(data,parent)
            poptXY = fit2Dgaussian(data,parent)

            if poptXY is None:
                #Failed to fit in the 2D plane, exit
                return ix, iy, poptZ[1]

            #gets the optimized gaussian2D parameters
            (height, xopt, yopt, width_x, width_y) = poptXY
            ## x and y are switched when applying the offset
            ix = ix-cutout+yopt
            iy = iy-cutout+xopt
            if 0 <= ix < img.shape[-1] and 0 <= iy < img.shape[-2]:
                data_z = img[:,int(iy),int(ix)]
            else:
                return ix, iy, poptZ[1]
            data = np.array([np.arange(len(data_z)), data_z])
            poptZ, pcov = gaussfit(data,parent,hold=True)
            if parent: parent.refreshUI()
            time.sleep(0.01)
        return ix, iy, poptZ[1]


def optimize_z(x,y,z,image,n=None):
    """Optimize z for poly fit"""
    if type(image) == str:
        img = tf.imread(image)
    elif type(image) == np.ndarray:
        img = image

    data_z = img[:,y,x]

    if n is None:
        n = getn(data_z)

    x_opt_vals, y_opt_vals, z_opt_vals = [], [], []

    x_opt,y_opt,z_opt = x,y,z
    for i in range(5):
        try:
            print(x_opt,y_opt,z_opt)
            x_opt,y_opt,z_opt = int(round(x_opt)),int(round(y_opt)),int(round(z_opt))
            x_opt, y_opt = optimize_xy(x_opt,y_opt,z_opt,img,nx=None,ny=None)
            data_z = img[:,round(y_opt),round(x_opt)]
        except Exception as e:
            if clrmsg and debug is True: print(clrmsg.ERROR)
            print(IndexError("Optimization failed, possibly due to low signal or low SNR. "+str(e)))
            return [x],[y],['failed']
        n = getn(data_z)
        z_opt, data_z_yp_poly = parabolic.parabolic_polyfit(data_z, np.argmax(data_z), n)
        x_opt_vals.append(x_opt)
        y_opt_vals.append(y_opt)
        z_opt_vals.append(z_opt)

    return x_opt_vals, y_opt_vals, z_opt_vals


def getn(data):
    """this function is used to determine the maximum amount of data points for the polyfit function
    data is a numpy array of values"""

    if len(data)-np.argmax(data) <= np.argmax(data):
        n = 2*(len(data)-np.argmax(data))-1
    else:
        n = 2*np.argmax(data)
    return n


def optimize_xy(x,y,z,image,nx=None,ny=None):
    """x and y are coordinates, z is the layer in the z-stack tiff file
    image can be either the path to the z-stack tiff file or the np.array data of itself
    n is the number of points around the max value that are used in the polyfit
    leave n to use the maximum amount of points"""
    get_nx, get_ny = False, False
    if type(image) == str:
        img = tf.imread(image)
    elif type(image) == np.ndarray:
        img = image
    ## amount of data points around coordinate
    samplewidth = 10
    data_x = img[z,y,x-samplewidth:x+samplewidth]
    data_y = img[z,y-samplewidth:y+samplewidth,x]

    if debug is True: f, axarr = plt.subplots(2, sharex=True)

    if nx is None:
        get_nx = True
    if ny is None:
        get_ny = True

    ## optimize x
    xmaxvals = np.array([], dtype=np.int32)
    for offset in range(10):
        data_x = img[z,y-offset,x-samplewidth:x+samplewidth]
        if data_x.max() < data_x.mean()*1.1:
            # print "breaking at ",offset
            # print data_x.max(), data_x.mean(), data_x.mean()*1.1
            break
        if get_nx is True:
            nx = getn(data_x)
        data_x_xp_poly, data_x_yp_poly = parabolic.parabolic_polyfit(data_x, np.argmax(data_x), nx)
        xmaxvals = np.append(xmaxvals,[data_x_xp_poly])
        c = np.random.rand(3,1)
        if debug is True:
            axarr[0].plot(list(range(0,len(data_x))), data_x, color=c)
            axarr[0].plot(data_x_xp_poly, data_x_yp_poly, 'o', color=c)
    for offset in range(10):
        data_x = img[z,y+offset,x-samplewidth:x+samplewidth]
        if data_x.max() < data_x.mean()*1.1:
            # print "breaking at ",offset
            # print data_x.max(), data_x.mean(), data_x.mean()*1.1
            break
        if get_nx is True:
            nx = getn(data_x)
        data_x_xp_poly, data_x_yp_poly = parabolic.parabolic_polyfit(data_x, np.argmax(data_x), nx)
        xmaxvals = np.append(xmaxvals,[data_x_xp_poly])
        c = np.random.rand(3,1)
        if debug is True:
            axarr[0].plot(list(range(0,len(data_x))), data_x, color=c)
            axarr[0].plot(data_x_xp_poly, data_x_yp_poly, 'o', color=c)

    if debug is True: axarr[0].set_title("mid-mean: "+str(xmaxvals.mean()))

    ## optimize y
    ymaxvals = np.array([], dtype=np.int32)
    for offset in range(10):
        data_y = img[z,y-samplewidth:y+samplewidth,x-offset]
        if data_y.max() < data_y.mean()*1.1:
            # print "breaking at ",offset
            # print data_y.max(), data_y.mean(), data_y.mean()*1.1
            break
        if get_ny is True:
            ny = getn(data_y)
        data_y_xp_poly, data_y_yp_poly = parabolic.parabolic_polyfit(data_y, np.argmax(data_y), ny)
        ymaxvals = np.append(ymaxvals,[data_y_xp_poly])
        c = np.random.rand(3,1)
        if debug is True:
            axarr[1].plot(list(range(0,len(data_y))), data_y, color=c)
            axarr[1].plot(data_y_xp_poly, data_y_yp_poly, 'o', color=c)

    for offset in range(10):
        data_y = img[z,y-samplewidth:y+samplewidth,x+offset]
        if data_y.max() < data_y.mean()*1.1:
            # print "breaking at ",offset
            # print data_y.max(), data_y.mean(), data_y.mean()*1.1
            break
        if get_ny is True:
            ny = getn(data_y)
        data_y_xp_poly, data_y_yp_poly = parabolic.parabolic_polyfit(data_y, np.argmax(data_y), ny)
        ymaxvals = np.append(ymaxvals,[data_y_xp_poly])
        c = np.random.rand(3,1)
        if debug is True:
            axarr[1].plot(list(range(0,len(data_y))), data_y, color=c)
            axarr[1].plot(data_y_xp_poly, data_y_yp_poly, 'o', color=c)

    if debug is True: axarr[1].set_title("mid-mean: "+str(ymaxvals.mean()))

    if debug is True:
        plt.draw()
        plt.pause(0.5)
        plt.close()
    ## calculate offset into coordinates
    x_opt = x+xmaxvals.mean()-samplewidth
    y_opt = y+ymaxvals.mean()-samplewidth

    return x_opt, y_opt


## Gaussian 1D fit
def gauss(x, *p):
    # A "magnitude"
    # mu "offset on x axis"
    # sigma "width"
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))


def gaussfit(data,parent=None,hold=False):
    ## Fitting 1D gaussian to data
    # and plots to parent.widget_matplotlib the result
    data[1] = data[1]-data[1].min()
    p0 = [data[1].max(), data[1].argmax(), 1]

    #uses curve_fit() from scipy
    popt, pcov = curve_fit(gauss, data[0], data[1], p0=p0)

    if parent is not None:
        ## Draw graphs in GUI
        x = []
        y = []
        for i in np.arange(len(data[0])):
            x.append(i)
            y.append(gauss(i,*popt))
        if hold is False:
            parent.widget_matplotlib.setupScatterCanvas(width=4,height=4,dpi=52,toolbar=False)
        parent.widget_matplotlib.xyPlot(data[0], data[1], label='z data',clear=True)
        #parent.widget_matplotlib.xyPlot(x, y, label='gaussian fit',clear=False)

        #Try adding wiidth to plot label
        parent.widget_matplotlib.xyPlot(x, y,
            label=('gauss fit w=%.1f' % (popt[2])),
            clear=False )

            

    ## DEBUG
    if clrmsg and debug is True:
        from scipy.stats import ks_2samp
        ## Get std from the diagonal of the covariance matrix
        std_height, std_mean, std_sigma = np.sqrt(np.diag(pcov))
        print(clrmsg.DEBUG + '='*15, 'GAUSS FIT', '='*25)
        print(clrmsg.DEBUG + 'Amplitude		:', popt[0])
        print(clrmsg.DEBUG + 'Location		:', popt[1])
        ## http://mathworld.wolfram.com/GaussianFunction.html -> sigma * 2 * sqrt(2 * ln(2))
        print(clrmsg.DEBUG + 'FWHM			:', popt[2] * 2 * math.sqrt(2 * math.log(2,math.e)))
        print(clrmsg.DEBUG + 'Std. Amplitude	:', std_height)
        print(clrmsg.DEBUG + 'Std. Location	:', std_mean)
        print(clrmsg.DEBUG + 'Std. FWHM		:', std_sigma * 2 * math.sqrt(2 * math.log(2,math.e)))
        print(clrmsg.DEBUG + 'Mean dy		:', np.absolute(y-data[1]).mean())
        print(clrmsg.DEBUG + str(ks_2samp(y, data[1])))
    return popt, pcov


## Gaussian 2D fit from http://scipy.github.io/old-wiki/pages/Cookbook/FittingData
def gaussian(height, center_x, center_y, width_x, width_y):
    """Returns a Gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x,y: height*np.exp(
                -(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)


def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the Gaussian parameters of a 2D distribution by calculating its
    moments"""
    #TODO: The role of this function is not clear
    #But it appears it makes gaussian fitting easier
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    col = data[:, int(y)]
    width_x = np.sqrt(abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
    height = data.max()

    #This actually returns the follwing
    #height = maximum datavalue
    #x = average of the ix*datavalue
    #y = average of the iy*datavalue
    #width_x ?
    #width_y ?
    return height, x, y, width_x, width_y


def fitgaussian(data,parent=None):
    """Returns (height, x, y, width_x, width_y)
    the Gaussian parameters of a 2D distribution found by a fit"""

    #LMAP: This 2D gaussian fitting is done using the least squares optimizer in scikit.
    #Strangely enough, it does not use the scipy.optimize.curve_fit

    def errorfunction(gaussianparams):
        #this error function is very weird. This is not the mathematical error function
        #It is just gaussian-datavalue

        #For the leastsq fitting to work, this function can return a 1D array with the
        # (fit-data) values
        #The leastsq algorithm will then minimize the value of
        # sum( (funct)**2 )
        #by adjusting the parameters

        return np.ravel(gaussian(*gaussianparams)(*np.indices(data.shape)) - data)
        '''
        This is equivalent to something like
        ind0 = np.indices(data.shape) #np.indices is similar to meshgrid but Y_mg and X_mg are obtaied with index)
        X_mg = ind0[0]
        Y_mg_ = ind0[1]
        mygaussianf = gaussian(*gaussianparams)
        mygaussianf_array = mygaussianf(X_mg,Y_mg)
        mygaussianf_array_flattened = np.ravel(mygaussianf_array)
        return mygaussianf_array_flattened
        '''

    try:
        gaussparams_initvalues = moments(data)
    except ValueError:
        return None
    
    #https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.leastsq.html
    #Finds the gaussian parameters p that fit best to the data.
    p, success = leastsq(errorfunction, gaussparams_initvalues)
    
    if np.isnan(p).any():
        parent.widget_matplotlib.matshowPlot(
            mat=data,contour=np.ones(data.shape),labelContour="XY optimization failed\n" +
            "Try reducing the\nmarker size (equates to\nFOV for gaussian fit)")
        return None
    if parent is not None:
        ## Draw graphs in GUI
        fit = gaussian(*p)
        contour = fit(*np.indices(data.shape))
        (height, x, y, width_x, width_y) = p
        labelContour = (
                        "      x : %.1f\n"
                        "      y : %.1f\n"
                        "width_x : %.1f\n"
                        "width_y : %.1f") % (x, y, width_x, width_y)
        parent.widget_matplotlib.matshowPlot(mat=data,contour=contour,labelContour=labelContour)
    return p


# def test1Dgauss(data=None):
# 	if not data:
# 		data = np.random.normal(loc=5., size=10000)
# 	hist, bin_edges = np.histogram(data, density=True)
# 	bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
# 	data = np.array([bin_centres, hist])
# 	# data = np.array([[0,1,2,3,4,5,6,7,8,9],[10,12,11,15,25,18,13,9,11,10]])
# 	popt, pcov = gaussfit(data)

# 	x = []
# 	y = []
# 	for i in np.arange(len(data[0])):
# 		x.append(i)
# 		y.append(gauss(i,*popt))
# 	plt.clf()
# 	plt.plot(data[0], data[1], label='Test data')
# 	plt.plot(x, y, label='Gaussian fit')

# 	new_bin_centers = np.linspace(bin_centres[0], bin_centres[-1], 200)
# 	new_hist_fit = gauss(new_bin_centers, *popt)
# 	plt.plot(new_bin_centers, new_hist_fit,label='Interpolated')

# 	plt.legend()
# 	plt.show()
# 	if clrmsg and debug is True:
# 		from scipy.stats import ks_2samp
# 		print clrmsg.DEBUG + ('Mean dy : %.6f' % np.absolute(y-data[1]).mean())
# 		print clrmsg.DEBUG + str(ks_2samp(y, data[1]))


# def test2Dgauss(data=None):
# 	from pylab import *
# 	if data is None:
# 		# Create the Gaussian data
# 		Xin, Yin = mgrid[0:201, 0:201]
# 		data = gaussian(3, 100, 100, 20, 40)(Xin, Yin) + np.random.random(Xin.shape)

# 	# data = data-data.min()
# 	print data.min(), data.max()
# 	threshold = data < data.max()-(data.max()-data.min())*0.6
# 	data[threshold] = 0

# 	matshow(data, cmap=cm.gist_earth_r)

# 	params = fitgaussian(data)
# 	fit = gaussian(*params)

# 	contour(fit(*indices(data.shape)), cmap=cm.copper)
# 	ax = gca()
# 	(height, x, y, width_x, width_y) = params

# 	text(0.85, 0.05, """
# 	x : %.1f
# 	y : %.1f
# 	width_x : %.1f
# 	width_y : %.1f""" % (x, y, width_x, width_y),
# 						fontsize=12, horizontalalignment='right',
# 						verticalalignment='bottom', transform=ax.transAxes)

# 	show()

# img = tf.imread('/Users/jan/Desktop/dot2.tif')
# print img.shape
# test2Dgauss(img)


def fit2Dgaussian(data2D, parent=None, hold=False):
    #To replace fitgaussian()
    #Also, it uses scipy.optimize.curve_fit
    #https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html#scipy.optimize.curve_fit

    #And idea is based on
    #https://stackoverflow.com/questions/21566379/fitting-a-2d-gaussian-function-using-scipy-optimize-curve-fit-valueerror-and-m

    #For curve_fit() to work
    #function to optimize must accept the independent variable(s) as first argument
    def gauss2D (yxpos , height, center_x, center_y, width_x, width_y, offset):
        '''
            Assume y = yxpos[0] and x = yxpos[1]
        '''
        y=yxpos[0] #Note that y can be a n-dim array
        x=yxpos[1]

        gaussres = offset + height*np.exp(
                -(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)

        return gaussres

    #Need to convert data to a flat array and we need also the corresponding yspos values
    ind0 = np.indices(data2D.shape, dtype=np.float32)
    X_mg = ind0[0]
    Y_mg = ind0[1]
    X_mg_flat = np.ravel(X_mg)
    Y_mg_flat = np.ravel(Y_mg)

    #YXPos = np.empty( (2,X_mg_flat.size) )
    #YXPos[0,:] = Y_mg_flat[:]
    #YXPos[1,:] = X_mg_flat[:]

    data2D_flat = np.ravel(data2D)

    #get initial guess values
    #height, center_x, center_y, width_x, width_y, offset
    height_guess = np.max(data2D)
    center_x_guess = data2D.shape[1]/2
    center_y_guess = data2D.shape[0]/2
    width_x_guess = center_x_guess
    width_y_guess = center_y_guess
    offset_guess=0.0

    #curve_fit() only seems to work with flattened data
    params_opt, params_cov = curve_fit(
        gauss2D,
        [Y_mg_flat, X_mg_flat],
        data2D_flat,
        p0=( height_guess, center_x_guess, center_y_guess, width_x_guess, width_y_guess, offset_guess)
    )

    p=params_opt[:-1]

    #Copied from fitgaussian(), changing data to data2D
    #Returns all parameters except last one called offset
    #optimized parameters should be in format (height, center_x, center_y, width_x, width_y)
    
    if np.isnan(p).any():
        parent.widget_matplotlib.matshowPlot(
            mat=data2D,contour=np.ones(data2D.shape),labelContour="XY optimization failed\n" +
            "Try reducing the\nmarker size (equates to\nFOV for gaussian fit)")
        return None
    if parent is not None:
        ## Draw graphs in GUI
        gaussfit_function = gaussian(*p) #Gets a gaussian function with the parameters given
        gaussfit_data= gaussfit_function(*np.indices(data2D.shape))
        (height, x, y, width_x, width_y) = p
        labelContour = (
                        "      x : %.1f\n"
                        "      y : %.1f\n"
                        "width_x : %.1f\n"
                        "width_y : %.1f") % (x, y, width_x, width_y)
        parent.widget_matplotlib.matshowPlot(mat=data2D, contour=gaussfit_data, labelContour=labelContour)
        #matshowplot() in QTCustom.py , MatplotlibWidgetCustom
    return p




