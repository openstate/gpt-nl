# ORI data

## Samenvatting

ORI (OpenRaadsInformatie) bevat documenten van Nederlandse Gemeenten, Provincies en Waterschappen.


## Wat

- 304 Gemeenten

- 7 Provincies

- 4 Waterschappen
- 

## Leveranciers

- Ibabs ([https://www.ibabs.com/](https://www.ibabs.com/)): gemeenten, provincies, waterschappen

- Notubiz ([https://www.notubiz.nl/](https://www.notubiz.nl/)): gemeenten, provincies, waterschappen

- Parlaeus, sinds 01-01-2025 Qualigraf ([https://qualigraf.com/nl/homepage-nl/](https://qualigraf.com/nl/homepage-nl/)): gemeenten

- Gemeenteoplossingen ([https://www.gemeenteoplossingen.nl/](https://www.gemeenteoplossingen.nl/)): gemeenten


## Periode

Documenten van 01-01-2010 tm TBD


## Oplevering

Per PDF bestand worden de volgende bestanden geleverd:


- PDF bestand zelf

- .md bestand met daarin de tekst van de PDF. Indien “ocr_used” (zie beneden) gelijk is aan “”, dan bevat dit bestand tekst met markdown formattering. Indien “ocr_used” een waarde heeft, dan bevat dit bestand tekst zonder markdown formattering.

- .metadata bestand met daarin de meta data

De .md en .metadata bestanden hebben dezelfde naam als het PDF bestand, waarbij de .pdf extensie vervangen is.


## Metadata

- key: identificatie van instantie, bv “amsterdam”

- key_type: type instantie, één van [“municipality”, “province”, “waterschap”]

- key_name: naam van instantie, bv “Amsterdam”

- supplier: bron, één van [“ibabs”, “notubiz”, “parlaeus”, “gemeenteoplossingen”]

- content_type: “application/pdf”

- size: grootte van het bestand in bytes

- filename: de oorspronkelijke naam van het bestand

- last_changed_at: de datum voor het bestand in ISO formaat, bv “2024-03-19T10:13:30+01:00”

- original_url: de URL waarmee het bestand bij de leverancier is opgehaald

- ocr_used:
    - als de PDF al een tekstlaag bevatte dan is die gebruikt voor het .md bestand en zal ocr_used de waarde “” hebben
    - als de PDF geen tekstlaag bevatte hebben wij OCR toegepast en het resultaat gebruikt voor het .md bestand. De gebruikte OCR engine (en versie) wordt in ocr_used opgeslagen.