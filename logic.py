import time
import random
import librosa
import os



def process(task):
    #TODO: don't hardcode stuff
    task.status = {'status': 'loading', 'progress': 0}
    y, sr = librosa.load(os.path.join('/tmp', task.uuid + ".mp3"))
    task.status = {'status': 'processing', 'progress': 50}
    beat = get_beat(y, sr)
    task.status = {'status': 'done', 'progress': 100, 'result': f"BPM = {beat:2f}"}


def get_beat(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo

