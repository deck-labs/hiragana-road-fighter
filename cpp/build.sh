#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Building Hiragana Road Fighter (C++) ==="

if command -v g++ >/dev/null 2>&1 && command -v make >/dev/null 2>&1; then
    echo "Using host toolchain..."
    make
elif command -v flatpak >/dev/null 2>&1 && flatpak info org.freedesktop.Sdk//25.08 >/dev/null 2>&1; then
    echo "Using Freedesktop SDK runtime..."
    flatpak run --filesystem=host --command=make org.freedesktop.Sdk//25.08
else
    echo "ERROR: Neither host g++/make nor flatpak org.freedesktop.Sdk was found."
    exit 1
fi

echo "Build successful -> ./road_fighter_cpp"
