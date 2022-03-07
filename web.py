import os

import flask as f
from flask import request

from anna.task import Task

app = f.Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'yeet'


@app.route('/')
def _hello():
    return app.send_static_file('index.html')


def allowed_file(filename):
    return True


@app.route('/upload', methods=['POST'])
def _upload():
    # https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
    print(request.form)
    print(request.files)
    print(request.data)
    file = request.files['file']
    if file and allowed_file(file.filename):
        task = Task(status={'status': 'in queue', 'progress': 0})
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], task.uuid + ".mp3"))
        app.config['queue'].put(task)
        app.config['work'][task.uuid] = task
        return task.uuid
    return None


@app.route('/results/<id_>')
def _get_results(id_):
    return app.config['work'][id_].status


def run(queue):
    app.config['work'] = {}
    app.config['queue'] = queue
    app.run()


if __name__ == '__main__':
    from queue import Queue
    run(Queue())
