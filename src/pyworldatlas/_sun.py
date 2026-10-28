"""Sunrise, sunset, and day length anywhere on Earth, using only the standard library.

The calculation follows the NOAA solar position equations, which agree with
published almanac times to about a minute between latitudes 72° north and
south. Times are in UTC. Near the poles the sun can stay up or down all day;
``sunrise`` and ``sunset`` are then ``None`` and ``day_length_hours`` is 24 or 0.
"""

from __future__ import annotations

from datetime import date as Date
from datetime import datetime, timedelta, timezone
from math import acos, asin, cos, degrees, radians, sin, tan

# The sun's centre is 0.833° below the horizon at sunrise and sunset, once
# atmospheric refraction and the size of the sun's disc are allowed for.
_HORIZON = -0.833


def _solar(day: Date, longitude: float) -> tuple[float, float]:
    """Return the sun's declination (degrees) and the equation of time (minutes) near local noon."""
    # Julian centuries from 2000-01-01 12:00 UTC to about local solar noon.
    days = day.toordinal() - Date(2000, 1, 1).toordinal() - longitude / 360
    julian_century = days / 36525
    mean_longitude = (280.46646 + julian_century * (36000.76983 + julian_century * 0.0003032)) % 360
    mean_anomaly = 357.52911 + julian_century * (35999.05029 - 0.0001537 * julian_century)
    eccentricity = 0.016708634 - julian_century * (0.000042037 + 0.0000001267 * julian_century)
    anomaly = radians(mean_anomaly)
    centre = (
        sin(anomaly) * (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century))
        + sin(2 * anomaly) * (0.019993 - 0.000101 * julian_century)
        + sin(3 * anomaly) * 0.000289
    )
    true_longitude = mean_longitude + centre
    omega = 125.04 - 1934.136 * julian_century
    apparent_longitude = true_longitude - 0.00569 - 0.00478 * sin(radians(omega))
    obliquity = 23 + (26 + (21.448 - julian_century * (46.815 + julian_century * (0.00059 - julian_century * 0.001813))) / 60) / 60
    corrected_obliquity = obliquity + 0.00256 * cos(radians(omega))
    declination = degrees(asin(sin(radians(corrected_obliquity)) * sin(radians(apparent_longitude))))
    y = tan(radians(corrected_obliquity / 2)) ** 2
    longitude = radians(mean_longitude)
    equation_of_time = 4 * degrees(
        y * sin(2 * longitude)
        - 2 * eccentricity * sin(anomaly)
        + 4 * eccentricity * y * sin(anomaly) * cos(2 * longitude)
        - 0.5 * y * y * sin(4 * longitude)
        - 1.25 * eccentricity * eccentricity * sin(2 * anomaly)
    )
    return declination, equation_of_time


def sun_times(
    latitude: float, longitude: float, day: Date
) -> tuple[datetime, datetime | None, datetime | None, float, float]:
    """Return solar noon, sunrise, sunset (UTC), day length in hours, and noon sun height in degrees."""
    declination, equation_of_time = _solar(day, longitude)
    midnight = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    noon_minutes = 720 - 4 * longitude - equation_of_time
    solar_noon = (midnight + timedelta(minutes=noon_minutes)).replace(microsecond=0)
    noon_height = 90 - abs(latitude - declination)
    phi, delta = radians(latitude), radians(declination)
    ratio = (sin(radians(_HORIZON)) - sin(phi) * sin(delta)) / (cos(phi) * cos(delta) or 1e-12)
    if ratio <= -1:  # the sun never sets
        return solar_noon, None, None, 24.0, noon_height
    if ratio >= 1:  # the sun never rises
        return solar_noon, None, None, 0.0, noon_height
    half_day_minutes = 4 * degrees(acos(ratio))
    sunrise = (solar_noon - timedelta(minutes=half_day_minutes)).replace(microsecond=0)
    sunset = (solar_noon + timedelta(minutes=half_day_minutes)).replace(microsecond=0)
    return solar_noon, sunrise, sunset, 2 * half_day_minutes / 60, noon_height
