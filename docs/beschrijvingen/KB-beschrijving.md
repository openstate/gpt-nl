# Koninklijke Bibliotheek data


## Samenvatting

Voor de KB (Koninklijke Bibliotheek) is een subset van gedigitaliseerde boeken gedownload.


## Wat

- Alle boeken van dit digitizationProject:
[https://www.delpher.nl/nl/boeken/results?query=digitizationProject+any+%22dpo%22&page=1&coll=boeken](https://www.delpher.nl/nl/boeken/results?query=digitizationProject+any+%22dpo%22&page=1&coll=boeken)

- Let op: niet alle boeken zijn in het Nederlands, er zitten bijvoorbeeld een aantal Franstalige boeken tussen. Er was geen metadata beschikbaar om hierin onderscheid te kunnen maken, dus alle boeken zijn geüpload.



## Leveranciers

- Delpher / KB


## Periode


- 17e eeuw (1 boek)

- 18e eeuw (10645 boeken)

- 19e eeuw (594 boeken)


## Oplevering

Per boek worden de volgende bestanden geleverd:

- een .xml bestand met de inhoud van het boek:
    - root element is <book>
    - elke pagina is een <text> element met daarin <p>
elementen 
- .txt bestand met daarin de metadata. 


De .xml en .txt bestanden hebben dezelfde naam als de identifier
op www.delpher.nl.


## Metadata

De metadata is een kopie van het attribute “data-metadata” van de <article> elementen die de boeken op [www.delpher.nl](http://www.delpher.nl/) bevatten, met als toevoeging “numberOfPages”.

- title: titel van het boek

- caption: meestal (altijd?) leeg

- volumeRemark: meestal (altijd?) leeg

- seq: volgnummer indien het een serie boeken betreft

- alternative: meestal (altijd?) identiek aan title

- subtitle: subtitel; meestal (altijd?) jaar van uitgave

- creator: auteur

- ppn: Pica productienummer; meestal (altijd?) leeg

- bookId: id van boek

- objectlevelId: identifier gebruikt op [www.delpher.nl](http://www.delpher.nl/) en voor naamgeving van .xml en .txt bestanden

- numberOfPages: aantal pagina’s in boek