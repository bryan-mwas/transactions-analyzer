import os
from flask import Flask, jsonify, request
from celery import Celery, Task
from werkzeug.exceptions import RequestEntityTooLarge
from tasks import extract_data_from_pdf
from celery.result import AsyncResult
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

app.config['MAX_CONTENT_LENGTH'] = 1.5 * 1000 * 1000  # 1.5 Megabytes

celery_app = celery_init_app(app)


@app.post('/')
def index():
    try:
        if 'file' not in request.files:
            return {'error': "No file uploaded"}, 400

        uploadedFile = request.files['file']

        if uploadedFile.filename == '':
            return {'error': 'No selected file'}, 400

        if uploadedFile and allowed_file(uploadedFile.filename):
            password = request.form['password']

            fP = os.path.join('/tmp/', secure_filename(uploadedFile.filename))
            uploadedFile.save(fP)
            result = extract_data_from_pdf.delay(fP, password)

            return jsonify({
                'taskID': result.id
            }), 202
        else:
            return {'error': 'Invalid file type'}, 400
    except RequestEntityTooLarge:
        return {'error': 'Request Entity Too Large'}, 413


@app.get('/result/<id>')
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    if result.ready() and result.successful():
        return result.result
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None
    }
