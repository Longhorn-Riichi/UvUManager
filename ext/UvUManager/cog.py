import asyncio
from discord.ext import commands
from discord import app_commands, Interaction
from os.path import join, dirname
import json

from modules.mahjongsoul.contest_manager import ContestManager

EXTENSION_NAME = "UvUManager" # must be the same as class name...

json_config_path = join(dirname(__file__), "config.json")
with open(json_config_path, "r") as f:
    json_config = json.load(f)
CONTEST_UNIQUE_ID = json_config["contest_unique_id"]
GUILD_ID = json_config["guild_id"]
BOT_CHANNEL_ID = json_config["bot_channel_id"]


class UvUManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_channel = None # fetched in `self.async_setup()`
        self.manager = ContestManager(CONTEST_UNIQUE_ID)

    async def async_setup(self):
        """
        to be called in `setup()`:
        1. fetch the channel specified in JSON
        2. connect and login to Mahjong Soul...
        3. subscribe to relevant events
        """
        
        # note that `bot.get_channel()` doesn't work because at this point
        # the bot has not cached the channel yet...
        self.bot_channel = await self.bot.fetch_channel(BOT_CHANNEL_ID)
        await self.manager.connect_and_login()
        await self.manager.subscribe('NotifyContestGameStart', self.on_NotifyContestGameStart)
        await self.manager.subscribe('NotifyContestGameEnd', self.on_NotifyContestGameEnd)

    """
    =====================================================
    SLASH COMMANDS
    =====================================================
    """

    @app_commands.command(name="terminate", description="Terminate the game of the specified player.")
    @app_commands.describe(nickname="Specify the nickname of a player that's in the game you want to terminate.")
    @app_commands.guilds(GUILD_ID)
    async def terminate(self, interaction: Interaction, nickname: str):
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
    
    @app_commands.command(name="register", description="Register yourself with your Mahjong Soul friend ID.")
    @app_commands.choices(affiliation=[
        app_commands.Choice(name="UT Austin", value="UT Austin"),
        app_commands.Choice(name="UT Dallas", value="UT Dallas")
    ])
    @app_commands.describe(
        friend_id="Find your friend ID in the Friends tab; this is separate from your username.",
        affiliation="Which club you represent: Austin? Dallas?"
    )
    @app_commands.guilds(GUILD_ID)
    async def register(self, interaction: Interaction, friend_id: int, affiliation: app_commands.Choice[str]):
        """
        here we use Mahjong Soul ID as the unique identifier, since the
        tournament will be held over Mahjong Soul anyway.
        TODO: allow registration only for a select Discord role
        """
        res = await self.manager.call(
            "searchAccountByEid",
            eids = [friend_id]
        )

        if res.search_result:
            mahjongsoul_nickname = res.search_result[0].nickname
            # NOTE: account ID is different from friend ID!!!
            mahjongsoul_account_id = res.search_result[0].account_id
            discord_name = interaction.user.name

            # TODO: record `mahjongsoul_account_id`, `mahjongsoul_nickname`, `discord_name`, and `affiliation.value` to Google Sheets here.
            # NOTE: if a Discord user tries to register again, it should override the existing entry that has the same Discord name.

            await interaction.response.send_message(
                content=f"\"{discord_name}\" from {affiliation.value} has registered their Mahjong Soul account \"{mahjongsoul_nickname}\".",
            )
        else:
            await interaction.response.send_message(
                content=f"Couldn't find Mahjong Soul account for this friend ID: {friend_id}",
            )

    # @app_commands.command(name="start", description="Propose to start a game.")
    # @app_commands.guilds(GUILD_ID)
    # async def start(self, interaction: Interaction):

    """
    =====================================================
    MAHJONG SOUL API STUFF
    =====================================================
    """

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
            response = f'A game concluded without a record: {msg.game_uuid}'

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