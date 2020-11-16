import os
from .firebase_authentication import firebase_auth
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadSignature,
    SignatureExpired,
)

SECRET_KEY = os.environ.get("SECRET_KEY")


def generate_auth_token(idToken, expiration=3600):
    s = Serializer(SECRET_KEY, expires_in=expiration)
    return s.dumps({"idToken": idToken})


def verify_auth_token(token):
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None  # valid token, but expired
    except BadSignature:
        return None  # invalid token

    return True
