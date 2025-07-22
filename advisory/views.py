from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.shortcuts import render, redirect
from .forms import FieldForm
from django.shortcuts import render, get_object_or_404
from django.db import models
from django.http import JsonResponse
from .models import FarmField, IrrigationAdvisory
from datetime import date
import logging

# Import enhanced utilities
from .utils.crop_coefficients import get_kc, get_crop_info
from .utils.recommendation_engine import IrrigationRecommendationEngine
from .utils.gee.gee_data import get_comprehensive_weather_data
from .utils.simulate import simulate_et0, simulate_weekly_rainfall
from .utils.analytics import IrrigationAnalytics

logger = logging.getLogger(__name__)


def create_field_view(request):
    if request.method == 'POST':
        form = FieldForm(request.POST)
        if form.is_valid():
            field = form.save()
            return redirect('advisory:get_advice', field_id=field.id)
    else:
        form = FieldForm()
    return render(request, 'advisory/create_field_point.html', {'form': form})


def get_irrigation_advice(request, field_id):
    """Enhanced irrigation advice using comprehensive data and recommendation engine"""
    field = get_object_or_404(FarmField, id=field_id)

    try:
        # Initialize recommendation engine
        engine = IrrigationRecommendationEngine()

        # Get comprehensive weather data (try GEE first, fallback to simulation)
        try:
            weather_data = get_comprehensive_weather_data(
                field.latitude, field.longitude)
            logger.info(f"Using GEE data for field {field.id}")
        except Exception as e:
            logger.warning(
                f"GEE data failed for field {field.id}, using simulation: {e}")
            # Fallback to simulation
            weather_data = {
                'weekly_rainfall': simulate_weekly_rainfall(field.latitude, field.longitude),
                'daily_eto': simulate_et0(field.latitude),
                'soil_moisture_ndmi': 0.0,  # Default value
                'forecast': {'temperature': 25.0, 'precipitation': 0.0, 'days': 5},
                'confidence_score': 0.3,
                'data_source': 'simulated',
                'timestamp': date.today().isoformat()
            }

        # Prepare field data for recommendation engine
        field_data = {
            'crop_type': field.crop_type,
            'planting_date': field.planting_date,
            'soil_type': field.soil_type,
            'field_area_ha': field.field_area_ha or 1.0,
            'elevation': field.elevation or 0.0
        }

        # Generate comprehensive recommendation
        recommendation = engine.generate_recommendation(
            field_data, weather_data)

        # Get crop stage information
        kc, stage = get_kc(field.crop_type, field.planting_date)
        crop_info = get_crop_info(field.crop_type)

        # Create advisory record
        advisory = IrrigationAdvisory.objects.create(
            field=field,
            crop_stage=stage,
            eto=weather_data['daily_eto'],
            rainfall=weather_data['weekly_rainfall'],
            kc=kc,
            water_need=recommendation['weather_summary'].get('weekly_need', 0),
            water_deficit=recommendation['irrigation_volume'],
            recommendation=recommendation['recommendation_message'],
            soil_moisture=weather_data.get('soil_moisture_ndmi', 0),
            irrigation_recommended=recommendation['irrigation_needed'],
            irrigation_volume=recommendation['irrigation_volume'],
            confidence_score=recommendation['confidence_score'],
            data_source=weather_data['data_source']
        )

        # Prepare context for template
        context = {
            'field': field,
            'advisory': advisory,
            'recommendation': recommendation,
            'weather_data': weather_data,
            'crop_info': crop_info,
            'stage': stage,
            'kc': kc,
            'eto': weather_data['daily_eto'],
            'rain': weather_data['weekly_rainfall'],
            'soil_moisture': weather_data.get('soil_moisture_ndmi', 0),
            'confidence': recommendation['confidence_score'],
            'data_source': weather_data['data_source'],
            'priority': recommendation['priority'],
            'timing': recommendation['timing'],
            'method': recommendation['method']
        }

        return render(request, 'advisory/advice.html', context)

    except Exception as e:
        logger.error(
            f"Error generating irrigation advice for field {field_id}: {e}")
        # Fallback to basic advice
        return render(request, 'advisory/advice.html', {
            'field': field,
            'error': 'Unable to generate irrigation advice. Please try again later.',
            'fallback': True
        })


class FieldListView(ListView):
    model = FarmField
    template_name = 'advisory/field_list.html'
    context_object_name = 'fields'

    def get_queryset(self):
        """Get fields with latest advisory information"""
        return FarmField.objects.prefetch_related('advisories').all()


def advisory_history_view(request, field_id):
    """Enhanced advisory history with detailed information"""
    field = get_object_or_404(FarmField, id=field_id)
    advisories = IrrigationAdvisory.objects.filter(
        field=field).order_by('-date')

    # Calculate summary statistics
    total_advisories = advisories.count()
    irrigation_recommended_count = advisories.filter(
        irrigation_recommended=True).count()
    avg_confidence = advisories.aggregate(
        avg_confidence=models.Avg('confidence_score'))['avg_confidence'] or 0

    context = {
        'field': field,
        'advisories': advisories,
        'summary': {
            'total_advisories': total_advisories,
            'irrigation_recommended_count': irrigation_recommended_count,
            'irrigation_percentage': (irrigation_recommended_count / total_advisories * 100) if total_advisories > 0 else 0,
            'avg_confidence': round(avg_confidence, 2)
        }
    }
    return render(request, 'advisory/advisory_history.html', context)


def field_map_view(request, field_id):
    """Enhanced field map with comprehensive data"""
    field = get_object_or_404(FarmField, id=field_id)

    # Get latest advisory if available
    latest_advisory = IrrigationAdvisory.objects.filter(
        field=field).order_by('-date').first()

    # Get weather data for map display
    try:
        weather_data = get_comprehensive_weather_data(
            field.latitude, field.longitude)
    except Exception as e:
        logger.warning(f"Could not get weather data for map: {e}")
        weather_data = {
            'weekly_rainfall': 0.0,
            'daily_eto': 0.0,
            'soil_moisture_ndmi': 0.0,
            'forecast': {'temperature': 25.0, 'precipitation': 0.0, 'days': 5},
            'data_source': 'simulated'
        }

    context = {
        "field": field,
        "latest_advisory": latest_advisory,
        "weather_data": weather_data,
        "crop_info": get_crop_info(field.crop_type) if field.crop_type else None
    }
    return render(request, "advisory/map.html", context)


def dashboard_view(request):
    """New dashboard view for overview of all fields"""
    fields = FarmField.objects.all()

    # Get summary statistics
    total_fields = fields.count()
    total_advisories = IrrigationAdvisory.objects.count()

    # Get fields by crop type
    crop_summary = {}
    for field in fields:
        crop = field.crop_type
        if crop not in crop_summary:
            crop_summary[crop] = 0
        crop_summary[crop] += 1

    # Get recent advisories
    recent_advisories = IrrigationAdvisory.objects.select_related(
        'field').order_by('-date')[:5]

    context = {
        'total_fields': total_fields,
        'total_advisories': total_advisories,
        'crop_summary': crop_summary,
        'recent_advisories': recent_advisories,
        'fields': fields
    }

    return render(request, 'advisory/dashboard.html', context)


# New Analytics Views
def field_analytics_view(request, field_id):
    """Detailed analytics view for a specific field"""
    field = get_object_or_404(FarmField, id=field_id)
    analytics = IrrigationAnalytics()

    # Get period from request
    period = request.GET.get('period', '30')
    try:
        period_days = int(period)
    except ValueError:
        period_days = 30

    # Get performance summary
    performance = analytics.get_field_performance_summary(
        field_id, period_days)

    # Get prediction
    prediction = analytics.predict_irrigation_needs(field_id, days_ahead=7)

    context = {
        'field': field,
        'performance': performance,
        'prediction': prediction,
        'period_days': period_days,
        'period_options': [7, 30, 90, 365]
    }

    return render(request, 'advisory/field_analytics.html', context)


def system_analytics_view(request):
    """System-wide analytics dashboard"""
    analytics = IrrigationAnalytics()
    system_data = analytics.get_system_analytics()

    context = {
        'system_data': system_data,
        'total_fields': FarmField.objects.count(),
        'total_advisories': IrrigationAdvisory.objects.count()
    }

    return render(request, 'advisory/system_analytics.html', context)


def analytics_api_view(request, field_id):
    """API endpoint for analytics data (for AJAX requests)"""
    try:
        analytics = IrrigationAnalytics()

        # Get performance data
        performance = analytics.get_field_performance_summary(field_id)

        # Get prediction
        prediction = analytics.predict_irrigation_needs(field_id)

        return JsonResponse({
            'success': True,
            'performance': performance,
            'prediction': prediction
        })

    except Exception as e:
        logger.error(f"Error in analytics API for field {field_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def performance_comparison_view(request):
    """Compare performance across multiple fields"""
    fields = FarmField.objects.all()
    analytics = IrrigationAnalytics()

    field_performances = []
    for field in fields:
        performance = analytics.get_field_performance_summary(field.id, 30)
        field_performances.append({
            'field': field,
            'performance': performance
        })

    # Sort by water use efficiency
    field_performances.sort(
        key=lambda x: x['performance']['water_use_efficiency'], reverse=True)

    context = {
        'field_performances': field_performances,
        'total_fields': len(field_performances)
    }

    return render(request, 'advisory/performance_comparison.html', context)
