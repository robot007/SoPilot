import SwiftUI

@main
struct SoPilotMacApp: App {
    var body: some Scene {
        WindowGroup {
            LaunchView()
                .frame(minWidth: 1040, minHeight: 700)
        }
        .windowResizability(.contentMinSize)
    }
}
