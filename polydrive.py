import gdal
import sys
import geojson
import fiona
import pyproj
from shapely.geometry import shape, mapping, MultiPolygon, Polygon, LineString
from fiona.crs import from_epsg
from pyproj import Proj, transform
from shapely.ops import transform


WIDTH = 1.85 #Standard constant width for lanes. This is the width of highway lanes in the US (12 ft/2). Eventually may split this more based on road type

inGeo = geojson.load(file(sys.argv[1]))
in_crs = Proj(init='epsg:4326')

def featFilter(x):
	if "geometry" in x:
		if "type" in x["geometry"] and x["geometry"]["type"] == "LineString":
			if "properties" in x and "highway" in x["properties"] and x["properties"]["highway"] in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link']:
				return True
	return False

inGeo = filter(featFilter, inGeo["features"])

polys = []
attrs = ["highway", "width", "lanes", "name", "oneway", "surface", "destination:ref", "destination:street", "ref", "layer", "bridge"]
for g in inGeo:
	if "width" in g["properties"]:
		w = g["properties"]["width"]
	else:
		if "oneway" in g["properties"] and g["properties"]["oneway"] == "yes":
			if "lanes" in g["properties"]:
				w = int(g["properties"]["lanes"]) * WIDTH
			else:
				w = WIDTH
		else:
			if "lanes" in g["properties"]:
				w = int(g["properties"]["lanes"]) * WIDTH
			else:
				w = 2 * WIDTH
	ls = LineString(g["geometry"]["coordinates"])
	centroid = ls.centroid

	trans_crs = Proj(proj="aeqd", lat_0=centroid.y, lon_0=centroid.x, datum="WGS84", units="m")
	project = pyproj.Transformer.from_proj(
		in_crs,
		trans_crs)
	p = transform(project.transform, ls)
	p = p.buffer(w+.1, cap_style=3, join_style=1)
	project2 = pyproj.Transformer.from_proj(
		trans_crs,
		in_crs)
	p = transform(project2.transform, p)
	for a in attrs:
		if a in g["properties"]:
			setattr(p, a, g["properties"][a])
	polys.append(p)

for i,p in enumerate(polys):
	layer = getattr(p, "layer", 0)
	p3 = p
	for p2 in polys:
		if p3 is not p2 and p3.intersects(p2) and getattr(p2, "layer", 0) > layer:
			p3 = (p3.symmetric_difference(p2)).difference(p2)
	for a in attrs:
		try:
			setattr(p3, a, getattr(p, a))
		except AttributeError, e:
			pass
	polys[i] = p3
def polyMap(x):
	result = {}
	result["type"] = x.type
	result["geometry"] = mapping(x)
	for a in attrs:
		try:
			result[a] = getattr(x, a)
		except AttributeError, e:
			pass
	return result

gjs = { "type": "FeatureCollection", "features": map(polyMap, polys) }
with open("out.geojson", "w") as out:
	geojson.dump(gjs, out)
