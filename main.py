from packages.pdfLoader.load_pdf import MpesaLoader
from packages.pdfLoader.process_data import TransactionFactory
import json
import dataclasses


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


if __name__ == "__main__":
    mpesa_pdf = MpesaLoader()
    dataFrames = mpesa_pdf.initDF()
    tFactory = TransactionFactory(dataFrames)

    tFactory.handle_all_charges()
    tFactory.handle_paybill()
    tFactory.handle_till()
    tFactory.handle_send_money()

    result = json.dumps(tFactory.transactions, cls=EnhancedJSONEncoder)
