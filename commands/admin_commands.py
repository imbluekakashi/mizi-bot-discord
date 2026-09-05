import os

import discord
from discord import app_commands

from ai.provider_monitor import ProviderMonitor


class AdminCommands:
    def __init__(self, bot, config_manager, provider_monitor: ProviderMonitor):
        self.bot = bot
        self.config_manager = config_manager
        self.provider_monitor = provider_monitor

        self.setup_command = app_commands.Command(
            name="setup",
            description="Configura el servidor autorizado para Mizi.",
            callback=self.setup,
        )

        self.setchannel_command = app_commands.Command(
            name="setchannel",
            description="Establece este canal como el canal de conversación de Mizi.",
            callback=self.setchannel,
        )

        self.setmessagefrequency_command = app_commands.Command(
            name="setmessagefrequency",
            description="Establece cada cuántos minutos Mizi hablará si nadie escribe.",
            callback=self.setmessagefrequency,
        )

        self.setchannellogs_command = app_commands.Command(
            name="setchannellogs",
            description="Establece este canal como panel de monitoreo de proveedores.",
            callback=self.setchannellogs,
        )

    async def setup(
        self,
        interaction: discord.Interaction,
        password: str,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Necesitas permisos de Administrador.",
                ephemeral=True,
            )
            return

        expected_password = os.getenv("MIZI_SETUP_PASSWORD")

        if not expected_password:
            await interaction.response.send_message(
                "❌ MIZI_SETUP_PASSWORD no está configurada en Render.",
                ephemeral=True,
            )
            return

        if password != expected_password:
            await interaction.response.send_message(
                "❌ Contraseña incorrecta.",
                ephemeral=True,
            )
            return

        config = self.config_manager.data

        if (
            config.guild_id is not None
            and config.guild_id != interaction.guild.id
        ):
            await interaction.response.send_message(
                "❌ Mizi ya está configurada en otro servidor.",
                ephemeral=True,
            )
            return

        try:
            await self.config_manager.setup_guild(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
            )
        except Exception as error:
            print(f"[COMMAND ERROR] /setup -> {error}")

            await interaction.response.send_message(
                "❌ No se pudo guardar la configuración del servidor.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "✅ **Servidor autorizado correctamente.**\n\n"
            "Ahora puedes usar `/setchannel` para elegir "
            "el canal donde Mizi conversará.",
            ephemeral=True,
        )

    async def setchannel(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Necesitas permisos de Administrador.",
                ephemeral=True,
            )
            return

        config = self.config_manager.data

        if config.guild_id is None:
            await interaction.response.send_message(
                "❌ Primero debes utilizar `/setup`.",
                ephemeral=True,
            )
            return

        if config.guild_id != interaction.guild.id:
            await interaction.response.send_message(
                "❌ Este servidor no está autorizado para utilizar Mizi.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Este comando debe utilizarse en un canal de texto.",
                ephemeral=True,
            )
            return

        try:
            # IMPORTANTE:
            # ConfigManager.set_chat_channel() ES async.
            await self.config_manager.set_chat_channel(
                interaction.channel.id
            )
        except Exception as error:
            print(f"[COMMAND ERROR] /setchannel -> {error}")

            await interaction.response.send_message(
                "❌ No se pudo guardar este canal.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ **Canal configurado.**\n\n"
            f"Mizi ahora solo conversará en {interaction.channel.mention}.\n"
            f"Los mensajes humanos en este canal reiniciarán "
            f"el temporizador de actividad.",
            ephemeral=True,
        )

    async def setmessagefrequency(
        self,
        interaction: discord.Interaction,
        minutes: int,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Necesitas permisos de Administrador.",
                ephemeral=True,
            )
            return

        config = self.config_manager.data

        if config.guild_id is None:
            await interaction.response.send_message(
                "❌ Primero debes utilizar `/setup`.",
                ephemeral=True,
            )
            return

        if config.guild_id != interaction.guild.id:
            await interaction.response.send_message(
                "❌ Este servidor no está autorizado para utilizar Mizi.",
                ephemeral=True,
            )
            return

        if minutes < 1 or minutes > 1440:
            await interaction.response.send_message(
                "❌ Los minutos deben estar entre **1 y 1440**.",
                ephemeral=True,
            )
            return

        try:
            await self.config_manager.set_frequency(minutes)
        except Exception as error:
            print(
                f"[COMMAND ERROR] /setmessagefrequency -> {error}"
            )

            await interaction.response.send_message(
                "❌ No se pudo guardar la frecuencia.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Frecuencia configurada a **{minutes} minuto(s)**.\n\n"
            "Si nadie escribe durante ese tiempo, Mizi podrá "
            "enviar un mensaje espontáneo.",
            ephemeral=True,
        )

    async def setchannellogs(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Necesitas permisos de Administrador.",
                ephemeral=True,
            )
            return

        config = self.config_manager.data

        if config.guild_id is None:
            await interaction.response.send_message(
                "❌ Primero debes utilizar `/setup`.",
                ephemeral=True,
            )
            return

        if config.guild_id != interaction.guild.id:
            await interaction.response.send_message(
                "❌ Este servidor no está autorizado para utilizar Mizi.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Este comando debe utilizarse en un canal de texto.",
                ephemeral=True,
            )
            return

        models = {}

        if hasattr(self.bot, "character"):
            models = self.bot.character.ai_settings.provider_models

        embed = self.provider_monitor.build_embed(models)

        await interaction.response.send_message(
            embed=embed
        )

        try:
            message = await interaction.original_response()

            await self.config_manager.set_logs_channel(
                interaction.channel.id,
                message.id,
            )

            await message.edit(
                embed=self.provider_monitor.build_embed(models)
            )

        except Exception as error:
            print(
                f"[COMMAND ERROR] /setchannellogs -> {error}"
            )

    def register(self):
        self.bot.tree.add_command(self.setup_command)
        self.bot.tree.add_command(self.setchannel_command)
        self.bot.tree.add_command(
            self.setmessagefrequency_command
        )
        self.bot.tree.add_command(
            self.setchannellogs_command
        )
