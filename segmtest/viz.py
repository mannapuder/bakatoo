import functools
import os

import matplotlib.pyplot as plt
import librosa
import matplotlib.widgets
from functools import partial
from scipy import signal, ndimage
from segmtest.util import *

FILEDIR = "C:\\Users\\Anna Talas\\PycharmProjects\\bakatoo\\uploads"  # mussikaust
files = {fn: load_file(os.path.join(FILEDIR, fn)) for fn in os.listdir(FILEDIR)}


def pick_file(file):
    return files[file]


class OptionsParameter:
    def __init__(self, options: dict, default=None, label=None):
        self.keys = list(options.keys())
        self.options = options
        self.selected = default
        self.label = label

    def add_widget(self, ax, cb):
        button = matplotlib.widgets.RadioButtons(ax, self.options.keys(), self.keys.index(self.selected))
        button.on_clicked(cb)
        return button

    def update(self, selected):
        self.selected = selected

    def value(self):
        return self.options[self.selected]


class IntParameter:
    def __init__(self, _range: range, default=None, label=None):
        self._range = _range
        self.selected = default
        self.label = label

    def add_widget(self, ax, cb):
        slider = matplotlib.widgets.Slider(ax, label=self.label, valmin=self._range.start,
                                           valmax=self._range.stop,
                                           valstep=self._range.step,
                                           valinit=self.selected)
        slider.on_changed(cb)
        return slider

    def update(self, selected):
        self.selected = selected

    def value(self):
        return self.selected


class FloatParameter:
    def __init__(self, start, stop, default=None, label=None):
        self._range = (start, stop)
        self.selected = default
        self.label = label

    def add_widget(self, ax, cb):
        slider = matplotlib.widgets.Slider(ax, label=self.label, valmin=self._range[0],
                                           valmax=self._range[1],
                                           valinit=self.selected)
        slider.on_changed(cb)
        return slider

    def update(self, selected):
        self.selected = selected

    def value(self):
        return self.selected


def chroma(y, sr, n_fft_exponent=14):
    n_fft = 2 ** n_fft_exponent
    s = np.abs(librosa.stft(y, n_fft=n_fft)) ** 2
    chroma = librosa.feature.chroma_stft(S=s, sr=sr)
    return chroma, sr


def ssm(chroma, smoothing_filter_length=51, transposition_invariant=True):
    ssm = chroma.T @ chroma
    if smoothing_filter_length > 0:
        ssm = librosa.segment.path_enhance(ssm, smoothing_filter_length)
    if transposition_invariant:
        for shift in range(1, 12):
            shifted = np.roll(chroma, shift, axis=0)
            cs = chroma.T @ shifted
            if smoothing_filter_length > 0:
                cs = librosa.segment.path_enhance(cs, smoothing_filter_length)
            ssm = np.maximum(ssm, cs)
    return ssm


def time_lag(ssm):
    return librosa.segment.recurrence_to_lag(ssm, pad=False)


def downsample_2d(X, sr, filter_length, down_sampling=10, window_type='boxcar'):
    if down_sampling == 0:
        return X
    kernel = np.expand_dims(signal.get_window(window_type, filter_length), axis=0)
    X_smooth = (signal.convolve(X, kernel, mode='same') / filter_length)[:, ::down_sampling]
    sr /= down_sampling
    return X_smooth


def downsample_1d(X, sr, filter_length, down_sampling=10, window_type='boxcar'):
    if down_sampling == 0:
        return X, sr
    kernel = signal.get_window(window_type, filter_length)
    X_smooth = (signal.convolve(X, kernel, mode='same') / filter_length)[::down_sampling]
    sr /= down_sampling
    return X_smooth, sr


def ssm_novelty(ssm, L=10, var=0.5):
    kernel = compute_kernel_checkerboard_gaussian(L, var)
    n = ssm.shape[0]
    m = 2 * L + 1
    nov = np.zeros(n)
    s_padded = np.pad(ssm, L, mode='constant')
    for n in range(n):
        nov[n] = np.sum(s_padded[n:n + m, n:n + m] * kernel)
    return nov


def tl_novelty(ssm):
    N = ssm.shape[0]
    nov = np.zeros(N)
    for n in range(N - 1):
        nov[n] = np.linalg.norm(ssm[:, n + 1] - ssm[:, n])
    return nov


def median_filter(m, width, height):
    if width == height == 1:
        return m
    return ndimage.median_filter(m, (height, width))


def gaussian_filter(m, sigma=4):
    if sigma == 0:
        return m
    return ndimage.gaussian_filter(m, sigma)


def threshold_matrix(S, thresh, strategy='absolute', scale=False, penalty=0.0, binarize=False):
    """Treshold matrix in a relative fashion

    Notebook: C4/C4S2_SSM-Thresholding.ipynb

    Args:
        S (np.ndarray): Input matrix
        thresh (float or list): Treshold (meaning depends on strategy)
        strategy (str): Thresholding strategy ('absolute', 'relative', 'local') (Default value = 'absolute')
        scale (bool): If scale=True, then scaling of positive values to range [0,1] (Default value = False)
        penalty (float): Set values below treshold to value specified (Default value = 0.0)
        binarize (bool): Binarizes final matrix (positive: 1; otherwise: 0) (Default value = False)

    Returns:
        S_thresh (np.ndarray): Thresholded matrix
    """
    if thresh == 0.0:
        return S
    if np.min(S) < 0:
        raise Exception('All entries of the input matrix must be nonnegative')

    S_thresh = np.copy(S)
    N, M = S.shape
    num_cells = N * M

    if strategy == 'absolute':
        thresh_abs = thresh
        S_thresh[S_thresh < thresh] = 0

    if strategy == 'relative':
        thresh_rel = thresh
        num_cells_below_thresh = int(np.round(S_thresh.size * (1 - thresh_rel)))
        if num_cells_below_thresh < num_cells:
            values_sorted = np.sort(S_thresh.flatten('F'))
            thresh_abs = values_sorted[num_cells_below_thresh]
            S_thresh[S_thresh < thresh_abs] = 0
        else:
            S_thresh = np.zeros([N, M])

    if strategy == 'local':
        # can't have list param, maybe in the future
        # thresh_rel_row = thresh[0]
        # thresh_rel_col = thresh[1]
        thresh_rel_row = thresh
        thresh_rel_col = thresh
        S_binary_row = np.zeros([N, M])
        num_cells_row_below_thresh = int(np.round(M * (1 - thresh_rel_row)))
        for n in range(N):
            row = S[n, :]
            values_sorted = np.sort(row)
            if num_cells_row_below_thresh < M:
                thresh_abs = values_sorted[num_cells_row_below_thresh]
                S_binary_row[n, :] = (row >= thresh_abs)
        S_binary_col = np.zeros([N, M])
        num_cells_col_below_thresh = int(np.round(N * (1 - thresh_rel_col)))
        for m in range(M):
            col = S[:, m]
            values_sorted = np.sort(col)
            if num_cells_col_below_thresh < N:
                thresh_abs = values_sorted[num_cells_col_below_thresh]
                S_binary_col[:, m] = (col >= thresh_abs)
        S_thresh = S * S_binary_row * S_binary_col

    if scale:
        cell_val_zero = np.where(S_thresh == 0)
        cell_val_pos = np.where(S_thresh > 0)
        if len(cell_val_pos[0]) == 0:
            min_value = 0
        else:
            min_value = np.min(S_thresh[cell_val_pos])
        max_value = np.max(S_thresh)
        # print('min_value = ', min_value, ', max_value = ', max_value)
        if max_value > min_value:
            S_thresh = np.divide((S_thresh - min_value), (max_value - min_value))
            if len(cell_val_zero[0]) > 0:
                S_thresh[cell_val_zero] = penalty
        else:
            print('Condition max_value > min_value is voliated: output zero matrix')

    if binarize:
        S_thresh[S_thresh > 0] = 1
        S_thresh[S_thresh < 0] = 0
    return S_thresh


def peak_picking_MSAF(x, median_len=16, offset_rel=0.05, sigma=4.0):
    """Peak picking strategy following MSFA using an adaptive threshold (https://github.com/urinieto/msaf)
    https://github.com/meinardmueller/libfmp/blob/1f25dfaf3de3b8ed49713d79760078f058a8c8b8/libfmp/c6/c6s1_peak_picking.py

    Notebook: C6/C6S1_PeakPicking.ipynb

    Args:
        x (np.ndarray): Input function
        median_len (int): Length of media filter used for adaptive thresholding (Default value = 16)
        offset_rel (float): Additional offset used for adaptive thresholding (Default value = 0.05)
        sigma (float): Variance for Gaussian kernel used for smoothing the novelty function (Default value = 4.0)

    Returns:
        peaks (np.ndarray): Peak positions
        x (np.ndarray): Local threshold
        threshold_local (np.ndarray): Filtered novelty curve
    """
    offset = x.mean() * offset_rel
    x = ndimage.gaussian_filter1d(x, sigma=sigma)
    threshold_local = ndimage.median_filter(x, size=median_len) + offset
    peaks = []
    for i in range(1, x.shape[0] - 1):
        if x[i - 1] < x[i] and x[i] > x[i + 1]:
            if x[i] > threshold_local[i]:
                peaks.append(i)
    peaks = np.array(peaks)
    return peaks  # , x, threshold_local


def plot_ssm(ssm):
    if 'ssm' in plot_cache:
        plot_cache['ssm'].remove()
    plot_cache['ssm'] = axs[0, 0].imshow(np.flipud(ssm), cmap='magma', aspect='auto')


def plot_tl(tl):
    if 'tl' in plot_cache:
        plot_cache['tl'].remove()
    plot_cache['tl'] = axs[0, 1].imshow(np.flipud(tl), cmap='magma', aspect='auto')


def plot_ssm_novelty(nov):
    if 'ssm_novelty' in plot_cache:
        for el in plot_cache['ssm_novelty']:
            el.remove()
    plot_cache['ssm_novelty'] = axs[1, 0].plot(nov)


def plot_tl_novelty(nov):
    if 'tl_novelty' in plot_cache:
        for el in plot_cache['tl_novelty']:
            el.remove()
    plot_cache['tl_novelty'] = axs[1, 1].plot(nov)


def plot_ssm_peaks(peaks):
    c = plot_cache.get('ssm_peaks', False)
    while c:
        c.pop().remove()
    for peak in peaks:
        plot_cache.setdefault('ssm_peaks', []).append(axs[1, 0].axvline(peak, ls='--', c='red'))


def plot_tl_peaks(peaks):
    c = plot_cache.get('tl_peaks', False)
    while c:
        c.pop().remove()
    for peak in peaks:
        plot_cache.setdefault('tl_peaks', []).append(axs[1, 1].axvline(peak, ls='--', c='red'))


# häkk praegu
peaks_tl = lambda *args, **kwargs: peak_picking_MSAF(*args, **kwargs)
peaks_ssm = lambda *args, **kwargs: peak_picking_MSAF(*args, **kwargs)

param_map = {
    pick_file: {'file': OptionsParameter({k: k for k, _ in files.items()}, list(files)[0], 'file')},
    downsample_1d: {'filter_length': IntParameter(range(1, 200, 2), 1, '1d_filter_length'),
                    'down_sampling': IntParameter(range(0, 20), 0, '1d_down_sampling')},
    chroma: {'n_fft_exponent': IntParameter(range(14, 25), 14, 'n_fft_exponent')},  # võib errordada
    downsample_2d: {'filter_length': IntParameter(range(1, 200, 2), 1, '1d_filter_length'),
                    'down_sampling': IntParameter(range(0, 20), 0, '1d_down_sampling')},
    ssm: {'smoothing_filter_length': IntParameter(range(0, 100, 3), 0, 'smoothing_filter_length'),
          'transposition_invariant': OptionsParameter({'true': True, 'false': False}, 'false',
                                                      'transposition_invariant')},
    median_filter: {'width': IntParameter(range(1, 100), 1, 'width'),
                    'height': IntParameter(range(1, 100), 1, 'height')},
    gaussian_filter: {'sigma': IntParameter(range(0, 100), 0, 'sigma')},
    threshold_matrix: {'thresh': FloatParameter(0, 5.0, 0, 'thresh'),
                       'strategy': OptionsParameter({'absolute': 'absolute', 'relative': 'relative', 'local': 'local'},
                                                    'absolute', 'strategy'),
                       'scale': OptionsParameter({'true': True, 'false': False}, 'false', 'scale'),
                       'penalty': FloatParameter(0.0, 100.0, 0.0, 'penalty'),
                       'binarize': OptionsParameter({'true': True, 'false': False}, 'false', 'binarize')},
    ssm_novelty: {'L': IntParameter(range(1, 100), 10, 'L'),
                  'var': FloatParameter(0.1, 10.0, 0.5, 'var')},
    peaks_tl: {'median_len': IntParameter(range(1, 100), 16, 'tl_median_len'),
               'offset_rel': FloatParameter(0.01, 1.0, 0.05, 'tl_offset_rel'),
               'sigma': FloatParameter(1.0, 50.0, 4.0, 'tl_sigma')},
    peaks_ssm: {'median_len': IntParameter(range(1, 100), 16, 'ssm_median_len'),
                'offset_rel': FloatParameter(0.01, 1.0, 0.05, 'ssm_offset_rel'),
                'sigma': FloatParameter(1.0, 50.0, 4.0, 'ssm_sigma')}
}

nexts = {
    pick_file: [downsample_1d],
    downsample_1d: [chroma],
    chroma: [downsample_2d],
    downsample_2d: [ssm],
    ssm: [median_filter],
    median_filter: [gaussian_filter],
    gaussian_filter: [threshold_matrix],
    threshold_matrix: [plot_ssm, ssm_novelty, time_lag],
    ssm_novelty: [plot_ssm_novelty, peaks_ssm],
    peaks_ssm: [plot_ssm_peaks],
    time_lag: [plot_tl, tl_novelty],
    tl_novelty: [plot_tl_novelty, peaks_tl],
    #peaks_tl: [plot_tl_peaks]
}

cache = {}


def run_from(fn, args=None):
    print(fn)
    if args is None:
        args = cache.get(fn, [])
    else:
        cache[fn] = args
    kwargs = {k: v.value() for k, v in param_map[fn].items()} if fn in param_map else {}
    if isinstance(args, tuple) or isinstance(args, list):
        res = fn(*args, **kwargs)
    else:
        res = fn(args, **kwargs)
    if fn not in nexts:
        return
    for f in nexts[fn]:
        run_from(f, res)


def update(fn, param, label):
    param_map[fn][param].update(label)
    run_from(fn)
    fig.canvas.draw()


plot_cache = {}
ctrl_panel = plt.figure()
total_tweaks = sum(len(p) for p in param_map.values())
i = 0
tweak_refs = []  # fight the evil garbage collector
for fn in param_map:
    for label, param in param_map[fn].items():
        i += 1
        tweak_ax = ctrl_panel.add_axes([0.2, (1 / total_tweaks) * i, 0.6, (1 / total_tweaks)])
        tweak_refs.append(param.add_widget(tweak_ax, functools.partial(update, fn, label)))

fig = plt.figure()
gs = fig.add_gridspec(2, 2)
axs = gs.subplots(sharex='col', sharey='row')

run_from(pick_file)

plt.show()
