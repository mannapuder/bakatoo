import concurrent.futures
import time
import random
import librosa
import os
import pychorus
import requests
import audio_segmentation
import audio_structure
from collections import Counter

import madmom

local = True
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# Global parameters
tempos = [[0, 24], [25, 45], [45, 60], [60, 66], [66, 72], [72, 80], [80, 108], [108, 120], [120, 156], [156, 176], [168, 200],
          [200, 400]]
terms = ["Larghissimo", "Grave", "Largo", "Larghetto", "Adagio", "Adagietto", "Andante", "Moderato", "Allegro", "Vivace", "Presto",
         "Prestissimo"]

key_recognizer = madmom.features.key.CNNKeyRecognitionProcessor()


def process(task):
    task.status = {'status': 'heliteose laadimine', 'progress': 10}
    # try:
    if local:
        path = os.path.join('uploads', task.uuid + ".mp3")
    else:
        path = os.path.join('/tmp', task.uuid + ".mp3")
    y, sr = librosa.load(path)
    y, trim_index = librosa.effects.trim(y)
    task.status = {'status': 'töötlemine', 'progress': 20}

    results = {}

    get_segmentation(y, sr, results, trim_index)
    task.status = {'status': 'töötlemine', 'progress': 50}

    print(results)
    print(y)
    get_tempo_each_segm(results["segmentation"], y, sr, results)
    futs = [executor.submit(*fn_and_args) for fn_and_args in [
        [get_beat, y, sr, results],
        [get_structure, results["segmentation"], results],
        [get_key_each_segm, results["segmentation"], y, sr, results],
    ]]

    i = 1
    for fut in concurrent.futures.as_completed(futs):
        task.status = {'status': 'töötlemine', 'progress': round(50 + (40 / len(futs) * i))}
        i += 1

    task.status = {'status': 'loon väljundit..', 'progress': 90}

    just_get_key(y, results)
    print(results)
    # Text info builder
    make_text(results)

    task.status = {'status': 'valmis', 'progress': 100, 'result': 'töötlemine lõpetatud',
                   'segmentation': results['segmentation_perc'], 'structure_name': results['structure_name'],
                   'structure_desc': results['structure_desc'], 'keys': results['keys'], 'tempos': results['tempos'],
                   'general_desc': results['text'], 'timestamps': results['timestamps']}

def get_beat(y, sr, results):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    results['beat'] = tempo
    for i in range(len(tempos)):
        if tempos[i][0] <= tempo <= tempos[i][1]:
            results['tempo_term'] = terms[i]


def just_get_beat(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = round(tempo)
    tempo_term = "Unknown"
    for i in range(len(tempos)):
        if tempos[i][0] <= tempo <= tempos[i][1]:
            tempo_term = terms[i]
    return tempo, tempo_term


def just_get_term(tempo):
    for i in range(len(tempos)):
        if tempos[i][0] <= tempo <= tempos[i][1]:
            tempo_term = terms[i]
            return tempo_term


def just_get_key(y, results):
    key = madmom.features.key.key_prediction_to_label(key_recognizer(y))
    # key = "G major"
    key = key.split(" ")
    key[1] = "duur" if key[1] == "major" else "moll"
    key = " ".join(key)
    # key = "Helistikku ei leitud"
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


def get_segmentation(y, sr, results, trim_index):
    segments, percentages = audio_segmentation.get_segmentation(y, sr, results)
    timestamps = calculate_timestamps(sr, segments, trim_index)
    results['segmentation'] = segments
    results["segmentation_perc"] = percentages
    results["timestamps"] = timestamps


def calculate_timestamps(sr, segmentation, trim_index):
    timestamps = []
    for seg in segmentation:
        start = int((seg[1] + trim_index[0]) / sr)
        end = int((seg[2] + trim_index[0]) / sr)
        start_time_str = "{0:g}:{1:02}".format( start // 60, start % 60)
        end_time_str = "{0:g}:{1:02}".format( end // 60, end % 60)
        timestamps.append([start_time_str, end_time_str])
    return timestamps


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
    text = ""
    tempos = results['tempos']
    min = 400
    max = 0
    min_tempo_term = tempos[0][1]
    max_tempo_term = tempos[0][1]
    for tempo in tempos:
        if tempo[0] > max:
            max = tempo[0]
            max_tempo_term = tempo[1]
        if tempo[0] < min:
            min = tempo[0]
            min_tempo_term = tempo[1]
    keys = set(results['keys'])
    if "Helistikku ei leitud" in keys:
        keys.remove("Helistikku ei leitud")
    segm = "".join([i[0] for i in results['segmentation']])
    segm_array = Counter([i[0] for i in results['segmentation']])
    segm_set = set([i[0] for i in results['segmentation']])

    if len(keys) > 1:
        text += "Teose põhihelistikuks on " + results['key'] + ", kuid leiti ka järgnevad helistikud: " + ", ".join(keys) + ". "
    elif len(keys) == 1:
        text += "Teose helistikuks on " + results['key'] + ". "
    if min_tempo_term == max_tempo_term:
        text += "Antud teos on esitatud ligikaudu ühtlases tempos. Keskmiselt on teose tempo " + str(
            int(min)) + " lööki minutis ehk " + min_tempo_term + ". "
    else:
        text += "Pala esitamise kiirus vaheldub " + str(min) + " lööki minutis ehk " + min_tempo_term + " ja " + str(
            max) + " lööki minutis ehk " + max_tempo_term + " vahel. " "Keskmiselt on teose tempo " + str(
            int((min + max) / 2)) + " lööki minutis ehk " + just_get_term(int((min + max) / 2)) + ". "

    text += "\n\n"

    vorm = results['structure_name']
    if len(segm_array) > 1:
        text += "Teosest leiti " + str(len(segm_array)) + " erinevat teemat. "
        text += "Nendest peateema esineb " + str(segm_array.get("A")) + (
            " korda. " if segm_array.get("A") > 1 else " kord. ")

    else:
        text += "Teosest leiti ainut üks teema, mis esineb " + str(segm_array.get("A")) + (
            " korda. " if segm_array.get("A") > 1 else " kord. ")
    text += "Analüüsitud vormidest on antud teose vormile kõige lähem " + vorm + ". "
    text += results['structure_desc']

    print(text)

    results['text'] = text



"""
results = {'segmentation': [('A', 0, 377810), ('A', 377810, 758692), ('B', 758692, 1197935), ('B', 1197935, 1652536), ('C', 1652536, 2638529), ('A', 2638529, 3004053), ('A', 3004053, 3329645), ('B', 3329645, 3781175), ('B', 3781175, 4238848)], 'segmentation_perc': [['A', 8.91303486230221], ['A', 8.98550738313806], ['B', 10.36232013981157], ['B', 10.724635561360067], ['C', 23.260871821777993], ['A', 8.623191961589564], ['A', 7.681143555985022], ['B', 10.652186631839594], ['B', 10.797108082195917]], 'tempos': [[144.0, 'Allegro'], [144.0, 'Allegro'], [129.0, 'Allegro'], [144.0, 'Allegro'], [152.0, 'Allegro'], [92.0, 'Andante'], [96.0, 'Andante'], [136.0, 'Allegro'], [144.0, 'Allegro']], 'structure_name': 'variatsioonivorm', 'structure_desc': 'TBA', 'key': 'Helistikku ei leitud', 'keys': ['G duur', 'B duur', 'g moll', 'C duur', 'G duur', 'Helistikku ei leitud', 'Helistikku ei leitud', 'Helistikku ei leitud', 'G duur'], 'beat': 143.5546875, 'tempo_term': 'Allegro', 'title and artist': 'Rick Astley - Never Gonna Give You Up ', 'chorus': 'aa35ad00-18d1-46a9-bc2d-105a93eaaf46main_theme.wav', 'start_sec': 139.66713840559265}


make_text(results)"""

# print(calculate_timestamps(22050, [('A', 0, 365541), ('B', 365541, 2107238), ('A', 2107238, 2675517), ('C', 2675517, 4527798), ('D', 4527798, 5234307), ('E', 5234307, 6662683), ('D', 6662683, 7043584)]))