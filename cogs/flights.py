"""
Bangkok Airways PTFS Bot - Flights Cog

Manages flight planning, listing, booking, and cancellation.
All data stored in JSON files (flights.json and bookings.json).
"""

import uuid
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils import read_json, write_json


class FlightPlanModal(discord.ui.Modal, title='Plan a New Flight'):
    """
    Modal for creating a new flight plan.

    Fields:
        - Flight Number: e.g., PG123
        - Departure Airport: e.g., VTBS
        - Arrival Airport: e.g., VTCC
        - Aircraft: e.g., A320
        - Gate: e.g., A12
    """

    flight_number = discord.ui.TextInput(
        label='Flight Number',
        placeholder='PG123',
        max_length=10,
        required=True,
    )

    departure = discord.ui.TextInput(
        label='Departure Airport (ICAO)',
        placeholder='VTBS',
        max_length=10,
        required=True,
    )

    arrival = discord.ui.TextInput(
        label='Arrival Airport (ICAO)',
        placeholder='VTCC',
        max_length=10,
        required=True,
    )

    aircraft = discord.ui.TextInput(
        label='Aircraft Type',
        placeholder='A320',
        max_length=20,
        required=True,
    )

    gate = discord.ui.TextInput(
        label='Gate',
        placeholder='A12',
        max_length=10,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle flight plan creation."""
        flights = read_json(Config.FLIGHTS_FILE, [])

        # Normalize flight number
        flight_number = self.flight_number.value.strip().upper()

        # Check for duplicate flight numbers
        if any(f['flight_number'] == flight_number for f in flights):
            await interaction.response.send_message(
                f'Flight number **{flight_number}** already exists.',
                ephemeral=True,
            )
            return

        # Create new flight entry
        new_flight = {
            'flight_id': str(uuid.uuid4())[:8].upper(),
            'flight_number': flight_number,
            'departure': self.departure.value.strip().upper(),
            'arrival': self.arrival.value.strip().upper(),
            'aircraft': self.aircraft.value.strip().upper(),
            'gate': self.gate.value.strip().upper(),
            'captain': interaction.user.display_name,
            'captain_id': interaction.user.id,
            'first_officer': None,
            'first_officer_id': None,
            'notes': '',
            'status': 'Scheduled',
            'creator_id': interaction.user.id,
            'passenger_count': 0,
            'created_at': discord.utils.utcnow().isoformat(),
        }

        flights.append(new_flight)
        write_json(Config.FLIGHTS_FILE, flights)

        # Build confirmation embed
        embed = discord.Embed(
            title=f'{Config.IATA_CODE} Flight Plan Created',
            description=f'Flight **{flight_number}** has been scheduled successfully.',
            color=0x2ecc71,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name='Route', value=f'{new_flight['departure']} → {new_flight['arrival']}', inline=True)
        embed.add_field(name='Aircraft', value=new_flight['aircraft'], inline=True)
        embed.add_field(name='Gate', value=new_flight['gate'], inline=True)
        embed.add_field(name='Flight ID', value=new_flight['flight_id'], inline=True)
        embed.add_field(name='Captain', value=interaction.user.mention, inline=True)
        embed.add_field(name='Status', value=new_flight['status'], inline=True)
        embed.set_footer(text='Powered by Bangkok Airways Bot')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """Handle modal errors."""
        await interaction.response.send_message(
            f'An error occurred: {error}',
            ephemeral=True,
        )


class Flights(commands.Cog):
    """
    Cog for managing flight operations.

    Commands:
        /flight-plan    - Create a new flight plan
        /flights        - List all scheduled flights
        /myflights      - List flights created by the user
        /book           - Book a seat on a flight
        /passengers     - View passengers on a flight
        /cancel         - Cancel a booking
        /deleteflight   - Delete a flight (creator or admin)
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the Flights cog."""
        self.bot = bot

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def _get_flight_by_id(self, flight_id: str) -> dict | None:
        """Retrieve a flight by its unique ID."""
        flights = read_json(Config.FLIGHTS_FILE, [])
        for flight in flights:
            if flight['flight_id'].upper() == flight_id.upper():
                return flight
        return None

    def _get_flight_by_number(self, flight_number: str) -> dict | None:
        """Retrieve a flight by its flight number."""
        flights = read_json(Config.FLIGHTS_FILE, [])
        flight_number = flight_number.strip().upper()
        for flight in flights:
            if flight['flight_number'].upper() == flight_number:
                return flight
        return None

    def _update_passenger_count(self, flight_id: str) -> None:
        """Recalculate and update passenger count for a flight."""
        flights = read_json(Config.FLIGHTS_FILE, [])
        bookings = read_json(Config.BOOKINGS_FILE, [])

        count = sum(
            1 for b in bookings if b['flight_id'].upper() == flight_id.upper()
        )

        for flight in flights:
            if flight['flight_id'].upper() == flight_id.upper():
                flight['passenger_count'] = count
                break

        write_json(Config.FLIGHTS_FILE, flights)

    def _get_bookings_for_flight(self, flight_id: str) -> list[dict]:
        """Get all bookings for a specific flight."""
        bookings = read_json(Config.BOOKINGS_FILE, [])
        return [
            b for b in bookings
            if b['flight_id'].upper() == flight_id.upper()
        ]

    # ------------------------------------------------------------------
    # /flight-plan
    # ------------------------------------------------------------------

    @app_commands.command(
        name='flight-plan',
        description='Plan a new Bangkok Airways flight',
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def flight_plan(self, interaction: discord.Interaction) -> None:
        """Open the flight plan creation modal."""
        await interaction.response.send_modal(FlightPlanModal())

    @flight_plan.error
    async def flight_plan_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /flight-plan."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before planning another flight.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An error occurred: {error}',
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /flights
    # ------------------------------------------------------------------

    @app_commands.command(
        name='flights',
        description='List all scheduled flights',
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def flights_list(self, interaction: discord.Interaction) -> None:
        """Display all scheduled flights."""
        flights = read_json(Config.FLIGHTS_FILE, [])

        if not flights:
            embed = discord.Embed(
                title=f'{Config.IATA_CODE} Flight Schedule',
                description='No flights are currently scheduled.',
                color=0x95a5a6,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} Flight Schedule',
            description=f'Total flights: **{len(flights)}**',
            color=0x3498db,
            timestamp=discord.utils.utcnow(),
        )

        for flight in flights:
            route = f'{flight['departure']} → {flight['arrival']}'
            value = (
                f'**Aircraft:** {flight['aircraft']} | **Gate:** {flight['gate']}\n'
                f'**Captain:** {flight['captain']}\n'
                f'**Passengers:** {flight['passenger_count']}\n'
                f'**Status:** {flight['status']}'
            )
            embed.add_field(
                name=f'{flight['flight_number']} ({flight['flight_id']}) — {route}',
                value=value,
                inline=False,
            )

        embed.set_footer(text='Powered by Bangkok Airways Bot')
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @flights_list.error
    async def flights_list_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /flights."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before listing flights again.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An error occurred: {error}',
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /myflights
    # ------------------------------------------------------------------

    @app_commands.command(
        name='myflights',
        description='View flights you have created',
    )
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def my_flights(self, interaction: discord.Interaction) -> None:
        """Display flights created by the invoking user."""
        flights = read_json(Config.FLIGHTS_FILE, [])
        user_flights = [f for f in flights if f['creator_id'] == interaction.user.id]

        if not user_flights:
            embed = discord.Embed(
                title=f'{Config.IATA_CODE} My Flights',
                description='You have not created any flights yet.',
                color=0x95a5a6,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} My Flights',
            description=f'Your flights: **{len(user_flights)}**',
            color=0x9b59b6,
            timestamp=discord.utils.utcnow(),
        )

        for flight in user_flights:
            route = f'{flight['departure']} → {flight['arrival']}'
            value = (
                f'**Aircraft:** {flight['aircraft']} | **Gate:** {flight['gate']}\n'
                f'**Passengers:** {flight['passenger_count']}\n'
                f'**Status:** {flight['status']}'
            )
            embed.add_field(
                name=f'{flight['flight_number']} ({flight['flight_id']}) — {route}',
                value=value,
                inline=False,
            )

        embed.set_footer(text='Powered by Bangkok Airways Bot')
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @my_flights.error
    async def my_flights_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /myflights."""
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

    # ------------------------------------------------------------------
    # /book
    # ------------------------------------------------------------------

    @app_commands.command(
        name='book',
        description='Book a seat on a flight',
    )
    @app_commands.describe(flight_number='The flight number to book (e.g., PG123)')
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def book(
        self, interaction: discord.Interaction, flight_number: str
    ) -> None:
        """Book a seat on the specified flight."""
        flight = self._get_flight_by_number(flight_number)

        if flight is None:
            embed = discord.Embed(
                title='Flight Not Found',
                description=f'No flight found with number **{flight_number.upper()}**.',
                color=0xe74c3c,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        bookings = read_json(Config.BOOKINGS_FILE, [])

        # Check if user already booked this flight
        existing = any(
            b['flight_id'] == flight['flight_id'] and b['user_id'] == interaction.user.id
            for b in bookings
        )
        if existing:
            embed = discord.Embed(
                title='Already Booked',
                description=f'You have already booked **{flight['flight_number']}**.',
                color=0xf1c40f,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create booking
        new_booking = {
            'booking_id': str(uuid.uuid4())[:8].upper(),
            'flight_id': flight['flight_id'],
            'flight_number': flight['flight_number'],
            'user_id': interaction.user.id,
            'user_name': interaction.user.display_name,
            'booked_at': discord.utils.utcnow().isoformat(),
        }

        bookings.append(new_booking)
        write_json(Config.BOOKINGS_FILE, bookings)

        # Update passenger count
        self._update_passenger_count(flight['flight_id'])

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} Booking Confirmed',
            description=f'You have successfully booked **{flight['flight_number']}**.',
            color=0x2ecc71,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name='Route', value=f'{flight['departure']} → {flight['arrival']}', inline=True)
        embed.add_field(name='Aircraft', value=flight['aircraft'], inline=True)
        embed.add_field(name='Gate', value=flight['gate'], inline=True)
        embed.add_field(name='Booking ID', value=new_booking['booking_id'], inline=True)
        embed.set_footer(text='Powered by Bangkok Airways Bot')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @book.error
    async def book_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /book."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before booking again.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An error occurred: {error}',
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /passengers
    # ------------------------------------------------------------------

    @app_commands.command(
        name='passengers',
        description='View passengers on a specific flight',
    )
    @app_commands.describe(flight_number='The flight number to check (e.g., PG123)')
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def passengers(
        self, interaction: discord.Interaction, flight_number: str
    ) -> None:
        """Display all passengers booked on a flight."""
        flight = self._get_flight_by_number(flight_number)

        if flight is None:
            embed = discord.Embed(
                title='Flight Not Found',
                description=f'No flight found with number **{flight_number.upper()}**.',
                color=0xe74c3c,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        bookings = self._get_bookings_for_flight(flight['flight_id'])

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} Passenger Manifest',
            description=f'Flight **{flight['flight_number']}** ({flight['flight_id']})',
            color=0x3498db,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name='Route', value=f'{flight['departure']} → {flight['arrival']}', inline=True)
        embed.add_field(name='Aircraft', value=flight['aircraft'], inline=True)
        embed.add_field(name='Total Passengers', value=str(len(bookings)), inline=True)

        if bookings:
            passenger_list = '\n'.join(
                f'{i + 1}. {b['user_name']}' for i, b in enumerate(bookings)
            )
            embed.add_field(
                name='Passengers',
                value=passenger_list[:1024] or 'None',
                inline=False,
            )
        else:
            embed.add_field(
                name='Passengers',
                value='No bookings yet.',
                inline=False,
            )

        embed.set_footer(text='Powered by Bangkok Airways Bot')
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @passengers.error
    async def passengers_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /passengers."""
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

    # ------------------------------------------------------------------
    # /cancel
    # ------------------------------------------------------------------

    @app_commands.command(
        name='cancel',
        description='Cancel your booking on a flight',
    )
    @app_commands.describe(flight_number='The flight number to cancel (e.g., PG123)')
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def cancel(
        self, interaction: discord.Interaction, flight_number: str
    ) -> None:
        """Cancel the user's booking on the specified flight."""
        flight = self._get_flight_by_number(flight_number)

        if flight is None:
            embed = discord.Embed(
                title='Flight Not Found',
                description=f'No flight found with number **{flight_number.upper()}**.',
                color=0xe74c3c,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        bookings = read_json(Config.BOOKINGS_FILE, [])
        original_count = len(bookings)

        # Remove user's booking for this flight
        bookings = [
            b for b in bookings
            if not (b['flight_id'] == flight['flight_id'] and b['user_id'] == interaction.user.id)
        ]

        if len(bookings) == original_count:
            embed = discord.Embed(
                title='No Booking Found',
                description=f'You do not have a booking on **{flight['flight_number']}**.',
                color=0xf1c40f,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        write_json(Config.BOOKINGS_FILE, bookings)
        self._update_passenger_count(flight['flight_id'])

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} Booking Cancelled',
            description=f'Your booking on **{flight['flight_number']}** has been cancelled.',
            color=0xe74c3c,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name='Route', value=f'{flight['departure']} → {flight['arrival']}', inline=True)
        embed.add_field(name='Aircraft', value=flight['aircraft'], inline=True)
        embed.add_field(name='Gate', value=flight['gate'], inline=True)
        embed.set_footer(text='Powered by Bangkok Airways Bot')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @cancel.error
    async def cancel_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /cancel."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before cancelling again.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An error occurred: {error}',
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /deleteflight
    # ------------------------------------------------------------------

    @app_commands.command(
        name='deleteflight',
        description='Delete a flight (Creator or Admin only)',
    )
    @app_commands.describe(flight_number='The flight number to delete (e.g., PG123)')
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def delete_flight(
        self, interaction: discord.Interaction, flight_number: str
    ) -> None:
        """Delete a flight and all associated bookings."""
        flights = read_json(Config.FLIGHTS_FILE, [])
        flight = self._get_flight_by_number(flight_number)

        if flight is None:
            embed = discord.Embed(
                title='Flight Not Found',
                description=f'No flight found with number **{flight_number.upper()}**.',
                color=0xe74c3c,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check permissions: creator or admin
        is_creator = flight['creator_id'] == interaction.user.id
        is_admin = interaction.user.guild_permissions.administrator

        if not (is_creator or is_admin):
            embed = discord.Embed(
                title='Permission Denied',
                description='Only the flight creator or an Administrator can delete this flight.',
                color=0xe74c3c,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Remove the flight
        flights = [f for f in flights if f['flight_id'] != flight['flight_id']]
        write_json(Config.FLIGHTS_FILE, flights)

        # Remove all bookings for this flight
        bookings = read_json(Config.BOOKINGS_FILE, [])
        original_booking_count = len(bookings)
        bookings = [b for b in bookings if b['flight_id'] != flight['flight_id']]
        write_json(Config.BOOKINGS_FILE, bookings)

        removed_bookings = original_booking_count - len(bookings)

        embed = discord.Embed(
            title=f'{Config.IATA_CODE} Flight Deleted',
            description=f'Flight **{flight['flight_number']}** has been deleted.',
            color=0xe74c3c,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name='Route', value=f'{flight['departure']} → {flight['arrival']}', inline=True)
        embed.add_field(name='Aircraft', value=flight['aircraft'], inline=True)
        embed.add_field(name='Bookings Removed', value=str(removed_bookings), inline=True)
        embed.set_footer(text='Powered by Bangkok Airways Bot')

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @delete_flight.error
    async def delete_flight_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for /deleteflight."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before deleting again.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An error occurred: {error}',
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    """Add the Flights cog to the bot."""
    await bot.add_cog(Flights(bot))
