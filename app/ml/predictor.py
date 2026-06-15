import numpy as np
from collections import Counter
from app.ml.model_loader import model, scaler
from app.ml.preprocess import segment_signal, preprocess


def predict_signal(signal):
    segments, peaks = segment_signal(signal)
    predictions = []
    detailed_beats = []

    class_map = {0: 'N', 1: 'S', 2: 'V', 3: 'F', 4: 'Q'}

    for i, seg in enumerate(segments):
        seg_prep = preprocess(seg, scaler)
        pred = model.predict(seg_prep)
        # Convertim din np.int64 in int nativ de Python
        pred_class = int(np.argmax(pred))
        predictions.append(pred_class)

        detailed_beats.append({
            "index": int(peaks[i]),  # Ne asiguram ca e int nativ
            "class": class_map.get(pred_class, 'U')
        })

    if not predictions:
        return {"error": "Nu au putut fi gasite batai in semnal."}

    # Calculam clasa dominanta si o convertim in string ('N', 'V', etc.)
    final_class_int = Counter(predictions).most_common(1)[0][0]
    final_prediction_str = class_map.get(final_class_int, 'U')

    total = len(predictions)
    counts = Counter(predictions)

    # Construim un dictionar cu CHEI DE TIP STRING (asa cum vrea MongoDB)
    percentages = {}
    for cls_int, count in counts.items():
        cls_str = class_map.get(int(cls_int), 'U')
        percentages[cls_str] = float(round((count / total) * 100, 2))

    return {
        "final_prediction": final_prediction_str,
        "percentages": percentages,
        "detailed_beats": detailed_beats
    }