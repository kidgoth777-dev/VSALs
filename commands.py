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


def setup_commands(bot):
    """Registers all slash commands that live in this file onto the bot."""

    @bot.tree.command(
        name="checkact",
        description="See how many recent activity checks a member has reacted to.",
    )
    @app_commands.describe(
        user="The member to check.",
        checks="How many recent checks to look at (default 1).",
        debug="Show which messages/reactions were checked (for troubleshooting).",
    )
    async def checkact(
        interaction: discord.Interaction,
        user: discord.Member,
        checks: int = DEFAULT_CHECK_COUNT,
        debug: bool = False,
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
                f"❌ Couldn't find channel ID `{ACTIVITY_CHANNEL_ID}` in this server. "
                f"Double check ACTIVITY_CHANNEL_ID matches a channel that actually exists here.",
                ephemeral=True,
            )
            return

        # Pull the most recent non-bot messages from the activity channel —
        # each one counts as one "check". No pre-tracking needed. Any
        # reaction, with any emoji, counts as that person being "ticked in".
        messages = []
        async for msg in channel.history(limit=200):
            if msg.author.bot:
                continue
            messages.append(msg)
            if len(messages) >= checks:
                break

        if not messages:
            await interaction.followup.send(
                f"There are no non-bot messages in {channel.mention} yet.",
                ephemeral=True,
            )
            return

        reacted_count = 0
        debug_lines = []

        for msg in messages:
            found = False
            msg_reaction_summary = []

            for reaction in msg.reactions:
                users_here = []
                async for reactor in reaction.users():
                    users_here.append(reactor)
                    if reactor.id == user.id:
                        found = True

                msg_reaction_summary.append(
                    f"{reaction.emoji} × {len(users_here)}"
                    f" ({', '.join(u.name for u in users_here) or 'none'})"
                )

            debug_lines.append(
                f"[{msg.jump_url}] by {msg.author}: "
                + ("; ".join(msg_reaction_summary) if msg_reaction_summary else "no reactions")
                + (" ✅ MATCH" if found else "")
            )

            if found:
                reacted_count += 1

        total = len(messages)
        passed = (reacted_count / total) >= PASS_THRESHOLD
        emoji = "✅" if passed else "❌"

        result = (
            f"{emoji} {user.mention} has reacted to **{reacted_count}** of the last **{total}** checks."
        )

        if debug:
            debug_text = "\n".join(debug_lines)
            result += f"\n\n**Debug info:**\n{debug_text}"

        if len(result) > 1900:
            result = result[:1900] + "\n… (truncated)"

        await interaction.followup.send(result)
