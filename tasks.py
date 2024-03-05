from celery import shared_task
from packages.pdfLoader.load_pdf import MpesaLoader
from packages.pdfLoader.process_data import TransactionFactory
from dataclasses import asdict


@shared_task(bind=True)
def extract_data_from_pdf(self, fP, password):
    mpesa_pdf = MpesaLoader(filePath=fP, secret=password)
    dataFrames = mpesa_pdf.initDF(task=self)
    tFactory = TransactionFactory(dataFrames)

    tFactory.handle_all_charges()
    tFactory.handle_paybill()
    tFactory.handle_till()
    tFactory.handle_send_money()

    transactions = [asdict(transaction)
                    for transaction in tFactory.transactions]
    return transactions
