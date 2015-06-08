'''
Created on Jun 8, 2015

Demonstrates the use of struct module to read the bounding box from a shapefile.
The shapefile 'hancock.shp' can be downloaded at:
https://geospatialpython.googlecode.com/files/hancock.zip

@author: larcuser
'''

import struct

# Open the shapefile
f = open("./data/hancock/hancock.shp", "rb")

# Go to the start of the bounding box coordinates
f.seek(36)

# Read min-x,min-y,max-x,max-y in little-endian format
print(struct.unpack("<d", f.read(8)))
print(struct.unpack("<d", f.read(8)))
print(struct.unpack("<d", f.read(8)))
print(struct.unpack("<d", f.read(8)))

# Read all 4 values at once
f.seek(36)
print(struct.unpack("<dddd", f.read(32)))
