import asyncio
from discord.ext import commands
from discord import app_commands
import os
import json
import aiohttp
import hmac
import hashlib

from ms_tournament.base import MSRPCChannel
from ms_tournament.rpc import CustomizedContestManagerApi
import ms_tournament.protocol_admin_pb2 as pb

# MS_HOST: URL to the Chinese tournament manager
MS_HOST = "https://www.maj-soul.com/"
# MS_MANAGER_API_URL: `__MJ_DHS_LB__` from https://www.maj-soul.com/dhs/js/config.js
MS_MANAGER_API_URL = "https://gateway-v2.maj-soul.com"
MS_USERNAME = os.environ.get("ms_username")
MS_PASSWORD = os.environ.get("ms_password")

# boilerplate references:
# 1. Chinese game server: https://github.com/MahjongRepository/mahjong_soul_api/blob/master/example.py
# 2. English tournament management server: https://github.com/MahjongRepository/mahjong_soul_api/blob/master/example_admin.py

# general tips for reverse-engineering Mahjong Soul API:
# refer to liqi_admin.json for all API; use WebSocket Inspector to get ideas
# use https://protobuf-decoder.netlify.app/ to decode the WebSocket Protobuf

# connect via WebSocket to the Chinese tournament manager server
async def connect():
    # get one websocket endpoint to the Chinese tournament manager
    async with aiohttp.ClientSession() as session:
    	async with session.get(f"{MS_MANAGER_API_URL}/api/customized_contest/random") as res:
            servers = await res.json()
            print(f"servers received:\n{servers}")
            endpoint_gate = servers['servers'][0]
            endpoint = f"wss://{endpoint_gate}/"

    channel = MSRPCChannel(endpoint)
    manager_api = CustomizedContestManagerApi(channel)
    await channel.connect(MS_HOST)

    return manager_api, channel

# login with username and password environment variables, given a WebSocket connection
async def login(manager_api):
    req = pb.ReqContestManageLogin()
    req.account = MS_USERNAME
    req.password = hmac.new(b"lailai", MS_PASSWORD.encode(), hashlib.sha256).hexdigest()
    req.gen_access_token = True
    req.type = 0

    res = await manager_api.login_contest_manager(req)
    token = res.access_token
    if not token:
        print(f"Login Error:\n{res}")
        return False
    print(f"Login succesfull! Access token: {token}")
    return True


class UvUManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("./config.json", "r") as f:
            self.json_config = json.loads(f.read())

    # to be called in `setup()`:
    # connect, login, and subscribe to events...
    async def async_setup(self):
        await connect
        
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
