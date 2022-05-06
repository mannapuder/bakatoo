import concurrent.futures
import time
import random
import librosa
import os
import pychorus
import requests
import audio_segmentation
import audio_structure
import madmom


local = False
executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

#Global parameters
tempos = [[0, 24], [25, 45], [45, 60], [60, 66], [66, 76], [76, 108], [108, 120], [120, 156], [156, 176], [168, 200],
          [200, 400]]
terms = ["Larghissimo", "Grave", "Largo", "Larghetto", "Adagio", "Andante", "Moderno", "Allegro", "Vivace", "Presto",
         "Prestissimo"]
key_recognizer = madmom.features.key.CNNKeyRecognitionProcessor()


def process(task):
    # TODO: don't hardcode stuff
    task.status = {'status': 'laeb..', 'progress': 10}
    # try:
    if local:
        path = os.path.join('uploads', task.uuid + ".mp3")
    else:
        path = os.path.join('/tmp', task.uuid + ".mp3")
    y, sr = librosa.load(path)
    y, trim_index = librosa.effects.trim(y)
    task.status = {'status': 'töötlemine', 'progress': 20}

    results = {}

    get_segmentation(y, sr, results)
    task.status = {'status': 'töötlemine', 'progress': 50}

    print(results)
    print(y)
    get_tempo_each_segm(results["segmentation"], y, sr, results)
    futs = [executor.submit(*fn_and_args) for fn_and_args in [
        [recognize, path, results],
        [get_beat, y, sr, results],
        [get_main_theme, path, task.uuid, results],
        [get_structure, results["segmentation"], results],
        [get_key_each_segm, results["segmentation"], y, sr, results]
    ]]

    i = 1
    for fut in concurrent.futures.as_completed(futs):
        task.status = {'status': 'töötlemine', 'progress': round(50 + (40 / len(futs) * i))}
        i += 1

    just_get_key(y, results)
    get_beat(y, sr, results)
    #dummy data for testing
    print(results)
    #Text info builder
    make_text(results)

    task.status = {'status': 'valmis', 'progress': 100, 'result': 'töötlemine lõpetatud',
                   'chorus_start': results['start_sec'], 'title_and_artist': results['title and artist'],
                   'segmentation': results['segmentation_perc'], 'structure_name': results['structure_name'],
                   'structure_desc': results['structure_desc'], 'keys': results['keys'], 'tempos': results['tempos'],
                   'general_desc': results['text']}
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
    tempo = round(tempo)
    tempo_term = "Unknown"
    for i in range(len(tempos)):
        if tempos[i][0] <= tempo <= tempos[i][1]:
            tempo_term = terms[i]
    return tempo, tempo_term


def just_get_key(y, results):
    key = madmom.features.key.key_prediction_to_label(key_recognizer(y))
    key = key.split(" ")
    key[1] = "duur" if key[1] == "major" else "moll"
    key = " ".join(key)
    results['key'] = key
    return key


def get_main_theme(src, uuid, results):
    path = "".join(src.split(".")[:-1])
    print(path)
    output_file = path + "main_theme.wav"
    chorus_start_sec = pychorus.find_and_output_chorus(src, output_file, 15)
    results['chorus'] = uuid + "main_theme.wav"
    results['start_sec'] = chorus_start_sec
    # return uuid + "main_theme.wav", chorus_start_sec


def get_segmentation(y, sr, results):
    segments, percentages = audio_segmentation.get_segmentation(y, sr, results)
    results['segmentation'] = segments
    results["segmentation_perc"] = percentages


def get_structure(segm, results):
    name, desc = audio_structure.predict(segm)
    results["structure_name"] = name
    results["structure_desc"] = desc


def get_tempo_each_segm(segments, y, sr, results):
    segm_tempos = []

    for seg in segments:  # TODO: figure this out

        tempo, tempo_term = just_get_beat(y[int(seg[1]):int(seg[2])], sr)
        segm_tempos.append([tempo, tempo_term])
    print("Tempos: ")
    print(segm_tempos)
    results["tempos"] = segm_tempos
    pass


def get_key_each_segm(segments, y, sr, results):
    segm_keys = []
    for seg in segments:
        # TODO: get key here somehow
        key = just_get_key(y[seg[1]:seg[2]], results)
        segm_keys.append(key)

    results["keys"] = segm_keys

def make_text(results):
    text = "Lorem ipsum dolore sit amet"
    tempos = results['tempos']
    keys = results['keys']

    results['text'] = text

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
    # return f"{resp['response']['artist']} - {resp['response']['title']}"
