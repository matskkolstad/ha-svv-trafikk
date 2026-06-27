#!/usr/bin/env python3
"""Diagnoseskript for SVV DATEX – inspiserer FAKTISK XML-struktur.

Formål: verifisere hvilke felt DATEX GetSituation faktisk leverer for sted,
fylke, vegnummer og koordinater, slik at vi ikke gjetter på skjemaet når vi
fikser fylkesfiltreringen.

Bruk:
    1. Fyll inn tools/datex_secrets.env med DATEX_USERNAME og DATEX_PASSWORD.
    2. Kjør:  python tools/datex_inspect.py
       (valgfritt:  python tools/datex_inspect.py --dump-xml 3  for rå XML)

Skriptet bruker kun Python-stdlib (urllib + ElementTree) – ingen avhengigheter.
Det skriver IKKE passordet til skjerm eller fil.
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

DATEX_SITUATION_URL = (
    "https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi"
    "/GetSituation/pullsnapshotdata"
)

# Felt vi er spesielt interessert i for områdefiltrering
GEO_FIELDS_OF_INTEREST = (
    "countyName",
    "county",
    "countyNumber",
    "municipality",
    "municipalityName",
    "areaName",
    "roadNumber",
    "roadName",
    "locationDescription",
    "latitude",
    "longitude",
    "pointCoordinates",
    "gmlLineString",
    "areaOfInterest",
    "namedArea",
)


def _secrets_path() -> Path:
    return Path(__file__).resolve().parent / "datex_secrets.env"


def load_credentials() -> tuple[str, str]:
    """Hent brukernavn/passord fra env-fil eller miljøvariabler."""
    user = os.environ.get("DATEX_USERNAME", "")
    pw = os.environ.get("DATEX_PASSWORD", "")

    path = _secrets_path()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key == "DATEX_USERNAME" and val:
                user = val
            elif key == "DATEX_PASSWORD" and val:
                pw = val

    if not user or not pw:
        sys.exit(
            "Mangler pålogging. Fyll inn DATEX_USERNAME og DATEX_PASSWORD i "
            f"{path}\n(eller sett dem som miljøvariabler)."
        )
    return user, pw


def fetch(url: str, user: str, pw: str) -> bytes:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            print(f"HTTP {resp.status} – hentet {len(data):,} bytes fra DATEX.")
            return data
    except urllib.error.HTTPError as err:
        if err.code in (401, 403):
            sys.exit(
                f"DATEX avviste påloggingen ({err.code}). Sjekk brukernavn/"
                "passord (og evt. registrert IP)."
            )
        sys.exit(f"DATEX svarte med HTTP {err.code}: {err.read()[:300]!r}")
    except urllib.error.URLError as err:
        sys.exit(f"Nettverksfeil mot DATEX: {err}")


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_records(root: ET.Element) -> list[ET.Element]:
    recs = [r for r in root.iter() if localname(r.tag) == "situationRecord"]
    if recs:
        return recs
    # Fall tilbake til 'situation' hvis records ikke finnes
    return [s for s in root.iter() if localname(s.tag) == "situation"]


def first_text(elem: ET.Element, name: str) -> str | None:
    for child in elem.iter():
        if localname(child.tag) == name and child.text and child.text.strip():
            return child.text.strip()
    return None


def describe_record(rec: ET.Element, index: int) -> None:
    rtype = (
        rec.get("{http://www.w3.org/2001/XMLSchema-instance}type") or ""
    ).split(":")[-1]
    print(f"\n--- situationRecord #{index}  (type: {rtype or 'ukjent'}) ---")
    print(f"  id-attributt: {rec.get('id')!r}")
    for field in GEO_FIELDS_OF_INTEREST:
        val = first_text(rec, field)
        if val is not None:
            shown = val if len(val) <= 80 else val[:77] + "..."
            print(f"  {field:22} = {shown!r}")
    # List alle unike descendant-elementnavn for å avsløre ukjente geo-felt
    names = sorted({localname(c.tag) for c in rec.iter()})
    print(f"  alle elementnavn i record: {', '.join(names)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump-xml",
        type=int,
        default=0,
        metavar="N",
        help="Skriv ut rå XML for de N første recordene",
    )
    parser.add_argument(
        "--describe",
        type=int,
        default=5,
        metavar="N",
        help="Beskriv geo-felt for de N første recordene (standard 5)",
    )
    args = parser.parse_args()

    user, pw = load_credentials()
    raw = fetch(DATEX_SITUATION_URL, user, pw)

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as err:
        sys.exit(f"Kunne ikke tolke XML: {err}")

    records = find_records(root)
    print(f"\nFant {len(records)} situationRecord (eller situation) totalt.")

    if not records:
        print("Ingen records funnet – sjekker toppnivå-elementnavn:")
        print("  ", sorted({localname(c.tag) for c in list(root.iter())[:200]}))
        return

    # Frekvensanalyse: hvilke geo-relevante felt finnes, og hvor ofte?
    print("\n=== Feltfrekvens over ALLE records ===")
    field_counts: Counter[str] = Counter()
    county_values: Counter[str] = Counter()
    for rec in records:
        present = {localname(c.tag) for c in rec.iter()}
        for field in GEO_FIELDS_OF_INTEREST:
            if field in present:
                field_counts[field] += 1
        for cfield in ("countyName", "county", "countyNumber"):
            cval = first_text(rec, cfield)
            if cval:
                county_values[f"{cfield}={cval}"] += 1

    total = len(records)
    for field in GEO_FIELDS_OF_INTEREST:
        n = field_counts.get(field, 0)
        flag = "" if n else "   <-- MANGLER HELT"
        print(f"  {field:22} finnes i {n:4}/{total} records{flag}")

    print("\n=== Faktiske fylkesverdier funnet (om noen) ===")
    if county_values:
        for val, n in county_values.most_common(30):
            print(f"  {n:4}x  {val}")
    else:
        print("  INGEN fylkesfelt (countyName/county/countyNumber) funnet i noen "
              "record. Dette bekrefter at fylkesfiltrering på navn ikke kan virke.")

    # Detaljert beskrivelse av de første recordene
    print("\n=== Detaljer for de første recordene ===")
    for i, rec in enumerate(records[: args.describe]):
        describe_record(rec, i)

    if args.dump_xml:
        print("\n=== RÅ XML ===")
        for i, rec in enumerate(records[: args.dump_xml]):
            print(f"\n----- RÅ XML record #{i} -----")
            print(ET.tostring(rec, encoding="unicode"))


if __name__ == "__main__":
    main()
