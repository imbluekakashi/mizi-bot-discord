from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class CharacterModel(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    character_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    guild_id: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )

    channel_id: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Nueva conversación",
    )


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    conversation_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )