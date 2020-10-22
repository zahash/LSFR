import re
import requests
from urllib.parse import urlparse
from igramscraper.instagram import Instagram
from .credentials import username, password

ACCOUNT_NAME_PATTERN = re.compile("(?!.*\.\.)(?!.*\.$)[^\W][\w.]{0,29}")
INSTAGRAM = Instagram()


def scrape_instagram_url(url, latest_post_num=-1):
    account_name = extract_account_name_from_url(url)
    for data in scrape_instagram_account(account_name, latest_post_num):
        yield data


def extract_account_name_from_url(url):
    p = urlparse(url).path
    matches = re.findall(ACCOUNT_NAME_PATTERN, p)

    if len(matches) != 1:
        raise ValueError(
            "Invalid URL; Detected Multiple or No Usernames; {}".format(matches)
        )

    account_name = matches[0]
    return account_name


def download_image(url, filepath):
    img_data = requests.get(url).content
    with open(filepath, "wb") as handler:
        handler.write(img_data)


def scrape_instagram_account(account_name, latest_post_num=-1):
    INSTAGRAM.with_credentials(username, password)
    INSTAGRAM.login()

    account = INSTAGRAM.get_account(account_name)
    total_media_count = account.media_count

    unscraped_media_count = total_media_count - latest_post_num

    media = INSTAGRAM.get_medias(account_name, count=unscraped_media_count)
    media = media[::-1]

    for item_num, item in enumerate(media):
        item_num = item_num + latest_post_num

        if item.type != "image":
            continue

        # img_id, post_url, img_url, saved_img_path
        # img_id = "<timestamp>_<instagram>_<account_name>_<img_num>"

        image_url = item.image_high_resolution_url
        item_url = item.link
        timestamp = item.created_time

        image_path = "image.jpg"
        download_image(image_url, image_path)

        img_id = "{}_{}_{}_{}".format(timestamp, "instagram", account_name, item_num)

        yield img_id, item_url, image_url, image_path
