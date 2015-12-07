'''
Created on Dec 7, 2015
    
    Return the locations of a bus given a route. If direction tag not specified, Nextbus returns
    the first one. We are going to poll Nextbus tracking API by calling REST URL and output the
    latest lon and lat of the Mainline bus.

@author: trucvietle
'''

from urllib2 import urlopen
from urllib2 import urlparse
from urllib2 import URLError
from xml.dom import minidom
import time

def nextbus(a, r, c='vehicleLocations', e=0):
    '''
    Returns the most recent lon and lat of the selected bus
    line using the Nextbus API (nbapi).
    Arguments: a=agency; r=route; c=command;
    e=epoch: timestamp for start date of track,
    0 = the last 15 minutes.
    '''
    nbapi = 'http://webservices.nextbus.com'
    nbapi += '/service/publicXMLFeed?'
    nbapi += 'command={}&a={}&r={}&t={}'.format(c, a, r, e)
    xml = minidom.parse(urlopen(nbapi))
    ## If more than one vehicle, just get the first
    bus = xml.getElementsByTagName('vehicle')[0]
    if bus:
        at = bus.attributes
        return(at['lon'].value, at['lat'].value)
    else:
        return(False, False)

def nextmap(a, r, mapimg):
    '''
    Plots a nextbus location on the map image and saves it to
    disk using the OSM Static Map API (osmapi).
    '''
    ## Fetch the latest bus location
    lon, lat = nextbus(a, r)
    if not lon:
        return False
    ## Base URL + service path
    osmapi = 'http://staticmap.openstreetmap.de/staticmap.php?'
    ## Center the map around the bus location
    osmapi += 'center={},{}&'.format(lat, lon)
    ## Set the zoom level (between 1--18, where higher = lower scale)
    osmapi += 'zoom=14&'
    ## Set the map image size
    ## NOTE: This line causes URL timeout
#     osmapi += 'size=865x512&'
    ## Use the mapnik rendering image
    osmapi += 'maptype=mapnik&'
    ## Use a red, pushpin marker to pin point the bus
    osmapi += 'markers={},{},red-pushpin'.format(lat, lon)
    img = urlopen(osmapi)
    ## Save the map image
    with open('{}.png'.format(mapimg), 'wb') as f:
        f.write(img.read())
    return True
    
## Nextbus API agency and busline variables
agency = 'lametro'
route = '2'

## Name of the map image to save as PNG
nextimg = './figures/realtime/nextmap'
## Number of updates we want to make
requests = 3
## How often we want to update (seconds)
freq = 5
## Map the bus location every few seconds
for i in range(requests):
    success = nextmap(agency, route, nextimg)
    if not success:
        print('No data available.')
        continue
    print('Saved map {} at {}'.format(i, time.asctime()))
    time.sleep(freq)
