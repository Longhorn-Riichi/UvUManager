import os
import hmac
import hashlib

from ms_tournament.base import MSRPCChannel
from ms_tournament.rpc import CustomizedContestManagerApi
import ms_tournament.protocol_admin_pb2 as pb


# MS_HOST: URL to the Chinese tournament manager
MS_HOST = "https://www.maj-soul.com/"
# MS_MANAGER_WSS_ENDPOINT: `__MJ_DHS_WS__` from https://www.maj-soul.com/dhs/js/config.js
MS_MANAGER_WSS_ENDPOINT = "wss://gateway-v2.maj-soul.com/contest_ws_gateway"
MS_USERNAME = os.environ.get("ms_username")
MS_PASSWORD = os.environ.get("ms_password")

# TODO: login once but allow managing multiple contests across different cogs?!
# or maybe login multiple times using the same account...? Ban risk?

class ContestManager():
    def __init__(self, contest_unique_id, discord_server_id):
        self.contest_unique_id = contest_unique_id
        self.discord_server_id = discord_server_id
        self.manager_api = None
        self.channel = None # TODO: close the channel in clean-up?

    async def connect_and_login(self):
        """
        Connect to the Chinese tournament manager server, then login with username and password environment variables
        """
        # Establish WSS connection
        
        self.channel = MSRPCChannel(MS_MANAGER_WSS_ENDPOINT)
        self.manager_api = CustomizedContestManagerApi(self.channel)
        await self.channel.connect(MS_HOST)

        # Login via username and password
        req = pb.ReqContestManageLogin()
        req.account = MS_USERNAME
        req.password = hmac.new(b"lailai", MS_PASSWORD.encode(), hashlib.sha256).hexdigest()
        req.gen_access_token = True
        req.type = 0

        res = await self.manager_api.login_contest_manager(req)
        if not res.access_token:
            print(f"Login Error:\n{res}")
        print(f"Login to tournament manager server succesfull!")

    async def load_tournaments_list(self):
        print("Loading tournament list...")

        req = pb.ReqCommon()
        res = await self.manager_api.fetch_related_contest_list(req)
        tournaments_count = len(res.contests)
        print(f"found tournaments : {tournaments_count}")


        for i in range(0, tournaments_count):
            print("") 
            print(f"unique_id: {res.contests[i].unique_id}") 
            print(f"contest_id: {res.contests[i].contest_id}")
            print(f"contest_name: {res.contests[i].contest_name}")

        await self.channel.close()
