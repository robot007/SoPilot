import Vision
import Combine

struct DetectedFace: Identifiable {
    let id = UUID()
    let boundingBox: CGRect
    let confidence: Float
}

class FaceDetector: ObservableObject {
    @Published var faces: [DetectedFace] = []
    
    private let faceDetectionRequest: VNDetectFaceRectanglesRequest
    private let processingQueue = DispatchQueue(label: "com.sopilot.FaceBoxDemo.vision", qos: .userInitiated)
    
    init() {
        faceDetectionRequest = VNDetectFaceRectanglesRequest()
        faceDetectionRequest.revision = VNDetectFaceRectanglesRequestRevision3
    }
    
    func process(sampleBuffer: CMSampleBuffer) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: .up, options: [:])
        
        do {
            try handler.perform([faceDetectionRequest])
            let observations = faceDetectionRequest.results ?? []
            
            let detectedFaces = observations.map { observation -> DetectedFace in
                let confidence = observation.confidence
                return DetectedFace(boundingBox: observation.boundingBox, confidence: confidence)
            }
            
            DispatchQueue.main.async { [weak self] in
                self?.faces = detectedFaces
            }
        } catch {
            print("Face detection error: \(error)")
        }
    }
}
