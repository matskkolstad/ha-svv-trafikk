# SVV Trafikk for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/matskkolstad/ha-svv-trafikk?style=for-the-badge)](https://github.com/matskkolstad/ha-svv-trafikk/releases)
[![Lisens: MIT](https://img.shields.io/badge/Lisens-MIT-blue.svg?style=for-the-badge)](LICENSE)

En tilpassbar integrasjon og et Lovelace-kort som henter trafikkdata fra
**Statens vegvesen** og viser dem i Home Assistant. Følg med på veimeldinger,
stengte veier og tunneler, trafikkmengde, reisetid, webkamera og kjøreforhold –
for ett eller flere geografiske områder.

> Inneholder data under norsk lisens for offentlige data (NLOD), tilgjengeliggjort
> av Statens vegvesen.

[![Åpne i HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=matskkolstad&repository=ha-svv-trafikk&category=integration)

---

## Innhold

- [Funksjoner](#funksjoner)
- [Datakilder og tilgang](#datakilder-og-tilgang)
- [Installasjon via HACS](#installasjon-via-hacs)
- [Oppsett](#oppsett)
- [Kortet](#kortet)
- [Entiteter](#entiteter)
- [Automasjoner: events og services](#automasjoner-events-og-services)
- [Feilsøking](#feilsøking)
- [Veikart](#veikart)

---

## Funksjoner

| Funksjon | Beskrivelse | Krever DATEX-pålogging |
|---|---|---|
| Veimeldinger | Veiarbeid, ulykker, hendelser | Ja |
| Stengte veier/tunneler | Aktive stengninger i området | Ja |
| Trafikkmengde | Antall passeringer per time fra registreringspunkter | **Nei** |
| Reisetid / kø | Målt reisetid og forsinkelsestrend | Ja |
| Webkamera | Stillbilder fra veikameraer | Ja |
| Kjøreforhold | Vær- og veibanedata | Ja |

Områder kan defineres på tre måter, og kombineres ved å sette opp flere oppføringer:

- **Fylke** – f.eks. «Agder»
- **Veinummer** – f.eks. «E18» eller «Rv9»
- **Radius** – koordinat + antall km (standard er Home Assistant sin egen posisjon)

## Datakilder og tilgang

Integrasjonen bruker to API-er fra Statens vegvesen:

1. **Trafikkdata-API (GraphQL)** – åpent, krever ingen pålogging. Gir trafikkmengde
   (passeringer). Fungerer rett ut av boksen.
2. **DATEX II 3.1** – krever en gratis brukerkonto fra SVV (brukernavn/passord).
   Gir veimeldinger, stengninger, webkamera, reisetid og vær.

### Slik får du DATEX-tilgang

1. Søk om tilgang via skjemaet hos SVV:
   <https://www.vegvesen.no/fag/teknologi/apne-data/et-utvalg-apne-data/hva-er-datex/bestille-tilgang-til-datex/>
2. Du må oppgi en **fast IP-adresse eller DNS-navn** som tjenesten skal nås fra.
   For hjemmebruk er dette den offentlige IP-en til internettlinjen din.
3. Når du har fått brukernavn og passord, legger du dem inn under oppsettet (eller
   senere via **Innstillinger**).

> **Glemt passord eller endret IP?** Det finnes ingen selvbetjent gjenoppretting.
> Kontakt SVV på **DATEX@vegvesen.no** og oppgi organisasjonen/brukernavnet ditt.
> Husk å oppdatere registrert IP-adresse hvis hjemme-IP-en din har endret seg.

**Vil du teste uten pålogging?** Slå på **Demomodus** under oppsettet for å se
kortet med syntetiske eksempeldata.

## Installasjon via HACS

1. Åpne **HACS → Integrasjoner**.
2. Velg menyen oppe til høyre → **Egendefinerte depoter (Custom repositories)**.
3. Lim inn `https://github.com/matskkolstad/ha-svv-trafikk` og velg kategori
   **Integration**.
4. Søk opp **SVV Trafikk**, last ned, og **start Home Assistant på nytt**.
5. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon** og søk
   opp **SVV Trafikk**.

Lovelace-kortet følger med og registreres automatisk – du trenger normalt ikke
legge til noen ressurs manuelt. (Hvis du kjører Lovelace i YAML-modus, se
[Feilsøking](#feilsøking).)

### Manuell installasjon (uten HACS)

Kopier mappen `custom_components/svv_traffic` til `config/custom_components/` i
Home Assistant-installasjonen din, og start på nytt.

## Oppsett

Oppsettveiviseren har inntil tre trinn:

1. **Navn, områdetype og datatyper.** Velg hva området heter, hvordan det
   defineres, og hvilke datatyper du vil hente. Kryss av for demomodus om ønskelig.
2. **Områdedetaljer.** Skriv inn fylke, veinummer eller koordinat + radius,
   avhengig av valgt type.
3. **DATEX-pålogging** (kun hvis en valgt datatype krever det). La feltene stå
   tomme for å hoppe over – du kan legge dem til senere.

Du kan sette opp flere områder ved å legge til integrasjonen på nytt.

### Innstillinger i ettertid

Under integrasjonens **Innstillinger** kan du endre aktiverte datatyper,
oppdateringsintervall (60–3600 sekunder) og DATEX-pålogging.

## Kortet

Legg til et kort i dashbordet og velg **SVV Trafikk-kort**. Kortet har en
**visuell editor** – du kan sette opp alt grafisk (velge sensor, layout, kart,
seksjoner og antall rader) uten å skrive YAML. Foretrekker du YAML, støttes
dette fullt ut:

```yaml
type: custom:svv-traffic-card
entity: sensor.svv_trafikk_status      # statussensoren for området
title: Trafikk – Kristiansand          # valgfritt
layout: vertical                       # vertical (standard) eller horizontal
show_map: true                         # vis kart med aktive varsler (standard: false)
map_height: 220                        # karthøyde i piksler (valgfritt)
sections:                              # valgfritt; standard er alle
  - status
  - closures
  - incidents
  - travel_time
  - traffic_volume
  - weather
  - webcams
max_items: 5                           # maks antall rader i lister
show_empty: false                      # vis seksjoner uten data
```

Kortet viser en samlet statusindikator (🟢/🟡/🔴), tellere, lister over
hendelser og stengninger med fargekoding, trafikkmengde som søylediagram,
reisetid med trendpil, og en webkamera-karusell. Aktive varsler gir en dempet
puls-animasjon (respekterer «redusert bevegelse»).

**Layout.** Sett `layout: horizontal` for å fordele seksjonene i et responsivt
rutenett ved siden av hverandre – nyttig på brede dashbord. Standard `vertical`
stabler seksjonene under hverandre.

**Kart.** Med `show_map: true` vises et kart (OpenStreetMap/CARTO, ingen API-nøkkel
nødvendig) som plotter alle datapunkter – veimeldinger, stengninger, webkamera og
trafikkmengde – som fargekodede markører. Klikk på en markør for å se detaljer og
for å **velge punktet**. Med knappen **«Vis kun valgte»** viser kortet kun de valgte
datapunktene. Utvalget huskes per nettleser. Kartrendereren er avhengighetsfri og
lastes kun når kartet er aktivert.

**Område på kart.** Velger du områdetype **radius** i oppsettet, plasserer du et punkt
og radius direkte på et kart – nyttig for «trafikkdata nær meg».

## Entiteter

Per område opprettes blant annet:

| Entitet | Type | Beskrivelse |
|---|---|---|
| `sensor.svv_trafikk_status` | sensor | Samlet status (ok/warning/alert) + full datablokk i attributter |
| `sensor.svv_trafikk_antall_veimeldinger` | sensor | Antall aktive veimeldinger |
| `sensor.svv_trafikk_antall_stengninger` | sensor | Antall stengte veier/tunneler |
| `sensor.svv_trafikk_trafikkmengde` | sensor | Sum passeringer (kjt/t) |
| `sensor.svv_trafikk_storste_forsinkelse` | sensor | Største forsinkelse (s) |
| `binary_sensor.svv_trafikk_stengt_vei_tunnel` | binary_sensor | På når noe er stengt |
| `binary_sensor.svv_trafikk_aktive_veimeldinger` | binary_sensor | På ved aktive meldinger |
| `camera.svv_trafikk_*` | camera | Ett kamera per webkamera i området |

## Automasjoner: events og services

### Events

Integrasjonen sender hendelser du kan utløse automasjoner på (også fra Node-RED):

| Event | Når |
|---|---|
| `svv_traffic_new_incident` | En ny veimelding dukker opp |
| `svv_traffic_road_closed` | En vei/tunnel blir stengt |
| `svv_traffic_road_reopened` | En tidligere stenging er borte |
| `svv_traffic_congestion_warning` | Køvarsel registreres |

Eksempel:

```yaml
automation:
  - alias: Varsle ved stengt vei
    trigger:
      - platform: event
        event_type: svv_traffic_road_closed
    action:
      - service: notify.mobile_app_din_telefon
        data:
          title: "Vei stengt"
          message: "{{ trigger.event.data.title }} ({{ trigger.event.data.road }})"
```

### Services

| Service | Beskrivelse |
|---|---|
| `svv_traffic.refresh` | Tving oppdatering (valgfri `entry_id`) |
| `svv_traffic.get_incidents` | Returnerer gjeldende hendelser/stengninger (`response_variable`) |

```yaml
action:
  - service: svv_traffic.get_incidents
    response_variable: trafikk
  - service: notify.mobile_app_din_telefon
    data:
      message: "{{ trafikk.areas[0].incidents | length }} aktive meldinger."
```

## Feilsøking

- **Kortet vises ikke / «Custom element doesn't exist».** Tøm nettleser-cache
  (Ctrl+F5). Hvis du kjører Lovelace i **YAML-modus**, legg ressursen til manuelt:
  ```yaml
  lovelace:
    resources:
      - url: /svv_traffic_frontend/svv-traffic-card.js
        type: module
  ```
- **DATEX-pålogging avvises (401/403).** Sjekk brukernavn/passord, og at den
  registrerte IP-adressen din stemmer med nåværende offentlige IP.
- **Ingen data i et område.** Reisetid og webkamera dekker hovedsakelig større
  byer og europaveier. Prøv et større område eller en annen områdetype.
- **Tomt på trafikkmengde.** Det åpne API-et henter de nærmeste
  registreringspunktene; juster radius eller veinummer.

## Veikart

- [x] Veimeldinger og stengninger (DATEX)
- [x] Trafikkmengde / passeringer (åpent API)
- [x] Reisetid / kø, webkamera, kjøreforhold (DATEX)
- [x] Events og services for automasjoner
- [x] Tospråklig grensesnitt (nb/en)
- [x] Vertikal og horisontal layout
- [x] Kart med fargekodede varselmarkører
- [x] Visuell kort-editor i UI
- [ ] Historikk/grafer for trafikkmengde
- [ ] Klikkbar rute fra kort til detaljvisning
- [ ] Pendlerstrekning med terskelvarsling

## Lisens

Koden er lisensiert under MIT. Trafikkdataene tilhører Statens vegvesen og brukes
under NLOD – husk å kreditere SVV ved videreformidling.
