#!/bin/bash
ms_tournament_path=$(pip show ms_api | sed -n -e 's/^Location: //p')/ms_tournament/
sudo cp liqi_admin.json $ms_tournament_path
cd $ms_tournament_path
python generate_proto_file.py
protoc --python_out=. protocol_admin.proto
chmod +x ms-admin-plugin.py
protoc --custom_out=. --plugin=protoc-gen-custom=ms-admin-plugin.py ./protocol_admin.proto