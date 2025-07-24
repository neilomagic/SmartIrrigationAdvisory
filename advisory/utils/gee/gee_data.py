import ee
import datetime
import logging
from typing import Optional, Tuple, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Earth Engine with better error handling


def initialize_gee():
    """Initialize Google Earth Engine with proper error handling"""
    try:
        # Try to authenticate first
        try:
            ee.Authenticate()
            logger.info("GEE authentication successful")
        except Exception as auth_error:
            logger.warning(f"GEE authentication failed: {auth_error}")

        # Initialize with project
        ee.Initialize(project="mgis-438709")
        logger.info("GEE initialization successful")
        return True
    except Exception as e:
        logger.error(f"GEE initialization failed: {e}")
        return False


# Initialize GEE on module import
GEE_INITIALIZED = initialize_gee()


def get_point_geometry(lat: float, lon: float) -> ee.Geometry:
    """Create a point geometry for the given coordinates"""
    return ee.Geometry.Point([lon, lat])


def get_buffer_geometry(lat: float, lon: float, buffer_meters: int = 1000) -> ee.Geometry:
    """Create a buffered point geometry for area-based calculations"""
    point = get_point_geometry(lat, lon)
    return point.buffer(buffer_meters)


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate that coordinates are within reasonable bounds"""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def get_weekly_rainfall(lat: float, lon: float) -> float:
    """Get weekly rainfall from CHIRPS dataset with improved error handling"""
    if not GEE_INITIALIZED:
        logger.warning("GEE not initialized, using fallback rainfall data")
        return 0.0

    if not validate_coordinates(lat, lon):
        logger.error(f"Invalid coordinates: {lat}, {lon}")
        return 0.0

    try:
        # point = get_point_geometry(lat, lon)
        point = get_buffer_geometry(
            lat, lon, buffer_meters=10000)  # 5km buffer
        today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))
        week_ago = today.advance(-30, 'day')

        # Get CHIRPS daily rainfall data
        dataset = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") \
                    .filterDate(week_ago, today) \
                    .filterBounds(point)

        # Check if we have data
        image = dataset.first()
        if image is None:
            logger.warning(f"No CHIRPS image available for {lat}, {lon}")
            return 0.0
        # dataset_size = dataset.size().getInfo()
        # if dataset_size == 0:
        #     logger.warning(f"No CHIRPS data available for {lat}, {lon}")
        #     return 0.0

        rainfall_image = dataset.select('precipitation').sum()
        reduction = rainfall_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=5000,
            maxPixels=1e9
        )
        reduction_dict = reduction.getInfo()
        # result = rainfall_mm.getInfo() if rainfall_mm else 0
        logger.debug(f"Reduction result keys: {list(reduction_dict.keys())}")

        if 'precipitation' in reduction_dict:
            result = reduction_dict['precipitation']
        else:
            logger.warning(
                "Key 'precipitation' not found in reduceRegion output")
            result = 0.0

        # Validate result
        if result is None or result < 0:
            logger.warning(f"Invalid rainfall value: {result}")
            return 0.0

        logger.info(f"Weekly rainfall for {lat}, {lon}: {result}mm")
        return float(result)

    except Exception as e:
        logger.error(f"Failed to get weekly rainfall: {e}")
        return 0.0


def get_daily_et0(lat: float, lon: float) -> float:
    """Get daily ET₀ from ERA5 dataset with improved error handling"""
    if not GEE_INITIALIZED:
        logger.warning("GEE not initialized, using fallback ET₀ data")
        return 0.0

    if not validate_coordinates(lat, lon):
        logger.error(f"Invalid coordinates: {lat}, {lon}")
        return 0.0

    try:
        # point = get_point_geometry(lat, lon)
        point = get_buffer_geometry(
            lat, lon, buffer_meters=10000)  # 100km buffer
        today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))

        # Get ERA5 daily aggregated data
        dataset = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
                    .filterDate(today.advance(-15, 'day'), today.advance(-0, 'day')) \
                    .filterBounds(point)

        # Check if we have data
        dataset_size = dataset.size().getInfo()
        if dataset_size == 0:
            logger.warning(f"No ERA5 data available for {lat}, {lon}")
            return 0.0

        image = dataset.first()
        eto_image = image.select('potential_evaporation_sum')
        eto_image2 = dataset.select('potential_evaporation_sum').mean()
        # print(f"ET₀ image mean: {eto_image2}")
        eto_mm = eto_image.reduceRegion(
            reducer=ee.Reducer.mean().unweighted(),
            geometry=point,
            scale=1000,
            maxPixels=1e9
        ).get('potential_evaporation_sum')
        # print(f"ET₀ mm: {eto_mm}")
        # Convert from m to mm and validate
        if eto_mm:
            result = eto_mm.getInfo()
            print(f"ET₀ mm getInfo: {result}")
            if result is not None:
                result = round(float(result) / 2.45e6, 2)  # Convert J/m² → mm
                if result == -0.0:
                    result = 0.0
            else:
                result = 0.0
        else:
            result = 0.0

        # result = eto_mm.getInfo() if eto_mm else 0
        # if result is not None:
        #     # NEW (correct) — convert J/m² to mm using latent heat
        #     result = round(float(result) / 2.45e6, 2)  # ✅ correct

        #     # result = round(float(result) * 1000, 2)  # Convert m to mm
        # else:
        #     result = 0.0

        # Validate result (reasonable ET₀ range: 0-15 mm/day)
        if result < 0 or result > 15:
            logger.warning(
                f"ET₀ value outside reasonable range: {result} mm/day")
            result = max(0, min(15, result))  # Clamp to reasonable range

        logger.info(f"Daily ET₀ for {lat}, {lon}: {result}mm")
        return result

    except Exception as e:
        logger.error(f"Failed to get daily ET₀: {e}")
        return 0.0


def get_ndmi_soil_moisture(lat: float, lon: float) -> float:
    """Calculate NDMI (Normalized Difference Moisture Index) from Sentinel-2 with improved error handling"""
    if not GEE_INITIALIZED:
        logger.warning(
            "GEE not initialized, using fallback soil moisture data")
        return 0.0

    if not validate_coordinates(lat, lon):
        logger.error(f"Invalid coordinates: {lat}, {lon}")
        return 0.0

    try:
        # point = get_point_geometry(lat, lon)
        point = get_buffer_geometry(lat, lon, buffer_meters=1000)  # 1km buffer
        today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))
        week_ago = today.advance(-30, 'day')

        # Get Sentinel-2 data with cloud filtering (using current dataset)
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterDate(week_ago, today) \
            .filterBounds(point) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)) \
            .select(['B8', 'B11'])  # NIR and SWIR bands

        # Check if we have data
        dataset_size = sentinel2.size().getInfo()
        print(f"Sentinel-2 dataset size: {dataset_size}")
        if dataset_size == 0:
            logger.warning(f"No Sentinel-2 data available for {lat}, {lon}")
            return 0.0

        # def calculate_ndmi(image):
        #     ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
        #     return image.addBands(ndmi)
        def calculate_ndmi(image):
            return image.addBands(image.normalizedDifference(['B8', 'B11']).rename('NDMI'))

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

        # Validate NDMI result (should be between -1 and 1)
        if result is not None:
            result = float(result)
            if result < -1 or result > 1:
                logger.warning(f"NDMI value outside valid range: {result}")
                result = max(-1, min(1, result))  # Clamp to valid range
        else:
            result = 0.0

        logger.info(f"NDMI for {lat}, {lon}: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to get NDMI: {e}")
        return 0.0


def get_weather_forecast(lat: float, lon: float, days: int = 5) -> Dict[str, Any]:
    """Get weather forecast for the next few days with improved error handling"""
    if not GEE_INITIALIZED:
        logger.warning("GEE not initialized, using fallback forecast data")
        return {'temperature': 25.0, 'precipitation': 0.0, 'days': days}

    if not validate_coordinates(lat, lon):
        logger.error(f"Invalid coordinates: {lat}, {lon}")
        return {'temperature': 25.0, 'precipitation': 0.0, 'days': days}

    try:
        point = get_point_geometry(lat, lon)
        today = ee.Date(datetime.datetime.utcnow().strftime('%Y-%m-%d'))
        future_date = today.advance(days, 'day')

        # Get GFS forecast data
        gfs = ee.ImageCollection('NOAA/GFS0P25') \
            .filterDate(today, future_date) \
            .filterBounds(point)

        # Check if we have data
        dataset_size = gfs.size().getInfo()
        if dataset_size == 0:
            logger.warning(f"No GFS forecast data available for {lat}, {lon}")
            return {'temperature': 25.0, 'precipitation': 0.0, 'days': days}

        # Extract temperature and precipitation (using correct band names)
        temp_collection = gfs.select('temperature_2m_above_ground')
        precip_collection = gfs.select('precipitation_rate')  # kg/m²/s

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
        ).get('precipitation_rate')

        # Process and validate results
        temp_k = temp_value.getInfo() if temp_value else 298.15  # Default 25°C in Kelvin
        precip_rate = precip_value.getInfo() if precip_value else 0.0

        # Validate temperature before conversion
        if temp_k is None or temp_k < 100 or temp_k > 400:  # Reasonable Kelvin range
            logger.warning(
                f"Invalid temperature value: {temp_k}K, using default")
            temp_k = 298.15  # 25°C in Kelvin

        # Convert units and validate
        temp_c = round(float(temp_k) - 273.15, 1)  # Convert K to C

        # Convert precipitation rate (kg/m²/s) to mm for forecast period
        # 1 kg/m² = 1 mm, so kg/m²/s * seconds = mm
        if precip_rate is None or precip_rate < 0:
            logger.warning(
                f"Invalid precipitation rate: {precip_rate}, using 0")
            precip_rate = 0.0

        # Convert to mm for the forecast period (assuming daily rate * days)
        # Limit to reasonable range
        precip_mm = min(200.0, float(precip_rate) *
                        86400 * days / 1000)  # Cap at 200mm
        precip_mm = round(max(0.0, precip_mm), 1)

        # Final validation
        if temp_c < -50 or temp_c > 60:
            logger.warning(f"Temperature outside reasonable range: {temp_c}°C")
            temp_c = max(-50, min(60, temp_c))

        forecast = {
            'temperature': temp_c,
            'precipitation': precip_mm,
            'days': days
        }

        logger.info(f"Weather forecast for {lat}, {lon}: {forecast}")
        return forecast

    except Exception as e:
        logger.error(f"Failed to get weather forecast: {e}")
        return {'temperature': 25.0, 'precipitation': 0.0, 'days': days}


def get_comprehensive_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    """Get comprehensive weather data including rainfall, ET₀, soil moisture, and forecast with improved validation"""
    if not validate_coordinates(lat, lon):
        logger.error(f"Invalid coordinates provided: {lat}, {lon}")
        return _get_fallback_weather_data()

    try:
        # Get all weather data with individual error handling
        weekly_rain = get_weekly_rainfall(lat, lon)
        daily_eto = get_daily_et0(lat, lon)
        soil_moisture = get_ndmi_soil_moisture(lat, lon)
        forecast = get_weather_forecast(lat, lon)

        # Calculate confidence score based on data availability and quality
        confidence_score = _calculate_confidence_score(
            weekly_rain, daily_eto, soil_moisture, forecast
        )

        # Determine data source
        data_source = 'GEE' if GEE_INITIALIZED and confidence_score > 0.5 else 'fallback'

        weather_data = {
            'weekly_rainfall': weekly_rain,
            'daily_eto': daily_eto,
            'soil_moisture_ndmi': soil_moisture,
            'forecast': forecast,
            'confidence_score': confidence_score,
            'data_source': data_source,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'gee_initialized': GEE_INITIALIZED
        }

        logger.info(
            f"Comprehensive weather data for {lat}, {lon}: {weather_data}")
        return weather_data

    except Exception as e:
        logger.error(f"Failed to get comprehensive weather data: {e}")
        return _get_fallback_weather_data()


def _calculate_confidence_score(rainfall: float, eto: float, soil_moisture: float, forecast: Dict) -> float:
    """Calculate confidence score based on data quality and availability"""
    score = 0.0
    factors = 0

    # Rainfall confidence - only give credit if we have actual data
    if rainfall > 0:
        score += 0.8
        factors += 1
    elif rainfall == 0:
        # Could be real zero or no data - lower confidence
        score += 0.3
        factors += 1

    # ET₀ confidence - similar logic
    if 1 <= eto <= 15:  # Realistic positive range
        score += 0.8
        factors += 1
    elif eto == 0:
        # No ET₀ data available
        score += 0.2
        factors += 1

    # Soil moisture confidence - NDMI can be zero but should be in valid range
    if -1 <= soil_moisture <= 1 and soil_moisture != 0:
        score += 0.7
        factors += 1
    elif soil_moisture == 0:
        # Could be real zero or no data
        score += 0.3
        factors += 1

    # Forecast confidence - check for realistic values
    temp = forecast.get('temperature', 25)
    precip = forecast.get('precipitation', 0)

    if temp != 25.0 and -50 <= temp <= 60:  # Not fallback and realistic
        score += 0.6
        factors += 1
    elif temp == 25.0:  # Fallback value
        score += 0.2
        factors += 1

    # Additional check for unrealistic forecast values
    if precip > 100:  # Very high precipitation suggests data error
        score -= 0.2

    # Calculate average confidence
    if factors > 0:
        confidence = score / factors
        # Cap confidence at 0.5 if all primary data sources return 0
        if rainfall == 0 and eto == 0 and soil_moisture == 0:
            confidence = min(0.5, confidence)
        return round(confidence, 2)
    else:
        return 0.3


def _get_fallback_weather_data() -> Dict[str, Any]:
    """Get fallback weather data when GEE fails"""
    return {
        'weekly_rainfall': 0.0,
        'daily_eto': 0.0,
        'soil_moisture_ndmi': 0.0,
        'forecast': {'temperature': 25.0, 'precipitation': 0.0, 'days': 5},
        'confidence_score': 0.3,
        'data_source': 'fallback',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'gee_initialized': False
    }
