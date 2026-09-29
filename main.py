import discord
from discord.ext import commands

from config import TOKEN, GUILD_ID
from commands import setup_commands

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

setup_commands(bot)


@bot.event
async def on_ready():
    print("=" * 40)
    print(f"Logged in as {bot.user}")
    print(f"Configured GUILD_ID: {GUILD_ID}")
    guild_check = bot.get_guild(GUILD_ID) if GUILD_ID else None
    if guild_check:
        print(f"  -> Found matching guild: {guild_check.name}")
    else:
        print(f"  -> WARNING: bot is not in any guild matching this ID. "
              f"Guilds this bot IS in: {[g.name + ' (' + str(g.id) + ')' for g in bot.guilds]}")
    print("=" * 40)

    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {GUILD_ID} (instant).")
        else:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} commands globally (can take up to an hour to appear).")
    except discord.Forbidden as e:
        print(f"403 FORBIDDEN while syncing commands: {e}")
        print("This means the bot's invite is missing the 'applications.commands' OAuth scope "
              "for this specific server. Re-invite it with that scope checked.")
    except Exception as e:
        print(f"Error syncing commands: {e}")


bot.run(TOKEN)
