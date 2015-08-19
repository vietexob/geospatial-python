'''
Created on Aug 19, 2015

Convert an classified/thresholded raster image into an ESRI shapefile (polygonal vector)

@author: trucvietle
'''

import gdal
from osgeo import ogr, osr

src = './data/remote_sensing/islands_classified.tiff'
tgt = './data/remote_sensing/extract.shp'

tgtLayer = 'extract'
srcDS = gdal.Open(src)
band = srcDS.GetRasterBand(1)
mask = band
driver = ogr.GetDriverByName('ESRI Shapefile')
shp = driver.CreateDataSource(tgt)
srs = osr.SpatialReference()
srs.ImportFromWkt(srcDS.GetProjectionRef())
layer = shp.CreateLayer(tgtLayer, srs = srs)
fd = ogr.FieldDefn('DN', ogr.OFTInteger)
layer.CreateField(fd)
dst_field = 0
extract = gdal.Polygonize(band, mask, layer, dst_field, [], None)
