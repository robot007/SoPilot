import Combine
import Foundation

struct VLMModel: Decodable, Identifiable, Equatable {
    let id: String
    let displayName: String
    let description: String
    let provider: String
    let repoId: String
    let recommended: Bool
    let status: String
    let sizeOnDiskMb: Int
    let localPath: String

    var isInstalled: Bool {
        status == "installed" || status == "active"
    }

    var isActive: Bool {
        status == "active"
    }

    var isDownloading: Bool {
        status == "downloading"
    }

    var downloadFailed: Bool {
        status == "download_failed"
    }
}

struct VLMModelListResponse: Decodable {
    let models: [VLMModel]
    let activeModelId: String?
}

private struct VLMCommandErrorResponse: Decodable {
    let error: String?
    let errorType: String?
}

private enum VLMModelServiceError: LocalizedError {
    case runtimeUnavailable(String)
    case commandFailed(String)
    case invalidResponse(String)

    var errorDescription: String? {
        switch self {
        case .runtimeUnavailable(let message), .commandFailed(let message), .invalidResponse(let message):
            return message
        }
    }
}

final class VLMModelService: ObservableObject {
    @Published private(set) var models: [VLMModel] = []
    @Published private(set) var activeModelId: String?
    @Published var selectedModelId: String?
    @Published private(set) var isBusy = false
    @Published private(set) var downloadingModelId: String?
    @Published var errorMessage: String?

    private let workQueue = DispatchQueue(label: "com.sopilot.FaceBoxDemo.vlm-models", qos: .userInitiated)
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    var selectedModel: VLMModel? {
        guard let selectedModelId else { return models.first }
        return models.first { $0.id == selectedModelId } ?? models.first
    }

    var statusLine: String {
        if let downloading = downloadingModel {
            return "Downloading \(downloading.displayName)..."
        }
        if let active = models.first(where: { $0.isActive }) {
            return "\(active.displayName) active"
        }
        if let installed = models.first(where: { $0.isInstalled }) {
            return "\(installed.displayName) installed"
        }
        return "No VLM installed"
    }

    var downloadingModel: VLMModel? {
        guard let downloadingModelId else { return models.first(where: { $0.isDownloading }) }
        return models.first { $0.id == downloadingModelId }
    }

    func refresh() {
        runModelListCommand(["list"])
    }

    func downloadSelectedModel() {
        guard let model = selectedModel else { return }
        runModelListCommand(["download", model.id], downloadingModelId: model.id)
    }

    func activateSelectedModel() {
        guard let model = selectedModel else { return }
        runModelListCommand(["activate", model.id])
    }

    func deleteSelectedModel() {
        guard let model = selectedModel else { return }
        runModelListCommand(["delete", model.id])
    }

    private func runModelListCommand(_ arguments: [String], downloadingModelId: String? = nil) {
        DispatchQueue.main.async {
            self.errorMessage = nil
            self.isBusy = true
            self.downloadingModelId = downloadingModelId
        }

        workQueue.async { [weak self] in
            guard let self else { return }
            let result = Result { try self.runPythonModelListCommand(arguments) }
            DispatchQueue.main.async {
                self.isBusy = false
                self.downloadingModelId = nil
                switch result {
                case .success(let response):
                    self.apply(response)
                case .failure(let error):
                    self.errorMessage = error.localizedDescription
                    if arguments.first == "download" {
                        self.refresh()
                    }
                }
            }
        }
    }

    private func apply(_ response: VLMModelListResponse) {
        models = response.models
        activeModelId = response.activeModelId

        let currentSelectionIsValid = selectedModelId.map { selected in
            response.models.contains { $0.id == selected }
        } ?? false

        if !currentSelectionIsValid {
            selectedModelId = response.activeModelId ?? response.models.first?.id
        }
    }

    private func runPythonModelListCommand(_ arguments: [String]) throws -> VLMModelListResponse {
        guard let pythonURL = PythonRuntimeLocator.findPythonExecutable() else {
            throw VLMModelServiceError.runtimeUnavailable("Python runtime was not found.")
        }
        guard let scriptURL = PythonRuntimeLocator.findResource(named: "vlm_model_manager_cli.py") else {
            throw VLMModelServiceError.runtimeUnavailable("VLM model manager script was not found.")
        }

        let process = Process()
        let outputPipe = Pipe()
        process.executableURL = pythonURL
        process.arguments = [scriptURL.path] + arguments
        process.standardOutput = outputPipe
        process.standardError = FileHandle.standardError

        var environment = ProcessInfo.processInfo.environment
        var pythonPath = PythonRuntimeLocator.findPythonPathEntries()
        if let existingPath = environment["PYTHONPATH"], !existingPath.isEmpty {
            pythonPath.append(existingPath)
        }
        if !pythonPath.isEmpty {
            environment["PYTHONPATH"] = pythonPath.joined(separator: ":")
        }
        process.environment = environment

        do {
            try process.run()
        } catch {
            throw VLMModelServiceError.runtimeUnavailable(error.localizedDescription)
        }

        let output = outputPipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()

        if process.terminationStatus != 0 {
            if let commandError = try? decoder.decode(VLMCommandErrorResponse.self, from: output),
               let message = commandError.error {
                throw VLMModelServiceError.commandFailed(message)
            }
            throw VLMModelServiceError.commandFailed("VLM model command failed.")
        }

        do {
            return try decoder.decode(VLMModelListResponse.self, from: output)
        } catch {
            let rawOutput = String(data: output, encoding: .utf8) ?? ""
            throw VLMModelServiceError.invalidResponse(
                "VLM model command returned an invalid response: \(rawOutput)"
            )
        }
    }
}
