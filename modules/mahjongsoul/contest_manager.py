import os
import hmac
import hashlib

from modules.pymjsoul.channel import MajsoulChannel
from modules.pymjsoul.proto import liqi_combined_pb2
from discord import Interaction

# MS_MANAGER_WSS_ENDPOINT: `__MJ_DHS_WS__` from https://www.maj-soul.com/dhs/js/config.js
MS_MANAGER_WSS_ENDPOINT = "wss://gateway-v2.maj-soul.com/contest_ws_gateway"
MS_USERNAME = os.environ.get("ms_username")
MS_PASSWORD = os.environ.get("ms_password")
EAST = 0
SOUTH = 1
WEST = 2
NORTH = 3

class ContestManager(MajsoulChannel):
    """
    wraps around the `MajsoulChannel` class to provide additional functionalities for managing ONE specific contest on Discord
    """
    def __init__(self, contest_unique_id):
        self.contest_unique_id = contest_unique_id
        self.contest = None # contest info; `CustomizedContest` protobuf
        # TODO: close the channel in clean-up?
        super().__init__(proto=liqi_combined_pb2, log_messages=False)

    async def connect_and_login(self):
        """
        Connect to the Chinese tournament manager server, login with username and password environment variables, and start managing the specified contest.
        Returns True if all steps succeed; otherwise False.
        """
        # Establish WSS connection
        await self.connect(MS_MANAGER_WSS_ENDPOINT)

        # Login via username and password
        res = await self.call(
            methodName = "loginContestManager",
            account = MS_USERNAME,
            password = hmac.new(b"lailai", MS_PASSWORD.encode(), hashlib.sha256).hexdigest(),
            gen_access_token = True,
            type = 0
        )
        if not res.access_token:
            print(f"loginContestManager Error; response:\n{res}")
            return False
        
        print("Login to tournament manager server succesfull!")

        res = await self.call(
            methodName = 'manageContest',
            unique_id = self.contest_unique_id
        )
        if not res.contest:
            print(f"manageContest Error; response:\n{res}")
            return False

        self.contest = res.contest

        # `startManageGame` is needed to start receiving the notifications
        res = await self.call(methodName = 'startManageGame')
        print(f"Started managing contest {self.contest.contest_name}!")
        return True
        

    async def get_ongoing_game_uuid(self, nickname):
        """
        return the UUID for an ongoing game the specified player is in
        """
        res = await self.call('startManageGame')
        for game in res.games:
            for player in game.players:
                if player.nickname == nickname:
                    return game.game_uuid
    
    # TODO: login to Lobby to directly do `fetchGameRecord`?
    async def locate_completed_game(self, game_uuid):
        """
        locate and return a completed game's record
        """
        res = await self.call('fetchContestGameRecords')
        for item in res.record_list:
            if item.record.uuid == game_uuid:
                return item.record
        return None
    
    async def terminate_game(self, nickname: str, interaction: Interaction):
        """
        terminate the game that the specified player is in.
        NOTE: this and similar methods assume that nicknames are unique,
        which is not true when multiple servers are allowed to participate
        in the same contest... this potential but unlikely issue is ignored.
        NOTE: also, technically we could make more precise wrappers for when
        people want to terminate their own game (we need to fetch their info anyway)
        """
        game_uuid = await self.get_ongoing_game_uuid(nickname)

        if game_uuid == None:
            await interaction.response.send_message(
                content=f"No ongoing game to be terminated for {nickname}!",
            )
            return
        
        await self.call(
            'terminateGame',
            serviceName='CustomizedContestManagerApi',
            uuid=game_uuid
        )

        await interaction.response.send_message(
            content=f"{nickname}'s game has been terminated.",
        )

    async def pause_game(self, nickname: str, interaction: Interaction):
        game_uuid = await self.get_ongoing_game_uuid(nickname)

        if game_uuid == None:
            await interaction.response.send_message(
                content=f"No ongoing game to be paused for {nickname}!",
            )
            return
        
        await self.call(
            'pauseGame',
            uuid=game_uuid
        )

        await interaction.response.send_message(
            content=f"{nickname}'s game has been paused.",
        )
    
    async def resume_game(self, nickname: str, interaction: Interaction):
        game_uuid = await self.get_ongoing_game_uuid(nickname)

        if game_uuid == None:
            await interaction.response.send_message(
                content=f"No paused game to be resumed for {nickname}!",
            )
            return
        
        await self.call(
            'resumeGame',
            uuid=game_uuid
        )

        await interaction.response.send_message(
            content=f"{nickname}'s paused game has been resumed.",
        )

    async def start_game(self, account_ids: list[int], random_position=False, open_live=True, ai_level=2):
        """
        start a tournament game. `account_ids` is a list of mahjong soul player
        ids, where 0 means adding a computer at the given seat.
        TODO: explain the parameters

        returns `None` on success, otherwise a `str` describing the issue
        """
        playerList = []
        for i in range(len(account_ids)):
            account_id = account_ids[i]
            playerList.append(self.proto.ReqCreateContestGame.Slot(
                account_id=account_id,
                seat=i
            ))
            # if it's a real player, call `lockGamePlayer`
            if account_id > 0:
                await self.call('lockGamePlayer', account_id=account_id)
        res = await self.call(
            methodName='createContestGame',
            slots = playerList,
            random_position=random_position,
            open_live=open_live,
            ai_level=ai_level
        )
