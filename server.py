import os
import urllib.request
import requests
from flask import Flask, request, redirect, jsonify, g
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from werkzeug.utils import secure_filename

from core.LSH.lsh import SQLDiskLSH
from utils import get_matches, _parse_firebase_error, NoFacesFound, MultipleFacesFound

from auth.token_system import generate_auth_token, verify_auth_token
from auth.firebase_authentication import firebase_auth

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["UPLOAD_FOLDER"] = "./uploads"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

http_basic_auth = HTTPBasicAuth()

INDEX = SQLDiskLSH()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["POST"])
@http_basic_auth.login_required
def upload_file():
    # check if the post request has the file part
    if "file" not in request.files:
        resp = jsonify({"message": "No file part in the request"})
        resp.status_code = 400
        return resp
    file = request.files["file"]
    if file.filename == "":
        resp = jsonify({"message": "No file selected for uploading"})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            matches = get_matches(INDEX, filepath)
            resp = jsonify({"matches": matches})
            resp.status_code = 201

        except (NoFacesFound, MultipleFacesFound) as err:
            resp = jsonify({"message": str(err)})
            resp.status_code = 400

        finally:
            return resp

    else:
        resp = jsonify(
            {"message": "Allowed file types are {}".format(str(ALLOWED_EXTENSIONS))}
        )
        resp.status_code = 400
        return resp


@app.route("/auth/token")
@http_basic_auth.login_required
def get_auth_token():
    # g.user was set by the verify_password method to store
    # the user object for further usage
    token = generate_auth_token(g.user["idToken"])
    return jsonify({"token": token.decode("ascii")})


@app.route("/auth/register", methods=["POST"])
def register_user():
    email = request.json.get("email")
    password = request.json.get("password")

    try:
        user = firebase_auth.create_user_with_email_and_password(email, password)
        firebase_auth.send_email_verification(user["idToken"])

        resp = jsonify({"email": email, "message": "Email verification link sent"})
        resp.status_code = 200

        return resp

    except requests.exceptions.HTTPError as e:
        error, error_code = _parse_firebase_error(e)
        resp = jsonify(error)
        resp.status_code = error_code

        return resp


@app.route("/auth/reset-password", methods=["POST"])
def reset_password():
    email = request.json.get("email")

    try:
        firebase_auth.send_password_reset_email(email)

        resp = jsonify({"email": email, "message": "Password reset link sent"})
        resp.status_code = 200
        return resp
    except requests.exceptions.HTTPError as e:
        error, error_code = _parse_firebase_error(e)
        resp = jsonify(error)
        resp.status_code = error_code
        return resp


@http_basic_auth.verify_password
def verify_password(email_or_token, password):
    # TODO: improve exception handling (no internet, etc...)
    if verify_auth_token(email_or_token):
        return True

    try:
        # user is just a dictionary returned by firebase
        user = firebase_auth.sign_in_with_email_and_password(email_or_token, password)
        # set g.user to store the user object
        # g acts like a global variable which other
        # functions like get_auth_token() can use
        g.user = user
        return True
    except:
        return False


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
