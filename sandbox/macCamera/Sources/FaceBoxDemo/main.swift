import SwiftUI

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
    }
}
