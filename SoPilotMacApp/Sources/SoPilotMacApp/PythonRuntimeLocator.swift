import Foundation

enum PythonRuntimeLocator {
    static func findPythonExecutable() -> URL? {
        let fileManager = FileManager.default
        let environment = ProcessInfo.processInfo.environment
        for key in ["SOPILOT_PYTHON", "YOLO_MLX_PYTHON"] {
            if let override = environment[key], fileManager.isExecutableFile(atPath: override) {
                return URL(fileURLWithPath: override)
            }
        }

        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        let root = projectRoot()
        let candidates = [
            Bundle.main.resourceURL?.appendingPathComponent("PythonRuntime/bin/python"),
            cwd.appendingPathComponent(".venv/bin/python").standardizedFileURL,
            cwd.appendingPathComponent("../.venv/bin/python").standardizedFileURL,
            root.appendingPathComponent(".venv/bin/python"),
            URL(fileURLWithPath: "/usr/bin/python3"),
        ].compactMap { $0 }

        return candidates.first { fileManager.isExecutableFile(atPath: $0.path) }
    }

    static func findPythonPathEntries() -> [String] {
        let fileManager = FileManager.default
        let root = projectRoot()
        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        let candidates = [
            Bundle.main.resourceURL?.appendingPathComponent("Python"),
            Bundle.main.resourceURL?.appendingPathComponent("python-packages"),
            root.appendingPathComponent("sandbox/soup-engine/src"),
            cwd.appendingPathComponent("sandbox/soup-engine/src").standardizedFileURL,
            cwd.appendingPathComponent("../sandbox/soup-engine/src").standardizedFileURL,
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
        let fileManager = FileManager.default
        var current = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()

        while current.path != "/" {
            let soupEngine = current.appendingPathComponent("sandbox/soup-engine/src/sopilot_rules")
            let gitDir = current.appendingPathComponent(".git")
            if fileManager.fileExists(atPath: soupEngine.path) || fileManager.fileExists(atPath: gitDir.path) {
                return current
            }
            current.deleteLastPathComponent()
        }

        return URL(fileURLWithPath: fileManager.currentDirectoryPath)
    }

    private static func directoryExists(atPath path: String, fileManager: FileManager) -> Bool {
        var isDirectory: ObjCBool = false
        return fileManager.fileExists(atPath: path, isDirectory: &isDirectory) && isDirectory.boolValue
    }
}
