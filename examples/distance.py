"""Measure great-circle distance between two bundled cities."""

from pyworldatlas import Atlas


with Atlas() as atlas:
    tokyo = atlas.city("Tokyo", country="Japan")
    paris = atlas.city("Paris", country="France")
    print(f"Tokyo to Paris: {atlas.distance_between(tokyo, paris):,.0f} km")
    print(f"Initial bearing: {tokyo.coordinates.bearing_to(paris.coordinates):.1f} degrees")
