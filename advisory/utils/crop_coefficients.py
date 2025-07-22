# FAO-56 standardized coefficients
from datetime import datetime, timedelta

# Purpose: Manages dynamic crop coefficients (Kc) based on growth stages.

# Expanded crop database with FAO-56 coefficients
CROP_DATA = {
    "maize": {
        "kc_stages": [0.3, 1.2, 0.6],
        "duration_days": 120,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (20, 30),
        "water_requirement": "high"
    },
    "soybean": {
        "kc_stages": [0.4, 1.15, 0.5],
        "duration_days": 110,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (20, 30),
        "water_requirement": "high"
    },
    "rice": {
        "kc_stages": [1.1, 1.2, 0.9],
        "duration_days": 150,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (25, 35),
        "water_requirement": "very_high"
    },
    "wheat": {
        "kc_stages": [0.3, 1.15, 0.3],
        "duration_days": 100,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": False,
        "optimal_temp": (15, 25),
        "water_requirement": "medium"
    },
    "sugarcane": {
        "kc_stages": [0.4, 1.25, 0.75],
        "duration_days": 365,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (25, 35),
        "water_requirement": "very_high"
    },
    "cotton": {
        "kc_stages": [0.35, 1.2, 0.7],
        "duration_days": 180,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (25, 35),
        "water_requirement": "high"
    },
    "beans": {
        "kc_stages": [0.35, 1.1, 0.6],
        "duration_days": 80,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (20, 30),
        "water_requirement": "medium"
    },
    "potatoes": {
        "kc_stages": [0.45, 1.15, 0.75],
        "duration_days": 120,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (15, 25),
        "water_requirement": "high"
    },
    "tomatoes": {
        "kc_stages": [0.4, 1.2, 0.8],
        "duration_days": 100,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": True,
        "optimal_temp": (20, 30),
        "water_requirement": "high"
    },
    "cassava": {
        "kc_stages": [0.3, 1.1, 0.6],
        "duration_days": 300,
        "stages": ["Initial", "Mid-Season", "Late Season"],
        "water_sensitive": False,
        "optimal_temp": (25, 35),
        "water_requirement": "low"
    }
}


def get_crop_info(crop_type):
    """Get comprehensive crop information"""
    return CROP_DATA.get(crop_type.lower(), CROP_DATA["maize"])


def get_kc(crop_type, planting_date):
    """Get crop coefficient based on days since planting"""
    crop_info = get_crop_info(crop_type)
    days_since_planting = (datetime.now().date() - planting_date).days

    if days_since_planting < crop_info["duration_days"] * 0.25:
        return crop_info["kc_stages"][0], crop_info["stages"][0]
    elif days_since_planting < crop_info["duration_days"] * 0.75:
        return crop_info["kc_stages"][1], crop_info["stages"][1]
    else:
        return crop_info["kc_stages"][2], crop_info["stages"][2]


def get_crop_duration(crop_type):
    """Get total crop duration in days"""
    return get_crop_info(crop_type)["duration_days"]


def is_water_sensitive(crop_type):
    """Check if crop is water sensitive"""
    return get_crop_info(crop_type)["water_sensitive"]


def get_water_requirement_level(crop_type):
    """Get water requirement level"""
    return get_crop_info(crop_type)["water_requirement"]
