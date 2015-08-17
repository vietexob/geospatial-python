'''
Created on Aug 17, 2015

The following script reprojects the shapefile. The geometry is transformed and written to
a new file, but the dbf file is simply copied to the new name as we aren't changing it.

@author: trucvietle
'''

import ogr
import osr
import os
import shutil

srcName = './data/NYC_MUSEUMS_LAMBERT/NYC_MUSEUMS_LAMBERT.shp'
tgtName = './data/NYC_MUSEUMS_LAMBERT/NYC_MUSEUMS_GEO.shp'
tgt_spatRef = osr.SpatialReference()
tgt_spatRef.ImportFromEPSG(4326)
driver = ogr.GetDriverByName('ESRI Shapefile')
src = driver.Open(srcName, 0)
srcLyr = src.GetLayer()
src_spatRef = srcLyr.GetSpatialRef()

if os.path.exists(tgtName):
    driver.DeleteDataSource(tgtName)

tgt = driver.CreateDataSource(tgtName)
lyrName = os.path.splitext(tgtName)[0]
tgtLyr = tgt.CreateLayer(lyrName, geom_type = ogr.wkbPoint)
featDef = srcLyr.GetLayerDefn()
trans = osr.CoordinateTransformation(src_spatRef, tgt_spatRef)
srcFeat = srcLyr.GetNextFeature()

while srcFeat:
    geom = srcFeat.GetGeometryRef()
    geom.Transform(trans)
    feature = ogr.Feature(featDef)
    tgtLyr.CreateFeature(feature)
    feature.Destroy()
    srcFeat.Destroy()
    srcFeat = srcLyr.GetNextFeature()

src.Destroy()
tgt.Destroy()
tgt_spatRef.MorphToESRI()
prj = open(lyrName + '.prj', 'w')
prj.write(tgt_spatRef.ExportToWkt())
prj.close()

srcDbf = os.path.splitext(srcName)[0] + '.dbf'
tgtDbf = lyrName + '.dbf'
shutil.copy(srcDbf, tgtDbf)
