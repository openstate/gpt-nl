#  Planbureau voor de Leefomgeving data

## Samenvatting

Voor het PBL (Planbureau voor de Leefomgeving) zijn de Rapporten gedownload.


## Wat

- Alle publicaties van het type “Rapport” van pagina [https://www.pbl.nl/publicaties?f%5B0%5D=publication_subtype%3A26](https://www.pbl.nl/publicaties?f%5B0%5D=publication_subtype%3A26)

- Aanname: het rapport op de Rapport pagina zelf is de bovenste link in het blauwe blok rechts.

- Sommige rapportlinks verwijzen niet naar een pdf bestand maar naar een andere externe pagina, ook deze zijn overgeslagen.


## Leveranciers

- PBL


## Periode

- Alle beschikbare rapporten zonder selectie op datum


## Oplevering

Per rapport is een subfolder aangemaakt met als naam het laatste deel van de rapport URL. In de folder staan de volgende bestanden:

- een .pdf bestand met de inhoud van het rapport:

- metadata.txt bestand met daarin de metadata. 


## Metadata

De metadata zijn de volgende gegevens die overgenomen zijn van de webpagina van het rapport, onder de kopjes “Auteurs” en “Kenmerken”, aangevuld met “rapportURL” en “pdfURL”:

- pbl_auteurs: de PBL auteurs van het rapport, gescheiden door een puntkomma

- overige_auteurs: de overige auteurs van het rapport, gescheiden door puntkomma

- titel: titel van het rapport

- subtitel: subtitel van het rapport

- publicatieDatum: publicatiedatum van het rapport

- aantalPaginas: aantal pagina’s in het rapport

- productNummer: PBL identifier

- rapportURL: volledige URL naar het rapport

- pdfURL: volledige URL voor de PDF binnen dit rapport