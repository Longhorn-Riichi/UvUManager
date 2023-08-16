# UvUManager

A Discord bot for Longhorn Riichi's special tournament "UTA vs UTD". Functions include `/register`, `/create_table`, `/pause_own_game`, etc.
## Repository Structure:
- `/ext/extensions`: list of all modules for `bot.py` to load from `/ext/`, one per line
- `/modules/pymjsoul`: a copy of [mjsoul.py](https://github.com/RiichiNomi/mjsoul.py) that provides `MajsoulChannel`, a class for interfacing with Mahjong Soul's API
- `/modules/mahjongsoul`: contains a wrapper of `MajsoulChannel` for use in our bot (in `/ext/extensions/UvUManager`)
## Setting up the bot
First, `cp config.template.env config.env`.
### Discord Stuff
1. set up a bot account on Discord's [developer portal](https://discord.com/developers/applications) (`New Application`).
    - (SETTINGS -> Bot) Privileged Gateway Intents: `MESSAGE CONTENT INTENT`
1. invite the bot to the respective servers. You can use the developer portal's OAuth2 URL Generator (SETTINGS -> OAuth2 -> URL Generator):
    - Scopes: bot
    - Bot Permissions: Send Messages, Manage Messages, Add Reactions
1. fill in the `Discord Stuff` section of [config.env](config.env)
### Google Sheets Stuff
1. set up a Google Cloud project. Enable Google Sheets API access, and make a service account. Generate a JSON key for that service account and save it as `gs_service_account.json` in [ext/UvUManager/](ext/UvUManager/)
1. make a suitable Google Spreadsheet ([example](https://docs.google.com/spreadsheets/d/1rvsH9FQVwqV5IE5YJbBqVqPjCJsl6P7E376IQBg4_Pg/edit?usp=sharing)) and share the Spreadsheet with that service account.
1. fill in the `Google Sheets Stuff` section of [config.env](config.env)
### Mahjong Soul Stuff
1. fill in the `Mahjong Soul Stuff` section of [config.env](config.env)

## Running the bot
1. in a Unix shell:

        pipenv install
        pipenv shell
        ./start.sh
1. in the relevant Discord server: run `$sync_local` to sync the slash commands for that server.

## Automated Features
1. pings the server every 4 hours to see if a reconnection is necessary.
1. every ping, requests to set the `finish_time` of the tournament to be 90 days from the current time. Note that the `deadline` still needs to be extended manually (this can't be automated because only the contest creator can extend the deadline).

## Relevant Links (References)
- [Riichi Nomi's Ronnie bot](https://github.com/RiichiNomi/ronnie)
- [mjsoul.py](https://github.com/RiichiNomi/mjsoul.py)
- [ms_api: Mahjong Soul API in Python](https://github.com/MahjongRepository/mahjong_soul_api/tree/master) (this project originally relied on this API and then switched to [mjsoul.py](https://github.com/RiichiNomi/mjsoul.py))

