from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geolocator = Nominatim(user_agent="coach_app")
tf = TimezoneFinder()

def get_time_zone_for_city(city_name: str) -> str:
    try:
        location = geolocator.geocode(city_name)
        if location:
            timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return timezone_str if timezone_str else 'UTC'
    except Exception as e:
        print(f"Error finding time zone for {city_name}: {e}")
    return 'UTC'
