'''
Created on Oct 11, 2015

@author: trucvietle
'''

import numpy as np

## Width and height of grid
w = 5
h = 5

## Start location: lower left of grid
start = (h-1, 0)
## End location: top right of grid
dx = w-1
dy = 0

## Blank grid
a = np.zeros((w, h))

## Distance grid
dist = np.zeros(a.shape, dtype=np.int8)
## Calculate distance for all cells
for y, x in np.ndindex(a.shape):
    dist[y][x] = abs((dx-x)+(dy-y))

## Terrain is a random value between 1-16
## Add to the distance grid to calculate the cost of moving to a cell
cost = np.random.randint(1, 16, (w, h)) + dist

print("Cost Grid (Value + Distance)")
print(cost)

## Our A* search algorithm
def astar(start, end, h, g):
    cset = set()
    oset = set()
    path = set()
    oset.add(start)
    while oset:
        cur = oset.pop()
        if cur == end:
            return path
        cset.add(cur)
        path.add(cur)
        options = []
        y1 = cur[0]
        x1 = cur[1]
        if y1 > 0:
            options.append((y1-1, x1))
        if y1 < h.shape[0]-1:
            options.append((y1+1, x1))
        if x1 > 0:
            options.append((y1, x1-1))
        if x1 < h.shape[1]-1:
            options.append((y1, x1+1))
        if end in options:
            return path
        best = options[0]
        cset.add(options[0])
        for i in range(1, len(options)):
            option = options[i]
            if option in cset:
                continue
            elif h[option] <= h[best]:
                best = option
                cset.add(option)
            elif g[option] < g[best]:
                best = option
                cset.add(option)
            else:
                cset.add(option)
        print(best, ', ', h[best], ', ', g[best])
        oset.add(best)
    return []

print ('(Y, X), Heuristic, Distance')
## Find the path
path = astar(start, (dy, dx), cost, dist)

## Create and populate the path grid
path_grid = np.zeros(cost.shape, dtype = np.uint8)
for y, x in path:
    path_grid[y][x] = 1
path_grid[dy][dx] = 1

print('Path Grid: 1=path')
print(path_grid)
