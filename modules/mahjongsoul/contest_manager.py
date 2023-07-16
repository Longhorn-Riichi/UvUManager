import os
import hmac
import hashlib

from modules.pymjsoul.channel import MajsoulChannel, GeneralMajsoulError
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
    def __init__(self, contest_unique_id, log_messages=False):
        self.contest_unique_id = contest_unique_id
        self.contest = None # contest info; `CustomizedContest` protobuf
        super().__init__(proto=liqi_combined_pb2, log_messages=log_messages)

    async def connect_and_login(self):
        """
        Connect to the Chinese tournament manager server, login with username and password environment variables, start managing the specified contest, and start receiving the notifications for the games in that contest.
        Caller is responsible for catching errors and acting on them.
        """
        # Establish WSS connection
        await self.connect(MS_MANAGER_WSS_ENDPOINT)
        # Login, manage specific contest, and start listening to notifications
        await self.login_and_start_listening()
    
    async def reconnect_and_login(self):
        """
        login to Mahjong Soul again, keeping the existing subscriptions.
        Needs to make a new connection with `self.reconnect()` because trying to
        log in through the same connection results in `2504 : "ERR_CONTEST_MGR_HAS_LOGINED"`
        """
        await self.reconnect()
        await self.login_and_start_listening()

    async def login_and_start_listening(self):
        """
        this is its own method so it can be used again without having to establish
        another WSS connection (e.g., when we were logged out outside of this module)

        NOTE: use the original `MajsoulChannel.call()` to avoid infinite errors
        """
        await super().call(
            methodName = "loginContestManager",
            account = MS_USERNAME,
            password = hmac.new(b"lailai", MS_PASSWORD.encode(), hashlib.sha256).hexdigest(),
            type = 0
        )
    
        print(f"`loginContestManager` with {MS_USERNAME} successful!")
    
        res = await super().call(
            methodName = 'manageContest',
            unique_id = self.contest_unique_id
        )

        self.contest = res.contest

        print(f"`manageContest` for {self.contest.contest_name} successful!")

        # `startManageGame` is needed to start receiving the notifications
        await super().call(methodName = 'startManageGame')
        
        print(f"`startManageGame` successful!")

    async def call(self, methodName, **msgFields):
        """
        Wrap around `MajsoulChannel.call()` to handle certain errors. Note that
        `MajsoulChannel` already prints the API Errors to the console.
        """
        try:
            return await super().call(methodName, **msgFields)
        except GeneralMajsoulError as error:
            if error.errorCode == 2505:
                """
                "ERR_CONTEST_MGR_NOT_LOGIN"
                In this case, try logging BACK in and retrying the call.
                Do nothing if the retry still failed. (we do this because
                the account may have been logged out elsewhere unintentionally,
                e.g., from the web version of the tournament manager)
                """
                print("Received `ERR_CONTEST_MGR_NOT_LOGIN`; now trying to log in again and resend the previous request.")
                await self.reconnect_and_login()
                return await super().call(methodName, **msgFields)
            else:
                raise error
        

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
    async def locate_completed_game(self, game_uuid: int):
        """
        locate and return a completed game's record
        """
        res = await self.call('fetchContestGameRecords')
        for item in res.record_list:
            if item.record.uuid == game_uuid:
                return item.record
        return None
    
    async def terminate_game(self, nickname: str) -> str:
        """
        terminate the game that the specified player is in.
        returns a human-readable message whether successful.
        NOTE: this and similar methods assume that nicknames are unique,
        which is not true when multiple servers are allowed to participate
        in the same contest... this potential but unlikely issue is ignored,
        since it's much more convenient to terminate games by nickname.
        NOTE: also, technically we could make more precise wrappers for when
        people want to terminate their own game (we need to fetch their info anyway)
        """
        game_uuid = await self.get_ongoing_game_uuid(nickname)

        if game_uuid == None:
            return f"No ongoing game to be terminated for {nickname}!"
        
        await self.call(
            'terminateGame',
            serviceName='CustomizedContestManagerApi',
            uuid=game_uuid
        )

        return f"{nickname}'s game has been terminated."

    async def pause_game(self, nickname: str) -> str:
        """
        `pause` variant of the `terminate_game()`
        """
        game_uuid = await self.get_ongoing_game_uuid(nickname)

        if game_uuid == None:
            return f"No ongoing game to be paused for {nickname}!"
        
        await self.call(
            'pauseGame',
            uuid=game_uuid
        )

        return f"{nickname}'s game has been paused."
    
    async def unpause_game(self, nickname: str) -> str:
        """
        `unpause` variant of the `terminate_game()`
        """
        game_uuid = await self.get_ongoing_game_uuid(nickname)

        if game_uuid == None:
            return f"No paused game to be unpaused for {nickname}!"
        
        await self.call(
            'resumeGame',
            uuid=game_uuid
        )

        return f"{nickname}'s paused game has been unpaused."

    async def start_game(self, account_ids: list[int], random_position=False, open_live=True, ai_level=2) -> None:
        """
        start a tournament game. `account_ids` is a list of mahjong soul player
        ids, where 0 means adding a computer at the given seat.
        
        parameters
        ------------
        account_ids: a list of Mahjong Soul account ids [East, South, West, North]
        random_position: whether to randomize the seats (ignore the ordering in accounts_ids)
        open_live: TODO: whether to allow live spectating?
        ai_level: TODO: the level of the AI? What levels are there?
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
