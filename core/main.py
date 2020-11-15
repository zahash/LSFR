import face_recognition

from .scraper import scrape_url
from .FaceData.add_face import add_data
from .FaceData.models import FData, FLoc
from .FaceData.utils import SessionCM as FaceDataSessionCM
from .LSH.utils import SessionCM as FaceIndexSessionCM
from .LSH.lsh import SQLDiskLSH, NonEmptyDirectory
from .utils import pil_compatible_bb
from .mappers import default_sql_mapper

import argparse


def set_credentials(domain, username, password):
    domain = domain.lower().strip()
    if domain == "instagram":
        credential_filepath = "./core/IGS/credentials.py"

    elif domain == "facebook":
        credential_filepath = "./core/FBS/credentials.py"

    with open(credential_filepath, "w") as f:
        f.write("username = '{}' \n".format(username))
        f.write("password = '{}' \n".format(password))


def get_faces(img_path):
    image = face_recognition.load_image_file(img_path)

    face_locations = face_recognition.face_locations(image)
    if not face_locations:
        return

    face_embeddings = face_recognition.face_encodings(image)

    corrected_face_locations = []
    for coords in face_locations:
        corrected_face_locations.append(pil_compatible_bb(coords))

    for face_num, (face_loc, face_embedding) in enumerate(
        zip(corrected_face_locations, face_embeddings)
    ):
        face_embedding = list(face_embedding)

        yield (face_num, face_loc, face_embedding)


def query(index, mapper, face_encoding, k=10):
    with FaceIndexSessionCM() as session:
        matching_id_dist = index.query(session, mapper, face_encoding, k=k)

    matches = []
    with FaceDataSessionCM() as session:
        for match in matching_id_dist:
            post_data = session.query(FData).filter(FData.vec_id == match.l_id).all()
            post_data = post_data[0]

            loc_data = session.query(FLoc).filter(FLoc.vec_id == match.l_id).all()
            loc_data = sorted(loc_data, key=lambda x: x.loc_idx)
            loc_data = [l.loc_val for l in loc_data]

            data = {
                "id": post_data.vec_id,
                "post_url": post_data.post_url,
                "img_url": post_data.img_url,
                "loc": loc_data,
                "dist": match.dist,
            }

            matches.append(data)

    return matches


def add(index, url):
    with FaceDataSessionCM() as fd_session, FaceIndexSessionCM() as fi_session:
        print("Scraping URL: ", url)
        for scraped_data in scrape_url(url):
            img_id, post_url, img_url, saved_img_path = scraped_data
            for face_data in get_faces(saved_img_path):
                if not face_data:
                    continue

                face_num, face_loc, face_embedding = face_data
                face_id = "{}_{}".format(img_id, face_num)

                add_data(
                    session=fd_session,
                    vec_id=face_id,
                    face_embedding=face_embedding,
                    face_loc=face_loc,
                    post_url=post_url,
                    img_url=img_url,
                )

                index.add(session=fi_session, id=face_id, arr=face_embedding)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument(
        "-u",
        "--urls",
        nargs="+",
        type=str,
        required=True,
        help="list of profile urls to scrape (space separated)",
    )
    args = ap.parse_args()

    index = SQLDiskLSH()
    for url in args.urls:
        add(index, url)
