import AppKit
import Combine
import CoreImage
import CoreMedia
import Vision

private protocol FaceDetectionBackend {
    func detect(sampleBuffer: CMSampleBuffer) throws -> [DetectedFace]
}

struct DetectedFace: Identifiable {
    let id = UUID()
    let boundingBox: CGRect
    let confidence: Float
}

class FaceDetector: ObservableObject {
    @Published var faces: [DetectedFace] = []

    private let processingQueue = DispatchQueue(label: "com.sopilot.FaceBoxDemo.detector", qos: .userInitiated)
    private let stateLock = NSLock()
    private let visionBackend = VisionFaceDetectionBackend()
    private let yoloBackend = YoloMLXFaceDetectionBackend()
    private let minFrameInterval: TimeInterval = 0.18
    private var isProcessing = false
    private var lastProcessedAt = Date.distantPast

    init() {
    }

    func process(sampleBuffer: CMSampleBuffer) {
        stateLock.lock()
        let now = Date()
        guard !isProcessing, now.timeIntervalSince(lastProcessedAt) >= minFrameInterval else {
            stateLock.unlock()
            return
        }
        isProcessing = true
        lastProcessedAt = now
        stateLock.unlock()

        processingQueue.async { [weak self] in
            guard let self else { return }
            defer {
                self.stateLock.lock()
                self.isProcessing = false
                self.stateLock.unlock()
            }

            do {
                let yoloFaces = try self.yoloBackend.detect(sampleBuffer: sampleBuffer)
                let detectedFaces = yoloFaces.isEmpty
                    ? try self.visionBackend.detect(sampleBuffer: sampleBuffer)
                    : yoloFaces

                DispatchQueue.main.async { [weak self] in
                    self?.faces = detectedFaces
                }
            } catch {
                do {
                    let detectedFaces = try self.visionBackend.detect(sampleBuffer: sampleBuffer)
                    DispatchQueue.main.async { [weak self] in
                        self?.faces = detectedFaces
                    }
                } catch {
                    print("Face detection error: \(error)")
                }
            }
        }
    }
}

private final class VisionFaceDetectionBackend: FaceDetectionBackend {
    private let faceDetectionRequest: VNDetectFaceRectanglesRequest

    init() {
        faceDetectionRequest = VNDetectFaceRectanglesRequest()
        faceDetectionRequest.revision = VNDetectFaceRectanglesRequestRevision3
    }

    func detect(sampleBuffer: CMSampleBuffer) throws -> [DetectedFace] {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return [] }

        let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: .up, options: [:])
        try handler.perform([faceDetectionRequest])

        return (faceDetectionRequest.results ?? []).map { observation in
            DetectedFace(boundingBox: observation.boundingBox, confidence: observation.confidence)
        }
    }
}

private final class YoloMLXFaceDetectionBackend: FaceDetectionBackend {
    private enum BackendError: Error {
        case unavailable
        case invalidFrame
    }

    private let ciContext = CIContext()
    private let worker: YoloMLXWorker?

    init() {
        worker = YoloMLXWorker.makeDefault()
    }

    func detect(sampleBuffer: CMSampleBuffer) throws -> [DetectedFace] {
        guard let worker else { throw BackendError.unavailable }
        guard let frame = jpegFrame(from: sampleBuffer) else { throw BackendError.invalidFrame }
        return try worker.detect(jpegData: frame.data, width: frame.width, height: frame.height)
    }

    private func jpegFrame(from sampleBuffer: CMSampleBuffer) -> (data: Data, width: Int, height: Int)? {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return nil }
        let image = CIImage(cvPixelBuffer: pixelBuffer)
        guard let cgImage = ciContext.createCGImage(image, from: image.extent) else { return nil }

        let bitmap = NSBitmapImageRep(cgImage: cgImage)
        let properties: [NSBitmapImageRep.PropertyKey: Any] = [.compressionFactor: 0.65]
        guard let data = bitmap.representation(using: .jpeg, properties: properties) else { return nil }

        return (data, cgImage.width, cgImage.height)
    }
}
