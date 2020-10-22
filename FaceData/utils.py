from sqlalchemy.exc import IntegrityError
from .base import Session


class SessionCM:
    """Context manager for the Session class"""

    def __enter__(self):
        self.session = Session()
        return self.session

    def __exit__(self, exc_type, exc_val, traceback):
        self.session.close()


def commit_add_db_row(session, db_row):
    try:
        session.add(db_row)
        print("ADDING: ", str(db_row))
        session.flush()
    except IntegrityError:
        session.rollback()
        print("* INTEGRITY FAILURE: ", str(db_row))
        return -1
    else:
        session.commit()
        print("* SUCESS")
        return 1
