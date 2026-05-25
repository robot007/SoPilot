#!/bin/bash
set -e

APP_NAME="SoPilotMacApp"
DISPLAY_NAME="SoPilot"
BUILD_DIR=".build/release"
APP_BUNDLE="${DISPLAY_NAME}.app"
DMG_NAME="${DISPLAY_NAME}.dmg"
REPO_ROOT="$(cd .. && pwd)"

echo "========================================"
echo "  Building ${DISPLAY_NAME}"
echo "========================================"

echo "-> Building Swift package (release)..."
swift build -c release

echo "-> Bundling into ${APP_BUNDLE}..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
cp "${BUILD_DIR}/${APP_NAME}" "${APP_BUNDLE}/Contents/MacOS/"

mkdir -p "${APP_BUNDLE}/Contents"
cp "Resources/Info.plist" "${APP_BUNDLE}/Contents/Info.plist"
APP_VERSION="$(sed -nE 's/^[[:space:]]*static let version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "Sources/SoPilotMacApp/AppConfig.swift" | head -n 1)"
if [ -z "${APP_VERSION}" ]; then
    echo "Could not read app version from Sources/SoPilotMacApp/AppConfig.swift"
    exit 1
fi
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"

mkdir -p "${APP_BUNDLE}/Contents/Resources/Python"
cp -R "${REPO_ROOT}/sandbox/soup-engine/src/sopilot_rules" "${APP_BUNDLE}/Contents/Resources/Python/"
find "${APP_BUNDLE}/Contents/Resources/Python" -name "__pycache__" -type d -prune -exec rm -rf {} +

mkdir -p "${APP_BUNDLE}/Contents/Resources/AppPages"
cp "${REPO_ROOT}/doc/appPages/PA2-createBP.png" "${APP_BUNDLE}/Contents/Resources/AppPages/"

PYTHON_FOR_PACKAGING="${SOPILOT_PYTHON:-${REPO_ROOT}/.venv/bin/python}"
if [ -x "${PYTHON_FOR_PACKAGING}" ]; then
    echo "-> Bundling Python packages..."
    mkdir -p "${APP_BUNDLE}/Contents/Resources/python-packages"
    "${PYTHON_FOR_PACKAGING}" -m pip install --upgrade \
        --target "${APP_BUNDLE}/Contents/Resources/python-packages" \
        "${REPO_ROOT}/sandbox/soup-engine"
else
    echo "  Python package bundling skipped; ${PYTHON_FOR_PACKAGING} was not found."
fi

echo "-> Ad-hoc signing..."
codesign --force --deep --sign - "${APP_BUNDLE}"

echo "-> Verifying signature..."
codesign -vv "${APP_BUNDLE}"

echo "-> Creating DMG..."
rm -f "${DMG_NAME}"

if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "${DISPLAY_NAME} Installer" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --app-drop-link 600 185 \
        "${DMG_NAME}" \
        "${APP_BUNDLE}"
else
    echo "  (create-dmg not found; using plain hdiutil)"
    hdiutil create -srcfolder "${APP_BUNDLE}" -volname "${DISPLAY_NAME}" "${DMG_NAME}"
fi

echo ""
echo "========================================"
echo "  Build complete!"
echo "========================================"
echo "  App: ${APP_BUNDLE}"
echo "  DMG: ${DMG_NAME}"
echo ""
echo "  To test:"
echo "    open ${APP_BUNDLE}"
echo "========================================"
