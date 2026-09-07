#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "========================================================="
echo "   Building Hiragana Road Fighter Python AppImage        "
echo "========================================================="

# 1. Ensure Python Virtual Environment
VENV_PATH="/tmp/pygame_build_venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install --upgrade pip setuptools pygame pyinstaller
fi

# Ensure packages are up to date
"$VENV_PATH/bin/pip" install -q pygame pyinstaller

# 2. Compile with PyInstaller
echo "=== 1. Compiling Standalone Python Distribution ==="
BUILD_DIR="/tmp/pyinstaller_road_fighter"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

"$VENV_PATH/bin/pyinstaller" \
    --name "hiragana_road_fighter" \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "$DIR/assets:assets" \
    --paths "$DIR/python" \
    "$DIR/python/main.py"

cd "$DIR"

# 3. Assemble AppDir
echo "=== 2. Assembling AppDir ==="
APPDIR="/tmp/Hiragana_Road_Fighter_Py.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/icons/hicolor/256x256/apps" "$APPDIR/usr/share/applications"

# Copy PyInstaller bundle into AppDir
cp -r "$BUILD_DIR/dist/hiragana_road_fighter/"* "$APPDIR/usr/bin/"

# Generate High-Res 256x256 Icon
"$VENV_PATH/bin/python" -c "
import pygame
pygame.init()
size = 256
surf = pygame.Surface((size, size), pygame.SRCALPHA)

# Dark arcade chassis with neon border
pygame.draw.rect(surf, (15, 20, 32), (0, 0, size, size), border_radius=36)
pygame.draw.rect(surf, (0, 217, 255), (0, 0, size, size), 6, border_radius=36)

# Road strip
pygame.draw.rect(surf, (45, 48, 55), (68, 0, 120, size))
for y in range(0, size, 32):
    pygame.draw.rect(surf, (255, 215, 0), (126, y, 4, 18))
    # Curbs
    c_col = (225, 45, 45) if (y // 16) % 2 == 0 else (255, 255, 255)
    pygame.draw.rect(surf, c_col, (64, y, 4, 32))
    pygame.draw.rect(surf, c_col, (188, y, 4, 32))

# Red player car in center
car_w, car_h = 44, 88
car_x = (size - car_w) // 2
car_y = (size - car_h) // 2 + 10
pygame.draw.rect(surf, (220, 35, 35), (car_x, car_y, car_w, car_h), border_radius=8)
pygame.draw.rect(surf, (255, 60, 60), (car_x + 4, car_y + 4, car_w - 8, car_h - 8), border_radius=6)
# Windshields
pygame.draw.rect(surf, (100, 200, 255), (car_x + 6, car_y + 14, car_w - 12, 16), border_radius=3)
pygame.draw.rect(surf, (100, 200, 255), (car_x + 6, car_y + car_h - 26, car_w - 12, 10), border_radius=3)

# Japanese Hiragana glyph on car roof
try:
    f = pygame.font.Font('$DIR/assets/fonts/NotoSansCJK-Bold.ttc', 26)
    t = f.render('あ', True, (255, 255, 255))
    surf.blit(t, t.get_rect(center=(size // 2, car_y + car_h // 2 - 2)))
except Exception as e:
    pass

pygame.image.save(surf, '$APPDIR/hiragana_road_fighter.png')
pygame.image.save(surf, '$APPDIR/usr/share/icons/hicolor/256x256/apps/hiragana_road_fighter.png')
"

# Copy Icon to root of nihongo smith
cp "$APPDIR/hiragana_road_fighter.png" "$DIR/hiragana_road_fighter.png"

# Create Desktop Entry
cat << 'EOD' > "$APPDIR/hiragana_road_fighter.desktop"
[Desktop Entry]
Name=Hiragana Road Fighter
Comment=Retro Hiragana Learning Arcade Racer (Python Edition)
Exec=hiragana_road_fighter
Icon=hiragana_road_fighter
Terminal=false
Type=Application
Categories=Game;ArcadeGame;Education;
EOD

cp "$APPDIR/hiragana_road_fighter.desktop" "$APPDIR/usr/share/applications/"

# Create AppRun Launcher
cat << 'EOA' > "$APPDIR/AppRun"
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin/_internal:${HERE}/usr/lib:${LD_LIBRARY_PATH}"
cd "${HERE}"
exec "${HERE}/usr/bin/hiragana_road_fighter" "$@"
EOA

chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/hiragana_road_fighter"

# 4. Packaging AppImage with appimagetool
echo "=== 3. Packaging Standalone AppImage ==="
TOOL="/home/deck/.local/bin/appimagetool"
if [ ! -x "$TOOL" ]; then
    TOOL="/tmp/appimagetool"
    if [ ! -f "$TOOL" ]; then
        curl -L -o "$TOOL" "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        chmod +x "$TOOL"
    fi
fi

OUT_FILE="/home/deck/Downloads/Hiragana_Road_Fighter-x86_64.AppImage"
rm -f "$OUT_FILE"

echo "Running $TOOL on $APPDIR -> $OUT_FILE..."
ARCH=x86_64 "$TOOL" "$APPDIR" "$OUT_FILE"
chmod +x "$OUT_FILE"

# Also place copy in project root
cp -f "$OUT_FILE" "$DIR/Hiragana_Road_Fighter-x86_64.AppImage"

echo "========================================================="
echo " AppImage successfully generated at:                      "
echo "   $OUT_FILE                                             "
echo " Size: $(du -h "$OUT_FILE" | cut -f1)                    "
echo "========================================================="
