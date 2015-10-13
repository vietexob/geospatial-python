'''
Created on Oct 13, 2015

We use geotags to create a shapefile with point locations for the photos
and paths to the photos as attributes.

@author: trucvietle
'''

import glob
import os
from PIL import Image, ImageDraw
from PIL.ExifTags import TAGS
import shapefile

def exif(img):
    """
    Extracts EXIF data.
    """
    exif_data = {}
    try:
        i = Image.open(img)
        tags = i._getexif()
        for tag, value in tags.items():
            decoded = TAGS.get(tag, tag)
            exif_data[decoded] = value
    except:
        pass
    return exif_data

def dms2dd(d, m, s, i):
    """
    Converts degree, minutes, seconds (DMS) coordinates
    to decimal degrees.
    """
    sec = float((m*60)+s)
    dec = float(sec / 3600)
    deg = float(d + dec)
    if i.upper() == 'W':
        deg = deg * -1
    elif i.upper() == 'S':
        deg = deg * -1
    return float(deg)

def gps(exif):
    lat = None
    lon = None
    if exif['GPSInfo']:
        ## Lat
        coords = exif['GPSInfo']
        i = coords[1]
        d = coords[2][0][0]
        m = coords[2][1][0]
        s = coords[2][2][0]
        lat = dms2dd(d, m, s, i)
        ## Lon
        i = coords[3]
        d = coords[4][0][0]
        m = coords[4][1][0]
        s = coords[4][2][0]
        lon = dms2dd(d, m, s, i)
    return lat, lon

## Loop through the photos, extract coordinates, and store them and filenames in a dict
photos = {}
photo_dir = './data/advanced/photos'
files = glob.glob(os.path.join(photo_dir, '*.jpg'))
for f in files:
    e = exif(f)
    lat, lon = gps(e)
    photos[f] = [lon, lat]

## Save the photo info as shapefile
w = shapefile.Writer(shapefile.POINT)
w.field('NAME', 'C', 80)
for f, coords in photos.items():
    w.point(*coords)
    w.record(f)
w.save('./data/advanced/photos/photos')
