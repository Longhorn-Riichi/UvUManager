# Ronhorn

A bot for Longhorn Riichi. Helps record online club games and provides utilities (e.g., member registration) on the club servers.

# Running the bot

1. refer to the `*_FORMAT` files to make a `config.env` in the root directory and a `config.json` file for each extension in [ext/](ext/).
1. in a Unix shell:

        pipenv install
        pipenv shell
        ./start.sh
1. in the respective servers: run `$sync_local` to sync the slash commands for that server.

# References

- [Riichi Nomi's Ronnie bot](https://github.com/RiichiNomi/ronnie)
- [mjsou.py](https://github.com/RiichiNomi/mjsoul.py)
- [ms_api: Mahjong Soul API in Python](https://github.com/MahjongRepository/mahjong_soul_api/tree/master)

