import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_PATH = os.getenv("DATABASE_PATH", "mizi_bot.db")

Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass

def init_db():
    from database.models import (
        CharacterModel,
        ConversationModel,
        MessageModel,
    )

    Base.metadata.create_all(bind=engine)