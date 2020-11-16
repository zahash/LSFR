import pyrebase
from .firebase_config import config

firebase = pyrebase.initialize_app(config)
firebase_auth = firebase.auth()

