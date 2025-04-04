import ee


def get_chirps_rainfall(field, start_date, end_date):
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
    return chirps.filterDate(start_date, end_date).sum()
