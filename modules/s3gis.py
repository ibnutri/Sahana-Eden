# -*- coding: utf-8 -*-

"""
    SahanaPy GIS Module

    @version: 0.0.4
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @author: Fran Boon <francisboon@gmail.com>
    @author: Timothy Caro-Bruce <tcarobruce@gmail.com>
    @author: Zubin Mithra <zubin.mithra@gmail.com>
    @copyright: (c) 2010 Sahana Software Foundation
    @license: MIT
    
    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__name__ = "S3GIS"

__all__ = ['GIS', 'GoogleGeocoder', 'YahooGeocoder']

import sys, uuid
import logging                                                    
from urllib import urlencode                                      

from gluon.storage import Storage, Messages
from gluon.tools import fetch                                     

SHAPELY = False
try:
    import shapely
    import shapely.geometry
    from shapely.wkt import loads as wkt_loads
    SHAPELY = True
except ImportError:
    print >> sys.stderr, "WARNING: %s: Shapely GIS library not installed" % __name__

# Map WKT types to db types (multi-geometry types are mapped to single types)
GEOM_TYPES = {
    "point": 1,
    "multipoint": 1,
    "linestring": 2,
    "multilinestring": 2,
    "polygon": 3,
    "multipolygon": 3,
}

class GIS(object):
    """ GIS functions """

    def __init__(self, environment, db):
        self.environment = Storage(environment)
        assert db is not None, "Database must not be None."
        self.db = db
        self.messages = Messages(None)
        #self.messages.centroid_error = str(A('Shapely', _href='http://pypi.python.org/pypi/Shapely/', _target='_blank')) + " library not found, so can't find centroid!"
        self.messages.centroid_error = "Shapely library not functional, so can't find centroid! Install Geos & Shapely for Line/Polygon support"
        self.messages.unknown_type = "Unknown Type!"
        self.messages.invalid_wkt_linestring = "Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!"
        self.messages.invalid_wkt_polygon = "Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!"
        self.messages.lon_empty = "Invalid: Longitude can't be empty if Latitude specified!"
        self.messages.lat_empty = "Invalid: Latitude can't be empty if Longitude specified!"
        self.messages.unknown_parent = "Invalid: %(parent_id)s is not a known Location"
        self.messages['T'] = self.environment.T
        self.messages.lock_keys = True
        
    def read_config(self):
        """
            Reads the current GIS Config from the DB 
        """
        
        db = self.db
                
        config = db(db.gis_config.id == 1).select().first()
        
        return config
        
    def get_feature_class_id_from_name(self, name):
        """
            Returns the Feature Class ID from it's name
        """

        db = self.db
        
        feature = db(db.gis_feature_class.name == name).select()
        if feature:
            return feature[0].id
        else:
            return None
    
    def get_marker(self, feature_id):
        """
            Returns the Marker URL for a Feature
        """

        db = self.db
        
        config = self.read_config()
        symbology = config.symbology_id
        
        feature = db(db.gis_location.id == feature_id).select().first()
        #feature_class = db(db.gis_feature_class.id == feature.feature_class_id).select().first().id
        feature_class = feature.feature_class_id
        
        # 1st choice for a Marker is the Feature's
        marker = feature.marker_id
        if not marker:
            # 2nd choice for a Marker is the Symbology for the Feature Class
            query = (db.gis_symbology_to_feature_class.feature_class_id == feature_class) & (db.gis_symbology_to_feature_class.symbology_id == symbology)
            try:
                marker = db(query).select().first().marker_id
            except:
                if not marker:
                    # 3rd choice for a Marker is the Feature Class's
                    marker = db(db.gis_feature_class.id == feature_class).select().first()
                    if marker:
                        marker = marker.marker_id
                if not marker:
                    # 4th choice for a Marker is the default
                    marker = config.marker_id
        
        marker = db(db.gis_marker.id == marker).select().first().image
        
        return marker
    
    def get_bounds(self, features=[]):
        """
            Calculate the Bounds of a list of Features
            e.g. to use in GPX export for correct zooming
        """
        # If we have a list of features, then use this to build the bounds
        if features:
            min_lon = 180
            min_lat = 90
            max_lon = -180
            max_lat = -90
            for feature in features:
                if feature.lon > max_lon:
                    max_lon = feature.lon
                if feature.lon < min_lon:
                    min_lon = feature.lon
                if feature.lat > max_lat:
                    max_lat = feature.lat
                if feature.lat < min_lat:
                    min_lat = feature.lat
            # Check that we're still within overall bounds
            config = self.read_config()
            if min_lon < config.min_lon:
                min_lon = config.min_lon
            if min_lat < config.min_lat:
                min_lat = config.min_lat
            if max_lon > config.max_lon:
                max_lon = config.max_lon
            if max_lat > config.max_lat:
                max_lat = config.max_lat
        
        else:
            # Read from config
            config = self.read_config()
            min_lon = config.min_lon
            min_lat = config.min_lat
            max_lon = config.max_lon
            max_lat = config.max_lat
        
        return dict(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    def update_location_tree(self):
        """
            Update the Tree for GIS Locations:
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        """

        db = self.db
        
        # tbc
        
        return

    def get_children(self, parent_id):
        "Return a list of all GIS Features which are children of the requested parent"
        
        db = self.db
        
        # Switch to modified preorder tree traversal:
        # http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        children = db(db.gis_location.parent == parent_id).select()
        for child in children:
            children = children & self.get_children(child.id)

        return children
    
    def bbox_intersects(self, lon_min, lat_min, lon_max, lat_max):
        db = self.db
        return db((db.gis_location.lat_min <= lat_max) & 
            (db.gis_location.lat_max >= lat_min) &
            (db.gis_location.lon_min <= lon_max) & 
            (db.gis_location.lon_max >= lon_min))
    
    def _intersects(self, shape):
        """
            Returns Rows of locations whose shape intersects the given shape
        """
        
        db = self.db
        for loc in self.bbox_intersects(*shape.bounds).select():
            location_shape = wkt_loads(loc.wkt)
            if location_shape.intersects(shape):
                yield loc
    
    def _intersects_latlon(self, lat, lon):
        """
            Returns a generator of locations whose shape intersects the given LatLon
        """    
        
        point = shapely.geometry.point.Point(lon, lat)
        return self.intersects(point)
    
    if SHAPELY:
        intersects = _intersects
        intersects_latlon = _intersects_latlon 
    
    def parse_location(self, wkt, lon=None, lat=None):
        """
            Parses a location from wkt, returning wkt, lat, lon, bounding box and type.
            For points, wkt may be None if lat and lon are provided; wkt will be generated.
            For lines and polygons, the lat, lon returned represent the shape's centroid.
            Centroid and bounding box will be None if shapely is not available.
        """
        
        if not wkt:
            assert lon is not None and lat is not None, "Need wkt or lon+lat to parse a location"
            wkt = 'POINT(%f %f)' % (lon, lat)
            geom_type = GEOM_TYPES['point']
            bbox = (lon, lat, lon, lat)
        else:
            if SHAPELY:
                shape = shapely.wkt.loads(wkt)
                centroid = shape.centroid
                lat = centroid.y
                lon = centroid.x
                geom_type = GEOM_TYPES[shape.type.lower()]
                bbox = shape.bounds
            else:
                lat = None
                lon = None
                geom_type = GEOM_TYPES[wkt.split('(')[0].lower()]
                bbox = None
                
        res = {'wkt': wkt, 'lat': lat, 'lon': lon, 'gis_feature_type': geom_type}
        if bbox:
            res['lon_min'], res['lat_min'], res['lon_max'], res['lat_max'] = bbox
        
        return res

    def abbreviate_wkt(self, wkt, max_length=30):
        if len(wkt) > max_length:
            return "%s(...)" % wkt[0:wkt.index('(')]
        return wkt
        
    def latlon_to_wkt(self, lat, lon):
        """
            Convert a LatLon to a WKT string
        
            >>> s3gis.latlon_to_wkt(6, 80)
            'POINT(80 6)'
        """
        WKT = 'POINT(%f %f)' % (lon, lat)
        return WKT

    def wkt_centroid(self, form):
        """
            OnValidation callback:
            If a Point has LonLat defined: calculate the WKT.
            If a Line/Polygon has WKT defined: validate the format & calculate the LonLat of the Centroid
            Centroid calculation is done using Shapely, which wraps Geos.
            A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm
        """
        
        if form.vars.gis_feature_type == '1':
            # Point
            if form.vars.lon == None and form.vars.lat == None:
                # No geo to create WKT from, so skip
                return
            elif form.vars.lat == None:
                form.errors['lat'] = self.messages.lat_empty
                return
            elif form.vars.lon == None:
                form.errors['lon'] = self.messages.lon_empty
                return
            else:
                form.vars.wkt = 'POINT(%(lon)f %(lat)f)' % form.vars
                return
            
        elif form.vars.gis_feature_type == '2':
            # Line
            try:
                from shapely.wkt import loads
                try:
                    line = loads(form.vars.wkt)
                except:
                    form.errors['wkt'] = self.messages.invalid_wkt_linestring
                    return
                centroid_point = line.centroid
                form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
                form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
            except:
                form.errors.gis_feature_type = self.messages.centroid_error
        elif form.vars.gis_feature_type == '3':
            # Polygon
            try:
                from shapely.wkt import loads
                try:
                    polygon = loads(form.vars.wkt)
                except:
                    form.errors['wkt'] = self.messages.invalid_wkt_polygon
                    return
                centroid_point = polygon.centroid
                form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
                form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
            except:
                form.errors.gis_feature_type = self.messages.centroid_error

        else:
            form.errors.gis_feature_type = self.messages.unknown_type
        
        return

    def bearing(lat_start, lon_start, lat_end, lon_end):
        """
            Given a Start & End set of Coordinates, return a Bearing
            Formula from: http://www.movable-type.co.uk/scripts/latlong.html
        """
        
        import math
        
        delta_lon = lon_start - lon_end
        bearing = math.atan2( math.sin(delta_lon)*math.cos(lat_end) , (math.cos(lat_start)*math.sin(lat_end)) - (math.sin(lat_start)*math.cos(lat_end)*math.cos(delta_lon)) )
        # Convert to a compass bearing
        bearing = (bearing + 360) % 360
        
        return bearing

    def get_features_in_radius(lat, lon, radius):
        """
            Returns Features within a Radius (in km) of a LatLon Location
            Calling function has the job of filtering features by the type they are interested in
            Formula from: http://blog.peoplesdns.com/archives/24
            Spherical Law of Cosines (accurate down to around 1m & computationally quick): http://www.movable-type.co.uk/scripts/latlong.html
            
            IF PROJECTION CHANGES THIS WILL NOT WORK
        """
        
        import math
        
        # km
        radius_earth = 6378.137
        pi = math.pi

        # ToDo: Do a Square query 1st & then run the complex query over subset (to improve performance)
        lat_max = 90
        lat_min = -90
        lon_max = 180
        lon_min = -180
        table = db.gis_location
        query = (table.lat > lat_min) & (table.lat < lat_max) & (table.lon < lon_max) & (table.lon > lon_min)
        deleted = ((table.deleted==False) | (table.deleted==None))
        query = deleted & query
        
        # ToDo: complete port from PHP to Eden
        pilat180 = pi * lat /180
        #calc = "radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180)) + (math.cos(pilat180) * math.cos(pi*table.lat/180) * math.cos(pi * table.lon/180-pi* lon /180)))"
        #query2 = "SELECT DISTINCT table.lon, table.lat, calc AS distance FROM table WHERE calc <= radius ORDER BY distance"
        #query2 = (radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180)) + (math.cos(pilat180) * math.cos(pi*table.lat/180) * math.cos(pi * table.lon/180-pi* lon /180))) < radius)
        # TypeError: unsupported operand type(s) for *: 'float' and 'Field'
        query2 = (radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180))) < radius)
        #query = query & query2
        features = db(query).select()
        #features = db(query).select(orderby=distance)
      
        return features

class Geocoder(object):
    " Base class for all geocoders "
    
    def __init__(self):
        " Initializes the page content object "
        self.page = ""
        
    def read_details(self, url):
        self.page = fetch(url)  

class GoogleGeocoder(Geocoder):
    " Google Geocoder module "
    
    def __init__(self, location, db, domain='maps.google.com', resource='maps/geo', output_format='kml'):
        " Initialize the values based on arguments or default settings "                        
        self.api_key = self.get_api_key()                                                  
        self.domain = domain                                                               
        self.resource = resource                                                           
        self.params = {'q': location, 'key': self.api_key}                                 
        self.url = "http://%(domain)s/%(resource)?%%s" % locals()                          
        self.db = db                                                                       

    def get_api_key(self):
        " Acquire API key from the database "
        query = self.db.gis_apikey.name=='google'                          
        return self.db(query).select().first().apikey                      

    def construct_url(self):
        " Construct the URL based on the arguments passed "
        self.url = self.url % urlencode(params)
    
    def get_kml(self):
        " Returns the output in KML format " 
        return self.page.read()                

class YahooGeocoder(Geocoder):
    " Yahoo Geocoder module "
    
    def __init__(self, location, db):
        " Initialize the values based on arguments or default settings "
        self.api_key = self.get_api_key()
        self.location = location
        self.params = {'location': self.location, 'appid': self.app_key}
        self.db = db
        
    def get_api_key(self):
        " Acquire API key from the database "
        query = self.db.gis_apikey.name=='yahoo'
        return self.db(query).select().first().apikey

    def construct_url(self):
        " Construct the URL based on the arguments passed "
        self.url = self.url % urlencode(params)

    def get_xml(self):
        " Return the output in XML format "
        return self.page.read()        
