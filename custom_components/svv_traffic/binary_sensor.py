"""Binary sensor-entiteter for SVV Trafikk.

Gir enkle på/av-tilstander som er praktiske i automasjoner:
- Stengt vei/tunnel i området (problem-klasse)
- Aktive veimeldinger i området
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import SvvDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SvvDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SvvRoadClosedBinarySensor(coordinator, entry),
            SvvIncidentsBinarySensor(coordinator, entry),
        ]
    )


class _BaseBinary(CoordinatorEntity[SvvDataUpdateCoordinator], BinarySensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }


class SvvRoadClosedBinarySensor(_BaseBinary):
    _attr_translation_key = "road_closed"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "road_closed")
        self._attr_icon = "mdi:boom-gate-alert"

    @property
    def is_on(self) -> bool:
        return len(self.coordinator.data.closures) > 0

    @property
    def extra_state_attributes(self) -> dict:
        return {"closures": [c.as_dict() for c in self.coordinator.data.closures]}


class SvvIncidentsBinarySensor(_BaseBinary):
    _attr_translation_key = "has_incidents"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "has_incidents")
        self._attr_icon = "mdi:alert"

    @property
    def is_on(self) -> bool:
        return len(self.coordinator.data.incidents) > 0
