"""
Bangkok Airways PTFS Bot - Passengers Cog

Provides additional passenger-related utilities.
Currently serves as an extension point for future features.
"""

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils import read_json


class Passengers(commands.Cog):
    """
    Cog for passenger-related commands and utilities.

    Commands:
        /mybookings - View all flights the user has booked.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the Passengers cog."""
        self.bot = bot

    @app_commands.command(
        name='mybookings',
        description='View all your flight bookings',
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def my_bookings(self, interaction: discord.Interaction) -> None:
        """Display all flights the user has booked."""
        bookings = read_json(Config.BOOKINGS_FILE, [])
        flights = read_json(Config.FLIGHTS_FILE, [])

        user_bookings = [
            b for b in bookings if b['user_id'] == interaction.user.id
        ]

        if not user_bookings:
            embed = discord.Embed(
                title=f'{Config.IATA_CODE} My Bookings',
                description='You have no active bookings.',
                color=0x95a5a6,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} My Bookings',
            description=f'Your active bookings: **{len(user_bookings)}**',
            color=0x2ecc71,
            timestamp=discord.utils.utcnow(),
        )

        for booking in user_bookings:
            flight = next(
                (f for f in flights if f['flight_id'] == booking['flight_id']),
                None,
            )
            if flight:
                route = f'{flight['departure']} → {flight['arrival']}'
                value = (
                    f'**Route:** {route}\n'
                    f'**Aircraft:** {flight['aircraft']} | **Gate:** {flight['gate']}\n'
                    f'**Booking ID:** {booking['booking_id']}\n'
                    f'**Status:** {flight['status']}'
                )
                embed.add_field(
                    name=f'{flight['flight_number']} ({flight['flight_id']})',
                    value=value,
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f'Unknown Flight ({booking['flight_id']})',
                    value='Flight details no longer available.',
                    inline=False,
                )

        embed.set_footer(text='Powered by Bangkok Airways Bot')
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @my_bookings.error
    async def my_bookings_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /mybookings."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before trying again.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An error occurred: {error}',
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    """Add the Passengers cog to the bot."""
    await bot.add_cog(Passengers(bot))
