import numpy as np

def segment_signal(signal, window_size=187):
    segments = []
    for i in range(0, len(signal) - window_size, window_size):
        segments.append(signal[i:i+window_size])
    return segments


import numpy as np

def preprocess(seg, scaler=None):
    seg = seg.flatten()
    seg = seg - np.mean(seg)
    seg = seg / (np.std(seg) + 1e-8)
    seg = seg.reshape(1, -1, 1)

    return seg