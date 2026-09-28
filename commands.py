import urllib.parse

import discord
from discord import app_commands
from config import (
    STAFF_ROLE_IDS,
    ACTIVITY_CHANNEL_ID,
    DEFAULT_CHECK_COUNT,
    PASS_THRESHOLD,
)


def is_staff(member: discord.Member):
    return any(role.id in STAFF_ROLE_IDS for role in member.roles)


async def get_all_reactor_ids(bot, channel_id: int, message_id: int, emoji) -> set:
    """Returns the set of user IDs who reacted with this emoji, covering
    BOTH normal reactions and Discord's 'super reactions' (burst type).
    A plain reaction.users() call can silently miss burst reactors, which
    is why this hits the API directly for both types."""
    ids = set()
    quoted_emoji = urllib.parse.quote(str(emoji), safe="")

    for reaction_type in (0, 1):  # 0 = normal, 1 = burst/super reaction
        after = None
        while True:
            try:
                data = await bot.http.get_reaction_users(
                    channel_id, message_id, quoted_emoji, 100,
                    after=after, type=reaction_type,
                )
            except TypeError:
                # Older discord.py without burst-type support — fall back
                # to a single untyped call (normal reactions only).
                data = await bot.http.get_reaction_users(
                    channel_id, message_id, quoted_emoji, 100, after=after,
                )
                for u in data:
                    ids.add(int(u["id"]))
                break
            except discord.HTTPException:
                break

            if not data:
                break
            for u in data:
                ids.add(int(u["id"]))
            if len(data) < 100:
                break
            after = data[-1]["id"]

    return ids


def setup_commands(bot):
    """Registers all slash commands that live in this file onto the bot."""

    @bot.tree.command(
        name="checkact",
        description="See how many recent activity checks a member has reacted to.",
    )
    @app_commands.describe(
        user="The member to check.",
        checks="How many recent checks to look at (default 1).",
    )
    async def checkact(
        interaction: discord.Interaction,
        user: discord.Member,
        checks: int = DEFAULT_CHECK_COUNT,
    ):
        await interaction.response.defer()

        if not is_staff(interaction.user):
            await interaction.followup.send(
                "❌ You don't have permission.",
                ephemeral=True,
            )
            return

        if checks < 1:
            await interaction.followup.send(
                "❌ Number of checks must be at least 1.",
                ephemeral=True,
            )
            return

        if not ACTIVITY_CHANNEL_ID:
            await interaction.followup.send(
                "❌ ACTIVITY_CHANNEL_ID isn't configured.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(ACTIVITY_CHANNEL_ID)
        if channel is None:
            await interaction.followup.send(
                "❌ Couldn't find the activity check channel.",
                ephemeral=True,
            )
            return

        # Pull the most recent non-bot messages from the activity channel —
        # each one counts as one "check". No pre-tracking needed.
        messages = []
        async for msg in channel.history(limit=200):
            if msg.author.bot:
                continue
            messages.append(msg)
            if len(messages) >= checks:
                break

        if not messages:
            await interaction.followup.send(
                "There are no activity check messages in that channel yet.",
                ephemeral=True,
            )
            return

        reacted_count = 0
        for msg in messages:
            found = False
            for reaction in msg.reactions:
                reactor_ids = await get_all_reactor_ids(
                    bot, msg.channel.id, msg.id, reaction.emoji
                )
                if user.id in reactor_ids:
                    found = True
                    break
            if found:
                reacted_count += 1

        total = len(messages)
        passed = (reacted_count / total) >= PASS_THRESHOLD
        emoji = "✅" if passed else "❌"

        await interaction.followup.send(
            f"{emoji} {user.mention} has reacted to **{reacted_count}** of the last **{total}** checks."
        )
