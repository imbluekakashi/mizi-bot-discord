from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class CharacterModel(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    guild_id: Mapped[str] = mapped_column(String(100), nullable=True)
    channel_id: Mapped[str] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Nueva conversación",
    )


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class BotConfigModel(Base):
    __tablename__ = "bot_config"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="main")
    guild_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    chat_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logs_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logs_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message_frequency_minutes: Mapped[int] = mapped_column(nullable=False, default=60)
    last_activity_ts: Mapped[float] = mapped_column(nullable=False, default=0.0)
    setup_by_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ProviderStatsModel(Base):
    __tablename__ = "provider_stats"

    provider: Mapped[str] = mapped_column(String(50), primary_key=True)
    requests: Mapped[int] = mapped_column(nullable=False, default=0)
    successes: Mapped[int] = mapped_column(nullable=False, default=0)
    errors: Mapped[int] = mapped_column(nullable=False, default=0)
    rate_limits: Mapped[int] = mapped_column(nullable=False, default=0)
    estimated_input_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    estimated_output_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    total_latency_ms: Mapped[float] = mapped_column(nullable=False, default=0.0)
    last_latency_ms: Mapped[float] = mapped_column(nullable=False, default=0.0)
    last_used_ts: Mapped[float] = mapped_column(nullable=False, default=0.0)
    limited_until_ts: Mapped[float] = mapped_column(nullable=False, default=0.0)
