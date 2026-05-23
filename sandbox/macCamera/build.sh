#!/bin/bash
set -e

APP_NAME="FaceBoxDemo"
BUILD_DIR=".build/release"
APP_BUNDLE="${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
REPO_ROOT="$(cd ../.. && pwd)"

echo "========================================"
echo "  Building ${APP_NAME}"
echo "========================================"

# 1. Build release binary
echo "→ Building Swift package (release)..."
swift build -c release

# 2. Create .app bundle
echo "→ Bundling into ${APP_BUNDLE}..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
cp "${BUILD_DIR}/${APP_NAME}" "${APP_BUNDLE}/Contents/MacOS/"

# Copy Info.plist
mkdir -p "${APP_BUNDLE}/Contents"
cp "Resources/Info.plist" "${APP_BUNDLE}/Contents/Info.plist"
APP_VERSION="$(tr -d '[:space:]' < "Resources/app_version.txt")"
if [ -n "${APP_VERSION}" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${APP_VERSION}" "${APP_BUNDLE}/Contents/Info.plist"
fi

# Copy runtime resources (YOLO worker + optional bundled models)
mkdir -p "${APP_BUNDLE}/Contents/Resources"
find "Resources" -mindepth 1 -maxdepth 1 ! -name "Info.plist" ! -name "__pycache__" -exec cp -R {} "${APP_BUNDLE}/Contents/Resources/" \;

# Copy local Python package sources used by the worker and model-manager scripts.
mkdir -p "${APP_BUNDLE}/Contents/Resources/Python"
cp -R "${REPO_ROOT}/src/yolo26mlx" "${APP_BUNDLE}/Contents/Resources/Python/"
find "${APP_BUNDLE}/Contents/Resources/Python" -name "__pycache__" -type d -prune -exec rm -rf {} +

# Bundle Python package dependencies so the app does not depend on repo-local imports only.
PYTHON_FOR_PACKAGING="${SOPILOT_PYTHON:-${REPO_ROOT}/.venv/bin/python}"
if [ -x "${PYTHON_FOR_PACKAGING}" ]; then
    echo "→ Bundling Python packages..."
    mkdir -p "${APP_BUNDLE}/Contents/Resources/python-packages"
    "${PYTHON_FOR_PACKAGING}" -m pip install --upgrade \
        --target "${APP_BUNDLE}/Contents/Resources/python-packages" \
        "${REPO_ROOT}"
else
    echo "  Python package bundling skipped; ${PYTHON_FOR_PACKAGING} was not found."
fi

# 3. Ad-hoc sign
echo "→ Ad-hoc signing..."
codesign --force --deep --sign - "${APP_BUNDLE}"

# 4. Verify
echo "→ Verifying signature..."
codesign -vv "${APP_BUNDLE}"

# 5. Create DMG
echo "→ Creating DMG..."
rm -f "${DMG_NAME}"

if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "${APP_NAME} Installer" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --app-drop-link 600 185 \
        "${DMG_NAME}" \
        "${APP_BUNDLE}"
else
    echo "  (create-dmg not found; using plain hdiutil)"
    hdiutil create -srcfolder "${APP_BUNDLE}" -volname "${APP_NAME}" "${DMG_NAME}"
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
echo ""
echo "  If Gatekeeper blocks, right-click → Open"
echo "========================================"
