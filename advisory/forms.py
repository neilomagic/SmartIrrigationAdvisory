from django import forms
from .models import FarmField


class FieldForm(forms.ModelForm):
    class Meta:
        model = FarmField
        fields = ['name', 'latitude', 'longitude',
                  'soil_type', 'crop_type', 'planting_date']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'planting_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'name': 'Field Name',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'soil_type': 'Soil Type',
            'crop_type': 'Crop Type',
            'planting_date': 'Planting Date',
        }
        help_texts = {
            'name': 'Enter a name for the field.',
            'latitude': 'Enter the latitude of the field.',
            'longitude': 'Enter the longitude of the field.',
            'soil_type': 'Select the soil type of the field.',
            'crop_type': 'Select the crop type planted in the field.',
            'planting_date': 'Select the planting date of the crop.',
        }
