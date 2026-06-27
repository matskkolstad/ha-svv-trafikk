"""Konstanter for SVV Trafikk-integrasjonen.

Denne filen samler alle faste verdier som brukes på tvers av integrasjonen,
slik at de er enkle å vedlikeholde ett sted.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

# Grunnleggende identifikasjon
DOMAIN: Final = "svv_traffic"
PLATFORMS: Final = ["sensor", "binary_sensor", "camera"]

# Standard oppdateringsintervall (kan overstyres i opsjoner)
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)
MIN_SCAN_INTERVAL_SECONDS: Final = 60

# ---------------------------------------------------------------------------
# Konfigurasjonsnøkler (brukes i config_flow og options_flow)
# ---------------------------------------------------------------------------
CONF_AREA_NAME: Final = "area_name"
CONF_AREA_TYPE: Final = "area_type"          # "county" | "road" | "radius"
CONF_COUNTY: Final = "county"                # fylkesnummer/-navn
CONF_MUNICIPALITY: Final = "municipality"
CONF_ROAD: Final = "road"                    # f.eks. "E18", "Rv9"
CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"
CONF_RADIUS_KM: Final = "radius_km"

CONF_DATA_TYPES: Final = "data_types"        # liste over aktiverte datatyper
CONF_SCAN_INTERVAL: Final = "scan_interval"

# DATEX-pålogging (valgfritt – kun nødvendig for visse datatyper)
CONF_DATEX_USERNAME: Final = "datex_username"
CONF_DATEX_PASSWORD: Final = "datex_password"
CONF_USE_DEMO: Final = "use_demo"            # demomodus med syntetiske data

# ---------------------------------------------------------------------------
# Områdetyper
# ---------------------------------------------------------------------------
AREA_TYPE_COUNTY: Final = "county"
AREA_TYPE_ROAD: Final = "road"
AREA_TYPE_RADIUS: Final = "radius"
AREA_TYPES: Final = [AREA_TYPE_COUNTY, AREA_TYPE_ROAD, AREA_TYPE_RADIUS]

# ---------------------------------------------------------------------------
# Datatyper – hver tilsvarer en kilde og styrer hvilke entiteter som lages.
# "requires_datex" forteller om datatypen krever DATEX-pålogging.
# ---------------------------------------------------------------------------
DATA_INCIDENTS: Final = "incidents"            # veimeldinger / hendelser
DATA_ROAD_CLOSURES: Final = "road_closures"    # stengte veier/tunneler
DATA_TRAFFIC_VOLUME: Final = "traffic_volume"  # passeringer/trafikkmengde
DATA_TRAVEL_TIME: Final = "travel_time"        # reisetid / kø
DATA_WEBCAM: Final = "webcam"                  # webkamera
DATA_WEATHER: Final = "weather"                # kjøreforhold / vær

DATA_TYPE_REQUIRES_DATEX: Final = {
    DATA_INCIDENTS: True,
    DATA_ROAD_CLOSURES: True,
    DATA_TRAFFIC_VOLUME: False,   # åpent GraphQL-API
    DATA_TRAVEL_TIME: True,
    DATA_WEBCAM: True,
    DATA_WEATHER: True,
}

ALL_DATA_TYPES: Final = list(DATA_TYPE_REQUIRES_DATEX.keys())

# Datatyper vi kan levere uten DATEX-passord (fungerer ut av boksen)
OPEN_DATA_TYPES: Final = [
    dt for dt, needs in DATA_TYPE_REQUIRES_DATEX.items() if not needs
]

# ---------------------------------------------------------------------------
# Statusnivåer – brukes for farge/ikon i kortet
# ---------------------------------------------------------------------------
STATUS_OK: Final = "ok"            # grønn
STATUS_WARNING: Final = "warning"  # gul
STATUS_ALERT: Final = "alert"      # rød
STATUS_UNKNOWN: Final = "unknown"  # grå

# ---------------------------------------------------------------------------
# API-endepunkter
# ---------------------------------------------------------------------------
# Åpent GraphQL-API for trafikkdata (ingen pålogging)
TRAFIKKDATA_GRAPHQL_URL: Final = "https://trafikkdata-api.atlas.vegvesen.no/"

# DATEX 3.1 pull-endepunkter (krever pålogging via basic auth)
DATEX_BASE: Final = "https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi"
DATEX_SITUATION_URL: Final = f"{DATEX_BASE}/GetSituation/pullsnapshotdata"
DATEX_CCTV_URL: Final = f"{DATEX_BASE}/GetCCTVSiteTable/pullsnapshotdata"
DATEX_TRAVELTIME_URL: Final = f"{DATEX_BASE}/GetTravelTimeData/pullsnapshotdata"
DATEX_TRAVELTIME_LOC_URL: Final = (
    f"{DATEX_BASE}/GetPredefinedTravelTimeLocations/pullsnapshotdata"
)
DATEX_WEATHER_URL: Final = f"{DATEX_BASE}/GetMeasuredWeatherData/pullsnapshotdata"
DATEX_WEATHER_LOC_URL: Final = (
    f"{DATEX_BASE}/GetMeasurementWeatherSiteTable/pullsnapshotdata"
)

# Attribusjon kreves av NLOD-lisensen
ATTRIBUTION: Final = (
    "Inneholder data under norsk lisens for offentlige data (NLOD) "
    "tilgjengeliggjort av Statens vegvesen."
)

# ---------------------------------------------------------------------------
# Event-navn (for automasjoner / Node-RED)
# ---------------------------------------------------------------------------
EVENT_NEW_INCIDENT: Final = f"{DOMAIN}_new_incident"
EVENT_ROAD_CLOSED: Final = f"{DOMAIN}_road_closed"
EVENT_ROAD_REOPENED: Final = f"{DOMAIN}_road_reopened"
EVENT_CONGESTION_WARNING: Final = f"{DOMAIN}_congestion_warning"

# ---------------------------------------------------------------------------
# Service-navn
# ---------------------------------------------------------------------------
SERVICE_REFRESH: Final = "refresh"
SERVICE_GET_INCIDENTS: Final = "get_incidents"
