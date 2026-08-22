import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:

    clean_host = TURSO_DATABASE_URL.replace("libsql://", "").replace("https://", "")

    print(f"[DB] Conectando a Turso remoto: {clean_host}")

    DATABASE_URL = (
        f"sqlite+libsql://{clean_host}"
        f"?authToken={TURSO_AUTH_TOKEN}&secure=true"
    )

    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

else:
    print("[DB] TURSO_DATABASE_URL o TURSO_AUTH_TOKEN no detectadas, usando SQLite local.")

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