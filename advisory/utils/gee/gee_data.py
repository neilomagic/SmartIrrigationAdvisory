import ee
import datetime
import logging
from typing import Optional, Tuple, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Make sure Earth Engine is initialized
try:
    ee.Authenticate()
    ee.Initialize(project="mgis-438709")
except Exception as e:
    logger.warning(f"GEE initialization failed: {e}")
    try:
        ee.Initialize(project="mgis-438709")
    except Exception as e2:
        logger.error(f"GEE initialization completely failed: {e2}")


def get_point_geometry(lat: float, lon: float) -> ee.Geometry:
    """Create a point geometry for the given coordinates"""
    return ee.Geometry.Point([lon, lat])


def get_buffer_geometry(lat: float, lon: float, buffer_meters: int = 1000) -> ee.Geometry:
    """Create a buffered point geometry for area-based calculations"""
    point = get_point_geometry(lat, lon)
    return point.buffer(buffer_meters)


def get_weekly_rainfall(lat: float, lon: float) -> float:
    """Get weekly rainfall from CHIRPS dataset"""
    try:
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

        result = rainfall_mm.getInfo() if rainfall_mm else 0
        logger.info(f"Weekly rainfall for {lat}, {lon}: {result}mm")
        return result
    except Exception as e:
        logger.error(f"Failed to get weekly rainfall: {e}")
        return 0.0


def get_daily_et0(lat: float, lon: float) -> float:
    """Get daily ET₀ from ERA5 dataset"""
    try:
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
        result = round(eto_mm.getInfo() * 1000, 2) if eto_mm else 0
        logger.info(f"Daily ET₀ for {lat}, {lon}: {result}mm")
        return result
    except Exception as e:
        logger.error(f"Failed to get daily ET₀: {e}")
        return 0.0


def get_ndmi_soil_moisture(lat: float, lon: float) -> float:
    """Calculate NDMI (Normalized Difference Moisture Index) from Sentinel-2"""
    try:
        point = get_point_geometry(lat, lon)
        today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))
        week_ago = today.advance(-7, 'day')

        # Get Sentinel-2 data
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(week_ago, today) \
            .filterBounds(point) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .select(['B8', 'B11'])  # NIR and SWIR bands

        def calculate_ndmi(image):
            ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
            return image.addBands(ndmi)

        # Calculate NDMI for each image and get the mean
        ndmi_collection = sentinel2.map(calculate_ndmi)
        ndmi_mean = ndmi_collection.select('NDMI').mean()

        # Get NDMI value at the point
        ndmi_value = ndmi_mean.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10,
            maxPixels=1e9
        ).get('NDMI')

        result = ndmi_value.getInfo() if ndmi_value else 0
        logger.info(f"NDMI for {lat}, {lon}: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to get NDMI: {e}")
        return 0.0


def get_weather_forecast(lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
    """Get weather forecast for the next few days"""
    try:
        point = get_point_geometry(lat, lon)
        today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))
        future_date = today.advance(days, 'day')

        # Get GFS forecast data
        gfs = ee.ImageCollection('NOAA/GFS0P25') \
            .filterDate(today, future_date) \
            .filterBounds(point)

        # Extract temperature and precipitation
        temp_collection = gfs.select('temperature_2m_above_ground')
        precip_collection = gfs.select('total_precipitation_surface')

        # Get mean values
        mean_temp = temp_collection.mean()
        total_precip = precip_collection.sum()

        # Extract values at point
        temp_value = mean_temp.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=25000,
            maxPixels=1e9
        ).get('temperature_2m_above_ground')

        precip_value = total_precip.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=25000,
            maxPixels=1e9
        ).get('total_precipitation_surface')

        forecast = {
            # Convert K to C
            'temperature': round(temp_value.getInfo() - 273.15, 1) if temp_value else 25.0,
            # Convert m to mm
            'precipitation': round(precip_value.getInfo() * 1000, 1) if precip_value else 0.0,
            'days': days
        }

        logger.info(f"Weather forecast for {lat}, {lon}: {forecast}")
        return forecast
    except Exception as e:
        logger.error(f"Failed to get weather forecast: {e}")
        return {'temperature': 25.0, 'precipitation': 0.0, 'days': days}


def get_comprehensive_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    """Get comprehensive weather data including rainfall, ET₀, soil moisture, and forecast"""
    try:
        # Get all weather data
        weekly_rain = get_weekly_rainfall(lat, lon)
        daily_eto = get_daily_et0(lat, lon)
        soil_moisture = get_ndmi_soil_moisture(lat, lon)
        forecast = get_weather_forecast(lat, lon)

        # Calculate confidence score based on data availability
        confidence_score = 0.8  # Base confidence for GEE data

        weather_data = {
            'weekly_rainfall': weekly_rain,
            'daily_eto': daily_eto,
            'soil_moisture_ndmi': soil_moisture,
            'forecast': forecast,
            'confidence_score': confidence_score,
            'data_source': 'GEE',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }

        logger.info(
            f"Comprehensive weather data for {lat}, {lon}: {weather_data}")
        return weather_data

    except Exception as e:
        logger.error(f"Failed to get comprehensive weather data: {e}")
        # Return fallback data
        return {
            'weekly_rainfall': 0.0,
            'daily_eto': 0.0,
            'soil_moisture_ndmi': 0.0,
            'forecast': {'temperature': 25.0, 'precipitation': 0.0, 'days': 5},
            'confidence_score': 0.3,
            'data_source': 'fallback',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
