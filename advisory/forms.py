from django import forms
from .models import FarmField
from datetime import date


class FieldForm(forms.ModelForm):
    class Meta:
        model = FarmField
        fields = ['name', 'latitude', 'longitude', 'soil_type', 'crop_type',
                  'planting_date', 'field_area_ha', 'elevation']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'planting_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'max': '2025-12-31'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter field name (e.g., North Field)'
            }),
            'soil_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'crop_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'field_area_ha': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Field area in hectares',
                'min': '0.1',
                'max': '1000',
                'step': '0.1'
            }),
            'elevation': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Elevation in meters (optional)',
                'min': '0',
                'max': '5000',
                'step': '1'
            }),
        }
        labels = {
            'name': 'Field Name',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'soil_type': 'Soil Type',
            'crop_type': 'Crop Type',
            'planting_date': 'Planting Date',
            'field_area_ha': 'Field Area (ha)',
            'elevation': 'Elevation (m)',
        }
        help_texts = {
            'name': 'Enter a descriptive name for your field.',
            'latitude': 'Latitude will be set automatically from map.',
            'longitude': 'Longitude will be set automatically from map.',
            'soil_type': 'Select the predominant soil type in your field.',
            'crop_type': 'Select the crop you have planted.',
            'planting_date': 'Select when you planted the crop.',
            'field_area_ha': 'Enter the area of your field in hectares (1 ha = 10,000 m²).',
            'elevation': 'Optional: Enter the elevation of your field in meters.',
        }

    def clean_planting_date(self):
        """Validate planting date is not in the future"""
        planting_date = self.cleaned_data.get('planting_date')
        if planting_date and planting_date > date.today():
            raise forms.ValidationError(
                "Planting date cannot be in the future.")
        return planting_date

    def clean_field_area_ha(self):
        """Validate field area is reasonable"""
        area = self.cleaned_data.get('field_area_ha')
        if area and (area < 0.1 or area > 1000):
            raise forms.ValidationError(
                "Field area must be between 0.1 and 1000 hectares.")
        return area

    def clean_elevation(self):
        """Validate elevation is reasonable"""
        elevation = self.cleaned_data.get('elevation')
        if elevation and (elevation < 0 or elevation > 5000):
            raise forms.ValidationError(
                "Elevation must be between 0 and 5000 meters.")
        return elevation
