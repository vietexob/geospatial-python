'''
Created on Dec 8, 2015

@author: trucvietle
'''

from xml.dom import minidom
from urllib2 import urlopen
from pygooglechart import SimpleLineChart
from pygooglechart import Axis
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
from PIL import ImageDraw
import numpy as np
import json
import srtm
import math
import time
import logging
import sys
import fpdf


## Python logging module provides a more advanced way to track and log program progress.
## Logging level -- everything at or below this level will output. INFO is below.
level = logging.DEBUG
## The formatter formats the log message. In this case, we print the local time,
## logger name, and message.
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
## Establish a logging object and name it
log = logging.getLogger('GPX-Reporter')
## Configure our logger
log.setLevel(level)
## Print the command to line
console = logging.StreamHandler()
console.setLevel(level)
console.setFormatter(formatter)
log.addHandler(console)

def ll2m(lat, lon):
    '''
    Converts lat/lon to meters.
    '''
    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = y * 20037508.34 / 180.0
    return (x, y)

def world2pixel(x, y, w, h, bbox):
    '''
    Converts world coordinates to image pixel coordinates.
    '''
    ## Bounding box of the map
    minx, miny, maxx, maxy = bbox
    ## World x distance
    xdist = maxx - minx
    ## World y distance
    ydist = maxy - miny
    ## Scaling factors for x, y
    xratio = w / xdist
    yratio = h / ydist
    ## Calculate x, y pixel coordinates
    px = w - ((maxx - x) * xratio)
    py = (maxy - y) * yratio
    return int(px), int(py)

def get_utc_epoch(timestr):
    '''
    Converts a GPX timestamp to Unix epoch seconds in Greenwich mean time
    to make time math faster.
    '''
    ## Get time object from ISO time string
    utc_time = time.strptime(timestr, '%Y-%m-%dT%H:%M:%SZ')
    ## Convert to seconds since epoch
    secs = int(time.mktime(utc_time))
    return secs
    
def get_local_time(timestr, utc_offset=None):
    '''
    Converts a GPX timestamp to Unix epoch seconds in the local time zone.
    '''
    secs = get_utc_epoch(timestr)
    if not utc_offset:
        ## Get local time zone offset
        if time.localtime(secs).tm_isdst:
            utc_offset = time.altzone
            pass
        else:
            utc_offset = time.timezone
            pass
        pass
    return time.localtime(secs - utc_offset)

def haversine(x1, y1, x2, y2):
    '''
    Haversine distance formula.
    '''
    x_dist = math.radians(x1 - x2)
    y_dist = math.radians(y1 - y2)
    y1_rad = math.radians(y1)
    y2_rad = math.radians(y2)
    a = math.sin(y_dist / 2)**2 + math.sin(x_dist/2)**2 * math.cos(y1_rad) * math.cos(y2_rad)
    c = 2 * math.asin(math.sqrt(a))
    ## Distance in miles. Just use c*6371 for kilometers
    distance = c * (6371 / 1.609344) # miles
    return distance

def wms(minx, miny, maxx, maxy, service, lyr, epsg, style , img, w, h):
    '''
    Retrieves a WMS map image from the specified service and saves it as JPEG.
    '''
    wms = service
    wms += '?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&'
    wms += 'LAYERS={}&'.format(lyr)
    wms += 'STYLES={}&'.format(style)
    wms += 'SRS=EPSG:{}&'.format(epsg)
    wms += 'BBOX={},{},{},{}&'.format(minx, miny, maxx, maxy)
    wms += 'WIDTH={}&'.format(w)
    wms += 'HEIGHT={}&'.format(h)
    wms += 'FORMAT=image/jpeg'
    wmsmap = urlopen(wms)
    print(wms)
    with open(img + '.jpg', 'wb') as f:
        f.write(wmsmap.read())
    
## Needed for numpy conversions in hillshading
deg2rad = math.pi / 180.0
rad2deg = 180.0 / math.pi

## Program variables
## Name of the GPX file containing the route
gpx = './data/gpx_reporter/route.gpx'

## NOAA OSM basemap
## NOAA OSM WMS service
osm_wms = 'http://osm.woc.noaa.gov/mapcache'
## Name of the WMS street layer
osm_lyr = 'osm'
## Name of the basemap image to save
osm_img = './figures/gpx_reporter/basemap'
## OSM EPSG code
osm_epsg = 3857
## Optional WMS parameter
osm_style = ''

## Shaded elevation parameters
## Sun direction
azimuth = 315.0
## Sun angle
altitude = 45.0
## Elevation exaggeration
z = 5.0
## Resolution
scale = 1.0
## No data value for output
no_data = 0
## Output elevation image name
elv_img = './figures/gpx_reporter/elevation'
## RGBA color of the SRTM minimum elevation
min_clr = (255, 255, 255, 0)
## RGBA color of the SRT maximum elevation
max_clr = (0, 0, 0, 0)
## No data color
zero_clr = (255, 255, 255, 255)
## Pixel width and height of the ouput images
w = 800
h = 800

## Parse the GPX file and extract the coordinates
log.info('Parsing GPX file: {}'.format(gpx))
xml = minidom.parse(gpx)
## Grab all of the 'trkpt' elements
trkpts = xml.getElementsByTagName('trkpt')
## Latitude, longitude, and elevation lists
lats = []
lons = []
elvs = []
## GPX timestamp list
times = []

## Parse lat/long, elevation and times
for trkpt in trkpts:
    ## Lat, lon, and elevation
    lat = float(trkpt.attributes['lat'].value)
    lats.append(lat)
    lon = float(trkpt.attributes['lon'].value)
    lons.append(lon)
    elv = trkpt.childNodes[0].firstChild.nodeValue
    elv = float(elv)
    elvs.append(elv)
    ## Times
    t = trkpt.childNodes[1].firstChild.nodeValue
    ## Convert to local time epoch seconds
    t = get_local_time(t)
    times.append(t)

## Find lat/lon bounding box of the route
minx = min(lons)
miny = min(lats)
maxx = max(lons)
maxy = max(lats)

## Buffer the GPX bounding box by 20% so the track isn't too close
## to the edge of the image
xdist = maxx - minx
ydist = maxy - miny
x10 = xdist * 0.20
y10 = ydist * 0.20
## 10% expansion on each side
minx -= x10
miny -= y10
maxx += x10
maxy += y10
## Store the bounding box in a single variable to streamline function calls
bbox = [minx, miny, maxx, maxy]
## We need the bounding box in meters for the OSM WMS service. We will
## download it in degrees to match the SRTM file. The WMS specs say the
## input SRS should match the output, but this custom service just doesn't
## work that way.
mminx, mminy = ll2m(miny, minx)
mmaxx, mmaxy = ll2m(maxy, maxx)

## Download the OSM basemap
log.info('Downloading basemap...')
wms(mminx, mminy, mmaxx, mmaxy, osm_wms, osm_lyr, osm_epsg, osm_style, osm_img, w, h)

## Download the SRTM image
log.info('Retrieving SRTM elevation data...')
## The SRTM module will try to use a local cache first, and if needed download it.
srt = srtm.get_data()
## Get the image and return a PIL Image object
print(miny, maxy)
print(minx, maxx)
image = srt.get_image((w, h), (miny, maxy), (minx, maxx), 300, zero_color=zero_clr, min_color=min_clr, max_color=max_clr)
## Save the image
image.save(elv_img + '.jpg', 'JPEG')

## Hillshade the elevation image















