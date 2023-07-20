# UvUManager

A Discord bot for Longhorn Riichi's special tournament "UTA vs UTD". Functions include `/register`, `/create_table`, `/pause_own_game`, etc.

# Running the bot
1. set up a bot account on Discord's [developer portal](https://discord.com/developers/applications) (`New Application`). Invite the bot to the respective server with their OAuth2 URL Generator (SETTINGS -> OAuth2 -> URL Generator).
1. refer to the `*_FORMAT` files to make a `config.env` in the root directory and a `config.json` file for each extension in [ext/](ext/).
1. in a Unix shell:

        pipenv install
        pipenv shell
        ./start.sh
1. in the respective server: run `$sync_local` to sync the slash commands for that server.

# Relevant Links

- [Riichi Nomi's Ronnie bot](https://github.com/RiichiNomi/ronnie)
- [mjsoul.py](https://github.com/RiichiNomi/mjsoul.py)
- [ms_api: Mahjong Soul API in Python](https://github.com/MahjongRepository/mahjong_soul_api/tree/master)

