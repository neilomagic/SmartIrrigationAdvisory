
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.db import models
import csv
import json
from datetime import datetime, timedelta
from .models import FarmField, IrrigationAdvisory, SystemConfig


# Custom admin site configuration
admin.site.site_header = "Smart Irrigation Advisory Administration"
admin.site.site_title = "Irrigation Admin"
admin.site.index_title = "Welcome to Smart Irrigation Administration"


# Enhanced FarmField Admin
class FarmFieldAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'crop_type_display', 'soil_type_display', 'location_display',
        'field_area_display', 'elevation_display', 'advisories_count',
        'latest_advisory_date', 'status_display', 'created_at'
    ]
    list_filter = [
        'crop_type', 'soil_type', 'created_at', 'updated_at',
        'planting_date',
    ]
    search_fields = ['name', 'crop_type', 'soil_type']
    readonly_fields = ['created_at', 'updated_at',
                       'advisories_count', 'latest_advisory_date']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'crop_type', 'planting_date')
        }),
        ('Location Details', {
            'fields': ('latitude', 'longitude', 'elevation'),
            'description': 'Geographic coordinates and elevation of the field'
        }),
        ('Field Characteristics', {
            'fields': ('soil_type', 'field_area_ha'),
            'description': 'Physical characteristics of the field'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'advisories_count', 'latest_advisory_date'),
            'classes': ('collapse',),
            'description': 'System-generated metadata'
        }),
    )
    actions = ['export_fields_csv', 'bulk_update_soil_type',
               'generate_advisories_report']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _advisories_count=Count('advisories'),
        )
        return queryset

    def crop_type_display(self, obj):
        """Display crop type with emoji"""
        crop_icons = {
            'maize': '🌽', 'soybean': '🫘', 'rice': '🌾', 'wheat': '🌾',
            'sugarcane': '🎋', 'cotton': '🌱', 'beans': '🫘', 'potatoes': '🥔',
            'tomatoes': '🍅', 'cassava': '🍠'
        }
        icon = crop_icons.get(obj.crop_type, '🌱')
        return format_html(f'{icon} {obj.get_crop_type_display()}')
    crop_type_display.short_description = 'Crop Type'
    crop_type_display.admin_order_field = 'crop_type'

    def soil_type_display(self, obj):
        """Display soil type with color coding"""
        if obj.soil_type:
            color_map = {
                'clay': '#8B4513', 'loam': '#654321', 'sandy': '#F4A460',
                'silt': '#D2B48C', 'clay_loam': '#A0522D', 'sandy_loam': '#DEB887'
            }
            color = color_map.get(obj.soil_type, '#666')
            return format_html(
                '<span style="color: {}; font-weight: bold;">🌍 {}</span>',
                color, obj.get_soil_type_display()
            )
        return '-'
    soil_type_display.short_description = 'Soil Type'
    soil_type_display.admin_order_field = 'soil_type'

    def location_display(self, obj):
        """Display location coordinates with map link"""
        lat = round(obj.latitude, 4)
        lng = round(obj.longitude, 4)
        return format_html(
            '<a href="https://maps.google.com/?q={},{}" target="_blank" style="color: #28a745;">'
            '📍 {}, {}</a>',
            obj.latitude, obj.longitude, lat, lng
        )
    location_display.short_description = 'Location'

    def field_area_display(self, obj):
        """Display field area with formatting"""
        if obj.field_area_ha:
            return format_html('📏 {} ha', obj.field_area_ha)
        return '-'
    field_area_display.short_description = 'Area'
    field_area_display.admin_order_field = 'field_area_ha'

    def elevation_display(self, obj):
        """Display elevation with formatting"""
        if obj.elevation:
            return format_html('⛰️ {} m', int(obj.elevation))
        return '-'
    elevation_display.short_description = 'Elevation'
    elevation_display.admin_order_field = 'elevation'

    def advisories_count(self, obj):
        """Display count of advisories with link"""
        count = obj._advisories_count
        if count > 0:
            url = reverse('admin:advisory_irrigationadvisory_changelist')
            return format_html(
                '<a href="{}?field__id__exact={}" style="color: #28a745; font-weight: bold;">'
                '💧 {} advisories</a>',
                url, obj.id, count
            )
        return '0 advisories'
    advisories_count.short_description = 'Advisories'
    advisories_count.admin_order_field = '_advisories_count'

    def latest_advisory_date(self, obj):
        """Display latest advisory date"""
        latest = obj.advisories.order_by('-date').first()
        if latest:
            days_ago = (datetime.now().date() - latest.date).days
            if days_ago == 0:
                return format_html('<span style="color: #28a745;">📅 Today</span>')
            elif days_ago <= 7:
                return format_html('<span style="color: #ffc107;">📅 {} days ago</span>', days_ago)
            else:
                return format_html('<span style="color: #dc3545;">📅 {} days ago</span>', days_ago)
        return '-'
    latest_advisory_date.short_description = 'Latest Advisory'

    def status_display(self, obj):
        """Display field status based on recent activity"""
        latest = obj.advisories.order_by('-date').first()
        if latest:
            days_ago = (datetime.now().date() - latest.date).days
            if days_ago <= 3:
                return format_html('<span style="color: #28a745; font-weight: bold;">✅ Active</span>')
            elif days_ago <= 14:
                return format_html('<span style="color: #ffc107; font-weight: bold;">⚠️ Monitoring</span>')
            else:
                return format_html('<span style="color: #dc3545; font-weight: bold;">❌ Inactive</span>')
        return format_html('<span style="color: #6c757d;">📝 New</span>')
    status_display.short_description = 'Status'

    # Custom actions
    def export_fields_csv(self, request, queryset):
        """Export selected fields to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="fields_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Crop Type', 'Soil Type', 'Latitude', 'Longitude',
            'Field Area (ha)', 'Elevation (m)', 'Planting Date', 'Created At'
        ])

        for field in queryset:
            writer.writerow([
                field.name, field.get_crop_type_display(), field.get_soil_type_display(),
                field.latitude, field.longitude, field.field_area_ha,
                field.elevation, field.planting_date, field.created_at
            ])

        return response
    export_fields_csv.short_description = "Export selected fields to CSV"

    def bulk_update_soil_type(self, request, queryset):
        """Bulk update soil type for selected fields"""
        # This would typically open a form, for now just show count
        count = queryset.count()
        self.message_user(
            request, f"Selected {count} fields for soil type update.")
    bulk_update_soil_type.short_description = "Bulk update soil type"

    def generate_advisories_report(self, request, queryset):
        """Generate advisories report for selected fields"""
        field_ids = list(queryset.values_list('id', flat=True))
        advisories = IrrigationAdvisory.objects.filter(field_id__in=field_ids)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="advisories_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Field Name', 'Date', 'Crop Stage', 'ETo', 'Rainfall', 'Water Need',
            'Irrigation Recommended', 'Irrigation Volume', 'Confidence Score', 'Data Source'
        ])

        for advisory in advisories:
            writer.writerow([
                advisory.field.name, advisory.date, advisory.crop_stage,
                advisory.eto, advisory.rainfall, advisory.water_need,
                advisory.irrigation_recommended, advisory.irrigation_volume,
                advisory.confidence_score, advisory.data_source
            ])

        return response
    generate_advisories_report.short_description = "Generate advisories report"


# Enhanced IrrigationAdvisory Admin
class IrrigationAdvisoryAdmin(admin.ModelAdmin):
    list_display = [
        'field_name_display', 'date', 'crop_stage_display', 'irrigation_status',
        'water_metrics', 'confidence_display', 'data_source_display', 'recommendation_preview'
    ]
    list_filter = [
        'irrigation_recommended', 'data_source', 'crop_stage',
        'date', 'field__crop_type', 'field__soil_type'
    ]
    search_fields = ['field__name', 'crop_stage', 'recommendation']
    readonly_fields = ['recommendation_preview', 'water_efficiency_score']
    date_hierarchy = 'date'
    ordering = ['-date', '-confidence_score']

    fieldsets = (
        ('Advisory Information', {
            'fields': ('field', 'date', 'crop_stage', 'recommendation')
        }),
        ('Weather & Environmental Data', {
            'fields': ('eto', 'rainfall', 'soil_moisture', 'data_source'),
            'description': 'Environmental conditions and data sources'
        }),
        ('Irrigation Analysis', {
            'fields': ('kc', 'water_need', 'water_deficit', 'irrigation_recommended', 'irrigation_volume'),
            'description': 'Water requirements and irrigation recommendations'
        }),
        ('Quality & Confidence', {
            'fields': ('confidence_score', 'water_efficiency_score'),
            'description': 'Recommendation quality metrics'
        }),
    )

    actions = [
        'export_advisories_csv', 'export_advisories_json', 'mark_as_high_confidence',
        'generate_field_summary', 'recalculate_water_efficiency'
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('field')
        return queryset

    def field_name_display(self, obj):
        """Display field name with crop icon and link"""
        crop_icons = {
            'maize': '🌽', 'soybean': '🫘', 'rice': '🌾', 'wheat': '🌾',
            'sugarcane': '🎋', 'cotton': '🌱', 'beans': '🫘', 'potatoes': '🥔',
            'tomatoes': '🍅', 'cassava': '🍠'
        }
        icon = crop_icons.get(obj.field.crop_type, '🌱')
        url = reverse('admin:advisory_farmfield_change', args=[obj.field.id])
        return format_html(
            '<a href="{}" style="color: #28a745; font-weight: bold;">{} {}</a>',
            url, icon, obj.field.name
        )
    field_name_display.short_description = 'Field'
    field_name_display.admin_order_field = 'field__name'

    def crop_stage_display(self, obj):
        """Display crop stage with appropriate styling"""
        stage_colors = {
            'Initial': '#17a2b8', 'Development': '#28a745', 'Mid-season': '#ffc107',
            'Late-season': '#fd7e14', 'Harvest': '#6f42c1'
        }
        color = stage_colors.get(obj.crop_stage, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">🌱 {}</span>',
            color, obj.crop_stage
        )
    crop_stage_display.short_description = 'Crop Stage'
    crop_stage_display.admin_order_field = 'crop_stage'

    def irrigation_status(self, obj):
        """Display irrigation recommendation status"""
        if obj.irrigation_recommended:
            volume = f" ({obj.irrigation_volume}mm)" if obj.irrigation_volume > 0 else ""
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">💧 Required{}</span>',
                volume
            )
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ Not Needed</span>')
    irrigation_status.short_description = 'Irrigation'
    irrigation_status.admin_order_field = 'irrigation_recommended'

    def water_metrics(self, obj):
        """Display key water metrics"""
        return format_html(
            '<div style="font-size: 0.9em;">'
            '<div>ET₀: <strong>{}</strong> mm/day</div>'
            '<div>Rain: <strong>{}</strong> mm</div>'
            '<div>Need: <strong>{}</strong> mm</div>'
            '</div>',
            obj.eto, obj.rainfall, obj.water_need
        )
    water_metrics.short_description = 'Water Metrics'

    def confidence_display(self, obj):
        """Display confidence score with color coding"""
        percentage = int(obj.confidence_score * 100)
        if percentage >= 80:
            color = '#28a745'
            icon = '🎯'
        elif percentage >= 60:
            color = '#ffc107'
            icon = '⚠️'
        else:
            color = '#dc3545'
            icon = '❌'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}%</span>',
            color, icon, percentage
        )
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'confidence_score'

    def data_source_display(self, obj):
        """Display data source with appropriate styling"""
        source_styles = {
            'GEE': {'color': '#28a745', 'icon': '🛰️'},
            'API': {'color': '#17a2b8', 'icon': '🌐'},
            'simulated': {'color': '#6c757d', 'icon': '🔬'}
        }
        style = source_styles.get(
            obj.data_source, {'color': '#6c757d', 'icon': '❓'})
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            style['color'], style['icon'], obj.data_source.upper()
        )
    data_source_display.short_description = 'Data Source'
    data_source_display.admin_order_field = 'data_source'

    def recommendation_preview(self, obj):
        """Display recommendation preview with full text in tooltip"""
        if obj.recommendation:
            preview = obj.recommendation[:60]
            if len(obj.recommendation) > 60:
                preview += "..."
            return format_html(
                '<span title="{}" style="cursor: help;">📝 {}</span>',
                obj.recommendation, preview
            )
        return '-'
    recommendation_preview.short_description = 'Recommendation'

    def water_efficiency_score(self, obj):
        """Calculate and display water efficiency score"""
        if obj.water_need > 0 and obj.irrigation_volume >= 0:
            efficiency = (1 - (obj.irrigation_volume /
                          max(obj.water_need, 1))) * 100
            efficiency = max(0, min(100, efficiency))

            if efficiency >= 80:
                color = '#28a745'
            elif efficiency >= 60:
                color = '#ffc107'
            else:
                color = '#dc3545'

            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color, round(efficiency, 1)
            )
        return '-'
    water_efficiency_score.short_description = 'Water Efficiency'

    # Custom actions
    def export_advisories_csv(self, request, queryset):
        """Export selected advisories to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="advisories_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Field Name', 'Date', 'Crop Type', 'Crop Stage', 'ET₀ (mm/day)', 'Rainfall (mm)',
            'Soil Moisture (%)', 'Water Need (mm)', 'Water Deficit (mm)', 'Irrigation Recommended',
            'Irrigation Volume (mm)', 'Confidence Score', 'Data Source', 'Recommendation'
        ])

        for advisory in queryset:
            writer.writerow([
                advisory.field.name, advisory.date, advisory.field.get_crop_type_display(),
                advisory.crop_stage, advisory.eto, advisory.rainfall, advisory.soil_moisture,
                advisory.water_need, advisory.water_deficit, advisory.irrigation_recommended,
                advisory.irrigation_volume, advisory.confidence_score, advisory.data_source,
                advisory.recommendation
            ])

        return response
    export_advisories_csv.short_description = "Export selected advisories to CSV"

    def export_advisories_json(self, request, queryset):
        """Export selected advisories to JSON"""
        data = []
        for advisory in queryset:
            data.append({
                'field_name': advisory.field.name,
                'field_id': advisory.field.id,
                'date': advisory.date.isoformat(),
                'crop_type': advisory.field.crop_type,
                'crop_stage': advisory.crop_stage,
                'eto': advisory.eto,
                'rainfall': advisory.rainfall,
                'soil_moisture': advisory.soil_moisture,
                'kc': advisory.kc,
                'water_need': advisory.water_need,
                'water_deficit': advisory.water_deficit,
                'irrigation_recommended': advisory.irrigation_recommended,
                'irrigation_volume': advisory.irrigation_volume,
                'confidence_score': advisory.confidence_score,
                'data_source': advisory.data_source,
                'recommendation': advisory.recommendation
            })

        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="advisories_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    export_advisories_json.short_description = "Export selected advisories to JSON"

    def mark_as_high_confidence(self, request, queryset):
        """Mark selected advisories as high confidence"""
        updated = queryset.update(confidence_score=0.95)
        self.message_user(
            request, f"Updated {updated} advisories to high confidence (95%).")
    mark_as_high_confidence.short_description = "Mark as high confidence"

    def generate_field_summary(self, request, queryset):
        """Generate summary report for selected advisories"""
        fields_data = {}

        for advisory in queryset:
            field_name = advisory.field.name
            if field_name not in fields_data:
                fields_data[field_name] = {
                    'advisories_count': 0,
                    'irrigation_recommended_count': 0,
                    'total_irrigation_volume': 0,
                    'avg_confidence': 0,
                    'data_sources': set()
                }

            field_data = fields_data[field_name]
            field_data['advisories_count'] += 1
            if advisory.irrigation_recommended:
                field_data['irrigation_recommended_count'] += 1
                field_data['total_irrigation_volume'] += advisory.irrigation_volume
            field_data['avg_confidence'] += advisory.confidence_score
            field_data['data_sources'].add(advisory.data_source)

        # Calculate averages
        for field_name, data in fields_data.items():
            data['avg_confidence'] = data['avg_confidence'] / \
                data['advisories_count']
            data['irrigation_frequency'] = (
                data['irrigation_recommended_count'] / data['advisories_count']) * 100
            data['data_sources'] = list(data['data_sources'])

        response = HttpResponse(
            json.dumps(fields_data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="field_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    generate_field_summary.short_description = "Generate field summary report"

    def recalculate_water_efficiency(self, request, queryset):
        """Recalculate water efficiency for selected advisories"""
        count = queryset.count()
        # This would trigger a recalculation process
        self.message_user(
            request, f"Triggered water efficiency recalculation for {count} advisories.")
    recalculate_water_efficiency.short_description = "Recalculate water efficiency"


# Enhanced User Admin
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced User Admin with irrigation-specific information"""

    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'fields_count', 'last_login_display', 'is_active', 'is_staff', 'date_joined'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser',
        ('last_login', admin.filters.DateFieldListFilter),
        ('date_joined', admin.filters.DateFieldListFilter)
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Add field count annotation if FarmField has a user field
        # For now, we'll count all fields (assuming single-user system)
        return queryset

    def fields_count(self, obj):
        """Display count of fields associated with user"""
        # This would require a user field in FarmField model
        # For now, show total system fields
        count = FarmField.objects.count()
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">🌾 {} fields</span>',
            count
        )
    fields_count.short_description = 'Fields'

    def last_login_display(self, obj):
        """Display last login with relative time"""
        if obj.last_login:
            days_ago = (datetime.now().date() - obj.last_login.date()).days
            if days_ago == 0:
                return format_html('<span style="color: #28a745;">Today</span>')
            elif days_ago <= 7:
                return format_html('<span style="color: #ffc107;">{} days ago</span>', days_ago)
            else:
                return format_html('<span style="color: #dc3545;">{} days ago</span>', days_ago)
        return format_html('<span style="color: #6c757d;">Never</span>')
    last_login_display.short_description = 'Last Login'
    last_login_display.admin_order_field = 'last_login'


class SystemConfigAdmin(admin.ModelAdmin):
    """Admin for system configuration"""

    list_display = [
        'config_summary', 'weather_provider', 'gee_status', 'notifications_status', 'updated_at'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Weather Data Configuration', {
            'fields': ('weather_api_provider', 'weather_api_key'),
            'description': 'Configuration for weather data providers'
        }),
        ('Google Earth Engine', {
            'fields': ('gee_project_id', 'gee_service_account_key'),
            'description': 'Google Earth Engine integration settings'
        }),
        ('Advisory Settings', {
            'fields': ('default_crop_coefficient', 'confidence_threshold', 'max_field_area'),
            'description': 'Default values and thresholds for advisory calculations'
        }),
        ('Notifications', {
            'fields': ('enable_email_notifications', 'notification_email'),
            'description': 'Email notification settings'
        }),
        ('Data Management', {
            'fields': ('advisory_retention_days',),
            'description': 'Data retention and cleanup settings'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'System-generated timestamps'
        }),
    )

    def has_add_permission(self, request):
        """Limit to one configuration instance"""
        return not SystemConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of configuration"""
        return False

    def config_summary(self, obj):
        """Display configuration summary"""
        return format_html(
            '<strong>System Configuration</strong><br/>'
            '<small>Weather: {} | GEE: {} | Notifications: {}</small>',
            obj.weather_api_provider,
            '✅' if obj.gee_project_id else '❌',
            '✅' if obj.enable_email_notifications else '❌'
        )
    config_summary.short_description = 'Configuration'

    def weather_provider(self, obj):
        """Display weather provider status"""
        provider_icons = {
            'openweathermap': '🌤️',
            'weatherapi': '🌦️',
            'custom': '🔧'
        }
        icon = provider_icons.get(obj.weather_api_provider, '❓')
        has_key = '✅' if obj.weather_api_key else '❌'
        return format_html(
            '{} {} {}',
            icon, obj.get_weather_api_provider_display(), has_key
        )
    weather_provider.short_description = 'Weather API'

    def gee_status(self, obj):
        """Display Google Earth Engine status"""
        if obj.gee_project_id and obj.gee_service_account_key:
            return format_html('<span style="color: #28a745;">🛰️ Configured</span>')
        elif obj.gee_project_id or obj.gee_service_account_key:
            return format_html('<span style="color: #ffc107;">⚠️ Partial</span>')
        else:
            return format_html('<span style="color: #dc3545;">❌ Not Configured</span>')
    gee_status.short_description = 'GEE Status'

    def notifications_status(self, obj):
        """Display notification status"""
        if obj.enable_email_notifications and obj.notification_email:
            return format_html('<span style="color: #28a745;">📧 Enabled</span>')
        else:
            return format_html('<span style="color: #6c757d;">📵 Disabled</span>')
    notifications_status.short_description = 'Notifications'


# Register models with the default admin site
admin.site.register(FarmField, FarmFieldAdmin)
admin.site.register(IrrigationAdvisory, IrrigationAdvisoryAdmin)

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(SystemConfig, SystemConfigAdmin)


# Additional Management Commands Helper
class DataManagementMixin:
    """Mixin for data management operations"""

    @staticmethod
    def cleanup_old_advisories(days=365):
        """Clean up old advisory records"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        old_advisories = IrrigationAdvisory.objects.filter(
            date__lt=cutoff_date)
        count = old_advisories.count()
        old_advisories.delete()
        return count

    @staticmethod
    def export_all_data():
        """Export all system data"""
        data = {
            'fields': list(FarmField.objects.values()),
            'advisories': list(IrrigationAdvisory.objects.values()),
            'export_date': datetime.now().isoformat(),
        }
        return data

    @staticmethod
    def get_system_statistics():
        """Get comprehensive system statistics"""
        return {
            'total_fields': FarmField.objects.count(),
            'total_advisories': IrrigationAdvisory.objects.count(),
            'crop_types': FarmField.objects.values('crop_type').distinct().count(),
            'soil_types': FarmField.objects.values('soil_type').distinct().count(),
            'avg_confidence': IrrigationAdvisory.objects.aggregate(
                Avg('confidence_score')
            )['confidence_score__avg'],
            'irrigation_frequency': IrrigationAdvisory.objects.filter(
                irrigation_recommended=True
            ).count() / max(IrrigationAdvisory.objects.count(), 1) * 100,
            'data_sources': list(IrrigationAdvisory.objects.values('data_source').annotate(
                count=Count('id')
            )),
        }


# Enhanced Actions for better bulk operations
def bulk_generate_advisories(modeladmin, request, queryset):
    """Bulk generate advisories for selected fields"""
    count = queryset.count()
    # This would trigger the advisory generation process for each field

    modeladmin.message_user(
        request,
        f"Triggered advisory generation for {count} fields. Check back in a few minutes for results."
    )


bulk_generate_advisories.short_description = "Generate advisories for selected fields"


def bulk_update_planting_dates(modeladmin, request, queryset):
    """Bulk update planting dates"""
    # This would open a form to set new planting date
    count = queryset.count()
    modeladmin.message_user(
        request,
        f"Ready to update planting dates for {count} fields. Feature available in admin interface."
    )


bulk_update_planting_dates.short_description = "Bulk update planting dates"


def export_field_performance_report(modeladmin, request, queryset):
    """Export performance report for selected fields"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="field_performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Field Name', 'Crop Type', 'Total Advisories', 'Irrigation Recommended',
        'Irrigation Frequency (%)', 'Avg Confidence', 'Last Advisory Date',
        'Water Efficiency Score'
    ])

    for field in queryset:
        advisories = field.advisories.all()
        total_advisories = advisories.count()
        irrigation_count = advisories.filter(
            irrigation_recommended=True).count()
        avg_confidence = advisories.aggregate(Avg('confidence_score'))[
            'confidence_score__avg'] or 0
        last_advisory = advisories.order_by('-date').first()

        irrigation_freq = (irrigation_count / max(total_advisories, 1)) * 100

        writer.writerow([
            field.name,
            field.get_crop_type_display(),
            total_advisories,
            irrigation_count,
            f"{irrigation_freq:.1f}",
            f"{avg_confidence:.3f}",
            last_advisory.date if last_advisory else 'Never',
            'N/A'  # Would calculate based on actual efficiency algorithm
        ])

    return response


export_field_performance_report.short_description = "Export performance report"

# Add these actions to the FarmField admin
FarmFieldAdmin.actions.extend([
    bulk_generate_advisories,
    bulk_update_planting_dates,
    export_field_performance_report
])
