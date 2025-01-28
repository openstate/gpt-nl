import json
import logging
import requests
import io
from collections import defaultdict
from requests.exceptions import HTTPError
from requests.adapters import Retry
from requests_ratelimiter import LimiterAdapter
from pathlib import Path

from utils.webdav_utils import WebDAVUtils

logger = logging.getLogger('obk')

#filetype_order = [
#    ['xml', 'xml-nl', 'xml-en'], # xml-nl en xml-en komen enkel voor bij verdragen ('vd') en we willen beide downloaden
#    ['html'],
#    ['odt'],
#    ['ocr'], # Simpele XML, deze moet boven PDF, want ocr resultaten zijn ook vaak als PDF beschikbaar, maar deze variant heeft dan de voorkeur
#    ['kaarten'], # XML met beschrijving van een jpg kaart
#    ['pdf']
#]

class Officiele_Bekendmakingen(object):
    # 'webdav' or 'local'
    save_location = 'local'

    maximum_records = '100'

    filetypes = {
        'datacollecties': {
            'download_order': [],
            'do_not_download': [
                'gml',
                'html',
                'metadata',
                'metadataowms',
                'pdf',
                'xml'
            ]
        },
        'officielepublicaties': {
            'download_order': [
                ['html'],
                ['odt'],
                ['pdf'],
                ['xml'] # Deze xml bevat schijnbaar nooit noemenswaardige geen teksten (soms enkel 'sluiting')
            ],
            'do_not_download': [
                'metadata',
                'metadataowms'
            ]
        },
        'lokalebekendmakingen': {
            'download_order': [
                ['html'],
                ['metadata']
            ],
            'do_not_download': []
        },
        'samenwerkendecatalogi': {
            'download_order': [
                ['metadata']
            ],
            'do_not_download': []
        },
        'sgd': {
            'download_order': [
                ['ocr', 'kaarten'],
                ['pdf']
            ],
            'do_not_download': [
                'coordinaten',
                'jpg',
                'metadata'
            ]
        },
        'tuchtrecht': {
            'download_order': [
                ['xml'],
                ['pdf']
            ],
            'do_not_download': []
        },
        'vd': {
            'download_order': [
                ['xml-nl', 'xml-en'],
                ['pdf']
            ],
            'do_not_download': [
                'pdf' # Er zit sporadisch aan PDF bij, maar bij steekproeven leken deze niet te bestaan.
            ]
        }
    }

    def __init__(self, settings):
        self.base_dir = ''
        if self.save_location == 'webdav':
            self.base_dir = 'GPT-NL OpenStateFoundation (Projectfolder)/officiele_bekendmakingen/'
        elif self.save_location == 'local':
            self.base_dir = './downloaded_files/officiele_bekendmakingen/'

        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        adapter = LimiterAdapter(per_minute=40, burst=1, max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        self.webdav_utils = WebDAVUtils(settings)

    # Download file from Officiële Bekendmakingen and upload it to Research
    # Drive
    def _download_and_upload_file(self, url, record, first_saved_item):
        logger.debug(f'Downloading {url}')

        file = ''
        if url.startswith('https://repository.overheid.nl/frbr/'):
            file = url[36:]
        else:
            logger.error("Not saving file, because URL doesn't start with https://repository.overheid.nl/frbr/")
            return

        try:
            file_response = self.session.get(url)
            file_response.raise_for_status()

            if self.save_location == 'webdav':
                self.webdav_utils.create_folder(self.base_dir, file)
                # If this is the first item of this record to be saved, then also
                # save the record metadata
                if first_saved_item:
                    self.webdav_utils.upload_fileobj(io.BytesIO(json.dumps(record).encode('utf-8')), f'{self.base_dir}{"/".join(file.split("/")[:-2])}/record.json')
                self.webdav_utils.upload_fileobj(io.BytesIO(file_response.content), f'{self.base_dir}{file}')
            elif self.save_location == 'local':
                Path(self.base_dir + '/'.join(file.split('/')[:-1])).mkdir(parents=True, exist_ok=True)
                if first_saved_item:
                    with open(f'{self.base_dir}{"/".join(file.split("/")[:-2])}/record.json', 'w') as OUT:
                        OUT.write(json.dumps(record))
                with open(f'{self.base_dir}{file}', 'wb') as OUT:
                    OUT.write(file_response.content)

        except HTTPError as http_err:
            logger.error(f'HTTP error occurred during file download: {http_err}')
        except Exception as err:
            logger.error(f'An error occurred during file download: {err}')



    def run(self, start_record, end_record):
        # List all documents (more than 6,1 million on 2024-12-16) sorted by oldest date
        query_url = 'https://repository.overheid.nl/sru?&query=*%20sortBy%20dt.modified%20/sort.ascending&startRecord={}&maximumRecords={}&httpAccept=application/json'

        next_record_position = '1'
        if start_record:
            next_record_position = start_record

        while next_record_position:
            logger.info(f'Start Record: {next_record_position}')

            try:
                response = self.session.get(query_url.format(next_record_position, self.maximum_records))
                response.raise_for_status()
                response_json = response.json()['searchRetrieveResponse']
                next_record_position = str(response_json.get('nextRecordPosition', ''))
            except Exception as e:
                logger.error(f'An error occurred during SRU query: {e}')
                # It seems that some SRU queries return status 200 but empty,
                # so try the next batch
                next_record_position = str(int(next_record_position) + int(self.maximum_records))

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

                collection = {}
                try:
                    collection = self.filetypes[record['recordData']['gzd']['originalData']['meta']['tpmeta']['product-area']]
                except Exception as e:
                    logger.info(f'Ran into unknown collection: {e}')

                found_filetype = False
                for filetypes_to_download in collection['download_order']:
                    for filetype_to_download in filetypes_to_download:
                        if filetype_to_download in available_filetypes:
                            found_filetype = True
                            for url in available_filetypes[filetype_to_download]:
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

                    for filetypes_to_download in collection['download_order']:
                        if available_filetype in filetypes_to_download:
                            known_filetype = True

                    if available_filetype in collection['do_not_download']:
                        known_filetype = True

                    if not known_filetype:
                        logger.info(f'Unknown filetype for record "{record["recordData"]["gzd"]["originalData"]["meta"]["owmskern"]["identifier"]}": {available_filetype}')

            if end_record and int(end_record) < int(next_record_position):
                logger.info(f'Stopped! Reached end_record {end_record} (next_record_position {next_record_position})')
                break
