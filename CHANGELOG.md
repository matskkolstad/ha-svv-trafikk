# Endringslogg

Alle vesentlige endringer i dette prosjektet dokumenteres her.
Formatet følger [Keep a Changelog](https://keepachangelog.com/),
og prosjektet bruker [semantisk versjonering](https://semver.org/lang/no/).

## [0.4.0] – 2026-06-28

### Rettet
- **Trafikkmengde viste feil områder.** Trafikkpunktene ble ikke filtrert på fylke,
  så et fylke-område kunne vise punkter fra hele landet (f.eks. E18 i Oslo/Vestfold
  for et Agder-område). Punktene henter nå fylke/kommune og filtreres korrekt.
- **Veimeldinger var uinformative.** Tittelen viste den engelske record-typen
  («MaintenanceWorks») og «beskrivelsen» viste «NPRA» (kilden). Tittelen er nå et
  lesbart norsk navn (Vegarbeid, Fartsregulering, Ulykke …) når sted mangler, og
  beskrivelsen henter den faktiske meldingsteksten.
- Veinummer fra de to datakildene forenes nå (DATEX «R9» ↔ Trafikkdata «RV9» osv.),
  slik at veivalg fungerer på tvers av kilder.

### Lagt til
- **Kart med nål og radius i oppsettveiviseren** for radius-områder: dropp en nål og
  sett radius direkte på et kart («data nær meg»).
- **Interaktivt datapunkt-kart i kortet.** Kartet viser nå alle datapunkter
  (veimeldinger, stengninger, webkamera og trafikkmengde) som fargekodede markører.
  Klikk en markør for å velge punkter, og bruk «Vis kun valgte» for å vise bare de
  valgte i kortet. Utvalget huskes per nettleser.
- Trafikkmengde-punkter viser nå kommunenavn for lettere gjenkjenning.

## [0.3.0] – 2026-06-28

### Lagt til
- Veivalg for fylke-områder: etter at du har valgt fylke, kan du velge hvilke
  veier du vil hente data for, fra en liste som viser veiene som faktisk har
  veimeldinger i fylket akkurat nå (med antall). La valget stå tomt for å ta
  med alle veier i fylket.
- Listen oppdateres automatisk – både i oppsettet og under Innstillinger henter
  den en fersk oversikt over veier med data.
- Fylke velges nå fra en nedtrekksliste over de 15 norske fylkene i stedet for
  fritekst.

### Endret
- Webkamera filtreres nå korrekt på fylke (leses fra `namedArea`), slik at et
  fylke-område ikke lenger tar med kameraer fra hele landet.
- Veinummer prioriteres over veinavn ved tolking, så samme vei ikke splittes i
  flere oppføringer.

## [0.2.1] – 2026-06-27

### Rettet
- Fylkesfiltrering virket ikke for DATEX-veimeldinger: norske
  situasjonsdata har ikke et `countyName`/`county`-felt, så fylket ble aldri
  funnet og alle hendelser ble filtrert bort. Fylket leses nå korrekt fra
  `namedArea` (subdivisionType=county).
- Fylkesfilteret er nå «fail-open»: hendelser uten fylkesinfo vises i stedet
  for å skjules.

### Lagt til
- Debug-logging i coordinatoren for antall hendelser hentet vs. innenfor
  området, og et diagnoseskript (`tools/datex_inspect.py`) for DATEX-XML.

## [0.2.0] – 2026-06-27

### Lagt til
- Visuell editor for kortet – konfigurer sensor, layout, kart, seksjoner og
  antall rader grafisk uten YAML.
- Valgfri kart-visning som plotter aktive veimeldinger og stengninger som
  fargekodede markører (OpenStreetMap/CARTO, ingen API-nøkkel).
- Vertikal og horisontal layout, valgbart per kort.

### Endret
- Helt nytt, mer minimalistisk kortdesign med rene SVG-ikoner i stedet for
  emojier, lettere typografi og mer luft.
- Kartet bruker en egen, avhengighetsfri renderer i stedet for Leaflet, for
  pålitelig visning inne i kortets shadow DOM.

## [0.1.0] – 2026-06-27

### Lagt til
- Første versjon: integrasjon med veimeldinger, stengninger og trafikkmengde.
- DATEX-støtte for webkamera, reisetid og vær (krever pålogging).
- Demomodus, områdefiltrering (fylke/veinummer/radius), events og services.
- Tospråklig grensesnitt (norsk og engelsk).
