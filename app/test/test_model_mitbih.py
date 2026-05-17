import wfdb
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, accuracy_score
from scipy.signal import resample

MODEL_PATH = "D:\\Facultate\\heartMonitor\\ml\\ecg_model.h5"

model = tf.keras.models.load_model(MODEL_PATH)

CLASS_MAP = {
    "N":0,
    "L":0,
    "R":0,
    "e":0,
    "j":1,
    "A":1,
    "a":1,
    "S":1,
    "V":2,
    "E":2,
    "F":3
}

records = [
"100","101","102","103","104","105","106","107",
"108","109","111","112","113","114","115","116",
"117","118","119","121","122","123","124","200",
"201","202","203","205","207","208","209","210",
"212","213","214","215","217","219","220","221",
"222","223","228","230","231","232","233","234"
]

X = []
y = []

for rec in records:

    record = wfdb.rdrecord(rec, pn_dir="mitdb")
    annotation = wfdb.rdann(rec, "atr", pn_dir="mitdb")

    signal = record.p_signal[:,0]

    signal = resample(signal, int(len(signal)*360/360))

    signal = (signal - np.mean(signal)) / np.std(signal)

    for i, symbol in enumerate(annotation.symbol):

        if symbol not in CLASS_MAP:
            continue

        peak = annotation.sample[i]

        start = peak - 100
        end = peak + 100

        if start < 0 or end > len(signal):
            continue

        beat = signal[start:end]

        X.append(beat)
        y.append(CLASS_MAP[symbol])

X = np.array(X)
y = np.array(y)

X = X.reshape(X.shape[0],200,1)

print("Total beats:",len(X))

pred = model.predict(X)

pred_classes = np.argmax(pred,axis=1)

acc = accuracy_score(y,pred_classes)

print("Accuracy:",acc)

print(classification_report(y,pred_classes))