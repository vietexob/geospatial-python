'''
Created on Dec 7, 2015

    We use HTML, GeoJSON, Leaflet, and pure Python library named Folium to create
    a client-server app that allows us to post geospatial information to a server,
    and then create an interactive web map to view those data updates.

@author: trucvietle
'''

import folium

m = folium.Map()
m.geo_json(geo_path='https://api.myjson.com/bins/467pm')
m.create_map(path = './data/realtime/map.html')
