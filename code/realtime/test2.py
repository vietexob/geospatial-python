'''
Created on Dec 7, 2015

    Gets the bus location, converts the location to meters, creates a 2-mile
    rectangle around the location, and downloads a street and weather map. The
    map images are then blended together using PIL, which shrinks the bus icon
    to 20x20 pixels and pastes it at the center of the map, at the bus location.

@author: trucvietle
'''

from urllib2 import urlopen
from urllib2 import urlparse
from urllib2 import URLError
from xml.dom import minidom
from PIL import Image
import sys
import math


