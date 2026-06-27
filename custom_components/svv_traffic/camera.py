"""Camera-entiteter for SVV-webkameraer.

Hvert webkamera i området blir en kamera-entitet som henter siste stillbilde
fra SVV. Bildene oppdateres ved å hente URL-en på nytt.
"""

from __future__ import annotations

import logging

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION, DATA_WEBCAM, DOMAIN
from .coordinator import SvvDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SvvDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if DATA_WEBCAM not in coordinator.enabled_types:
        return

    known: set[str] = set()

    def _sync_cameras() -> None:
        new_entities = []
        for cam in coordinator.data.webcams:
            if cam.id in known:
                continue
            known.add(cam.id)
            new_entities.append(SvvCamera(hass, coordinator, entry, cam.id))
        if new_entities:
            async_add_entities(new_entities)

    _sync_cameras()
    # Oppdag nye kameraer ved senere oppdateringer
    entry.async_on_unload(coordinator.async_add_listener(_sync_cameras))


class SvvCamera(Camera):
    """Et enkelt SVV-webkamera (stillbilde)."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: SvvDataUpdateCoordinator,
        entry: ConfigEntry,
        cam_id: str,
    ) -> None:
        super().__init__()
        self.hass = hass
        self._coordinator = coordinator
        self._cam_id = cam_id
        self._attr_unique_id = f"{entry.entry_id}_cam_{cam_id}"
        self._session = async_get_clientsession(hass)
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    def _current(self):
        for cam in self._coordinator.data.webcams:
            if cam.id == self._cam_id:
                return cam
        return None

    @property
    def name(self) -> str | None:
        cam = self._current()
        return cam.name if cam else self._cam_id

    @property
    def available(self) -> bool:
        cam = self._current()
        return cam is not None and bool(cam.image_url)

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        cam = self._current()
        if not cam or not cam.image_url:
            return None
        try:
            async with self._session.get(cam.image_url) as resp:
                if resp.status == 200:
                    return await resp.read()
                _LOGGER.debug(
                    "Webkamera %s svarte med status %s", self._cam_id, resp.status
                )
        except Exception as err:  # noqa: BLE001 - robust mot kamerafeil
            _LOGGER.debug("Klarte ikke hente kamerabilde %s: %s", self._cam_id, err)
        return None
