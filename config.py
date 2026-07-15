"""
Bangkok Airways PTFS Bot - Configuration

Central configuration file for the bot.
All settings are loaded from environment variables or defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Bot configuration class."""

    # Discord Bot Token (required)
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')

    # Announcement channel ID for /announcement command
    ANNOUNCEMENT_CHANNEL_ID: int = int(
        os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0')
    )

    # Bot settings
    COMMAND_PREFIX: str = '!'  # Legacy prefix (slash commands primary)
    BOT_STATUS: str = 'Bangkok Airways PTFS'

    # Airline codes
    IATA_CODE: str = 'PG'
    ICAO_CODE: str = 'BKP'

    # File paths
    DATA_DIR: str = 'data'
    FLIGHTS_FILE: str = 'data/flights.json'
    BOOKINGS_FILE: str = 'data/bookings.json'
    CONFIG_FILE: str = 'data/config.json'

    # Announcement type colors (Discord embed colors)
    ANNOUNCEMENT_COLORS: dict = {
        'General': 0x3498db,   # Blue
        'Flight': 0x2ecc71,    # Green
        'Event': 0xe74c3c,     # Red
        'Staff': 0xf1c40f,     # Yellow
    }

    # Role IDs for permission checks
    # Set to 0 to disable (uses Administrator permission instead)
    ANNOUNCEMENT_MANAGER_ROLE_ID: int = int(
        os.getenv('ANNOUNCEMENT_MANAGER_ROLE_ID', '0')
    )


# Validate token on import
if not Config.DISCORD_TOKEN:
    raise ValueError(
        'DISCORD_TOKEN not found. Please set it in your .env file.'
    )
