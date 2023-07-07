# tips for reverse-engineering Mahjong Soul admin API:
- refer to liqi_admin.json for all API
- learn the protobuf field values with the Chrome plugin [WebSocket Inspector](https://chrome.google.com/webstore/detail/websocket-frame-inspector/nlajeopfbepekemjhkjcbbnencojpaae) (e.g., the fact that Twitter OAuth2 protobuf request `type` field should be `10`)
- decode the WebSocket Protobuf with this [website](https://protobuf-decoder.netlify.app/)

boilerplate references:
- [Chinese game server](https://github.com/MahjongRepository/mahjong_soul_api/blob/master/example.py)
- [English tournament management server](https://github.com/MahjongRepository/mahjong_soul_api/blob/master/example_admin.py)

