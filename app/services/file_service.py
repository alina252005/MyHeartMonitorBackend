import requests
import os

def download_from_url(url: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    r = requests.get(url, timeout=15)
    r.raise_for_status()

    with open(local_path, "wb") as f:
        f.write(r.content)
