import librosa
import numpy as np
import scipy

N_FFT = 2 ** 14


def create_chroma(input_file, n_fft=N_FFT):
    """
    Generate the notes present in a song
    Returns: tuple of 12 x n chroma, song wav data, sample rate (usually 22050)
             and the song length in seconds
    """
    y, sr = librosa.load(input_file)
    # y, index = librosa.effects.trim(y)
    song_length_sec = y.shape[0] / float(sr)
    S = np.abs(librosa.stft(y, n_fft=n_fft)) ** 2
    chroma = librosa.feature.chroma_stft(S=S, sr=sr)

    return chroma, y, sr, song_length_sec


def ti_ssm2(chroma):  # TODO: custom funcs?
    # ssm = librosa.segment.recurrence_matrix(chroma, mode='affinity') # docsi alusel vajab veel self=True aga idk, esimene peab olema iseendaga
    ssm = chroma.T @ chroma
    ssm = librosa.segment.path_enhance(ssm, 51)  # smooth dat shit, vb annab paramsidega mängida
    for shift in range(1, 12):
        shifted = np.roll(chroma, shift, axis=0)
        #    cs = librosa.segment.cross_similarity(chroma, shifted, mode='affinity')
        cs = chroma.T @ shifted
        cs = librosa.segment.path_enhance(cs, 51)
        ssm = np.maximum(ssm, cs)
    return ssm


def time_lag(ssm):
    return librosa.segment.recurrence_to_lag(ssm, pad=False)


def threshold_matrix(S, thresh=[0.1, 0.1], scale=False, penalty=0.0):
    """Treshold matrix in a relative fashion

    Notebook: C4/C4S2_SSM-Thresholding.ipynb

    Args:
        S (np.ndarray): Input matrix
        thresh (float or list): Treshold (meaning depends on strategy)
        scale (bool): If scale=True, then scaling of positive values to range [0,1] (Default value = False)
        penalty (float): Set values below treshold to value specified (Default value = 0.0)


    Returns:
        S_thresh (np.ndarray): Thresholded matrix
    """
    if np.min(S) < 0:
        raise Exception('All entries of the input matrix must be nonnegative')

    N, M = S.shape

    thresh_rel_row = thresh[0]
    thresh_rel_col = thresh[1]
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


def filter_diag_sm(S, L):
    """Path smoothing of similarity matrix by forward filtering along main diagonal

    Notebook: C4/C4S2_SSM-PathEnhancement.ipynb

    Args:
        S (np.ndarray): Similarity matrix (SM)
        L (int): Length of filter

    Returns:
        S_L (np.ndarray): Smoothed SM
    """
    N = S.shape[0]
    M = S.shape[1]
    S_L = np.zeros((N, M))
    S_extend_L = np.zeros((N + L, M + L))
    S_extend_L[0:N, 0:M] = S
    for pos in range(0, L):
        S_L = S_L + S_extend_L[pos:(N + pos), pos:(M + pos)]
    S_L = S_L / L
    return S_L


def line_dilation(ssm):
    return scipy.ndimage.grey_dilation(ssm, size=(10, 10))

def custom_denoise(time_lag_matrix):
    new_matrix = np.copy(time_lag_matrix)
    empty = True
    for i in range(new_matrix.shape[0]):
        start = 0
        end = 0
        for j in range(new_matrix.shape[1]):
            end = j
            if new_matrix[i][j] != 0 and empty:
                if end - start < 20:
                    new_matrix[i][start: end].fill(1)
                empty = False
                start = j
                end = j
            if new_matrix[i][j] == 0 and not empty:
                start = j
                end = j
                empty = True

    empty = True
    for i in range(new_matrix.shape[0]):
        start = 0
        end = 0
        for j in range(new_matrix.shape[1]):
            end = j
            if new_matrix[i][j] != 0 and empty:
                empty = False
                start = j
                end = j
            if new_matrix[i][j] == 0 and not empty:
                if end - start < 50:
                    new_matrix[i][start: end].fill(0)
                start = j
                end = j
                empty = True
    

    return new_matrix
