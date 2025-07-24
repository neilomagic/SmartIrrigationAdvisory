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
        choices=SOIL_CHOICES, max_length=20, default="loam")
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
