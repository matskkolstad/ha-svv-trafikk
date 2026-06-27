"""SVV Trafikk – integrasjon for Home Assistant.

Henter trafikkdata fra Statens vegvesen (DATEX II og det åpne Trafikkdata-
API-et) og eksponerer dem som entiteter, services og events.
"""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_GET_INCIDENTS,
    SERVICE_REFRESH,
)
from .coordinator import SvvDataUpdateCoordinator
from .frontend import FrontendRegistration

_LOGGER = logging.getLogger(__name__)

# Holder versjonen for cache-busting av kort-ressursen
_INTEGRATION_VERSION = "0.2.0"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sett opp en konfigurert oppføring (ett område)."""
    # Registrer kort-ressursen (idempotent – trygt å kalle flere ganger)
    registration = FrontendRegistration(hass, _INTEGRATION_VERSION)
    await registration.async_register()

    coordinator = SvvDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Avregistrer en oppføring."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            _unregister_services(hass)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Last oppføringen på nytt når opsjoner endres."""
    await hass.config_entries.async_reload(entry.entry_id)


def _register_services(hass: HomeAssistant) -> None:
    """Registrer services (kun én gang)."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        return

    async def _handle_refresh(call: ServiceCall) -> None:
        """Tving en oppdatering av alle (eller ett angitt) områder."""
        target = call.data.get("entry_id")
        for entry_id, coord in hass.data.get(DOMAIN, {}).items():
            if target and entry_id != target:
                continue
            await coord.async_request_refresh()

    async def _handle_get_incidents(call: ServiceCall) -> ServiceResponse:
        """Returner gjeldende hendelser/stengninger (for automasjoner/scripts)."""
        result: dict = {"areas": []}
        for coord in hass.data.get(DOMAIN, {}).values():
            data = coord.data
            if data is None:
                continue
            result["areas"].append(
                {
                    "area_name": data.area_name,
                    "overall_status": data.overall_status,
                    "incidents": [i.as_dict() for i in data.incidents],
                    "closures": [c.as_dict() for c in data.closures],
                }
            )
        return result

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        _handle_refresh,
        schema=vol.Schema({vol.Optional("entry_id"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_INCIDENTS,
        _handle_get_incidents,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.ONLY,
    )


def _unregister_services(hass: HomeAssistant) -> None:
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
    hass.services.async_remove(DOMAIN, SERVICE_GET_INCIDENTS)
