import asyncio
from discord.ext import commands
from discord import app_commands
from os.path import join, dirname
import json

from modules.mahjongsoul.contest_manager import ContestManager
from modules.googlesheets.sheets_interface import Sheets_Interface

class UvUManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        json_config_path = join(dirname(__file__), "config.json")
        with open(json_config_path, "r") as f:
            self.json_config = json.loads(f.read())
        
        # TODO: failure to get bot channel?
        self.bot_channel = bot.get_channel(self.json_config["bot_channel_id"])
        self.manager = ContestManager(self.json_config["contest_unique_id"])

    # to be called in `setup()`:
    # connect, login, and subscribe to events...
    async def async_setup(self):
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
        self.bot_channel.send(f"UvU game started! Players: {nicknames}.")
    
    async def on_NotifyContestGameEnd(self, _, msg):
        # It takes some time for the results to register into the log
        await asyncio.sleep(3)

        # TODO: potential Error? Requires login and subscribing?
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
            player_scores_list = [[player_seat_lookup.get(p.seat, (0, "Computer"))[1], p.total_point] for p in record.result.players]
            flat_list = [[item for sublist in player_scores_list for item in sublist]]
            # spreadsheet_id = self.json_config["spreadsheet_id"]
            # sheet = Sheets_Interface(spreadsheet_id=spreadsheet_id)
            # sheet.append_xl(flat_list)
            
        else:
            response = f'An unknown game concluded: {msg.game_uuid}'

        await self.bot_channel.send(response)

async def setup(bot):
    instance = UvUManager(bot)
    asyncio.create_task(instance.async_setup())
    await bot.add_cog(instance)
    print(f'Extension `UvUManager` setup finished')
