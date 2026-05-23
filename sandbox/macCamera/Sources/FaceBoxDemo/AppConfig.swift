import Foundation

enum AppConfig {
    static let version = readTextConfig(named: "app_version.txt") ?? "unknown"

    private static func readTextConfig(named name: String) -> String? {
        guard let url = PythonRuntimeLocator.findResource(named: name),
              let contents = try? String(contentsOf: url, encoding: .utf8) else {
            return nil
        }

        let value = contents.trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? nil : value
    }
}
