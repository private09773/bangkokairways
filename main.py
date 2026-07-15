"""
Bangkok Airways PTFS Bot - Main Entry Point

A production-ready Discord bot for Bangkok Airways PTFS using discord.py 2.x.
Features slash commands, modular cogs, and JSON-based data storage.

Usage:
    python main.py

Requirements:
    - Python 3.12+
    - discord.py>=2.3.0
    - python-dotenv>=1.0.0
"""

import asyncio
import os

import discord
from discord.ext import commands

from config import Config
from utils import ensure_file_exists


class BangkokAirwaysBot(commands.Bot):
    """
    Main bot class for Bangkok Airways PTFS.

    Attributes:
        config: Bot configuration loaded from Config class.
    """

    def __init__(self) -> None:
        """
        Initialize the bot with default intents and command tree.

        Enables all necessary intents for slash commands and member tracking.
        """
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,  # Disable default help (slash commands only)
        )

    async def setup_hook(self) -> None:
        """
        Perform initial setup before the bot starts.

        - Ensures data directories and JSON files exist.
        - Loads all cogs from the cogs/ directory.
        - Syncs slash commands with Discord.
        """
        # Ensure data files exist
        ensure_file_exists(Config.FLIGHTS_FILE, [])
        ensure_file_exists(Config.BOOKINGS_FILE, [])
        ensure_file_exists(Config.CONFIG_FILE, {})

        # Load cogs
        cog_files = [
            'cogs.announcements',
            'cogs.flights',
            'cogs.passengers',
        ]

        for cog in cog_files:
            try:
                await self.load_extension(cog)
                print(f'Loaded cog: {cog}')
            except Exception as error:
                print(f'Failed to load cog {cog}: {error}')

        # Sync slash commands globally
        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} slash command(s) globally.')
        except Exception as error:
            print(f'Failed to sync commands: {error}')

    async def on_ready(self) -> None:
        """
        Event triggered when the bot is fully connected and ready.

        Sets the bot's presence and prints connection details.
        """
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=Config.BOT_STATUS,
        )
        await self.change_presence(activity=activity)

        print(f'\n{"=" * 50}')
        print(f'  Bangkok Airways PTFS Bot')
        print(f'  Logged in as: {self.user} (ID: {self.user.id})')
        print(f'  Guilds: {len(self.guilds)}')
        print(f'  Slash Commands: {len(self.tree.get_commands())}')
        print(f'{"=" * 50}\n')

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """
        Global error handler for prefix commands (legacy fallback).

        Args:
            ctx: The command context.
            error: The error that occurred.
        """
        if isinstance(error, commands.CommandNotFound):
            return
        print(f'Command error in {ctx.command}: {error}')

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """
        Global error handler for slash commands.

        Args:
            interaction: The interaction that triggered the error.
            error: The error that occurred.
        """
        if isinstance(error, app_commands.CommandOnCooldown):
            if interaction.response.is_done():
                await interaction.followup.send(
                    f'Cooldown active. Try again in {error.retry_after:.1f}s.',
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f'Cooldown active. Try again in {error.retry_after:.1f}s.',
                    ephemeral=True,
                )
        else:
            print(f'Slash command error: {error}')
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    'An unexpected error occurred. Please try again later.',
                    ephemeral=True,
                )


def main() -> None:
    """
    Main entry point for the bot.

    Creates the bot instance and starts the event loop.
    """
    bot = BangkokAirwaysBot()

    try:
        bot.run(Config.DISCORD_TOKEN)
    except discord.LoginFailure:
        print('ERROR: Invalid Discord token. Check your .env file.')
    except Exception as error:
        print(f'ERROR: {error}')


if __name__ == '__main__':
    main()
