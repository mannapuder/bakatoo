import time
import random
import librosa
import os
import pychorus


local = False


def process(task):
    # TODO: don't hardcode stuff
    task.status = {'status': 'laeb..', 'progress': 0}
    #try:
    if local:
        path = os.path.join('uploads', task.uuid + ".mp3")
        y, sr = librosa.load(path)
    else:
        path = os.path.join('/tmp', task.uuid + ".mp3")
        y, sr = librosa.load(path)
    task.status = {'status': 'töötlemine', 'progress': 50}
    beat = get_beat(y, sr)
    task.status = {'status': 'töötlemine', 'progress': 60}
    chorus, start_sec = get_main_theme(path, task.uuid)
    task.status = {'status': 'valmis', 'progress': 100, 'result': f"BPM = {beat:2f}", 'chorus': chorus, 'chorus_start': start_sec}
    # except:
    #    task.status = {'status': 'Ebasobiv helifail', 'progress': 100,
     #                  'result': 'Error. Selle helifaili töötlemine ei õnnestunud, palun proovi uuesti.'}


def get_beat(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo


def get_main_theme(src, uuid):
    path = "".join(src.split(".")[:-1])
    print(path)
    output_file = path+"main_theme.wav"
    chorus_start_sec = pychorus.find_and_output_chorus(src, output_file, 15)
    return uuid + "main_theme.wav", chorus_start_sec

def split_file(main, src):
    pass
