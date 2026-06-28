"""Normaliserte datamodeller for SVV Trafikk.

Alle kilder (DATEX XML, Trafikkdata GraphQL, demo) oversettes til disse
klassene. Da slipper resten av integrasjonen – og kortet – å forholde seg
til kildespesifikke formater.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .const import STATUS_OK, STATUS_UNKNOWN


@dataclass(slots=True)
class Incident:
    """En veimelding/hendelse (veiarbeid, ulykke, stengning osv.)."""

    id: str
    title: str
    description: str
    severity: str  # tilordnes STATUS_OK/WARNING/ALERT
    category: str  # f.eks. "roadworks", "accident", "closure", "condition"
    road: str | None = None
    county: str | None = None
    location_description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_closure: bool = False  # True hvis vei/tunnel er stengt

    def as_dict(self) -> dict:
        """Serialiser til en dict som kan brukes i events og attributter."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "road": self.road,
            "county": self.county,
            "location_description": self.location_description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_closure": self.is_closure,
        }


@dataclass(slots=True)
class TrafficVolumePoint:
    """Et trafikkregistreringspunkt med målt volum (antall passeringer)."""

    id: str
    name: str
    volume: int | None = None  # antall passeringer i siste periode
    coverage: float | None = None  # datadekning i prosent (0-100)
    latitude: float | None = None
    longitude: float | None = None
    road: str | None = None
    county: str | None = None
    municipality: str | None = None
    period: str | None = None  # f.eks. "hour", "day"
    measured_at: datetime | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "volume": self.volume,
            "coverage": self.coverage,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "road": self.road,
            "county": self.county,
            "municipality": self.municipality,
            "period": self.period,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
        }


@dataclass(slots=True)
class TravelTime:
    """Reisetid mellom to punkter, med forsinkelses-/kø-trend."""

    id: str
    name: str
    travel_time_seconds: int | None = None
    normal_time_seconds: int | None = None
    delay_seconds: int | None = None
    trend: str | None = None  # "increasing" | "stable" | "decreasing"
    status: str = STATUS_UNKNOWN
    road: str | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "travel_time_seconds": self.travel_time_seconds,
            "normal_time_seconds": self.normal_time_seconds,
            "delay_seconds": self.delay_seconds,
            "trend": self.trend,
            "status": self.status,
            "road": self.road,
        }


@dataclass(slots=True)
class Webcam:
    """Et webkamera fra SVV."""

    id: str
    name: str
    image_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    road: str | None = None
    county: str | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "image_url": self.image_url,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "road": self.road,
            "county": self.county,
        }


@dataclass(slots=True)
class WeatherStation:
    """Værstasjon langs vegen (for kjøreforhold)."""

    id: str
    name: str
    air_temperature: float | None = None
    road_temperature: float | None = None
    wind_speed: float | None = None
    precipitation: str | None = None
    status: str = STATUS_UNKNOWN  # avledet kjøreforhold
    latitude: float | None = None
    longitude: float | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "air_temperature": self.air_temperature,
            "road_temperature": self.road_temperature,
            "wind_speed": self.wind_speed,
            "precipitation": self.precipitation,
            "status": self.status,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


@dataclass(slots=True)
class AreaData:
    """Samlet, normalisert datasett for ett konfigurert område.

    Dette er objektet coordinatoren leverer til alle entiteter og til kortet.
    """

    area_name: str
    overall_status: str = STATUS_OK
    incidents: list[Incident] = field(default_factory=list)
    closures: list[Incident] = field(default_factory=list)
    traffic_volume: list[TrafficVolumePoint] = field(default_factory=list)
    travel_times: list[TravelTime] = field(default_factory=list)
    webcams: list[Webcam] = field(default_factory=list)
    weather: list[WeatherStation] = field(default_factory=list)
    last_updated: datetime | None = None
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "area_name": self.area_name,
            "overall_status": self.overall_status,
            "incidents": [i.as_dict() for i in self.incidents],
            "closures": [c.as_dict() for c in self.closures],
            "traffic_volume": [t.as_dict() for t in self.traffic_volume],
            "travel_times": [t.as_dict() for t in self.travel_times],
            "webcams": [w.as_dict() for w in self.webcams],
            "weather": [w.as_dict() for w in self.weather],
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
            "errors": self.errors,
        }
