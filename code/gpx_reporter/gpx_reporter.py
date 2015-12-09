'''
Created on Dec 8, 2015

    Final app: GPS route analysis report.
    
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
# print(miny, maxy)
# print(minx, maxx)
image = srt.get_image((w, h), (miny, maxy), (minx, maxx), 300, zero_color=zero_clr, min_color=min_clr, max_color=max_clr)
## Save the image
image.save(elv_img + '.jpg', 'JPEG')

## Hillshade the elevation image
log.info('Hillshading elevation data')
im = Image.open(elv_img + '.jpg').convert('L')
dem = np.asarray(im)

## Set up structure for a 3x3 to process the slope throughout the grid
window = []
## x, y resolutions
xres = (maxx - minx) / w
yres = (maxy - miny) / h

## Create the windows
for row in range(3):
    for col in range(3):
        window.append(dem[row:(row + dem.shape[0]-2), col:(col + dem.shape[1]-2)])

## Process each cell
x = ((z*window[0] + 2*z*window[3] + z*window[6]) - (z*window[2] + 2*z*window[5] + z*window[8])) / (8.0*xres*scale)
y = ((z*window[6] + 2*z*window[7] + z*window[8]) - (z*window[0] + 2*z*window[1] + z*window[2])) / (8.0*yres*scale)

## Calculate the slope
slope = 90.0 - np.arctan(np.sqrt(x*x + y*x)) * rad2deg
## Calculate aspect
aspect = np.arctan2(x, y)
## Calculate the shaded relief
shaded = np.sin(altitude*deg2rad) * np.sin(slope*deg2rad) + np.cos(altitude*deg2rad) * np.cos(slope*deg2rad) * np.cos((azimuth-90.0) * deg2rad-aspect)
shaded = shaded * 255

## Convert the numpy array back to an image
relief = Image.fromarray(shaded).convert('L')
## Smooth the image several times so it's not pixelated
for i in range(10):
    relief = relief.filter(ImageFilter.SMOOTH_MORE)
log.info('Creating map image')

## Increase the hillshade contrast to make it stand out more
e = ImageEnhance.Contrast(relief)
relief = e.enhance(2)

## Crop the image to match the SRTM image. We lose 2 pixels during the hillshading process
base = Image.open(osm_img + '.jpg').crop((0, 0, w-2, h-2))

## Enhance basemap contrast before blending
e = ImageEnhance.Contrast(base)
base = e.enhance(1)

## Blend the map and hillshade at 90% opacity
topo = Image.blend(relief.convert('RGB'), base, 0.90)

## Draw the GPX tracks
## Convert the coordinates to pixels
points = []
for x, y in zip(lons, lats):
    px, py = world2pixel(x, y, w, h, bbox)
    points.append((px, py))

## Crop the image size values to match the map
w -= 2
h -= 2
## Set up an translucent image to draw the route.
## This technique allows us to see the streets and street names under the route line.
track = Image.new('RGBA', (w, h))
track_draw = ImageDraw.Draw(track)

## Route line will be red at 50% transparency (255/2 = 127)
track_draw.line(points, fill=(255, 0, 0, 127), width=4)

## Paste onto the basemap using the drawing layer itself as a mask.
topo.paste(track, mask=track)

## Now we'll draw start and end points directly on top of our map. No need for transparency
topo_draw = ImageDraw.Draw(topo)

## Starting cycle
start_lon, start_lat = (lons[0], lats[0])
start_x, start_y = world2pixel(start_lon, start_lat, w, h, bbox)
start_point = [start_x-10, start_y-10, start_x+10, start_y+10]
topo_draw.ellipse(start_point, fill='lightgreen', outline='black')
start_marker = [start_x-4, start_y-4, start_x+4, start_y+4]
topo_draw.ellipse(start_marker, fill='black', outline='white')

## Ending circle
end_lon, end_lat = (lons[-1], lats[-1])
end_x, end_y = world2pixel(end_lon, end_lat, w, h, bbox)
end_point = [end_x-10, end_y-10, end_x+10, end_y+10]
topo_draw.ellipse(end_point, fill='red', outline='black')
end_marker = [end_x-4, end_y-4, end_x+4, end_y+4]
topo_draw.ellipse(end_marker, fill='black', outline='white')

## Save the topo map
topo.save('{}_topo.jpg'.format(osm_img))

## Build elevation chart using Google Charts API
log.info('Creating elevation profile chart')
chart = SimpleLineChart(600, 300, y_range=[min(elvs), max(elvs)])

## API quirk: You need 3 lines of data to color in the plot, so we add
## a line at minimum value twice.
chart.add_data([min(elvs)]*2)
chart.add_data(elvs)
chart.add_data([min(elvs)]*2)

## Black lines
chart.set_colours(['000000'])
## Fill in the elevation area with a hex color
chart.add_fill_range('80C65A', 1, 2)

## Set up labels for the min elevation, halfway value, and max value
elv_labels = int(round(min(elvs))), int(min(elvs) + ((max(elvs)-min(elvs)/2))), int(round(max(elvs))) 
## Assign the labels to an axis
elv_label = chart.set_axis_labels(Axis.LEFT, elv_labels)
## Label the axis
elv_text = chart.set_axis_labels(Axis.LEFT, ['FEET'])
## Place the label at 30% the distance of the line
chart.set_axis_positions(elv_text, [30])

## Calculate distances between track segments
distances = []
measurements = []
coords = list(zip(lons, lats))
for i in range(len(coords)-1):
    x1, y1 = coords[i]
    x2, y2 = coords[i+1]
    d = haversine(x1, y1, x2, y2)
    distances.append(d)

total = sum(distances)
distances.append(0)
j = -1

## Locate the mile markers
for i in range(1, int(round(total))):
    mile = 0
    while mile < i:
        j += 1
        mile += distances[j]
    measurements.append((int(mile), j))
    j = -1

## Set up labels for the mile points
positions = []
miles = []
for m, i in measurements:
    pos = ((i*1.0)/len(elvs)) * 100
    positions.append(pos)
    miles.append(m)

## Position the mile marker labels along the x axis
miles_label = chart.set_axis_labels(Axis.BOTTOM, miles)
chart.set_axis_positions(miles_label, positions)

## Label the x axis as 'Miles'
miles_text = chart.set_axis_labels(Axis.BOTTOM, ['MILES', ])
chart.set_axis_positions(miles_text, [50, ])

## Save the chart
chart.download('{}_profile.png'.format(elv_img))

log.info('Creating weather summary')
## Get the bounding box centroid for georeferencing weather data
centx = minx + ((maxx-minx)/2)
centy = miny + ((maxy-miny)/2)

## WeatherUnderground API key
api_key = '0cc5fdfd4599eddf'
## Get the location id of the route using the bounding box centroid
## and the geolookup API
geolookup_reg = 'http://api.wunderground.com/api/{}'.format(api_key)
geolookup_reg += '/geolookup/q/{},{}.json'.format(centy, centx)
request = urlopen(geolookup_reg)
geolookup_data = request.read().decode('utf-8')  

## Cache lookup data for testing if needed
with open('./data/gpx_reporter/geolookup.json', 'w') as f:
    f.write(geolookup_data)

js = json.loads(open('./data/gpx_reporter/geolookup.json').read())
loc = js['location']
route_url = loc['requesturl']

## Grab the latest route timestamp to query weather history
t = times[-1]
history_reg = 'http://api.wunderground.com/api/{}'.format(api_key)
name_info = [t.tm_year, t.tm_mon, t.tm_mday, route_url.split('.')[0]]
history_reg += '/history_{0}{1:02d}{2:02d}/q/{3}.json'.format(*name_info)
request = urlopen(history_reg)
weather_data = request.read()

## Cache weather data for testing
with open('./data/gpx_reporter/weather.json', 'w') as f:
    f.write(weather_data.decode('utf-8'))

## Retrieve weather data
js = json.loads(open('./data/gpx_reporter/weather.json').read())
history = js['history']

## Grab the weather summary data: first item in the list
daily = history['dailysummary'][0]

## Max temperature in Fahrenheit. Celcius would be metric: 'maxtempm'.
maxtemp = daily['maxtempi']
## Min temperature
mintemp = daily['mintempi']
## Max humidity
maxhum = daily['maxhumidity']
## Min humidity
minhum = daily['minhumidity']

## Precipitation in inches (cm = 'precipm')
precip = daily['precipi']

## Simple fpdf.py library for our report. New pdf, portrait mode, inches, letter size
pdf = fpdf.FPDF('P', 'in', 'Letter')

## Add our one-page report
pdf.add_page()
## Set up the title
pdf.set_font('Arial', 'B', 20)
## Cells containing text or space items horizontally
pdf.cell(6.25, 1, 'GPX Report', border=0, align='C')
## Lines space items vertically (units in inches)
pdf.ln(h=1)
pdf.cell(1.75)

## Create a horizontal rule line
pdf.cell(4, border='T')
pdf.ln(h=0)
pdf.set_font('Arial', style='B', size=14)

## Set up the route map
pdf.cell(w=1.2, h=1, txt='Route Map', border=0, align='C')
pdf.image('{}_topo.jpg'.format(osm_img), 1, 2, 4, 4)
pdf.ln(h=4.35)

## Add elevation chart
pdf.set_font('Arial', style='B', size=14)
pdf.cell(w=1.2, h=1, txt='Elevation Profile', border=0, align='C')
pdf.image('{}_profile.png'.format(elv_img), 1, 6.5, 4, 2)
pdf.ln(h=2.4)

## Write the weather summary
pdf.set_font('Arial', style='B', size=14)
pdf.cell(1.2, 1, 'Weather Summary', align='C')
pdf.ln(h=0.25)
pdf.set_font('Arial', style='', size=12)
pdf.cell(1.2, 1, 'Min. Temp.: {}'.format(mintemp), align='C')
pdf.cell(1.2, 1, 'Max. Hum.: {}'.format(maxhum), align='C')
pdf.ln(h = 0.25)
pdf.cell(1.2, 1, 'Max. Temp.: {}'.format(maxtemp), align='C')
pdf.cell(1.2, 1, 'Precip.: {}'.format(precip), align='C')
pdf.ln(h=0.25)
pdf.cell(1.2, 1, 'Min. Hum.: {}'.format(minhum), align='C')

## Give Wunderground credit for their service
pdf.image('./figures/gpx_reporter/wundergroundLogo_black_horz.jpg', 3.5, 9, 1.75, 0.25)

## Save the report
log.info('Saving report as PDF')
pdf.output('./data/gpx_reporter/report.pdf', 'F')
