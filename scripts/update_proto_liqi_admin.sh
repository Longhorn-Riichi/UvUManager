#!/bin/bash
cd $(pip show ms_api | sed -n -e 's/^Location: //p')/ms_tournament
python generate_proto_file.py
protoc --python_out=. protocol_admin.proto
chmod +x ms-admin-plugin.py
protoc --custom_out=. --plugin=protoc-gen-custom=ms-admin-plugin.py ./protocol_admin.proto