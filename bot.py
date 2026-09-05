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
from keep_alive import start_keep_alive_server
from memory.conversation_memory import ConversationMemory
from models.character import Character


load_dotenv()


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "No se encontró DISCORD_TOKEN en las variables de entorno."
    )


DB_TIMEOUT = int(
    os.getenv("MIZI_DB_TIMEOUT", "15")
)

AI_TIMEOUT = int(
    os.getenv("MIZI_AI_TIMEOUT", "45")
)

MAX_CONCURRENT_AI = int(
    os.getenv("MIZI_MAX_CONCURRENT_AI", "3")
)


# ============================================================
# DISCORD
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# ============================================================
# COMPONENTES
# ============================================================

character = Character()

init_db()

prompt_builder = PromptBuilder(
    character
)

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


# ============================================================
# CONTROL DE CONCURRENCIA
# ============================================================

ai_semaphore = asyncio.Semaphore(
    MAX_CONCURRENT_AI
)


# ============================================================
# EMOJIS
# ============================================================

LETTER_EMOJI = {
    chr(code): chr(
        0x1F1E6 + code - ord("A")
    )
    for code in range(
        ord("A"),
        ord("Z") + 1,
    )
}


# ============================================================
# UTILIDADES
# ============================================================

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

    if not parts:
        return [
            response.strip()
        ]

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
                LETTER_EMOJI[
                    part.upper()
                ]
            )
        else:
            emojis.append(part)

    return emojis


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


async def run_db(
    function,
    *args,
    **kwargs,
):

    return await asyncio.wait_for(
        asyncio.to_thread(
            function,
            *args,
            **kwargs,
        ),
        timeout=DB_TIMEOUT,
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

    print("=" * 60)


# ============================================================
# MENSAJES
# ============================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # --------------------------------------------------------
    # Si no menciona a Mizi, dejamos que los comandos funcionen
    # --------------------------------------------------------

    if bot.user not in message.mentions:

        await bot.process_commands(
            message
        )

        return

    # --------------------------------------------------------
    # Extraer mensaje
    # --------------------------------------------------------

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
            channel_id=str(
                message.channel.id
            ),
            user_id=str(
                message.author.id
            ),
        )
    )

    start_time = time.monotonic()

    try:

        print(
            f"[FLOW] {conversation_id} -> DB"
        )

        # ----------------------------------------------------
        # Crear conversación
        # ----------------------------------------------------

        await run_db(
            memory.ensure_conversation,
            conversation_id=conversation_id,
            character_id="mizi",
            user_id=str(
                message.author.id
            ),
            guild_id=(
                str(message.guild.id)
                if message.guild
                else None
            ),
            channel_id=str(
                message.channel.id
            ),
        )

        # ----------------------------------------------------
        # Historial
        # ----------------------------------------------------

        history = await run_db(
            memory.get_history,
            conversation_id,
        )

        # ----------------------------------------------------
        # Prompt
        # ----------------------------------------------------

        messages = (
            prompt_builder.build_messages(
                user_message,
                history=history,
            )
        )

        print(
            f"[FLOW] {conversation_id} -> AI"
        )

        # ----------------------------------------------------
        # Generación
        # ----------------------------------------------------

        async with message.channel.typing():

            response = await run_ai(
                messages
            )

        response = response.strip()

        if not response:
            raise RuntimeError(
                "La IA devolvió una respuesta vacía."
            )

        # ----------------------------------------------------
        # MODO REACCIÓN
        # ----------------------------------------------------

        if response.upper().startswith(
            "REACCIONAR:"
        ):

            print(
                f"[FLOW] {conversation_id} -> reacción"
            )

            spec = response.split(
                ":",
                1,
            )[1]

            emojis = (
                resolve_reaction_emojis(
                    spec
                )
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

        # ----------------------------------------------------
        # RESPUESTA NORMAL
        # ----------------------------------------------------

        else:

            print(
                f"[FLOW] {conversation_id} -> guardando"
            )

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

            parts = split_response(
                response
            )

            for index, part in enumerate(
                parts
            ):

                if index > 0:

                    async with (
                        message.channel.typing()
                    ):

                        await asyncio.sleep(
                            random.uniform(
                                0.8,
                                2.0,
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
            f"-> {elapsed:.2f}s"
        )

        try:

            await message.reply(
                "Perdón 😭 me tardé demasiado pensando. Intenta de nuevo."
            )

        except discord.HTTPException:
            pass

    except Exception as error:

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


# ============================================================
# MENSAJES ESPONTÁNEOS
# ============================================================

async def idle_message_loop():

    await bot.wait_until_ready()

    channel_id = os.getenv(
        "MIZI_IDLE_CHANNEL_ID"
    )

    if not channel_id:

        print(
            "[IDLE] MIZI_IDLE_CHANNEL_ID "
            "no configurado."
        )

        return

    try:

        channel = bot.get_channel(
            int(channel_id)
        )

    except ValueError:

        print(
            "[IDLE] MIZI_IDLE_CHANNEL_ID "
            "no es válido."
        )

        return

    if channel is None:

        print(
            "[IDLE] No se encontró "
            "el canal configurado."
        )

        return

    while not bot.is_closed():

        wait_seconds = random.uniform(
            3 * 3600,
            7 * 3600,
        )

        await asyncio.sleep(
            wait_seconds
        )

        if random.random() > 0.5:
            continue

        try:

            idle_prompt = (
                prompt_builder
                .build_idle_message_prompt()
            )

            response = await run_ai(
                idle_prompt
            )

            response = response.strip()

            if not response:
                continue

            await channel.send(
                response
            )

            print(
                "[IDLE] Mensaje espontáneo enviado:",
                response[:80],
            )

        except Exception as error:

            print(
                "[IDLE] Error:",
                type(error).__name__,
                error,
            )


# ============================================================
# MAIN
# ============================================================

async def main():

    await start_keep_alive_server()

    asyncio.create_task(
        idle_message_loop()
    )

    await bot.start(
        TOKEN
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
