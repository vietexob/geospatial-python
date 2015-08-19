'''
Created on Aug 19, 2015

@author: trucvietle
'''

import gdalnumeric

src = './data/remote_sensing/islands.tif'
tgt = './data/remote_sensing/islands_classified.tiff'
srcArr = gdalnumeric.LoadFile(src)
classes = gdalnumeric.numpy.histogram(srcArr, bins = 2)[1]
lut = [[255, 0, 0], [0, 0, 0], [255, 255, 255]]
start = 1
rgb = gdalnumeric.numpy.zeros((3, srcArr.shape[0], srcArr.shape[1], ), gdalnumeric.numpy.float32)

for i in range(len(classes)):
    mask = gdalnumeric.numpy.logical_and(start <= srcArr, srcArr <= classes[i])
    for j in range(len(lut[i])):
        rgb[j] = gdalnumeric.numpy.choose(mask, (rgb[j], lut[i][j]))
    start = classes[i] + 1

gdalnumeric.SaveArray(rgb.astype(gdalnumeric.numpy.uint8), tgt, format = 'GTIFF', prototype = src)
