import io
import json
import re
from time import sleep
from datetime import datetime
import logging
from utils.logging import KB_LOG_FILE
import requests
import httpx
from webdav4.client import HTTPError

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

    def _get_next_paginated_results(self, url, attempt = 1):
        exception = None
        try:
            response = self.session.get(url)
            response_json = response.json()
            results = html.fromstring(response_json['resultsAction'])
            return results.xpath("//article")
        except httpx.ConnectError as e:
            self._log_message(f"ConnectError when getting paginated results attempt {attempt}: {e}")
            exception = e
        except httpx.ReadTimeout as e:
            self._log_message(f"ReadTimeout when getting paginated results  attempt {attempt}: {e}")
            exception = e
        except requests.exceptions.JSONDecodeError as e:
            self._log_message(f"JSONDecodeError when getting paginated results  attempt {attempt}: {e}")
            exception = e
        except Exception as e:
            self._log_message(f"Unknown exception when getting paginated results  attempt {attempt}: {e.__class__.__name__}, {e}")
            raise

        if exception:
            attempt += 1
            sleepTime = self._get_sleep_time(attempt)
            if sleepTime:
                sleep(sleepTime)
                self._get_next_paginated_results(url, attempt)
            else:
                raise exception

    def _get_next_page(self, page_str):
        page = int(page_str)
        page += 1
        return "{:04d}".format(page)

    def _upload_book(self, book, identifier):
        filename = f"{identifier}.xml"
        self._upload_webdav("book", filename, io.BytesIO(etree.tostring(book)))

    def _upload_metadata(self, metadata_json, identifier):
        filename = f"{identifier}.txt"
        self._upload_webdav("metadata", filename, io.BytesIO(json.dumps(metadata_json).encode('utf-8')))

    def _upload_webdav(self, fileType, filename, bytesIO, attempt = 1):
        exception = None
        try:
            self.webdav_utils.create_folder(self.base_dir, filename)
            self.webdav_utils.upload_fileobj(bytesIO, f'{self.base_dir}{filename}', overwrite=True)
        except httpx.ConnectError as e:
            self._log_message(f"ConnectError when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except httpx.ReadTimeout as e:
            self._log_message(f"ReadTimeout when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except HTTPError as e:
            self._log_message(f"HTTPError when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except Exception as e:
            self._log_message(f"Unknown exception when uploading {fileType} attempt {attempt}: {e.__class__.__name__}, {e}")
            raise

        if exception:
            attempt += 1
            sleepTime = self._get_sleep_time(attempt)
            if sleepTime:
                sleep(sleepTime)
                self._upload_webdav(fileType, filename, bytesIO, attempt)
            else:
                raise exception

    def _get_sleep_time(self, attempt):
        if attempt > 9:
            return None
        return 2**attempt

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
                sleep(0.5)
            except etree.XMLSyntaxError as e:
                logger.info(f"XMLSyntaxError for page {next_page}")
                next_page = self._get_next_page(next_page)
                sleep(0.5)
            except OSError as e: # last page was retrieved
                self._log_message(f"OSError - probably last page was retreived: {e}")
                next_page = None

        return book

    def _has_been_processed(self, identifier):
        return identifier in self.processed_identifiers

    def _log_message(self, message):
        logger.info(message)
        logging.StreamHandler().flush()
        print(message)

    def run(self, start_page):
        query_url = "https://www.delpher.nl/nl/pres/results/multi?query=digitizationProject+any+%22dpo%22&page={}&coll=boeken&actions%5B%5D=results"

        next_paginated_results_page = start_page
        while next_paginated_results_page:
            self._log_message(f"Paginated results page: {next_paginated_results_page}")
            articles = self._get_next_paginated_results(query_url.format(next_paginated_results_page))

            for article_index, article in enumerate(articles, start=1):
                self._log_message(f"Article index on this page: {article_index}")
                identifier = article.xpath("@data-identifier")[0]
                if self._has_been_processed(identifier):
                    continue

                # Retrieving metadata via "http://resolver.kb.nl/resolve?urn={}:xml" does not seem
                # to work so we use the data-metadata attribute
                metadata = article.xpath("@data-metadata")[0]
                metadata_json = json.loads(str(metadata))

                self._log_message(f"START {identifier} {datetime.now().replace(microsecond=0).isoformat()}")

                book = self._get_book(identifier)
                number_of_pages = len(book.getchildren())
                metadata_json["numberOfPages"] = number_of_pages
                self._upload_book(book, identifier)
                self._upload_metadata(metadata_json, identifier)

                self._log_message(f"END   {identifier} {datetime.now().replace(microsecond=0).isoformat()} {number_of_pages}pages")

            if len(articles) == 0:
                logger.info(f"Length of articles is 0 for page {next_paginated_results_page}, end of books reached")
                next_paginated_results_page = None
            else:
                next_paginated_results_page = self._get_next_paginated_results_page(next_paginated_results_page)
