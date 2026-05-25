import Foundation

struct SoupValidationResult: Equatable {
    enum Status: Equatable {
        case idle
        case validating
        case valid(String)
        case invalid(String)
        case backendUnavailable(String)
    }

    var status: Status = .idle
}

@MainActor
final class SoupPackageValidator: ObservableObject {
    @Published private(set) var result = SoupValidationResult()

    func validate(url: URL) {
        result.status = .validating

        Task.detached(priority: .userInitiated) {
            let status = Self.runValidation(url: url)
            await MainActor.run {
                self.result.status = status
            }
        }
    }

    nonisolated private static func runValidation(url: URL) -> SoupValidationResult.Status {
        guard let pythonURL = PythonRuntimeLocator.findPythonExecutable() else {
            return .backendUnavailable("Python runtime not found")
        }

        let pythonPathEntries = PythonRuntimeLocator.findPythonPathEntries()
        guard !pythonPathEntries.isEmpty else {
            return .backendUnavailable("SOUP engine source not found")
        }

        let process = Process()
        let stdout = Pipe()
        let stderr = Pipe()

        process.executableURL = pythonURL
        process.arguments = ["-m", "sopilot_rules.tools.validate_soup", url.path]
        process.standardOutput = stdout
        process.standardError = stderr

        var environment = ProcessInfo.processInfo.environment
        var pythonPath = pythonPathEntries
        if let existing = environment["PYTHONPATH"], !existing.isEmpty {
            pythonPath.append(existing)
        }
        environment["PYTHONPATH"] = pythonPath.joined(separator: ":")
        process.environment = environment

        do {
            try process.run()
            process.waitUntilExit()
        } catch {
            return .backendUnavailable(error.localizedDescription)
        }

        let output = read(pipe: stdout)
        let errorOutput = read(pipe: stderr)
        let message = output.isEmpty ? errorOutput : output

        if process.terminationStatus == 0 {
            return .valid(message.isEmpty ? "Package validated" : message)
        }
        return .invalid(message.isEmpty ? "SOUP package failed validation" : message)
    }

    nonisolated private static func read(pipe: Pipe) -> String {
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    }
}
