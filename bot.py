# bot.py
import dotenv
import os
from os.path import join, dirname
import discord
from discord.ext import commands

# load environmental variables
env_path = join(dirname(__file__), "config.env")
dotenv.load_dotenv("config.env")

DISCORD_TOKEN = os.environ.get("bot_token")
EXTENSIONS_FILE = os.environ.get("extensions_file")
if DISCORD_TOKEN is None:
    raise Exception("Missing bot_token in config.env")

try:
    with open(EXTENSIONS_FILE, 'r') as f:
        EXTENSIONS = [l.strip('\n') for l in f.readlines()]
except FileNotFoundError:
    with open(EXTENSIONS_FILE, 'w') as f:
        EXTENSIONS = []

# initialize the bot
intents = discord.Intents.default()
intents.message_content = True # necessary for commands to work
bot = commands.Bot(
    command_prefix='$',
    intents=intents
    )
async def setup_hook():
    # note that extensions should be loaded before the slash commands
    # are synched. Here we ensure that by only allowing manual synching
    # once the bot finishes loading (i.e., `setup_hook()` also called)
    for extension in EXTENSIONS:
        await bot.load_extension(extension)
bot.setup_hook = setup_hook
bot.remove_command('help')

# bot events
@bot.event
async def on_ready():
    print(f"{bot.user} is now online.")
    

# bot commands (non-slash; only for the admin/owner)
@bot.command(name='sync_local', hidden=True)
@commands.is_owner()
async def sync_local(ctx):
    # note that global commands need to be explicitly copied...
    bot.tree.copy_global_to(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"Synching command tree for this server ({ctx.guild.name}).")

@bot.command(name='sync_global', hidden=True)
@commands.is_owner()
async def sync_global(ctx):
    await bot.tree.sync()
    await ctx.send(f"Synching command tree for for ALL servers.")

@bot.command(name='shutdown', hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    await bot.close()

@bot.command(name='restart', hidden=True)
@commands.is_owner()
async def restart(ctx): 
    await ctx.send("Restarting...")
    os.execl("./start.sh", "./start.sh")

@bot.command(name='load', hidden=True)
@commands.is_owner()
async def load_extension(ctx, extension_name): 
    await bot.load_extension(extension_name)

    await ctx.send(f"Loaded extension: {extension_name}.")

@bot.command(name='unload', hidden=True)
@commands.is_owner()
async def unload_extension(ctx, extension_name): 
    await bot.unload_extension(extension_name)

    await ctx.send(f"Unloaded extension: {extension_name}.")

@bot.command(name='reload', hidden=True)
@commands.is_owner()
async def reload_extension(ctx, extension_name=None):
    if (extension_name != None):
        await bot.reload_extension(extension_name)

        await ctx.send(f"Reloaded extension: {extension_name}.")
    else:
        for extension in EXTENSIONS:
            await bot.reload_extension(extension)
        
        await ctx.send(f"Reloaded all extensions: {EXTENSIONS}.")

# bot slash commands
# note that we could have done `@discord.app_commands.command(...)`
@bot.tree.command(name="hello", description="responds privately with `Hello [name]!`")
async def hello(interaction, name: str):
    await interaction.response.send_message(
        content=f"Hello {name}!",
        ephemeral=True
    )

bot.run(DISCORD_TOKEN)
