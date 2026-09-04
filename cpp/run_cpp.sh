#!/bin/bash
cd "$(dirname "$0")"

# Compile if binary does not exist or if main.cpp is newer
if [ ! -f "road_fighter_cpp" ] || [ "main.cpp" -nt "road_fighter_cpp" ]; then
    ./build.sh
fi

echo "Starting Hiragana Road Fighter (C++)..."
./road_fighter_cpp "$@"
