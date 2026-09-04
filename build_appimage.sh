#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=== 1. Compiling C++ Binary ==="
cd "$DIR/cpp"
./build.sh
cd "$DIR"

echo "=== 2. Preparing AppDir ==="
APPDIR="/tmp/Hiragana_Road_Fighter.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share/fonts" "$APPDIR/usr/share/icons/hicolor/256x256/apps" "$APPDIR/assets/fonts"

# Copy binary
cp "$DIR/cpp/road_fighter_cpp" "$APPDIR/usr/bin/"

# Copy Japanese Noto font (Bold preferred for maximum clarity)
cp /usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc "$APPDIR/assets/fonts/" 2>/dev/null || cp /usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc "$APPDIR/assets/fonts/" 2>/dev/null || true
cp /usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc "$APPDIR/usr/share/fonts/" 2>/dev/null || cp /usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc "$APPDIR/usr/share/fonts/" 2>/dev/null || true

# Generate icon
python3 -c "
import zlib, struct
def create_png(filename, width, height):
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)
        for x in range(width):
            if x < 4 or x >= width - 4 or y < 4 or y >= height - 4:
                raw_data.extend([255, 215, 0, 255])
            elif 40 <= x <= 48 or 208 <= x <= 216:
                raw_data.extend([255, 255, 255, 255])
            elif 124 <= x <= 132 and (y % 40 < 24):
                raw_data.extend([255, 235, 59, 255])
            elif 100 <= x <= 156 and 80 <= y <= 190:
                if 108 <= x <= 148 and 100 <= y <= 165:
                    raw_data.extend([180, 20, 20, 255])
                elif (112 <= x <= 144 and 90 <= y <= 98) or (112 <= x <= 144 and 168 <= y <= 176):
                    raw_data.extend([100, 200, 255, 255])
                else:
                    raw_data.extend([230, 40, 40, 255])
            elif (92 <= x <= 99 or 157 <= x <= 164) and ((86 <= y <= 112) or (158 <= y <= 184)):
                raw_data.extend([20, 20, 20, 255])
            else:
                raw_data.extend([28, 34, 46, 255])
    png = bytearray(b'\x89PNG\r\n\x1a\n')
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    png.extend(struct.pack('>I', len(ihdr)) + b'IHDR' + ihdr + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr)))
    compressed = zlib.compress(bytes(raw_data), 9)
    png.extend(struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', zlib.crc32(b'IDAT' + compressed)))
    png.extend(struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND')))
    with open(filename, 'wb') as f:
        f.write(png)
create_png('$APPDIR/hiragana_road_fighter.png', 256, 256)
create_png('$APPDIR/usr/share/icons/hicolor/256x256/apps/hiragana_road_fighter.png', 256, 256)
"

# Bundle dynamic shared libraries
for lib in /usr/lib/libfreetype.so.6 /usr/lib/libSDL2-2.0.so.0 /usr/lib/libpng16.so.16 /usr/lib/libharfbuzz.so.0 /usr/lib/libbrotlidec.so.1 /usr/lib/libbrotlicommon.so.1 /usr/lib/libbz2.so.1.0 /usr/lib/libz.so.1; do
    if [ -f "$lib" ]; then
        cp -L "$lib" "$APPDIR/usr/lib/"
    fi
done

# Desktop Entry
cat << 'EOD' > "$APPDIR/hiragana_road_fighter.desktop"
[Desktop Entry]
Name=Hiragana Road Fighter
Comment=Retro Hiragana Learning Arcade Racer
Exec=road_fighter_cpp
Icon=hiragana_road_fighter
Terminal=false
Type=Application
Categories=Game;ArcadeGame;
EOD

# AppRun Launcher
cat << 'EOA' > "$APPDIR/AppRun"
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PATH="${HERE}/usr/bin:${PATH}"
cd "${HERE}"
exec "${HERE}/usr/bin/road_fighter_cpp" "$@"
EOA
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/road_fighter_cpp"

echo "=== 3. Packaging AppImage ==="
if [ ! -f /tmp/appimagetool ]; then
    curl -L -o /tmp/appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x /tmp/appimagetool
fi

OUT_FILE="/home/deck/Downloads/Hiragana_Road_Fighter-x86_64.AppImage"
ARCH=x86_64 /tmp/appimagetool "$APPDIR" "$OUT_FILE"
chmod +x "$OUT_FILE"
cp -f "$OUT_FILE" "/home/deck/Downloads/Hiragana_Road_Fighter-v0.01-x86_64.AppImage"

echo "=== AppImage created successfully: $OUT_FILE and v0.01 ==="
