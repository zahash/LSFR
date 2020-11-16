import os
import urllib.request
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename

from core.LSH.lsh import SQLDiskLSH
from utils import get_matches, NoFacesFound, MultipleFacesFound

app = Flask(__name__)
app.secret_key = "YqiK4tFTuoz1QRXmegYTVqwJsFLFnhbPrRPSsnndk5yIYxKU"
app.config["UPLOAD_FOLDER"] = "./uploads"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

INDEX = SQLDiskLSH()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["POST"])
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


if __name__ == "__main__":
    app.run(debug=True)
