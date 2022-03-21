import os

import flask as f
from flask import request, send_from_directory

from task import Task

local = False
app = f.Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
if local:
    app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'yeet'


@app.route('/')
def _hello():
    return app.send_static_file('index.html')


def allowed_file(filename):
    print(filename)
    print(filename.split(".")[-1])
    return filename.split(".")[-1] == "wav"


@app.route('/upload', methods=['POST'])
def _upload():
    # https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
    print(request.form)
    print(request.files)
    print(request.data)
    file = request.files['file']
    print(file.filename)
    if file and allowed_file(file.filename):
        task = Task(status={'status': 'in queue', 'progress': 0})
        print(os.path.join(app.config['UPLOAD_FOLDER'], task.uuid + ".mp3"))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], task.uuid + ".mp3"))
        app.config['queue'].put(task)
        app.config['work'][task.uuid] = task
        return task.uuid
    else:
        task = Task(status={'status': 'Ebasobiv fail', 'progress': 100, 'result': 'Error. Sain ebasobiva laiendiga faili, palun proovi uuesti.'})
        app.config['work'][task.uuid] = task
        return task.uuid
    return None


@app.route('/results/<id_>')
def _get_results(id_):
    return app.config['work'][id_].status


@app.route("/uploads/<path:name>")
def download_file(name):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], name, as_attachment=True
    )

def run(queue):
    app.config['work'] = {}
    app.config['queue'] = queue
    port = int(os.environ.get("PORT", 5000))
    if local:
        app.run(debug=False, port=port)
    else:
        app.run(debug=False, host='0.0.0.0', port=port)



if __name__ == '__main__':
    from queue import Queue
    run(Queue())
