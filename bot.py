import asyncio
import os
import random
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

from ai.prompt_builder import PromptBuilder
from ai.provider_factory import FallbackAIProvider
from database.database import init_db
from database.repositories.bot_config_repository import BotConfigRepository
from commands.admin_commands import AdminCommands
from keep_alive import start_keep_alive_server
from memory.conversation_memory import ConversationMemory
from models.character import Character
from runtime_config import ConfigManager


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "No se encontró DISCORD_TOKEN en las variables de entorno."
    )

DB_TIMEOUT = int(os.getenv("MIZI_DB_TIMEOUT", "15"))
AI_TIMEOUT = int(os.getenv("MIZI_AI_TIMEOUT", "45"))
MAX_CONCURRENT_AI = int(
    os.getenv("MIZI_MAX_CONCURRENT_AI", "3")
)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


character = Character()

init_db()

prompt_builder = PromptBuilder(character)

memory = ConversationMemory(
    history_limit=getattr(
        character.ai_settings,
        "history_limit",
        12,
    )
)

ai = FallbackAIProvider(
    provider_names=character.ai_settings.fallback_providers,
    provider_models=getattr(
        character.ai_settings,
        "provider_models",
        None,
    ),
)

config_repo = BotConfigRepository()
config = ConfigManager(config_repo)

admin_commands = AdminCommands(
    bot=bot,
    config_manager=config,
    dashboard=ai.monitor,
)
admin_commands.register()

ai_semaphore = asyncio.Semaphore(
    MAX_CONCURRENT_AI
)

conversation_locks: dict[str, asyncio.Lock] = {}


@bot.event
async def setup_hook():
    synced = await bot.tree.sync()
    print(f"[DISCORD] Slash commands sincronizados: {len(synced)}")


LETTER_EMOJI = {
    chr(code): chr(
        0x1F1E6 + code - ord("A")
    )
    for code in range(
        ord("A"),
        ord("Z") + 1,
    )
}


def split_response(
    response: str,
    max_parts: int = 3,
) -> list[str]:
    parts = [
        part.strip()
        for part in response.split("|||")
        if part.strip()
    ]

    if not parts:
        return [response.strip()]

    return parts[:max_parts]


def resolve_reaction_emojis(
    spec: str,
) -> list[str]:
    raw_parts = [
        part.strip()
        for part in spec.split(",")
        if part.strip()
    ]

    emojis = []

    for part in raw_parts:
        if (
            len(part) == 1
            and part.upper() in LETTER_EMOJI
        ):
            emojis.append(
                LETTER_EMOJI[part.upper()]
            )
        else:
            emojis.append(part)

    return emojis


async def run_db(function, *args, **kwargs):
    return await asyncio.wait_for(
        asyncio.to_thread(
            function,
            *args,
            **kwargs,
        ),
        timeout=DB_TIMEOUT,
    )


async def run_ai(
    messages: list[dict[str, str]],
) -> str:
    async with ai_semaphore:
        return await asyncio.wait_for(
            asyncio.to_thread(
                ai.generate,
                messages=messages,
                model=character.ai_settings.model,
                temperature=character.ai_settings.temperature,
                max_tokens=character.ai_settings.max_tokens,
            ),
            timeout=AI_TIMEOUT,
        )


async def update_dashboard():
    channel_id = config.data.logs_channel_id
    message_id = config.data.logs_message_id

    if not channel_id or not message_id:
        return

    channel = bot.get_channel(channel_id)

    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception as error:
            print(
                "[DASHBOARD] No se pudo obtener el canal:",
                error,
            )
            return

    try:
        message = await channel.fetch_message(
            message_id
        )

        await message.edit(
            embed=ai.monitor.build_embed(
                getattr(
                    character.ai_settings,
                    "provider_models",
                    {},
                )
            )
        )

    except discord.NotFound:
        print(
            "[DASHBOARD] El mensaje del dashboard ya no existe."
        )

    except discord.HTTPException as error:
        print(
            "[DASHBOARD] Error actualizando:",
            error,
        )


async def activity_touch():
    try:
        await config.touch_activity()
    except Exception as error:
        print(
            "[ACTIVITY] Error actualizando actividad:",
            error,
        )


@bot.event
async def on_ready():
    await config.load()

    print("=" * 60)
    print(
        f"[DISCORD] Conectado como {bot.user}"
    )
    print(
        f"[DISCORD] ID: {bot.user.id}"
    )
    print(
        "[AI] Proveedores configurados:",
        character.ai_settings.fallback_providers,
    )
    print(
        "[AI] Modelo principal:",
        character.ai_settings.model,
    )
    print(
        "[AI] Concurrencia máxima:",
        MAX_CONCURRENT_AI,
    )
    print(
        "[CONFIG] Guild:",
        config.data.guild_id,
    )
    print(
        "[CONFIG] Chat:",
        config.data.chat_channel_id,
    )
    print(
        "[CONFIG] Logs:",
        config.data.logs_channel_id,
    )
    print("=" * 60)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # DMs: jamás consultan configuración ni IA.
    if message.guild is None:
        return

    # Servidor autorizado solamente.
    if (
        config.data.guild_id is None
        or message.guild.id != config.data.guild_id
    ):
        return

    # Canal autorizado solamente.
    if (
        config.data.chat_channel_id is None
        or message.channel.id != config.data.chat_channel_id
    ):
        return

    # Cualquier mensaje humano en el canal reinicia el contador.
    await activity_touch()

    # Si no menciona a Mizi, no gastamos tokens.
    if bot.user not in message.mentions:
        return

    user_message = (
        message.content
        .replace(
            f"<@{bot.user.id}>",
            "",
        )
        .replace(
            f"<@!{bot.user.id}>",
            "",
        )
        .strip()
    )

    if not user_message:
        user_message = "Hola Mizi."

    conversation_id = (
        ConversationMemory.build_conversation_id(
            channel_id=str(message.channel.id),
            user_id=str(message.author.id),
        )
    )

    lock = conversation_locks.setdefault(
        conversation_id,
        asyncio.Lock(),
    )

    async with lock:
        await handle_ai_message(
            message,
            conversation_id,
            user_message,
        )


async def handle_ai_message(
    message: discord.Message,
    conversation_id: str,
    user_message: str,
):
    start_time = time.monotonic()

    try:
        print(
            f"[FLOW] {conversation_id} -> DB"
        )

        await run_db(
            memory.ensure_conversation,
            conversation_id=conversation_id,
            character_id="mizi",
            user_id=str(message.author.id),
            guild_id=str(message.guild.id),
            channel_id=str(message.channel.id),
        )

        history = await run_db(
            memory.get_history,
            conversation_id,
        )

        messages = prompt_builder.build_messages(
            user_message,
            history=history,
        )

        print(
            f"[FLOW] {conversation_id} -> AI "
            f"(input≈{ai.monitor.estimate_tokens(chr(10).join(m.get('content','') for m in messages)):,} tokens)"
        )

        async with message.channel.typing():
            response = await run_ai(messages)

        await update_dashboard()

        response = response.strip()

        if not response:
            raise RuntimeError(
                "La IA devolvió una respuesta vacía."
            )

        if response.upper().startswith(
            "REACCIONAR:"
        ):
            spec = response.split(
                ":",
                1,
            )[1]

            emojis = resolve_reaction_emojis(
                spec
            )

            for emoji in emojis:
                try:
                    await message.add_reaction(
                        emoji
                    )
                except discord.HTTPException:
                    pass

                await asyncio.sleep(
                    random.uniform(
                        0.35,
                        0.75,
                    )
                )

            await run_db(
                memory.add_user_message,
                conversation_id,
                user_message,
            )

            await run_db(
                memory.add_assistant_message,
                conversation_id,
                (
                    "*reacciona con "
                    + " ".join(emojis)
                    + "*"
                ),
            )

        else:
            await run_db(
                memory.add_user_message,
                conversation_id,
                user_message,
            )

            await run_db(
                memory.add_assistant_message,
                conversation_id,
                response,
            )

            parts = split_response(response)

            for index, part in enumerate(parts):
                if index > 0:
                    async with message.channel.typing():
                        await asyncio.sleep(
                            random.uniform(
                                0.8,
                                2.0,
                            )
                        )

                if index == 0:
                    await message.reply(part)
                else:
                    await message.channel.send(part)

        elapsed = (
            time.monotonic() - start_time
        )

        print(
            f"[FLOW] {conversation_id} -> "
            f"completado en {elapsed:.2f}s"
        )

    except asyncio.TimeoutError:
        await update_dashboard()

        print(
            f"[TIMEOUT] {conversation_id}"
        )

        try:
            await message.reply(
                "Perdón 😭 me tardé demasiado pensando. Intenta de nuevo."
            )
        except discord.HTTPException:
            pass

    except Exception as error:
        await update_dashboard()

        print(
            f"[ERROR] {conversation_id} -> "
            f"{type(error).__name__}: {error}"
        )

        try:
            await message.reply(
                "Perdón 😭 tuve un pequeño problema intentando responderte."
            )
        except discord.HTTPException:
            pass


async def idle_message_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():
        await asyncio.sleep(10)

        if config.data.guild_id is None:
            continue

        if config.data.chat_channel_id is None:
            continue

        frequency = max(
            1,
            config.data.message_frequency_minutes,
        )

        now = time.time()
        elapsed = (
            now - config.data.last_activity_ts
        )

        if elapsed < frequency * 60:
            continue

        # Reservamos el siguiente ciclo antes de llamar a la IA para
        # evitar que dos iteraciones envíen mensajes simultáneos.
        await activity_touch()

        channel = bot.get_channel(
            config.data.chat_channel_id
        )

        if channel is None:
            try:
                channel = await bot.fetch_channel(
                    config.data.chat_channel_id
                )
            except Exception as error:
                print(
                    "[IDLE] No se pudo obtener el canal:",
                    error,
                )
                continue

        try:
            idle_prompt = (
                prompt_builder
                .build_idle_message_prompt()
            )

            async with channel.typing():
                response = await run_ai(idle_prompt)

            await update_dashboard()

            response = response.strip()

            if not response:
                continue

            await channel.send(response)

            print(
                "[IDLE] Mensaje espontáneo enviado:",
                response[:100],
            )

        except Exception as error:
            await update_dashboard()

            print(
                "[IDLE] Error:",
                type(error).__name__,
                error,
            )


async def main():
    await start_keep_alive_server()

    asyncio.create_task(
        idle_message_loop()
    )

    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
