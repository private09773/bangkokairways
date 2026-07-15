"""
Bangkok Airways PTFS Bot - Announcements Cog

Provides the /announcement slash command with a Discord Modal.
Only accessible to Administrators or users with the Announcement Manager role.
"""

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils import read_json, write_json


class AnnouncementModal(discord.ui.Modal, title='Create Announcement'):
    """
    Modal for creating a new announcement.

    Fields:
        - Title: Announcement title
        - Description: Main announcement content
        - Type: Dropdown for announcement category
        - Image URL: Optional image to include
    """

    title_input = discord.ui.TextInput(
        label='Title',
        placeholder='Enter announcement title...',
        max_length=256,
        required=True,
    )

    description = discord.ui.TextInput(
        label='Description',
        placeholder='Enter announcement details...',
        style=discord.TextStyle.paragraph,
        max_length=4000,
        required=True,
    )

    announcement_type = discord.ui.TextInput(
        label='Type (General/Flight/Event/Staff)',
        placeholder='General',
        max_length=10,
        required=True,
        default='General',
    )

    image_url = discord.ui.TextInput(
        label='Image URL (Optional)',
        placeholder='https://example.com/image.png',
        required=False,
        default='',
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Handle modal submission and send the announcement embed."""
        # Validate announcement type
        announcement_type = self.announcement_type.value.strip().title()
        valid_types = list(Config.ANNOUNCEMENT_COLORS.keys())

        if announcement_type not in valid_types:
            await interaction.response.send_message(
                f'Invalid type. Please use one of: {', '.join(valid_types)}',
                ephemeral=True,
            )
            return

        # Get the configured announcement channel
        channel = interaction.client.get_channel(Config.ANNOUNCEMENT_CHANNEL_ID)

        if channel is None:
            await interaction.response.send_message(
                'Announcement channel not found. Please check the configuration.',
                ephemeral=True,
            )
            return

        # Build the embed
        embed_color = Config.ANNOUNCEMENT_COLORS.get(announcement_type, 0x3498db)

        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description.value,
            color=embed_color,
            timestamp=discord.utils.utcnow(),
        )

        embed.set_author(
            name=f'{Config.IATA_CODE} | {announcement_type} Announcement',
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )

        embed.set_footer(
            text='Powered by Bangkok Airways Bot',
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )

        # Add image if provided
        image_url = self.image_url.value.strip()
        if image_url:
            embed.set_image(url=image_url)

        # Send to announcement channel
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message(
                'I do not have permission to send messages in the announcement channel.',
                ephemeral=True,
            )
            return
        except discord.HTTPException as error:
            await interaction.response.send_message(
                f'Failed to send announcement: {error}',
                ephemeral=True,
            )
            return

        # Confirm to the user
        await interaction.response.send_message(
            f'Announcement sent successfully to {channel.mention}!',
            ephemeral=True,
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """Handle any errors during modal submission."""
        await interaction.response.send_message(
            f'An error occurred: {error}',
            ephemeral=True,
        )


class Announcements(commands.Cog):
    """
    Cog for managing announcements.

    Commands:
        /announcement - Opens a modal to create an announcement.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the Announcements cog."""
        self.bot = bot

    def _has_announcement_permission(self, member: discord.Member) -> bool:
        """
        Check if a member has permission to create announcements.

        Args:
            member: The Discord member to check.

        Returns:
            True if the member is an Administrator or has the Announcement Manager role.
        """
        if member.guild_permissions.administrator:
            return True

        if Config.ANNOUNCEMENT_MANAGER_ROLE_ID != 0:
            return any(
                role.id == Config.ANNOUNCEMENT_MANAGER_ROLE_ID
                for role in member.roles
            )

        return False

    @app_commands.command(
        name='announcement',
        description='Create a professional announcement (Admin/Manager only)',
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def announcement(self, interaction: discord.Interaction) -> None:
        """
        Slash command to open the announcement creation modal.

        Restricted to Administrators and Announcement Managers.
        """
        if not self._has_announcement_permission(interaction.user):
            await interaction.response.send_message(
                'You need Administrator permissions or the Announcement Manager role '
                'to use this command.',
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(AnnouncementModal())

    @announcement.error
    async def announcement_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for the /announcement command."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'Please wait {error.retry_after:.1f}s before using this command again.',
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f'An unexpected error occurred: {error}',
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    """Add the Announcements cog to the bot."""
    await bot.add_cog(Announcements(bot))
