import librosa
import numpy as np
import scipy
from scipy.cluster import hierarchy


def get_segmentation(y, sr, results):
    # Test segmentation
    print("Here")
    final = main_algorithm(y, sr)
    print("Done")
    print(final)
    percentages = []
    length = final[-1][2]
    for segm in final:
        percentages.append([segm[0], (segm[2]-segm[1])*100/length])

    results["segmentation"] = final
    results["segmentation_perc"] = percentages

    return final, percentages


def main_algorithm(y, orig_sr):
    y = np.copy(y)
    sr = 22050
    if orig_sr != sr:
        y = librosa.resample(y, orig_sr=orig_sr, target_sr=sr)

    y_harm = librosa.effects.harmonic(y=y, margin=8)

    chroma_harm = librosa.feature.chroma_cqt(y=y_harm, sr=sr, hop_length=2 ** 6 * round(sr * 0.139 / 2 ** 6))
    chroma_filter = np.minimum(chroma_harm,
                               librosa.decompose.nn_filter(chroma_harm, aggregate=np.median, metric='cosine'))

    chroma_stack = librosa.feature.stack_memory(chroma_filter, n_steps=10, delay=3)
    ssm = librosa.segment.recurrence_matrix(chroma_stack).astype(float)

    ssm_smooth = librosa.segment.path_enhance(ssm, 51)  # TODO: 51 is arbitrary

    lag = librosa.segment.recurrence_to_lag(ssm_smooth, pad=False)
    gaussed = scipy.ndimage.gaussian_filter1d(lag, lag.shape[1] // 30, axis=1)

    N = gaussed.shape[0]
    nov = np.zeros(N)
    for n in range(N - 1):
        nov[n] = np.linalg.norm(gaussed[:, n + 1] - gaussed[:, n])
    _min = nov.min()
    nov = (nov - _min) / (nov.max() - _min)

    median_len = 61
    offset_rel = 0.01
    sigma = 20

    offset = nov.mean() * offset_rel
    x = scipy.ndimage.gaussian_filter1d(nov, sigma=sigma)
    threshold_local = scipy.ndimage.median_filter(x, size=median_len) + offset
    peaks = []
    for i in range(1, x.shape[0] - 1):
        if x[i - 1] < x[i] and x[i] > x[i + 1]:
            if x[i] > threshold_local[i]:
                peaks.append(i)
    peaks = np.array(peaks)

    sections = []
    prev = 0
    for peak in peaks:
        sections.append((prev, peak))
        prev = peak
    sections.append((prev, gaussed.shape[0]))

    section_difference = np.zeros((len(sections), len(sections)))
    for i1, (x1, x2) in enumerate(sections):
        for i2, (y1, y2) in enumerate(sections):
            section_difference[i1, i2] = 1 - ssm[x1:x2, y1:y2].mean()
    _min = section_difference.min()
    section_difference = (section_difference - _min) / (section_difference.max() - _min)

    distances = section_difference[np.triu_indices_from(section_difference, 1)]
    Z = hierarchy.linkage(distances, method='centroid')  # i don't know why but centroid works

    for a in range(100, 1, -1):
        t = a / 100
        labels = hierarchy.fcluster(Z, t=t)  # i don't know why but 1 works
        if max(labels) > 1:
            break
    print(labels)

    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    label_mapping = {}
    final = []
    original_index_mult = len(y) / ssm.shape[0]
    for label, section in zip(labels, sections):
        if label in label_mapping:
            letter = label_mapping[label]
        else:
            letter = letters[len(label_mapping)]
            label_mapping[label] = letter
        final.append((letter, int(section[0] * original_index_mult), int(section[1] * original_index_mult)))

    return final
