import AVFoundation
import AppKit
import Combine
import CoreImage

enum CameraAuthorizationStatus {
    case notDetermined
    case authorized
    case denied
}

enum CameraError: LocalizedError {
    case noCameraFound
    case inputError(Error)
    case sessionStartFailed
    
    var errorDescription: String? {
        switch self {
        case .noCameraFound:
            return "No camera device found on this Mac."
        case .inputError(let error):
            return "Camera input error: \(error.localizedDescription)"
        case .sessionStartFailed:
            return "Failed to start camera session."
        }
    }
}

/// Lightweight, Sendable-safe info for UI menus.
struct CameraInfo: Identifiable, Hashable, Sendable {
    let id: String       // uniqueID
    let name: String     // localizedName
}

private struct RecentVideoFrame {
    let capturedAt: Date
    let jpegData: Data
    let faces: [DetectedFace]
}

class CameraManager: NSObject, ObservableObject {
    @Published var authorizationStatus: CameraAuthorizationStatus = .notDetermined
    @Published var cameraError: CameraError?
    @Published var isRunning = false
    
    // MARK: - Camera Menu State
    @Published var availableCameras: [CameraInfo] = []
    @Published var selectedCameraID: String?
    @Published var frameDimensions: CGSize = .zero
    
    let session = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "com.sopilot.FaceBoxDemo.session")
    private let frameLock = NSLock()
    private let ciContext = CIContext()
    private var faceDetector: FaceDetector?
    private var latestJPEGData: Data?
    private var recentVideoFrames: [RecentVideoFrame] = []
    private var lastBufferedFrameAt = Date.distantPast
    
    override init() {
        super.init()
        checkAuthorization()
    }
    
    func setFaceDetector(_ detector: FaceDetector) {
        self.faceDetector = detector
    }

    func latestFrameJPEGData(compressionQuality: CGFloat = 0.78) -> Data? {
        frameLock.lock()
        let data = latestJPEGData
        frameLock.unlock()
        return data
    }

    func recentFrameJPEGs(windowSeconds: TimeInterval = 5, maxFrames: Int = 6) -> [Data] {
        recentFrames(windowSeconds: windowSeconds, maxFrames: maxFrames).map(\.jpegData)
    }

    func vlmFrameJPEGs(windowSeconds: TimeInterval = 5, maxFrames: Int = 6) -> [Data] {
        let frames = recentFrames(windowSeconds: windowSeconds, maxFrames: maxFrames)
        AppLog.write(
            "[VLM YOLO Overlay] requestedFrames=\(frames.count) "
                + "overlayEnabled=\(AppConfig.sendYoloOverlayVLM) "
                + "configuredFontSize=\(AppConfig.yoloFontSize)pt"
        )
        guard AppConfig.sendYoloOverlayVLM else {
            return frames.map(\.jpegData)
        }

        let fallbackFaces = faceDetector?.snapshotFaces() ?? []
        return frames.map { frame in
            let faces = frame.faces.isEmpty ? fallbackFaces : frame.faces
            guard !faces.isEmpty else {
                AppLog.write("[VLM YOLO Overlay] skippedFrame=noFaces")
                return frame.jpegData
            }
            return yoloOverlayJPEGData(from: frame.jpegData, faces: faces) ?? frame.jpegData
        }
    }

    private func recentFrames(windowSeconds: TimeInterval, maxFrames: Int) -> [RecentVideoFrame] {
        let cutoff = Date().addingTimeInterval(-windowSeconds)
        frameLock.lock()
        let frames = recentVideoFrames
            .filter { $0.capturedAt >= cutoff }
            .suffix(maxFrames)
        frameLock.unlock()
        return Array(frames)
    }
    
    // MARK: - Authorization
    
    private func checkAuthorization() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            authorizationStatus = .authorized
            refreshCameras()
            configureSession()
        case .notDetermined:
            requestAuthorization()
        case .denied, .restricted:
            authorizationStatus = .denied
        @unknown default:
            authorizationStatus = .denied
        }
    }
    
    private func requestAuthorization() {
        AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            DispatchQueue.main.async {
                if granted {
                    self?.authorizationStatus = .authorized
                    self?.refreshCameras()
                    self?.configureSession()
                } else {
                    self?.authorizationStatus = .denied
                }
            }
        }
    }
    
    // MARK: - Camera Discovery
    
    /// Discover all video capture devices (built-in + USB + external) and publish them.
    func refreshCameras() {
        let devices = allVideoDevices()
        availableCameras = devices.map { CameraInfo(id: $0.uniqueID, name: $0.localizedName) }
        
        print("[CameraManager] Discovered \(devices.count) camera(s):")
        for d in devices {
            print("  - \(d.localizedName) (id: \(d.uniqueID), type: \(d.deviceType))")
        }
        
        // Auto-select first camera if nothing selected yet
        if selectedCameraID == nil, let first = availableCameras.first {
            selectedCameraID = first.id
            print("[CameraManager] Auto-selected: \(first.name)")
        }
    }
    
    /// Return every video device visible to AVFoundation.
    private func allVideoDevices() -> [AVCaptureDevice] {
        var deviceTypes: [AVCaptureDevice.DeviceType] = [
            .builtInWideAngleCamera,
        ]
        if #available(macOS 14.0, *) {
            deviceTypes.append(.external)
        }
        
        let discovery = AVCaptureDevice.DiscoverySession(
            deviceTypes: deviceTypes,
            mediaType: .video,
            position: .unspecified
        )
        return discovery.devices
    }
    
    /// Look up an AVCaptureDevice by its uniqueID string.
    private func deviceForID(_ uniqueID: String) -> AVCaptureDevice? {
        allVideoDevices().first { $0.uniqueID == uniqueID }
    }
    
    // MARK: - Camera Selection
    
    /// Switch the active session to a different camera.
    func selectCamera(uniqueID: String) {
        guard selectedCameraID != uniqueID else {
            print("[CameraManager] Already using camera \(uniqueID)")
            return
        }
        selectedCameraID = uniqueID
        if let name = availableCameras.first(where: { $0.id == uniqueID })?.name {
            print("[CameraManager] Switching to: \(name)")
        }
        
        // Stop current session on main, then reconfigure.
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            if self.session.isRunning {
                self.session.stopRunning()
                self.isRunning = false
            }
            // Brief delay so stopRunning() finishes before we reconfigure.
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                self.configureSession()
            }
        }
    }
    
    // MARK: - Session Configuration
    
    /// Configure the capture session (must run on session queue).
    /// startRunning() is called on main thread after configuration completes.
    private func configureSession() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            
            self.session.beginConfiguration()
            defer { self.session.commitConfiguration() }
            
            // Remove existing inputs/outputs to avoid duplicates
            self.session.inputs.forEach { self.session.removeInput($0) }
            self.session.outputs.forEach { self.session.removeOutput($0) }
            
            self.session.sessionPreset = .high
            
            // Resolve the camera to use: selected > first available
            let device: AVCaptureDevice?
            if let id = self.selectedCameraID,
               let found = self.deviceForID(id) {
                device = found
            } else {
                device = self.allVideoDevices().first
            }
            
            guard let selectedDevice = device else {
                DispatchQueue.main.async {
                    self.cameraError = .noCameraFound
                }
                return
            }
            
            do {
                let input = try AVCaptureDeviceInput(device: selectedDevice)
                if self.session.canAddInput(input) {
                    self.session.addInput(input)
                }
            } catch {
                DispatchQueue.main.async {
                    self.cameraError = .inputError(error)
                }
                return
            }
            
            // Add video output
            self.videoOutput.setSampleBufferDelegate(
                self,
                queue: DispatchQueue(label: "com.sopilot.FaceBoxDemo.video", qos: .userInitiated)
            )
            self.videoOutput.alwaysDiscardsLateVideoFrames = true
            if self.session.canAddOutput(self.videoOutput) {
                self.session.addOutput(self.videoOutput)
            }
            
            // Clear any previous error now that we have a valid config
            DispatchQueue.main.async {
                self.cameraError = nil
            }
            
            // Start running on MAIN THREAD — required by AVCaptureSession on macOS
            DispatchQueue.main.async {
                self.session.startRunning()
                self.isRunning = self.session.isRunning
                print("[CameraManager] Session started: \(self.isRunning)")
            }
        }
    }
    
    // MARK: - Start / Stop
    
    func startSession() {
        DispatchQueue.main.async { [weak self] in
            guard let self = self, !self.session.isRunning else { return }
            self.session.startRunning()
            self.isRunning = self.session.isRunning
        }
    }
    
    func stopSession() {
        DispatchQueue.main.async { [weak self] in
            guard let self = self, self.session.isRunning else { return }
            self.session.stopRunning()
            self.isRunning = false
        }
    }
}

// MARK: - AVCaptureVideoDataOutputSampleBufferDelegate

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        if let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) {
            bufferRecentFrameIfNeeded(imageBuffer)

            let width = CVPixelBufferGetWidth(imageBuffer)
            let height = CVPixelBufferGetHeight(imageBuffer)
            let newDimensions = CGSize(width: CGFloat(width), height: CGFloat(height))
            if newDimensions != self.frameDimensions {
                DispatchQueue.main.async {
                    self.frameDimensions = newDimensions
                }
            }
        }
        faceDetector?.process(sampleBuffer: sampleBuffer)
    }

    private func bufferRecentFrameIfNeeded(_ pixelBuffer: CVPixelBuffer) {
        let now = Date()

        frameLock.lock()
        let shouldBuffer = now.timeIntervalSince(lastBufferedFrameAt) >= 1
        frameLock.unlock()

        guard shouldBuffer,
              let jpegData = jpegData(from: pixelBuffer, compressionQuality: 0.78) else {
            return
        }

        frameLock.lock()
        latestJPEGData = jpegData
        lastBufferedFrameAt = now
        recentVideoFrames.append(
            RecentVideoFrame(
                capturedAt: now,
                jpegData: jpegData,
                faces: faceDetector?.snapshotFaces() ?? []
            )
        )

        let cutoff = now.addingTimeInterval(-5)
        recentVideoFrames = Array(
            recentVideoFrames
                .filter { $0.capturedAt >= cutoff }
                .suffix(6)
        )
        frameLock.unlock()
    }

    private func jpegData(from pixelBuffer: CVPixelBuffer, compressionQuality: CGFloat) -> Data? {
        let image = CIImage(cvPixelBuffer: pixelBuffer)
        guard let cgImage = ciContext.createCGImage(image, from: image.extent) else { return nil }

        let bitmap = NSBitmapImageRep(cgImage: cgImage)
        return bitmap.representation(
            using: .jpeg,
            properties: [.compressionFactor: compressionQuality]
        )
    }

    private func yoloOverlayJPEGData(from jpegData: Data, faces: [DetectedFace]) -> Data? {
        guard !faces.isEmpty,
              let sourceRep = NSBitmapImageRep(data: jpegData) else {
            return nil
        }

        let imageSize = NSSize(width: sourceRep.pixelsWide, height: sourceRep.pixelsHigh)
        guard imageSize.width > 0, imageSize.height > 0 else { return nil }

        let sourceImage = NSImage(size: imageSize)
        sourceImage.addRepresentation(sourceRep)

        let annotatedImage = NSImage(size: imageSize)
        annotatedImage.lockFocus()
        sourceImage.draw(
            in: NSRect(origin: .zero, size: imageSize),
            from: NSRect(origin: .zero, size: imageSize),
            operation: .copy,
            fraction: 1
        )

        drawYoloOverlay(faces: faces, imageSize: imageSize)
        annotatedImage.unlockFocus()

        guard let tiffData = annotatedImage.tiffRepresentation,
              let annotatedRep = NSBitmapImageRep(data: tiffData) else {
            return nil
        }
        return annotatedRep.representation(using: .jpeg, properties: [.compressionFactor: 0.82])
    }

    private func drawYoloOverlay(faces: [DetectedFace], imageSize: NSSize) {
        let minDimension = min(imageSize.width, imageSize.height)
        let lineWidth = max(4, minDimension / 100)
        let labelFont = NSFont.boldSystemFont(ofSize: CGFloat(AppConfig.yoloFontSize))
        let labelPaddingX: CGFloat = 32
        let labelPaddingY: CGFloat = 20

        for face in faces {
            let rect = overlayRect(for: face.boundingBox, imageSize: imageSize)
            guard rect.width > 1, rect.height > 1 else { continue }

            NSColor.systemGreen.setStroke()
            let path = NSBezierPath(rect: rect)
            path.lineWidth = lineWidth
            path.stroke()

            let label = face.confidence > 0 && face.confidence < 1.0
                ? String(format: "(face, %.2f)", face.confidence)
                : "(face)"
            let attributes: [NSAttributedString.Key: Any] = [
                .font: labelFont,
                .foregroundColor: NSColor.white,
            ]
            let textSize = label.size(withAttributes: attributes)
            let labelSize = NSSize(
                width: textSize.width + labelPaddingX * 2,
                height: textSize.height + labelPaddingY * 2
            )
            let logMessage = "[VLM YOLO Overlay] configuredFontSize=\(AppConfig.yoloFontSize)pt "
                + "actualPointSize=\(String(format: "%.1f", labelFont.pointSize))pt "
                + "image=\(Int(imageSize.width))x\(Int(imageSize.height)) "
                + "label=\(label) "
                + "textSize=\(Int(textSize.width))x\(Int(textSize.height)) "
                + "labelBox=\(Int(labelSize.width))x\(Int(labelSize.height))"
            AppLog.write(logMessage)
            print(logMessage)
            let labelX = min(max(rect.minX, 0), max(0, imageSize.width - labelSize.width))
            var labelY = rect.maxY + lineWidth
            if labelY + labelSize.height > imageSize.height {
                labelY = max(rect.minY, rect.maxY - labelSize.height - lineWidth)
            }

            let labelRect = NSRect(origin: NSPoint(x: labelX, y: labelY), size: labelSize)
            NSColor.black.withAlphaComponent(0.72).setFill()
            NSBezierPath(roundedRect: labelRect, xRadius: 5, yRadius: 5).fill()

            label.draw(
                in: labelRect.insetBy(dx: labelPaddingX, dy: labelPaddingY),
                withAttributes: attributes
            )
        }
    }

    private func overlayRect(for normalizedBox: CGRect, imageSize: NSSize) -> NSRect {
        let x1 = clamp(normalizedBox.minX) * imageSize.width
        let y1 = clamp(normalizedBox.minY) * imageSize.height
        let x2 = clamp(normalizedBox.maxX) * imageSize.width
        let y2 = clamp(normalizedBox.maxY) * imageSize.height

        return NSRect(
            x: min(x1, x2),
            y: min(y1, y2),
            width: abs(x2 - x1),
            height: abs(y2 - y1)
        )
    }

    private func clamp(_ value: CGFloat) -> CGFloat {
        min(1, max(0, value))
    }
}
