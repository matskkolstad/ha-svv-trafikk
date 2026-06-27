"""Hjelpefunksjoner for å avgjøre om data tilhører et konfigurert område.

Støtter de tre områdetypene: fylke, veinummer og radius (lat/lon + km).
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .const import (
    AREA_TYPE_COUNTY,
    AREA_TYPE_RADIUS,
    AREA_TYPE_ROAD,
    CONF_AREA_TYPE,
    CONF_COUNTY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS_KM,
    CONF_ROAD,
    CONF_ROADS,
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returner avstanden i kilometer mellom to koordinater."""
    r = 6371.0  # jordens radius i km
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return 2 * r * asin(sqrt(a))


def _norm_road(value: str | None) -> str:
    """Normaliser veinummer for sammenligning (fjern mellomrom, store bokstaver).

    Eksempler: "E 18" -> "E18", "Rv 9" -> "RV9", "Ev18" -> "E18".
    """
    if not value:
        return ""
    v = value.upper().replace(" ", "").replace(".", "")
    # SVV bruker både "EV18" og "E18" for europaveger
    if v.startswith("EV"):
        v = "E" + v[2:]
    return v


def matches_area(
    config: dict,
    *,
    road: str | None = None,
    county: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> bool:
    """Avgjør om et dataobjekt hører til området definert i ``config``.

    Manglende informasjon på objektet behandles permissivt: et objekt uten
    koordinater filtreres f.eks. ikke bort av en radius-sjekk, slik at vi
    heller viser litt for mye enn å skjule relevant informasjon.
    """
    area_type = config.get(CONF_AREA_TYPE)

    if area_type == AREA_TYPE_COUNTY:
        wanted = str(config.get(CONF_COUNTY, "")).strip().lower()
        if wanted:
            have = str(county or "").strip().lower()
            # Mangler fylkesinfo på objektet – inkluder heller enn å skjule
            if have and wanted not in have:
                return False
        # Valgfri innsnevring til bestemte veier i fylket. Tom liste = alle veier.
        roads = config.get(CONF_ROADS) or []
        if roads:
            have_road = _norm_road(road)
            if not have_road:
                # Uten veinummer kan vi ikke avgjøre – inkluder (fail-open)
                return True
            wanted_roads = {_norm_road(r) for r in roads}
            return any(
                have_road == w or have_road.startswith(w) or w in have_road
                for w in wanted_roads
            )
        return True

    if area_type == AREA_TYPE_ROAD:
        wanted = _norm_road(config.get(CONF_ROAD))
        if not wanted:
            return True
        return _norm_road(road).startswith(wanted) or wanted in _norm_road(road)

    if area_type == AREA_TYPE_RADIUS:
        if latitude is None or longitude is None:
            # Uten koordinater kan vi ikke avgjøre – inkluder for sikkerhets skyld
            return True
        center_lat = config.get(CONF_LATITUDE)
        center_lon = config.get(CONF_LONGITUDE)
        radius = float(config.get(CONF_RADIUS_KM, 25))
        if center_lat is None or center_lon is None:
            return True
        return haversine_km(center_lat, center_lon, latitude, longitude) <= radius

    # Ukjent type – ingen filtrering
    return True
