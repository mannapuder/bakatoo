import time
import random
import librosa
import os

local = False


def process(task):
    # TODO: don't hardcode stuff
    task.status = {'status': 'laeb..', 'progress': 0}
    try:
        if local:
            y, sr = librosa.load(os.path.join('uploads', task.uuid + ".mp3"))
        else:
            y, sr = librosa.load(os.path.join('/tmp', task.uuid + ".mp3"))
        task.status = {'status': 'töötlemine', 'progress': 50}
        beat = get_beat(y, sr)
        task.status = {'status': 'valmis', 'progress': 100, 'result': f"BPM = {beat:2f}"}
    except:
        task.status = {'status': 'Ebasobiv helifail', 'progress': 100,
                       'result': 'Error. Selle helifaili töötlemine ei õnnestunud, palun proovi uuesti.'}


def get_beat(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo


def get_main_theme(src):
    pass


def split_file(main, src):
    pass
