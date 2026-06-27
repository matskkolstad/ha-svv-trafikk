# Bidra til SVV Trafikk

Takk for at du vil bidra! Her er det du trenger å vite.

## Feil og forslag

Bruk [issues](https://github.com/matskkolstad/ha-svv-trafikk/issues) for
feilrapporter og funksjonsønsker. Det finnes ferdige maler som hjelper deg å
gi den informasjonen som trengs.

## Utvikling

Integrasjonen ligger i `custom_components/svv_traffic/`. Kortet (én ren
JavaScript-fil, uten byggesteg) ligger i `custom_components/svv_traffic/frontend/`.

Nyttige sjekker før du sender inn endringer:

```bash
# Python kompilerer
python3 -m py_compile custom_components/svv_traffic/*.py \
  custom_components/svv_traffic/api/*.py \
  custom_components/svv_traffic/frontend/*.py

# Kortet har gyldig syntaks (krever Node)
node --check custom_components/svv_traffic/frontend/svv-traffic-card.js

# JSON er gyldig
python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('custom_components/svv_traffic/**/*.json', recursive=True)]"
```

GitHub Actions kjører i tillegg HACS-validering og `hassfest` automatisk på
hver pull request.

## Stil

- Hold koden lesbar og kommentert på norsk, slik resten av prosjektet er.
- Følg eksisterende mønstre for nye datakilder: legg dem bak datakilde-
  abstraksjonen og normaliser til modellene i `models.py`.

## Lisens

Ved å bidra godtar du at bidraget ditt lisensieres under prosjektets
[MIT-lisens](LICENSE).
