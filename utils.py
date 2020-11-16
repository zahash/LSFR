from core.main import get_faces, query
from core.mappers import default_sql_mapper


class NoFacesFound(Exception):
    pass


class MultipleFacesFound(Exception):
    pass


def get_matches(index, filepath, k=10):
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
