import SwiftUI

struct ContentView: View {
    @EnvironmentObject var cameraManager: CameraManager
    @StateObject private var faceDetector = FaceDetector()
    
    var body: some View {
        Group {
            switch cameraManager.authorizationStatus {
            case .notDetermined:
                ProgressView("Requesting camera access...")
                    .scaleEffect(1.5)
            case .denied:
                permissionDeniedView
            case .authorized:
                if let error = cameraManager.cameraError {
                    cameraErrorView(error)
                } else {
                    cameraView
                }
            }
        }
        .frame(minWidth: 640, minHeight: 480)
        .onAppear {
            cameraManager.setFaceDetector(faceDetector)
        }
    }
    
    private var currentCameraName: String {
        if let id = cameraManager.selectedCameraID,
           let name = cameraManager.availableCameras.first(where: { $0.id == id })?.name {
            return name
        }
        return "No camera"
    }

    private var cameraToolbar: some View {
        HStack(spacing: 12) {
            Menu {
                if cameraManager.availableCameras.isEmpty {
                    Text("No cameras found")
                } else {
                    ForEach(cameraManager.availableCameras) { camera in
                        Button {
                            cameraManager.selectCamera(uniqueID: camera.id)
                        } label: {
                            HStack {
                                Text(cameraManager.selectedCameraID == camera.id ? "✓" : " ")
                                Text(camera.name)
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "camera.fill")
                    Text(currentCameraName)
                        .lineLimit(1)
                    Image(systemName: "chevron.down")
                        .font(.caption2)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
            }
            .menuStyle(.borderlessButton)
            .fixedSize()

            Button {
                cameraManager.refreshCameras()
            } label: {
                Image(systemName: "arrow.clockwise")
            }
            .buttonStyle(.borderless)
            .help("Refresh camera list")

            Spacer()

            HStack(spacing: 4) {
                Circle()
                    .fill(cameraManager.isRunning ? Color.green : Color.secondary)
                    .frame(width: 8, height: 8)
                Text(cameraManager.isRunning ? "Live" : "Stopped")
                    .font(.caption)
                    .foregroundColor(cameraManager.isRunning ? .primary : .secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial)
    }

    private var cameraView: some View {
        VStack(spacing: 0) {
            cameraToolbar
            GeometryReader { geometry in
                ZStack {
                    CameraPreview(session: cameraManager.session)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)

                    ForEach(faceDetector.faces) { face in
                        faceOverlay(face, in: geometry.size)
                    }
                }
            }
        }
    }
    
    private func faceOverlay(_ face: DetectedFace, in viewSize: CGSize) -> some View {
        let box = face.boundingBox
        // Vision uses bottom-left origin; SwiftUI uses top-left
        let x = box.midX * viewSize.width
        let y = (1 - box.midY) * viewSize.height
        let w = box.width * viewSize.width
        let h = box.height * viewSize.height
        
        let confidenceText = face.confidence > 0 && face.confidence < 1.0
            ? String(format: "face %.2f", face.confidence)
            : "face"
        
        return ZStack(alignment: .bottomLeading) {
            Rectangle()
                .stroke(Color.green, lineWidth: 2)
                .frame(width: w, height: h)
            
            Text(confidenceText)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.black.opacity(0.7))
                .cornerRadius(4)
                .offset(y: -h / 2 - 12)
        }
        .position(x: x, y: y)
    }
    
    private var permissionDeniedView: some View {
        VStack(spacing: 20) {
            Image(systemName: "camera.fill")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            
            Text("Camera Access Required")
                .font(.title)
                .fontWeight(.semibold)
            
            Text("FaceBoxDemo needs camera access to detect faces in real time.")
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .frame(maxWidth: 400)
            
            Button("Open System Settings") {
                if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera") {
                    NSWorkspace.shared.open(url)
                }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding(40)
    }
    
    private func cameraErrorView(_ error: CameraError) -> some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 64))
                .foregroundColor(.orange)
            
            Text("Camera Error")
                .font(.title)
                .fontWeight(.semibold)
            
            Text(error.localizedDescription)
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .frame(maxWidth: 400)
            
            Text("Please ensure a camera is connected and not in use by another application.")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 400)
        }
        .padding(40)
    }
}
