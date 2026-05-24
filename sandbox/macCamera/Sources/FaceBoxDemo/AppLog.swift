import Foundation

enum AppLog {
    static let logURL: URL = {
        let libraryURL = FileManager.default.urls(for: .libraryDirectory, in: .userDomainMask)[0]
        return libraryURL
            .appendingPathComponent("Logs", isDirectory: true)
            .appendingPathComponent("SoPilot", isDirectory: true)
            .appendingPathComponent("FaceBoxDemo.log")
    }()

    private static let queue = DispatchQueue(label: "com.sopilot.FaceBoxDemo.log")

    static func write(_ message: String) {
        queue.async {
            let line = "\(timestamp()) \(message)\n"
            do {
                let directoryURL = logURL.deletingLastPathComponent()
                try FileManager.default.createDirectory(
                    at: directoryURL,
                    withIntermediateDirectories: true
                )

                if !FileManager.default.fileExists(atPath: logURL.path) {
                    FileManager.default.createFile(atPath: logURL.path, contents: nil)
                }

                let handle = try FileHandle(forWritingTo: logURL)
                try handle.seekToEnd()
                try handle.write(contentsOf: Data(line.utf8))
                try handle.close()
            } catch {
                print("[FaceBoxDemo Log] \(error)")
                print(message)
            }
        }
    }

    private static func timestamp() -> String {
        ISO8601DateFormatter().string(from: Date())
    }
}
