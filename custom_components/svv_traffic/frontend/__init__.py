"""Automatisk registrering av Lovelace-kortet.

Dette gjør at kortet blir tilgjengelig uten at brukeren må legge til en
ressurs manuelt – kortet serveres som en statisk fil og registreres som
Lovelace-ressurs (kun i 'storage'-modus; YAML-modus krever manuell ressurs).
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# URL der kortet serveres fra, og selve JS-filen
URL_BASE = f"/{DOMAIN}_frontend"
CARD_FILENAME = "svv-traffic-card.js"


class FrontendRegistration:
    """Registrerer kort-filen som statisk ressurs og Lovelace-modul."""

    def __init__(self, hass: HomeAssistant, version: str) -> None:
        self.hass = hass
        self.version = version

    async def async_register(self) -> None:
        await self._register_static_path()
        await self._register_resource()

    async def _register_static_path(self) -> None:
        """Eksponer frontend-mappen på en statisk URL."""
        folder = Path(__file__).parent
        try:
            await self.hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        URL_BASE,
                        str(folder),
                        cache_headers=False,
                    )
                ]
            )
            _LOGGER.debug("Registrerte statisk sti %s -> %s", URL_BASE, folder)
        except RuntimeError:
            # Allerede registrert (f.eks. ved reload) – ignorer
            _LOGGER.debug("Statisk sti %s er allerede registrert", URL_BASE)

    async def _register_resource(self) -> None:
        """Legg kortet til Lovelace-ressursene (kun i storage-modus)."""
        lovelace = self.hass.data.get("lovelace")
        if lovelace is None:
            return

        resources = getattr(lovelace, "resources", None)
        mode = getattr(lovelace, "mode", getattr(lovelace, "resource_mode", "yaml"))
        if resources is None or mode != "storage":
            _LOGGER.debug(
                "Lovelace i '%s'-modus – hopper over auto-registrering. "
                "Legg til ressursen manuelt om nødvendig.",
                mode,
            )
            return

        url = f"{URL_BASE}/{CARD_FILENAME}"
        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True

        # Finnes ressursen allerede? Oppdater versjon, ellers opprett.
        existing = [
            r for r in resources.async_items() if r["url"].startswith(url)
        ]
        versioned = f"{url}?v={self.version}"
        if existing:
            for item in existing:
                if item["url"] != versioned:
                    await resources.async_update_item(
                        item["id"], {"url": versioned, "res_type": "module"}
                    )
            return

        await resources.async_create_item(
            {"res_type": "module", "url": versioned}
        )
        _LOGGER.info("Registrerte Lovelace-ressurs: %s", versioned)

    async def async_unregister(self) -> None:
        """Ingen opprydding nødvendig – ressursen kan bli stående."""
        return
