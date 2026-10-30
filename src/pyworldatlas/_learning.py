"""Flashcards and quiz answers, picked the same way on every computer.

Teachers need the same seed to give the same questions to every student, on
every Python version. So countries are ordered by a SHA-256 hash of their
stable M49 code and the seed, never by :mod:`random`, whose results can
change between Python versions.
"""

from __future__ import annotations

from collections.abc import Callable

from .models import Country, Flashcard


def stable_country_sample(
    candidates: tuple[Country, ...], count: int, seed: int | str
) -> tuple[Country, ...]:
    """Select countries by a versioned SHA-256 ranking, independent of row order."""
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("count must be a positive integer")
    if count > len(candidates):
        raise ValueError(f"count {count} exceeds the {len(candidates)} available countries")
    from hashlib import sha256

    def rank(country: Country) -> tuple[bytes, str]:
        identifier = country.codes.numeric or country.alpha3 or country.alpha2
        payload = f"pyworldatlas:0.2:{seed}:{identifier}".encode()
        return sha256(payload).digest(), identifier

    return tuple(sorted(candidates, key=rank)[:count])


def stable_text_order(
    values: tuple[str, ...], *, seed: int | str, namespace: str
) -> tuple[str, ...]:
    """Order text deterministically without depending on global random state."""
    from hashlib import sha256

    def rank(value: str) -> tuple[bytes, str]:
        payload = f"pyworldatlas:0.8:{namespace}:{seed}:{value}".encode()
        return sha256(payload).digest(), value

    return tuple(sorted(values, key=rank))


FLASHCARD_TOPICS = (
    "alpha_2_codes",
    "alpha_3_codes",
    "areas",
    "border_counts",
    "calling_codes",
    "capitals",
    "climate_zones",
    "coastlines",
    "continents",
    "countries_from_capitals",
    "currencies",
    "driving_sides",
    "flags",
    "highest_points",
    "language_codes",
    "local_names",
    "lakes",
    "m49_codes",
    "mains_electricity",
    "neighbors",
    "plug_types",
    "population_density",
    "populations",
    "regions",
    "rivers",
    "top_level_domains",
)


def has_flashcard_answer(
    country: Country, topic: str, has_neighbors: Callable[[Country], bool]
) -> bool:
    """Return whether ``country`` has the field a ``topic`` flashcard needs."""
    if topic in {"capitals", "countries_from_capitals"}:
        return country.capital is not None
    if topic == "alpha_3_codes":
        return country.alpha3 is not None
    if topic == "areas":
        return country.area_km2 is not None
    if topic == "calling_codes":
        return bool(country.calling_codes)
    if topic == "climate_zones":
        return country.climate.dominant_zone is not None
    if topic == "coastlines":
        return country.coastline_km is not None
    if topic == "continents":
        return country.continent is not None
    if topic == "currencies":
        return country.currency is not None
    if topic == "flags":
        return country.flag_emoji is not None
    if topic == "highest_points":
        return country.highest_point is not None
    if topic == "language_codes":
        return bool(country.language_codes)
    if topic == "local_names":
        return bool(country.local_names)
    if topic == "lakes":
        return bool(country.lakes)
    if topic == "m49_codes":
        return country.codes.numeric is not None
    if topic == "neighbors":
        return has_neighbors(country)
    if topic == "population_density":
        return country.population_density is not None
    if topic == "populations":
        return country.population is not None
    if topic == "regions":
        return country.region is not None
    if topic == "rivers":
        return bool(country.rivers)
    if topic == "top_level_domains":
        return country.top_level_domain is not None
    if topic == "driving_sides":
        return country.travel is not None and country.travel.driving_side is not None
    if topic == "plug_types":
        return country.travel is not None and bool(country.travel.plug_types)
    if topic == "mains_electricity":
        return country.travel is not None and bool(country.travel.voltages_v)
    return True


def build_flashcard(
    country: Country,
    topic: str,
    neighbors: Callable[[Country], tuple[Country, ...]],
) -> Flashcard:
    """Build one flashcard; callers check :func:`has_flashcard_answer` first."""
    reference = country.reference()
    answer: str | None
    # _has_flashcard_answer() guarantees the optional field each topic reads.
    if topic == "capitals":
        assert country.capital is not None
        prompt, answer = f"What is the capital of {country.name}?", country.capital.name
    elif topic == "countries_from_capitals":
        assert country.capital is not None
        prompt, answer = (
            f"{country.capital.name} is the capital of which country or area?",
            country.name,
        )
    elif topic == "flags":
        prompt, answer = f"Which country or area uses the flag {country.flag_emoji}?", country.name
    elif topic == "alpha_2_codes":
        prompt, answer = f"What is the alpha-2 code for {country.name}?", country.alpha2
    elif topic == "alpha_3_codes":
        prompt, answer = f"What is the alpha-3 code for {country.name}?", country.alpha3
    elif topic == "m49_codes":
        prompt, answer = f"What is the M49 code for {country.name}?", country.codes.numeric
    elif topic == "border_counts":
        prompt = f"How many reviewed land neighbors does {country.name} have?"
        answer = str(len(neighbors(country)))
    elif topic == "neighbors":
        prompt = f"Which countries or areas share a reviewed land border with {country.name}?"
        answer = ", ".join(neighbor.name for neighbor in neighbors(country))
    elif topic == "currencies":
        assert country.currency is not None
        label = country.currency.name or country.currency.code
        answer = f"{label} ({country.currency.code})" if label != country.currency.code else label
        prompt = f"Which currency is listed for {country.name}?"
    elif topic == "calling_codes":
        prompt, answer = f"Which calling code is listed for {country.name}?", ", ".join(country.calling_codes)
    elif topic == "top_level_domains":
        prompt, answer = f"What is the country-code top-level domain for {country.name}?", country.top_level_domain
    elif topic == "language_codes":
        prompt, answer = f"Which language codes are listed for {country.name}?", ", ".join(country.language_codes)
    elif topic == "continents":
        prompt, answer = f"Which continent contains {country.name}?", country.continent
    elif topic == "regions":
        prompt, answer = f"Which UN region contains {country.name}?", country.region
    elif topic == "climate_zones":
        zone = country.climate.dominant_zone
        assert zone is not None
        prompt = (
            f"Which Köppen-Geiger class has the largest represented share "
            f"of {country.name}?"
        )
        answer = f"{zone.code}: {zone.name}"
    elif topic == "coastlines":
        prompt = f"What coastline length is listed for {country.name}?"
        answer = f"{country.coastline_km:g} km"
    elif topic == "highest_points":
        point = country.highest_point
        assert point is not None
        prompt = f"What is the highest point listed for {country.name}?"
        answer = f"{point.name} ({point.elevation_m:g} m)"
    elif topic == "rivers":
        river = country.rivers[0]
        prompt = f"Name a source-listed major river associated with {country.name}."
        answer = (
            f"{river.name} ({river.length_km:g} km)"
            if river.length_km is not None else river.name
        )
    elif topic == "lakes":
        lake = country.lakes[0]
        prompt = f"Name a source-listed major lake associated with {country.name}."
        answer = (
            f"{lake.name} ({lake.area_km2:g} km²)"
            if lake.area_km2 is not None else lake.name
        )
    elif topic == "local_names":
        local_name = next(
            (name for name in country.local_names if name.language_code != "en"),
            country.local_names[0],
        )
        prompt = f"What is a locally official short name for {country.name} in {local_name.language_name}?"
        answer = local_name.short_name
    elif topic == "driving_sides":
        assert country.travel is not None
        prompt = f"On which side of the road do people drive in {country.name}?"
        answer = f"On the {country.travel.driving_side}"
    elif topic == "plug_types":
        assert country.travel is not None
        prompt = f"Which electrical plug types are used in {country.name}?"
        answer = "Type " + ", ".join(country.travel.plug_types)
    elif topic == "mains_electricity":
        assert country.travel is not None
        prompt = f"What is the household mains supply in {country.name}?"
        answer = "/".join(map(str, country.travel.voltages_v)) + " V"
        if country.travel.frequencies_hz:
            answer += ", " + "/".join(map(str, country.travel.frequencies_hz)) + " Hz"
    elif topic == "areas":
        prompt, answer = f"What area is listed for {country.name}?", f"{country.area_km2:g} km²"
    elif topic == "populations":
        prompt, answer = f"What snapshot population is listed for {country.name}?", f"{country.population:,}"
    else:
        prompt = f"What snapshot population density is calculated for {country.name}?"
        answer = f"{country.population_density:.2f} people per km²"
    return Flashcard(topic, prompt, str(answer), reference)
