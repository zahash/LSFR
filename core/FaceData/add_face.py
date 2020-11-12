import os
import sys
import json

from .base import Base, ENGINE
from .models import FData, FEmbed, FLoc
from .utils import SessionCM, commit_add_db_row

Base.metadata.create_all(ENGINE)


def add_data(
    session, vec_id, face_embedding, face_loc, post_url, img_url,
):
    fdata_row = FData(vec_id=vec_id, post_url=post_url, img_url=img_url)
    commit_add_db_row(session, fdata_row)

    for embed_idx, embed_val in enumerate(face_embedding):
        fembed_row = FEmbed(vec_id=vec_id, embed_idx=embed_idx, embed_val=embed_val)
        commit_add_db_row(session, fembed_row)

    for loc_idx, loc_val in enumerate(face_loc):
        floc_row = FLoc(vec_id=vec_id, loc_idx=loc_idx, loc_val=loc_val)
        commit_add_db_row(session, floc_row)


def add_json_data(session, filepath):
    with open(filepath, "r") as f:
        data = json.load(f)

    filename = os.path.basename(filepath)
    vec_id = filename.replace(".json", "")

    face_embedding = data["face_enc"]
    face_loc = data["face_loc"]
    post_url = data["insta_url"]
    img_url = data["img_url"]

    add_data(
        session,
        vec_id=vec_id,
        face_embedding=face_embedding,
        face_loc=face_loc,
        post_url=post_url,
        img_url=img_url,
    )


if __name__ == "__main__":
    filepaths = sys.argv[1:]

    with SessionCM() as session:
        for filepath in filepaths:
            add_json_data(session, filepath)
