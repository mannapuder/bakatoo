import concurrent.futures
import time
import random
import librosa
import os
import pychorus
import requests
from pprint import pp

local = True

executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)  # max_workers võiks olla kui mitu funki on eeldatav pm


def process(task):
    # TODO: don't hardcode stuff
    task.status = {'status': 'laeb..', 'progress': 10}
    # try:
    if local:
        path = os.path.join('uploads', task.uuid + ".mp3")
        y, sr = librosa.load(path)
    else:
        path = os.path.join('/tmp', task.uuid + ".mp3")
        y, sr = librosa.load(path)
    task.status = {'status': 'töötlemine', 'progress': 30}

    results = {}

    futs = [executor.submit(*fn_and_args) for fn_and_args in [
        [recognize, path, results],
        [get_beat, y, sr, results],
        [get_main_theme, path, task.uuid, results]
        # lisa kui vaja, also increase max workers
    ]]

    i = 1
    for fut in concurrent.futures.as_completed(futs):
        task.status = {'status': 'töötlemine', 'progress': round(30 + (70 / len(futs) * i))}
        i += 1

    task.status = {'status': 'valmis', 'progress': 100, 'result': f"BPM = {results['beat']:2f}", 'chorus': results['chorus'],
                   'chorus_start': results['start_sec'], 'title_and_artist': results['title and artist']}
    # except:
    #    task.status = {'status': 'Ebasobiv helifail', 'progress': 100,
    #                  'result': 'Error. Selle helifaili töötlemine ei õnnestunud, palun proovi uuesti.'}


def get_beat(y, sr, results):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    results['beat'] = tempo
    # return tempo


def get_main_theme(src, uuid, results):
    path = "".join(src.split(".")[:-1])
    print(path)
    output_file = path + "main_theme.wav"
    chorus_start_sec = pychorus.find_and_output_chorus(src, output_file, 15)
    results['chorus'] = uuid + "main_theme.wav"
    results['start_sec'] = chorus_start_sec
    #return uuid + "main_theme.wav", chorus_start_sec


def split_file(main, src):
    pass


def recognize(path, results):
    # TODO: use chorus?
    resp = requests.post(
        'https://api.audd.io',
        data={
            'api_token': 'd10b34bdde19579f58c0903de2e40c3a',  # don't make me poor
            'return': 'apple_music,spotify'
        },
        files={
            'file': open(path, 'rb')
        }
    )
    if resp.status_code != 200:
        results['title and artist'] = "Rick Astley - Never Gonna Give You Up "
        raise RuntimeError("never gonna give")
    resp = resp.json()
    if resp['status'] != 'success':
        results['title and artist'] = "Rick Astley - Never Gonna Give You Up "
        raise RuntimeError("never gonna give")
    # do something with resp
    results['title and artist'] = f"{resp['response']['artist']} - {resp['response']['title']}"
    #return f"{resp['response']['artist']} - {resp['response']['title']}"
