from webdav4.client import Client

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
