import os
import hmac
import hashlib

from modules.pymjsoul.channel import MajsoulChannel
from modules.pymjsoul.proto import liqi_combined_pb2

# MS_MANAGER_WSS_ENDPOINT: `__MJ_DHS_WS__` from https://www.maj-soul.com/dhs/js/config.js
MS_MANAGER_WSS_ENDPOINT = "wss://gateway-v2.maj-soul.com/contest_ws_gateway"
MS_USERNAME = os.environ.get("ms_username")
MS_PASSWORD = os.environ.get("ms_password")

class ContestManager(MajsoulChannel):
    """
    wraps around the `MajsoulChannel` class to provide additional functionalities for managing ONE specific contest
    """
    def __init__(self, contest_unique_id):
        self.contest_unique_id = contest_unique_id
        self.contest = None
        # TODO: close the channel in clean-up?
        super().__init__(proto=liqi_combined_pb2, log_messages=False)

    async def connect_and_login(self):
        """
        Connect to the Chinese tournament manager server, login with username and password environment variables, and start managing the specified contest.
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
        print("Login to tournament manager server succesfull!")

        res = await self.call(
            methodName = 'manageContest',
            unique_id = self.contest_unique_id
        )
        if not res.contest:
            print(f"manageContest Error; response:\n{res}")
        self.contest = res.contest
        print(f"Started managed contest {self.contest.contest_name}!")

    async def get_game_uuid(self, nickname):
        """
        return the UUID for an ongoing game the specified player is in
        """
        res = await self.call('startManageGame')
        for game in res.games:
            for player in game.players:
                if player.nickname == nickname:
                    return game.game_uuid
    
    # TODO: login to Lobby to directly do `fetchGameRecord`
    async def locate_completed_game(self, game_uuid):
        """
        locate and return a completed game's record
        """
        res = await self.call('fetchContestGameRecords')
        for item in res.record_list:
            if item.record.uuid == game_uuid:
                return item.record
        return None


