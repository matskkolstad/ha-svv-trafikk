# SVV Trafikk

Vis trafikkdata fra **Statens vegvesen** direkte i Home Assistant: veimeldinger,
stengte veier og tunneler, trafikkmengde, reisetid, webkamera og kjøreforhold –
for ett eller flere områder du selv velger.

## Hva du får

- Integrasjon som henter og normaliserer data fra SVV
- Sensorer, binærsensorer og kamera-entiteter
- Et moderne Lovelace-kort med visuell editor, valgfri kart-visning og
  vertikal/horisontal layout
- Events og services for automasjoner og Node-RED

## Kom i gang

1. Installer via HACS og start Home Assistant på nytt.
2. Legg til integrasjonen under **Innstillinger → Enheter og tjenester**.
3. Velg område (fylke, veinummer eller radius) og hvilke data du vil hente.

Trafikkmengde fungerer uten pålogging. Veimeldinger, webkamera, reisetid og vær
krever gratis DATEX-tilgang fra Statens vegvesen – se README for hvordan du søker.

> Vil du teste først? Slå på **demomodus** i oppsettet for å se kortet med
> eksempeldata, helt uten pålogging.
