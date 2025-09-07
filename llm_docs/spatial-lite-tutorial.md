Title: Building a location to time zone API with SpatiaLite

URL Source: https://datasette.io/tutorials/spatialite

Markdown Content:
The [SpatiaLite extension](https://www.gaia-gis.it/fossil/libspatialite/index) for SQLite adds a large number of functions for geospatial analysis, which can be used with Datasette to build GIS (Geographic Information System) applications.

This tutorial will show how SpatiaLite and Datasette can be combined to create a JSON API that can return the time zone for a specific latitude and longitude point on earth.

What we are going to build
--------------------------

You can try the API out here. Give it a latitude and longitude and it will return the corresponding time zone ID: [https://timezones.datasette.io/timezones/by_point](https://timezones.datasette.io/timezones/by_point)

Some examples:

*   [Brighton, England](https://timezones.datasette.io/timezones/by_point?longitude=-0.1406632&latitude=50.8246776) is in Europe/London ([in JSON](https://timezones.datasette.io/timezones/by_point.json?longitude=-0.1406632&latitude=50.8246776&_shape=array))
*   [San Francisco, USA](https://timezones.datasette.io/timezones/by_point?longitude=-122.4494224&latitude=37.8022071) is in America/Los_Angeles ([in JSON](https://timezones.datasette.io/timezones/by_point.json?longitude=-122.4494224&latitude=37.8022071&_shape=array))
*   [Tokyo, Japan](https://timezones.datasette.io/timezones/by_point?longitude=139.7819661&latitude=35.6631424) is Asia/Tokyo ([in JSON](https://timezones.datasette.io/timezones/by_point.json?longitude=139.7819661&latitude=35.6631424&_shape=array))

Setting up a development environment
------------------------------------

You will need two things in place for this tutorial:

*   SpatiaLite installed on your system
*   A Python installation that allows the `sqlite3` module to load additional extensions

### Recommended: Use GitHub Codespaces

[GitHub Codespaces](https://github.com/codespaces) can provide you with a free development environment for this project accessible through your web browser, with all of the tools you need pre-installed.

This is the **easiest** way to work through this tutorial.

[Visit this link](https://github.com/codespaces/new?machine=basicLinux32gb&repo=114008133&ref=main) to create a new Codespace with everything you will need for the rest of the tutorial.

### Using a Mac

On a Mac you can install SpatiaLite and Datasette using Homebrew like so:

```
brew install spatialite-tools datasette
```

If you are on a Mac you may find that your installation of Python cannot load external SQLite modules. You can check by running the following:

```
datasette --load-extension spatialite
```

If you get an error message about `enable_load_extension` then consult [this page](https://datasette.io/help/extensions) for hints on how to fix the problem.

Building the database
---------------------

To build this project we first need geographic shapes for all of the world's time zones.

[timezone-boundary-builder](https://github.com/evansiroky/timezone-boundary-builder) is a project by Evan Siroky which uses data from [OpenStreetMap](https://www.openstreetmap.org/) to create detailed time zone polygons, which he then releases in GeoJSON and Shapefile format. The result is made available under the [Open Data Commons Open Database License (ODbL)](http://opendatacommons.org/licenses/odbl/).

Start by downloading the `timezones-with-oceans.shapefile.zip` file from the [latest release](https://github.com/evansiroky/timezone-boundary-builder/releases):

`wget https://github.com/evansiroky/timezone-boundary-builder/releases/download/2022g/timezones-with-oceans.shapefile.zip`

(If you are using Codespaces you should run all of these commands in the "Terminal" tab of the Codespaces interface.)

A [Shapefile](https://en.wikipedia.org/wiki/Shapefile) is a set of files that describe a collection of geographic features. There's no need to unzip this zip file - our tools can work directly with it.

We can load the file into a new SpatiaLite database using the `shapefile-to-sqlite` command.

If you are running this tutorial in Codespaces this has been installed already. Otherwise, you can install it like this:

```
pip install shapefile-to-sqlite
```

To load the Shapefile into a database, use the following:

```
shapefile-to-sqlite timezones.db \
    timezones-with-oceans.shapefile.zip \
    --table timezones \
    --spatial-index
```

This will create a new database file called `timezones.db`, and load the shapes from the Shapefile into a new table called `timezones`. It will also set up a spatial index on the `timezones` table, described later.

The command will show a progress bar like this:

```
zip://timezones-with-oceans.shapefile.zip
  [########----------------------------]   22%  00:00:38
```

This make take a couple of minutes to complete.

Browsing the database in Datasette
----------------------------------

We can now start Datasette against that file to browse the data:

```
datasette timezones.db --load-extension spatialite
```

You should see the following output:

```
INFO:     Started server process [5385]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

If you are using your own computer you can now visit [http://127.0.0.1:8001](http://127.0.0.1:8001/) to see the Datasette interface.

If you are running in Codespaces the tool should offer an "Open in Browser" button.

You can now browse the database. There should be a `timezones` table with three columns: `id`, `tzid` and `geometry`

There isn't much to see yet though! The geometry columns are just big binary blobs.

### Viewing the time zone shapes on a map

To see the time zone geometries on a map, we can install a Datasette plugin.

[datasette-geojson-map](https://datasette.io/plugins/datasette-geojson-map) by Chris Amico adds the ability to render GeoJSON and SpatiaLite geometries directly on a map.

Hit Ctrl+C in the terminal to stop the Datasette server, then run the following:

```
datasette install datasette-geojson-map
```

Now start Datasette running again:

```
datasette timezones.db \
  --load-extension spatialite \
  --setting default_page_size 10
```

We're adding an extra setting here, to set the default page size to 10. This is because some of the time zone polygons are really large and the default page size of 100 can take a long time to render.

Visit the `timezones` table again and you should see something like this:

![Image 1: The timezones table page in Datasette shows a map at the top with a small number of time zones represented, above a table listing them by name.](https://simonw.github.io/datasette-screenshots/non-retina/timezones.png)

Finding the time zone for a point
---------------------------------

Now that we have a table full of time zone geometries we can construct a SQL query that can show us the time zone for any specific point on earth.

We can do this using the SpatiaLite `within()` function, which takes two geometries and checks if one is contained within the other.

First we're going to need a geometry that represents a specific latitude/longitude point.

`41.798, -87.696` is a point within the city of Chicago - see it [here on Google Maps](https://www.google.com/maps/?ll=41.798,-87.696&z=10).

We can use the SpatiaLite `MakePoint(longitude, latitude)` function (note that the latitude and longitude are reversed here) to create a geometry which can then be used with the `within()` function:

select
  tzid
from
  timezones
where
  within(
    MakePoint(-87.696, 41.798),
    timezones.Geometry
  ) = 1

`within(geom1, geom2)` returns `1` if the first geometry is contained within the second, and `0` if it is not.

Sure enough, this query returns `America/Chicago`.

Using parameters in the SQL query
---------------------------------

Datasette has a feature where SQL queries can contain named parameters `:like_this` which will be turned into form fields and used to feed new values to the queries.

Try that with the following query:

select
  tzid
from
  timezones
where
  within(
    MakePoint(:longitude, :latitude),
    timezones.Geometry
  ) = 1

This looks like it should work... but if you try it with the previous coordinates you'll see that it returns no results.

This is because `MakePoint()` needs to be given floating point values, but Datasette passes all parameters as strings.

If you pass invalid types, `MakePoint()` returns `null` - and `within(null, geometry)` then returns `-1` to specify an invalid result.

We can fix this by casting the strings to floats, like this:

select
  tzid
from
  timezones
where
  within(
    MakePoint(cast(:longitude as float), cast(:latitude as float)),
    timezones.Geometry
  ) = 1

This query has the desired effect: given a latitude and longitude for any point on earth it will return the correct time zone.

Speeding it up with an index
----------------------------

There's one remaining catch with this query: it's relatively slow. In my testing I was seeing anything between 150ms and 750ms for the query to run, due to the need to compare the point with all 455 polygons in the database.

We used the `--spatial-index` option when we first imported the data. Here's how to take advantage of that spatial index to speed things up:

select tzid
from
  timezones
where
  within(
    MakePoint(cast(:longitude as float), cast(:latitude as float)),
    timezones.Geometry
  ) = 1
  and rowid in (
    select
      rowid
    from
      SpatialIndex
    where
      f_table_name = 'timezones'
      and search_frame = MakePoint(cast(:longitude as float), cast(:latitude as float))
  )

The trick here is the extra `and rowid in (...)` subquery.

`SpatialIndex` is a special table - it's a virtual table created by SpatiaLite.

You can query that table by passing the name of another table that has a spatial index associated with it - in this case `timezones`. Then you pass in a geometry as `search_frame` and the table will return a list of `rowid` values representing any polygons with a rough bounding box that overlaps that of the geometry you passed in.

Note that this is not an exact comparison: some of the row IDs you get back may not intersect exactly with the geometry.

But it's a good enough approximation. You can combine these values with a more accurate `within()` check, which will then only have to run full calculations against a subset of the overall set of polygons.

In my local testing this dropped the time taken for the query from 150ms to less than 8ms - a significant speedup!

Adding country polygons
-----------------------

Which time zones are relevant for a specific country?

Our data at the moment can't tell us that. We can filter for just time zones that start with `America/` but this will give us everything for both North and South America. Wouldn't it be neat if we could browse our time zones by country instead?

We can try to answer that question by loading in polygons for every country in the world.

[datahub.io/core/geo-countries](https://datahub.io/core/geo-countries) has the data we need for this, derived from [Natural Earth](https://www.naturalearthdata.com/) and released under the [PDDL](https://opendatacommons.org/licenses/pddl/1-0/) license.

We can download a GeoJSON file of countries like this:

```
wget https://datahub.io/core/geo-countries/r/countries.geojson
```

Now we can use [geojson-to-sqlite](https://datasette.io/tools/geojson-to-sqlite) to load it into a `countries` database table, again creating a spatial index:

```
pip install geojson-to-sqlite

geojson-to-sqlite timezones.db countries \
  countries.geojson --spatial-index
```

Datasette should pick up the new `countries` table, and `datasette-geojson-map` will now show rendered outlines of those countries.

To find the time zones that intersect a specific country, we can use the following query:

select
  tzid,
  geometry
from
  timezones
where intersects(
  timezones.geometry, (
    select geometry from countries where admin = 'United Kingdom'
  ) = 1
)

We are using a couple of additional tricks here.

The `intersects()` function is a SpatiaLite function that checks if two geometries intersect each other in any way.

We'e also using a subquery to access the geometry of the country that we are interested in:

select geometry from countries where admin = 'United Kingdom'

The `admin` column in `countries` has names of the countries - here we are pulling back the geometry for the United Kingdom.

Here are [the results of this query](https://timezones.datasette.io/timezones/by_country?country=United+Kingdom).

Simplifying the polygons
------------------------

Try changing the country name to "United States of America" and you may run into a problem: the geometries for the time zones that intersect with the United States are so large that they may not be possible to render on the map!

We can help solve that using another SpatiaLite function: `simplify()`. This function applies the [Douglas–Peucker algorithm](https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm) to simplify a polygon down to a smaller number of points, which makes it much easier to render.

`simplify()` takes a geometry and a precision value. After some trial and error I found that a precision value of `0.05` worked well for these time zone polygons:

select
  tzid,
  simplify(geometry, 0.05) as geometry
from
  timezones
where intersects(
  timezones.geometry, (
    select geometry from countries where admin = 'United States of America'
  )  = 1
)

It's necessary to use `simplify(...) as geometry` here because the `datasette-geojson-map` plugin will look for an output column called `geometry` to render on the map.

Here's [the results of this query](https://timezones.datasette.io/timezones/by_country?country=United+States+of+America) for the United States.

Speeding that up with an index
------------------------------

We can use a spatial index in a similar way to the time zone query listed above:

with country as (
  select
    geometry
  from
    countries
  where
    admin = :country
)
select
  timezones.tzid,
  simplify(timezones.geometry, 0.05) as geometry
from
  timezones,
  country
where
  timezones.id in (
    select
      SpatialIndex.rowid
    from
      SpatialIndex,
      country
    where
      f_table_name = 'timezones'
      and search_frame = country.geometry
  )
  and intersects(timezones.geometry, country.geometry) = 1

This uses the same trick as before - a `where timezones.id in (...)` subselect that returns a list of likely `rowid` values from the `SpatialIndex` virtual table.

If a table has an integer primary key - such as our `timezones` table here - SQLite will set the `rowid` to be the same value, which is why we can compare `timezones.id` with `rowid` in this query.

We're using one more trick here. To avoid having to run that query to select the country geometry twice, we're instead bundling that into a CTE - a Common Table Expression - at the start of the query.

The `with country as (...)` piece makes the result of that query available as a temporary table called `country` for the duration of the SQL query.

Defining metadata with canned queries
-------------------------------------

Now that we've figured out all of the queries needed to power our API, it's time to tie them together into a configuration that we can deploy to the internet.

Datasette's [metadata system](https://docs.datasette.io/en/stable/metadata.html) can be used to provide extra information about the database, and it can also be used to configure [canned queries](https://docs.datasette.io/en/stable/sql_queries.html#canned-queries) - SQL queries with names, like the `by_point` example shown at the beginning of this tutorial.

Here's a `metadata.yml` file which defines both the `by_point` query and a query for looking up time zones by country code.

title: Time zones API
description: |
 An API for looking up time zones by latitude/longitude
about: simonw/timezones-api
about_url: https://github.com/simonw/timezones-api
license: ODbL
license_url: http://opendatacommons.org/licenses/odbl/
source: timezone-boundary-builder
source_url: https://github.com/evansiroky/timezone-boundary-builder
allow_sql: false
databases:
  timezones:
    tables:
      countries:
        source: Natural Earth
        source_url: https://www.naturalearthdata.com/
        license: Open Data Commons Public Domain Dedication and License (PDDL) v1.0
        license_url: https://opendatacommons.org/licenses/pddl/1-0/
        about: geo-countries
        about_url: https://datahub.io/core/geo-countries
    queries:
      by_point:
        title: Find time zone by lat/lon
        sql: |
 select tzid
 from
 timezones
 where
 within(
 MakePoint(cast(:longitude as float), cast(:latitude as float)),
 timezones.Geometry
 ) = 1
 and rowid in (
 select
 rowid
 from
 SpatialIndex
 where
 f_table_name = 'timezones'
 and search_frame = MakePoint(cast(:longitude as float), cast(:latitude as float))
 )
      by_country:
        title: Find time zones that intersect a country
        sql: |
 with country as (
 select
 geometry
 from
 countries
 where
 admin = :country
 )
 select
 timezones.tzid,
 simplify(timezones.geometry, 0.05) as geometry
 from
 timezones,
 country
 where
 timezones.id in (
 select
 SpatialIndex.rowid
 from
 SpatialIndex,
 country
 where
 f_table_name = 'timezones'
 and search_frame = country.geometry
 )
 and intersects(timezones.geometry, country.geometry) = 1

In addition to providing canned queries called `by_name` and `by_country`, this file also includes metadata showing the source of the data we used for the database.

It also sets one more important option:

allow_sql: false

This option [prevents users from executing their own custom SQL queries](https://docs.datasette.io/en/stable/authentication.html#controlling-the-ability-to-execute-arbitrary-sql) against our published database. Only the canned queries we have defined will be available.

We're using that option here because SpatiaLite has a large number of functions, some of which could crash the underlying Datasette instance.

We can test our new `metadata.yml` file by starting Datasette like this:

```
datasette timezones.db --load-extension spatialite -m metadata.yml
```

Deploying the application to Fly
--------------------------------

The [datasette publish](https://docs.datasette.io/en/stable/publish.html) command can be used to deploy Datasette instances to a variety of different hosting providers.

[Fly](https://fly.io/) is an excellent choice for hosting this, since the API could attract a large amount of traffic.

[Google Cloud Run](https://cloud.google.com/run) charges based on how much sustained traffic an instance gets, which could become expensive for this application.

Fly charge a flat monthly rate for the instance, plus additional fees for bandwidth.

Current Fly pricing [can be found here](https://fly.io/docs/about/pricing/). At the time of writing an instance with 256MB of RAM - enough to comfortably host this API - costs $1.94/month.

You'll need to install the Fly CLI tool:

```
curl -L https://fly.io/install.sh | sh
```

Then run the following to authenticate with Fly:

```
flyctl auth login
```

You should also install the [datasette-publish-fly](https://datasette.io/plugins/datasette-publish-fly) plugin:

```
pip install datasette-publish-fly
```

With all of those pieces in place, you can deploy the application like this:

```
datasette publish fly timezones.db \
  --app timezones-api \
  --setting default_page_size 10 \
  --install datasette-geojson-map \
  --metadata metadata.yml \
  --spatialite
```

You need a unique `--app` name (I've already claimed `timezones-api` for this demo).

The `--spatialite` flag ensures SpatiaLite is configured for the deployed application.

The deploy command make take a few minutes to complete. Once it has finished you can visit `https://your-app-name.fly.dev/` to see the finished application, live on the internet.

Here's [timezones.datasette.io](https://timezones.datasette.io/), deployed using this exact command.

Source code
-----------

The source code for everything in this tutorial can be found in the [simonw/timezones-api](https://github.com/simonw/timezones-api) repository on GitHub.

### More tutorials

*   [Exploring a database with Datasette](https://datasette.io/tutorials/explore)
*   [Learn SQL with Datasette](https://datasette.io/tutorials/learn-sql)
*   [Using Datasette in GitHub Codespaces](https://datasette.io/tutorials/codespaces)
*   [Cleaning data with sqlite-utils and Datasette](https://datasette.io/tutorials/clean-data)
*   [Data analysis with SQLite and Python](https://datasette.io/tutorials/data-analysis)
