import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct LaunchView: View {
    @StateObject private var validator = SoupPackageValidator()
    @State private var showCreatorMessage = false
    @State private var scanOffset: CGFloat = 0

    var body: some View {
        HStack(spacing: 0) {
            sidebar
                .frame(width: 244)

            Divider()

            mainWorkspace
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .alert("Creator flow", isPresented: $showCreatorMessage) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Create a SOUP Package is a mocked creator entry point for this milestone.")
        }
    }

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(Color.accentColor)
                    Image(systemName: "viewfinder")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(.white)
                }
                .frame(width: 32, height: 32)

                VStack(alignment: .leading, spacing: 2) {
                    Text("SoPilot")
                        .font(.system(size: 17, weight: .semibold))
                    Text("Local Edition")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.top, 18)
            .padding(.horizontal, 18)

            VStack(spacing: 6) {
                SidebarItem(icon: "sparkles", title: "Launch", selected: true)
                SidebarItem(icon: "video.badge.checkmark", title: "Monitor", selected: false)
                SidebarItem(icon: "shippingbox", title: "Packages", selected: false)
                SidebarItem(icon: "wand.and.stars", title: "Creator", selected: false)
                SidebarItem(icon: "gearshape", title: "Settings", selected: false)
            }
            .padding(.horizontal, 10)

            Spacer()

            VStack(alignment: .leading, spacing: 12) {
                Text("Runtime")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)

                RuntimeLine(title: "SOUP Engine", status: "Ready", tint: .green)
                RuntimeLine(title: "YOLO MLX", status: "Local", tint: .blue)
                RuntimeLine(title: "Raw Video", status: "Private", tint: .green)
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.regularMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .padding(.horizontal, 14)

            Text("Version \(AppConfig.version)")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .padding(.horizontal, 18)
                .padding(.bottom, 14)
        }
        .background(.ultraThinMaterial)
    }

    private var mainWorkspace: some View {
        VStack(spacing: 0) {
            topToolbar
            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    heroPanel

                    HStack(alignment: .top, spacing: 18) {
                        VStack(spacing: 18) {
                            definitionsGrid
                            privacyStrip
                        }
                        .frame(minWidth: 300, idealWidth: 380, maxWidth: 440)

                        videoPanel
                    }

                    launchFooter
                }
                .padding(24)
                .frame(maxWidth: 1220, alignment: .leading)
            }
            .background(Color(nsColor: .controlBackgroundColor))
        }
    }

    private var topToolbar: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Launch")
                    .font(.system(size: 15, weight: .semibold))
                Text("Local SOP Video Checker")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }

            Spacer()

            HStack(spacing: 8) {
                Circle()
                    .fill(.green)
                    .frame(width: 8, height: 8)
                Text("All Local Systems Operational")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }

            Button {
                openSoupPackage()
            } label: {
                Label("Use Package", systemImage: "shippingbox.fill")
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(.horizontal, 20)
        .frame(height: 56)
        .background(.bar)
    }

    private var heroPanel: some View {
        HStack(alignment: .center, spacing: 24) {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("SoPilot")
                        .font(.system(size: 46, weight: .semibold))
                        .foregroundStyle(Color.primary)

                    Text("Local SOP Video Checker")
                        .font(.system(size: 24, weight: .regular))
                        .foregroundStyle(.secondary)
                }

                Text("Run a local SOUP package, keep workflow video private, and let deterministic rules produce the final SOP decision.")
                    .font(.system(size: 15))
                    .foregroundStyle(.secondary)
                    .lineSpacing(3)
                    .frame(maxWidth: 560, alignment: .leading)

                actionButtons
                validationStatus
            }

            Spacer(minLength: 20)

            VStack(alignment: .leading, spacing: 12) {
                MetricTile(icon: "lock.fill", title: "Local-first", value: "No cloud path")
                MetricTile(icon: "checkmark.seal.fill", title: "Decision engine", value: "SOUP rules")
                MetricTile(icon: "cpu", title: "Inference", value: "Edge ready")
            }
            .frame(width: 240)
        }
        .padding(28)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }

    private var definitionsGrid: some View {
        VStack(spacing: 12) {
            DefinitionCard(
                title: "SOP",
                description: "Standard Operating Procedure: step-by-step instructions for complex routine operations."
            )

            DefinitionCard(
                title: "SOUP",
                description: "SOP Unified Package: a local-first bundle of models, rules, and verification logic."
            )
        }
    }

    private var actionButtons: some View {
        HStack(spacing: 10) {
            Button {
                openSoupPackage()
            } label: {
                Label("Use a SOUP Package", systemImage: "shippingbox.fill")
            }
            .buttonStyle(PrimaryLaunchButtonStyle())

            Button {
                showCreatorMessage = true
            } label: {
                Label("Create a SOUP Package", systemImage: "wand.and.stars")
            }
            .buttonStyle(SecondaryLaunchButtonStyle())
        }
    }

    @ViewBuilder
    private var validationStatus: some View {
        switch validator.result.status {
        case .idle:
            EmptyView()
        case .validating:
            StatusPill(icon: "hourglass", tint: .blue, text: "Validating SOUP package...")
        case .valid(let message):
            StatusPill(icon: "checkmark.seal.fill", tint: .green, text: compact(message))
        case .invalid(let message):
            StatusPill(icon: "xmark.octagon.fill", tint: .red, text: compact(message))
        case .backendUnavailable(let message):
            StatusPill(icon: "exclamationmark.triangle.fill", tint: .orange, text: compact(message))
        }
    }

    private var privacyStrip: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Privacy Guarantees")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(.secondary)
            PrivacyFeature(icon: "lock.fill", text: "SOP rules stay local")
            PrivacyFeature(icon: "memorychip.fill", text: "YOLO model stays local")
            PrivacyFeature(icon: "video.fill", text: "Raw video stays local")
            PrivacyFeature(icon: "checkmark.shield.fill", text: "Final decision is local")
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }

    private var videoPanel: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text("Live Verification Preview")
                        .font(.system(size: 17, weight: .semibold))
                    Text("Mock edge-inference surface for the BP Monitor demo")
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                }

                Spacer()

                HStack(spacing: 6) {
                    Circle()
                        .fill(Color(red: 0.16, green: 0.59, blue: 1.0))
                        .frame(width: 8, height: 8)
                    Text("Ready")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color(red: 0.0, green: 0.31, blue: 0.62).opacity(0.10))
                .clipShape(Capsule())
            }

            videoMock
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }

    private var videoMock: some View {
        GeometryReader { geometry in
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(Color(red: 0.11, green: 0.11, blue: 0.12))

                IndustrialGrid()
                    .opacity(0.45)

                VStack(spacing: 10) {
                    Image(systemName: "center.viewfinder")
                        .font(.system(size: 42, weight: .regular))
                        .foregroundStyle(.white)
                        .padding(18)
                        .background(.white.opacity(0.08))
                        .clipShape(Circle())
                        .overlay(Circle().stroke(.white.opacity(0.20), lineWidth: 1))

                    Text("BP Monitor Demo Surface")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.white.opacity(0.86))
                }

                Rectangle()
                    .fill(
                        LinearGradient(
                            colors: [.clear, Color(red: 0.16, green: 0.59, blue: 1.0), .clear],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .frame(height: 2)
                    .shadow(color: Color(red: 0.16, green: 0.59, blue: 1.0), radius: 8)
                    .offset(y: scanOffset)
                    .onAppear {
                        scanOffset = -geometry.size.height / 2
                        withAnimation(.linear(duration: 3.0).repeatForever(autoreverses: false)) {
                            scanOffset = geometry.size.height / 2
                        }
                    }

                VStack {
                    Spacer()
                    HStack {
                        HStack(spacing: 7) {
                            Text("Edge Inference Status:")
                            Circle()
                                .fill(Color(red: 0.16, green: 0.59, blue: 1.0))
                                .frame(width: 7, height: 7)
                            Text("Ready")
                                .fontWeight(.bold)
                                .foregroundStyle(Color(red: 0.16, green: 0.59, blue: 1.0))
                        }
                        .font(.system(size: 12))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 8)
                        .background(.black.opacity(0.42))
                        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))

                        Spacer()
                    }
                    .padding(14)
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .aspectRatio(16.0 / 10.0, contentMode: .fit)
        .shadow(color: .black.opacity(0.12), radius: 10, x: 0, y: 4)
    }

    private var launchFooter: some View {
        HStack(spacing: 18) {
            HStack(spacing: 14) {
                Text("© 2024 SoPilot Inc.")
                Text("Privacy Policy")
                Text("System Requirements")
            }
            .font(.system(size: 11))
            .foregroundStyle(Color(red: 0.48, green: 0.48, blue: 0.48))
            .lineLimit(1)
            .minimumScaleFactor(0.75)

            Spacer()

            HStack(spacing: 8) {
                Circle()
                    .fill(.green)
                    .frame(width: 8, height: 8)
                Text("All Local Systems Operational")
                    .font(.system(size: 12))
                    .foregroundStyle(Color(red: 0.25, green: 0.28, blue: 0.33))
            }
        }
        .padding(.horizontal, 4)
        .padding(.bottom, 4)
    }

    private func openSoupPackage() {
        let panel = NSOpenPanel()
        panel.title = "Choose a SOUP package"
        panel.prompt = "Use Package"
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "soup.json"
        let soupDelegate = SoupOpenPanelDelegate()
        panel.delegate = soupDelegate

        if panel.runModal() == .OK, let url = panel.url {
            validator.validate(url: url)
        }
    }

    private func compact(_ message: String) -> String {
        let cleaned = message.replacingOccurrences(of: "\n", with: " ")
        guard cleaned.count > 96 else { return cleaned }
        return String(cleaned.prefix(93)) + "..."
    }
}

private final class SoupOpenPanelDelegate: NSObject, NSOpenSavePanelDelegate {
    func panel(_ sender: Any, shouldEnable url: URL) -> Bool {
        var isDirectory: ObjCBool = false
        if FileManager.default.fileExists(atPath: url.path, isDirectory: &isDirectory),
           isDirectory.boolValue {
            return true
        }
        return url.lastPathComponent.hasSuffix(".soup.json")
    }

    func panel(_ sender: Any, validate url: URL) throws {
        guard url.lastPathComponent.hasSuffix(".soup.json") else {
            throw NSError(
                domain: "SoPilotMacApp.SoupOpenPanel",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Choose a file ending in .soup.json"]
            )
        }
    }
}

private struct SidebarItem: View {
    let icon: String
    let title: String
    let selected: Bool

    var body: some View {
        HStack(spacing: 9) {
            Image(systemName: icon)
                .font(.system(size: 14, weight: .medium))
                .frame(width: 20)
            Text(title)
                .font(.system(size: 13, weight: selected ? .semibold : .regular))
            Spacer()
        }
        .foregroundStyle(selected ? Color.primary : Color.secondary)
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(selected ? Color.accentColor.opacity(0.14) : Color.clear)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

private struct RuntimeLine: View {
    let title: String
    let status: String
    let tint: Color

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(tint)
                .frame(width: 7, height: 7)
            Text(title)
                .font(.system(size: 12))
            Spacer()
            Text(status)
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.secondary)
        }
    }
}

private struct MetricTile: View {
    let icon: String
    let title: String
    let value: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(Color.accentColor)
                .frame(width: 28, height: 28)
                .background(Color.accentColor.opacity(0.10))
                .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 12, weight: .semibold))
                Text(value)
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
        .padding(12)
        .background(Color(nsColor: .controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

private struct DefinitionCard: View {
    let title: String
    let description: String

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            Text(title)
                .font(.system(size: 20, weight: .bold))
                .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))

            Text(description)
                .font(.system(size: 13))
                .lineSpacing(2)
                .foregroundStyle(Color(red: 0.25, green: 0.28, blue: 0.33))
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }
}

private struct PrivacyFeature: View {
    let icon: String
    let text: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
                .frame(width: 20)

            Text(text)
                .font(.system(size: 13, weight: .bold))
                .foregroundStyle(Color(red: 0.10, green: 0.10, blue: 0.11))
        }
    }
}

private struct StatusPill: View {
    let icon: String
    let tint: Color
    let text: String

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundStyle(tint)
            Text(text)
                .lineLimit(2)
                .minimumScaleFactor(0.85)
            Spacer(minLength: 0)
        }
        .font(.system(size: 12, weight: .semibold))
        .foregroundStyle(Color(red: 0.13, green: 0.14, blue: 0.15))
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(tint.opacity(0.12))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

private struct IndustrialGrid: View {
    var body: some View {
        Canvas { context, size in
            let lineColor = Color.white.opacity(0.18)
            var path = Path()
            let spacing: CGFloat = 28

            stride(from: CGFloat(0), through: size.width, by: spacing).forEach { x in
                path.move(to: CGPoint(x: x, y: 0))
                path.addLine(to: CGPoint(x: x, y: size.height))
            }

            stride(from: CGFloat(0), through: size.height, by: spacing).forEach { y in
                path.move(to: CGPoint(x: 0, y: y))
                path.addLine(to: CGPoint(x: size.width, y: y))
            }

            context.stroke(path, with: .color(lineColor), lineWidth: 1)

            let monitorRect = CGRect(x: size.width * 0.17, y: size.height * 0.34, width: size.width * 0.30, height: size.height * 0.24)
            let cuffRect = CGRect(x: size.width * 0.58, y: size.height * 0.28, width: size.width * 0.24, height: size.height * 0.34)

            context.stroke(Path(roundedRect: monitorRect, cornerRadius: 8), with: .color(.green.opacity(0.88)), lineWidth: 2)
            context.stroke(Path(roundedRect: cuffRect, cornerRadius: 12), with: .color(.cyan.opacity(0.88)), lineWidth: 2)
        }
    }
}

private struct PrimaryLaunchButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .semibold))
            .foregroundStyle(.white)
            .padding(.vertical, 9)
            .padding(.horizontal, 16)
            .background(Color(red: 0.0, green: 0.31, blue: 0.62).opacity(configuration.isPressed ? 0.82 : 1.0))
            .clipShape(Capsule())
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
    }
}

private struct SecondaryLaunchButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .semibold))
            .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
            .padding(.vertical, 9)
            .padding(.horizontal, 16)
            .background(Color(nsColor: .windowBackgroundColor).opacity(configuration.isPressed ? 0.72 : 0.96))
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.black.opacity(0.08), lineWidth: 1))
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
    }
}
