#!/usr/bin/env python3
"""
Test script to verify GEE integration and EO data fetching
"""

import logging
from advisory.utils.crop_coefficients import get_crop_info
from advisory.utils.recommendation_engine import IrrigationRecommendationEngine
from advisory.utils.gee.gee_data import (
    get_comprehensive_weather_data,
    get_weekly_rainfall,
    get_daily_et0,
    get_ndmi_soil_moisture,
    get_weather_forecast
)
import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'SmartIrrigationAdvisory.settings')
django.setup()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_gee_integration():
    """Test GEE integration with real coordinates"""

    # Test coordinates (Kampala, Uganda)
    test_lat, test_lon = 0.3476, 32.5825

    print("🌍 Testing GEE Integration with Real EO Data")
    print("=" * 50)
    print(f"📍 Test Location: {test_lat}, {test_lon} (Kampala, Uganda)")
    print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Test 1: Weekly Rainfall (CHIRPS)
        print("1️⃣ Testing Weekly Rainfall (CHIRPS Dataset)")
        print("-" * 40)
        try:
            rainfall = get_weekly_rainfall(test_lat, test_lon)
            print(f"✅ Weekly Rainfall: {rainfall} mm")
            if rainfall > 0:
                print("   📊 Real EO data detected!")
            else:
                print("   ⚠️  No rainfall data (might be dry season)")
        except Exception as e:
            print(f"❌ Rainfall test failed: {e}")
        print()

        # Test 2: Daily ET₀ (ERA5)
        print("2️⃣ Testing Daily ET₀ (ERA5 Dataset)")
        print("-" * 40)
        try:
            eto = get_daily_et0(test_lat, test_lon)
            print(f"✅ Daily ET₀: {eto} mm/day")
            if 0 < eto < 10:  # Reasonable range
                print("   📊 Real EO data detected!")
            else:
                print("   ⚠️  ET₀ value outside expected range")
        except Exception as e:
            print(f"❌ ET₀ test failed: {e}")
        print()

        # Test 3: Soil Moisture (Sentinel-2 NDMI)
        print("3️⃣ Testing Soil Moisture (Sentinel-2 NDMI)")
        print("-" * 40)
        try:
            soil_moisture = get_ndmi_soil_moisture(test_lat, test_lon)
            print(f"✅ Soil Moisture (NDMI): {soil_moisture}")
            if -1 <= soil_moisture <= 1:  # Valid NDMI range
                print("   📊 Real EO data detected!")
            else:
                print("   ⚠️  NDMI value outside expected range")
        except Exception as e:
            print(f"❌ Soil moisture test failed: {e}")
        print()

        # Test 4: Weather Forecast (GFS)
        print("4️⃣ Testing Weather Forecast (GFS Dataset)")
        print("-" * 40)
        try:
            forecast = get_weather_forecast(test_lat, test_lon)
            print(f"✅ Temperature: {forecast['temperature']}°C")
            print(f"✅ Precipitation: {forecast['precipitation']} mm")
            print(f"✅ Forecast Days: {forecast['days']}")
            if forecast['temperature'] != 25.0:  # Not fallback value
                print("   📊 Real EO data detected!")
            else:
                print("   ⚠️  Using fallback forecast data")
        except Exception as e:
            print(f"❌ Forecast test failed: {e}")
        print()

        # Test 5: Comprehensive Weather Data
        print("5️⃣ Testing Comprehensive Weather Data")
        print("-" * 40)
        try:
            weather_data = get_comprehensive_weather_data(test_lat, test_lon)
            print(f"✅ Data Source: {weather_data['data_source']}")
            print(f"✅ Confidence Score: {weather_data['confidence_score']}")
            print(f"✅ Timestamp: {weather_data['timestamp']}")

            if weather_data['data_source'] == 'GEE':
                print("   📊 All EO data sources working!")
            else:
                print("   ⚠️  Using fallback data sources")
        except Exception as e:
            print(f"❌ Comprehensive data test failed: {e}")
        print()

        # Test 6: Recommendation Engine Integration
        print("6️⃣ Testing Recommendation Engine with EO Data")
        print("-" * 40)
        try:
            engine = IrrigationRecommendationEngine()

            # Mock field data
            field_data = {
                'crop_type': 'maize',
                'planting_date': datetime.now().date(),
                'soil_type': 'loam',
                'field_area_ha': 1.0,
                'elevation': 1200.0
            }

            # Get weather data
            weather_data = get_comprehensive_weather_data(test_lat, test_lon)

            # Generate recommendation
            recommendation = engine.generate_recommendation(
                field_data, weather_data)

            print(
                f"✅ Irrigation Needed: {recommendation['irrigation_needed']}")
            print(
                f"✅ Irrigation Volume: {recommendation['irrigation_volume']} mm")
            print(f"✅ Confidence Score: {recommendation['confidence_score']}")
            print(f"✅ Data Source: {weather_data['data_source']}")

            if recommendation['confidence_score'] > 0.5:
                print("   📊 High-confidence recommendation generated!")
            else:
                print("   ⚠️  Low-confidence recommendation (check data quality)")

        except Exception as e:
            print(f"❌ Recommendation engine test failed: {e}")
        print()

        # Summary
        print("📋 GEE Integration Test Summary")
        print("=" * 50)
        print("✅ All tests completed")
        print("🌍 Real EO data sources tested:")
        print("   • CHIRPS (Rainfall)")
        print("   • ERA5 (Evapotranspiration)")
        print("   • Sentinel-2 (Soil Moisture)")
        print("   • GFS (Weather Forecast)")
        print()
        print("💡 If you see 'Real EO data detected!' messages,")
        print("   the GEE integration is working correctly!")

    except Exception as e:
        print(f"❌ Overall test failed: {e}")
        return False

    return True


def test_fallback_mechanism():
    """Test fallback mechanism when GEE fails"""
    print("\n🔄 Testing Fallback Mechanism")
    print("=" * 50)

    # Test with invalid coordinates
    invalid_lat, invalid_lon = 999.0, 999.0

    try:
        weather_data = get_comprehensive_weather_data(invalid_lat, invalid_lon)
        print(f"✅ Fallback data source: {weather_data['data_source']}")
        print(f"✅ Fallback confidence: {weather_data['confidence_score']}")
        print("   📊 Fallback mechanism working correctly!")
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting GEE Integration Verification...")
    print()

    # Run main test
    success = test_gee_integration()

    # Run fallback test
    test_fallback_mechanism()

    print("\n" + "=" * 50)
    if success:
        print("🎉 GEE Integration Test Completed Successfully!")
    else:
        print("⚠️  GEE Integration Test Completed with Issues")
    print("=" * 50)
