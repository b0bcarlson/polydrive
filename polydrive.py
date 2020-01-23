import gdal
import sys
import geojson
from shapely.geometry import shape, mapping, MultiPolygon, Polygon, LineString

WIDTH = 2.5 #Standard constant width for lanes. Placeholder for now

inGeo = geojson.load(file(sys.argv[1]))

def featFilter(x):
	if "geometry" in x:
		if "type" in x["geometry"] and x["geometry"]["type"] == "LineString":
			if "properties" in x and "highway" in x["properties"] and x["properties"]["highway"] in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link']:
				return True
	return False

inGeo = filter(featFilter, inGeo["features"])

polys = []
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
	p = ls.buffer(w)
	print(str(p))
outShape = MultiPolygon(polys)
#inGeo = geojson.loads(str(inGeo))
#inShp = shape(inGeo[0])

#print(str(inShp))
