import json
import logging
import requests
import io
from collections import defaultdict
from requests.exceptions import HTTPError
from webdav4.client import Client

logging.basicConfig(
    filename="../logs/officiele_bekendmakingen.log",
    filemode='a',
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger()

#filetype_order = [
#    ['xml', 'xml-nl', 'xml-en'], # xml-nl en xml-en komen enkel voor bij verdragen ('vd') en we willen beide downloaden
#    ['html'],
#    ['odt'],
#    ['ocr'], # Simpele XML, deze moet boven PDF, want ocr resultaten zijn ook vaak als PDF beschikbaar, maar deze variant heeft dan de voorkeur
#    ['kaarten'], # XML met beschrijving van een jpg kaart
#    ['pdf']
#]

filetypes = {
    'officielepublicaties': {
        'download_order': [
            ['html',]
            ['odt',]
            ['pdf',]
            ['xml'] # Deze xml bevat schijnbaar nooit noemenswaardige geen teksten (soms enkel 'sluiting')
        ],
        'do_not_download': [
            'metadata',
            'metadataowms'
        ]
    },
    'lokalebekendmakingen': {
        'download_order': [
            'html'
        ],
        'do_not_download': [
            'metadata',
        ]
    },
    '': {
        'download_order': [
            '',
        ],
        'do_not_download': [
            '',
        ]
    },
    '': {
        'download_order': [
            '',
        ],
        'do_not_download': [
            '',
        ]
    },
    '': {
        'download_order': [
            '',
        ],
        'do_not_download': [
            '',
        ]
    },
    '': {
        'download_order': [
            '',
        ],
        'do_not_download': [
            '',
        ]
    },
}

class Officiele_Bekendmakingen(object):
    def __init__(self, settings):
        self.base_dir = 'GPT-NL OpenStateFoundation (Projectfolder)/officiele_bekendmakingen/'

        self.session = requests.Session()

        # Create a WEBDAV connection
        self.client = Client(settings['URL'], auth=(settings['USER'], settings['PASSWORD']))

    # Check if all parent folders exist, if not create them
    def _create_folder(self, file):
        path = self.base_dir
        for folder in file.split('/')[:-1]:
            path += f'{folder}/'
            if not self.client.exists(path):
                self.client.mkdir(path)

    # Download file from Officiële Bekendmakingen and upload it to Research
    # Drive
    def _download_and_upload_file(self, url, record, first_saved__item):
        print(f'Downloading {url}')

        file = ''
        if url.startswith('https://repository.overheid.nl/frbr/'):
            file = url[36:]
        else:
            print("Not saving file, because URL doesn't start with https://repository.overheid.nl/frbr/")
            return

        try:
            file_response = self.session.get(url)
            file_response.raise_for_status()
            self._create_folder(file)
            # If this is the first item of this record to be saved, then also
            # save the record metadata
            if first_saved_item:
                self.client.upload_fileobj(io.BytesIO(json.dumps(record).encode('utf-8')), f'{self.base_dir}{"/".join(file.split("/")[:-2])}/record.json')
            self.client.upload_fileobj(io.BytesIO(file_response.content), f'{self.base_dir}{file}')
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'An error occurred: {err}')



    #def run(start_date, end_date):
    def run(self):
        # List all documents (more than 6,1 million on 2024-12-16) sorted by oldest date
        query_url = 'https://repository.overheid.nl/sru?&query=*%20sortBy%20dt.modified%20/sort.ascending&startRecord={}&maximumRecords=100&httpAccept=application/json'

        next_record_position = '1'

        while next_record_position:
            response = self.session.get(query_url.format(next_record_position))
            response_json = response.json()['searchRetrieveResponse']
            next_record_position = str(response_json.get('nextRecordPosition', ''))

            # If there is only 1 item, then the SRU API doesn't return a
            # list, but a dict, so we need to create a list ourselves
            if type(response_json['records']['record']) == dict:
                response_json['records']['record'] = [response_json['records']['record']]

            for record in response_json['records']['record']:
                item_url = record['recordData']['gzd']['enrichedData']['itemUrl']
                # If there is only 1 item, then the SRU API doesn't return a
                # list, but a dict, so we need to create a list ourselves
                if type(item_url) == dict:
                    item_url = [item_url]

                available_filetypes = defaultdict(list)
                for item in item_url:
                    available_filetypes[item['manifestation']].append(item['$'])

                first_saved_item = True

                try:
                    collection = filetypes[record['recordData']['gzd']['originalData']['meta']['tpmeta']['product-area']]
                except as e:
                    logger.info(f'Ran into unknown collection: {e}')

                found_filetype = False
                for filetypes in collection['download_order']:
                    for filetype in filetypes:
                        if filetype in available_filetypes:
                            found_filetype = True
                            for url in available_filetypes[filetype]:
                                self._download_and_upload_file(url, record, first_saved_item)
                                first_saved_item = False
                    # If one or more filetypes from the current download_order
                    # list was found in available_filetypes, then we can stop
                    if found_filetype:
                        break

                # If we run into an unknown filetype then log it (so we can
                # check if we need to add it)
                for available_filetype in available_filetypes:
                    known_filetype = False

                    for filetypes in collection['download_order']:
                        if available_filetype in filetypes:
                            known_filetype = True

                    if available_filetype in collection['do_not_download']:
                        known_filetype = True

                    if not known_filetype:
                        logger.info(f'Unknown filetype for record "{record["recordData"]["gzd"]["originalData"]["meta"]["owmskern"]["identifier"]}": {available_filetype}')

            # Deal with shifting index?
            input('Press enter to continue')
