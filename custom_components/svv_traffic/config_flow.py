"""Config flow for SVV Trafikk – UI-basert oppsett.

Trinn:
1. Velg navn, områdetype og datatyper, evt. demomodus
2. Avhengig av områdetype: skriv inn fylke / veinummer / radius
3. Valgfri DATEX-pålogging (kreves for noen datatyper)
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SvvApiError, SvvAuthError
from .api.datex import DatexClient
from .const import (
    ALL_DATA_TYPES,
    AREA_TYPE_COUNTY,
    AREA_TYPE_RADIUS,
    AREA_TYPE_ROAD,
    AREA_TYPES,
    CONF_AREA_NAME,
    CONF_AREA_TYPE,
    CONF_COUNTY,
    CONF_DATA_TYPES,
    CONF_DATEX_PASSWORD,
    CONF_DATEX_USERNAME,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS_KM,
    CONF_ROAD,
    CONF_ROADS,
    CONF_SCAN_INTERVAL,
    CONF_USE_DEMO,
    DATA_TYPE_REQUIRES_DATEX,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NORWEGIAN_COUNTIES,
)


def _data_type_selector(default: list[str] | None = None) -> dict:
    """Bygg en multi-select for datatyper."""
    return {dt: dt for dt in ALL_DATA_TYPES}


class SvvConfigFlow(ConfigFlow, domain=DOMAIN):
    """Håndterer oppsettsdialogen."""

    VERSION = 1

    def __init__(self) -> None:
        self._base: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._base = dict(user_input)
            if user_input.get(CONF_USE_DEMO):
                # Demomodus trenger ingen videre konfigurasjon
                return self.async_create_entry(
                    title=user_input[CONF_AREA_NAME] + " (demo)",
                    data=self._base,
                )
            # Gå videre til områdedetaljer
            return await self.async_step_area()

        schema = vol.Schema(
            {
                vol.Required(CONF_AREA_NAME, default="Mitt område"): str,
                vol.Required(CONF_AREA_TYPE, default=AREA_TYPE_RADIUS): vol.In(
                    AREA_TYPES
                ),
                vol.Required(
                    CONF_DATA_TYPES, default=ALL_DATA_TYPES
                ): cv_multi_select(_data_type_selector()),
                vol.Optional(CONF_USE_DEMO, default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_area(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Samle inn detaljer for den valgte områdetypen."""
        area_type = self._base[CONF_AREA_TYPE]
        errors: dict[str, str] = {}

        if user_input is not None:
            self._base.update(user_input)
            # Trenger vi DATEX? Bare hvis en valgt datatype krever det.
            needs_datex = any(
                DATA_TYPE_REQUIRES_DATEX.get(dt) for dt in self._base[CONF_DATA_TYPES]
            )
            if needs_datex:
                return await self.async_step_datex()
            return await self._after_credentials()

        if area_type == AREA_TYPE_COUNTY:
            schema = vol.Schema(
                {vol.Required(CONF_COUNTY, default="Agder"): vol.In(NORWEGIAN_COUNTIES)}
            )
        elif area_type == AREA_TYPE_ROAD:
            schema = vol.Schema({vol.Required(CONF_ROAD, default="E18"): str})
        else:  # radius
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): vol.Coerce(float),
                    vol.Required(CONF_RADIUS_KM, default=25): vol.All(
                        vol.Coerce(float), vol.Range(min=1, max=500)
                    ),
                }
            )
        return self.async_show_form(
            step_id="area", data_schema=schema, errors=errors
        )

    async def async_step_datex(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Valgfri DATEX-pålogging, med verifisering."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input.get(CONF_DATEX_USERNAME, "").strip()
            password = user_input.get(CONF_DATEX_PASSWORD, "").strip()

            if not username and not password:
                # Brukeren hopper over – fortsett uten DATEX
                return await self._after_credentials()

            # Verifiser påloggingen
            session = async_get_clientsession(self.hass)
            client = DatexClient(session, username, password)
            try:
                await client.async_verify()
            except SvvAuthError:
                errors["base"] = "auth"
            except SvvApiError:
                errors["base"] = "cannot_connect"
            else:
                self._base[CONF_DATEX_USERNAME] = username
                self._base[CONF_DATEX_PASSWORD] = password
                return await self._after_credentials()

        schema = vol.Schema(
            {
                vol.Optional(CONF_DATEX_USERNAME, default=""): str,
                vol.Optional(CONF_DATEX_PASSWORD, default=""): str,
            }
        )
        return self.async_show_form(
            step_id="datex", data_schema=schema, errors=errors
        )

    async def _after_credentials(self) -> ConfigFlowResult:
        """Etter at evt. DATEX-creds er kjent: vis veivalg for fylke-områder."""
        if (
            self._base.get(CONF_AREA_TYPE) == AREA_TYPE_COUNTY
            and self._base.get(CONF_DATEX_USERNAME)
            and self._base.get(CONF_DATEX_PASSWORD)
        ):
            return await self.async_step_roads()
        return self._finish()

    async def async_step_roads(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """La brukeren velge hvilke veier i fylket området skal omfatte.

        Listen bygges fra veier som faktisk har veimeldinger i fylket akkurat
        nå. Velges ingen, tas alle veier i fylket med (ingen innsnevring).
        """
        if user_input is not None:
            self._base[CONF_ROADS] = user_input.get(CONF_ROADS, [])
            return self._finish()

        session = async_get_clientsession(self.hass)
        client = DatexClient(
            session,
            self._base[CONF_DATEX_USERNAME],
            self._base[CONF_DATEX_PASSWORD],
        )
        try:
            roads = await client.async_get_county_roads(self._base[CONF_COUNTY])
        except SvvApiError:
            roads = []

        if not roads:
            # Ingen veier å velge mellom – hopp over og ta med alt i fylket
            self._base[CONF_ROADS] = []
            return self._finish()

        options = {road: f"{road} ({count})" for road, count in roads}
        schema = vol.Schema(
            {vol.Optional(CONF_ROADS, default=[]): cv_multi_select(options)}
        )
        return self.async_show_form(
            step_id="roads",
            data_schema=schema,
            description_placeholders={"county": self._base[CONF_COUNTY]},
        )

    def _finish(self) -> ConfigFlowResult:
        return self.async_create_entry(
            title=self._base[CONF_AREA_NAME], data=self._base
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> SvvOptionsFlow:
        return SvvOptionsFlow(entry)


class SvvOptionsFlow(OptionsFlow):
    """Lar brukeren endre datatyper, intervall og DATEX-pålogging i ettertid."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._entry.data, **self._entry.options}
        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_DATA_TYPES,
                default=current.get(CONF_DATA_TYPES, ALL_DATA_TYPES),
            ): cv_multi_select(_data_type_selector()),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=current.get(
                    CONF_SCAN_INTERVAL,
                    int(DEFAULT_SCAN_INTERVAL.total_seconds()),
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            vol.Optional(
                CONF_DATEX_USERNAME,
                default=current.get(CONF_DATEX_USERNAME, ""),
            ): str,
            vol.Optional(
                CONF_DATEX_PASSWORD,
                default=current.get(CONF_DATEX_PASSWORD, ""),
            ): str,
        }

        # Veivalg for fylke-områder med DATEX: hent en fersk liste over veier
        # som har data nå, slik at brukeren kan snevre inn (tom = alle veier).
        road_options = await self._build_road_options(current)
        if road_options is not None:
            schema_dict[
                vol.Optional(
                    CONF_ROADS, default=current.get(CONF_ROADS, [])
                )
            ] = cv_multi_select(road_options)

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema_dict)
        )

    async def _build_road_options(self, current: dict) -> dict | None:
        """Bygg veivalg-opsjoner for fylke-områder, ellers None.

        Returnerer None når veivalg ikke er aktuelt (ikke fylke, eller ingen
        DATEX-pålogging). Ved feil under henting vises iallfall de allerede
        valgte veiene, slik at man kan fjerne dem.
        """
        if (
            current.get(CONF_AREA_TYPE) != AREA_TYPE_COUNTY
            or not current.get(CONF_DATEX_USERNAME)
            or not current.get(CONF_DATEX_PASSWORD)
        ):
            return None

        session = async_get_clientsession(self.hass)
        client = DatexClient(
            session,
            current[CONF_DATEX_USERNAME],
            current[CONF_DATEX_PASSWORD],
        )
        try:
            roads = await client.async_get_county_roads(
                current.get(CONF_COUNTY, "")
            )
        except SvvApiError:
            roads = []

        options = {road: f"{road} ({count})" for road, count in roads}
        # Sørg for at allerede valgte veier alltid er valgbare
        for road in current.get(CONF_ROADS, []) or []:
            options.setdefault(road, road)
        return options or None


# Liten hjelper: HA tilbyr cv.multi_select, men vi importerer trygt her.
def cv_multi_select(options: dict):
    from homeassistant.helpers import config_validation as cv

    return cv.multi_select(options)
