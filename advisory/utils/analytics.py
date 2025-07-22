"""
Advanced Analytics Module for Smart Irrigation Advisory
Provides insights, trends, and predictive analytics
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import date, timedelta
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from advisory.models import FarmField, IrrigationAdvisory
from .crop_coefficients import get_crop_info

logger = logging.getLogger(__name__)


class IrrigationAnalytics:
    """Advanced analytics for irrigation advisory system"""

    def __init__(self):
        self.analysis_periods = {
            'week': 7,
            'month': 30,
            'quarter': 90,
            'year': 365
        }

    def get_field_performance_summary(self, field_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive performance summary for a field"""
        try:
            field = FarmField.objects.get(id=field_id)
            start_date = date.today() - timedelta(days=period_days)

            # Get advisories for the period
            advisories = IrrigationAdvisory.objects.filter(
                field=field,
                date__gte=start_date
            ).order_by('date')

            if not advisories.exists():
                return self._empty_performance_summary()

            # Calculate key metrics
            total_advisories = advisories.count()
            irrigation_recommended = advisories.filter(
                irrigation_recommended=True).count()
            total_irrigation_volume = advisories.filter(irrigation_recommended=True).aggregate(
                total=Sum('irrigation_volume'))['total'] or 0
            avg_confidence = advisories.aggregate(
                avg=Avg('confidence_score'))['avg'] or 0

            # Calculate water use efficiency
            total_rainfall = advisories.aggregate(
                total=Sum('rainfall'))['total'] or 0
            total_water_need = advisories.aggregate(
                total=Sum('water_need'))['total'] or 0

            # Water use efficiency = (rainfall + irrigation) / water_need
            water_use_efficiency = 0
            if total_water_need > 0:
                water_use_efficiency = min(
                    1.0, (total_rainfall + total_irrigation_volume) / total_water_need)

            # Calculate cost savings (assuming 40% water savings with advisory)
            baseline_irrigation = total_water_need * \
                0.4  # Assume 40% more without advisory
            water_saved = baseline_irrigation - total_irrigation_volume
            cost_savings = water_saved * 0.1  # Assume $0.1 per mm of water

            # Get trend analysis
            trends = self._analyze_trends(advisories)

            return {
                'field_name': field.name,
                'crop_type': field.crop_type,
                'period_days': period_days,
                'total_advisories': total_advisories,
                'irrigation_recommended_count': irrigation_recommended,
                'irrigation_frequency': irrigation_recommended / total_advisories if total_advisories > 0 else 0,
                'total_irrigation_volume': round(total_irrigation_volume, 1),
                'avg_irrigation_volume': round(total_irrigation_volume / irrigation_recommended, 1) if irrigation_recommended > 0 else 0,
                'avg_confidence': round(avg_confidence, 2),
                'water_use_efficiency': round(water_use_efficiency, 2),
                'total_rainfall': round(total_rainfall, 1),
                'total_water_need': round(total_water_need, 1),
                'water_saved': round(water_saved, 1),
                'cost_savings': round(cost_savings, 2),
                'trends': trends,
                'data_quality': self._assess_data_quality(advisories),
                'recommendations': self._generate_performance_recommendations(
                    water_use_efficiency, avg_confidence, irrigation_recommended, total_advisories
                )
            }

        except Exception as e:
            logger.error(
                f"Error generating performance summary for field {field_id}: {e}")
            return self._empty_performance_summary()

    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics and insights"""
        try:
            # Get all fields and advisories
            total_fields = FarmField.objects.count()
            total_advisories = IrrigationAdvisory.objects.count()

            # Crop distribution
            crop_distribution = {}
            for field in FarmField.objects.all():
                crop = field.crop_type
                crop_distribution[crop] = crop_distribution.get(crop, 0) + 1

            # Water use efficiency by crop
            crop_efficiency = {}
            for crop in crop_distribution.keys():
                crop_fields = FarmField.objects.filter(crop_type=crop)
                crop_advisories = IrrigationAdvisory.objects.filter(
                    field__in=crop_fields)

                if crop_advisories.exists():
                    total_irrigation = crop_advisories.filter(irrigation_recommended=True).aggregate(
                        total=Sum('irrigation_volume'))['total'] or 0
                    total_need = crop_advisories.aggregate(
                        total=Sum('water_need'))['total'] or 0

                    efficiency = 0
                    if total_need > 0:
                        efficiency = min(1.0, total_irrigation / total_need)

                    crop_efficiency[crop] = round(efficiency, 2)

            # Regional analysis (by latitude/longitude ranges)
            regional_analysis = self._analyze_regional_patterns()

            # Data source quality
            data_source_quality = self._analyze_data_source_quality()

            # Seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns()

            return {
                'total_fields': total_fields,
                'total_advisories': total_advisories,
                'crop_distribution': crop_distribution,
                'crop_efficiency': crop_efficiency,
                'regional_analysis': regional_analysis,
                'data_source_quality': data_source_quality,
                'seasonal_patterns': seasonal_patterns,
                'system_health': self._assess_system_health(),
                'insights': self._generate_system_insights()
            }

        except Exception as e:
            logger.error(f"Error generating system analytics: {e}")
            return {}

    def predict_irrigation_needs(self, field_id: int, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict irrigation needs for the next few days"""
        try:
            field = FarmField.objects.get(id=field_id)

            # Get historical data
            start_date = date.today() - timedelta(days=30)
            historical_advisories = IrrigationAdvisory.objects.filter(
                field=field,
                date__gte=start_date
            ).order_by('date')

            if not historical_advisories.exists():
                return {'prediction': 'insufficient_data', 'confidence': 0.0}

            # Calculate historical patterns
            avg_irrigation_frequency = historical_advisories.filter(
                irrigation_recommended=True).count() / historical_advisories.count()

            avg_irrigation_volume = historical_advisories.filter(
                irrigation_recommended=True).aggregate(avg=Avg('irrigation_volume'))['avg'] or 0

            # Get crop-specific patterns
            crop_info = get_crop_info(field.crop_type)
            days_since_planting = (date.today() - field.planting_date).days

            # Predict based on crop stage and historical patterns
            if days_since_planting < crop_info['duration_days'] * 0.25:
                # Initial stage - lower irrigation needs
                predicted_frequency = avg_irrigation_frequency * 0.7
            elif days_since_planting < crop_info['duration_days'] * 0.75:
                # Mid-season - peak irrigation needs
                predicted_frequency = avg_irrigation_frequency * 1.3
            else:
                # Late season - declining irrigation needs
                predicted_frequency = avg_irrigation_frequency * 0.8

            # Calculate prediction confidence
            # More data = higher confidence
            confidence = min(0.9, historical_advisories.count() / 10)

            # Generate prediction
            irrigation_probability = predicted_frequency * days_ahead
            will_need_irrigation = irrigation_probability > 0.5

            return {
                'prediction': 'irrigation_needed' if will_need_irrigation else 'no_irrigation_needed',
                'confidence': round(confidence, 2),
                'irrigation_probability': round(irrigation_probability, 2),
                'predicted_volume': round(avg_irrigation_volume, 1) if will_need_irrigation else 0,
                'days_ahead': days_ahead,
                'factors': {
                    'crop_stage': self._get_crop_stage_description(days_since_planting, crop_info),
                    'historical_frequency': round(avg_irrigation_frequency, 2),
                    'seasonal_adjustment': 'peak' if days_since_planting < crop_info['duration_days'] * 0.75 else 'declining'
                }
            }

        except Exception as e:
            logger.error(
                f"Error predicting irrigation needs for field {field_id}: {e}")
            return {'prediction': 'error', 'confidence': 0.0}

    def _analyze_trends(self, advisories) -> Dict[str, Any]:
        """Analyze trends in advisory data"""
        try:
            if not advisories.exists():
                return {}

            # Calculate weekly averages
            weekly_data = []
            for i in range(0, min(4, advisories.count())):  # Last 4 weeks
                week_advisories = advisories.order_by('-date')[i*7:(i+1)*7]
                if week_advisories.exists():
                    weekly_data.append({
                        'week': i + 1,
                        'avg_eto': week_advisories.aggregate(avg=Avg('eto'))['avg'] or 0,
                        'avg_rainfall': week_advisories.aggregate(avg=Avg('rainfall'))['avg'] or 0,
                        'irrigation_rate': week_advisories.filter(irrigation_recommended=True).count() / week_advisories.count()
                    })

            # Calculate trends
            if len(weekly_data) >= 2:
                eto_trend = 'increasing' if weekly_data[0]['avg_eto'] > weekly_data[-1]['avg_eto'] else 'decreasing'
                rainfall_trend = 'increasing' if weekly_data[0][
                    'avg_rainfall'] > weekly_data[-1]['avg_rainfall'] else 'decreasing'
                irrigation_trend = 'increasing' if weekly_data[0][
                    'irrigation_rate'] > weekly_data[-1]['irrigation_rate'] else 'decreasing'
            else:
                eto_trend = rainfall_trend = irrigation_trend = 'stable'

            return {
                'weekly_data': weekly_data,
                'eto_trend': eto_trend,
                'rainfall_trend': rainfall_trend,
                'irrigation_trend': irrigation_trend
            }

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {}

    def _assess_data_quality(self, advisories) -> Dict[str, Any]:
        """Assess the quality of advisory data"""
        try:
            if not advisories.exists():
                return {'score': 0, 'issues': ['no_data']}

            total_advisories = advisories.count()
            issues = []
            score = 100

            # Check data source quality
            gee_data = advisories.filter(data_source='GEE').count()
            simulated_data = advisories.filter(data_source='simulated').count()

            if simulated_data > gee_data:
                issues.append('high_simulation_usage')
                score -= 20

            # Check confidence scores
            low_confidence = advisories.filter(
                confidence_score__lt=0.5).count()
            if low_confidence > total_advisories * 0.3:
                issues.append('low_confidence_scores')
                score -= 15

            # Check data completeness
            incomplete_data = advisories.filter(
                Q(eto=0) | Q(rainfall=0) | Q(soil_moisture=0)
            ).count()

            if incomplete_data > total_advisories * 0.2:
                issues.append('incomplete_data')
                score -= 10

            return {
                'score': max(0, score),
                'issues': issues,
                'gee_ratio': round(gee_data / total_advisories, 2),
                'simulation_ratio': round(simulated_data / total_advisories, 2)
            }

        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return {'score': 0, 'issues': ['assessment_error']}

    def _generate_performance_recommendations(self, efficiency: float, confidence: float,
                                              irrigation_count: int, total_count: int) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        if efficiency < 0.7:
            recommendations.append(
                "Consider adjusting irrigation timing to improve water use efficiency")

        if confidence < 0.6:
            recommendations.append(
                "Data quality could be improved by ensuring consistent weather data sources")

        if irrigation_count / total_count > 0.8:
            recommendations.append(
                "High irrigation frequency detected - consider soil moisture monitoring")

        if not recommendations:
            recommendations.append(
                "Performance is optimal - continue current practices")

        return recommendations

    def _analyze_regional_patterns(self) -> Dict[str, Any]:
        """Analyze patterns by geographical regions"""
        try:
            # Group fields by latitude ranges (rough regional grouping)
            regions = {
                'tropical': {'lat_range': (-30, 30), 'fields': 0, 'avg_efficiency': 0},
                'temperate': {'lat_range': (30, 60), 'fields': 0, 'avg_efficiency': 0},
                'northern': {'lat_range': (60, 90), 'fields': 0, 'avg_efficiency': 0}
            }

            for field in FarmField.objects.all():
                for region_name, region_data in regions.items():
                    min_lat, max_lat = region_data['lat_range']
                    if min_lat <= field.latitude <= max_lat:
                        region_data['fields'] += 1
                        break

            return regions

        except Exception as e:
            logger.error(f"Error analyzing regional patterns: {e}")
            return {}

    def _analyze_data_source_quality(self) -> Dict[str, Any]:
        """Analyze quality of different data sources"""
        try:
            sources = IrrigationAdvisory.objects.values('data_source').annotate(
                count=Count('id'),
                avg_confidence=Avg('confidence_score')
            )

            return {source['data_source']: {
                'count': source['count'],
                'avg_confidence': round(source['avg_confidence'], 2)
            } for source in sources}

        except Exception as e:
            logger.error(f"Error analyzing data source quality: {e}")
            return {}

    def _analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """Analyze seasonal patterns in irrigation needs"""
        try:
            # Group advisories by month
            monthly_data = {}
            for advisory in IrrigationAdvisory.objects.all():
                month = advisory.date.month
                if month not in monthly_data:
                    monthly_data[month] = {'total': 0, 'irrigation': 0}

                monthly_data[month]['total'] += 1
                if advisory.irrigation_recommended:
                    monthly_data[month]['irrigation'] += 1

            # Calculate irrigation rates by month
            seasonal_patterns = {}
            for month, data in monthly_data.items():
                if data['total'] > 0:
                    seasonal_patterns[month] = round(
                        data['irrigation'] / data['total'], 2)

            return seasonal_patterns

        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {e}")
            return {}

    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        try:
            total_fields = FarmField.objects.count()
            total_advisories = IrrigationAdvisory.objects.count()

            # Calculate health metrics
            fields_with_advisories = FarmField.objects.filter(
                advisories__isnull=False).distinct().count()
            field_coverage = fields_with_advisories / \
                total_fields if total_fields > 0 else 0

            recent_advisories = IrrigationAdvisory.objects.filter(
                date__gte=date.today() - timedelta(days=7)
            ).count()

            avg_confidence = IrrigationAdvisory.objects.aggregate(
                avg=Avg('confidence_score'))['avg'] or 0

            return {
                'field_coverage': round(field_coverage, 2),
                'recent_activity': recent_advisories,
                'avg_confidence': round(avg_confidence, 2),
                'status': 'healthy' if field_coverage > 0.5 and avg_confidence > 0.6 else 'needs_attention'
            }

        except Exception as e:
            logger.error(f"Error assessing system health: {e}")
            return {'status': 'error'}

    def _generate_system_insights(self) -> List[str]:
        """Generate system-wide insights"""
        insights = []

        total_fields = FarmField.objects.count()
        if total_fields == 0:
            insights.append(
                "No fields registered - consider adding your first field")
            return insights

        # Crop diversity insights
        crop_count = FarmField.objects.values('crop_type').distinct().count()
        if crop_count < 3:
            insights.append(
                "Limited crop diversity - consider expanding to different crop types")

        # Data quality insights
        low_confidence_advisories = IrrigationAdvisory.objects.filter(
            confidence_score__lt=0.5).count()
        total_advisories = IrrigationAdvisory.objects.count()

        if total_advisories > 0 and low_confidence_advisories / total_advisories > 0.3:
            insights.append(
                "Many advisories have low confidence - consider improving data sources")

        # Water efficiency insights
        recent_advisories = IrrigationAdvisory.objects.filter(
            date__gte=date.today() - timedelta(days=30)
        )

        if recent_advisories.exists():
            high_irrigation_rate = recent_advisories.filter(
                irrigation_recommended=True).count() / recent_advisories.count()
            if high_irrigation_rate > 0.8:
                insights.append(
                    "High irrigation frequency detected - consider water conservation strategies")

        if not insights:
            insights.append(
                "System is performing well with good data quality and balanced irrigation patterns")

        return insights

    def _get_crop_stage_description(self, days_since_planting: int, crop_info: Dict) -> str:
        """Get human-readable crop stage description"""
        if days_since_planting < crop_info['duration_days'] * 0.25:
            return "Initial growth stage"
        elif days_since_planting < crop_info['duration_days'] * 0.75:
            return "Mid-season (peak water demand)"
        else:
            return "Late season (declining water demand)"

    def _empty_performance_summary(self) -> Dict[str, Any]:
        """Return empty performance summary"""
        return {
            'field_name': 'Unknown',
            'crop_type': 'Unknown',
            'period_days': 0,
            'total_advisories': 0,
            'irrigation_recommended_count': 0,
            'irrigation_frequency': 0,
            'total_irrigation_volume': 0,
            'avg_irrigation_volume': 0,
            'avg_confidence': 0,
            'water_use_efficiency': 0,
            'total_rainfall': 0,
            'total_water_need': 0,
            'water_saved': 0,
            'cost_savings': 0,
            'trends': {},
            'data_quality': {'score': 0, 'issues': ['no_data']},
            'recommendations': ['No data available for analysis']
        }
