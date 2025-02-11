#  Naturalis

## Samenvatting

Voor Naturalis gaat het om alle artikelen van https://repository.naturalis.nl/.


## Wat

- Alle artikelen worden via de OAI links opgehaald met als entrypoint https://repository.naturalis.nl/oai/?verb=ListIdentifiers&metadataPrefix=nl_didl

- Deze `ListIdentifiers` aanroep geeft een `resumptionToken` terug waarmee de volgende pagina opgehaald kan worden via https://repository.naturalis.nl/oai/?verb=ListIdentifiers&resumptionToken=<resumptionToken> enz.

- Elk artikel heeft een `identifier` en wordt opgehaald via https://repository.naturalis.nl/oai/?verb=GetRecord&metadataPrefix=nl_didl&identifier=<identifier>

- Soms is er geen tijdschrift informatie beschikbaar in de `nl_didl` beschrijving voor de referentie. In dit soort gevallen wordt het artikel nogmaals opgehaald in de `oai_dc` beschrijving (`metadataPrefix=oai_dc`) die dan vaak wel de gezochte informatie bevat.


## Leveranciers

- Naturalis


## Periode

- Alle beschikbare artikelen vanaf 1848 tm 2025 zonder selectie op datum


## Oplevering

Per artikel is een subdirectory aangemaakt met als naam de `identifier`. In de folder staan de volgende bestanden:

- een .pdf bestand met de inhoud van het artikel

- metadata.txt bestand met daarin de metadata. 


## Metadata

De metadata zijn de volgende gegevens die overgenomen zijn uit de `nl_didl` (en soms van de `oai_dc`) beschrijvingen van het artikel:

- identifier: het ID zoals gebruikt door Naturalis
- didlIdentifier: het DIDL ID
- OAIUrl: de URL waarmee de `nl_didl` beschrijving van het artikel is opgehaald
- pdfUrl: de URL van de PDF versie van het artikel
- titel: titel van het artikel
- auteurs: auteurs van het artikel
- journal: tijdschrift waarin het artikel is verschenen
- rechten: de rechten die op het hergebruik van het artikel van toepassing zijn
- jaartal: jaar van verschijning van het artikel
- bestandsGrootte: grootte van de PDF in bytes
- bestandsType: application/pdf
- citation: de volledige referentie van het artikel in APA style
- keywords: de topics die aan het artikel zijn toegekend
- abstract: samenvatting van het artikel
