﻿var proj_current = map.getProjectionObject();

// Layer to hold the Feature
featuresLayer = new OpenLayers.Layer.Vector("Locations", {displayInLayerSwitcher: false});
map.addLayer(featuresLayer);

var parser = new OpenLayers.Format.WKT();
var geom, popupContentHTML, iconURL;

geom = parser.read('{{=feature.wkt}}').geometry;
geom = geom.transform(proj4326, projection_current);
popupContentHTML = "{{include 'gis/ol_features_popup.html'}}";
iconURL = '{{=URL(r=request, c='default', f='download', args=[feature.marker])}}';
add_Feature_with_popup(featuresLayer, '{{=feature.uuid}}', geom, popupContentHTML, iconURL);

// Select Control for Internal FeatureGroup Layers
select = new OpenLayers.Control.SelectFeature(featuresLayer, {
        clickout: true,
        toggle: true,
        multiple: false,
        onSelect: onFeatureSelect,
        onUnselect: onFeatureUnselect
    }
);
map.addControl(select);
select.activate();