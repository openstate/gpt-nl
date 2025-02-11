import io
import json
import logging
import re
import requests
import httpx

from datetime import datetime
from time import sleep
from utils.logging import NATURALIS_LOG_FILE
from urllib.request import urlopen
from utils.webdav_utils import WebDAVUtils
from lxml import html, etree
from urllib.parse import urljoin
from requests.exceptions import HTTPError

logger = logging.getLogger('naturalis')

class Naturalis(object):
    def __init__(self, settings):
        self.base_dir = 'GPT-NL OpenStateFoundation (Projectfolder)/naturalis/'

        self.session = requests.Session()

        self.webdav_utils = WebDAVUtils(settings)

        self.processed_identifiers = self._get_processed_identifiers()

        self.didl_namespace = 'urn:mpeg:mpeg21:2002:02-DIDL-NS'
        self.dii_namespace = 'urn:mpeg:mpeg21:2002:01-DII-NS'
        self.oai_namespace = 'http://www.openarchives.org/OAI/2.0/'
        self.mods_namespace = 'http://www.loc.gov/mods/v3'
        self.dc_namespace = 'http://purl.org/dc/elements/1.1/'
        self.oai_dc_namespace = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
        self.dcterms_namespace = 'http://purl.org/dc/terms/'
        self.metadata_prefix = "nl_didl"
        self.base_url = "https://repository.naturalis.nl"
        self.list_url_start = f"{self.base_url}/oai/?verb=ListIdentifiers&metadataPrefix={self.metadata_prefix}"
        self.list_url_next_prefix = f"{self.base_url}/oai/?verb=ListIdentifiers&resumptionToken="
        self.article_url_prefix = f"{self.base_url}/oai/?verb=GetRecord&metadataPrefix={self.metadata_prefix}&identifier="

    def _log_message(self, message):
        logger.info(message)
        logging.StreamHandler().flush()
        print(message)

    def _has_been_processed(self, identifier):
        return identifier in self.processed_identifiers

    def _get_processed_identifiers(self):
        try:
            with open(NATURALIS_LOG_FILE, 'r') as f:
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


    def _query_url(self, resumption_token):
        if resumption_token is None:
            return self.list_url_start
        else:
            return self.list_url_next_prefix + resumption_token

    def _get_identifiers(self, url):
        list_xml = etree.parse(urlopen(url))
        parser = etree.ETXPath("//{%s}header[not(contains(@status, 'deleted'))]/{%s}identifier" % (self.oai_namespace, self.oai_namespace))
        identifiers  = [identifier.text for identifier in parser(list_xml)]
        resumption_token = list_xml.find('.//{*}resumptionToken')
        if resumption_token is not None:
            resumption_token = resumption_token.text
        
        return identifiers, resumption_token

    def _get_sleep_time(self, attempt):
        if attempt > 9:
            return None
        return 2**attempt

    def _get_response(self, url, attempt = 1):
        exception = None
        try:
            return etree.parse(urlopen(url))
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

    def _get_pdf_url_and_metadata(self, url_prefix, identifier):
        url = url_prefix + identifier
        doc = self._get_response(url).getroot()

        didl_identifier = self._get_didl_child(doc, '//didl:DIDL//dii:Identifier/text()')[0]
        pdf_url = self._get_pdf_url(doc)
        title = self._get_mods_child(doc, '//mods:mods/mods:titleInfo/mods:title')[0].text

        author_elements = self._get_mods_child(doc, '//mods:mods/mods:name[@type=\'personal\']/mods:displayForm')
        authors = [author.text for author in author_elements]

        authors = self._get_authors(doc)

        publication_date_str = self._get_mods_child(doc, '//mods:mods/mods:originInfo/mods:dateIssued')[0].text
        try:
            publication_date = datetime.strptime(publication_date_str, "%Y-%m-%d")
        except ValueError as e:
            publication_date = None

        file_size = self._get_mods_child(doc, '//mods:physicalDescription/mods:extent/text()')
        if len(file_size) > 0:
            file_size = file_size[0]
        else:
            file_size = None
        file_type = self._get_mods_child(doc, '//mods:physicalDescription/mods:internetMediaType/text()')
        if len(file_type) > 0:
            file_type = file_type[0]
        else:
            file_type = None

        doi_identifier_element = self._get_mods_child(doc, '//mods:mods/mods:identifier[@type="doi"]/text()')
        doi_identifier = doi_identifier_element[0] if len(doi_identifier_element) > 0 else None

        journal, journal_reference = self._get_journal_reference(doc, url)

        rights = self._get_didl_child(doc, '//didl:DIDL//dcterms:accessRights/text()')[0]

        citation = f"{', '.join(authors)} ({publication_date.year}). {title}."
        if journal_reference:
            citation += f" {journal_reference}."
        if doi_identifier:
            citation += f" {doi_identifier}"

        abstract_element = self._get_mods_child(doc, '//mods:mods/mods:abstract/text()')
        abstract = abstract_element[0] if len(abstract_element) > 0 else None

        topics = ', '.join(self._get_mods_child(doc, '//mods:mods/mods:subject/mods:topic/text()'))

        metadata = {
            'identifier': identifier,
            'didlIdentifier': didl_identifier,
            'OAIUrl': url,
            'pdfUrl': pdf_url,
            'titel': title,
            'auteurs': authors,
            'journal': journal,
            'rechten': rights,
            'jaartal': publication_date.year if publication_date else None,
            'bestandsGrootte': file_size,
            'bestandsType': file_type,
            'citation': citation,
            'keywords': topics,
            'abstract': abstract
        }

        return pdf_url, metadata

    def _get_pdf_url(self, doc):
        pdf_url = self._get_mods_child(doc, '//mods:mods/mods:location/mods:url[@access=\'raw object\']/text()')
        if len(pdf_url) > 0:
            pdf_url = pdf_url[0]
        else:
            pdf_url = self._get_didl_child(doc, '//didl:DIDL//didl:Resource[@mimeType="application/pdf"]/@ref')
            if len(pdf_url) > 0:
                pdf_url = pdf_url[0]
            else:
                return None

        return pdf_url
    
    def _get_authors(self, doc):
        author_elements = self._get_mods_child(doc, '//mods:mods/mods:name[@type=\'personal\']')
        authors = []
        for author_element in author_elements:
            first_name = self._get_mods_child(author_element, './mods:namePart[@type="given"]/text()')
            if len(first_name) == 0:
                name = self._get_mods_child(author_element, './mods:displayForm/text()')
                if len(name) > 0:
                    authors.append(name[0])
            else:
                first_name = first_name[0]
                last_name = self._get_mods_child(author_element, './mods:namePart[@type="family"]/text()')[0]
                authors.append(f"{first_name} {last_name}")

        return authors

    def _get_didl_child(self, doc, xpath):
        child = doc.xpath(xpath, namespaces={
            'didl': self.didl_namespace,
            'dii': self.dii_namespace,
            'dcterms': self.dcterms_namespace
            })
        return child

    def _get_mods_child(self, doc, xpath):
        child = doc.xpath(xpath, namespaces={'mods': self.mods_namespace})
        return child
    
    def _get_oai_dc_child(self, doc, xpath):
        child = doc.xpath(xpath, namespaces={'dc': self.dc_namespace, 'oai': self.oai_dc_namespace})
        return child

    def _get_journal_reference(self, doc, url):
        # Try to retrieve the details for the APA Style journal reference
        related_item = '//mods:mods/mods:relatedItem'
        journal = self._get_mods_child(doc, f'{related_item}/mods:titleInfo/mods:title')
        if len(journal) == 0:
            return self._get_journal_reference_using_oai_dc(url)
        
        journal = journal[0].text

        volume_elements = self._get_mods_child(doc, f'{related_item}/mods:part/mods:detail[@type="volume"]//*[normalize-space()]/text()')
        volume = volume_elements[0] if len(volume_elements) > 0 else None
        issue_elements = self._get_mods_child(doc, f'{related_item}/mods:part/mods:detail[@type="issue"]//*[normalize-space()]/text()')
        issue = issue_elements[0] if len(issue_elements) > 0 else None

        start_page_element = self._get_mods_child(doc, f'{related_item}/mods:part/mods:extent[@unit="page"]/mods:start/text()')
        start_page = start_page_element[0] if len(start_page_element) > 0 else None
        end_page_element = self._get_mods_child(doc, f'{related_item}/mods:part/mods:extent[@unit="page"]/mods:end/text()')
        end_page = end_page_element[0] if len(end_page_element) > 0 else None

        reference = f"{journal}, {volume}"
        if issue:
            reference += f"({issue})"
        if start_page:
            reference += f", {start_page}-{end_page}"

        return journal, reference

    def _get_journal_reference_using_oai_dc(self, url):
        # If no journal reference was present in the nl_didl metadata, try the oai_dc metadata
        oai_dc_url = url.replace(f"metadataPrefix={self.metadata_prefix}", "metadataPrefix=oai_dc")
        doc = self._get_response(oai_dc_url).getroot()

        reference = self._get_oai_dc_child(doc, f"//oai:dc/dc:source/text()")
        if len(reference) == 0:
            return None, None
        journal = reference[0].split(" vol.")[0] # This assumes that name of journal is always followed by " vol."

        return journal, reference

    def _get_pdf(self, pdf_url):
        try:
            return self.session.get(pdf_url).content
        except HTTPError as e:
            self._log_message(f'HTTPError occurred during pdf download: {e}')
            raise
        except Exception as e:
            self._log_message(f'Unknown error occurred during pdf download: {e}')
            raise

    def _upload_pdf(self, pdf, pdf_url, identifier):
        pdf_name = pdf_url.split("/")[-1]

        filename = f"{identifier}/{pdf_name}"
        self.webdav_utils.upload_webdav(self._log_message, "article_pdf", self.base_dir, filename, io.BytesIO(pdf))

    def _upload_metadata(self, metadata, identifier):
        filename = f"{identifier}/metadata.txt"
        self.webdav_utils.upload_webdav(self._log_message, "article_metadata", self.base_dir, filename,
                                        io.BytesIO(json.dumps(metadata).encode('utf-8')))

    def run(self, resumption_token):
        while True:
            self._log_message(f"Using resumption token: {resumption_token}")
            identifiers, resumption_token = self._get_identifiers(self._query_url(resumption_token))
            if len(identifiers) == 0:
                self._log_message(f"WARNING: no identifiers found for resumption token {resumption_token}")

            for identifier_index, identifier in enumerate(identifiers, start=1):                
                self._log_message(f"Identifier index on this page: {identifier_index}")
                if self._has_been_processed(identifier):
                    continue

                self._log_message(f"START {identifier} {datetime.now().replace(microsecond=0).isoformat()}")

                pdf_url, metadata = self._get_pdf_url_and_metadata(self.article_url_prefix, identifier)

                pdf = self._get_pdf(pdf_url)

                self._upload_pdf(pdf, pdf_url, identifier)
                self._upload_metadata(metadata, identifier)

                self._log_message(f"END   {identifier} {datetime.now().replace(microsecond=0).isoformat()} {metadata['bestandsGrootte']}")
                sleep(1)

            if resumption_token is None or resumption_token.strip() == '':
                self._log_message(f"No resumption token anymore, end of identifiers reached")
                break
