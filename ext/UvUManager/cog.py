import asyncio
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from os.path import join, dirname
import json

from modules.mahjongsoul.contest_manager import ContestManager
from .table_view import TableView, Player, default_embed
from modules.googlesheets.sheets_interface import Sheets_Interface


EXTENSION_NAME = "UvUManager" # must be the same as class name...

json_config_path = join(dirname(__file__), "config.json")
with open(json_config_path, "r") as f:
    json_config = json.load(f)
CONTEST_UNIQUE_ID = json_config["contest_unique_id"]
CONTEST_TOURNAMENT_ID = json_config["contest_tournament_id"]
GUILD_ID = json_config["guild_id"]
BOT_CHANNEL_ID = json_config["bot_channel_id"]
PLAYER_ROLE = json_config["player_role"]
ADMIN_ROLE = json_config["admin_role"]
TEAM_1 = json_config["team_1"]
TEAM_2 = json_config["team_2"]
SPREADSHEET_ID = json_config["spreadsheet_id"]


class UvUManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_channel = None # fetched in `self.async_setup()`
        self.manager = ContestManager(CONTEST_UNIQUE_ID, True)
        self.sheet = Sheets_Interface(spreadsheet_id=SPREADSHEET_ID)

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
        await self.manager.subscribe("NotifyContestGameStart", self.on_NotifyContestGameStart)
        await self.manager.subscribe("NotifyContestGameEnd", self.on_NotifyContestGameEnd)

    """
    =====================================================
    SLASH COMMANDS
    =====================================================
    """

    @app_commands.command(name="help", description="show helpful hints for using this bot (only visible to you)")
    async def help(self, interaction: Interaction):
        await interaction.response.send_message(
            content=(
                "How to start a tournament game:\n"
                "1. Register your Mahjong Soul account using the `/register` command.\n"
                f"2. On Mahjong Soul: Tournament Match -> Tournament Lobby -> Enter Tournament ID ({CONTEST_TOURNAMENT_ID}) -> Prepare for match.\n"
                "3. Create a table with `/create_table` command. Once everyone chose their seat, the game can be started using the `START` button.\n"
                "Helpful commands for when people need to be AFK (do NOT abuse!):\n"
                "`/terminate_own_game`, `/pause_own_game`, `/unpause_own_game`"),
            ephemeral=True)

    @app_commands.command(name="terminate_any_game", description=f"Terminate the game of the specified player. Only usable by {ADMIN_ROLE}.")
    @app_commands.describe(nickname="Specify the nickname of a player that's in the game you want to terminate.")
    @app_commands.checks.has_role(ADMIN_ROLE)
    async def terminate_any_game(self, interaction: Interaction, nickname: str):
        await interaction.response.defer()
        message = await self.manager.terminate_game(nickname)
        await interaction.followup.send(content=message)

    @app_commands.command(name="terminate_own_game", description=f"Terminate the game you are currently in. Usable by {PLAYER_ROLE}.")
    @app_commands.checks.has_role(PLAYER_ROLE)
    async def terminate_own_game(self, interaction: Interaction):
        await interaction.response.defer()
        player = self.look_up_player(interaction.user.name)
        if player is None:
            await interaction.followup.send(content="You are not a registered player; there shouldn't be an ongoing game for you.")
            return
        message = await self.manager.terminate_game(player.mjs_nickname)
        await interaction.followup.send(content=message)
    
    @app_commands.command(name="pause_any_game", description=f"Pause the game of the specified player. Only usable by {ADMIN_ROLE}.")
    @app_commands.describe(nickname="Specify the nickname of a player that's in the game you want to pause.")
    @app_commands.checks.has_role(ADMIN_ROLE)
    async def pause_any_game(self, interaction: Interaction, nickname: str):
        await interaction.response.defer()
        message = await self.manager.pause_game(nickname)
        await interaction.followup.send(content=message)

    @app_commands.command(name="pause_own_game", description=f"Pause the game you are currently in. Usable by {PLAYER_ROLE}.")
    @app_commands.checks.has_role(PLAYER_ROLE)
    async def pause_own_game(self, interaction: Interaction):
        await interaction.response.defer()
        player = self.look_up_player(interaction.user.name)
        if player is None:
            await interaction.followup.send(content="You are not a registered player; there shouldn't be an ongoing game for you.")
            return
        message = await self.manager.pause_game(player.mjs_nickname)
        await interaction.followup.send(content=message)
    
    @app_commands.command(name="unpause_any_game", description=f"Unpause the paused game of the specified player. Only usable by {ADMIN_ROLE}.")
    @app_commands.describe(nickname="Specify the nickname of a player that's in the paused game you want to unpause.")
    @app_commands.checks.has_role(ADMIN_ROLE)
    async def unpause_any_game(self, interaction: Interaction, nickname: str):
        await interaction.response.defer()
        message = await self.manager.unpause_game(nickname)
        await interaction.followup.send(content=message)

    @app_commands.command(name="unpause_own_game", description=f"Unpause the paused game you were in. Usable by {PLAYER_ROLE}.")
    @app_commands.checks.has_role(PLAYER_ROLE)
    async def unpause_own_game(self, interaction: Interaction):
        await interaction.response.defer()
        player = self.look_up_player(interaction.user.name)
        if player is None:
            await interaction.followup.send(content="You are not a registered player; there shouldn't be an ongoing game for you.")
            return
        message = await self.manager.unpause_game(player.mjs_nickname)
        await interaction.followup.send(content=message)

    @app_commands.command(name="register", description="Register yourself with your Mahjong Soul friend ID, or update your existing registry.")
    @app_commands.checks.has_role(PLAYER_ROLE)
    @app_commands.choices(affiliation=[
        app_commands.Choice(name=TEAM_1, value=TEAM_1),
        app_commands.Choice(name=TEAM_2, value=TEAM_2)
    ])
    @app_commands.describe(
        friend_id="Find your friend ID in the Friends tab; this is separate from your username.",
        affiliation=f"Which club you represent: {TEAM_1}? {TEAM_2}?")
    async def register(self, interaction: Interaction, friend_id: int, affiliation: app_commands.Choice[str]):
        """
        here we use Mahjong Soul ID as the unique identifier, since the
        tournament will be held over Mahjong Soul anyway.
        """
        await interaction.response.defer()

        res = await self.manager.call(
            "searchAccountByEid",
            eids = [friend_id])

        # if no account found, then `res` won't have a `search_result` field, but it won't
        # have an `error`` field, either (i.e., it's not an error!).
        if not res.search_result:
            await interaction.followup.send(content=f"Couldn't find Mahjong Soul account for this friend ID: {friend_id}")
            return

        mahjongsoul_nickname = res.search_result[0].nickname
        # NOTE: account ID is different from friend ID!!!
        mahjongsoul_account_id = res.search_result[0].account_id
        # NOTE: `user.name` is the unique Discord account name (NOT the display name):
        discord_name = interaction.user.name

        registry_values = [discord_name, mahjongsoul_nickname, mahjongsoul_account_id, affiliation.value]

        # check if a Discord user already registered; if yes, override the entry instead of
        # making a new entry
        relative_row_num = self.sheet.find_relative_row_xl("Registry!A2:A", discord_name)
        if relative_row_num >= 0:
            absolute_row_num = 2 + relative_row_num
            sheet_range = "Registry!A" + str(absolute_row_num) + ":D" + str(absolute_row_num)
            self.sheet.update_xl(sheet_range, [registry_values])
            await interaction.followup.send(
                content=f"\"{discord_name}\" from {affiliation.value} has updated their registry with Mahjong Soul account \"{mahjongsoul_nickname}\".")
            return

        self.sheet.append_xl("Registry", [registry_values])

        await interaction.followup.send(
            content=f"\"{discord_name}\" from {affiliation.value} has registered their Mahjong Soul account \"{mahjongsoul_nickname}\".")
            

    @app_commands.command(name="create_table", description="Create a table prompt where players self-assign seats before starting a game.")
    @app_commands.checks.has_role(PLAYER_ROLE)
    async def create_table(self, interaction: Interaction):
        """
        The interactive messages auto-delete self after a certain amount of time.
        
        Originally, there was going to be a way to track the alive interactive
        messages to prevent users from spamming the `create_table` commands and/or
        sitting down at multiple tables. Since the functionality was only useful against
        malicious users, the difficulty in implementing it made it not worthwhile.

        TOTHINK: similarly, it's difficult to connect to listeners to check whether
        someone has hit "prepare for match" (or is `locked` according to MJS terms)
        """
        view = TableView(look_up_player=self.look_up_player, start_game=self.manager.start_game, original_interaction=interaction)

        view.interactive_message = await interaction.response.send_message(
            content="Choose a seat!",
            embed=default_embed,
            view=view)
        

    """
    =====================================================
    MAHJONG SOUL API STUFF
    =====================================================
    """

    async def on_NotifyContestGameStart(self, _, msg):
        nicknames = " | ".join([p.nickname for p in msg.game_info.players])
        await self.bot_channel.send(f"UvU game started! Players: {nicknames}.")
    
    async def on_NotifyContestGameEnd(self, _, msg):
        # It takes some time for the results to register into the log
        await asyncio.sleep(3)

        record = await self.manager.locate_completed_game(msg.game_uuid)

        if record is None:
            await self.bot_channel.send("A game concluded without a record (possibly due to being terminated early).")

        # TODO: just do player look up so affiliation can be included as well
        # TODO: deal with ordering the scores; currently assumes the scores are ordered by
        #       total_point (this algorithm can be shared with manual score entering)
        # TODO: examine the record when there is a computer!! May re-write whole thing again...
        player_seat_lookup = {a.seat: (a.account_id, a.nickname) for a in record.accounts}

        player_scores_rendered = ["Game concluded! Results:"] # to be newline-separated
        google_sheets_row = [] # a list of values for a "Score Dump" row on Google Sheets
        for p in record.result.players:
            if not p.total_point:
                # the object has no `total_point` if the player ends up
                # with 0 points after bonuses...
                p.total_point = 0

            player_scores_rendered.append(
                f"{player_seat_lookup.get(p.seat, (0, 'Computer'))[1]} ({p.part_point_1}) [{p.total_point/1000:+}]")
            google_sheets_row.extend((
                player_seat_lookup.get(p.seat, (0, "Computer"))[0],
                p.total_point/1000))

        asyncio.create_task(self.bot_channel.send(
            content='\n'.join(player_scores_rendered)))

        self.sheet.append_xl("Score Dump", [google_sheets_row])

    """
    =====================================================
    GOOGLE SHEETS HELPER FUNCTIONS
    =====================================================
    """

    def look_up_player(self, discord_name: str) -> Player | None:
        relative_row_num = self.sheet.find_relative_row_xl("Registry!A2:A", discord_name)
        
        if relative_row_num >= 0:
            absolute_row_num = 2 + relative_row_num
            sheet_range = "Registry!A" + str(absolute_row_num) + ":D" + str(absolute_row_num)
            values = self.sheet.read_xl(sheet_range)[0]
            return Player(
                mjs_account_id=int(values[2]),
                mjs_nickname=values[1],
                discord_name=discord_name,
                affiliation=values[3])
        
        # No player with given Discord name found; returning None
        return None

async def setup(bot: commands.Bot):
    instance = UvUManager(bot)
    asyncio.create_task(instance.async_setup())
    await bot.add_cog(instance, guild=discord.Object(id=GUILD_ID))
    print(f"Extension `{EXTENSION_NAME}` is being loaded")

# `teardown()` currently doesn't get called for some reason...
# async def teardown(bot: commands.Bot):
#     instance: UvUManager = bot.get_cog(EXTENSION_NAME)
#     await instance.manager.close()
#     print(f"Extension `{EXTENSION_NAME}` is being unloaded")