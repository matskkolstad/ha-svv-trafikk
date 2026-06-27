"""Sensor-entiteter for SVV Trafikk.

Lager én hovedsensor for samlet områdestatus, samt tellere og målepunkter
avhengig av hvilke datatyper som er aktivert.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    DATA_TRAFFIC_VOLUME,
    DATA_TRAVEL_TIME,
    DOMAIN,
)
from .coordinator import SvvDataUpdateCoordinator

STATUS_ICON = {
    "ok": "mdi:check-circle",
    "warning": "mdi:alert",
    "alert": "mdi:alert-octagon",
    "unknown": "mdi:help-circle",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SvvDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        SvvStatusSensor(coordinator, entry),
        SvvIncidentCountSensor(coordinator, entry),
        SvvClosureCountSensor(coordinator, entry),
    ]
    if DATA_TRAFFIC_VOLUME in coordinator.enabled_types:
        entities.append(SvvTrafficVolumeSensor(coordinator, entry))
    if DATA_TRAVEL_TIME in coordinator.enabled_types:
        entities.append(SvvMaxDelaySensor(coordinator, entry))
    async_add_entities(entities)


class _BaseSvvSensor(CoordinatorEntity[SvvDataUpdateCoordinator], SensorEntity):
    """Felles grunnklasse for SVV-sensorer."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SvvDataUpdateCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"SVV Trafikk – {coordinator.config.get('area_name', 'Område')}",
            "manufacturer": "Statens vegvesen",
            "model": "DATEX II / Trafikkdata",
            "entry_type": "service",
        }


class SvvStatusSensor(_BaseSvvSensor):
    """Samlet status for området (ok/warning/alert)."""

    _attr_translation_key = "overall_status"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "status")

    @property
    def native_value(self) -> str:
        return self.coordinator.data.overall_status

    @property
    def icon(self) -> str:
        return STATUS_ICON.get(self.coordinator.data.overall_status, "mdi:road")

    @property
    def extra_state_attributes(self) -> dict:
        d = self.coordinator.data
        return {
            "area_name": d.area_name,
            "incident_count": len(d.incidents),
            "closure_count": len(d.closures),
            "webcam_count": len(d.webcams),
            "last_updated": d.last_updated.isoformat() if d.last_updated else None,
            "errors": d.errors,
            # Full nyttelast som kortet kan lese direkte:
            "data": d.as_dict(),
        }


class SvvIncidentCountSensor(_BaseSvvSensor):
    _attr_translation_key = "incident_count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "stk"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "incident_count")
        self._attr_icon = "mdi:alert-circle-outline"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.incidents)

    @property
    def extra_state_attributes(self) -> dict:
        return {"incidents": [i.as_dict() for i in self.coordinator.data.incidents]}


class SvvClosureCountSensor(_BaseSvvSensor):
    _attr_translation_key = "closure_count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "stk"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "closure_count")
        self._attr_icon = "mdi:boom-gate"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.closures)

    @property
    def extra_state_attributes(self) -> dict:
        return {"closures": [c.as_dict() for c in self.coordinator.data.closures]}


class SvvTrafficVolumeSensor(_BaseSvvSensor):
    """Sum av passeringer over alle målepunkter i området (siste time)."""

    _attr_translation_key = "traffic_volume"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "kjt/t"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "traffic_volume")
        self._attr_icon = "mdi:car-multiple"

    @property
    def native_value(self) -> int | None:
        vols = [p.volume for p in self.coordinator.data.traffic_volume if p.volume]
        return sum(vols) if vols else None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "points": [p.as_dict() for p in self.coordinator.data.traffic_volume]
        }


class SvvMaxDelaySensor(_BaseSvvSensor):
    """Største forsinkelse (sekunder) blant reisetidsstrekninger i området."""

    _attr_translation_key = "max_delay"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "max_delay")
        self._attr_icon = "mdi:timer-alert-outline"

    @property
    def native_value(self) -> int | None:
        delays = [
            t.delay_seconds
            for t in self.coordinator.data.travel_times
            if t.delay_seconds is not None
        ]
        return max(delays) if delays else None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "routes": [t.as_dict() for t in self.coordinator.data.travel_times]
        }
