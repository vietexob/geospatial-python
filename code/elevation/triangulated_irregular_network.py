'''
Created on Sep 7, 2015

@author: trucvietle
'''
import pickle
import os
import time
import math
import numpy as np
import shapefile
from laspy.file import File
import voronoi

## Source LAS file
source = './data/elevation/clippedLAS.las'
## Output shapefile
target = 'mesh'

## Triangles archive
archive = 'triangles.p'
## Pyshp archive
pyshp = 'mesh_pyshp.p'

class Point:
    """Point class required by the voronoi module"""
    def __init__(self, x, y):
        self.px = x
        self.py = y
    def x(self):
        return self.px
    def y(self):
        return self.py


## The triangle array holds tuples. 3 point indices used to retrieve the points.
## Load it from a pickle file or use the voronoi module to create the triangles.
triangles = None
