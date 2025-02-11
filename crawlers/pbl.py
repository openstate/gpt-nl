import io
import json
import re
import requests
from requests.exceptions import HTTPError
import httpx
from datetime import datetime
from time import sleep
import logging
from utils.logging import PBL_LOG_FILE
from urllib.request import urlopen
from urllib.parse import urljoin

from utils.webdav_utils import WebDAVUtils
from lxml import html

logger = logging.getLogger('pbl')

class PBL(object):
    def __init__(self, settings):
        self.base_dir = 'GPT-NL OpenStateFoundation (Projectfolder)/pbl/'
        self.base_url = 'https://www.pbl.nl'

        self.session = requests.Session()

        self.webdav_utils = WebDAVUtils(settings)

        self.processed_identifiers = self._get_processed_identifiers()

    def _get_processed_identifiers(self):
        try:
            with open(PBL_LOG_FILE, 'r') as f:
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
        doc = self._get_response(url).getroot()
        links = doc.cssselect('.view-publications-overview__content a.node-publication-teaser__read-more-link')
        report_paths = [link.xpath("@href")[0] for link in links]
        return report_paths

    def _get_sleep_time(self, attempt):
        if attempt > 9:
            return None
        return 2**attempt

    def _get_response(self, url, attempt = 1):
        exception = None
        try:
            return html.parse(urlopen(url))
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
                return self._get_response(url, attempt)
            else:
                raise exception

    def _has_been_processed(self, identifier):
        return identifier in self.processed_identifiers

    def _get_pdf_url_and_metadata(self, report_url):
        doc = self._get_response(report_url).getroot()
        # The pdf we are interested in is contained in the first <li> in <aside>. Note
        # that the text for the link can be anything and cannot be used for selection.
        # Also note that some of these "pdf_url"s point to external webpages, these
        # will be filtered out later on when attempting to download the pdf.
        pdf_element = doc.xpath("//aside/ul/li[1]/a")[0]
        pdf_url = urljoin(self.base_url, pdf_element.xpath("@href")[0])

        metadata = {}
        pbl_authors_items = doc.cssselect('.node-publication-full__authors-item')
        metadata['pbl_auteurs'] = ';'.join([pbl_authors_item.text_content().strip() for pbl_authors_item in pbl_authors_items])

        other_authors_items = doc.cssselect('.node-publication-full__authors-external-item')
        metadata['overige_auteurs'] = ';'.join([other_authors_item.text_content().strip() for other_authors_item in other_authors_items])

        metadata['titel'] = self._get_metadata_item(doc, 'Publicatietitel')
        metadata['subtitel'] = self._get_metadata_item(doc, 'Publicatiesubtitel')
        metadata['publicatieDatum'] = self._get_metadata_item(doc, 'Publicatiedatum')
        metadata['aantalPaginas'] = self._get_metadata_item(doc, 'Aantal pagina')
        metadata['productNummer'] = self._get_metadata_item(doc, 'Productnummer')
        metadata['rapportURL'] = report_url
        metadata[f"pdfURL"] = pdf_url

        return pdf_url, metadata

    def _get_metadata_item(self, doc, label):
        xpath = "//dt[contains(@class, 'node-publication-full__specifications-item-label') and contains(text(), '{}')]/following-sibling::dd/text()"
        item = doc.xpath(xpath.format(label))
        if len(item) > 0:
            return item[0]
        return ""

    def _get_pdf(self, pdf_url):
        try:
            response = self.session.get(pdf_url)
            content_type = response.headers['content-type']
            if content_type != 'application/pdf':
                self._log_message(f"...ERROR: unsupported content type {content_type}")
                return None
            return response.content
        except HTTPError as e:
            self._log_message(f'HTTPError occurred during pdf download: {e}')
            raise
        except Exception as e:
            self._log_message(f'Unknown error occurred during pdf download: {e}')
            raise

    def _upload_pdf(self, pdf, pdf_url, report_path_id):
        pdf_name = pdf_url.split("/")[-1]
        if pdf_name.endswith('pdf'):
            pdf_name = f"{pdf_name[:-3]}.pdf"
        elif pdf_name.endswith('pdf-0'):
            pdf_name = f"{pdf_name[:-5]}.pdf"
        else:
            pdf_name = f"{pdf_name}.pdf"

        filename = f"{report_path_id}/{pdf_name}"
        self.webdav_utils.upload_webdav(self._log_message, "report_pdf", self.base_dir, filename, io.BytesIO(pdf))

    def _upload_metadata(self, metadata, report_path_id):
        filename = f"{report_path_id}/metadata.txt"
        self.webdav_utils.upload_webdav(self._log_message, "report_metadata", self.base_dir, filename,
                                        io.BytesIO(json.dumps(metadata).encode('utf-8')))

    def _log_message(self, message):
        logger.info(message)
        logging.StreamHandler().flush()
        print(message)

    def run(self, start_page):
        query_url = "{}/publicaties?f%5B0%5D=publication_subtype%3A26&page={}"

        next_paginated_results_page = start_page
        while next_paginated_results_page:
            self._log_message(f"Paginated results page: {next_paginated_results_page}")
            report_paths = self._get_next_paginated_results(query_url.format(self.base_url, next_paginated_results_page))

            for report_index, report_path in enumerate(report_paths, start=1):
                self._log_message(f"Report index on this page: {report_index}")
                if self._has_been_processed(report_path):
                    continue

                self._log_message(f"START {report_path} {datetime.now().replace(microsecond=0).isoformat()}")

                pdf_url, metadata = self._get_pdf_url_and_metadata(urljoin(self.base_url, report_path))

                pdf = self._get_pdf(pdf_url)
                if pdf is None:
                    self._log_message("...ERROR: no pdf found for pdf_url, skipping this report")
                    continue

                report_path_id = report_path.split("/")[-1]
                self._upload_pdf(pdf, pdf_url, report_path_id)
                self._upload_metadata(metadata, report_path_id)

                self._log_message(f"END   {report_path} {datetime.now().replace(microsecond=0).isoformat()} {metadata['aantalPaginas']}pages")
                sleep(1)

            if len(report_paths) == 0:
                self._log_message(f"Length of report_paths is 0 for page {next_paginated_results_page}, end of reports reached")
                next_paginated_results_page = None
            else:
                next_paginated_results_page = self._get_next_paginated_results_page(next_paginated_results_page)