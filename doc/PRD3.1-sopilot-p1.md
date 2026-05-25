# SoPilotMacApp Launch Page Plan

## Summary
Build a new native SwiftUI macOS app in `sandbox/SoPilotMacApp`, following the `sandbox/macCamera` Swift Package style. The app will mock a mobile app by rendering the launch experience in a centered phone-like surface inside a macOS window, based on `doc/appPages/p1-launch.html`.

## Key Changes
- Create a new Swift executable package named `SoPilotMacApp`, not modifying `sandbox/macCamera`.
- Add a SwiftUI app entrypoint, app config, launch view, reusable UI components, `Info.plist`, and a `build.sh` modeled after `macCamera`.
- Recreate the first page natively:
  - Header: `SoPilot`, version label.
  - Hero: `SoPilot`, “Local SOP Video Checker”.
  - SOP and SOUP definition panels.
  - Primary buttons: `Use a SOUP Package`, `Create a SOUP Package`.
  - Privacy/local-first feature row.
  - Mock video/inference visual with scan-line animation and `Edge Inference Status: Ready`.
  - Footer/status text.

## SOUP Engine Integration
- `Use a SOUP Package` opens an `NSOpenPanel` filtered for `.soup.json`.
- After selection, the app attempts local validation through the existing Python backend:
  - Locate Python using the same pattern as `macCamera`.
  - Set `PYTHONPATH` to `sandbox/soup-engine/src`.
  - Run `python -m sopilot_rules.tools.validate_soup <selected-file>`.
- Show compact status feedback for valid, invalid, or backend-unavailable states.
- `Create a SOUP Package` shows a mocked “Creator flow coming next” sheet/message.

## Test Plan
- Run `swift build` inside `sandbox/SoPilotMacApp`.
- Run the app locally with `swift run SoPilotMacApp` if supported by the environment.
- Validate the SOUP backend path using an existing fixture such as `sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json`.
- Confirm layout works at the app’s minimum macOS window size and still reads like a mobile mockup.

## Assumptions
- Use native SwiftUI, not a WebView wrapper.
- First milestone is one page only; no real monitoring flow yet.
- The SOUP engine is only used for package validation on this page, not full rule evaluation.
- The visual anchor should be local SwiftUI artwork/animation rather than loading the remote image from the HTML.
