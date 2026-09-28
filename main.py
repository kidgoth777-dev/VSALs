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
    except Exception as e:
        print(e)


bot.run(TOKEN)
