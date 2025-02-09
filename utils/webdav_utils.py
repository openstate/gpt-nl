import httpx
from time import sleep

from webdav4.client import Client, HTTPError

class WebDAVUtils():
    def __init__(self, settings):
        # Create a WEBDAV connection
        self.client = Client(settings['URL'], auth=(settings['USER'], settings['PASSWORD']))

    # Check if all parent folders exist, if not create them
    def create_folder(self, path, file):
        for folder in file.split('/')[:-1]:
            path += f'{folder}/'
            if not self.client.exists(path):
                self.client.mkdir(path)

    def upload_fileobj(self, content, filename, **kwargs):
        self.client.upload_fileobj(content, filename, **kwargs)

    def _get_sleep_time(self, attempt):
        if attempt > 9:
            return None
        return 2**attempt

    def upload_webdav(self, log_callback, fileType, base_dir, filename, bytesIO, attempt = 1):
        exception = None
        try:
            self.create_folder(base_dir, filename)
            self.upload_fileobj(bytesIO, f'{base_dir}{filename}', overwrite=True)
        except httpx.ConnectError as e:
            log_callback(f"ConnectError when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except httpx.ConnectTimeout as e:
            log_callback(f"ConnectTimeout when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except httpx.ReadTimeout as e:
            log_callback(f"ReadTimeout when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except httpx.RemoteProtocolError as e:
            log_callback(f"RemoteProtocolError when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except HTTPError as e:
            log_callback(f"HTTPError when uploading {fileType} attempt {attempt}: {e}")
            exception = e
        except Exception as e:
            log_callback(f"Unknown exception when uploading {fileType} attempt {attempt}: {e.__class__.__name__}, {e}")
            raise

        if exception:
            attempt += 1
            sleepTime = self._get_sleep_time(attempt)
            if sleepTime:
                sleep(sleepTime)
                self.upload_webdav(log_callback, fileType, base_dir, filename, bytesIO, attempt)
            else:
                raise exception
