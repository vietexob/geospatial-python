'''
Created on Sep 6, 2015

@author: trucvietle
'''
import gdal
import ogr
import shapefile
import pngcanvas

## Elevation DEM
source = './data/elevation/dem/dem.asc'
## Output shapefile
target = './data/elevation/dem/contours'

ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
ogr_ds = ogr_driver.CreateDataSource(target + '.shp')
ogr_lyr = ogr_ds.CreateLayer(target, geom_type = ogr.wkbLineString25D)
field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
ogr_lyr.CreateField(field_defn)
field_defn = ogr.FieldDefn('ELEV', ogr.OFTReal)
ogr_lyr.CreateField(field_defn)

ds = gdal.Open(source)
gdal.ContourGenerate(ds.GetRasterBand(1), 400, 10, [], 0, 0, ogr_lyr, 0, 1)

## Draw the contour shapefile we've just created using PNGCanvas
## Open the contours
r = shapefile.Reader('./data/elevation/dem/contours.shp')
## Set up the world to pixels conversion
xdist = r.bbox[2] - r.bbox[0]
ydist = r.bbox[3] - r.bbox[1]
iwidth = 800
iheight = 600
xratio = iwidth / xdist
yratio = iheight / ydist

contours = []
## Loop through all shapes
for shape in r.shapes():
    ## Loop through all parts
    for i in range(len(shape.parts)):
        pixels = []
        pt = None
        if i < len(shape.parts)-1:
            pt = shape.points[shape.parts[i]:shape.parts[i+1]]
        else:
            pt = shape.points[shape.parts[i]:]
        for x, y in pt:
            px = int(iwidth - ((r.bbox[2]-x) * xratio))
            py = int((r.bbox[3] - y) * yratio)
            pixels.append([px, py])
        contours.append(pixels)

## Set up the output canvas
canvas = pngcanvas.PNGCanvas(iwidth, iheight)
## PNGCanvas accepts rgba byte arrays for colors
red = [0xff, 0, 0, 0xff]
canvas.color = red
## Loop through the polygons and draw them
for c in contours:
    canvas.polyline(c)

## Save the image
f = open('./data/elevation/dem/contours.png', 'wb')
f.write(canvas.dump())
f.close()
