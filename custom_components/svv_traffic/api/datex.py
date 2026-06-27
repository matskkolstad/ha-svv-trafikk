"""Klient for SVVs DATEX II 3.1-tjenester (XML, krever pålogging).

Disse endepunktene krever brukernavn/passord (basic auth) som du får ved
å søke om DATEX-tilgang hos Statens vegvesen. Tilgangen er knyttet til en
fast IP-adresse oppgitt ved registrering.

Vi parser kun de feltene vi trenger, og er bevisst tolerante mot variasjoner
i navnerom og struktur, siden DATEX-XML er omfattende.
"""

from __future__ import annotations

import logging
from datetime import datetime
from xml.etree import ElementTree as ET

from aiohttp import BasicAuth, ClientError, ClientSession

from ..const import (
    DATEX_CCTV_URL,
    DATEX_SITUATION_URL,
    DATEX_TRAVELTIME_URL,
    DATEX_WEATHER_URL,
    STATUS_ALERT,
    STATUS_OK,
    STATUS_WARNING,
)
from ..models import Incident, TravelTime, Webcam, WeatherStation
from . import SvvApiError, SvvAuthError

_LOGGER = logging.getLogger(__name__)


def _localname(tag: str) -> str:
    """Fjern XML-navnerom: '{ns}Situation' -> 'Situation'."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _find_text(elem: ET.Element, *names: str) -> str | None:
    """Finn første descendant med et av de gitte lokalnavnene og returner tekst."""
    wanted = set(names)
    for child in elem.iter():
        if _localname(child.tag) in wanted and child.text and child.text.strip():
            return child.text.strip()
    return None


def _find_county(rec: ET.Element) -> str | None:
    """Hent fylkesnavn fra DATEX ``namedArea``-blokken.

    Norske situasjonsdata har ikke noe eget ``countyName``/``county``-felt.
    Fylket ligger i ``<namedArea>`` med ``subdivisionType=county``, og selve
    navnet er nestet i ``namedArea/areaName/values/value`` (f.eks. "Agder").
    Vi foretrekker county-blokken, men faller tilbake til et evt. kommunenavn
    dersom fylke mangler.
    """
    fallback: str | None = None
    for na in rec.iter():
        if _localname(na.tag) != "namedArea":
            continue
        subtype = _find_text(na, "subdivisionType")
        name: str | None = None
        for child in na.iter():
            if _localname(child.tag) == "areaName":
                name = _find_text(child, "value")
                break
        if subtype == "county" and name:
            return name
        if name and fallback is None:
            fallback = name
    return fallback


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# Nøkkelord som indikerer at en hendelse er en stenging
_CLOSURE_HINTS = (
    "closed",
    "carriagewayClosed",
    "roadClosed",
    "stengt",
    "tunnelClosed",
)
# Kategorisering basert på DATEX record-typer (forenklet)
_CATEGORY_MAP = {
    "MaintenanceWorks": "roadworks",
    "ConstructionWorks": "roadworks",
    "Roadworks": "roadworks",
    "Accident": "accident",
    "AbnormalTraffic": "congestion",
    "PoorEnvironmentConditions": "condition",
    "RoadOrCarriagewayOrLaneManagement": "closure",
    "GeneralNetworkManagement": "closure",
}


class DatexClient:
    """Asynkron klient mot DATEX-pull-tjenestene."""

    def __init__(
        self, session: ClientSession, username: str, password: str
    ) -> None:
        self._session = session
        self._auth = BasicAuth(username, password)

    async def _get_xml(self, url: str) -> ET.Element:
        """Hent og parse XML fra et DATEX-endepunkt."""
        try:
            async with self._session.get(url, auth=self._auth) as resp:
                if resp.status in (401, 403):
                    raise SvvAuthError(
                        "DATEX avviste påloggingen (401/403). Sjekk brukernavn, "
                        "passord og at IP-adressen din er registrert hos SVV."
                    )
                if resp.status != 200:
                    text = await resp.text()
                    raise SvvApiError(
                        f"DATEX svarte med status {resp.status}: {text[:200]}"
                    )
                raw = await resp.read()
        except ClientError as err:
            raise SvvApiError(f"Nettverksfeil mot DATEX: {err}") from err

        try:
            return ET.fromstring(raw)
        except ET.ParseError as err:
            raise SvvApiError(f"Kunne ikke tolke DATEX-XML: {err}") from err

    # ------------------------------------------------------------------
    # Veimeldinger / hendelser / stengninger
    # ------------------------------------------------------------------
    async def async_get_situations(self) -> list[Incident]:
        """Hent alle situasjoner og normaliser til Incident-objekter."""
        root = await self._get_xml(DATEX_SITUATION_URL)
        incidents: list[Incident] = []

        for sit in root.iter():
            if _localname(sit.tag) != "situation":
                continue
            sit_id = sit.get("id") or _find_text(sit, "situationId") or "ukjent"

            # En situasjon kan ha flere records; vi lager én Incident per record
            records = [
                r for r in sit.iter() if _localname(r.tag) == "situationRecord"
            ]
            if not records:
                records = [sit]

            for rec in records:
                rec_type = rec.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}type"
                ) or ""
                rec_type = rec_type.split(":")[-1]
                category = _CATEGORY_MAP.get(rec_type, "other")

                comment = _find_text(rec, "comment", "generalPublicComment", "value")
                location = _find_text(
                    rec, "locationDescription", "roadName", "areaName"
                )
                # Prioriter veinummer (E39, R9) over veinavn for konsistent
                # filtrering og veivalg; fall tilbake til navn kun om nr. mangler.
                road = _find_text(rec, "roadNumber") or _find_text(rec, "roadName")
                county = _find_county(rec)

                lat = _find_text(rec, "latitude")
                lon = _find_text(rec, "longitude")
                start = _parse_dt(_find_text(rec, "overallStartTime", "startTime"))
                end = _parse_dt(_find_text(rec, "overallEndTime", "endTime"))

                raw_xml = ET.tostring(rec, encoding="unicode")
                is_closure = any(h.lower() in raw_xml.lower() for h in _CLOSURE_HINTS)

                if is_closure or category in ("accident",):
                    severity = STATUS_ALERT
                elif category in ("roadworks", "congestion", "condition"):
                    severity = STATUS_WARNING
                else:
                    severity = STATUS_OK

                incidents.append(
                    Incident(
                        id=f"{sit_id}:{rec.get('id', len(incidents))}",
                        title=location or rec_type or "Veimelding",
                        description=comment or "",
                        severity=severity,
                        category="closure" if is_closure else category,
                        road=road,
                        county=county,
                        location_description=location,
                        latitude=float(lat) if lat else None,
                        longitude=float(lon) if lon else None,
                        start_time=start,
                        end_time=end,
                        is_closure=is_closure,
                    )
                )

        _LOGGER.debug("DATEX: tolket %d hendelser", len(incidents))
        return incidents

    async def async_get_county_roads(self, county: str) -> list[tuple[str, int]]:
        """List distinkte veinummer som har veimeldinger i et gitt fylke.

        Brukes av oppsettflyten til å la brukeren velge hvilke veier området
        skal omfatte. Returnerer en liste av (veinummer, antall hendelser),
        sortert synkende på antall. Henter rått snapshot og er bevisst lett –
        vi bygger ikke fullstendige Incident-objekter.
        """
        root = await self._get_xml(DATEX_SITUATION_URL)
        wanted = county.strip().lower()
        counts: dict[str, int] = {}
        for rec in root.iter():
            if _localname(rec.tag) != "situationRecord":
                continue
            rec_county = _find_county(rec)
            if not rec_county or wanted not in rec_county.strip().lower():
                continue
            road = _find_text(rec, "roadNumber") or _find_text(rec, "roadName")
            if not road:
                continue
            counts[road] = counts.get(road, 0) + 1
        roads = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        _LOGGER.debug(
            "DATEX: fant %d distinkte veier i fylket '%s'", len(roads), county
        )
        return roads

    # ------------------------------------------------------------------
    # Webkameraer
    # ------------------------------------------------------------------
    async def async_get_webcams(self) -> list[Webcam]:
        root = await self._get_xml(DATEX_CCTV_URL)
        cams: list[Webcam] = []
        for site in root.iter():
            if _localname(site.tag) not in ("cctvCameraMetadataRecord", "cctvSite"):
                continue
            cam_id = site.get("id") or _find_text(site, "id") or str(len(cams))
            name = _find_text(site, "cameraName", "name", "value") or cam_id
            url = _find_text(site, "stillImageUrl", "imageUrl", "urlLinkAddress")
            lat = _find_text(site, "latitude")
            lon = _find_text(site, "longitude")
            cams.append(
                Webcam(
                    id=cam_id,
                    name=name,
                    image_url=url,
                    latitude=float(lat) if lat else None,
                    longitude=float(lon) if lon else None,
                    road=_find_text(site, "roadNumber"),
                    county=_find_county(site),
                )
            )
        _LOGGER.debug("DATEX: tolket %d webkameraer", len(cams))
        return cams

    # ------------------------------------------------------------------
    # Reisetid / kø
    # ------------------------------------------------------------------
    async def async_get_travel_times(self) -> list[TravelTime]:
        root = await self._get_xml(DATEX_TRAVELTIME_URL)
        results: list[TravelTime] = []
        for elem in root.iter():
            if _localname(elem.tag) != "elaboratedData":
                continue
            tt_id = elem.get("id") or str(len(results))
            measured = _find_text(elem, "travelTime", "duration")
            normal = _find_text(elem, "freeFlowTravelTime", "normallyExpectedTravelTime")
            trend = _find_text(elem, "delayTrend", "trend")
            name = _find_text(elem, "name", "value") or tt_id

            tt = float(measured) if measured else None
            nt = float(normal) if normal else None
            delay = int(tt - nt) if (tt is not None and nt is not None) else None

            status = STATUS_OK
            if delay is not None and nt:
                ratio = (tt / nt) if nt else 1
                if ratio >= 1.5:
                    status = STATUS_ALERT
                elif ratio >= 1.2:
                    status = STATUS_WARNING

            results.append(
                TravelTime(
                    id=tt_id,
                    name=name,
                    travel_time_seconds=int(tt) if tt else None,
                    normal_time_seconds=int(nt) if nt else None,
                    delay_seconds=delay,
                    trend=trend,
                    status=status,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Vær / kjøreforhold
    # ------------------------------------------------------------------
    async def async_get_weather(self) -> list[WeatherStation]:
        root = await self._get_xml(DATEX_WEATHER_URL)
        stations: list[WeatherStation] = []
        for site in root.iter():
            if _localname(site.tag) != "measurementSiteRecord":
                continue
            st_id = site.get("id") or str(len(stations))
            air = _find_text(site, "airTemperature")
            road_t = _find_text(site, "roadSurfaceTemperature")
            wind = _find_text(site, "windSpeed")
            precip = _find_text(site, "precipitationType", "precipitation")

            status = STATUS_OK
            try:
                if road_t is not None and float(road_t) <= 0:
                    status = STATUS_WARNING
                if precip and precip.lower() in ("snow", "freezingrain", "snø"):
                    status = STATUS_ALERT
            except ValueError:
                pass

            stations.append(
                WeatherStation(
                    id=st_id,
                    name=_find_text(site, "name", "value") or st_id,
                    air_temperature=float(air) if air else None,
                    road_temperature=float(road_t) if road_t else None,
                    wind_speed=float(wind) if wind else None,
                    precipitation=precip,
                    status=status,
                    latitude=None,
                    longitude=None,
                )
            )
        return stations

    async def async_verify(self) -> bool:
        """Test påloggingen ved å hente situasjonsdata (kaster ved feil)."""
        await self._get_xml(DATEX_SITUATION_URL)
        return True
