import os
import json
import firebase_admin

from firebase_admin import credentials, storage


def initialize_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    firebase_bucket = os.getenv("FIREBASE_BUCKET")

    if firebase_credentials_json:
        try:
            firebase_credentials_dict = json.loads(firebase_credentials_json)

            if "private_key" in firebase_credentials_dict:
                firebase_credentials_dict["private_key"] = firebase_credentials_dict[
                    "private_key"
                ].replace("\\n", "\n")

            cred = credentials.Certificate(firebase_credentials_dict)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"FIREBASE_CREDENTIALS_JSON is not valid JSON: {e}"
            )

    else:
        local_firebase_path = os.path.join(
            os.path.dirname(__file__),
            "firebase.json",
        )

        if not os.path.exists(local_firebase_path):
            raise FileNotFoundError(
                "Firebase credentials were not found. "
                "Set FIREBASE_CREDENTIALS_JSON in Azure Environment Variables "
                "or provide app/services/firebase.json locally."
            )

        cred = credentials.Certificate(local_firebase_path)

    options = {}

    if firebase_bucket:
        options["storageBucket"] = firebase_bucket.replace("gs://", "")

    app = firebase_admin.initialize_app(
        cred,
        options,
    )

    print("Firebase initialized successfully")
    print(f"Firebase bucket: {firebase_bucket}")

    return app


def init_firebase():
    return initialize_firebase()


firebase_app = initialize_firebase()
bucket = storage.bucket()