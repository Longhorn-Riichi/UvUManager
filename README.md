# Ronhorn

A Discord bot for Longhorn Riichi. Helps record club games (e.g., automaticaly records Mahjong Soul tournament lobby games on the club leaderboard)

# Running the bot

1. refer to the `*_FORMAT` files to make a `config.env` in the root directory and a `config.json` file for each extension in [ext/](ext/).
1. in a Unix shell:

        pipenv install
        pipenv shell
        ./start.sh

If you encounter errors regarding the protocol files, try updating them (e.g., update the tournament manager protocols with [./scripts/update_proto_liqi_admin.sh](./scripts/update_proto_liqi_admin.sh))

# References

- [Riichi Nomi's Ronnie bot](https://github.com/RiichiNomi/ronnie)
- [ms_api: Mahjong Soul API in Python](https://github.com/MahjongRepository/mahjong_soul_api/tree/master)

