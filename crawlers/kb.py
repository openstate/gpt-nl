import io
import json
import re
from time import sleep
from datetime import datetime
import logging
from utils.logging import KB_LOG_FILE
import requests

from utils.webdav_utils import WebDAVUtils
from lxml import html, etree

logger = logging.getLogger('kb')

class KB(object):

    def __init__(self, settings):
        self.base_dir = 'GPT-NL OpenStateFoundation (Projectfolder)/kb/'

        self.session = requests.Session()

        self.webdav_utils = WebDAVUtils(settings)

        self.processed_identifiers = self._get_processed_identifiers()

    def _get_processed_identifiers(self):
        try:
            with open(KB_LOG_FILE, 'r') as f:
                lines = f.readlines()
                h = set()
                for line in lines:
                    match = re.search(r"\s+END\s+([^\s]+)\s+", line)
                    if match:
                        h.add(match[1])
                return h
        except Exception as e:
            self._log_message(f"Error getting processed identifiers: {e}")
            return set()

    def _get_next_paginated_results_page(self, next_paginated_results_page):
        page = int(next_paginated_results_page)
        page += 1
        return str(page)

    def _get_next_page(self, page_str):
        page = int(page_str)
        page += 1
        return "{:04d}".format(page)

    def _upload_book(self, book, identifier):
        filename = f"{identifier}.xml"
        self.webdav_utils.create_folder(self.base_dir, filename)
        self.webdav_utils.upload_fileobj(io.BytesIO(etree.tostring(book)), f'{self.base_dir}{filename}', overwrite=True)

    def _upload_metadata(self, metadata_json, identifier):
        filename = f"{identifier}.txt"
        self.webdav_utils.create_folder(self.base_dir, filename)
        self.webdav_utils.upload_fileobj(io.BytesIO(json.dumps(metadata_json).encode('utf-8')), f'{self.base_dir}{filename}', overwrite=True)

    def _get_book(self, identifier):
        page_ocr_url = "http://resolver.kb.nl/resolve?urn={}:{}:ocr"

        # page needs 4 digits so up to 3 leading zeros
        next_page = '0001'
        book = etree.Element("book")

        while next_page:
            print(f"...now retrieving page {next_page}")
            try:
                page_ocr_xml = etree.parse(page_ocr_url.format(identifier, next_page))
                book.append(page_ocr_xml.getroot())

                next_page = self._get_next_page(next_page)
                sleep(1)
            except OSError as e: # last page was retrieved
                next_page = None

        return book

    def _has_been_processed(self, identifier):
        return identifier in self.processed_identifiers

    def _log_message(self, message):
        logger.info(message)
        logging.StreamHandler().flush()

    #def run(start_date, end_date):
    def run(self):
        query_url = "https://www.delpher.nl/nl/pres/results/multi?query=digitizationProject+any+%22dpo%22&page={}&coll=boeken&actions%5B%5D=paginate&actions%5B%5D=resultsCount&actions%5B%5D=breadcrumbs&actions%5B%5D=sortlinks&actions%5B%5D=results&actions%5B%5D=facets&actions%5B%5D=facettoggle"

        next_paginated_results_page = '1'
        while next_paginated_results_page:
            self._log_message(f"Paginated results page: {next_paginated_results_page}")
            response = self.session.get(query_url.format(next_paginated_results_page))
            response_json = response.json()
            results = html.fromstring(response_json['resultsAction'])

            for article_index, article in enumerate(results.xpath("//article"), start=1):
                self._log_message(f"Article index on this page: {article_index}")
                identifier = article.xpath("@data-identifier")[0]
                if self._has_been_processed(identifier):
                    continue

                # Retrieving metadata via "http://resolver.kb.nl/resolve?urn={}:xml" does not seem
                # to work so we use the data-metadata attribute
                metadata = article.xpath("@data-metadata")[0]
                metadata_json = json.loads(str(metadata))

                self._log_message(f"START {identifier} {datetime.now()}")

                book = self._get_book(identifier)
                metadata_json["numberOfPages"] = len(book.getchildren())
                self._upload_book(book, identifier)
                self._upload_metadata(metadata_json, identifier)

                self._log_message(f"END   {identifier} {datetime.now()}")

            next_paginated_results_page = self._get_next_paginated_results_page(next_paginated_results_page)
