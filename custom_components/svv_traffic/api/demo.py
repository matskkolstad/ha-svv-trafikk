"""Genererer syntetiske demodata slik at kortet kan testes uten pålogging.

Aktiveres via "demomodus" i oppsettet. Dataene varierer litt over tid for å
vise at oppdatering fungerer.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone

from ..const import STATUS_ALERT, STATUS_OK, STATUS_WARNING
from ..models import (
    AreaData,
    Incident,
    TrafficVolumePoint,
    TravelTime,
    Webcam,
    WeatherStation,
)


def generate_demo_area(area_name: str) -> AreaData:
    """Lag et realistisk, variert datasett for ett område."""
    now = datetime.now(timezone.utc)
    seed = now.minute  # gir variasjon over tid

    incidents = [
        Incident(
            id="demo-rw-1",
            title="Vegarbeid på E18",
            description="Redusert framkommelighet pga. asfaltering. Ett kjørefelt stengt.",
            severity=STATUS_WARNING,
            category="roadworks",
            road="E18",
            county="Agder",
            location_description="E18 ved Bjørndalssletta",
            latitude=58.16,
            longitude=8.02,
            start_time=now,
        ),
        Incident(
            id="demo-acc-1",
            title="Trafikkuhell på Rv9",
            description="Berging pågår. Vis hensyn.",
            severity=STATUS_ALERT,
            category="accident",
            road="Rv9",
            county="Agder",
            location_description="Rv9 Setesdal",
            latitude=58.78,
            longitude=7.80,
            start_time=now,
        ),
    ]

    closures = [
        Incident(
            id="demo-cls-1",
            title="Tunnel stengt",
            description="Hagebåttunnelen er stengt for vedlikehold til kl. 06:00.",
            severity=STATUS_ALERT,
            category="closure",
            road="E39",
            county="Agder",
            location_description="E39 Hagebåttunnelen",
            latitude=58.14,
            longitude=7.99,
            start_time=now,
            is_closure=True,
        )
    ]

    traffic_volume = [
        TrafficVolumePoint(
            id="demo-trp-1",
            name="Varoddbrua",
            volume=1100 + seed * 7,
            coverage=99.0,
            latitude=58.16,
            longitude=8.04,
            road="E18",
            period="hour",
            measured_at=now,
        ),
        TrafficVolumePoint(
            id="demo-trp-2",
            name="Kvadraturen",
            volume=620 + seed * 4,
            coverage=97.5,
            latitude=58.15,
            longitude=7.99,
            road="Fv",
            period="hour",
            measured_at=now,
        ),
    ]

    travel_times = [
        TravelTime(
            id="demo-tt-1",
            name="E18 Vest → Sentrum",
            travel_time_seconds=480 + seed * 6,
            normal_time_seconds=420,
            delay_seconds=60 + seed * 6,
            trend=random.choice(["increasing", "stable", "decreasing"]),
            status=STATUS_WARNING if seed > 20 else STATUS_OK,
            road="E18",
        )
    ]

    webcams = [
        Webcam(
            id="demo-cam-1",
            name="E18 Bjørndalssletta",
            image_url="https://webkamera.atlas.vegvesen.no/public/kamera?id=demo1",
            latitude=58.16,
            longitude=8.02,
            road="E18",
        )
    ]

    weather = [
        WeatherStation(
            id="demo-ws-1",
            name="Kristiansand",
            air_temperature=round(2 + seed * 0.1, 1),
            road_temperature=round(0.5 + seed * 0.05, 1),
            wind_speed=round(3 + seed * 0.1, 1),
            precipitation="rain" if seed % 2 else "none",
            status=STATUS_OK if seed % 2 else STATUS_WARNING,
            latitude=58.15,
            longitude=8.00,
        )
    ]

    # Samlet status = verste enkeltstatus
    overall = STATUS_OK
    if closures or any(i.severity == STATUS_ALERT for i in incidents):
        overall = STATUS_ALERT
    elif any(i.severity == STATUS_WARNING for i in incidents):
        overall = STATUS_WARNING

    return AreaData(
        area_name=area_name,
        overall_status=overall,
        incidents=incidents,
        closures=closures,
        traffic_volume=traffic_volume,
        travel_times=travel_times,
        webcams=webcams,
        weather=weather,
        last_updated=now,
    )
