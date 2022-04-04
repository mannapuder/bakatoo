import librosa
import numpy as np
import scipy.signal
import soundfile as sf
from abc import ABCMeta, abstractmethod
from math import sqrt


def create_chroma(input_file, n_fft=N_FFT):
    """
    Generate the notes present in a song
    Returns: tuple of 12 x n chroma, song wav data, sample rate (usually 22050)
             and the song length in seconds
    """
    y, sr = librosa.load(input_file)
    song_length_sec = y.shape[0] / float(sr)
    S = np.abs(librosa.stft(y, n_fft=n_fft)) ** 2
    chroma = librosa.feature.chroma_stft(S=S, sr=sr)

    return chroma, y, sr, song_length_sec