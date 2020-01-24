import bisect
import sys

import geojson
import pyproj
from pyproj import Proj
from shapely.geometry import mapping, LineString
from shapely.ops import transform

WIDTH = 1.85 #Standard constant width for lanes. This is the width of highway lanes in the US (12 ft/2).
#Eventually may split this more based on road type

inGeo = geojson.load(file(sys.argv[1])) #input file
in_crs = Proj(init='epsg:4326') #OSM epsg
attrs = ["highway", "width", "lanes", "name", "oneway", "surface", "destination:ref", "destination:street", "ref", "layer", "bridge"]

def featFilter(x):
	if "geometry" in x:
		if "type" in x["geometry"] and x["geometry"]["type"] == "LineString":
			if "properties" in x and "highway" in x["properties"] and x["properties"]["highway"] in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link']:
					if not "layer" in x["properties"] or int(x["properties"]["layer"]) >= 0:
						return True
	return False

#Filter to only get roads
inGeo = filter(featFilter, inGeo["features"])

polys = {}
transformations = {}
for g in inGeo:
	#Calculate the half-width of the road
	if "width" in g["properties"]:
		w = float(g["properties"]["width"])/2
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
	x = round(centroid.x)
	y = round(centroid.y)
	#Create the projection that is used to convert the input (4326) to meters.
	#As things get closer to the poles there is more distortion, but for now I simply have it round to the nearest degree.
	trans_crs = Proj(proj="aeqd", lat_0=y, lon_0=x, datum="WGS84", units="m")
	#As it turns out, creating the Transformers (pyproj.Transformer...) is very intensive even in comparison to actually transforming.
	#Here I am storing Transformers based on the lat/long so less need to be created and it's faster
	if (y, x) not in transformations.keys():
		project = pyproj.Transformer.from_proj(
			in_crs,
			trans_crs)
		project2 = pyproj.Transformer.from_proj(
			trans_crs,
			in_crs)
		transformations[(y, x)] = (project, project2)
	else:
		project = transformations[(y, x)][0]
		project2 = transformations[(y, x)][1]
	#Transform to a projection in meters, create a polygon based on the line, and transform back
	p = transform(project.transform, ls)
	p = p.buffer(w+.1, cap_style=3, join_style=1)
	p = transform(project2.transform, p)

	#Copy attributes
	for a in attrs:
		if a in g["properties"]:
			setattr(p, a, g["properties"][a])
	#Save the created polygon in a list index by its layer
	layer = int(getattr(p, "layer", 0))
	if layer not in polys.keys():
		polys[layer] = []
	polys[layer].append(p)

finalized_polys = []
for k in sorted(polys):
	#For each layer iterate through the polys it contains, then the layers above it.
	#When there are intersections cut out those parts, then save the poly to the finalized_polys list
	remaining_keys = sorted(polys)[bisect.bisect_right(sorted(polys), k):]
	for poly in polys[k]:
		out_poly = poly
		for check_key in remaining_keys:
			for check_poly in polys[check_key]:
				out_poly = (out_poly.symmetric_difference(check_poly)).difference(check_poly)
		for a in attrs:
			try:
				setattr(out_poly, a, getattr(poly, a))
			except AttributeError, e:
				pass
		finalized_polys.append(out_poly)

def polyMap(x):
	#Convert the shapely shape to a geojson shape
	result = {}
	result["type"] = x.type
	result["geometry"] = mapping(x)
	for a in attrs:
		try:
			result[a] = getattr(x, a)
		except AttributeError, e:
			pass
	return result

gjs = { "type": "FeatureCollection", "features": map(polyMap, finalized_polys) }
with open(sys.argv[2], "w") as out:
	geojson.dump(gjs, out)
