#!/bin/bash
cd $(pip show ms_api | sed -n -e 's/^Location: //p')/ms
python generate_proto_file.py
protoc --python_out=. protocol.proto
chmod +x ms-plugin.py
protoc --custom_out=. --plugin=protoc-gen-custom=ms-plugin.py ./protocol.proto