import geopy.geocoders

def get_lat_lon(location_name):
    geolocator = geopy.geocoders.Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(location_name, exactly_one=True)
    if location:
        return location.latitude, location.longitude
    else:
        return "Location not found"

if __name__ == "__main__":
    location_name = input("Enter location name: ")
    coordinates = get_lat_lon(location_name.strip())
    print("Coordinates:", coordinates)