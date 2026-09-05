import os

import discord
from discord import app_commands
from discord.ext import commands

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
                "❌ La contraseña de configuración no está configurada en Render.",
                ephemeral=True,
            )
            return

        if password != expected_password:
            await interaction.response.send_message(
                "❌ Contraseña incorrecta.",
                ephemeral=True,
            )
            return

        current_config = self.config_manager.config

        if (
            current_config.guild_id is not None
            and current_config.guild_id != str(interaction.guild.id)
        ):
            await interaction.response.send_message(
                "❌ Mizi ya está configurada en otro servidor.",
                ephemeral=True,
            )
            return

        success = self.config_manager.setup_guild(
            guild_id=str(interaction.guild.id),
            user_id=str(interaction.user.id),
        )

        if not success:
            await interaction.response.send_message(
                "❌ No se pudo guardar la configuración.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "✅ **Servidor autorizado correctamente.**\n\n"
            "Ahora puedes utilizar `/setchannel` para establecer "
            "el canal donde Mizi podrá conversar.",
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

        config = self.config_manager.config

        if config.guild_id is None:
            await interaction.response.send_message(
                "❌ Primero debes utilizar `/setup`.",
                ephemeral=True,
            )
            return

        if config.guild_id != str(interaction.guild.id):
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

        # IMPORTANTE:
        # set_chat_channel() es una función normal, NO async.
        # Por eso NO lleva "await".
        success = self.config_manager.set_chat_channel(
            channel_id=str(interaction.channel.id)
        )

        if not success:
            await interaction.response.send_message(
                "❌ No se pudo guardar este canal.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Este canal ({interaction.channel.mention}) "
            "ahora es el único canal donde Mizi podrá conversar.",
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

        config = self.config_manager.config

        if config.guild_id is None:
            await interaction.response.send_message(
                "❌ Primero debes utilizar `/setup`.",
                ephemeral=True,
            )
            return

        if config.guild_id != str(interaction.guild.id):
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

        success = self.config_manager.set_frequency(minutes)

        if not success:
            await interaction.response.send_message(
                "❌ No se pudo guardar la frecuencia.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Mizi enviará un mensaje espontáneo después de "
            f"**{minutes} minuto(s)** sin actividad.",
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

        config = self.config_manager.config

        if config.guild_id is None:
            await interaction.response.send_message(
                "❌ Primero debes utilizar `/setup`.",
                ephemeral=True,
            )
            return

        if config.guild_id != str(interaction.guild.id):
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

        # Creamos el dashboard inicial.
        embed = self.provider_monitor.build_embed()

        await interaction.response.send_message(
            embed=embed
        )

        message = await interaction.original_response()

        success = self.config_manager.set_logs_channel(
            channel_id=str(interaction.channel.id),
            message_id=str(message.id),
        )

        if not success:
            await message.edit(
                content="⚠️ El panel fue creado, pero no se pudo guardar su configuración.",
                embed=embed,
            )
            return

        await message.edit(
            embed=self.provider_monitor.build_embed()
        )

    def register(self):
        """
        Registra los comandos slash en el CommandTree del bot.
        """
        self.bot.tree.add_command(self.setup_command)
        self.bot.tree.add_command(self.setchannel_command)
        self.bot.tree.add_command(self.setmessagefrequency_command)
        self.bot.tree.add_command(self.setchannellogs_command)
