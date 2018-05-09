import hashlib

FIT_ATTRIBUTES = [
        "registered_first_name",
        "registered_last_name",
        "registered_email",
]


def filter_session(session):
    s = {}
    for attr in FIT_ATTRIBUTES:
        s[attr] = session.get(attr)
    return s


def clean_session(session):
    for attr in FIT_ATTRIBUTES:
        try:
            del session[attr]
        except KeyError:
            pass


def user_hash(user_email):
    return hashlib.md5(user_email).hexdigest()[:16]

