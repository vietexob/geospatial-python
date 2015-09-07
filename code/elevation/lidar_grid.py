'''
Created on Sep 6, 2015

@author: trucvietle
'''
from laspy.file import File
import numpy as np

## Source LAS file
source = './data/elevation/lidar.las'

## Output ASCII DEM file
target = './data/elevation/lidar.asc'

## Grid cell size (data units)
cell = 1.0

## No-data value for output DEM
NODATA = 0

## Open LIDAR LAS file
las = File(source, mode='r')

## xyz min and max
min = las.header.min
max = las.header.max

## Get the x-axis distance
xdist = max[0] - min[0]
## Get the y-axis distance
ydist = max[1] - min[1]

## Number of columns for our grid
ncols = int(xdist) / cell
## Number of rows for our grid
nrows = int(ydist) / cell

ncols += 1
nrows += 1

## Track how many elevation values we aggregate
count = np.zeros((nrows, ncols)).astype(np.float32)
## Aggregate elevalation values
zsum = np.zeros((nrows, ncols)).astype(np.float32)

## Y resolution is negative
ycell = -1 * cell

## Project x, y values onto grid
projx = (las.x - min[0]) / cell
projy = (las.y - min[1]) / ycell

## Cast to integers and clip for use as index
ix = projx.astype(np.int32)
iy = projy.astype(np.int32)

## Loop through x, y, z arrays, add to grid shape, and aggregate values for averaging
for x, y, z in np.nditer([ix, iy, las.z]):
    count[y, x] += 1
    zsum[y, x] += z

## Change 0 values to 1 to avoid numpy warnings and NaN values in array
nonzero = np.where(count > 0, count, 1)
## Average our z values
zavg = zsum / nonzero

## Interpolate 0 values in array to avoid any holes in the grid
mean = np.ones((nrows, ncols)) * np.mean(zavg)
left = np.roll(zavg, -1, 1)
lavg = np.where(left > 0, left, mean)
right = np.roll(zavg, 1, 1)
ravg = np.where(right > 0, right, mean)
interpolate = (lavg + ravg) / 2
fill = np.where(zavg > 0, zavg, interpolate)

## Create our ASCII DEM header
header = 'ncols    {}\n'.format(fill.shape[1])
header += 'nrows    {}\n'.format(fill.shape[0])
header += 'xllcorner    {}\n'.format(min[0])
header += 'yllcorner    {}\n'.format(min[1])
header += 'cellsize    {}\n'.format(cell)
header += 'NODATA value    {}'.format(NODATA)

## Open the output file, add the header, and save the array
with open(target, 'wb') as f:
    f.write(str(header))
    ## The fmt string ensures we output floats that have at least one number but only two decimals
    np.savetxt(f, fill, fmt = '%1.2f')
