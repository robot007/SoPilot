// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "SoPilotMacApp",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "SoPilotMacApp", targets: ["SoPilotMacApp"])
    ],
    targets: [
        .executableTarget(
            name: "SoPilotMacApp",
            path: "Sources/SoPilotMacApp",
            swiftSettings: [
                .unsafeFlags(["-parse-as-library"])
            ]
        )
    ]
)
