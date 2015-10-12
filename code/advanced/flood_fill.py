'''
Created on Oct 11, 2015

@author: trucvietle
'''

import numpy as np
from linecache import getline

def floodFill(c, r, mask):
    """
    Crawls a mask array containing only 1 and 0 values from the
    starting point (c = column, r = row) and returns an array with
    all values connected to the starting cell. This algorithm performs
    a 4-way check non-recursively.
    """
    ## Cells already filled
    filled = set()
    ## Cells to fill
    fill = set()
    fill.add((c, r))
    width = mask.shape[1]-1
    height = mask.shape[0]-1
    ## Out output inundation array
    flood = np.zeros_like(mask, dtype=np.int8)
    ## Loop through the modify the cells that need to be checked
    while fill:
        ## Grab a cell
        x, y = fill.pop()
        if y == height or x == width or x < 0 or y < 0:
            ## Dont't fill
            continue
        if mask[y][x] == 1:
            ## Do fill
            flood[y][x] = 1
            filled.add((x, y))
            ## Check neighbors for 1 values
            west = (x-1, y)
            east = (x+1, y)
            north = (x, y-1)
            south = (x, y+1)
            if west not in filled:
                fill.add(east)
            if east not in filled:
                fill.add(east)
            if north not in filled:
                fill.add(north)
            if south not in filled:
                fill.add(south)
    return flood

source = './data/advanced/FloodFill/terrain.asc'
target = './data/advanced/FloodFill/flood.asc'

print('Opening image...')
img = np.loadtxt(source, skiprows=6)
print('Image opened')

a = np.where(img < 70, 1, 0)
print('Image masked')

## Parse the header using a loop and the builtin linecache module
hdr = [getline(source, i) for i in range(1, 7)]
values = [float(h.split(' ')[-1].strip()) for h in hdr]
cols, rows, lx, ly, cell, nd = values
xres = cell
yres = cell * -1

## Starting point for the flood inundation
sx = 2582
sy = 2057

print('Beginning flood fill')
flood = floodFill(sx, sy, a)
print('Finnished flood fill')

header = ''
for i in range(6):
    header += hdr[i]

print('Saving grid')
## Open the output file, add the hdr and save the array
with open(target, 'wb') as f:
    f.write(bytes(header))
    np.savetxt(f, flood, fmt='%li')
print('Done!')
