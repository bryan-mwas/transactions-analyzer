import os
import json
import time
import tempfile
import dataclasses
from celery import shared_task
from werkzeug.utils import secure_filename
from packages.pdfLoader.load_pdf import MpesaLoader
from packages.pdfLoader.process_data import TransactionFactory


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


@shared_task()
def extract_data_from_pdf(fP, password):
    mpesa_pdf = MpesaLoader(filePath=fP, secret=password)
    dataFrames = mpesa_pdf.initDF()
    tFactory = TransactionFactory(dataFrames)

    tFactory.handle_all_charges()
    tFactory.handle_paybill()
    tFactory.handle_till()
    tFactory.handle_send_money()

    return json.dumps(tFactory.transactions, cls=EnhancedJSONEncoder)
