# tips for reverse-engineering Mahjong Soul admin API:
- refer to `liqi_combined.proto` for all API
- learn the message fields' possible values by examining WS messages sent by browser (Chrome: Inspect -> Network -> WS).
- decode the Protobuf with this [tool](https://protobuf-decoder.netlify.app/) if you feel lazy. To get more accurate results, decode with a tool that'll take in `liqi_combined.proto`. Remember to remove the first 3 bytes of the captured WS messages (those are message type and index; only 4th byte onward is protobuf).

boilerplate references:
- [Chinese game server](https://github.com/MahjongRepository/mahjong_soul_api/blob/master/example.py)
- [English tournament management server](https://github.com/MahjongRepository/mahjong_soul_api/blob/master/example_admin.py)

