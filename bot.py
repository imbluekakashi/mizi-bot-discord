from keep_alive import start_keep_alive_server
from database.database import init_db

import asyncio
import os
import random

import discord

from discord.ext import commands
from dotenv import load_dotenv

from ai.prompt_builder import PromptBuilder
from ai.provider_factory import FallbackAIProvider
from memory.conversation_memory import ConversationMemory
from models.character import Character


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("No se encontró DISCORD_TOKEN en el archivo .env")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

character = Character()
init_db()
prompt_builder = PromptBuilder(character)
memory = ConversationMemory()

ai = FallbackAIProvider(character.ai_settings.fallback_providers)


def split_response(response: str, max_parts: int = 3) -> list[str]:
    parts = [part.strip() for part in response.split("|||")]
    parts = [part for part in parts if part]
    return parts[:max_parts] if parts else [response.strip()]


@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")
    print(f"ID: {bot.user.id}")
    print(f"Proveedores de IA: {character.ai_settings.fallback_providers}")
    print(f"Modelo: {character.ai_settings.model}")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if bot.user not in message.mentions:
        await bot.process_commands(message)
        return

    user_message = message.content.replace(f"<@{bot.user.id}>", "").strip()

    if not user_message:
        user_message = "Hola Mizi."

    conversation_id = ConversationMemory.build_conversation_id(
        channel_id=str(message.channel.id),
        user_id=str(message.author.id),
    )

    memory.ensure_conversation(
        conversation_id=conversation_id,
        character_id="mizi",
        user_id=str(message.author.id),
        guild_id=str(message.guild.id) if message.guild else None,
        channel_id=str(message.channel.id),
    )

    history = memory.get_history(conversation_id)

    messages = prompt_builder.build_messages(user_message, history=history)

    try:
        async with message.channel.typing():
            response = ai.generate(
                messages=messages,
                model=character.ai_settings.model,
                temperature=character.ai_settings.temperature,
                max_tokens=character.ai_settings.max_tokens,
            )

        memory.add_user_message(conversation_id, user_message)
        memory.add_assistant_message(conversation_id, response)

        parts = split_response(response)

        for index, part in enumerate(parts):
            if index > 0:
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(1.0, 2.5))

            if index == 0:
                await message.reply(part)
            else:
                await message.channel.send(part)

    except Exception as error:
        print("Error al generar respuesta:")
        print(error)

        await message.reply(
            "Perdón, tuve un pequeño problema intentando responderte."
        )

    await bot.process_commands(message)


async def main():
    await start_keep_alive_server()
    await bot.start(TOKEN)


import asyncio
asyncio.run(main())