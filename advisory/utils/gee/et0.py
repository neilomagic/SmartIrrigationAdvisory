from datetime import datetime
import ee

# Purpose: Fetches real-time ET₀ from ERA5 (replaces hardcoded values).


def get_et0(field_geometry):
    era5 = ee.ImageCollection("ECMWF/ERA5/DAILY") \
        .filterDate(ee.Date(datetime.now().strftime('%Y-%m-%d'))) \
        .select(['mean_2m_air_temperature', 'surface_solar_radiation_downwards'])

    # Hargreaves-Samani approximation (simplified FAO-PM)
    et0 = era5.map(lambda img:
                   img.select('surface_solar_radiation_downwards')
                   .multiply(0.0023)
                   .multiply(img.select('mean_2m_air_temperature').add(17.8))
                   .rename('ET0')
                   )
    return et0.mean().clip(field_geometry)
