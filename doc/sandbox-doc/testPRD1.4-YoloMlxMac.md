# FaceBoxDemo macOS App — Build Documentation

## Goal
Build a minimal native macOS SwiftUI app (`FaceBoxDemo.app`) that shows live camera preview with real-time face detection overlays, packaged into a `.dmg` installer.

## What Was Built

A complete Swift Package Manager project in `sandbox/macCamera/` that produces:
- `FaceBoxDemo.app` — double-clickable macOS app (~234 KB binary)
- `FaceBoxDemo.dmg` — disk image containing the app (~79 KB)

## Architecture

```
sandbox/macCamera/
├── Package.swift
├── build.sh
├── Sources/FaceBoxDemo/
│   ├── main.swift              # @main SwiftUI app entry
│   ├── ContentView.swift       # ZStack: preview + face overlays
│   ├── CameraManager.swift     # AVFoundation session + permissions
│   ├── FaceDetector.swift      # Vision VNDetectFaceRectanglesRequest
│   └── CameraPreview.swift     # NSViewRepresentable wrapper
├── Resources/
│   └── Info.plist              # Bundle ID + NSCameraUsageDescription
├── FaceBoxDemo.app             # ← Built artifact
└── FaceBoxDemo.dmg             # ← Built artifact
```

## Technologies Used

| Layer | Framework |
|-------|-----------|
| UI | SwiftUI |
| Camera | AVFoundation (`AVCaptureSession`) |
| Face Detection | Apple Vision (`VNDetectFaceRectanglesRequest`) |
| Packaging | `swift build`, `codesign`, `hdiutil` |

## Build Commands

```bash
cd sandbox/macCamera
./build.sh
```

The script performs:
1. `swift build -c release` — compile optimized binary
2. Bundle binary + `Info.plist` into `FaceBoxDemo.app`
3. Ad-hoc sign: `codesign --force --deep --sign - FaceBoxDemo.app`
4. Create DMG: `hdiutil create -srcfolder FaceBoxDemo.app ...`

## How to Run

### From Terminal (for testing)
```bash
cd sandbox/macCamera
open FaceBoxDemo.app
```

### From DMG (for end users)
1. Double-click `FaceBoxDemo.dmg` to mount it
2. Drag `FaceBoxDemo.app` to `/Applications`
3. Double-click the app from `/Applications`

## First Launch — Gatekeeper

Because the app is **ad-hoc signed** (no Apple Developer ID), macOS Gatekeeper will block it on first launch.

**What you'll see:**
> "FaceBoxDemo" cannot be opened because the developer cannot be verified.

**How to bypass (first time only):**
1. **Right-click** the app → **Open**
2. Click **Open** in the dialog
3. The app will launch normally from then on

**Alternative:** Run this once in Terminal:
```bash
xattr -dr com.apple.quarantine sandbox/macCamera/FaceBoxDemo.app
```

## Camera Permission

On first launch, macOS will show a system dialog:
> **FaceBoxDemo** would like to access the camera.

Click **Allow**. If denied, the app shows a permission-denied screen with a button to open System Settings.

## App Behavior

| Feature | Status |
|---------|--------|
| Launch camera on startup | ✅ |
| Live preview | ✅ |
| Real-time face detection | ✅ |
| Green bounding box overlay | ✅ |
| Label above box (`face` or `face 0.XX`) | ✅ |
| Permission-denied UI | ✅ |
| No cloud calls | ✅ (Vision runs locally) |

## Notes on Confidence Scores

`VNDetectFaceRectanglesRequest` on macOS does not always provide varying confidence values. The app shows:
- `face 0.85` when Vision provides a meaningful confidence (< 1.0)
- `face` when confidence is 1.0 (common on macOS)

**Future:** When you replace Vision with YOLO MLX, confidence scores will come naturally from the YOLO detector.

## Production Signing (Later)

To eliminate the Gatekeeper warning for distribution:

1. **Apple Developer Program** ($99/year)
2. **Sign with Developer ID:**
   ```bash
   codesign --sign "Developer ID Application: Your Name" FaceBoxDemo.app
   ```
3. **Notarize the DMG:**
   ```bash
   xcrun notarytool submit FaceBoxDemo.dmg --wait --apple-id your@email.com
   ```
4. **Staple the ticket:**
   ```bash
   xcrun stapler staple FaceBoxDemo.dmg
   ```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `swift build` fails | Ensure Xcode 15+ and `swift --version` works |
| Camera not found | Check Privacy & Security → Camera → allow Terminal/IDE |
| App won't open | Right-click → Open, or run `xattr -dr com.apple.quarantine` |
| No face boxes | Ensure face is well-lit and facing camera |
| DMG won't mount | Double-click again; try `hdiutil attach FaceBoxDemo.dmg` |

## Verification Checklist

- [x] `swift build -c release` succeeds
- [x] `FaceBoxDemo.app` bundle created with correct structure
- [x] Ad-hoc signature valid
- [x] `FaceBoxDemo.dmg` created
- [ ] App launches by double-click (test on Mac with display)
- [ ] Camera permission prompt appears
- [ ] Live preview works
- [ ] Face box + label appear
- [ ] DMG installs the app
