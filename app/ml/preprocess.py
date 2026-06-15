import numpy as np
from scipy.signal import resample, find_peaks


def segment_signal(signal_250hz):
    target_length = int(len(signal_250hz) / 2)
    signal_125hz = resample(signal_250hz, target_length)

    peaks, _ = find_peaks(signal_125hz, distance=60, height=np.mean(signal_125hz))

    segments = []
    valid_peaks = []

    for peak in peaks:
        start = peak - 90
        end = peak + 97

        if start >= 0 and end <= len(signal_125hz):
            segment = signal_125hz[start:end]

            if len(segment) == 187:
                segments.append(segment)
                valid_peaks.append(peak * 2)

    return segments, valid_peaks


def preprocess(segment, scaler):
    segment = np.array(segment)

    # PASUL 1: Replicam formatul din MIT-BIH CSV (Normalizare 0 la 1 pe bataie)
    min_val = np.min(segment)
    max_val = np.max(segment)
    if max_val != min_val:
        segment = (segment - min_val) / (max_val - min_val)

    segment = segment.reshape(1, -1)

    # PASUL 2: Replicam StandardScaler-ul folosit in notebook-ul de antrenament
    if scaler is not None:
        segment = scaler.transform(segment)

    # PASUL 3: Pregatim forma pentru reteaua Conv1D: (1, 187, 1)
    segment = segment.reshape(1, 187, 1)
    return segment