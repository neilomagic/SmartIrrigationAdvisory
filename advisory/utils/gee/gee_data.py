import ee
import datetime

# Make sure Earth Engine is initialized
try:
    ee.Authenticate()
    ee.Initialize(project="ee-haronotwal55-irrigation-adv")

except Exception:
    ee.Authenticate()
    ee.Initialize(project="ee-haronotwal55-irrigation-adv")


def get_point_geometry(lat, lon):
    return ee.Geometry.Point([lon, lat])


def get_weekly_rainfall(lat, lon):
    point = get_point_geometry(lat, lon)
    today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))
    week_ago = today.advance(-7, 'day')

    dataset = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") \
                .filterDate(week_ago, today).filterBounds(point)

    rainfall_image = dataset.sum()
    rainfall_mm = rainfall_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=5000,
        maxPixels=1e9
    ).get('precipitation')

    return rainfall_mm.getInfo() if rainfall_mm else 0


def get_daily_et0(lat, lon):
    point = get_point_geometry(lat, lon)
    today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    dataset = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
                .filterDate(today.advance(-1, 'day'), today) \
                .filterBounds(point)

    image = dataset.first()
    eto_image = image.select('potential_evaporation')

    eto_mm = eto_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point,
        scale=1000,
        maxPixels=1e9
    ).get('potential_evaporation')

    # Convert from m to mm
    return round(eto_mm.getInfo() * 1000, 2) if eto_mm else 0
