import librosa
import numpy as np
import scipy.signal
import soundfile as sf
from abc import ABCMeta, abstractmethod
from math import sqrt

# Denoising size in seconds
SMOOTHING_SIZE_SEC = 2.5

# Number of samples to consider in one chunk.
# Smaller values take more time, but are more accurate
N_FFT = 2 ** 14

# For line detection
LINE_THRESHOLD = 0.15
MIN_LINES = 8
NUM_ITERATIONS = 8

# We allow an error proportional to the length of the clip
OVERLAP_PERCENT_MARGIN = 0.2


def local_maxima_rows(denoised_time_lag):
    """Find rows whose normalized sum is a local maxima"""
    row_sums = np.sum(denoised_time_lag, axis=1)
    divisor = np.arange(row_sums.shape[0], 0, -1)
    normalized_rows = row_sums / divisor
    local_minima_rows = scipy.signal.argrelextrema(normalized_rows, np.greater)
    return local_minima_rows[0]


def detect_lines(denoised_time_lag, rows, min_length_samples):
    """Detect lines in the time lag matrix. Reduce the threshold until we find enough lines"""
    cur_threshold = LINE_THRESHOLD
    for _ in range(NUM_ITERATIONS):
        line_segments = detect_lines_helper(denoised_time_lag, rows,
                                            cur_threshold, min_length_samples)
        if len(line_segments) >= MIN_LINES:
            return line_segments
        cur_threshold *= 0.95

    return line_segments


def detect_lines_helper(denoised_time_lag, rows, threshold,
                        min_length_samples):
    """Detect lines where at least min_length_samples are above threshold"""
    num_samples = denoised_time_lag.shape[0]
    line_segments = []
    cur_segment_start = None
    for row in rows:
        if row < min_length_samples:
            continue
        for col in range(row, num_samples):
            if denoised_time_lag[row, col] > threshold:
                if cur_segment_start is None:
                    cur_segment_start = col
            else:
                if (cur_segment_start is not None
                ) and (col - cur_segment_start) > min_length_samples:
                    line_segments.append(Line(cur_segment_start, col, row))
                cur_segment_start = None
    return line_segments


def count_overlapping_lines(lines, margin, min_length_samples):
    """Look at all pairs of lines and see which ones overlap vertically and diagonally"""
    line_scores = {}
    for line in lines:
        line_scores[line] = 0

    # Iterate over all pairs of lines
    for line_1 in lines:
        for line_2 in lines:
            # If line_2 completely covers line_1 (with some margin), line_1 gets a point
            lines_overlap_vertically = (
                                               line_2.start < (line_1.start + margin)) and (
                                               line_2.end > (line_1.end - margin)) and (
                                               abs(line_2.lag - line_1.lag) > min_length_samples)

            lines_overlap_diagonally = (
                                               (line_2.start - line_2.lag) < (line_1.start - line_1.lag + margin)) and (
                                               (line_2.end - line_2.lag) > (line_1.end - line_1.lag - margin)) and (
                                               abs(line_2.lag - line_1.lag) > min_length_samples)

            if lines_overlap_vertically or lines_overlap_diagonally:
                line_scores[line_1] += 1

    return line_scores


def best_segment(line_scores):
    """Return the best line, sorted first by chorus matches, then by duration"""
    lines_to_sort = []
    for line in line_scores:
        lines_to_sort.append((line, line_scores[line], line.end - line.start))

    lines_to_sort.sort(key=lambda x: (x[1], x[2]), reverse=True)
    best_tuple = lines_to_sort[0]
    return best_tuple[0]


def draw_lines(num_samples, sample_rate, lines):
    """Debugging function to draw detected lines in black"""
    lines_matrix = np.zeros((num_samples, num_samples))
    for line in lines:
        lines_matrix[line.lag:line.lag + 4, line.start:line.end + 1] = 1

    # Import here since this function is only for debugging
    import librosa.display
    import matplotlib.pyplot as plt
    librosa.display.specshow(
        lines_matrix,
        y_axis='time',
        x_axis='time',
        sr=sample_rate / (N_FFT / 2048))
    plt.colorbar()
    plt.set_cmap("hot_r")
    plt.show()


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


def find_chorus(chroma, sr, song_length_sec, clip_length):
    """
    Find the most repeated chorus
    Args:
        chroma: 12 x n frequency chromogram
        sr: sample rate of the song, usually 22050
        song_length_sec: length in seconds of the song (lost in processing chroma)
        clip_length: minimum length in seconds we want our chorus to be (at least 10-15s)
    Returns: Time in seconds of the start of the best chorus
    """
    num_samples = chroma.shape[1]

    time_time_similarity = TimeTimeSimilarityMatrix(chroma, sr)
    time_lag_similarity = TimeLagSimilarityMatrix(chroma, sr)

    # Denoise the time lag matrix
    chroma_sr = num_samples / song_length_sec
    smoothing_size_samples = int(SMOOTHING_SIZE_SEC * chroma_sr)
    time_lag_similarity.denoise(time_time_similarity.matrix,
                                smoothing_size_samples)

    # Detect lines in the image
    clip_length_samples = clip_length * chroma_sr
    candidate_rows = local_maxima_rows(time_lag_similarity.matrix)
    lines = detect_lines(time_lag_similarity.matrix, candidate_rows,
                         clip_length_samples)
    if len(lines) == 0:
        print("No choruses were detected. Try a smaller search duration")
        return None
    line_scores = count_overlapping_lines(
        lines, OVERLAP_PERCENT_MARGIN * clip_length_samples,
        clip_length_samples)
    best_chorus = best_segment(line_scores)
    return best_chorus.start / chroma_sr


def find_and_output_chorus(input_file, output_file, clip_length=15):
    """
    Finds the most repeated chorus from input_file and outputs to output file.
    Args:
        input_file: string specifying the input file
        output_file: string where to write the chorus (wav only)
            None means don't write anything
        clip_length: minimum length in seconds of the chorus
    Returns: Time in seconds of the start of the best chorus
    """
    chroma, song_wav_data, sr, song_length_sec = create_chroma(input_file)
    chorus_start = find_chorus(chroma, sr, song_length_sec, clip_length)
    if chorus_start is None:
        return

    print("Best chorus found at {0:g} min {1:.2f} sec".format(
        chorus_start // 60, chorus_start % 60))

    if output_file is not None:
        chorus_wave_data = song_wav_data[int(chorus_start * sr): int((chorus_start + clip_length) * sr)]
        sf.write(output_file, chorus_wave_data, sr)
        # librosa.output.write_wav(output_file, chorus_wave_data, sr)

    return chorus_start


class SimilarityMatrix(object):
    """Abstract class for our time-time and time-lag similarity matrices"""

    __metaclass__ = ABCMeta

    def __init__(self, chroma, sample_rate):
        self.chroma = chroma
        self.sample_rate = sample_rate  # sample_rate of the audio, almost always 22050
        self.matrix = self.compute_similarity_matrix(chroma)

    @abstractmethod
    def compute_similarity_matrix(self, chroma):
        """"
        The specific type of similarity matrix we want to compute
        Args:
            chroma: 12 x n numpy array of musical notes present at every time step
        """
        pass

    def display(self):
        import librosa.display
        import matplotlib.pyplot as plt
        librosa.display.specshow(
            self.matrix,
            y_axis='time',
            x_axis='time',
            sr=self.sample_rate / (N_FFT / 2048))
        plt.colorbar()
        plt.set_cmap("hot_r")
        plt.show()


class TimeTimeSimilarityMatrix(SimilarityMatrix):
    """
    Class for the time time similarity matrix where sample (x,y) represents how similar
    are the song frames x and y
    """

    def compute_similarity_matrix(self, chroma):
        """Optimized way to compute the time-time similarity matrix with numpy broadcasting"""
        broadcast_x = np.expand_dims(chroma, 2)  # (12 x n x 1)
        broadcast_y = np.swapaxes(np.expand_dims(chroma, 2), 1,
                                  2)  # (12 x 1 x n)
        time_time_matrix = 1 - (np.linalg.norm(
            (broadcast_x - broadcast_y), axis=0) / sqrt(12))
        return time_time_matrix

    def compute_similarity_matrix_slow(self, chroma):
        """Slow but straightforward way to compute time time similarity matrix"""
        num_samples = chroma.shape[1]
        time_time_similarity = np.zeros((num_samples, num_samples))
        for i in range(num_samples):
            for j in range(num_samples):
                # For every pair of samples, check similarity
                time_time_similarity[i, j] = 1 - (
                        np.linalg.norm(chroma[:, i] - chroma[:, j]) / sqrt(12))

        return time_time_similarity


class TimeLagSimilarityMatrix(SimilarityMatrix):
    """
    Class to hold the time lag similarity matrix where sample (x,y) represents the
    similarity of song frames x and (x-y)
    """

    def compute_similarity_matrix(self, chroma):
        """Optimized way to compute the time-lag similarity matrix"""
        num_samples = chroma.shape[1]
        broadcast_x = np.repeat(
            np.expand_dims(chroma, 2), num_samples + 1, axis=2)

        # We create the lag effect by tiling the samples but reshaping with an extra column
        # so that subsequent rows are offset by one each time
        circulant_y = np.tile(chroma, (1, num_samples + 1)).reshape(
            12, num_samples, num_samples + 1)
        time_lag_similarity = 1 - (np.linalg.norm(
            (broadcast_x - circulant_y), axis=0) / sqrt(12))
        time_lag_similarity = np.rot90(time_lag_similarity, k=1, axes=(0, 1))
        return time_lag_similarity[:num_samples, :num_samples]

    def compute_similarity_matrix_slow(self, chroma):
        """Slow but straightforward way to compute time lag similarity matrix"""
        num_samples = chroma.shape[1]
        time_lag_similarity = np.zeros((num_samples, num_samples))
        for i in range(num_samples):
            for j in range(i + 1):
                # For every pair of samples, check similarity using lag
                # [j, i] because numpy indexes by column then row
                time_lag_similarity[j, i] = 1 - (
                        np.linalg.norm(chroma[:, i] - chroma[:, i - j]) / sqrt(12))

        return time_lag_similarity

    def denoise(self, time_time_matrix, smoothing_size):
        """
        Emphasize horizontal lines by suppressing vertical and diagonal lines. We look at 6
        moving averages (left, right, up, down, upper diagonal, lower diagonal). For lines, the
        left or right average should be much greater than the other ones.
        Args:
            time_time_matrix: n x n numpy array to quickly compute diagonal averages
            smoothing_size: smoothing size in samples (usually 1-2 sec is good)
        """
        n = self.matrix.shape[0]

        # Get the horizontal strength at every sample
        horizontal_smoothing_window = np.ones(
            (1, smoothing_size)) / smoothing_size
        horizontal_moving_average = scipy.signal.convolve2d(
            self.matrix, horizontal_smoothing_window, mode="full")
        left_average = horizontal_moving_average[:, 0:n]
        right_average = horizontal_moving_average[:, smoothing_size - 1:]
        max_horizontal_average = np.maximum(left_average, right_average)

        # Get the vertical strength at every sample
        vertical_smoothing_window = np.ones((smoothing_size,
                                             1)) / smoothing_size
        vertical_moving_average = scipy.signal.convolve2d(
            self.matrix, vertical_smoothing_window, mode="full")
        down_average = vertical_moving_average[0:n, :]
        up_average = vertical_moving_average[smoothing_size - 1:, :]

        # Get the diagonal strength of every sample from the time_time_matrix.
        # The key insight is that diagonal averages in the time lag matrix are horizontal
        # lines in the time time matrix
        diagonal_moving_average = scipy.signal.convolve2d(
            time_time_matrix, horizontal_smoothing_window, mode="full")
        ur_average = np.zeros((n, n))
        ll_average = np.zeros((n, n))
        for x in range(n):
            for y in range(x):
                ll_average[y, x] = diagonal_moving_average[x - y, x]
                ur_average[y, x] = diagonal_moving_average[x - y,
                                                           x + smoothing_size - 1]

        non_horizontal_max = np.maximum.reduce([down_average, up_average, ll_average, ur_average])
        non_horizontal_min = np.minimum.reduce([up_average, down_average, ll_average, ur_average])

        # If the horizontal score is stronger than the vertical score, it is considered part of a line
        # and we only subtract the minimum average. Otherwise subtract the maximum average
        suppression = (max_horizontal_average > non_horizontal_max) * non_horizontal_min + (
                max_horizontal_average <= non_horizontal_max) * non_horizontal_max

        # Filter it horizontally to remove any holes, and ignore values less than 0
        denoised_matrix = scipy.ndimage.filters.gaussian_filter1d(
            np.triu(self.matrix - suppression), smoothing_size, axis=1)
        denoised_matrix = np.maximum(denoised_matrix, 0)
        denoised_matrix[0:5, :] = 0

        self.matrix = denoised_matrix


class Line(object):
    def __init__(self, start, end, lag):
        self.start = start
        self.end = end
        self.lag = lag

    def __repr__(self):
        return "Line ({} {} {})".format(self.start, self.end, self.lag)
