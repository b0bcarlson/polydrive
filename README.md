# polydrive
Creates polygons for visible roads from OSM

This is part of my undergraduate Computer Science research project at the University of Northern Iowa

Usage: `python polydrive.py [input geojson] [output geojson]`

Tested only with geojson from [BBBike](https://extract.bbbike.org/).

Future:
 - Automatic downloading of geojson based on an input geotif (or similar).
 - Cutting of the input geojson based on the created polygons.
 - Storage of polygons to a database.