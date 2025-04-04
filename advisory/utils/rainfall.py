# Purpose: Adjusts rainfall based on soil type (FAO-56 Table 22).
SOIL_EFFECTIVENESS = {
    "clay": 0.6,   # 60% effective
    "loam": 0.8,   # 80% effective (default)
    "sandy": 0.9   # 90% effective
}


def get_effective_rainfall(total_rainfall, soil_type="loam"):
    return total_rainfall * SOIL_EFFECTIVENESS.get(soil_type.lower(), 0.8)
