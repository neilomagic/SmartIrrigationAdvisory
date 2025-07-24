"""
Advanced Irrigation Recommendation Engine
Uses multiple factors to generate intelligent irrigation advice
"""

import logging
from typing import Dict, Any, Tuple
from datetime import date, timedelta
from .crop_coefficients import get_crop_info, get_kc, is_water_sensitive
from .rainfall import get_effective_rainfall

logger = logging.getLogger(__name__)


class IrrigationRecommendationEngine:
    """Advanced irrigation recommendation engine using multiple factors"""

    def __init__(self):
        self.risk_thresholds = {
            'low_risk': 0.3,
            'medium_risk': 0.6,
            'high_risk': 0.8
        }

        self.irrigation_methods = {
            'drip': {'efficiency': 0.9, 'cost': 'high'},
            'sprinkler': {'efficiency': 0.75, 'cost': 'medium'},
            'furrow': {'efficiency': 0.6, 'cost': 'low'},
            'flood': {'efficiency': 0.5, 'cost': 'low'}
        }

    def calculate_water_stress_index(self, soil_moisture: float, crop_type: str) -> float:
        """Calculate water stress index based on soil moisture and crop sensitivity"""
        crop_info = get_crop_info(crop_type)

        # Normalize soil moisture (NDMI typically ranges from -1 to 1)
        # Convert to 0-1 scale where 1 is optimal moisture
        normalized_moisture = (soil_moisture + 1) / 2

        # Adjust based on crop water sensitivity
        if crop_info['water_sensitive']:
            # Water-sensitive crops need higher moisture
            optimal_moisture = 0.7
            stress_factor = 1.5
        else:
            # Drought-tolerant crops can handle lower moisture
            optimal_moisture = 0.5
            stress_factor = 1.0

        # Calculate stress index (0 = no stress, 1 = severe stress)
        if normalized_moisture >= optimal_moisture:
            return 0.0
        else:
            stress = (optimal_moisture - normalized_moisture) / \
                optimal_moisture
            return min(1.0, stress * stress_factor)

    def calculate_drought_risk(self, weather_data: Dict[str, Any], field_data: Dict[str, Any]) -> float:
        """Calculate drought risk based on weather patterns and field conditions"""
        try:
            # Factors contributing to drought risk
            factors = []

            # 1. Low rainfall factor
            weekly_rainfall = weather_data.get('weekly_rainfall', 0)
            expected_rainfall = 25.0  # mm/week (typical for most regions)
            rainfall_factor = max(
                0, (expected_rainfall - weekly_rainfall) / expected_rainfall)
            factors.append(rainfall_factor * 0.4)  # 40% weight

            # 2. High ET₀ factor
            daily_eto = weather_data.get('daily_eto', 0)
            high_eto_threshold = 6.0  # mm/day
            eto_factor = max(0, (daily_eto - high_eto_threshold) /
                             high_eto_threshold) if daily_eto > high_eto_threshold else 0
            factors.append(eto_factor * 0.3)  # 30% weight

            # 3. Forecast factor
            forecast = weather_data.get('forecast', {})
            forecast_rain = forecast.get('precipitation', 0)
            forecast_factor = max(
                0, (expected_rainfall - forecast_rain) / expected_rainfall)
            factors.append(forecast_factor * 0.2)  # 20% weight

            # 4. Soil type factor
            soil_type = field_data.get('soil_type', 'loam')
            soil_retention = {
                'clay': 0.8, 'clay_loam': 0.7, 'loam': 0.6,
                'sandy_loam': 0.5, 'sandy': 0.3, 'silt': 0.7
            }
            soil_factor = 1 - soil_retention.get(soil_type, 0.6)
            factors.append(soil_factor * 0.1)  # 10% weight

            # Calculate weighted average
            drought_risk = sum(factors)
            return min(1.0, drought_risk)

        except Exception as e:
            logger.error(f"Error calculating drought risk: {e}")
            return 0.5  # Default medium risk

    def calculate_irrigation_volume(self, field_data: Dict[str, Any], weather_data: Dict[str, Any]) -> float:
        """Calculate recommended irrigation volume in mm"""
        try:
            # Get crop and field information
            crop_type = field_data.get('crop_type', 'maize')
            planting_date = field_data.get('planting_date')
            soil_type = field_data.get('soil_type', 'loam')

            # Ensure planting_date is a date object
            if isinstance(planting_date, str):
                from datetime import datetime
                planting_date = datetime.strptime(
                    planting_date, '%Y-%m-%d').date()
            elif planting_date is None:
                planting_date = date.today()

            # Calculate crop water need
            kc, stage = get_kc(crop_type, planting_date)
            daily_eto = weather_data.get('daily_eto', 0)
            weekly_need = daily_eto * kc * 7  # mm/week

            # Get effective rainfall
            weekly_rainfall = weather_data.get('weekly_rainfall', 0)
            effective_rainfall = get_effective_rainfall(
                weekly_rainfall, soil_type)

            # Calculate deficit
            deficit = max(0, weekly_need - effective_rainfall)

            # Adjust based on soil moisture
            soil_moisture = weather_data.get('soil_moisture_ndmi', 0)
            water_stress = self.calculate_water_stress_index(
                soil_moisture, crop_type)

            # Apply stress factor
            adjusted_deficit = deficit * (1 + water_stress * 0.5)

            # Apply irrigation efficiency factor
            irrigation_efficiency = 0.8  # Default efficiency
            final_volume = adjusted_deficit / irrigation_efficiency

            return round(final_volume, 1)

        except Exception as e:
            logger.error(f"Error calculating irrigation volume: {e}")
            return 0.0

    def determine_irrigation_timing(self, weather_data: Dict[str, Any], field_data: Dict[str, Any]) -> str:
        """Determine optimal irrigation timing"""
        try:
            forecast = weather_data.get('forecast', {})
            forecast_rain = forecast.get('precipitation', 0)
            drought_risk = self.calculate_drought_risk(
                weather_data, field_data)

            if drought_risk > self.risk_thresholds['high_risk']:
                return "immediate"
            elif forecast_rain < 5:  # Less than 5mm forecast
                return "within_2_days"
            elif drought_risk > self.risk_thresholds['medium_risk']:
                return "within_3_days"
            else:
                return "within_week"

        except Exception as e:
            logger.error(f"Error determining irrigation timing: {e}")
            return "within_week"

    def recommend_irrigation_method(self, field_data: Dict[str, Any], irrigation_volume: float) -> str:
        """Recommend irrigation method based on field conditions and volume"""
        try:
            crop_type = field_data.get('crop_type', 'maize')
            field_area = field_data.get('field_area_ha', 1.0)

            # Water-sensitive crops benefit from precise irrigation
            if is_water_sensitive(crop_type):
                if field_area <= 2.0:  # Small fields
                    return "drip"
                else:
                    return "sprinkler"

            # Large volumes favor flood irrigation
            if irrigation_volume > 50:  # mm
                return "flood"
            elif irrigation_volume > 20:
                return "furrow"
            else:
                return "sprinkler"

        except Exception as e:
            logger.error(f"Error recommending irrigation method: {e}")
            return "sprinkler"

    def calculate_confidence_score(self, weather_data: Dict[str, Any]) -> float:
        """Calculate confidence in the recommendation"""
        try:
            base_confidence = weather_data.get('confidence_score', 0.5)
            data_source = weather_data.get('data_source', 'simulated')

            # Adjust confidence based on data source
            source_confidence = {
                'GEE': 0.9,
                'API': 0.7,
                'simulated': 0.5,
                'fallback': 0.3
            }

            source_score = source_confidence.get(data_source, 0.5)

            # Combine base confidence with source confidence
            final_confidence = (base_confidence + source_score) / 2

            return round(final_confidence, 2)

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5

    def generate_recommendation(self, field_data: Dict[str, Any], weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive irrigation recommendation"""
        try:
            # Calculate key metrics
            water_stress = self.calculate_water_stress_index(
                weather_data.get('soil_moisture_ndmi', 0),
                field_data.get('crop_type', 'maize')
            )

            drought_risk = self.calculate_drought_risk(
                weather_data, field_data)
            irrigation_volume = self.calculate_irrigation_volume(
                field_data, weather_data)
            timing = self.determine_irrigation_timing(weather_data, field_data)
            method = self.recommend_irrigation_method(
                field_data, irrigation_volume)
            confidence = self.calculate_confidence_score(weather_data)

            # Determine if irrigation is needed
            irrigation_needed = irrigation_volume > 5.0  # Minimum 5mm threshold

            # Generate recommendation message
            message = self._generate_message(
                irrigation_needed, irrigation_volume, timing, method,
                water_stress, drought_risk, field_data
            )

            # Determine priority level
            if drought_risk > self.risk_thresholds['high_risk'] or water_stress > 0.8:
                priority = "high"
            elif drought_risk > self.risk_thresholds['medium_risk'] or water_stress > 0.5:
                priority = "medium"
            else:
                priority = "low"

            recommendation = {
                'irrigation_needed': irrigation_needed,
                'irrigation_volume': irrigation_volume,
                'timing': timing,
                'method': method,
                'priority': priority,
                'confidence_score': confidence,
                'water_stress_index': water_stress,
                'drought_risk': drought_risk,
                'recommendation_message': message,
                'weather_summary': {
                    'weekly_rainfall': weather_data.get('weekly_rainfall', 0),
                    'daily_eto': weather_data.get('daily_eto', 0),
                    'soil_moisture': weather_data.get('soil_moisture_ndmi', 0),
                    'forecast_rain': weather_data.get('forecast', {}).get('precipitation', 0)
                }
            }

            logger.info(f"Generated recommendation: {recommendation}")
            return recommendation

        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {
                'irrigation_needed': False,
                'irrigation_volume': 0.0,
                'timing': 'within_week',
                'method': 'sprinkler',
                'priority': 'low',
                'confidence_score': 0.3,
                'water_stress_index': 0.0,
                'drought_risk': 0.5,
                'recommendation_message': 'Unable to generate recommendation due to data issues.',
                'weather_summary': {}
            }

    def _generate_message(self, irrigation_needed: bool, volume: float, timing: str,
                          method: str, water_stress: float, drought_risk: float,
                          field_data: Dict[str, Any]) -> str:
        """Generate human-readable recommendation message"""
        try:
            crop_name = field_data.get('crop_type', 'crop').capitalize()

            if not irrigation_needed:
                return f"✅ No irrigation needed for {crop_name}. Sufficient rainfall and soil moisture available."

            # Format timing
            timing_text = {
                'immediate': 'immediately',
                'within_2_days': 'within 2 days',
                'within_3_days': 'within 3 days',
                'within_week': 'this week'
            }.get(timing, 'this week')

            # Format method
            method_text = {
                'drip': 'drip irrigation',
                'sprinkler': 'sprinkler irrigation',
                'furrow': 'furrow irrigation',
                'flood': 'flood irrigation'
            }.get(method, 'irrigation')

            # Base message
            message = f"💧 Apply {volume}mm of water using {method_text} {timing_text}."

            # Add urgency indicators
            if drought_risk > 0.8:
                message += " ⚠️ High drought risk - urgent action required."
            elif water_stress > 0.7:
                message += " ⚠️ High water stress detected."

            # Add efficiency tip
            if method == 'drip':
                message += " 💡 Drip irrigation recommended for water efficiency."
            elif method == 'sprinkler':
                message += " 💡 Apply in early morning to reduce evaporation."

            return message

        except Exception as e:
            logger.error(f"Error generating message: {e}")
            return "Apply irrigation as needed based on field conditions."
