import SwiftUI

@main
struct FaceBoxDemoApp: App {
    @StateObject private var cameraManager = CameraManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(cameraManager)
                .frame(minWidth: 960, minHeight: 520)
        }
        .windowResizability(.contentSize)
    }
}
