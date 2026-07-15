# Bangkok Airways PTFS Bot

A production-ready Discord bot for Bangkok Airways PTFS (Pilot Training Flight Simulator) built with `discord.py` 2.x.

## Features

- **Slash Commands Only** — Modern Discord interactions via `app_commands`
- **Modular Cog Structure** — Easy to extend and maintain
- **JSON Data Storage** — No database setup required
- **Flight Management** — Plan flights, book seats, view manifests
- **Announcements** — Professional embeds with role-based permissions
- **Bangkok Airways Branding** — Real IATA (`PG`) and ICAO (`BKP`) codes

## Project Structure

```
/
├── main.py                 # Bot entry point
├── config.py               # Configuration & environment variables
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment file
├── README.md               # This file
├── data/                   # JSON data storage
│   ├── flights.json
│   ├── bookings.json
│   └── config.json
├── cogs/                   # Command modules
│   ├── announcements.py
│   ├── flights.py
│   └── passengers.py
└── utils/                  # Utilities
    ├── __init__.py
    └── json_manager.py
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DISCORD_TOKEN=your_bot_token_here
ANNOUNCEMENT_CHANNEL_ID=your_announcement_channel_id_here
```

> Get your bot token from [Discord Developer Portal](https://discord.com/developers/applications).
> Enable **Message Content Intent** and **Server Members Intent** in the Bot tab.

### 3. Invite the Bot

Use this URL generator with scopes `bot` and `applications.commands`:

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

### 4. Run the Bot

```bash
python main.py
```

## Commands

### Announcements
| Command | Description | Permission |
|---------|-------------|------------|
| `/announcement` | Create a professional announcement embed | Admin / Announcement Manager |

### Flights
| Command | Description |
|---------|-------------|
| `/flight-plan` | Plan a new flight (modal) |
| `/flights` | List all scheduled flights |
| `/myflights` | View flights you created |
| `/book <flight_number>` | Book a seat on a flight |
| `/passengers <flight_number>` | View passenger manifest |
| `/cancel <flight_number>` | Cancel your booking |
| `/deleteflight <flight_number>` | Delete a flight (creator/admin) |

### Passengers
| Command | Description |
|---------|-------------|
| `/mybookings` | View all your active bookings |

## Data Storage

All data is stored in JSON files under `data/`:

- **flights.json** — Flight records with auto-generated IDs
- **bookings.json** — Passenger bookings linked to flights
- **config.json** — Runtime configuration

Files are created automatically on first run. The JSON manager uses atomic writes to prevent data corruption.

## Hosting on BotHosting.net

1. Upload all files (preserve directory structure).
2. Set your `DISCORD_TOKEN` in the hosting panel's environment variables.
3. Set the startup file to `main.py`.
4. The bot will auto-create JSON files in the `data/` directory.

## License

MIT License — Free for personal and commercial use.
