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
from keep_alive import start_keep_alive_server
from memory.conversation_memory import ConversationMemory
from models.character import Character
from runtime_config import ConfigManager

from commands.admin_commands import AdminCommands


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "No se encontró DISCORD_TOKEN en las variables de entorno."
    )


intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# ============================================================
# COMPONENTES PRINCIPALES
# ============================================================

character = Character()

# Para que AdminCommands pueda acceder a los modelos.
bot.character = character

init_db()

prompt_builder = PromptBuilder(character)

memory = ConversationMemory(
    history_limit=character.ai_settings.history_limit
)

ai = FallbackAIProvider(
    character.ai_settings.fallback_providers
)

# El ProviderMonitor vive dentro de FallbackAIProvider.
provider_monitor = ai.monitor

config_repository = BotConfigRepository()

config_manager = ConfigManager(
    config_repository
)

admin_commands = AdminCommands(
    bot=bot,
    config_manager=config_manager,
    provider_monitor=provider_monitor,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

DB_TIMEOUT = 15
AI_TIMEOUT = 45
MAX_CONCURRENT_AI = int(
    os.getenv("MAX_CONCURRENT_AI", "3")
)

ai_semaphore = asyncio.Semaphore(
    MAX_CONCURRENT_AI
)

conversation_locks = {}


LETTER_EMOJI = {
    chr(code): chr(0x1F1E6 + code - ord("A"))
    for code in range(ord("A"), ord("Z") + 1)
}


# ============================================================
# UTILIDADES
# ============================================================

def get_conversation_lock(conversation_id: str):
    lock = conversation_locks.get(conversation_id)

    if lock is None:
        lock = asyncio.Lock()
        conversation_locks[conversation_id] = lock

    return lock


def split_response(
    response: str,
    max_parts: int = 3,
) -> list[str]:
    parts = [
        part.strip()
        for part in response.split("|||")
    ]

    parts = [
        part
        for part in parts
        if part
    ]

    return (
        parts[:max_parts]
        if parts
        else [response.strip()]
    )


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


# ============================================================
# ACTUALIZACIÓN DEL DASHBOARD
# ============================================================

async def update_provider_dashboard():
    config = config_manager.data

    if not config.logs_channel_id:
        return

    if not config.logs_message_id:
        return

    channel = bot.get_channel(
        config.logs_channel_id
    )

    if channel is None:
        try:
            channel = await bot.fetch_channel(
                config.logs_channel_id
            )
        except Exception as error:
            print(
                f"[DASHBOARD] No se pudo obtener el canal: {error}"
            )
            return

    try:
        message = await channel.fetch_message(
            config.logs_message_id
        )

        models = (
            character.ai_settings.provider_models
        )

        await message.edit(
            embed=provider_monitor.build_embed(
                models
            )
        )

    except discord.NotFound:
        print(
            "[DASHBOARD] El mensaje del dashboard ya no existe."
        )

    except discord.Forbidden:
        print(
            "[DASHBOARD] No tengo permisos para editar el dashboard."
        )

    except Exception as error:
        print(
            f"[DASHBOARD] Error actualizando dashboard: {error}"
        )


# ============================================================
# SETUP DE DISCORD
# ============================================================

@bot.event
async def setup_hook():

    # Cargar configuración persistida.
    try:
        await config_manager.load()
    except Exception as error:
        print(
            f"[CONFIG] Error cargando configuración: {error}"
        )

    # Registrar comandos administrativos.
    admin_commands.register()

    # Sincronizar slash commands.
    try:
        synced = await bot.tree.sync()

        print(
            f"[DISCORD] Slash commands sincronizados: "
            f"{len(synced)}"
        )

    except Exception as error:
        print(
            f"[DISCORD] Error sincronizando slash commands: "
            f"{error}"
        )


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("=" * 60)

    print(
        f"[DISCORD] Conectado como {bot.user}"
    )

    print(
        f"[DISCORD] ID: {bot.user.id}"
    )

    print(
        f"[AI] Proveedores configurados: "
        f"{character.ai_settings.fallback_providers}"
    )

    print(
        f"[AI] Modelo principal: "
        f"{character.ai_settings.model}"
    )

    print(
        f"[AI] Concurrencia máxima: "
        f"{MAX_CONCURRENT_AI}"
    )

    config = config_manager.data

    print(
        f"[CONFIG] Guild: {config.guild_id}"
    )

    print(
        f"[CONFIG] Chat: {config.chat_channel_id}"
    )

    print(
        f"[CONFIG] Logs: {config.logs_channel_id}"
    )

    print("=" * 60)


# ============================================================
# MENSAJES
# ============================================================

@bot.event
async def on_message(message: discord.Message):

    # Nunca responder a otros bots.
    if message.author.bot:
        return

    # ========================================================
    # BLOQUEAR DMs
    # ========================================================

    if message.guild is None:
        return

    config = config_manager.data

    # ========================================================
    # SOLO SERVIDOR AUTORIZADO
    # ========================================================

    if config.guild_id is None:
        return

    if message.guild.id != config.guild_id:
        return

    # ========================================================
    # SOLO CANAL AUTORIZADO
    # ========================================================

    if config.chat_channel_id is None:
        return

    if message.channel.id != config.chat_channel_id:
        return

    # ========================================================
    # TODA ACTIVIDAD HUMANA REINICIA EL TEMPORIZADOR
    # ========================================================

    try:
        await config_manager.touch_activity()
    except Exception as error:
        print(
            f"[CONFIG] Error actualizando actividad: {error}"
        )

    # ========================================================
    # SOLO MENCIONES CONSUMEN IA
    # ========================================================

    if bot.user is None:
        return

    if bot.user not in message.mentions:
        return

    # ========================================================
    # LIMPIAR MENCIÓN
    # ========================================================

    user_message = message.content

    user_message = user_message.replace(
        f"<@{bot.user.id}>",
        "",
    )

    user_message = user_message.replace(
        f"<@!{bot.user.id}>",
        "",
    )

    user_message = user_message.strip()

    if not user_message:
        user_message = "Hola Mizi."

    await handle_ai_message(
        message,
        user_message,
    )


# ============================================================
# IA
# ============================================================

async def handle_ai_message(
    message: discord.Message,
    user_message: str,
):

    conversation_id = (
        ConversationMemory.build_conversation_id(
            channel_id=str(message.channel.id),
            user_id=str(message.author.id),
        )
    )

    lock = get_conversation_lock(
        conversation_id
    )

    async with lock:

        start_time = time.monotonic()

        try:

            print(
                f"[FLOW] {conversation_id} "
                "-> ensure_conversation"
            )

            await asyncio.wait_for(
                asyncio.to_thread(
                    memory.ensure_conversation,
                    conversation_id=conversation_id,
                    character_id="mizi",
                    user_id=str(message.author.id),
                    guild_id=str(message.guild.id),
                    channel_id=str(message.channel.id),
                ),
                timeout=DB_TIMEOUT,
            )

            print(
                f"[FLOW] {conversation_id} "
                "-> get_history"
            )

            history = await asyncio.wait_for(
                asyncio.to_thread(
                    memory.get_history,
                    conversation_id,
                ),
                timeout=DB_TIMEOUT,
            )

            messages = (
                prompt_builder.build_messages(
                    user_message,
                    history=history,
                )
            )

            print(
                f"[FLOW] {conversation_id} "
                "-> ai.generate"
            )

            async with ai_semaphore:

                async with message.channel.typing():

                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            ai.generate,
                            messages=messages,
                            model=character.ai_settings.model,
                            temperature=character.ai_settings.temperature,
                            max_tokens=character.ai_settings.max_tokens,
                        ),
                        timeout=AI_TIMEOUT,
                    )

            # Actualizar dashboard después del intento.
            await update_provider_dashboard()

            # =================================================
            # REACCIONES
            # =================================================

            if response.strip().upper().startswith(
                "REACCIONAR:"
            ):

                print(
                    f"[FLOW] {conversation_id} "
                    "-> reaccionando"
                )

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
                            0.4,
                            0.9,
                        )
                    )

                await asyncio.wait_for(
                    asyncio.to_thread(
                        memory.add_user_message,
                        conversation_id,
                        user_message,
                    ),
                    timeout=DB_TIMEOUT,
                )

                await asyncio.wait_for(
                    asyncio.to_thread(
                        memory.add_assistant_message,
                        conversation_id,
                        (
                            f"*reacciona con "
                            f"{' '.join(emojis)}*"
                        ),
                    ),
                    timeout=DB_TIMEOUT,
                )

            # =================================================
            # RESPUESTA NORMAL
            # =================================================

            else:

                print(
                    f"[FLOW] {conversation_id} "
                    "-> guardando mensajes"
                )

                await asyncio.wait_for(
                    asyncio.to_thread(
                        memory.add_user_message,
                        conversation_id,
                        user_message,
                    ),
                    timeout=DB_TIMEOUT,
                )

                await asyncio.wait_for(
                    asyncio.to_thread(
                        memory.add_assistant_message,
                        conversation_id,
                        response,
                    ),
                    timeout=DB_TIMEOUT,
                )

                parts = split_response(
                    response
                )

                for index, part in enumerate(parts):

                    if index > 0:

                        async with message.channel.typing():

                            await asyncio.sleep(
                                random.uniform(
                                    1.0,
                                    2.5,
                                )
                            )

                    if index == 0:

                        await message.reply(
                            part
                        )

                    else:

                        await message.channel.send(
                            part
                        )

            elapsed = (
                time.monotonic()
                - start_time
            )

            print(
                f"[FLOW] {conversation_id} "
                f"-> completado en {elapsed:.2f}s"
            )

        except asyncio.TimeoutError:

            elapsed = (
                time.monotonic()
                - start_time
            )

            print(
                f"[TIMEOUT] {conversation_id} "
                f"-> se colgó tras {elapsed:.2f}s"
            )

            try:

                await message.reply(
                    "Perdón, me tardé demasiado "
                    "pensando la respuesta, intenta de nuevo."
                )

            except discord.HTTPException:
                pass

        except Exception as error:

            print(
                f"[ERROR] {conversation_id} "
                f"-> {type(error).__name__}: {error}"
            )

            # Actualizar dashboard incluso si la IA falla.
            await update_provider_dashboard()

            try:

                await message.reply(
                    "Perdón, tuve un pequeño problema "
                    "intentando responderte."
                )

            except discord.HTTPException:
                pass


# ============================================================
# MENSAJES ESPONTÁNEOS
# ============================================================

async def idle_message_loop():

    await bot.wait_until_ready()

    print(
        "[IDLE] Sistema de mensajes espontáneos iniciado."
    )

    while not bot.is_closed():

        try:

            config = config_manager.data

            # Todavía no configurado.
            if (
                config.guild_id is None
                or config.chat_channel_id is None
            ):
                await asyncio.sleep(10)
                continue

            frequency_seconds = (
                config.message_frequency_minutes
                * 60
            )

            now = time.time()

            elapsed = (
                now
                - config.last_activity_ts
            )

            remaining = (
                frequency_seconds
                - elapsed
            )

            # Todavía no ha pasado el tiempo.
            if remaining > 0:

                await asyncio.sleep(
                    min(
                        10,
                        max(
                            1,
                            remaining,
                        ),
                    )
                )

                continue

            # =================================================
            # RESERVAR EL CICLO
            # =================================================

            # Evita que varias iteraciones detecten
            # simultáneamente la misma inactividad.
            await config_manager.touch_activity()

            channel = bot.get_channel(
                config.chat_channel_id
            )

            if channel is None:

                try:
                    channel = await bot.fetch_channel(
                        config.chat_channel_id
                    )

                except Exception as error:

                    print(
                        f"[IDLE] No se pudo obtener "
                        f"el canal: {error}"
                    )

                    continue

            print(
                "[IDLE] Generando mensaje espontáneo..."
            )

            idle_prompt = (
                prompt_builder.build_idle_message_prompt()
            )

            async with ai_semaphore:

                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        ai.generate,
                        messages=idle_prompt,
                        model=character.ai_settings.model,
                        temperature=character.ai_settings.temperature,
                        max_tokens=min(
                            character.ai_settings.max_tokens,
                            150,
                        ),
                    ),
                    timeout=AI_TIMEOUT,
                )

            await update_provider_dashboard()

            response = response.strip()

            if response:

                await channel.send(
                    response
                )

                print(
                    f"[IDLE] Mensaje enviado: "
                    f"{response[:100]}"
                )

        except asyncio.CancelledError:
            raise

        except asyncio.TimeoutError:

            print(
                "[IDLE] Timeout generando mensaje."
            )

        except Exception as error:

            print(
                f"[IDLE] Error: "
                f"{type(error).__name__}: {error}"
            )

        await asyncio.sleep(10)


# ============================================================
# MAIN
# ============================================================

async def main():

    await start_keep_alive_server()

    asyncio.create_task(
        idle_message_loop()
    )

    await bot.start(TOKEN)


asyncio.run(main())
