from django.shortcuts import render


from django.views.generic import TemplateView, ListView


from django.shortcuts import render, redirect
from .forms import FieldForm
from django.shortcuts import render, get_object_or_404
from .models import FarmField, IrrigationAdvisory
from datetime import date
# from .utils.gee.gee_data import get_weekly_rainfall, get_daily_et0
from .utils.simulate import simulate_et0, simulate_weekly_rainfall


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
    field = get_object_or_404(FarmField, id=field_id)
    today = date.today()
    days_since_planting = (today - field.planting_date).days

    # 1. Determine crop stage and Kc
    if days_since_planting < 20:
        stage = "Initial"
        kc = 0.3
    elif days_since_planting < 60:
        stage = "Mid-Season"
        kc = 1.2
    else:
        stage = "Late Season"
        kc = 0.6

    # 2. Simulated ET₀ and Rainfall (later: fetch from GEE or API)
    # eto = 5.0  # mm/day typical value
    # rain = 15  # mm/week forecast

    # eto = get_daily_et0(field.latitude, field.longitude)
    # rain = get_weekly_rainfall(field.latitude, field.longitude)

    eto = simulate_et0(field.latitude)
    rain = simulate_weekly_rainfall(field.latitude, field.longitude)

    # fallback to GEE if simulation fails
    # try:
    #     eto = get_daily_et0(field.latitude, field.longitude)
    # except Exception as e:
    #     print("GEE ET₀ failed, simulating:", e)
    #     eto = simulate_et0(field.latitude)

    # try:
    #     rain = get_weekly_rainfall(field.latitude, field.longitude)
    # except Exception as e:
    #     print("GEE rainfall failed, simulating:", e)
    #     rain = simulate_weekly_rainfall(field.latitude, field.longitude)

    # 3. Weekly water need = ET₀ × Kc × 7 days
    weekly_need = eto * kc * 7
    deficit = max(0, weekly_need - rain)

    # 4. Message
    if deficit == 0:
        message = f"No irrigation needed. Forecast rain ({rain}mm) covers crop need."
        color = "green"
    else:
        message = f"Irrigate this week. Apply approx. {deficit:.1f}mm of water."
        color = "red"

    IrrigationAdvisory.objects.create(
        field=field,
        crop_stage=stage,
        eto=eto,
        rainfall=rain,
        kc=kc,
        water_need=weekly_need,
        water_deficit=deficit,
        recommendation=message
    )

    return render(request, 'advisory/advice.html', {
        'field': field,
        'stage': stage,
        'kc': kc,
        'eto': eto,
        'rain': rain,
        'weekly_need': weekly_need,
        'deficit': deficit,
        'message': message,
        'color': color,
    })
# List all fields


class FieldListView(ListView):
    model = FarmField
    template_name = 'advisory/field_list.html'
    context_object_name = 'fields'


# View past advisories for a field
def advisory_history_view(request, field_id):
    field = get_object_or_404(FarmField, id=field_id)
    advisories = IrrigationAdvisory.objects.filter(
        field=field).order_by('-date')
    return render(request, 'advisory/advisory_history.html', {
        'field': field,
        'advisories': advisories
    })


def field_map_view(request, field_id):
    field = get_object_or_404(FarmField, id=field_id)

    # (Optional) Calculate or retrieve latest advisory data
    context = {
        "field": field,
        "stage": "Mid",  # Example values
        "kc": 1.1,
        "eto": 4.7,
        "rain": 18.5,
        "weekly_need": 36.2,
        "deficit": 12.3,
        "message": "Apply irrigation this week.",
    }
    return render(request, "advisory/map.html", context)
