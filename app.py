import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from packages.pdfLoader.load_pdf import MpesaLoader
from packages.pdfLoader.process_data import TransactionFactory
import json
import dataclasses
import tempfile


app = Flask(__name__)


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


@app.route("/", methods=['POST', "GET"])
def index():
    if request.method == 'POST':
        f = request.files['file']
        password = request.form['password']

        with tempfile.TemporaryDirectory() as tmpdir:
            fP = os.path.join(tmpdir,
                              secure_filename(f.filename))
            f.save(fP)  # crucial else file won't be read.
            mpesa_pdf = MpesaLoader(filePath=fP, secret=password)
            dataFrames = mpesa_pdf.initDF()
            tFactory = TransactionFactory(dataFrames)

            tFactory.handle_all_charges()
            tFactory.handle_paybill()
            tFactory.handle_till()
            tFactory.handle_send_money()

            result = json.dumps(tFactory.transactions, cls=EnhancedJSONEncoder)

            print(result)
    return render_template('index.html')
