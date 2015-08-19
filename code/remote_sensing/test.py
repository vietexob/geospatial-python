'''
Created on Aug 19, 2015

@author: trucvietle
'''

from osgeo import gdalnumeric

src = './data/remote_sensing/FalseColor.tif'
arr = gdalnumeric.LoadFile(src)
gdalnumeric.SaveArray(arr[[1, 0, 2], :], './data/remote_sensing/swap.tif',
                      format = 'GTiff', prototype = src)
