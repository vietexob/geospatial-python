'''
Created on Aug 19, 2015

@author: trucvietle
'''

import operator
from osgeo import gdal, gdalnumeric, osr
import shapefile
from PIL import Image, ImageDraw

raster = './data/remote_sensing/stretched.tif'
shp = './data/hancock/hancock'
output = './data/remote_sensing/clip'

def imageToArray(i):
    a = gdalnumeric.numpy.fromstring(i.tostring(), 'b')
    a.shape = i.im.size[1], i.im.size[0]
    return(a)

def world2Pixel(geoMatrix, x, y):
    ulX = geoMatrix[0]
    ulY = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]
    pixel = int((x-ulX)/xDist)
    line = int((ulY-y)/xDist)
    return(pixel, line)

srcArray = gdalnumeric.LoadFile(raster)
srcImage = gdal.Open(raster)
geoTrans = srcImage.GetGeoTransform()
r = shapefile.Reader('{}.shp'.format(shp))
minX, minY, maxX, maxY = r.bbox
ulX, ulY = world2Pixel(geoTrans, minX, maxY)
lrX, lrY = world2Pixel(geoTrans, maxX, minY)
pxWidth = int(lrX - ulX)
pxHeight = int(lrY - ulY)
clip = srcArray[:, ulY:lrY, ulX:lrX]
geoTrans = list(geoTrans)
geoTrans[0] = minX
geoTrans[3] = maxY

pixels = []
for p in r.shape(0).points:
    pixels.append(world2Pixel(geoTrans, p[0], p[1]))
rasterPoly = Image.new('L', (pxWidth, pxHeight), 1)
rasterize = ImageDraw.Draw(rasterPoly)
rasterize.polygon(pixels, 0)
mask = imageToArray(rasterPoly)

clip = gdalnumeric.numpy.choose(mask, (clip, 0)).astype(gdalnumeric.numpy.uint8)
gdalnumeric.SaveArray(clip, '{}.tif'.format(output), format='GTiff', prototype=raster)
