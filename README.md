# Ronhorn

A bot for Longhorn Riichi. Helps record online club games and provides utilities (e.g., member registration) on the club servers.

# Running the bot

1. refer to the `*_FORMAT` files to make a `config.env` in the root directory and a `config.json` file for each extension in [ext/](ext/).
1. in a Unix shell:

        pipenv install
        pipenv shell
        ./start.sh

### recompiling the Mahjong Soul protobuf files
If you encounter issues with Mahjong Soul protobuf files in the `ms_api` package, try recompiling them with the included `liqi_admin.json`:
1. install the latest Protobuf **Compiler** (>=3.20). `apt` may have an oudated version so you have to get the right binary from [their GitHub](https://github.com/protocolbuffers/protobuf/releases) and put it in `/usr/local/bin`
1. `cd` into [modules/mahjongsoul/protocol](./modules/mahjongsoul/protocol) and run `./update_proto_liqi_admin.sh`

### updating the Mahjong Soul protocol file
You can obtain the latest `liqi_admin.json` by extracting the `nested` JS object in the obfuscated `app.xxxx.js` from the tournament manager site like [this](https://github.com/MahjongRepository/mahjong_soul_api/issues/14#issuecomment-1624183351).

# References

- [Riichi Nomi's Ronnie bot](https://github.com/RiichiNomi/ronnie)
- [ms_api: Mahjong Soul API in Python](https://github.com/MahjongRepository/mahjong_soul_api/tree/master)

