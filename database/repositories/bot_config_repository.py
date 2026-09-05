from database.database import SessionLocal
from database.models import BotConfigModel


CONFIG_ID = "main"


class BotConfigRepository:
    def get(self) -> BotConfigModel:
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None:
                config = BotConfigModel(
                    id=CONFIG_ID,
                    message_frequency_minutes=60,
                    last_activity_ts=0.0,
                )
                session.add(config)
                session.commit()
                session.refresh(config)

            return config

    def setup_guild(self, guild_id: int, user_id: int):
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None:
                config = BotConfigModel(
                    id=CONFIG_ID,
                    message_frequency_minutes=60,
                    last_activity_ts=0.0,
                )
                session.add(config)

            config.guild_id = str(guild_id)
            config.setup_by_user_id = str(user_id)
            config.last_activity_ts = __import__("time").time()

            session.commit()
            session.refresh(config)
            return config

    def set_chat_channel(self, channel_id: int):
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None:
                raise RuntimeError("El bot todavía no está configurado.")

            config.chat_channel_id = str(channel_id)
            config.last_activity_ts = __import__("time").time()

            session.commit()

    def set_logs_channel(self, channel_id: int, message_id: int | None = None):
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None:
                raise RuntimeError("El bot todavía no está configurado.")

            config.logs_channel_id = str(channel_id)
            if message_id is not None:
                config.logs_message_id = str(message_id)
            session.commit()

    def set_frequency(self, minutes: int):
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None:
                raise RuntimeError("El bot todavía no está configurado.")

            config.message_frequency_minutes = minutes
            config.last_activity_ts = __import__("time").time()

            session.commit()

    def touch_activity(self):
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None:
                return

            config.last_activity_ts = __import__("time").time()
            session.commit()

    def get_if_configured(self):
        with SessionLocal() as session:
            config = session.get(BotConfigModel, CONFIG_ID)

            if config is None or not config.guild_id:
                return None

            return config
