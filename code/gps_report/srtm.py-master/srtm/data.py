# -*- coding: utf-8 -*-

# Copyright 2013 Tomo Krajina
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Classess containing parsed elevation data.
"""

import pdb

import logging
import math
import re
import io

from . import utils as mod_utils
from . import retriever as retriever

import requests as requests

class GeoElevationData:
    """
    The main class with utility methods for elevations. Note that files are 
    loaded in memory, so if you need to find elevations for multiple points on 
    the earth -- this will load *many* files in memory!
    """

    srtm1_files = None
    srtm3_files = None

    # Lazy loaded files used in current app:
    files = None

    def __init__(self, srtm1_files, srtm3_files, leave_zipped=False,
                 file_handler=None):
        self.srtm1_files = srtm1_files
        self.srtm3_files = srtm3_files

        self.leave_zipped = leave_zipped

        self.file_handler = file_handler if file_handler else mod_utils.FileHandler()

        self.files = {}

    def get_elevation(self, latitude, longitude, approximate=None):
        geo_elevation_file = self.get_file(float(latitude), float(longitude))

        #logging.debug('File for ({0}, {1}) -> {2}'.format(
        #                  latitude, longitude, geo_elevation_file))

        if not geo_elevation_file:
            return None

        return geo_elevation_file.get_elevation(
                float(latitude),
                float(longitude),
                approximate)

    def get_file(self, latitude, longitude):
        """
        If the file can't be found -- it will be retrieved from the server.
        """
        file_name = self.get_file_name(latitude, longitude)
		
        if not file_name:
            return None

        if (file_name in self.files):
            return self.files[file_name]
        else:
            data = self.retrieve_or_load_file_data(file_name)
            if not data:
                return None

            result = GeoElevationFile(file_name, data, self)
            self.files[file_name] = result
            return result

    def retrieve_or_load_file_data(self, file_name):
        data_file_name = file_name
        zip_data_file_name = '{0}.zip'.format(file_name)

        if self.file_handler.exists(data_file_name):
            return self.file_handler.read(data_file_name)
        elif self.file_handler.exists(zip_data_file_name):
            data = self.file_handler.read(zip_data_file_name)
            return mod_utils.unzip(data)

        url = None

        if (file_name in self.srtm1_files):
            url = self.srtm1_files[file_name]
        elif (file_name in self.srtm3_files):
            url = self.srtm3_files[file_name]

        if not url:
            #logging.error('No file found: {0}'.format(file_name))
            return None

        r = requests.get(url)
        if r.status_code < 200 or 300 <= r.status_code:
            raise Exception('Cannot retrieve %s' % url)
        logging.info('Retrieving {0}'.format(url))
        data = r.content
        logging.info('Retrieved {0} ({1} bytes)'.format(url, len(data)))

        if not data:
            return None

        # data is zipped:

        if self.leave_zipped:
            self.file_handler.write(data_file_name + '.zip', data)
            data = mod_utils.unzip(data)
        else:
            data = mod_utils.unzip(data)
            self.file_handler.write(data_file_name, data)

        return data

    def get_file_name(self, latitude, longitude):
        # Decide the file name:
        if latitude >= 0:
            north_south = 'N'
        else:
            north_south = 'S'

        if longitude >= 0:
            east_west = 'E'
        else:
            east_west = 'W'

        file_name = '%s%s%s%s.hgt' % (north_south, str(int(abs(math.floor(latitude)))).zfill(2), 
                                      east_west, str(int(abs(math.floor(longitude)))).zfill(3))

        if not (file_name in self.srtm1_files) and not (file_name in self.srtm3_files):
            #logging.debug('No file found for ({0}, {1}) (file_name: {2})'.format(latitude, longitude, file_name))
            return None

        return file_name

    def get_image(self, size, latitude_interval, longitude_interval, max_elevation, 
                  unknown_color = (255, 255, 255, 255), zero_color = (0, 0, 255, 255),
                  min_color = (0, 0, 0, 255), max_color = (0, 255, 0, 255)):
        """
        Returns a PIL image.
        """
        try:
            import Image as mod_image
            import ImageDraw as mod_imagedraw
        except:
            from PIL import Image as mod_image
            from PIL import ImageDraw as mod_imagedraw

        if not size or len(size) != 2:
            raise Exception('Invalid size %s' % size)
        if not latitude_interval or len(latitude_interval) != 2:
            raise Exception('Invalid latitude interval %s' % latitude_interval)
        if not longitude_interval or len(longitude_interval) != 2:
            raise Exception('Invalid longitude interval %s' % longitude_interval)

        width, height = size
        width, height = int(width), int(height)

        latitude_from,  latitude_to  = latitude_interval
        longitude_from, longitude_to = longitude_interval

        image = mod_image.new('RGBA', (width, height),
                              (255, 255, 255, 255))
        draw = mod_imagedraw.Draw(image)

        for row in range(height):
            for column in range(width):
                latitude  = latitude_from  + float(row) / height * (latitude_to  - latitude_from)
                longitude = longitude_from + float(column) / height * (longitude_to - longitude_from)
                elevation = self.get_elevation(latitude, longitude)

                if elevation == None:
                    color = unknown_color
                else:
                    elevation_coef = elevation / float(max_elevation)
                    if elevation_coef < 0: elevation_coef = 0
                    if elevation_coef > 1: elevation_coef = 1
                    color = mod_utils.get_color_between(min_color, max_color, elevation_coef)
                    if elevation <= 0:
                        color = zero_color

                draw.point((column, height - row), color)

        return image

    def add_elevations(self, gpx, only_missing=False, smooth=False, gpx_smooth_no=0):
        """
        only_missing -- if True only points without elevation will get a SRTM value

        smooth -- if True interpolate between points

        if gpx_smooth_no > 0 -- execute gpx.smooth(vertical=True)
        """
        try: import gpxpy
        except: raise Exception('gpxpy needed')

        if only_missing:
            original_elevations = list([point.elevation for point in gpx.walk(only_points=True)])

        if smooth:
            self._add_sampled_elevations(gpx)
        else:
            for point in gpx.walk(only_points=True):
                point.elevation = self.get_elevation(point.latitude, point.longitude)

        for i in range(gpx_smooth_no):
            gpx.smooth(vertical=True, horizontal=False)

        if only_missing:
            for original_elevation, point in zip(original_elevations, list(gpx.walk(only_points=True))):
                if original_elevation != None:
                    point.elevation = original_elevation

    def _add_interval_elevations(self, gpx, min_interval_length=100):
        """
        Adds elevation on points every min_interval_length and add missing 
        elevation between
        """
        for track in gpx.tracks:
            for segment in track.segments:
                last_interval_changed = 0
                previous_point = None
                length = 0
                for no, point in enumerate(segment.points):
                    if previous_point:
                        length += point.distance_2d(previous_point)

                    if no == 0 or no == len(segment.points) - 1 or length > last_interval_changed:
                        last_interval_changed += min_interval_length
                        point.elevation = self.get_elevation(point.latitude, point.longitude)
                    else:
                        point.elevation = None
                    previous_point = point
        gpx.add_missing_elevations()

    def _add_sampled_elevations(self, gpx):
        # Use some random intervals here to randomize a bit:
        self._add_interval_elevations(gpx, min_interval_length=35)
        elevations_1 = list([point.elevation for point in gpx.walk(only_points=True)])
        self._add_interval_elevations(gpx, min_interval_length=141)
        elevations_2 = list([point.elevation for point in gpx.walk(only_points=True)])
        self._add_interval_elevations(gpx, min_interval_length=241)
        elevations_3 = list([point.elevation for point in gpx.walk(only_points=True)])

        n = 0
        for point in gpx.walk(only_points=True):
            if elevations_1[n] != None and elevations_2[n] != None and elevations_3[n] != None:
                #print elevations_1[n], elevations_2[n], elevations_3[n]
                point.elevation = (elevations_1[n] + elevations_2[n] + elevations_3[n]) / 3.
            else:
                point.elevation = None
            n += 1

class GeoElevationFile:
    """
    Contains data from a single Shuttle elevation file.

    This class hould not be instantiated without its GeoElevationData because 
    it may need elevations from nearby files.
    """

    file_name = None
    url = None
	
    latitude = None
    longitude = None

    data = None

    def __init__(self, file_name, data, geo_elevation_data):
        """ Data is a raw file contents of the file. """

        self.geo_elevation_data = geo_elevation_data
        self.file_name = file_name

        self.parse_file_name_starting_position()

        self.data = data

        square_side = math.sqrt(len(self.data) / 2.)
        assert square_side == int(square_side), 'Invalid file size: {0} for file {1}'.format(len(self.data), self.file_name)

        self.square_side = int(square_side)

    def get_row_and_column(self, latitude, longitude):
        return math.floor((self.latitude + 1 - latitude) * float(self.square_side - 1)), \
               math.floor((longitude - self.longitude) * float(self.square_side - 1))

    def get_elevation(self, latitude, longitude, approximate=None):
        """
        If approximate is True then only the points from SRTM grid will be 
        used, otherwise a basic aproximation of nearby points will be calculated.
        """
        if not (self.latitude <= latitude < self.latitude + 1):
            raise Exception('Invalid latitude %s for file %s' % (latitude, self.file_name))
        if not (self.longitude <= longitude < self.longitude + 1):
            raise Exception('Invalid longitude %s for file %s' % (longitude, self.file_name))

        points = self.square_side ** 2

        row, column = self.get_row_and_column(latitude, longitude)

        if approximate:
            return self.approximation(latitude, longitude)
        else:
            return self.get_elevation_from_row_and_column(int(row), int(column))
    
    def approximation(self, latitude, longitude):
        """
        Dummy approximation with nearest points. The nearest the neighbour the 
        more important will be its elevation.
        """
        d = 1. / self.square_side
        d_meters = d * mod_utils.ONE_DEGREE

        # Since the less the distance => the more important should be the 
        # distance of the point, we'll use d-distance as importance coef 
        # here:
        importance_1 = d_meters - mod_utils.distance(latitude + d, longitude, latitude, longitude)
        elevation_1  = self.geo_elevation_data.get_elevation(latitude + d, longitude, approximate=False)

        importance_2 = d_meters - mod_utils.distance(latitude - d, longitude, latitude, longitude)
        elevation_2  = self.geo_elevation_data.get_elevation(latitude - d, longitude, approximate=False)

        importance_3 = d_meters - mod_utils.distance(latitude, longitude + d, latitude, longitude)
        elevation_3  = self.geo_elevation_data.get_elevation(latitude, longitude + d, approximate=False)

        importance_4 = d_meters - mod_utils.distance(latitude, longitude - d, latitude, longitude)
        elevation_4  = self.geo_elevation_data.get_elevation(latitude, longitude - d, approximate=False)
        # TODO(TK) Check if coordinates inside the same file, and only the decide if to xall 
        # self.geo_elevation_data.get_elevation or just self.get_elevation

        if elevation_1 == None or elevation_2 == None or elevation_3 == None or elevation_4 == None:
            elevation = self.get_elevation(latitude, longitude, approximate=False)
            if not elevation:
                return None
            elevation_1 = elevation_1 or elevation
            elevation_2 = elevation_2 or elevation
            elevation_3 = elevation_3 or elevation
            elevation_4 = elevation_4 or elevation

        # Normalize importance:
        sum_importances = float(importance_1 + importance_2 + importance_3 + importance_4)

        # Check normallization:
        assert abs(importance_1 / sum_importances + \
                   importance_2 / sum_importances + \
                   importance_3 / sum_importances + \
                   importance_4 / sum_importances - 1 ) < 0.000001

        result = importance_1 / sum_importances * elevation_1 + \
               importance_2 / sum_importances * elevation_2 + \
               importance_3 / sum_importances * elevation_3 + \
               importance_4 / sum_importances * elevation_4

        return result

    def get_elevation_from_row_and_column(self, row, column):
        i = row * (self.square_side) + column
        assert i < len(self.data) - 1

        #logging.debug('{0}, {1} -> {2}'.format(row, column, i))
        byte_1 = self.data[i * 2]
        byte_2 = self.data[i * 2 + 1]

        result = byte_1 * 256 + byte_2

        if result > 9000:
            # TODO(TK) try to detect the elevation from neighbour point:
            return None

        return result

    def parse_file_name_starting_position(self):
        """ Returns (latitude, longitude) of lower left point of the file """
        groups = re.findall('([NS])(\d+)([EW])(\d+)\.hgt', self.file_name)

        assert groups and len(groups) == 1 and len(groups[0]) == 4, 'Invalid file name {0}'.format(self.file_name)

        groups = groups[0]

        if groups[0] == 'N':
            latitude = float(groups[1])
        else:
            latitude = - float(groups[1])

        if groups[2] == 'E':
            longitude = float(groups[3])
        else:
            longitude = - float(groups[3])

        self.latitude = latitude
        self.longitude = longitude
	
    def __str__(self):
        return '[{0}:{1}]'.format(self.__class__, self.file_name)
