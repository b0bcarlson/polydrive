# polydrive
Creates polygons for visible roads from OSM and cuts an input geotif to those polygons.

This is part of my undergraduate Computer Science research project at the University of Northern Iowa

Usage: `python polydrive.py [input geojson] [output name] [input geotif]`

Example: `python polydrive.py sampleinput.geojson output sample.TIF`

Tested only with geojson from [BBBike](https://extract.bbbike.org/).

Future:
 - Automatic downloading of geojson based on an input geotif (or similar). - Cutting of the input geotif based on the created polygons.
 - Support of manually created geojsons, OSM only tracks the centerline which isn't always good enough.