"""Klient for SVVs åpne Trafikkdata-API (GraphQL).

Dette API-et krever IKKE pålogging og leverer trafikkmengde (antall
passeringer) fra trafikkregistreringspunkter over hele landet.

Skjema bekreftet mot offisiell dokumentasjon:
  trafficRegistrationPoints(searchQuery: {...}) { id name location {...} }
  trafficData(trafficRegistrationPointId: "...") {
      volume { byHour(from, to) { edges { node {
          from to total { volumeNumbers { volume } coverage { percentage } }
      }}}}
  }
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiohttp import ClientError, ClientSession

from ..const import TRAFIKKDATA_GRAPHQL_URL
from ..models import TrafficVolumePoint
from . import SvvApiError

_LOGGER = logging.getLogger(__name__)

# Henter alle registreringspunkter med koordinater og veireferanse.
_POINTS_QUERY = """
{
  trafficRegistrationPoints {
    id
    name
    location {
      roadReference { shortForm }
      coordinates { latLon { lat lon } }
    }
  }
}
"""

# Henter siste tilgjengelige timevolum for ett punkt.
_VOLUME_QUERY = """
query($id: String!, $from: ZonedDateTime!, $to: ZonedDateTime!) {
  trafficData(trafficRegistrationPointId: $id) {
    volume {
      byHour(from: $from, to: $to) {
        edges {
          node {
            from
            to
            total {
              volumeNumbers { volume }
              coverage { percentage }
            }
          }
        }
      }
    }
  }
}
"""


class TrafikkdataClient:
    """Asynkron klient mot det åpne GraphQL-API-et."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._points_cache: list[dict] | None = None

    async def _post(self, query: str, variables: dict | None = None) -> dict:
        """Kjør en GraphQL-spørring og returner ``data``-feltet."""
        payload: dict = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        try:
            async with self._session.post(
                TRAFIKKDATA_GRAPHQL_URL,
                json=payload,
                headers={"content-type": "application/json"},
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise SvvApiError(
                        f"Trafikkdata svarte med status {resp.status}: {text[:200]}"
                    )
                body = await resp.json()
        except ClientError as err:
            raise SvvApiError(f"Nettverksfeil mot Trafikkdata: {err}") from err

        if "errors" in body and body["errors"]:
            raise SvvApiError(f"GraphQL-feil: {body['errors']}")
        return body.get("data", {})

    async def async_get_points(self, force: bool = False) -> list[dict]:
        """Hent (og cache) listen over alle trafikkregistreringspunkter."""
        if self._points_cache is not None and not force:
            return self._points_cache

        data = await self._post(_POINTS_QUERY)
        points = data.get("trafficRegistrationPoints") or []
        result: list[dict] = []
        for p in points:
            loc = p.get("location") or {}
            coords = (loc.get("coordinates") or {}).get("latLon") or {}
            road_ref = (loc.get("roadReference") or {}).get("shortForm")
            result.append(
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "lat": coords.get("lat"),
                    "lon": coords.get("lon"),
                    "road": road_ref,
                }
            )
        self._points_cache = result
        _LOGGER.debug("Hentet %d trafikkregistreringspunkter", len(result))
        return result

    async def async_get_volume(
        self, point: dict
    ) -> TrafficVolumePoint | None:
        """Hent siste timevolum for ett punkt og returner en normalisert modell."""
        # Vi spør om et vindu på de siste 6 timene og bruker nyeste komplette time.
        now = datetime.now(timezone.utc)
        frm = (now - timedelta(hours=6)).isoformat()
        to = now.isoformat()

        try:
            data = await self._post(
                _VOLUME_QUERY,
                {"id": point["id"], "from": frm, "to": to},
            )
        except SvvApiError as err:
            _LOGGER.debug("Klarte ikke hente volum for %s: %s", point["id"], err)
            return None

        edges = (
            ((data.get("trafficData") or {}).get("volume") or {}).get("byHour")
            or {}
        ).get("edges") or []
        if not edges:
            return TrafficVolumePoint(
                id=point["id"],
                name=point.get("name") or point["id"],
                latitude=point.get("lat"),
                longitude=point.get("lon"),
                road=point.get("road"),
                period="hour",
            )

        node = edges[-1]["node"]  # nyeste time
        total = node.get("total") or {}
        vol = (total.get("volumeNumbers") or {}).get("volume")
        cov = (total.get("coverage") or {}).get("percentage")
        measured_at = None
        if node.get("to"):
            try:
                measured_at = datetime.fromisoformat(node["to"])
            except ValueError:
                measured_at = None

        return TrafficVolumePoint(
            id=point["id"],
            name=point.get("name") or point["id"],
            volume=vol,
            coverage=cov,
            latitude=point.get("lat"),
            longitude=point.get("lon"),
            road=point.get("road"),
            period="hour",
            measured_at=measured_at,
        )
