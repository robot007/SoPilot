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

private struct VLMChatResponse: Decodable {
    let answer: String?
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

    var activeModel: VLMModel? {
        models.first { $0.isActive }
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

    func askActiveModel(
        question: String,
        frameData: [Data],
        systemPrompt: String,
        completion: @escaping (Result<String, Error>) -> Void
    ) {
        guard let model = activeModel else {
            completion(.failure(VLMModelServiceError.commandFailed("No active VLM model.")))
            return
        }
        guard !frameData.isEmpty else {
            completion(.failure(VLMModelServiceError.commandFailed("No camera frames are available yet.")))
            return
        }

        workQueue.async { [weak self] in
            guard let self else { return }
            let result = Result {
                try self.runPythonChatCommand(
                    modelId: model.id,
                    question: question,
                    frameData: frameData,
                    systemPrompt: systemPrompt
                )
            }

            DispatchQueue.main.async {
                completion(result)
            }
        }
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

        process.environment = pythonEnvironment()

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

    private func runPythonChatCommand(
        modelId: String,
        question: String,
        frameData: [Data],
        systemPrompt: String
    ) throws -> String {
        guard let pythonURL = PythonRuntimeLocator.findPythonExecutable() else {
            throw VLMModelServiceError.runtimeUnavailable("Python runtime was not found.")
        }
        guard let scriptURL = PythonRuntimeLocator.findResource(named: "vlm_model_manager_cli.py") else {
            throw VLMModelServiceError.runtimeUnavailable("VLM model manager script was not found.")
        }

        var frameURLs: [URL] = []
        var systemPromptURL: URL?
        defer {
            for url in frameURLs {
                try? FileManager.default.removeItem(at: url)
            }
            if let systemPromptURL {
                try? FileManager.default.removeItem(at: systemPromptURL)
            }
        }
        for (index, data) in frameData.enumerated() {
            let frameURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("sopilot-vlm-\(UUID().uuidString)-\(index).jpg")
            try data.write(to: frameURL, options: .atomic)
            frameURLs.append(frameURL)
        }

        let trimmedSystemPrompt = systemPrompt.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedSystemPrompt.isEmpty {
            let promptURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("sopilot-vlm-system-\(UUID().uuidString).txt")
            try trimmedSystemPrompt.write(to: promptURL, atomically: true, encoding: .utf8)
            systemPromptURL = promptURL
        }

        var arguments = [
            scriptURL.path,
            "chat",
            modelId,
            "--prompt",
            question,
        ]
        for frameURL in frameURLs {
            arguments.append(contentsOf: ["--frame-file", frameURL.path])
        }
        if let systemPromptURL {
            arguments.append(contentsOf: ["--system-prompt-file", systemPromptURL.path])
        }

        let process = Process()
        let outputPipe = Pipe()
        process.executableURL = pythonURL
        process.arguments = arguments
        process.standardOutput = outputPipe
        process.standardError = FileHandle.standardError
        process.environment = pythonEnvironment()

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
            throw VLMModelServiceError.commandFailed("VLM chat command failed.")
        }

        do {
            let response = try decoder.decode(VLMChatResponse.self, from: output)
            if let answer = response.answer, !answer.isEmpty {
                return answer
            }
            throw VLMModelServiceError.invalidResponse("VLM chat command returned an empty answer.")
        } catch let error as VLMModelServiceError {
            throw error
        } catch {
            let rawOutput = String(data: output, encoding: .utf8) ?? ""
            throw VLMModelServiceError.invalidResponse(
                "VLM chat command returned an invalid response: \(rawOutput)"
            )
        }
    }

    private func pythonEnvironment() -> [String: String] {
        var environment = ProcessInfo.processInfo.environment
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        var pythonPath = PythonRuntimeLocator.findPythonPathEntries()
        if let existingPath = environment["PYTHONPATH"], !existingPath.isEmpty {
            pythonPath.append(existingPath)
        }
        if !pythonPath.isEmpty {
            environment["PYTHONPATH"] = pythonPath.joined(separator: ":")
        }
        return environment
    }
}
