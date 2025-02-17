import io
from datetime import datetime, timedelta
import re
import logging
import requests
import httpx

from time import sleep
from urllib.request import urlopen
from utils.logging import EP_LOG_FILE
from utils.webdav_utils import WebDAVUtils
from lxml import etree, html
from requests.exceptions import HTTPError

logger = logging.getLogger('ep')
HTML_TYPE = 'html'
XML_TYPE = 'xml'

class EP(object):
    def __init__(self, settings):
        self.base_dir = 'GPT-NL OpenStateFoundation (Projectfolder)/ep/'

        self.session = requests.Session()

        self.webdav_utils = WebDAVUtils(settings)

        self.processed_identifiers = self._get_processed_identifiers()

        self.base_url = 'https://www.europarl.europa.eu'

        self.earliest_date = datetime(2010, 1, 1).date()

    def _has_been_processed(self, identifier):
        return identifier in self.processed_identifiers

    def _log_message(self, message):
        logger.info(message)
        logging.StreamHandler().flush()
        print(message)

    def _get_processed_identifiers(self):
        try:
            with open(EP_LOG_FILE, 'r') as f:
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

    def _get_sleep_time(self, attempt):
        if attempt > 9:
            return None
        return 2**attempt

    def _get_report_page(self, url, attempt = 1):
        exception = None
        try:
            response = self.session.get(url)
            if response.status_code == 404:
                return response.status_code, '' # No report for this day
            else:
                return response.status_code, response.text
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

        attempt += 1
        sleepTime = self._get_sleep_time(attempt)
        if sleepTime:
            sleep(sleepTime)
            return self._get_report_page(url, attempt)
        else:
            raise exception

    def _get_report_path_from_report_page(self, report_page):
        doc = html.fromstring(report_page)
        container = "//table[contains(concat(' ', @class, ' '), ' doc_formats_box ')]"
        xml_elements = doc.xpath(f"{container}//a[substring(@href, string-length(@href) - 3) = '.xml']/@href")
        if len(xml_elements) == 1:
            return XML_TYPE, xml_elements[0]

        message = f"... number of XML links encountered not equal to 1 ({len(xml_elements)})"
        self._log_message(message)
        html_elements = doc.xpath(f"{container}//a[substring(@href, string-length(@href) - 4) = '.html']/@href")
        if len(html_elements) == 1:
            return HTML_TYPE, html_elements[0]

        message = f"... number of HTML links encountered not equal to 1 ({len(html_elements)})"
        self._log_message(message)
        raise Exception(message)

    def _get_minutes_path_from_report_page(self, report_page):
        return report_page.replace("CRE-", "PV-").replace("-TOC", "")

    def _get_report(self, report_type, report_path):
        report_url = self.base_url + report_path
        if report_type == XML_TYPE:
            return self._get_xml_doc('report', report_url)
        elif report_type == HTML_TYPE:
            return self._get_html_doc('report', report_url)
        else:
            raise Exception(f"... unknown report type {report_type}")

    def _get_xml_doc(self, doc_type, url):
        try:
            return etree.parse(urlopen(url))
        except etree.XMLSyntaxError as e:
            self._log_message(f"XMLSyntaxError occurred during xml download of {doc_type} {url}, {e}")
            raise

    def _get_html_doc(self, doc_type, url):
        try:
            return html.parse(urlopen(url))
        except HTTPError as e:
            self._log_message(f"HTTPError occurred during html download of {doc_type} {url}, {e}")
            raise
        except Exception as e:
            self._log_message(f"Unknown error occurred during html download of {doc_type} {url}, {e}")
            raise

    def _get_minutes(self, report_type, minutes_path):
        minutes_url = self.base_url + minutes_path
        if report_type == XML_TYPE:
            return self._get_xml_doc('minutes', minutes_url)
        elif report_type == HTML_TYPE:
            return self._get_html_doc('minutes', minutes_url)
        else:
            raise Exception(f"... unknown report type {report_type}")

    def _upload_docs(self, report, minutes, report_type, date_str):
        self.webdav_utils.upload_webdav(self._log_message, "report", self.base_dir, f"{date_str}/volledig_verslag.{report_type}", io.BytesIO(etree.tostring(report)))
        self.webdav_utils.upload_webdav(self._log_message, "minutes", self.base_dir, f"{date_str}/notulen.{report_type}", io.BytesIO(etree.tostring(minutes)))

    def _get_next_date(self, date):
        return date - timedelta(1)
    
    def _log_start_message(self, date_str):
        self._log_message(f"START {date_str} {datetime.now().replace(microsecond=0).isoformat()}")

    def _log_end_message(self, date_str):
        self._log_message(f"END   {date_str} {datetime.now().replace(microsecond=0).isoformat()}")

    def run(self, start_date):
        query_url = self.base_url + '/sides/getDoc.do?pubRef=-//EP//TEXT+CRE+{}+TOC+DOC+XML+V0//NL'

        if start_date:
            date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            date = datetime.now().date()

        while date >= self.earliest_date:
            date_str = "%04d%02d%02d" % (date.year, date.month, date.day)
            self._log_message(f"Processing day: {date_str}")
            if self._has_been_processed(date_str):
                date = self._get_next_date(date)
                continue

            self._log_start_message(date_str)
            url = query_url.format(date_str)
            status_code, report_page = self._get_report_page(url)
            if status_code == 404:
                self._log_message(f"... no report found for this day")
                self._log_end_message(date_str)
                date = self._get_next_date(date)
                continue
            elif status_code != 200:
                message = f"... status code when retrieving report is {status_code}"
                self._log_message(message)
                raise Exception(message)

            report_type, report_path = self._get_report_path_from_report_page(report_page)
            report = self._get_report(report_type, report_path)
            minutes_path = self._get_minutes_path_from_report_page(report_path)
            minutes = self._get_minutes(report_type, minutes_path)
            self._upload_docs(report, minutes, report_type, date_str)

            self._log_end_message(date_str)

            sleep(1)
            date = self._get_next_date(date)