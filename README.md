# 🌾 Smart Irrigation Advisory System

A web-based decision support tool that helps farmers receive field-specific irrigation advice based on crop type, soil conditions, and recent weather data.

## ✅ What It Does

- Select your field using an interactive map
- Enter crop type, soil type, and planting date
- Receive weekly irrigation advice based on:
  - Crop stage
  - Evapotranspiration (ET₀)
  - Rainfall (from Google Earth Engine or simulated)
  - Crop water need and deficit

## 🚀 How to Run

1. **Clone the project**

```bash
git clone https://github.com/your-username/smart-irrigation-advisory.git
cd smart-irrigation-advisory
```

2. **Set up a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up database**

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. **Run the app**

```bash
python manage.py runserver
```

Then open: [http://localhost:8000/](http://localhost:8000/)

## 🌐 Google Earth Engine (Optional)

To enable real satellite data for ET₀ and rainfall:

```bash
pip install earthengine-api
earthengine authenticate
```

If not available, the system will simulate weather data intelligently.

## 📁 Key Features

- Clean and responsive interface (Bootstrap + Leaflet)
- Smart map-based field registration
- Real or simulated advisory engine
- Advisory dashboard and history
- Admin panel for data management

---
