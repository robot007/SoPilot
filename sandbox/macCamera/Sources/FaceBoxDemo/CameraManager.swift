import AVFoundation
import Combine

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
    private var faceDetector: FaceDetector?
    
    override init() {
        super.init()
        checkAuthorization()
    }
    
    func setFaceDetector(_ detector: FaceDetector) {
        self.faceDetector = detector
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
}
