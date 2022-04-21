import concurrent.futures
import time
import random
import librosa
import os
import pychorus
import requests
import audio_segmentation
import audio_structure
from pprint import pp

local = True

executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)  # max_workers võiks olla kui mitu funki on eeldatav pm

tempos = [[0, 24], [25, 45], [45, 60], [60, 66], [66, 76], [76, 108], [108, 120], [120, 156], [156, 176], [168, 200], [200, 400]]
terms = ["Larghissimo", "Grave", "Largo", "Larghetto", "Adagio", "Moderato", "Andante", "Allegro", "Vivace", "Presto", "Prestissimo"]

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
    get_segmentation(y, sr, results)
    i = 1
    for fut in concurrent.futures.as_completed(futs):
        task.status = {'status': 'töötlemine', 'progress': round(30 + (70 / len(futs) * i))}
        i += 1

    task.status = {'status': 'valmis', 'progress': 100, 'result': f"BPM = {results['beat']:2f}", 'chorus': results['chorus'],
                   'chorus_start': results['start_sec'], 'title_and_artist': results['title and artist'],
                   'segmentation': results['segmentation'], 'structure_name': results['structure_name'], 'structure_desc': results['structure_desc']}
    # except:
    #    task.status = {'status': 'Ebasobiv helifail', 'progress': 100,
    #                  'result': 'Error. Selle helifaili töötlemine ei õnnestunud, palun proovi uuesti.'}


def get_beat(y, sr, results):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    results['beat'] = tempo
    for i in tempos:
        if i[0] <= tempo <= i[1]:
            results['tempo_term'] = terms[i]

def just_get_beat(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    for i in tempos:
        if i[0] <= tempo <= i[1]:
            tempo_term = terms[i]
    return tempo, tempo_term

def get_main_theme(src, uuid, results):
    path = "".join(src.split(".")[:-1])
    print(path)
    output_file = path + "main_theme.wav"
    chorus_start_sec = pychorus.find_and_output_chorus(src, output_file, 15)
    results['chorus'] = uuid + "main_theme.wav"
    results['start_sec'] = chorus_start_sec
    #return uuid + "main_theme.wav", chorus_start_sec

#felt good might delete later
def features(audio_path):
    features, features_frames = es.MusicExtractor(lowlevelStats=['mean', 'stdev'],
                                                  rhythmStats=['mean', 'stdev'],
                                                  tonalStats=['mean', 'stdev'])(audio_path)
    bpm = features['rhythm.bpm']
    helistik = (features['tonal.chords_key'], features['tonal.chords_scale'])
    energy = features['tonal.tuning_nontempered_energy_ratio']
    dance = features['rhythm.danceability'] / 3

def get_segmentation(y, sr, results):
    segments = audio_segmentation.get_segmentation(y, sr)
    results['segmentation'] = segments

def get_structure(segm, results):
    name, desc = audio_structure.predict(segm)
    results["structure_name"] = name
    results["structure_desc"] = desc

def get_tempo_each_segm(segm, y, sr, results):

    segm_tempos = []

    for seg in segm: #TODO: figure this shit out
        tempo, tempo_term = just_get_beat(y, sr)
        segm_tempos.append([tempo, tempo_term])

    results["tempos"] = segm_tempos
    pass

def get_key_each_segm(segm, results):

    segm_keys = []
    for seg in segm:
        #TODO: get key here somehow
        key = "A"
        segm_keys.append(key)

    results["keys"] = segm_keys

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
