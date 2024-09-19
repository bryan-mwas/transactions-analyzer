from celery import shared_task
from packages.pdfLoader.load_pdf import MpesaLoader
from packages.pdfLoader.process_data import TransactionFactory
from dataclasses import asdict
from celery import Task
from tempfile import NamedTemporaryFile
import os


@shared_task(bind=True)
def extract_data_from_pdf(self: Task, fileUpload, password):
    # Pass the uploaded file at this point for context management
    tmp_file_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(fileUpload)
            tmp_pdf.flush()
            tmp_file_path = tmp_pdf.name
            mpesa_pdf = MpesaLoader(filePath=tmp_file_path, secret=password)
            dataFrames = mpesa_pdf.initDF(task=self)
            tFactory = TransactionFactory(dataFrames)

            tFactory.handle_all_charges()
            tFactory.handle_paybill()
            tFactory.handle_till()
            tFactory.handle_send_money()

            transactions = [asdict(transaction)
                            for transaction in tFactory.transactions]
            return transactions
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            print(f'Cleaning file >> {tmp_file_path}')
            os.unlink(tmp_file_path)
