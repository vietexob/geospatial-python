'''
Created on Aug 19, 2015

@author: trucvietle
'''

import gdalnumeric
import operator
from functools import reduce

def histogram(a, bins = list(range(0, 256))):
    fa = a.flat
    n = gdalnumeric.numpy.searchsorted(fa, bins)
    n = gdalnumeric.numpy.concatenate([n, [len(fa)]])
    hist = n[1:]-n[:-1]
    
    return(hist)

def stretch(a):
    hist = histogram(a)
    lut = []
    for b in range(0, len(hist), 256):
        step = reduce(operator.add, hist[b:b+256]) / 255
        n = 0
        for i in range(256):
            lut.append(n / step)
            n += hist[i+b]
    
    gdalnumeric.numpy.take(lut, a, out = a)
    return(a)

src = './data/remote_sensing/swap.tif'
arr = gdalnumeric.LoadFile(src)
stretched = stretch(arr)
gdalnumeric.SaveArray(arr, './data/remote_sensing/stretched.tif', format='GTiff', prototype=src)
