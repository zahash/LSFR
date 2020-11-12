def pil_compatible_bb(bb):
    if len(bb) != 4:
        raise ValueError(
            "The bounding box must be a list|tuple of length 4 (top, right, bottom, left)"
        )

    top, right, bottom, left = bb
    return (left, top, right, bottom)


def parse_face_id(id):
    "<timestamp>_<domain>_<account_name>_<img_num>_<face_num>"
    timestamp, domain, *account_name, img_num, face_num = id.split("_")
    account_name = "_".join(account_name)

    return timestamp, domain, account_name, int(img_num), int(face_num)
