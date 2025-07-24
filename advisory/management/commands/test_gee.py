from django.core.management.base import BaseCommand
from django.conf import settings
from advisory.utils.gee.gee_data import (
    get_comprehensive_weather_data,
    get_weekly_rainfall,
    get_daily_et0,
    get_ndmi_soil_moisture,
    get_weather_forecast
)
from advisory.utils.recommendation_engine import IrrigationRecommendationEngine
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test GEE integration and EO data fetching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lat',
            type=float,
            default=0.32925,  # Better test coordinates (uganda)
            help='Latitude for testing (default: Uganda)'
        )
        parser.add_argument(
            '--lon',
            type=float,
            default=32.56065,  # Better test coordinates (uganda)
            help='Longitude for testing (default: Uganda)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        lat = options['lat']
        lon = options['lon']
        verbose = options['verbose']

        if verbose:
            logging.basicConfig(level=logging.INFO)

        self.stdout.write(
            self.style.SUCCESS('🌍 Testing GEE Integration with Real EO Data')
        )
        self.stdout.write('=' * 50)
        self.stdout.write(f'📍 Test Location: {lat}, {lon}')
        self.stdout.write('')

        # Test individual data sources
        self.test_rainfall(lat, lon)
        self.test_eto(lat, lon)
        self.test_soil_moisture(lat, lon)
        self.test_forecast(lat, lon)
        self.test_comprehensive_data(lat, lon)
        self.test_recommendation_engine(lat, lon)

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✅ GEE Integration Test Completed!')
        )

    def test_rainfall(self, lat, lon):
        """Test rainfall data fetching"""
        self.stdout.write('1️⃣ Testing Weekly Rainfall (CHIRPS Dataset)')
        self.stdout.write('-' * 40)

        try:
            rainfall = get_weekly_rainfall(lat, lon)
            self.stdout.write(f'✅ Weekly Rainfall: {rainfall} mm')

            if rainfall > 0:
                self.stdout.write(self.style.SUCCESS(
                    '   📊 Real EO data detected!'))
            else:
                self.stdout.write(self.style.WARNING(
                    '   ⚠️  No rainfall data (might be dry season)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Rainfall test failed: {e}'))

        self.stdout.write('')

    def test_eto(self, lat, lon):
        """Test ET₀ data fetching"""
        self.stdout.write('2️⃣ Testing Daily ET₀ (ERA5 Dataset)')
        self.stdout.write('-' * 40)

        try:
            eto = get_daily_et0(lat, lon)
            self.stdout.write(f'✅ Daily ET₀: {eto} mm/day')

            if 0 < eto < 10:  # Reasonable range
                self.stdout.write(self.style.SUCCESS(
                    '   📊 Real EO data detected!'))
            else:
                self.stdout.write(self.style.WARNING(
                    '   ⚠️  ET₀ value outside expected range'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ ET₀ test failed: {e}'))

        self.stdout.write('')

    def test_soil_moisture(self, lat, lon):
        """Test soil moisture data fetching"""
        self.stdout.write('3️⃣ Testing Soil Moisture (Sentinel-2 NDMI)')
        self.stdout.write('-' * 40)

        try:
            soil_moisture = get_ndmi_soil_moisture(lat, lon)
            self.stdout.write(f'✅ Soil Moisture (NDMI): {soil_moisture}')

            if -1 <= soil_moisture <= 1:  # Valid NDMI range
                self.stdout.write(self.style.SUCCESS(
                    '   📊 Real EO data detected!'))
            else:
                self.stdout.write(self.style.WARNING(
                    '   ⚠️  NDMI value outside expected range'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Soil moisture test failed: {e}'))

        self.stdout.write('')

    def test_forecast(self, lat, lon):
        """Test weather forecast data fetching"""
        self.stdout.write('4️⃣ Testing Weather Forecast (GFS Dataset)')
        self.stdout.write('-' * 40)

        try:
            forecast = get_weather_forecast(lat, lon)
            self.stdout.write(f'✅ Temperature: {forecast["temperature"]}°C')
            self.stdout.write(
                f'✅ Precipitation: {forecast["precipitation"]} mm')
            self.stdout.write(f'✅ Forecast Days: {forecast["days"]}')

            if forecast['temperature'] != 25.0:  # Not fallback value
                self.stdout.write(self.style.SUCCESS(
                    '   📊 Real EO data detected!'))
            else:
                self.stdout.write(self.style.WARNING(
                    '   ⚠️  Using fallback forecast data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Forecast test failed: {e}'))

        self.stdout.write('')

    def test_comprehensive_data(self, lat, lon):
        """Test comprehensive weather data"""
        self.stdout.write('5️⃣ Testing Comprehensive Weather Data')
        self.stdout.write('-' * 40)

        try:
            weather_data = get_comprehensive_weather_data(lat, lon)
            self.stdout.write(f'✅ Data Source: {weather_data["data_source"]}')
            self.stdout.write(
                f'✅ Confidence Score: {weather_data["confidence_score"]}')
            self.stdout.write(
                f'✅ GEE Initialized: {weather_data["gee_initialized"]}')

            if weather_data['data_source'] == 'GEE':
                self.stdout.write(self.style.SUCCESS(
                    '   📊 All EO data sources working!'))
            else:
                self.stdout.write(self.style.WARNING(
                    '   ⚠️  Using fallback data sources'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Comprehensive data test failed: {e}'))

        self.stdout.write('')

    def test_recommendation_engine(self, lat, lon):
        """Test recommendation engine with EO data"""
        self.stdout.write('6️⃣ Testing Recommendation Engine with EO Data')
        self.stdout.write('-' * 40)

        try:
            engine = IrrigationRecommendationEngine()

            # Mock field data with proper date format
            from datetime import date
            field_data = {
                'crop_type': 'maize',
                'planting_date': date.today(),  # Use date object instead of string
                'soil_type': 'loam',
                'field_area_ha': 1.0,
                'elevation': 1200.0
            }

            # Get weather data
            weather_data = get_comprehensive_weather_data(lat, lon)

            # Generate recommendation
            recommendation = engine.generate_recommendation(
                field_data, weather_data)

            self.stdout.write(
                f'✅ Irrigation Needed: {recommendation["irrigation_needed"]}')
            self.stdout.write(
                f'✅ Irrigation Volume: {recommendation["irrigation_volume"]} mm')
            self.stdout.write(
                f'✅ Confidence Score: {recommendation["confidence_score"]}')
            self.stdout.write(f'✅ Data Source: {weather_data["data_source"]}')

            if recommendation['confidence_score'] > 0.5:
                self.stdout.write(self.style.SUCCESS(
                    '   📊 High-confidence recommendation generated!'))
            else:
                self.stdout.write(self.style.WARNING(
                    '   ⚠️  Low-confidence recommendation (check data quality)'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Recommendation engine test failed: {e}'))

        self.stdout.write('')
