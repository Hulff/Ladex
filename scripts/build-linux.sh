#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Build this target on Linux; PyInstaller does not cross-compile Linux binaries." >&2
    exit 1
fi

python -m PyInstaller \
    --noconfirm \
    --clean \
    --onefile \
    --windowed \
    --name TabConv \
    --paths src \
    --collect-all charset_normalizer \
    --collect-all PySide6 \
    src/tabconv_gui_entry.py

app_dir="dist/TabConv.AppDir"
mkdir -p "$app_dir/usr/bin" "$app_dir/usr/share/icons/hicolor/scalable/apps"
cp dist/TabConv "$app_dir/usr/bin/TabConv"
cp packaging/tabconv.svg "$app_dir/usr/share/icons/hicolor/scalable/apps/tabconv.svg"
cp packaging/tabconv.desktop "$app_dir/tabconv.desktop"
cp packaging/tabconv.svg "$app_dir/tabconv.svg"
cp packaging/AppRun "$app_dir/AppRun"
chmod +x "$app_dir/AppRun" "$app_dir/usr/bin/TabConv"

appimagetool="${APPIMAGETOOL:-appimagetool}"
if command -v "$appimagetool" >/dev/null 2>&1 || [[ -x "$appimagetool" ]]; then
    ARCH="${ARCH:-x86_64}" APPIMAGE_EXTRACT_AND_RUN=1 "$appimagetool" "$app_dir" \
        "dist/TabConv-${ARCH:-x86_64}.AppImage"
else
    echo "AppImage tool not found; created $app_dir and dist/TabConv."
fi

echo "Created dist/TabConv and $app_dir"
