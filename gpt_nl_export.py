# This script should be run in the ori_backend_1 container of the ORI project
#   sudo docker exec ori_backend_1 /bin/sh -c "python gpt_nl_export.py" >> gpt_nl_export.log
#   cd gpt_nl/
#   tar -cvf ori.tar *
#   gzip and upload to Research Drive
import math
import os
import pathlib
import shutil

from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import StoredDocument
from ocd_backend.settings import DATA_DIR_PATH, PROJECT_PATH

class GPTNLExport:
    # START_ID = 1
    # END_ID = 1449449
    # START_ID = 1449000
    # END_ID = 2738999
    START_ID = 2739000
    END_ID = 3738999
    BATCH_SIZE = 1000

    def __init__(self):
        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()

    def export(self):
        number_of_batches = math.ceil((self.END_ID - self.START_ID + 1)/self.BATCH_SIZE)

        for batch_index in range(0, number_of_batches):
            batch_start_id = self.START_ID + batch_index * self.BATCH_SIZE
            batch_end_id = self.START_ID + (batch_index + 1) * self.BATCH_SIZE - 1
            batch_start_id = min(batch_start_id, self.END_ID)
            batch_end_id = min(batch_end_id, self.END_ID)

            print(f"\nNow exporting ids {batch_start_id} --- {batch_end_id}")
            self.export_batch(batch_start_id, batch_end_id)

    def export_batch(self, batch_start_id, batch_end_id):
        self.output_path = os.path.join(PROJECT_PATH, f'gpt_nl', f'{batch_start_id}_{batch_end_id}')
        pathlib.Path(self.output_path).mkdir(parents=True, exist_ok=True) 

        records = self.session.query(StoredDocument).filter(StoredDocument.id >= batch_start_id).filter(StoredDocument.id <= batch_end_id).all()
        for record in records:
            markdown_name = self.full_markdown_name(record.id, record.resource_ori_id)
            metadata_name = self.full_metadata_name(record.id, record.resource_ori_id)
            markdown_size = self.file_size(markdown_name)
            metadata_size = self.file_size(metadata_name)
            if markdown_size > 0 and metadata_size > 0:
                shutil.copy2(markdown_name, self.output_markdown_name(record.id))
                shutil.copy2(metadata_name, self.output_metadata_name(record.id))
                print(f"...copied id={record.id}, resource_ori_id={record.resource_ori_id}")
            else:
                print(f"...ERROR, empty file encountered for {record.id},{record.resource_ori_id}: {markdown_size} {metadata_size}")

    def file_size(self, file_name):
        if os.path.exists(file_name):
            return os.stat(file_name).st_size
        else:
            return 0

    def full_markdown_name(self, id, resource_ori_id):
        return f"{self.base_name(id, resource_ori_id)}.md"
    
    def full_metadata_name(self, id, resource_ori_id):
        return f"{self.base_name(id, resource_ori_id)}.metadata"

    def base_name(self, id, resource_ori_id):
        return f"{DATA_DIR_PATH}/{self._id_partitioned(id)}/{resource_ori_id}"

    def _id_partitioned(self, id):
        thousands = id//1000
        thousands_as_string = str(thousands).zfill(9)
        return f"{thousands_as_string[0:3]}/{thousands_as_string[3:6]}/{thousands_as_string[6:]}"

    def output_base_name(self, id):
        return f"{self.output_path}/{id}"

    def output_markdown_name(self, id):
        return f"{self.output_base_name(id)}.md"
    
    def output_metadata_name(self, id):
        return f"{self.output_base_name(id)}.metadata"

GPTNLExport().export()