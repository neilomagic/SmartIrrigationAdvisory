from datetime import date
from django.db import models


from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class FarmField(models.Model):
    # Crop type choices expanded to 10 crops
    CROP_CHOICES = [
        ("maize", "Maize"),
        ("soybean", "Soybean"),
        ("rice", "Rice"),
        ("wheat", "Wheat"),
        ("sugarcane", "Sugarcane"),
        ("cotton", "Cotton"),
        ("beans", "Beans"),
        ("potatoes", "Potatoes"),
        ("tomatoes", "Tomatoes"),
        ("cassava", "Cassava"),
    ]

    # Soil type choices expanded
    SOIL_CHOICES = [
        ("clay", "Clay"),
        ("loam", "Loam"),
        ("sandy", "Sandy"),
        ("silt", "Silt"),
        ("clay_loam", "Clay Loam"),
        ("sandy_loam", "Sandy Loam"),
    ]

    name = models.CharField(max_length=100)
    latitude = models.FloatField(_('Latitude'), validators=[
        MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitude = models.FloatField(_('Longitude'), validators=[
        MinValueValidator(-180.0), MaxValueValidator(180.0)])
    soil_type = models.CharField(
        choices=SOIL_CHOICES, max_length=20, default="loam", null=True, blank=True)
    crop_type = models.CharField(
        choices=CROP_CHOICES, max_length=20, default="maize")
    planting_date = models.DateField(_('Planting Date'), default=date.today)

    # New fields for enhanced tracking
    field_area_ha = models.FloatField(
        _('Field Area (ha)'),
        validators=[MinValueValidator(0.1), MaxValueValidator(1000.0)],
        null=True, blank=True,
        help_text="Field area in hectares"
    )
    elevation = models.FloatField(
        _('Elevation (m)'),
        null=True, blank=True,
        help_text="Field elevation in meters"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Farm Field'
        verbose_name_plural = 'Farm Fields'

    def __str__(self):
        return f"{self.name} - {str(self.crop_type).capitalize()}"


class IrrigationAdvisory(models.Model):
    field = models.ForeignKey(
        FarmField, on_delete=models.CASCADE, related_name='advisories')
    date = models.DateField(default=date.today)
    crop_stage = models.CharField(max_length=50, default="Initial")
    eto = models.FloatField(default=0.0)  # mm/day
    rainfall = models.FloatField(default=0.0)  # mm/week
    kc = models.FloatField(default=0.0)  # Crop Coefficient
    water_need = models.FloatField(default=0.0)  # mm/week
    water_deficit = models.FloatField(default=0.0)
    recommendation = models.TextField(blank=True)

    # New fields for enhanced advisory
    soil_moisture = models.FloatField(
        default=0.0,
        help_text="Soil moisture percentage"
    )
    irrigation_recommended = models.BooleanField(default=False)
    irrigation_volume = models.FloatField(
        default=0.0,
        help_text="Recommended irrigation volume in mm"
    )
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence in recommendation (0-1)"
    )
    data_source = models.CharField(
        max_length=50,
        default="simulated",
        help_text="Source of weather data (GEE, API, simulated)"
    )

    class Meta:
        ordering = ['-date']
        verbose_name = 'Irrigation Advisory'
        verbose_name_plural = 'Irrigation Advisories'
        get_latest_by = 'date'

    def __str__(self):
        recommendation_text = str(self.recommendation)[
            :25] if self.recommendation else 'No recommendation'
        return f"{self.field.name} - {self.date} - {recommendation_text}"


class SystemConfig(models.Model):
    """System configuration for irrigation advisory"""

    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configuration'

    # Weather API Configuration
    weather_api_key = models.CharField(
        max_length=200, blank=True,
        help_text="API key for weather data service"
    )
    weather_api_provider = models.CharField(
        max_length=50, default='openweathermap',
        choices=[
            ('openweathermap', 'OpenWeatherMap'),
            ('weatherapi', 'WeatherAPI'),
            ('custom', 'Custom API')
        ]
    )

    # Google Earth Engine Configuration
    gee_service_account_key = models.TextField(
        blank=True,
        help_text="JSON service account key for Google Earth Engine"
    )
    gee_project_id = models.CharField(
        max_length=100, blank=True,
        help_text="Google Cloud Project ID for Earth Engine"
    )

    # System Settings
    default_crop_coefficient = models.FloatField(
        default=1.0,
        help_text="Default crop coefficient when specific data unavailable"
    )
    confidence_threshold = models.FloatField(
        default=0.7,
        help_text="Minimum confidence score for high-quality recommendations"
    )
    max_field_area = models.FloatField(
        default=1000.0,
        help_text="Maximum allowed field area in hectares"
    )

    # Email Notifications
    enable_email_notifications = models.BooleanField(
        default=False,
        help_text="Enable email notifications for irrigation alerts"
    )
    notification_email = models.EmailField(
        blank=True,
        help_text="Email address for system notifications"
    )

    # Data Retention
    advisory_retention_days = models.IntegerField(
        default=365,
        help_text="Number of days to retain advisory records"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.updated_at:
            return f"System Configuration (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
        return "System Configuration"
