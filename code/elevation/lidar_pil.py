'''
Created on Sep 7, 2015

@author: trucvietle
'''
import numpy as np
from PIL import Image, ImageOps

## Source LIDAR DEM file
source = './data/elevation/dem/relief.asc'
## Output image file
target = './data/elevation/dem/relief.bmp'

## Load the ASCII DEM into a numpy array
arr = np.loadtxt(source, skiprows = 6)

## Convert array into numpy image
im = Image.fromarray(arr).convert('RGB')

## Enhance the image, equalize and increase contrast
im = ImageOps.equalize(im)
im = ImageOps.autocontrast(im)

## Save the image
im.save(target)
