import requests scrapers
import io
from requests.exceptions import HTTPError
from webdav4.client import Client

filetype_order = [
    'xml',
    'html',
    'odt',
    'ocr', # Simpele XML, deze moet boven PDF, want ocr resultaten zijn ook vaak als PDF beschikbaar, maar deze variant heeft dan de voorkeur
    'kaarten',
    'pdf'
]

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
    def _download_and_upload_file(self, url):
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
            self.client.upload_fileobj(io.BytesIO(file_response.content), f'{self.base_dir}{file}')
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'An error occurred: {err}')


    #def run(start_date, end_date):
    def run(self):
        # List all documents (more than 6,1 million on 2024-12-16) sorted by oldest date
        query_url = 'https://repository.overheid.nl/sru?&query=*%20sortBy%20dt.modified%20/sort.ascending&startRecord={}&maximumRecords=10&httpAccept=application/json'

        next_record_position = '1'

        while next_record_position:
            response = self.session.get(query_url.format(next_record_position))
            response_json = response.json()['searchRetrieveResponse']
            next_record_position = str(response_json.get('nextRecordPosition', ''))
            for record in response_json['records']['record']:
                item_url = record['recordData']['gzd']['enrichedData']['itemUrl']
                # If there is only 1 item, then the SRU API doesn't return a
                # list, so we need to create a list ourselves
                if 'manifestation' in item_url:
                    item_url = [item_url]

                for item in item_url:
                    url = item['$']
                    self._download_and_upload_file(url)

            # Deal with shifting index?
            input('Press enter to continue')
