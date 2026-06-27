"""Coordinator som henter data fra alle aktiverte kilder og samordner dem.

Ansvar:
- Velge kilder basert på konfigurasjon og om DATEX-pålogging finnes
- Filtrere på det konfigurerte området
- Beregne samlet status
- Sende events ved nye hendelser / stengninger (for automasjoner)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SvvApiError
from .api.datex import DatexClient
from .api.demo import generate_demo_area
from .api.trafikkdata import TrafikkdataClient
from .area import matches_area
from .const import (
    CONF_AREA_NAME,
    CONF_DATA_TYPES,
    CONF_DATEX_PASSWORD,
    CONF_DATEX_USERNAME,
    CONF_SCAN_INTERVAL,
    CONF_USE_DEMO,
    DATA_INCIDENTS,
    DATA_ROAD_CLOSURES,
    DATA_TRAFFIC_VOLUME,
    DATA_TRAVEL_TIME,
    DATA_WEATHER,
    DATA_WEBCAM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL_SECONDS,
    EVENT_CONGESTION_WARNING,
    EVENT_NEW_INCIDENT,
    EVENT_ROAD_CLOSED,
    EVENT_ROAD_REOPENED,
    STATUS_ALERT,
    STATUS_OK,
    STATUS_WARNING,
)
from .models import AreaData

_LOGGER = logging.getLogger(__name__)

# Hvor mange trafikkpunkter vi henter volum for per oppdatering (ytelse).
_MAX_VOLUME_POINTS = 15


class SvvDataUpdateCoordinator(DataUpdateCoordinator[AreaData]):
    """Henter og samordner SVV-data for ett konfigurert område."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.config = {**entry.data, **entry.options}
        self._session = async_get_clientsession(hass)

        scan = self.config.get(CONF_SCAN_INTERVAL)
        if scan:
            interval = timedelta(seconds=max(int(scan), MIN_SCAN_INTERVAL_SECONDS))
        else:
            interval = DEFAULT_SCAN_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.config.get(CONF_AREA_NAME, 'omrade')}",
            update_interval=interval,
        )

        self._trafikkdata = TrafikkdataClient(self._session)
        self._datex: DatexClient | None = None
        username = self.config.get(CONF_DATEX_USERNAME)
        password = self.config.get(CONF_DATEX_PASSWORD)
        if username and password:
            self._datex = DatexClient(self._session, username, password)

        # Holder forrige tilstand for å oppdage endringer (events)
        self._known_incident_ids: set[str] = set()
        self._known_closure_ids: set[str] = set()

    @property
    def has_datex(self) -> bool:
        return self._datex is not None

    @property
    def enabled_types(self) -> list[str]:
        return self.config.get(CONF_DATA_TYPES, [])

    async def _async_update_data(self) -> AreaData:
        area_name = self.config.get(CONF_AREA_NAME, "Område")

        # Demomodus: returner syntetiske data og hopp over nettverkskall
        if self.config.get(CONF_USE_DEMO):
            data = generate_demo_area(area_name)
            self._fire_events(data)
            return data

        data = AreaData(area_name=area_name, last_updated=datetime.now(timezone.utc))
        enabled = self.enabled_types

        # --- Åpne trafikkdata (passeringer) -----------------------------
        if DATA_TRAFFIC_VOLUME in enabled:
            try:
                await self._collect_traffic_volume(data)
            except SvvApiError as err:
                data.errors.append(f"Trafikkdata: {err}")
                _LOGGER.warning("Feil ved henting av trafikkvolum: %s", err)

        # --- DATEX-baserte kilder ---------------------------------------
        if self._datex is not None:
            await self._collect_datex(data, enabled)
        else:
            needs_datex = [
                t
                for t in enabled
                if t in (DATA_INCIDENTS, DATA_ROAD_CLOSURES, DATA_TRAVEL_TIME,
                         DATA_WEBCAM, DATA_WEATHER)
            ]
            if needs_datex:
                data.errors.append(
                    "DATEX-pålogging mangler – noen datatyper er ikke tilgjengelige."
                )

        data.overall_status = self._compute_overall_status(data)
        self._fire_events(data)

        if data.errors and not any(
            [data.incidents, data.closures, data.traffic_volume,
             data.travel_times, data.webcams, data.weather]
        ):
            # Alt feilet – la HA markere som utilgjengelig
            raise UpdateFailed("; ".join(data.errors))

        return data

    async def _collect_traffic_volume(self, data: AreaData) -> None:
        points = await self._trafikkdata.async_get_points()
        # Filtrer punkter på området før vi henter volum (sparer kall)
        in_area = [
            p
            for p in points
            if matches_area(
                self.config,
                road=p.get("road"),
                latitude=p.get("lat"),
                longitude=p.get("lon"),
            )
        ]
        for p in in_area[:_MAX_VOLUME_POINTS]:
            vp = await self._trafikkdata.async_get_volume(p)
            if vp is not None:
                data.traffic_volume.append(vp)

    async def _collect_datex(self, data: AreaData, enabled: list[str]) -> None:
        assert self._datex is not None

        if DATA_INCIDENTS in enabled or DATA_ROAD_CLOSURES in enabled:
            try:
                incidents = await self._datex.async_get_situations()
                for inc in incidents:
                    if not matches_area(
                        self.config,
                        road=inc.road,
                        county=inc.county,
                        latitude=inc.latitude,
                        longitude=inc.longitude,
                    ):
                        continue
                    if inc.is_closure and DATA_ROAD_CLOSURES in enabled:
                        data.closures.append(inc)
                    elif DATA_INCIDENTS in enabled:
                        data.incidents.append(inc)
            except SvvApiError as err:
                data.errors.append(f"Veimeldinger: {err}")

        if DATA_TRAVEL_TIME in enabled:
            try:
                for tt in await self._datex.async_get_travel_times():
                    if matches_area(self.config, road=tt.road):
                        data.travel_times.append(tt)
            except SvvApiError as err:
                data.errors.append(f"Reisetid: {err}")

        if DATA_WEBCAM in enabled:
            try:
                for cam in await self._datex.async_get_webcams():
                    if matches_area(
                        self.config,
                        road=cam.road,
                        latitude=cam.latitude,
                        longitude=cam.longitude,
                    ):
                        data.webcams.append(cam)
            except SvvApiError as err:
                data.errors.append(f"Webkamera: {err}")

        if DATA_WEATHER in enabled:
            try:
                for ws in await self._datex.async_get_weather():
                    if matches_area(
                        self.config,
                        latitude=ws.latitude,
                        longitude=ws.longitude,
                    ):
                        data.weather.append(ws)
            except SvvApiError as err:
                data.errors.append(f"Vær: {err}")

    @staticmethod
    def _compute_overall_status(data: AreaData) -> str:
        statuses = [STATUS_OK]
        if data.closures:
            statuses.append(STATUS_ALERT)
        statuses.extend(i.severity for i in data.incidents)
        statuses.extend(t.status for t in data.travel_times)
        if STATUS_ALERT in statuses:
            return STATUS_ALERT
        if STATUS_WARNING in statuses:
            return STATUS_WARNING
        return STATUS_OK

    def _fire_events(self, data: AreaData) -> None:
        """Send events for nye hendelser/stengninger og gjenåpninger."""
        area = data.area_name

        current_incident_ids = {i.id for i in data.incidents}
        for inc in data.incidents:
            if inc.id not in self._known_incident_ids:
                self.hass.bus.async_fire(
                    EVENT_NEW_INCIDENT, {"area": area, **inc.as_dict()}
                )
                if inc.severity == STATUS_WARNING and inc.category == "congestion":
                    self.hass.bus.async_fire(
                        EVENT_CONGESTION_WARNING, {"area": area, **inc.as_dict()}
                    )

        current_closure_ids = {c.id for c in data.closures}
        for cls in data.closures:
            if cls.id not in self._known_closure_ids:
                self.hass.bus.async_fire(
                    EVENT_ROAD_CLOSED, {"area": area, **cls.as_dict()}
                )
        # Gjenåpning: var stengt før, men ikke nå
        for old_id in self._known_closure_ids - current_closure_ids:
            self.hass.bus.async_fire(
                EVENT_ROAD_REOPENED, {"area": area, "id": old_id}
            )

        self._known_incident_ids = current_incident_ids
        self._known_closure_ids = current_closure_ids
