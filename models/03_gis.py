# -*- coding: utf-8 -*-

"""
    GIS
"""

module = "gis"

MARKER = Tstr("Marker")

# Settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

# GIS Markers (Icons)
resource = "marker"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                #uuidstamp, # Markers don't sync
                Field("name", length=128, notnull=True, unique=True),
                #Field("height", "integer"), # In Pixels, for display purposes
                #Field("width", "integer"),  # Not needed since we get size client-side using Javascript's Image() class
                Field("image", "upload", autodelete = True),
                migrate=migrate)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "static/img/markers")
table.image.represent = lambda filename: (filename and [DIV(IMG(_src=URL(r=request, c="default", f="download", args=filename), _height=40))] or [""])[0]
table.name.label = T("Name")
table.image.label = T("Image")

# Reusable field to include in other table definitions
ADD_MARKER = Tstr("Add") + " " + MARKER
marker_id = db.Table(None, "marker_id",
            FieldS3("marker_id", db.gis_marker, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_marker.id", "%(name)s", zero=T("Use default from feature class"))),
                represent = lambda id: (id and [DIV(IMG(_src=URL(r=request, c="default", f="download", args=db(db.gis_marker.id == id).select(db.gis_marker.image, limitby=(0, 1)).first().image), _height=40))] or [""])[0],
                label = T("Marker"),
                comment = DIV(A(ADD_MARKER, _class="colorbox", _href=URL(r=request, c="gis", f="marker", args="create", vars=dict(format="popup")), _target="top", _title=ADD_MARKER),
                          DIV( _class="tooltip", _title=MARKER + "|" + Tstr("Defines the icon used for display of features on interactive map & KML exports. A Marker assigned to an individual Location is set if there is a need to override the Marker assigned to the Feature Class. If neither are defined, then the Default Marker is used."))),
                ondelete = "RESTRICT"
                ))

# GIS Projections
resource = "projection"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                Field("name", length=128, notnull=True, unique=True),
                Field("epsg", "integer", notnull=True),
                Field("maxExtent", length=64, notnull=True),
                Field("maxResolution", "double", notnull=True),
                Field("units", notnull=True),
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.epsg.requires = IS_NOT_EMPTY()
table.maxExtent.requires = IS_NOT_EMPTY()
table.maxResolution.requires = IS_NOT_EMPTY()
table.units.requires = IS_IN_SET(["m", "degrees"], zero=None)
table.name.label = T("Name")
table.epsg.label = "EPSG"
table.maxExtent.label = T("maxExtent")
table.maxResolution.label = T("maxResolution")
table.units.label = T("Units")
# Reusable field to include in other table definitions
projection_id = db.Table(None, "projection_id",
            FieldS3("projection_id", db.gis_projection, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_projection.id", "%(name)s")),
                represent = lambda id: db(db.gis_projection.id == id).select(db.gis_projection.name, limitby=(0, 1)).first().name,
                label = T("Projection"),
                comment = "",
                ondelete = "RESTRICT"
                ))

# GIS Symbology
resource = "symbology"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                Field("name", length=128, notnull=True, unique=True),
                migrate=migrate)
# Reusable field to include in other table definitions
symbology_id = db.Table(None, "symbology_id",
            FieldS3("symbology_id", db.gis_symbology, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_symbology.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_symbology.id == id).select(db.gis_symbology.name, limitby=(0, 1)).first().name] or ["None"])[0],
                label = T("Symbology"),
                comment = "",
                ondelete = "RESTRICT"
                ))

# GIS Config
gis_config_layout_opts = {
    1:T("window"),
    2:T("embedded")
    }
opt_gis_layout = db.Table(None, "opt_gis_layout",
                    Field("opt_gis_layout", "integer",
                        requires = IS_IN_SET(gis_config_layout_opts, zero=None),
                        default = 1,
                        label = T("Layout"),
                        represent = lambda opt: gis_config_layout_opts.get(opt, UNKNOWN_OPT)))
# id=1 = Default settings
# separated from Framework settings above
# ToDo Extend for per-user Profiles - this is the WMC
resource = "config"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                pe_id,                           # Personal Entity Reference
                Field("lat", "double"),
                Field("lon", "double"),
                Field("zoom", "integer"),
                projection_id,
                symbology_id,
                marker_id,
                Field("map_height", "integer", notnull=True),
                Field("map_width", "integer", notnull=True),
                Field("min_lon", "double", default=-180),
                Field("min_lat", "double", default=-90),
                Field("max_lon", "double", default=180),
                Field("max_lat", "double", default=90),
                Field("zoom_levels", "integer", default=16, notnull=True),
                Field("cluster_distance", "integer", default=5, notnull=True),
                Field("cluster_threshold", "integer", default=2, notnull=True),
                opt_gis_layout,
                migrate=migrate)

table.uuid.requires = IS_NOT_IN_DB(db, "gis_config.uuid")
table.pe_id.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent))
table.pe_id.readable = table.pe_id.writable = False
table.lat.requires = IS_LAT()
table.lon.requires = IS_LON()
table.zoom.requires = IS_INT_IN_RANGE(0, 19)
table.map_height.requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(160, 1024)]
table.map_width.requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(320, 1280)]
table.min_lat.requires = IS_LAT()
table.max_lat.requires = IS_LAT()
table.min_lon.requires = IS_LON()
table.max_lon.requires = IS_LON()
table.zoom_levels.requires = IS_INT_IN_RANGE(1, 30)
table.cluster_distance.requires = IS_INT_IN_RANGE(1, 30)
table.cluster_threshold.requires = IS_INT_IN_RANGE(1, 10)
table.lat.label = T("Latitude")
table.lon.label = T("Longitude")
table.zoom.label = T("Zoom")
table.marker_id.label = T("Default Marker")
table.map_height.label = T("Map Height")
table.map_width.label = T("Map Width")
table.zoom_levels.label = T("Zoom Levels")
table.cluster_distance.label = T("Cluster Distance")
table.cluster_threshold.label = T("Cluster Threshold")
# Defined here since Component
table.lat.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Latitude") + "|" + Tstr("Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
table.lon.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Longitude") + "|" + Tstr("Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
table.zoom.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Zoom") + "|" + Tstr("How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))
table.map_height.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Height") + "|" + Tstr("Default Height of the map window. In Window layout the map maximises to fill the window, so no need to set a large value here.")))
table.map_width.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("Width") + "|" + Tstr("Default Width of the map window. In Window layout the map maximises to fill the window, so no need to set a large value here.")))
ADD_CONFIG = T("Add Config")
LIST_CONFIGS = T("List Configs")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_CONFIG,
    title_display = T("Config"),
    title_list = T("Configs"),
    title_update = T("Edit Config"),
    title_search = T("Search Configs"),
    subtitle_create = T("Add New Config"),
    subtitle_list = LIST_CONFIGS,
    label_list_button = LIST_CONFIGS,
    label_create_button = ADD_CONFIG,
    label_delete_button = T("Delete Config"),
    msg_record_created = T("Config added"),
    msg_record_modified = T("Config updated"),
    msg_record_deleted = T("Config deleted"),
    msg_list_empty = T("No Configs currently defined")
)

# Configs as component of Persons
s3xrc.model.add_component(module, resource,
                          multiple=False,
                          joinby="pe_id",
                          deletable=False,
                          editable=True)

s3xrc.model.configure(table,
                      list_fields = ["lat",
                                     "lon",
                                     "zoom",
                                     "projection_id",
                                     "map_height",
                                     "map_width"])
# GIS Feature Classes
# These are used in groups (for display/export), for icons & for URLs to edit data
#gis_resource_opts = {
#        "shelter":T("Shelter"),
#        "office":T("Office"),
#        "track":T("Track"),
#        "image":T("Photo"),
#        }
resource = "feature_class"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                Field("description"),
                marker_id,
                Field("gps_marker"),
                Field("module"),    # Used to build Edit URL
                Field("resource"),  # Used to build Edit URL & to provide Attributes to Display
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.gps_marker.requires = IS_IN_SET([
    "Airport",
    "Amusement Park"
    "Ball Park",
    "Bank",
    "Bar",
    "Beach",
    "Bell",
    "Boat Ramp",
    "Bowling",
    "Bridge",
    "Building",
    "Campground",
    "Car",
    "Car Rental",
    "Car Repair",
    "Cemetery",
    "Church",
    "Circle with X",
    "City (Capitol)",
    "City (Large)",
    "City (Medium)",
    "City (Small)",
    "Civil",
    "Controlled Area",
    "Convenience Store",
    "Crossing",
    "Dam",
    "Danger Area",
    "Department Store",
    "Diver Down Flag 1",
    "Diver Down Flag 2",
    "Drinking Water",
    "Exit",
    "Fast Food",
    "Fishing Area",
    "Fitness Center",
    "Flag",
    "Forest",
    "Gas Station",
    "Geocache",
    "Geocache Found",
    "Ghost Town",
    "Glider Area",
    "Golf Course",
    "Green Diamond",
    "Green Square",
    "Heliport",
    "Horn",
    "Hunting Area",
    "Information",
    "Levee",
    "Light",
    "Live Theater",
    "Lodging",
    "Man Overboard",
    "Marina",
    "Medical Facility",
    "Mile Marker",
    "Military",
    "Mine",
    "Movie Theater",
    "Museum",
    "Navaid, Amber",
    "Navaid, Black",
    "Navaid, Blue",
    "Navaid, Green",
    "Navaid, Green/Red",
    "Navaid, Green/White",
    "Navaid, Orange",
    "Navaid, Red",
    "Navaid, Red/Green",
    "Navaid, Red/White",
    "Navaid, Violet",
    "Navaid, White",
    "Navaid, White/Green",
    "Navaid, White/Red",
    "Oil Field",
    "Parachute Area",
    "Park",
    "Parking Area",
    "Pharmacy",
    "Picnic Area",
    "Pizza",
    "Post Office",
    "Private Field",
    "Radio Beacon",
    "Red Diamond",
    "Red Square",
    "Residence",
    "Restaurant",
    "Restricted Area",
    "Restroom",
    "RV Park",
    "Scales",
    "Scenic Area",
    "School",
    "Seaplane Base",
    "Shipwreck",
    "Shopping Center",
    "Short Tower",
    "Shower",
    "Skiing Area",
    "Skull and Crossbones",
    "Soft Field",
    "Stadium",
    "Summit",
    "Swimming Area",
    "Tall Tower",
    "Telephone",
    "Toll Booth",
    "TracBack Point",
    "Trail Head",
    "Truck Stop",
    "Tunnel",
    "Ultralight Area",
    "Water Hydrant",
    "Waypoint",
    "White Buoy",
    "White Dot",
    "Zoo"
    ])
#table.module.requires = IS_NULL_OR(IS_ONE_OF(db((db.s3_module.enabled=="True") & (~db.s3_module.name.like("default"))), "s3_module.name", "%(name_nice)s"))
#table.resource.requires = IS_NULL_OR(IS_IN_SET(gis_resource_opts))
table.name.label = T("Name")
table.gps_marker.label = T("GPS Marker")
table.description.label = T("Description")
table.module.label = T("Module")
table.resource.label = T("Resource")

# Reusable field to include in other table definitions
ADD_FEATURE_CLASS = T("Add Feature Class")
feature_class_id = db.Table(None, "feature_class_id",
            FieldS3("feature_class_id", db.gis_feature_class, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_feature_class.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_feature_class.id == id).select(db.gis_feature_class.name, limitby=(0, 1)).first().name] or ["None"])[0],
                label = T("Feature Class"),
                comment = DIV(A(ADD_FEATURE_CLASS, _class="colorbox", _href=URL(r=request, c="gis", f="feature_class", args="create", vars=dict(format="popup")), _target="top", _title=ADD_FEATURE_CLASS),
                          DIV( _class="tooltip", _title=Tstr("Feature Class") + "|" + Tstr("Defines the marker used for display & the attributes visible in the popup."))),
                ondelete = "RESTRICT"
                ))

# Symbology to Feature Class to Marker
resource = "symbology_to_feature_class"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                symbology_id,
                feature_class_id,
                marker_id,
                migrate=migrate)

# GIS Locations
gis_feature_type_opts = {
    1:T("Point"),
    2:T("Line"),
    3:T("Polygon"),
    #4:T("MultiPolygon")
    }
gis_source_opts = {
    1:T("GPS"),
    2:T("Imagery"),
    3:T("Wikipedia"),
    }
gis_location_hierarchy = {
    "L0":T("Country"),
    "L1":T("Region"),
    "L2":T("District"),
    "L3":T("Town"),
    "L4":T("Village")
}
# Expose this to Views for AutoCompletes
response.s3.gis.location_hierarchy = gis_location_hierarchy
gis_location_languages = {
    1:T("English"),
    2:T("Urdu"),
    3:T("Punjabi"),
    4:T("Pashto"),
    5:T("Sindhi"),
    6:T("Seraiki"),
    7:T("Balochi"),
    #3:T("Local Language"),
}
gis_location_language_default = 1
resource = "location"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", notnull=True),    # Primary name
                Field("name_l10n"),             # Local Names are stored in this field
                Field("name_dummy"),            # Dummy field to provide Widget
                Field("code"),
                feature_class_id,       # Will be removed
                marker_id,              # Will be removed
                Field("level", length=2),
                Field("parent", "reference gis_location", ondelete = "RESTRICT"),   # This form of hierarchy may not work on all Databases
                Field("lft", "integer", readable=False, writable=False), # Left will be for MPTT: http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
                Field("rght", "integer", readable=False, writable=False),# Right currently unused
                # Street Address (other address fields come from hierarchy)
                Field("addr_street"),
                #Field("addr_postcode"),
                Field("gis_feature_type", "integer", default=1, notnull=True),
                Field("lat", "double"), # Points or Centroid for Polygons
                Field("lon", "double"), # Points or Centroid for Polygons
                Field("wkt", "text"),   # WKT is auto-calculated from lat/lon for Points
                Field("url"),
                Field("osm_id"),        # OpenStreetMap ID. Should this be used in UUID field instead?
                Field("lon_min", "double", writable=False, readable=False), # bounding-box
                Field("lat_min", "double", writable=False, readable=False), # bounding-box
                Field("lon_max", "double", writable=False, readable=False), # bounding-box
                Field("lat_max", "double", writable=False, readable=False), # bounding-box
                Field("elevation", "integer", writable=False, readable=False),   # m in height above WGS84 ellipsoid (approximately sea-level). not displayed currently
                Field("ce", "integer", writable=False, readable=False), # Circular 'Error' around Lat/Lon (in m). Needed for CoT.
                Field("le", "integer", writable=False, readable=False), # Linear 'Error' for the Elevation (in m). Needed for CoT.
                Field("source", "integer"),
                comments,
                migrate=migrate)

table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)
table.name.requires = IS_NOT_EMPTY()    # Placenames don't have to be unique
table.name.label = T("Primary Name")
# We never access name_l10n directly
table.name_l10n.readable = False
table.name_l10n.writable = False
table.name_dummy.label = T("Local Names")
table.name_dummy.comment = DIV(_class="tooltip", _title=Tstr("Local Names") + "|" + Tstr("Names can be added in multiple languages"))
table.level.requires = IS_NULL_OR(IS_IN_SET(gis_location_hierarchy))
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.gis_location.id == id).select(db.gis_location.name, limitby=(0, 1)).first().name] or ["None"])[0]
table.gis_feature_type.requires = IS_IN_SET(gis_feature_type_opts, zero=None)
table.gis_feature_type.represent = lambda opt: gis_feature_type_opts.get(opt, UNKNOWN_OPT)
# WKT validation is done in the onvalidation callback
#table.wkt.requires = IS_NULL_OR(IS_WKT())
table.wkt.represent = lambda wkt: gis.abbreviate_wkt(wkt)
table.lat.requires = IS_NULL_OR(IS_LAT())
table.lon.requires = IS_NULL_OR(IS_LON())
table.url.requires = IS_NULL_OR(IS_URL())
table.source.requires = IS_NULL_OR(IS_IN_SET(gis_source_opts))
table.level.label = T("Level")
table.code.label = T("Code")
table.parent.label = T("Parent")
table.addr_street.label = T("Street Address")
table.gis_feature_type.label = T("Feature Type")
table.lat.label = T("Latitude")
table.lon.label = T("Longitude")
table.wkt.label = T("Well-Known Text")
table.url.label = "URL"
table.osm_id.label = "OpenStreetMap"

# Reusable field to include in other table definitions
ADD_LOCATION = T("Add Location")
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name
location_id = db.Table(None, "location_id",
                       FieldS3("location_id", db.gis_location, sortby="name",
                       requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", repr_select, sort=True)),
                       represent = lambda id: shn_gis_location_represent(id),
                       label = T("Location"),
                       comment = DIV(A(ADD_LOCATION,
                                       _class="colorbox",
                                       _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
                                       _target="top",
                                       _title=ADD_LOCATION),
                                     DIV( _class="tooltip",
                                       _title=Tstr("Location") + "|" + Tstr("The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                       ondelete = "RESTRICT"))

# Expose the default country to Views for Autocompletes
if response.s3.country:
    response.s3.gis.country = db(db.gis_location.code == response.s3.country).select(db.gis_location.id, limitby=(0, 1)).first().id

# -----------------------------------------------------------------------------
def get_location_id (field_name = "location_id", 
                     label = T("Location"),
                     filterby = None,
                     filter_opts = None,
                     editable = True):
    """
    @author Michael Howden
    
    Function for creating a location field with a customisable field_name/label
    
    @ToDo: more functionality from this function to port from ADPC Branch
    """
    
    requires = location_id.location_id.requires
    
    comment = location_id.location_id.comment
    comment[0].attributes['_href'] = URL(r=request, 
                                         c="gis", 
                                         f="location", 
                                         args="create", 
                                         vars=dict(format="popup", child=field_name)
                                        )
    
    return db.Table(None, 
                    field_name,
                    FieldS3(field_name, 
                            db.gis_location, sortby="name",
                            requires = requires,
                            represent = shn_gis_location_represent,
                            label = label,
                            comment = comment,
                            ondelete = "RESTRICT"
                            )
                    )
# -----------------------------------------------------------------------------
# Locations as component of Locations ('Parent')
s3xrc.model.add_component(module, resource,
                          multiple=False,
                          joinby=dict(gis_location="location_id"),
                          deletable=True,
                          editable=True)

resource = "location_name"
tablename = module + "_" + resource
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                location_id,
                Field("name_l10n"),
                Field("language", "integer"),
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
table.name_l10n.label = T("Name")
table.language.requires = IS_IN_SET(gis_location_languages)
table.language.represent = lambda opt: gis_location_languages.get(opt, UNKNOWN_OPT)
table.language.label = T("Language")

s3xrc.model.add_component(module, resource, joinby=dict(gis_location="location_id"), multiple=True)

# Multiselect Widget
name_dummy_element = S3MultiSelectWidget(db = db,
                                         link_table_name = tablename,
                                         link_field_name = "location_id")
table = db.gis_location
table.name_dummy.widget = name_dummy_element.widget
table.name_dummy.represent = name_dummy_element.represent
def gis_location_onaccept(form):
    if session.rcvars and hasattr(name_dummy_element, "onaccept"):
        # HTML UI, not XML import
        name_dummy_element.onaccept(db, session.rcvars.gis_location, request)
    else:
        location_id = form.vars.id
        table = db.gis_location_name
        names = db(table.location_id==location_id).select(table.id)
        if names:
            ids = [str(name.id) for name in names]
            #name_dummy = "|%s|" % "|".join(ids)
            name_dummy = "|".join(ids) # That's not how it should be
            table = db.gis_location
            db(table.id==location_id).update(name_dummy=name_dummy)
    # Include the normal onaccept
    gis.update_location_tree()

s3xrc.model.configure(table,
                      onvalidation=lambda form: gis.wkt_centroid(form),
                      onaccept=gis_location_onaccept)

# -----------------------------------------------------------------------------
#
def shn_gis_location_represent(id):
    try:
        location = db(db.gis_location.id == id).select(db.gis_location.name, db.gis_location.level, db.gis_location.lat, db.gis_location.lon, db.gis_location.id, limitby=(0, 1)).first()
        if location.level in ["L0", "L1", "L2"]:
            # Countries, Regions shouldn't be represented as Lat/Lon
            text = location.name
        else:
            # Simple
            #represent = location.name
            # Lat/Lon
            lat = location.lat
            lon = location.lon
            if lat and lon:
                if lat > 0:
                    lat_prefix = "N"
                else:
                    lat_prefix = "S"
                if lon > 0:
                    lon_prefix = "E"
                else:
                    lon_prefix = "W"
                text = location.name + " (%s %s %s %s)" % (lat_prefix, lat, lon_prefix, lon)
            else:
                text = location.name
        # Simple
        #represent = text
        # Hyperlink
        #represent = A(text, _href = deployment_settings.get_base_public_url() + URL(r=request, c="gis", f="location", args=[location.id]))
        # Map
        represent = A(text, _href="#", _onclick="viewMap(" + str(id) +");return false")
        # ToDo: Convert to popup? (HTML again!)
    except:
        try:
            # "Invalid" => data consistency wrong
            represent = location.id
        except:
            represent = None
    return represent

# Feature Layers
# Used to select a set of Features for either Display or Export
# (replaces feature_group)
resource = "feature_layer"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                Field("resource"),              # Used to build a simple query
                Field("filter_field"),          # Used to build a simple query
                Field("filter_value"),          # Used to build a simple query
                Field("query", notnull=True),
                marker_id,                      # Optional Marker to over-ride the values from the Feature Classes
                comments,
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#table.author.requires = IS_ONE_OF(db, "auth_user.id","%(id)s: %(first_name)s %(last_name)s")
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.resource.label = T("Resource")
# In zzz_last.py
#table.resource.requires = IS_IN_SET(db.tables)
table.filter_field.label = T("Filter Field")
table.filter_value.label = T("Filter Value")
table.query.label = T("Query")

# Feature Groups
# Used to select a set of Feature Classes for either Display or Export
# This is being deprecated by feature_layer
resource = "feature_group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                Field("description"),
                Field("enabled", "boolean", default=True, label=T("Enabled?")),
                Field("visible", "boolean", default=False, label=T("On by default?")),
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#table.author.requires = IS_ONE_OF(db, "auth_user.id","%(id)s: %(first_name)s %(last_name)s")
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.description.label = T("Description")
# Reusable field to include in other table definitions
ADD_FEATURE_GROUP = T("Add Feature Group")
feature_group_id = db.Table(None, "feature_group_id",
            FieldS3("feature_group_id", db.gis_feature_group, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_feature_group.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_feature_group.id == id).select(db.gis_feature_group.name, limitby=(0, 1)).first().name] or ["None"])[0],
                label = T("Feature Group"),
                comment = DIV(A(ADD_FEATURE_GROUP, _class="colorbox", _href=URL(r=request, c="gis", f="feature_group", args="create", vars=dict(format="popup")), _target="top", _title=ADD_FEATURE_GROUP),
                          DIV( _class="tooltip", _title=Tstr("Feature Group") + "|" + Tstr("A collection of Feature Classes which can be displayed together on a map or exported together."))),
                ondelete = "RESTRICT"
                ))

# Many-to-Many tables
# No longer supported
#resource = "location_to_feature_group"
#tablename = "%s_%s" % (module, resource)
#table = db.define_table(tablename, timestamp, deletion_status,
#                feature_group_id,
#                location_id,
#                migrate=migrate)

# This is being deprecated by feature_layer
resource = "feature_class_to_feature_group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, deletion_status,
                feature_group_id,
                feature_class_id,
                migrate=migrate)

# GIS Keys - needed for commercial mapping services
resource = "apikey" # Can't use 'key' as this has other meanings for dicts!
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                Field("name", notnull=True),
                Field("apikey", length=128, notnull=True),
                Field("description"),
                migrate=migrate)
# FIXME
# We want a THIS_NOT_IN_DB here: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540/fc129fd476558944?lnk=gst&q=THIS_NOT_IN_DB#fc129fd476558944
table.name.requires = IS_IN_SET(["google", "multimap", "yahoo"], zero=None)
#table.apikey.requires = THIS_NOT_IN_DB(db(table.name == request.vars.name), "gis_apikey.name", request.vars.name, "Service already in use")
table.apikey.requires = IS_NOT_EMPTY()
table.name.label = T("Service")
table.apikey.label = T("Key")

# GPS Tracks (files in GPX format)
resource = "track"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                #uuidstamp, # Tracks don't sync
                Field("name", length=128, notnull=True, unique=True),
                Field("description", length=128),
                Field("track", "upload", autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
table.track.uploadfolder = os.path.join(request.folder, "uploads/tracks")
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
table.track.requires = IS_UPLOAD_FILENAME(extension="gpx")
table.track.description = T("Description")
table.track.label = T("GPS Track File")
table.track.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=Tstr("GPS Track") + "|" + Tstr("A file in GPX format taken from a GPS whose timestamps can be correlated with the timestamps on the photos to locate them on the map.")))
ADD_TRACK = T("Upload Track")
LIST_TRACKS = T("List Tracks")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_TRACK,
    title_display = T("Track Details"),
    title_list = LIST_TRACKS,
    title_update = T("Edit Track"),
    title_search = T("Search Tracks"),
    subtitle_create = T("Add New Track"),
    subtitle_list = T("Tracks"),
    label_list_button = LIST_TRACKS,
    label_create_button = ADD_TRACK,
    msg_record_created = T("Track uploaded"),
    msg_record_modified = T("Track updated"),
    msg_record_deleted = T("Track deleted"),
    msg_list_empty = T("No Tracks currently available"))
# Reusable field to include in other table definitions
track_id = db.Table(None, "track_id",
            FieldS3("track_id", db.gis_track, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_track.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_track.id == id).select(db.gis_track.name, limitby=(0, 1)).first().name] or ["None"])[0],
                label = T("Track"),
                comment = DIV(A(ADD_TRACK, _class="colorbox", _href=URL(r=request, c="gis", f="track", args="create", vars=dict(format="popup")), _target="top", _title=ADD_TRACK),
                          DIV( _class="tooltip", _title=Tstr("GPX Track") + "|" + Tstr("A file downloaded from a GPS containing a series of geographic points in XML format."))),
                ondelete = "RESTRICT"
                ))

# GIS Layers
#gis_layer_types = ["bing", "shapefile", "scan", "wfs"]
gis_layer_types = ["openstreetmap", "georss", "google", "gpx", "js", "kml", "mgrs", "tms", "wms", "xyz", "yahoo"]
gis_layer_openstreetmap_subtypes = gis.layer_subtypes("openstreetmap")
gis_layer_google_subtypes = gis.layer_subtypes("google")
gis_layer_yahoo_subtypes = gis.layer_subtypes("yahoo")
gis_layer_bing_subtypes = gis.layer_subtypes("bing")
# Base table from which the rest inherit
gis_layer = db.Table(db, "gis_layer", timestamp,
            #uuidstamp, # Layers like OpenStreetMap, Google, etc shouldn't sync
            Field("name", notnull=True, label=T("Name"), requires=IS_NOT_EMPTY(), comment=SPAN("*", _class="req")),
            Field("description", label=T("Description")),
            #Field("priority", "integer", label=T("Priority")),    # System default priority is set in ol_layers_all.js. User priorities are set in WMC.
            Field("enabled", "boolean", default=True, label=T("Available in Viewer?")))
for layertype in gis_layer_types:
    resource = "layer_" + layertype
    tablename = "%s_%s" % (module, resource)
    # Create Type-specific Layer tables
    if layertype == "openstreetmap":
        t = db.Table(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_openstreetmap_subtypes, zero=None)))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "georss":
        t = db.Table(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
            projection_id,
            marker_id)
        table = db.define_table(tablename, t, migrate=migrate)
        table.projection_id.requires = IS_ONE_OF(db, "gis_projection.id", "%(name)s")
        table.projection_id.default = 2
    elif layertype == "google":
        t = db.Table(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_google_subtypes, zero=None)))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "gpx":
        t = db.Table(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            #Field("url", label=T("Location")),
            track_id,
            marker_id)
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "kml":
        t = db.Table(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            Field("url", label=T("Location"), requires = IS_NOT_EMPTY()))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "js":
        t = db.Table(db, table,
            gis_layer,
            Field("code", "text", label=T("Code"), default="var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);"))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "mgrs":
        t = db.Table(db, table,
            gis_layer,
            Field("url", label=T("Location")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "tms":
        t = db.Table(db, table,
            gis_layer,
            Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
            Field("layers", label=T("Layers"), requires = IS_NOT_EMPTY()),
            Field("format", label=T("Format")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "wms":
        t = db.Table(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
            Field("base", "boolean", default=True, label=T("Base Layer?")),
            Field("map", label=T("Map")),
            Field("layers", label=T("Layers"), requires = IS_NOT_EMPTY()),
            Field("format", label=T("Format"), requires = IS_NULL_OR(IS_IN_SET(["image/jpeg", "image/png"]))),
            Field("transparent", "boolean", default=False, label=T("Transparent?")),
            projection_id)
        table = db.define_table(tablename, t, migrate=migrate)
        #table.url.requires = [IS_URL, IS_NOT_EMPTY()]
        # Default IS_NULL_OR() not appropriate here
        table.projection_id.requires = IS_ONE_OF(db, "gis_projection.id", "%(name)s")
        table.projection_id.default = 2
    elif layertype == "xyz":
        t = db.Table(db, table,
            gis_layer,
            Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
            Field("base", "boolean", default=True, label=T("Base Layer?")),
            Field("sphericalMercator", "boolean", default=False, label=T("Spherical Mercator?")),
            Field("transitionEffect", requires=IS_NULL_OR(IS_IN_SET(["resize"])), label=T("Transition Effect")),
            Field("numZoomLevels", "integer", label=T("num Zoom Levels")),
            Field("transparent", "boolean", default=False, label=T("Transparent?")),
            Field("visible", "boolean", default=True, label=T("Visible?")),
            Field("opacity", "double", default=0.0, label=T("Transparent?"))
            )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "yahoo":
        t = db.Table(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_yahoo_subtypes, zero=None)))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "bing":
        t = db.Table(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_bing_subtypes, zero=None)))
        table = db.define_table(tablename, t, migrate=migrate)

# GIS Cache
# (Store downloaded KML & GeoRSS feeds)
resource = "cache"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                Field("name", length=128, notnull=True, unique=True),
                Field("file", "upload", autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
table.file.uploadfolder = os.path.join(request.folder, "uploads/gis_cache")

# Below tables are not yet implemented

# GIS Styles: SLD
#db.define_table("gis_style", timestamp,
#                Field("name", notnull=True, unique=True))
#db.gis_style.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "gis_style.name")]

# GIS WebMapContexts
# (User preferences)
# GIS Config's Defaults should just be the version for user=0?
#db.define_table("gis_webmapcontext", timestamp,
#                Field("user", db.auth_user))
#db.gis_webmapcontext.user.requires = IS_ONE_OF(db, "auth_user.id", "%(email)s")
