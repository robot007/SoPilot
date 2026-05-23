import Foundation

enum PythonRuntimeLocator {
    static func findResource(named name: String) -> URL? {
        let fileManager = FileManager.default
        let candidates = [
            Bundle.main.resourceURL?.appendingPathComponent(name),
            URL(fileURLWithPath: fileManager.currentDirectoryPath).appendingPathComponent("Resources/\(name)"),
            projectRoot().appendingPathComponent("sandbox/macCamera/Resources/\(name)"),
        ].compactMap { $0 }

        return candidates.first { fileManager.fileExists(atPath: $0.path) }
    }

    static func findPythonExecutable() -> URL? {
        let fileManager = FileManager.default
        let environment = ProcessInfo.processInfo.environment
        for key in ["SOPILOT_PYTHON", "YOLO_MLX_PYTHON"] {
            if let override = environment[key], fileManager.isExecutableFile(atPath: override) {
                return URL(fileURLWithPath: override)
            }
        }

        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        let candidates = [
            Bundle.main.resourceURL?.appendingPathComponent("PythonRuntime/bin/python"),
            cwd.appendingPathComponent("../../.venv/bin/python").standardizedFileURL,
            projectRoot().appendingPathComponent(".venv/bin/python"),
            URL(fileURLWithPath: "/usr/bin/python3"),
        ].compactMap { $0 }

        return candidates.first { fileManager.isExecutableFile(atPath: $0.path) }
    }

    static func findPythonPathEntries() -> [String] {
        let fileManager = FileManager.default
        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        let resourceURL = Bundle.main.resourceURL
        let candidates = [
            resourceURL?.appendingPathComponent("Python"),
            resourceURL?.appendingPathComponent("python-packages"),
            cwd.appendingPathComponent("../../src").standardizedFileURL,
            projectRoot().appendingPathComponent("src").standardizedFileURL,
        ].compactMap { $0 }

        var seen = Set<String>()
        return candidates.compactMap { candidate in
            let path = candidate.path
            guard directoryExists(atPath: path, fileManager: fileManager),
                  seen.insert(path).inserted else {
                return nil
            }
            return path
        }
    }

    static func projectRoot() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
    }

    private static func directoryExists(atPath path: String, fileManager: FileManager) -> Bool {
        var isDirectory: ObjCBool = false
        return fileManager.fileExists(atPath: path, isDirectory: &isDirectory) && isDirectory.boolValue
    }
}
