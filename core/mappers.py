from .FaceData.models import FEmbed
from .FaceData.utils import SessionCM as FaceDataSessionCM


def default_sql_mapper(face_id):
    with FaceDataSessionCM() as session:
        results = (
            session.query(FEmbed.embed_val)
            .filter(FEmbed.vec_id == face_id)
            .order_by(FEmbed.embed_idx)
            .all()
        )

    face_embedding = [x[0] for x in results]
    return face_embedding
