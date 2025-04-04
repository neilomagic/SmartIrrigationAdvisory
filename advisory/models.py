from datetime import date
from django.db import models


from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class FarmField(models.Model):

    name = models.CharField(max_length=100)
    latitude = models.FloatField(_('Latitude'), validators=[
        MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitude = models.FloatField(_('Longitude'), validators=[
        MinValueValidator(-180.0), MaxValueValidator(180.0)])
    soil_type = models.CharField(
        choices=[("clay", "Clay"), ("loam", "Loam")], max_length=20, default="loam")
    crop_type = models.CharField(
        choices=[("maize", "Maize"), ("soybean", "Soybean")], max_length=20, default="maize")
    planting_date = models.DateField(_('Planting Date'), default=date.today)


class IrrigationAdvisory(models.Model):
    field = models.ForeignKey(FarmField, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    crop_stage = models.CharField(max_length=50, default="Initial")
    eto = models.FloatField(default=0.0)  # mm/day
    rainfall = models.FloatField(default=0.0)  # mm/week
    kc = models.FloatField(default=0.0)  # Crop Coefficient
    water_need = models.FloatField(default=0.0)  # mm/week
    water_deficit = models.FloatField(default=0.0)
    recommendation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.field.name} - {self.date} - {self.recommendation[:25]}"
