from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .dbconfig import DATABASE_CONFIG
from sqlalchemy.engine.url import URL

DB_URL = URL(**DATABASE_CONFIG)
ENGINE = create_engine(DB_URL, echo=False)

Session = sessionmaker(bind=ENGINE)
Base = declarative_base()
