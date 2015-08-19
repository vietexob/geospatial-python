'''
Created on Aug 19, 2015

Visualize the extracted shapefile (from raster image) and draw the small lagoon (properly)
that shows up as a small hole in the polygon.

@author: trucvietle
'''

import shapefile
import pngcanvas

r = shapefile.Reader('./data/remote_sensing/extract.shp')
xdist = r.bbox[2] - r.bbox[0]
ydist = r.bbox[3] - r.bbox[1]
iwidth = 800
iheight = 600
xratio = iwidth / xdist
yratio = iheight / ydist
polygons = []

for shape in r.shapes():
    for i in range(len(shape.parts)):
        pixels = []
        pt = None
        if i < len(shape.parts)-1:
            pt = shape.points[shape.parts[i]:shape.parts[i+1]]
        else:
            pt = shape.points[shape.parts[i]:]
        for x, y in pt:
            px = int(iwidth - ((r.bbox[2]-x)*xratio))
            py = int((r.bbox[3]-y)*yratio)
            pixels.append([px, py])
        
        polygons.append(pixels)

c = pngcanvas.PNGCanvas(iwidth, iheight)
for p in polygons:
    c.polyline(p)

f = open('./data/remote_sensing/extract.png', 'wb')
f.write(c.dump())
f.close()
