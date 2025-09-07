Title: SpatiaLite - Datasette documentation

URL Source: https://docs.datasette.io/en/stable/spatialite.html

Published Time: Mon, 07 Oct 2024 17:45:33 GMT

Markdown Content:
[View this page](https://docs.datasette.io/en/stable/_sources/spatialite.rst.txt "View this page")

Toggle table of contents sidebar

The [SpatiaLite module](https://www.gaia-gis.it/fossil/libspatialite/index) for SQLite adds features for handling geographic and spatial data. For an example of what you can do with it, see the tutorial [Building a location to time zone API with SpatiaLite](https://datasette.io/tutorials/spatialite).

To use it with Datasette, you need to install the `mod_spatialite` dynamic library. This can then be loaded into Datasette using the `--load-extension` command-line option.

Datasette can look for SpatiaLite in common installation locations if you run it like this:

datasette --load-extension=spatialite --setting default_allow_sql off

If SpatiaLite is in another location, use the full path to the extension instead:

datasette --setting default_allow_sql off \
  --load-extension=/usr/local/lib/mod_spatialite.dylib

Warning[¶](https://docs.datasette.io/en/stable/spatialite.html#warning "Link to this heading")
----------------------------------------------------------------------------------------------

Warning

The SpatiaLite extension adds [a large number of additional SQL functions](https://www.gaia-gis.it/gaia-sins/spatialite-sql-5.0.1.html), some of which are not be safe for untrusted users to execute: they may cause the Datasette server to crash.

You should not expose a SpatiaLite-enabled Datasette instance to the public internet without taking extra measures to secure it against potentially harmful SQL queries.

The following steps are recommended:

*   Disable arbitrary SQL queries by untrusted users. See [Controlling the ability to execute arbitrary SQL](https://docs.datasette.io/en/stable/authentication.html#authentication-permissions-execute-sql) for ways to do this. The easiest is to start Datasette with the `datasette --setting default_allow_sql off` option.

*   Define [Canned queries](https://docs.datasette.io/en/stable/sql_queries.html#canned-queries) with the SQL queries that use SpatiaLite functions that you want people to be able to execute.

The [Datasette SpatiaLite tutorial](https://datasette.io/tutorials/spatialite) includes detailed instructions for running SpatiaLite safely using these techniques

Installation[¶](https://docs.datasette.io/en/stable/spatialite.html#installation "Link to this heading")
--------------------------------------------------------------------------------------------------------

### Installing SpatiaLite on OS X[¶](https://docs.datasette.io/en/stable/spatialite.html#installing-spatialite-on-os-x "Link to this heading")

The easiest way to install SpatiaLite on OS X is to use [Homebrew](https://brew.sh/).

brew update
brew install spatialite-tools

This will install the `spatialite` command-line tool and the `mod_spatialite` dynamic library.

You can now run Datasette like so:

datasette --load-extension=spatialite

### Installing SpatiaLite on Linux[¶](https://docs.datasette.io/en/stable/spatialite.html#installing-spatialite-on-linux "Link to this heading")

SpatiaLite is packaged for most Linux distributions.

apt install spatialite-bin libsqlite3-mod-spatialite

Depending on your distribution, you should be able to run Datasette something like this:

datasette --load-extension=/usr/lib/x86_64-linux-gnu/mod_spatialite.so

If you are unsure of the location of the module, try running `locate mod_spatialite` and see what comes back.

Spatial indexing latitude/longitude columns[¶](https://docs.datasette.io/en/stable/spatialite.html#spatial-indexing-latitude-longitude-columns "Link to this heading")
----------------------------------------------------------------------------------------------------------------------------------------------------------------------

Here's a recipe for taking a table with existing latitude and longitude columns, adding a SpatiaLite POINT geometry column to that table, populating the new column and then populating a spatial index:

import sqlite3

conn = sqlite3.connect("museums.db")
# Lead the spatialite extension:
conn.enable_load_extension(True)
conn.load_extension("/usr/local/lib/mod_spatialite.dylib")
# Initialize spatial metadata for this database:
conn.execute("select InitSpatialMetadata(1)")
# Add a geometry column called point_geom to our museums table:
conn.execute(
    "SELECT AddGeometryColumn('museums', 'point_geom', 4326, 'POINT', 2);"
)
# Now update that geometry column with the lat/lon points
conn.execute(
 """
 UPDATE museums SET
 point_geom = GeomFromText('POINT('||"longitude"||' '||"latitude"||')',4326);
"""
)
# Now add a spatial index to that column
conn.execute(
    'select CreateSpatialIndex("museums", "point_geom");'
)
# If you don't commit your changes will not be persisted:
conn.commit()
conn.close()

Making use of a spatial index[¶](https://docs.datasette.io/en/stable/spatialite.html#making-use-of-a-spatial-index "Link to this heading")
------------------------------------------------------------------------------------------------------------------------------------------

SpatiaLite spatial indexes are R*Trees. They allow you to run efficient bounding box queries using a sub-select, with a similar pattern to that used for [Searches using custom SQL](https://docs.datasette.io/en/stable/full_text_search.html#full-text-search-custom-sql).

In the above example, the resulting index will be called `idx_museums_point_geom`. This takes the form of a SQLite virtual table. You can inspect its contents using the following query:

select * from idx_museums_point_geom limit 10;

Here's a live example: [timezones-api.datasette.io/timezones/idx_timezones_Geometry](https://timezones-api.datasette.io/timezones/idx_timezones_Geometry)

| pkid | xmin | xmax | ymin | ymax |
| --- | --- | --- | --- | --- |
| 1 | -8.601725578308105 | -2.4930307865142822 | 4.162120819091797 | 10.74019718170166 |
| 2 | -3.2607860565185547 | 1.27329421043396 | 4.539252281188965 | 11.174856185913086 |
| 3 | 32.997581481933594 | 47.98238754272461 | 3.3974475860595703 | 14.894054412841797 |
| 4 | -8.66890811920166 | 11.997337341308594 | 18.9681453704834 | 37.296207427978516 |
| 5 | 36.43336486816406 | 43.300174713134766 | 12.354820251464844 | 18.070993423461914 |

You can now construct efficient bounding box queries that will make use of the index like this:

select * from museums where museums.rowid in (
 SELECT pkid FROM idx_museums_point_geom
 -- left-hand-edge of point > left-hand-edge of bbox (minx)
 where xmin > :bbox_minx
 -- right-hand-edge of point < right-hand-edge of bbox (maxx)
 and xmax < :bbox_maxx
 -- bottom-edge of point > bottom-edge of bbox (miny)
 and ymin > :bbox_miny
 -- top-edge of point < top-edge of bbox (maxy)
 and ymax < :bbox_maxy
);

Spatial indexes can be created against polygon columns as well as point columns, in which case they will represent the minimum bounding rectangle of that polygon. This is useful for accelerating `within` queries, as seen in the Timezones API example.

Importing shapefiles into SpatiaLite[¶](https://docs.datasette.io/en/stable/spatialite.html#importing-shapefiles-into-spatialite "Link to this heading")
--------------------------------------------------------------------------------------------------------------------------------------------------------

The [shapefile format](https://en.wikipedia.org/wiki/Shapefile) is a common format for distributing geospatial data. You can use the `spatialite` command-line tool to create a new database table from a shapefile.

Try it now with the North America shapefile available from the University of North Carolina [Global River Database](http://gaia.geosci.unc.edu/rivers/) project. Download the file and unzip it (this will create files called `narivs.dbf`, `narivs.prj`, `narivs.shp` and `narivs.shx` in the current directory), then run the following:

$ spatialite rivers-database.db
SpatiaLite version ..: 4.3.0a       Supported Extensions:
...
spatialite> .loadshp narivs rivers CP1252 23032
========
Loading shapefile at 'narivs' into SQLite table 'rivers'
...
Inserted 467973 rows into 'rivers' from SHAPEFILE

This will load the data from the `narivs` shapefile into a new database table called `rivers`.

Exit out of `spatialite` (using `Ctrl+D`) and run Datasette against your new database like this:

datasette rivers-database.db \
    --load-extension=/usr/local/lib/mod_spatialite.dylib

If you browse to `http://localhost:8001/rivers-database/rivers` you will see the new table... but the `Geometry` column will contain unreadable binary data (SpatiaLite uses [a custom format based on WKB](https://www.gaia-gis.it/gaia-sins/BLOB-Geometry.html)).

The easiest way to turn this into semi-readable data is to use the SpatiaLite `AsGeoJSON` function. Try the following using the SQL query interface at `http://localhost:8001/rivers-database`:

select *, AsGeoJSON(Geometry) from rivers limit 10;

This will give you back an additional column of GeoJSON. You can copy and paste GeoJSON from this column into the debugging tool at [geojson.io](https://geojson.io/) to visualize it on a map.

To see a more interesting example, try ordering the records with the longest geometry first. Since there are 467,000 rows in the table you will first need to increase the SQL time limit imposed by Datasette:

datasette rivers-database.db \
    --load-extension=/usr/local/lib/mod_spatialite.dylib \
    --setting sql_time_limit_ms 10000

Now try the following query:

select *, AsGeoJSON(Geometry) from rivers
order by length(Geometry) desc limit 10;

Importing GeoJSON polygons using Shapely[¶](https://docs.datasette.io/en/stable/spatialite.html#importing-geojson-polygons-using-shapely "Link to this heading")
----------------------------------------------------------------------------------------------------------------------------------------------------------------

Another common form of polygon data is the GeoJSON format. This can be imported into SpatiaLite directly, or by using the [Shapely](https://pypi.org/project/Shapely/) Python library.

[Who's On First](https://whosonfirst.org/) is an excellent source of openly licensed GeoJSON polygons. Let's import the geographical polygon for Wales. First, we can use the Who's On First Spelunker tool to find the record for Wales:

[spelunker.whosonfirst.org/id/404227475](https://spelunker.whosonfirst.org/id/404227475/)

That page includes a link to the GeoJSON record, which can be accessed here:

[data.whosonfirst.org/404/227/475/404227475.geojson](https://data.whosonfirst.org/404/227/475/404227475.geojson)

Here's Python code to create a SQLite database, enable SpatiaLite, create a places table and then add a record for Wales:

import sqlite3

conn = sqlite3.connect("places.db")
# Enable SpatialLite extension
conn.enable_load_extension(True)
conn.load_extension("/usr/local/lib/mod_spatialite.dylib")
# Create the masic countries table
conn.execute("select InitSpatialMetadata(1)")
conn.execute(
    "create table places (id integer primary key, name text);"
)
# Add a MULTIPOLYGON Geometry column
conn.execute(
    "SELECT AddGeometryColumn('places', 'geom', 4326, 'MULTIPOLYGON', 2);"
)
# Add a spatial index against the new column
conn.execute("SELECT CreateSpatialIndex('places', 'geom');")
# Now populate the table
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry import shape
import requests

geojson = requests.get(
    "https://data.whosonfirst.org/404/227/475/404227475.geojson"
).json()
# Convert to "Well Known Text" format
wkt = shape(geojson["geometry"]).wkt
# Insert and commit the record
conn.execute(
    "INSERT INTO places (id, name, geom) VALUES(null, ?, GeomFromText(?, 4326))",
    ("Wales", wkt),
)
conn.commit()

Querying polygons using within()[¶](https://docs.datasette.io/en/stable/spatialite.html#querying-polygons-using-within "Link to this heading")
----------------------------------------------------------------------------------------------------------------------------------------------

The `within()` SQL function can be used to check if a point is within a geometry:

select
 name
from
 places
where
 within(GeomFromText('POINT(-3.1724366 51.4704448)'), places.geom);

The `GeomFromText()` function takes a string of well-known text. Note that the order used here is `longitude` then `latitude`.

To run that same `within()` query in a way that benefits from the spatial index, use the following:

select
 name
from
 places
where
 within(GeomFromText('POINT(-3.1724366 51.4704448)'), places.geom)
 and rowid in (
 SELECT pkid FROM idx_places_geom
 where xmin < -3.1724366
 and xmax > -3.1724366
 and ymin < 51.4704448
 and ymax > 51.4704448
 );
