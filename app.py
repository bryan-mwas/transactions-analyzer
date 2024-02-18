import os
from flask import Flask, jsonify, request
from celery import Celery, Task
from packages.pdfLoader.load_pdf import MpesaLoader
from tasks import extract_data_from_pdf
from celery.result import AsyncResult
from werkzeug.utils import secure_filename


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config['CELERY'])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


app = Flask(__name__)

app.config.from_mapping(
    CELERY=dict(
        broker_url="amqp://localhost",
        result_backend="rpc://",
    )
)

celery_app = celery_init_app(app)


@app.post('/')
def index():
    if request.method == 'POST':
        f = request.files['file']
        password = request.form['password']

        fP = os.path.join('/tmp/', secure_filename(f.filename))
        f.save(fP)
        result = extract_data_from_pdf.delay(fP, password)

        return jsonify({
            'taskID': result.id
        })


@app.get('/result/<id>')
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    if result.ready():
        return result.result
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None
    }
