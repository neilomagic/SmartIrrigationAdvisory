import math
import random


def simulate_et0(latitude: float) -> float:
    # Equatorial zones: higher evapotranspiration
    base_eto = 4.0 + (0.5 * math.cos(math.radians(latitude)))
    noise = random.uniform(-0.2, 0.2)
    return round(base_eto + noise, 2)


def simulate_weekly_rainfall(latitude: float, longitude: float) -> float:
    # simulate ITCZ effect
    seasonal_effect = 20 * math.sin(math.radians(latitude + longitude))
    base_rain = 10 + seasonal_effect
    noise = random.uniform(-5, 5)
    rain = max(0, base_rain + noise)
    return round(rain, 1)
