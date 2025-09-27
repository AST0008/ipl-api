from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from models import Player, Team, Match, Inning, BattingStat
from dotenv import load_dotenv
load_dotenv()
import os
DATABASE_URL = os.getenv("DATABASE_URL")



engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal  = sessionmaker(bind=engine, autoflush=False)


Base.metadata.create_all(engine)

