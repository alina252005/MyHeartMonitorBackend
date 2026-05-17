import wfdb
import numpy as np

record = wfdb.rdrecord("100", pn_dir="mitdb")
annotation = wfdb.rdann("100", "atr", pn_dir="mitdb")

ecg = record.p_signal[:,0]

print("ECG length:", len(ecg))

symbols = annotation.symbol

normal_beats = symbols.count("N")

print("Normal beats:", normal_beats)
np.save("test_normal_ecg.npy", ecg)