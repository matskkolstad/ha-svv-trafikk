# Endringslogg

Alle vesentlige endringer i dette prosjektet dokumenteres her.
Formatet følger [Keep a Changelog](https://keepachangelog.com/),
og prosjektet bruker [semantisk versjonering](https://semver.org/lang/no/).

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
