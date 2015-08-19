'''
Created on Aug 19, 2015

@author: trucvietle
'''

from osgeo import gdal, gdalnumeric
import numpy as np

im1 = './data/remote_sensing/before.tif'
im2 = './data/remote_sensing/after.tif'
ar1 = gdalnumeric.LoadFile(im1).astype(np.int8)
ar2 = gdalnumeric.LoadFile(im2)[1].astype(np.int8)
diff = ar2 - ar1

classes = np.histogram(diff, bins = 5)[1]
lut = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 255, 0], [255, 0, 0]]

start = 1
rgb = np.zeros((3, diff.shape[0], diff.shape[1], ), np.int8)
for i in range(len(classes)):
    mask = np.logical_and(start <= diff, diff <= classes[i])
    for j in range(len(lut[i])):
        rgb[j] = np.choose(mask, (rgb[j], lut[i][j]))
    start = classes[i] + 1

gdalnumeric.SaveArray(rgb, './data/remote_sensing/change.tif', format = 'GTiff', prototype=im2)
