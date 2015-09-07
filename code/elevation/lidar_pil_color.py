'''
Created on Sep 7, 2015

@author: trucvietle
'''
import numpy as np
from PIL import Image, ImageOps
import colorsys

## Source LIDAR DEM file
source = './data/elevation/lidar.asc'
## Output image file
target = './data/elevation/lidar.bmp'

## Load the ASCII DEM into a numpy array
arr = np.loadtxt(source, skiprows=6)
## Convert the numpy array into a PIL image
im = Image.fromarray(arr).convert('L')

## Enhance the image
im = ImageOps.equalize(im)
im = ImageOps.autocontrast(im)

## Begin building our color ramp
palette = []

## Hue, saturation, value color space
h = 0.67
s = 1
v = 1

## We'll step through colors from blue-green-yellow-orange-red
## Blue = low elevation, Red = high elevation
step = h / 256.0

## Build the palette
for i in range(256):
    rp, gp, bp = colorsys.hsv_to_rgb(h, s, v)
    r = int(rp * 255)
    g = int(gp * 255)
    b = int(bp * 255)
    palette.extend([r, g, b])
    h -= step
    
## Apply the palette to the image
im.putpalette(palette)

## Save the image
im.save(target)
