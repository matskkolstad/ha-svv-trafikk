# Slik laster du opp til GitHub

Denne fila er kun en hjelp til deg – du kan slette den etter opplasting.
Repoet er ferdig konfigurert for brukeren **matskkolstad** og repo-navnet
**ha-svv-trafikk**.

## Alternativ A: Via nettleseren (enklest)

1. Opprett et nytt, tomt repo på GitHub: <https://github.com/new>
   - Eier: `matskkolstad`
   - Navn: `ha-svv-trafikk`
   - Sett det til **Public** (HACS krever offentlig repo)
   - **Ikke** kryss av for «Add a README», «.gitignore» eller «license»
     (repoet inneholder disse allerede)
2. På den nye, tomme repo-siden: klikk **uploading an existing file**.
3. Dra inn **alt innholdet** fra denne mappen (ikke selve mappen, men filene og
   undermappene inni). Pass på at skjulte mapper som `.github` blir med.
4. Skriv en commit-melding (f.eks. «Første versjon») og klikk **Commit changes**.

## Alternativ B: Via kommandolinjen (git)

```bash
# Stå i mappen som inneholder custom_components/, README.md osv.
git init
git add .
git commit -m "Første versjon"
git branch -M main
git remote add origin https://github.com/matskkolstad/ha-svv-trafikk.git
git push -u origin main
```

## Etter opplasting: lag en release (viktig for HACS)

HACS installerer helst fra en **release**. Slik lager du en:

1. Gå til repoet → **Releases** → **Create a new release**.
2. **Choose a tag** → skriv `v0.2.0` → **Create new tag**.
3. Tittel: `v0.2.0`. Beskrivelse: kopier gjerne fra `CHANGELOG.md`.
4. Klikk **Publish release**.

Da kjører GitHub Actions automatisk og lager en `svv_traffic.zip` som HACS
bruker ved installasjon. (Workflowen ligger klar i `.github/workflows/`.)

## Anbefalt: sett beskrivelse og emneord (topics)

På repoets forside, klikk tannhjulet ved «About» og legg til:

- **Description:** «Trafikkdata fra Statens vegvesen i Home Assistant»
- **Topics:** `home-assistant`, `hacs`, `lovelace`, `norway`, `traffic`,
  `statens-vegvesen`, `datex`

## Så installerer du i Home Assistant

1. HACS → Integrasjoner → tre prikker → **Egendefinerte depoter**.
2. URL: `https://github.com/matskkolstad/ha-svv-trafikk`, kategori **Integration**.
3. Last ned, start HA på nytt, og legg til integrasjonen.

Lykke til! Husk at veimeldinger m.m. krever DATEX-tilgang – se `README.md`.
Vil du teste først, slå på **demomodus** under oppsettet.
