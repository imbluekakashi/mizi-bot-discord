import asyncio
import os

import discord
from discord import app_commands


class AdminCommands:
    def __init__(self, bot, config_manager, dashboard):
        self.bot = bot
        self.config = config_manager
        self.dashboard = dashboard

    def _authorized_guild(self, interaction: discord.Interaction) -> bool:
        return bool(
            interaction.guild
            and self.config.data.guild_id == interaction.guild.id
        )

    def register(self):
        @self.bot.tree.command(
            name="setup",
            description="Configura Mizi en este servidor.",
        )
        @app_commands.describe(
            password="Contraseña de configuración.",
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def setup(
            interaction: discord.Interaction,
            password: str,
        ):
            if interaction.guild is None:
                await interaction.response.send_message(
                    "❌ Este comando solo funciona dentro de un servidor.",
                    ephemeral=True,
                )
                return

            expected = os.getenv("MIZI_SETUP_PASSWORD")

            if not expected:
                await interaction.response.send_message(
                    "❌ MIZI_SETUP_PASSWORD no está configurada en Render.",
                    ephemeral=True,
                )
                return

            config = self.config.data

            if (
                config.guild_id
                and config.guild_id != str(interaction.guild.id)
            ):
                await interaction.response.send_message(
                    "❌ Mizi ya está configurada para otro servidor.",
                    ephemeral=True,
                )
                return

            if password != expected:
                await interaction.response.send_message(
                    "❌ Contraseña incorrecta.",
                    ephemeral=True,
                )
                return

            await self.config.setup_guild(
                interaction.guild.id,
                interaction.user.id,
            )

            await interaction.response.send_message(
                "✅ Mizi quedó configurada para este servidor. "
                "Ahora usa `/setchannel` en el canal donde quieres que converse.",
                ephemeral=True,
            )

        @self.bot.tree.command(
            name="setchannel",
            description="Establece el canal donde Mizi puede conversar.",
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def setchannel(interaction: discord.Interaction):
            if not await self._authorized_guild(interaction):
                await interaction.response.send_message(
                    "❌ Este servidor no está autorizado para usar Mizi.",
                    ephemeral=True,
                )
                return

            if interaction.channel is None:
                await interaction.response.send_message(
                    "❌ No pude identificar este canal.",
                    ephemeral=True,
                )
                return

            self.config.set_chat_channel(
                interaction.channel.id
            )

            await interaction.response.send_message(
                f"✅ Mizi solo responderá en {interaction.channel.mention}. "
                "Los mensajes normales de este canal también reiniciarán "
                "su contador de inactividad.",
                ephemeral=True,
            )

        @self.bot.tree.command(
            name="setmessagefrequency",
            description="Define cada cuántos minutos Mizi puede hablar sola.",
        )
        @app_commands.describe(
            minutes="Minutos de inactividad antes de un mensaje espontáneo.",
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def setmessagefrequency(
            interaction: discord.Interaction,
            minutes: app_commands.Range[int, 1, 1440],
        ):
            if not await self._authorized_guild(interaction):
                await interaction.response.send_message(
                    "❌ Este servidor no está autorizado para usar Mizi.",
                    ephemeral=True,
                )
                return

            await self.config.set_frequency(
                int(minutes)
            )

            await interaction.response.send_message(
                f"✅ Frecuencia establecida en **{minutes} minutos**. "
                "Cada mensaje de usuario en el canal de Mizi reiniciará "
                "el contador.",
                ephemeral=True,
            )

        @self.bot.tree.command(
            name="setchannellogs",
            description="Establece este canal como dashboard de Mizi.",
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def setchannellogs(interaction: discord.Interaction):
            if not await self._authorized_guild(interaction):
                await interaction.response.send_message(
                    "❌ Este servidor no está autorizado para usar Mizi.",
                    ephemeral=True,
                )
                return

            if interaction.channel is None:
                await interaction.response.send_message(
                    "❌ No pude identificar este canal.",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True)

            embed = self.dashboard.build_embed()

            message = await interaction.channel.send(
                embed=embed
            )

            await self.config.set_logs_channel(
                interaction.channel.id,
                message.id,
            )

            await interaction.followup.send(
                "✅ Este canal es ahora el dashboard de logs de Mizi.",
                ephemeral=True,
            )

        @self.bot.tree.error
        async def on_tree_error(
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
        ):
            if isinstance(
                error,
                app_commands.MissingPermissions,
            ):
                if interaction.response.is_done():
                    await interaction.followup.send(
                        "❌ Necesitas permisos de administrador.",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        "❌ Necesitas permisos de administrador.",
                        ephemeral=True,
                    )
                return

            print(
                "[COMMAND ERROR]",
                repr(error),
            )

            if interaction.response.is_done():
                await interaction.followup.send(
                    "❌ Ocurrió un error ejecutando el comando.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ Ocurrió un error ejecutando el comando.",
                    ephemeral=True,
                )
