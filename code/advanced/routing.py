'''
Created on Oct 13, 2015

@author: trucvietle
'''

import networkx as nx
import math
from itertools import tee
import shapefile
import os

savedir = './data/advanced/routing/'
## Road network shapefile: subset of a US interstates from the USGS edited
shp = './data/advanced/routing/road_network.shp'

def haversine(n0, n1):
    x1, y1 = n0
    x2, y2 = n1
    x_dist = math.radians(x1-x2)
    y_dist = math.radians(y1-y2)
    y1_rad = math.radians(y1)
    y2_rad = math.radians(y2)
    a = math.sin(y_dist/2)**2 + math.sin(x_dist/2)**2 * math.cos(y1_rad) * math.cos(y2_rad)
    c = 2 * math.asin(math.sqrt(a))
    distance = c * 6371
    return distance

def pairwise(iterable):
    """
    Returns an iterable in tuples of two.
    s -> (s0, s1), (s1, s2), (s2, s3), ...
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

## Create a graph with NetworkX and add the shapefile segments as edges
G = nx.DiGraph()
r = shapefile.Reader(shp)
for s in r.shapes():
    for p1, p2 in pairwise(s.points):
        G.add_edge(tuple(p1), tuple(p2))

## Extract connected component as subgraph
sg = list(nx.connected_component_subgraphs(G.to_undirected()))[0]
## Read the start and end points we want to navigate
r = shapefile.Reader('./data/advanced/routing/start_end')
start = r.shape(0).points[0]
end = r.shape(1).points[0]

## Loop through the subgraph and assign distance values to each edge
## using haversine formula
for n0, n1 in sg.edges_iter():
    dist = haversine(n0, n1)
    sg.edge[n0][n1]['dist'] = dist

## We find the nodes in the graph closest to our start and end points
## to begin and end our route by looping through all of the nodes and
## measuring the distance to our end points until we find the shortest distance.
nn_start = None
nn_end = None
start_delta = float('inf')
end_delta = float('inf')
for n in sg.nodes():
    s_dist = haversine(start, n)
    e_dist = haversine(end, n)
    if s_dist < start_delta:
        nn_start = n
        start_delta = s_dist
    if e_dist < end_delta:
        nn_end = n
        end_delta = e_dist

## Calculate the shortest distance through our network
path = nx.shortest_path(sg, source=nn_start, target=nn_end, weight='dist')

## We will add the results to the shapefile and save our route
w = shapefile.Writer(shapefile.POLYLINE)
w.field('NAME', 'C', 40)
w.line(parts=[[list(p) for p in path]])
w.record('route')
w.save(os.path.join(savedir, 'route'))
