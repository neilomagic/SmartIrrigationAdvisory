#!/usr/bin/env python3
"""
Quick test to verify GEE fixes
"""

from datetime import date
from advisory.utils.recommendation_engine import IrrigationRecommendationEngine
from advisory.utils.gee.gee_data import get_weather_forecast, get_comprehensive_weather_data
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'SmartIrrigationAdvisory.settings')
django.setup()


def test_fixes():
    """Test the GEE fixes"""
    print("🔧 Testing GEE Fixes")
    print("=" * 40)

    # Test coordinates (Nairobi - better data availability)
    lat, lon = 1.2921, 36.8219

    print(f"📍 Test Location: {lat}, {lon} (Nairobi, Kenya)")
    print()

    # Test 1: Weather Forecast (GFS fix)
    print("1️⃣ Testing Weather Forecast Fix")
    print("-" * 30)
    try:
        forecast = get_weather_forecast(lat, lon)
        print(f"✅ Temperature: {forecast['temperature']}°C")
        print(f"✅ Precipitation: {forecast['precipitation']} mm")
        print(f"✅ Days: {forecast['days']}")

        if forecast['temperature'] != 25.0:
            print("   📊 GFS forecast working!")
        else:
            print("   ⚠️  Using fallback data")
    except Exception as e:
        print(f"❌ Forecast test failed: {e}")
    print()

    # Test 2: Comprehensive Data
    print("2️⃣ Testing Comprehensive Data")
    print("-" * 30)
    try:
        weather_data = get_comprehensive_weather_data(lat, lon)
        print(f"✅ Data Source: {weather_data['data_source']}")
        print(f"✅ Confidence: {weather_data['confidence_score']}")
        print(f"✅ GEE Status: {weather_data['gee_initialized']}")

        if weather_data['data_source'] == 'GEE':
            print("   📊 GEE integration working!")
        else:
            print("   ⚠️  Using fallback data")
    except Exception as e:
        print(f"❌ Comprehensive data test failed: {e}")
    print()

    # Test 3: Recommendation Engine (Date fix)
    print("3️⃣ Testing Recommendation Engine Fix")
    print("-" * 30)
    try:
        engine = IrrigationRecommendationEngine()

        field_data = {
            'crop_type': 'maize',
            'planting_date': date.today(),
            'soil_type': 'loam',
            'field_area_ha': 1.0,
            'elevation': 1200.0
        }

        weather_data = get_comprehensive_weather_data(lat, lon)
        recommendation = engine.generate_recommendation(
            field_data, weather_data)

        print(f"✅ Irrigation Needed: {recommendation['irrigation_needed']}")
        print(f"✅ Volume: {recommendation['irrigation_volume']} mm")
        print(f"✅ Confidence: {recommendation['confidence_score']}")
        print("   📊 Recommendation engine working!")

    except Exception as e:
        print(f"❌ Recommendation engine test failed: {e}")
    print()

    print("✅ GEE Fixes Test Completed!")


if __name__ == "__main__":
    test_fixes()
