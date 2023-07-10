import asyncio
from discord.ext import commands
from discord import app_commands
from os.path import join, dirname
import json

from modules.mahjongsoul.contest_manager import ContestManager

EXTENSION_NAME = "UvUManager" # must be the same as class name...

class UvUManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        json_config_path = join(dirname(__file__), "config.json")
        with open(json_config_path, "r") as f:
            self.json_config = json.load(f)
        self.bot_channel = None # fetched in `self.async_setup()`
        self.manager = ContestManager(self.json_config["contest_unique_id"])

    async def async_setup(self):
        """
        to be called in `setup()`:
        1. fetch the channel specified in JSON
        2. connect and login to Mahjong Soul...
        3. subscribe to relevant events
        """
        
        # note that `bot.get_channel()` doesn't work because at this point
        # the bot has not cached the channel yet...
        self.bot_channel = await self.bot.fetch_channel(self.json_config["bot_channel_id"])
        await self.manager.connect_and_login()
        await self.manager.subscribe('NotifyContestGameStart', self.on_NotifyContestGameStart)
        await self.manager.subscribe('NotifyContestGameEnd', self.on_NotifyContestGameEnd)

    @app_commands.command(name="terminate", description="Terminate the game of the specified player.")
    async def terminate(self, interaction, nickname: str):
        """
        TODO: ensure that it's either the caller terminating their own game or it's the admin terminating any game; allow terminating own game without nickname input -- requires looking up mahjong soul ID
        """
        game_uuid = await self.manager.get_game_uuid(nickname)

        if game_uuid == None:
            await interaction.response.send_message(
                content=f"No ongoing game found for {nickname}!",
                ephemeral=True
            )
            return
        
        await self.manager.call(
            'terminateGame',
            serviceName='CustomizedContestManagerApi',
            uuid=game_uuid
        )

        await interaction.response.send_message(
            content=f"{nickname}'s game has been terminated.",
        )
    
    async def on_NotifyContestGameStart(self, _, msg):
        nicknames = ' | '.join([p.nickname for p in msg.game_info.players])
        await self.bot_channel.send(f"UvU game started! Players: {nicknames}.")
    
    async def on_NotifyContestGameEnd(self, _, msg):
        # It takes some time for the results to register into the log
        await asyncio.sleep(3)

        record = await self.manager.locate_completed_game(msg.game_uuid)

        response = None

        if record:
            print(f"Received game record object: {record}")
            player_seat_lookup = {a.seat: (a.account_id, a.nickname) for a in record.accounts}

            player_scores_rendered = [
                f'{player_seat_lookup.get(p.seat, (0, "Computer"))[1]} ({p.part_point_1})'
                for p in record.result.players]
            response = f'Game concluded for {" | ".join(player_scores_rendered)}'

            # TODO: record score to Google Sheets here
        else:
            response = f'An unknown game concluded: {msg.game_uuid}'

        await self.bot_channel.send(response)

async def setup(bot: commands.Bot):
    instance = UvUManager(bot)
    asyncio.create_task(instance.async_setup())
    await bot.add_cog(instance)
    print(f'Extension `{EXTENSION_NAME}` is being loaded')

# `teardown()` currently doesn't get called for some reason...
# async def teardown(bot: commands.Bot):
#     instance: UvUManager = bot.get_cog(EXTENSION_NAME)
#     await instance.manager.close()
#     print(f'Extension `{EXTENSION_NAME}` is being unloaded')