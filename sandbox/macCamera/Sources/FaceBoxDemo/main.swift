import SwiftUI

/// Dedicated Commands struct so SwiftUI knows to re-evaluate when cameraManager changes.
struct CameraCommands: Commands {
    @ObservedObject var cameraManager: CameraManager
    
    var body: some Commands {
        CommandMenu("Camera") {
            // Refresh
            Button("Refresh Camera List") {
                cameraManager.refreshCameras()
            }
            .keyboardShortcut("r", modifiers: [.command, .shift])
            
            Divider()
            
            // Camera list — flat buttons directly in the menu (no nested Menu)
            if cameraManager.availableCameras.isEmpty {
                Button("No cameras found") {}
                    .disabled(true)
            } else {
                ForEach(cameraManager.availableCameras) { camera in
                    Button {
                        cameraManager.selectCamera(uniqueID: camera.id)
                    } label: {
                        HStack {
                            // Checkmark for active camera
                            Text(cameraManager.selectedCameraID == camera.id ? "✓" : " ")
                                .frame(width: 16, alignment: .leading)
                            Text(camera.name)
                        }
                    }
                }
            }
            
            Divider()
            
            // Start / Stop
            Button(cameraManager.isRunning ? "Stop Camera" : "Start Camera") {
                cameraManager.isRunning
                    ? cameraManager.stopSession()
                    : cameraManager.startSession()
            }
            .keyboardShortcut("s", modifiers: [.command, .shift])
            .disabled(cameraManager.cameraError != nil)
        }
    }
}

@main
struct FaceBoxDemoApp: App {
    @StateObject private var cameraManager = CameraManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(cameraManager)
                .frame(minWidth: 640, minHeight: 480)
        }
        .windowResizability(.contentSize)
        .commands {
            CameraCommands(cameraManager: cameraManager)
        }
    }
}
