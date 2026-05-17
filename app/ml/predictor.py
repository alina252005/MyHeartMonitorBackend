import numpy as np
from collections import Counter
from app.ml.model_loader import model, scaler
from app.ml.preprocess import segment_signal, preprocess


def predict_signal(signal):
    segments = segment_signal(signal)
    predictions = []

    for seg in segments:
        seg = preprocess(seg, scaler)
        pred = model.predict(seg)
        pred_class = int(np.argmax(pred))
        predictions.append(pred_class)

    final = Counter(predictions).most_common(1)[0][0]
    total = len(predictions)
    counts = Counter(predictions)

    percentages = {}

    for cls, count in counts.items():
        percentages[int(cls)] = round((count / total) * 100, 2)
        print("Segment sample:", seg[:10])
    return {
        "final_prediction": final,
        "segments": predictions,
        "percentages": percentages
    }