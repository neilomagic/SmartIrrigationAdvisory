# FAO-56 standardized coefficients
from datetime import datetime


# Purpose: Manages dynamic crop coefficients (Kc) based on growth stages.

CROP_KC = {
    "maize": [0.4, 1.2, 0.6],  # [Initial, Mid, Late]
    "soybean": [0.4, 1.15, 0.5]
}


def get_kc(crop_type, planting_date):
    days_since_planting = (datetime.now() - planting_date).days
    if days_since_planting < 30:
        return CROP_KC[crop_type][0]  # Initial stage
    elif days_since_planting < 80:
        return CROP_KC[crop_type][1]  # Mid-season
    else:
        return CROP_KC[crop_type][2]  # Late season
