from dataclasses import dataclass


@dataclass
class RuntimeConfig:
    guild_id: int | None = None
    chat_channel_id: int | None = None
    logs_channel_id: int | None = None
    logs_message_id: int | None = None
    message_frequency_minutes: int = 60
    last_activity_ts: float = 0.0


class ConfigManager:
    def __init__(self, repository):
        self.repository = repository
        self.data = RuntimeConfig()

    @staticmethod
    def _int_or_none(value):
        return int(value) if value else None

    async def load(self):
        import asyncio

        config = await asyncio.to_thread(
            self.repository.get
        )

        self._apply(config)
        return self.data

    async def refresh(self):
        return await self.load()

    def _apply(self, config):
        self.data = RuntimeConfig(
            guild_id=self._int_or_none(config.guild_id),
            chat_channel_id=self._int_or_none(
                config.chat_channel_id
            ),
            logs_channel_id=self._int_or_none(
                config.logs_channel_id
            ),
            logs_message_id=self._int_or_none(
                config.logs_message_id
            ),
            message_frequency_minutes=int(
                config.message_frequency_minutes or 60
            ),
            last_activity_ts=float(
                config.last_activity_ts or 0
            ),
        )

    async def touch_activity(self):
        import asyncio

        await asyncio.to_thread(
            self.repository.touch_activity
        )

        self.data.last_activity_ts = __import__("time").time()

    async def setup_guild(self, guild_id, user_id):
        import asyncio

        await asyncio.to_thread(
            self.repository.setup_guild,
            guild_id,
            user_id,
        )
        await self.refresh()

    async def set_chat_channel(self, channel_id):
        import asyncio

        await asyncio.to_thread(
            self.repository.set_chat_channel,
            channel_id,
        )
        await self.refresh()

    async def set_logs_channel(self, channel_id, message_id):
        import asyncio

        await asyncio.to_thread(
            self.repository.set_logs_channel,
            channel_id,
            message_id,
        )
        await self.refresh()

    async def set_frequency(self, minutes):
        import asyncio

        await asyncio.to_thread(
            self.repository.set_frequency,
            minutes,
        )
        await self.refresh()
