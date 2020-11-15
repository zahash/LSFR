import os
import urllib.request
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename

from core.main import get_faces, query
from core.mappers import default_sql_mapper
from core.LSH.lsh import SQLDiskLSH


class NoFacesFound(Exception):
    pass


class MultipleFacesFound(Exception):
    pass


app = Flask(__name__)
app.secret_key = "YqiK4tFTuoz1QRXmegYTVqwJsFLFnhbPrRPSsnndk5yIYxKU"
app.config["UPLOAD_FOLDER"] = "./uploads"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

index = SQLDiskLSH()


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
            matches = get_matches(filepath)
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


def get_matches(filepath, k=10):
    faces = []
    for data in get_faces(filepath):
        faces.append(data)

    if len(faces) == 0:
        raise NoFacesFound(
            "No face is detected in the image. Please make sure that the image has atleast one face"
        )
    elif len(faces) > 1:
        raise MultipleFacesFound(
            "multiple faces detected in the image. Please crop the image to have a single face"
        )
    else:
        face_data = faces[0]
        face_num, face_loc, face_embedding = face_data
        matches = query(index, default_sql_mapper, face_embedding, k=k)

    return matches


if __name__ == "__main__":
    app.run(debug=True)
