import Foundation

final class YoloMLXWorker {
    private enum WorkerError: Error {
        case launchFailed(String)
        case emptyResponse
        case workerError(String)
    }

    private struct DetectionResponse: Decodable {
        struct Detection: Decodable {
            let x1: Double
            let y1: Double
            let x2: Double
            let y2: Double
            let confidence: Float
        }

        let ok: Bool
        let error: String?
        let detections: [Detection]?
    }

    private let process: Process
    private let input: FileHandle
    private let output: FileHandle
    private let ioLock = NSLock()

    static func makeDefault() -> YoloMLXWorker? {
        guard let scriptURL = PythonRuntimeLocator.findResource(named: "yolo_mlx_face_worker.py"),
              let pythonURL = PythonRuntimeLocator.findPythonExecutable(),
              let modelURL = ResourceLocator.findYoloModel() else {
            return nil
        }

        do {
            return try YoloMLXWorker(
                pythonURL: pythonURL,
                scriptURL: scriptURL,
                modelURL: modelURL
            )
        } catch {
            print("[YOLO MLX] Worker unavailable: \(error)")
            return nil
        }
    }

    private init(pythonURL: URL, scriptURL: URL, modelURL: URL) throws {
        let stdinPipe = Pipe()
        let stdoutPipe = Pipe()

        process = Process()
        process.executableURL = pythonURL
        process.arguments = [scriptURL.path]
        process.standardInput = stdinPipe
        process.standardOutput = stdoutPipe
        process.standardError = FileHandle.standardError

        var environment = ProcessInfo.processInfo.environment
        environment["YOLO_MLX_MODEL"] = modelURL.path
        environment["YOLO_MLX_FACE_CLASS_IDS"] = environment["YOLO_MLX_FACE_CLASS_IDS"] ?? "0"

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
            throw WorkerError.launchFailed(error.localizedDescription)
        }

        input = stdinPipe.fileHandleForWriting
        output = stdoutPipe.fileHandleForReading
    }

    deinit {
        if process.isRunning {
            process.terminate()
        }
    }

    func detect(jpegData: Data, width: Int, height: Int) throws -> [DetectedFace] {
        ioLock.lock()
        defer { ioLock.unlock() }

        guard process.isRunning else {
            throw WorkerError.workerError("YOLO MLX worker is not running")
        }

        let request: [String: Any] = [
            "image": jpegData.base64EncodedString(),
            "width": width,
            "height": height,
        ]
        let requestData = try JSONSerialization.data(withJSONObject: request)

        input.write(requestData)
        input.write(Data([0x0A]))

        let responseLine = output.readLineData()
        guard !responseLine.isEmpty else { throw WorkerError.emptyResponse }

        let response = try JSONDecoder().decode(DetectionResponse.self, from: responseLine)
        guard response.ok else {
            throw WorkerError.workerError(response.error ?? "Unknown YOLO MLX worker error")
        }

        return (response.detections ?? []).compactMap { detection in
            let x1 = max(0, min(width, Int(detection.x1.rounded())))
            let y1 = max(0, min(height, Int(detection.y1.rounded())))
            let x2 = max(0, min(width, Int(detection.x2.rounded())))
            let y2 = max(0, min(height, Int(detection.y2.rounded())))
            guard x2 > x1, y2 > y1 else { return nil }

            let normalizedX = CGFloat(x1) / CGFloat(width)
            let normalizedY = CGFloat(y1) / CGFloat(height)
            let normalizedWidth = CGFloat(x2 - x1) / CGFloat(width)
            let normalizedHeight = CGFloat(y2 - y1) / CGFloat(height)

            // Match Vision's normalized bottom-left origin so existing overlays remain unchanged.
            let visionY = 1 - normalizedY - normalizedHeight
            let box = CGRect(
                x: normalizedX,
                y: visionY,
                width: normalizedWidth,
                height: normalizedHeight
            )
            return DetectedFace(boundingBox: box, confidence: detection.confidence)
        }
    }
}

private enum ResourceLocator {
    static func findYoloModel() -> URL? {
        let fileManager = FileManager.default
        let environment = ProcessInfo.processInfo.environment
        if let override = environment["YOLO_MLX_MODEL"], fileManager.fileExists(atPath: override) {
            return URL(fileURLWithPath: override)
        }

        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        let sourceRoot = PythonRuntimeLocator.projectRoot()
        let resourceURL = Bundle.main.resourceURL

        // Search order: face-specific models first (if dropped in), then the
        // generic COCO model in the repo's models/ directory. The Python worker
        // applies person→face approximation when the model is COCO-trained.
        let modelNames = [
            "yolo-face.npz",
            "yolo-face.safetensors",
            "yolo26n.npz",
            "yolo26n.safetensors",
        ]

        var candidates: [URL] = []
        for name in modelNames {
            if let bundleURL = resourceURL?.appendingPathComponent("Models/\(name)") {
                candidates.append(bundleURL)
            }
            candidates.append(cwd.appendingPathComponent("Resources/Models/\(name)"))
            candidates.append(sourceRoot.appendingPathComponent("models/\(name)"))
        }

        return candidates
            .map { $0.standardizedFileURL }
            .first { fileManager.fileExists(atPath: $0.path) }
    }
}

private extension FileHandle {
    func readLineData() -> Data {
        var data = Data()

        while true {
            let chunk = self.readData(ofLength: 1)
            if chunk.isEmpty || chunk == Data([0x0A]) {
                return data
            }
            data.append(chunk)
        }
    }
}
