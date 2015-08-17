'''
Created on Aug 17, 2015

Shapefile selections -- Chapter 5

@author: trucvietle
'''

import shapefile

r = shapefile.Reader('./data/roads/roadtrl020')
w = shapefile.Writer(r.shapeType)
w.fields = list(r.fields)
x_min = -67.50
x_max = -65.00
y_min = 17.80
y_max = 18.60

for road in r.iterShapeRecords():
    geom = road.shape
    rec = road.record
    sx_min, sy_min, sx_max, sy_max = geom.bbox
    if sx_min < x_min: continue
    elif sx_min > x_max: continue
    elif sy_min < y_min: continue
    elif sy_max > y_max: continue
    w._shapes.append(geom)
    w.records.append(rec)

w.save('Puerto_Rico_Roads')
