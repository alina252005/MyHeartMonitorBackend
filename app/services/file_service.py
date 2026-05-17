import time
import numpy as np
import time
import os
import requests
import os
import pandas as pd

def download_from_url(url: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    r = requests.get(url, timeout=15)
    r.raise_for_status()

    with open(local_path, "wb") as f:
        f.write(r.content)


def load_signal_from_file(url: str):
    local_path = f"temp/ecg_{int(time.time())}.npy"
    download_from_url(url, local_path)
    signal = np.load(local_path)
    signal = signal.flatten()
    print("Signal shape:", signal.shape)

    return signal