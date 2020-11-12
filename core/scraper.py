from urllib.parse import urlparse
from sqlalchemy import distinct

from .FaceData.utils import SessionCM as FaceDataSessionCM
from .FaceData.models import FData
from .utils import parse_face_id


def scrape_url(url):
    domain = find_domain(url)
    # img_id format : "<timestamp>_<domain>_<account_name>_<img_num>"

    if "instagram" in domain:
        from .IGS.scraper import scrape_instagram_url, extract_account_name_from_url

        account_name = extract_account_name_from_url(url)

        with FaceDataSessionCM() as fd_session:
            latest_face_id = (
                fd_session.query(distinct(FData.vec_id))
                .filter(FData.vec_id.like("%" + account_name + "%"))
                .order_by(FData.vec_id.desc())
                .first()
            )

        if latest_face_id:
            latest_face_id = latest_face_id[0]
            _, _, _, latest_post_num, _ = parse_face_id(latest_face_id)
        else:
            latest_post_num = 0

        for data in scrape_instagram_url(url, latest_post_num):
            yield data

    elif "facebook" in domain:
        from .FBS.scraper import scrape_facebook_url

        for data in scrape_facebook_url(url):
            yield data


def find_domain(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    return domain

