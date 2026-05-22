// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "FaceBoxDemo",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "FaceBoxDemo", targets: ["FaceBoxDemo"])
    ],
    targets: [
        .executableTarget(
            name: "FaceBoxDemo",
            path: "Sources/FaceBoxDemo",
            swiftSettings: [
                .unsafeFlags(["-parse-as-library"])
            ]
        )
    ]
)
