import asyncio
from discord.ext import commands
from discord import app_commands
from os.path import join, dirname
import json

from modules.mahjonsoul.contest_manager import ContestManager

class UvUManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        json_config_path = join(dirname(__file__), "config.json")
        with open(json_config_path, "r") as f:
            self.json_config = json.loads(f.read())

        self.manager = ContestManager(
            self.json_config["contest_unique_id"],
            self.json_config["discord_server_id"]
        )

    # to be called in `setup()`:
    # connect, login, and subscribe to events...
    async def async_setup(self):
        await self.manager.connect_and_login()
        await self.manager.load_tournaments_list()
        
    @app_commands.command(name="coghello", description="ALSO responds privately with `Hello [name]!`")
    async def hello(self, interaction, name: str):
        await interaction.response.send_message(
            content=f"Hello {name}!",
            ephemeral=True
        )

async def setup(bot):
    instance = UvUManager(bot)
    asyncio.create_task(instance.async_setup())
    await bot.add_cog(instance)
    print(f'Extension `UvUManager` setup finished')
