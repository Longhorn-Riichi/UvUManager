## Bare Minimum Features
1. multiple leaderboards (semesterly, UTA vs UTD...). Each leaderboard has its own class/spreadsheet setup.
1. the spreadsheets are the final say -- the bot is only responsible for recording raw scores onto spreadsheets and does not apply okauma or aggregate data in any way.
1. use Member ID as the unique identifier. It's either the student's EID or assigned by algorithm (go through list and find the last `EM_*` entry?). Discord ID, Mahjong Soul ID, etc., are all optional. Manual input necessary for someone without a Discord ID.

## Useful Features
1. manually enter score with auto-complete-able names (no need to remember/ask for EID; list EID by name for identification?) (automatically accounts for placement based on starting East). (command options: Sanma/Yonma, and East/South) Use `discord.ui.TextInput` (i.e., slash command takes no input and the view handles an interactive score entering session? Maybe the `Modal` is better?)? Generate UUIDs for each game. Checks for input errors (repeat names, non-existing usernames [not possible with auto-complete?], summation check -- need an optional "leftover riichi sticks" option -- they are awarded to first place AFTER placement checking.).
1. automatically extend contest duration (`prolongContest`)
1. automatically analyze the latest game played on an account with Mortal

## Not as important Features
1. allow fixing scores by game UUID (should be easy once manual score entry is implemented)
1. allow starting games at arbitrary scores (via `createContestGame`)

## Developer TODO
1. it seems only one contest can be managed at a time by one connection to Mahjong Soul, so we can't use the same instance of Contest Manager simultaneously (worst case we make an account for each contest).
1. similarly, maybe each contest (including the in-person games) requires its own instance of Google Sheets connection... if this isn't necessary, then we can make a Google Sheets **cog** and share it via the `self.bot.get_cog()` method.
1. For each extension, there should be a link in the README that points to an example of the Google Sheets doc that works for that extension. People should not be allowed to edit that example doc but can make copies of the example doc.

## `mjsoul.py` TODO
1. turn `mjsoul.py` into a package available through `pip`. Then refactor Ronhorn accordingly.
1. automate getting the Chinese WSS servers and add Chinese login functionality (`client.py`?)
1. automate getting the latest `.json` file.
1. major task: generate functions for `client.py` like what [ms-admin-plugin.py](https://github.com/MahjongRepository/mahjong_soul_api/blob/master/ms_tournament/ms-admin-plugin.py) does as a `protoc` plugin... My old protobuf update script for `mahjong_soul_api` is available [here](https://github.com/peter1357908/Ronhorn/blob/578bbe39ba90bd7ecde4d6997e1337e53eab1aa6/modules/mahjongsoul/protocol/update_proto_liqi_admin.sh)
### Protocol Documentation:
1. `open_live` field of `createContestGame` doesn't actually do anything. In fact, the same toggle on the management website doesn't work either, as a result.
1. known unknown error: `ERROR CODE 1209` (trying to pause an already paused tournament game)
1. note in the documentation how this module raises Exceptions if the response contains an Error object. (I already motified the module so GeneralMajsoulError has a field `errorCode`)
1. note how logging out through the tournament manager website (or closing the browser tab after logging in) also logs out the bot. Now the bot has to make a new WSS connection before retrying login; otherwise login results in a `2504 : "ERR_CONTEST_MGR_HAS_LOGINED`)

## Other TODO/TOTHINK

1. Update Maki's server welcome message and the #rules-and-roles channel...
1. Fix `README.md` for `ms_api`:
    1. "requerements.txt"
    1. `sudo apt install protobuf-compiler` may not work; need to install the latest version manually from [their GitHub](https://github.com/protocolbuffers/protobuf/releases)
    1. reconcile the directory inconsistency in the proto update between the regular version versus the admin version
    1. updating the `.proto` files do not require the `sudo cp` step -- in fact, just supply the update scripts...
1. the `restart` command doesn't load the latest `config.env` file?? And the `reload` command doesn't re-import the modules? So what's done exactly in those cases?
1. do we care about preventing two instances of bot running at the same time? Similar discussion [here](https://github.com/serenity-rs/serenity/issues/1054)
1. is it better to just write a different bot if the functionalities are separated by server? (how does Discord.py manage concurrency?)

## Massive Future Refactors
1. what if we just write everything in JS so we can use the `json` protocol files directly? Maybe we eventually learn to do this to build our club website?
1. use a proper database (looking up/replacing values is troublesome...). Store all data in e.g., MongoDB and display the data on own website?
1. switch from `discord.py` to `Nextcord` -- its documentation alone seems better...?
