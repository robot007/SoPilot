import AppKit
import SwiftUI
import UniformTypeIdentifiers

private enum AppPage: Equatable {
    case launch
    case packages
    case pa2
    case pa3

    var title: String {
        switch self {
        case .launch: "Launch"
        case .packages: "Packages"
        case .pa2: "Creator"
        case .pa3: "Upload"
        }
    }

    var subtitle: String {
        switch self {
        case .launch: "Local SOP Video Checker"
        case .packages: "Choose a SOUP package"
        case .pa2: "Create BP Monitor package"
        case .pa3: "Upload source media"
        }
    }

    var mockupTitle: String {
        switch self {
        case .launch: "Launch"
        case .packages: "PB2 - SOUP Package Store"
        case .pa2: "PA2 - Create BP Monitor"
        case .pa3: "PA3 - Upload"
        }
    }

    var mockupHint: String {
        switch self {
        case .launch:
            "Local SOP Video Checker"
        case .packages:
            "Choose a verified SOUP package for local SOP validation."
        case .pa2:
            "Any click on this mockup advances to PA3."
        case .pa3:
            "Upload screen mockup."
        }
    }

    var imageFileName: String {
        switch self {
        case .launch: ""
        case .packages: "PB2-soup-store.png"
        case .pa2: "PA2-createBP.png"
        case .pa3: "PA3-upload.png"
        }
    }

    var isCreatorFlow: Bool {
        self == .pa2 || self == .pa3
    }
}

struct LaunchView: View {
    @StateObject private var validator = SoupPackageValidator()
    @State private var scanOffset: CGFloat = 0
    @State private var currentPage: AppPage = .launch

    var body: some View {
        HStack(spacing: 0) {
            sidebar
                .frame(width: 244)

            Divider()

            mainWorkspace
        }
        .background(Color(nsColor: .windowBackgroundColor))
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
                SidebarItem(icon: "sparkles", title: "Launch", selected: currentPage == .launch) {
                    navigate(to: .launch)
                }
                SidebarItem(icon: "video.badge.checkmark", title: "Monitor", selected: false) {
                    advancePA2IfNeeded()
                }
                SidebarItem(icon: "shippingbox", title: "Packages", selected: currentPage == .packages) {
                    navigate(to: .packages)
                }
                SidebarItem(icon: "wand.and.stars", title: "Creator", selected: currentPage.isCreatorFlow) {
                    navigate(to: .pa2)
                }
                SidebarItem(icon: "gearshape", title: "Settings", selected: false) {
                    advancePA2IfNeeded()
                }
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

            switch currentPage {
            case .launch:
                launchWorkspace
            case .packages:
                packageStoreWorkspace
            case .pa2:
                mockupWorkspace(page: .pa2)
            case .pa3:
                pa3UploadWorkspace
            }
        }
    }

    private var topToolbar: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(currentPage.title)
                    .font(.system(size: 15, weight: .semibold))
                Text(currentPage.subtitle)
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
                if currentPage == .pa2 {
                    currentPage = .pa3
                } else if currentPage == .packages {
                    openSoupPackage()
                } else if currentPage.isCreatorFlow {
                    currentPage = .launch
                } else {
                    currentPage = .packages
                }
            } label: {
                Label(
                    topToolbarActionTitle,
                    systemImage: topToolbarActionIcon
                )
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(.horizontal, 20)
        .frame(height: 56)
        .background(.bar)
    }

    private var topToolbarActionTitle: String {
        if currentPage.isCreatorFlow { return "Back to Launch" }
        if currentPage == .packages { return "Use Local File" }
        return "Choose a SOUP Package"
    }

    private var topToolbarActionIcon: String {
        if currentPage.isCreatorFlow { return "chevron.left" }
        if currentPage == .packages { return "doc.badge.plus" }
        return "shippingbox.fill"
    }

    private var launchWorkspace: some View {
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

    private func mockupWorkspace(page: AppPage) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(page.mockupTitle)
                            .font(.system(size: 18, weight: .semibold))
                        Text(page.mockupHint)
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                }

                MockupImageView(fileName: page.imageFileName)
                    .frame(maxWidth: .infinity)
                    .contentShape(Rectangle())
            }
            .padding(24)
            .frame(maxWidth: 980, alignment: .leading)
            .contentShape(Rectangle())
            .onTapGesture {
                if page == .pa2 {
                    currentPage = .pa3
                }
            }
        }
        .background(Color(nsColor: .controlBackgroundColor))
    }

    private var packageStoreWorkspace: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 26) {
                HStack(spacing: 10) {
                    Button {
                        currentPage = .launch
                    } label: {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 13, weight: .semibold))
                    }
                    .buttonStyle(.plain)

                    Text("SoPilot")
                        .font(.system(size: 24, weight: .bold, design: .serif))

                    Spacer()

                    Image(systemName: "person.crop.circle.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(Color(red: 0.38, green: 0.50, blue: 0.56))
                }

                HStack(spacing: 10) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    Text("Search SOUP packages...")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                    Spacer()
                }
                .padding(.horizontal, 16)
                .frame(maxWidth: 760, minHeight: 44)
                .background(Color(nsColor: .windowBackgroundColor))
                .clipShape(Capsule())
                .overlay(Capsule().stroke(Color.black.opacity(0.08), lineWidth: 1))
                .padding(.leading, 104)

                HStack(spacing: 10) {
                    CategoryChip(title: "All Packages", selected: true)
                    CategoryChip(title: "Healthcare", selected: false)
                    CategoryChip(title: "HVAC", selected: false)
                    CategoryChip(title: "Factory", selected: false)
                    CategoryChip(title: "Safety", selected: false)
                    CategoryChip(title: "Lab", selected: false)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Featured Packages")
                        .font(.system(size: 28, weight: .bold, design: .serif))
                    Text("Verified Standard Operating Procedures for immediate deployment.")
                        .font(.system(size: 12))
                        .foregroundStyle(Color(red: 0.36, green: 0.36, blue: 0.36))
                }
                .padding(.top, 28)

                LazyVGrid(
                    columns: [GridItem(.adaptive(minimum: 220, maximum: 280), spacing: 18)],
                    alignment: .leading,
                    spacing: 18
                ) {
                    PackageStoreCard(
                        title: "Blood Pressure Monitor SOP Checker",
                        description: "Automated visual verification for clinical blood pressure measurement protocols. Ensures cuff placement and patient posture compliance.",
                        badge: "Verified",
                        price: "FREE",
                        meta: "All Local",
                        installs: "2.4k installs",
                        artwork: .photo("cuff-ipad-table.png"),
                        actionIcon: "plus"
                    )

                    PackageStoreCard(
                        title: "HVAC Filter Maintenance SOP",
                        description: "Step-by-step vision guidance for industrial air handling units. Includes particle sensor calibration and seal integrity checks.",
                        badge: "Enterprise",
                        price: "$49.00",
                        meta: "Cloud Hybrid",
                        installs: "1.1k installs",
                        artwork: .industrial,
                        actionIcon: "cart"
                    )

                    PackageStoreCard(
                        title: "Lab Pipette Sterilization Routine",
                        description: "Vision-based audit for GLP-compliant sterilization. Tracks contact time, temperature readings, and equipment positioning.",
                        badge: "Advanced",
                        price: "FREE",
                        meta: "All Local",
                        installs: "840 installs",
                        artwork: .lab,
                        actionIcon: "plus"
                    )
                }

                PackagePromoBanner()
                    .padding(.top, 38)
            }
            .padding(24)
            .frame(maxWidth: 1120, alignment: .leading)
        }
        .background(Color(red: 0.99, green: 0.97, blue: 0.985))
    }

    private var pa3UploadWorkspace: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 26) {
                VStack(alignment: .leading, spacing: 12) {
                    Text("SOP Audit Engine")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(red: 0.0, green: 0.31, blue: 0.62).opacity(0.10))
                        .clipShape(Capsule())

                    Text("Mock: upload videos for correct processes")
                        .font(.system(size: 34, weight: .semibold))
                        .foregroundStyle(.primary)
                        .frame(maxWidth: 620, alignment: .leading)

                    Text("High-fidelity YOLO-based analysis of the Blood Pressure Monitor Standard Operating Procedure. Every frame is verified against the digital twin protocol.")
                        .font(.system(size: 14))
                        .foregroundStyle(.secondary)
                        .lineSpacing(3)
                        .frame(maxWidth: 680, alignment: .leading)
                }

                HStack(alignment: .top, spacing: 18) {
                    pa3ProcessCard

                    VStack(spacing: 18) {
                        verificationStatsCard
                        systemLogCard
                    }
                    .frame(width: 300)
                }

                workflowStepsSection
            }
            .padding(24)
            .frame(maxWidth: 1120, alignment: .leading)
        }
        .background(Color(nsColor: .controlBackgroundColor))
    }

    private var pa3ProcessCard: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack {
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .fill(Color(red: 0.13, green: 0.13, blue: 0.14))

                IndustrialGrid()
                    .opacity(0.30)

                VStack(spacing: 10) {
                    Image(systemName: "play.fill")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundStyle(.white)
                        .frame(width: 58, height: 58)
                        .background(.white.opacity(0.22))
                        .clipShape(Circle())

                    Text("BP Monitor Training Clip")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.white.opacity(0.90))
                }

                VStack {
                    Spacer()
                    HStack(spacing: 7) {
                        Circle()
                            .fill(.green)
                            .frame(width: 8, height: 8)
                        Text("Live YOLO Inference: Step 1 Active")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundStyle(.white)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(14)
                }
            }
            .aspectRatio(16 / 9, contentMode: .fit)

            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 7) {
                    Text("Process Overview")
                        .font(.system(size: 21, weight: .semibold))
                    Text("Video ID: SOP-BP-0042 · Duration: 02:14")
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button("Approve SOP") {}
                    .buttonStyle(PrimaryLaunchButtonStyle())
            }
            .padding(18)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }

    private var verificationStatsCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Verification Stats")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.secondary)
                .textCase(.uppercase)

            HStack {
                Text("Compliance Score")
                    .font(.system(size: 12))
                Spacer()
                Text("98.4%")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
            }

            ProgressView(value: 0.984)
                .tint(Color(red: 0.0, green: 0.31, blue: 0.62))

            HStack(spacing: 10) {
                StatBox(value: "5/5", label: "Steps Validated")
                StatBox(value: "0.4s", label: "Avg. Latency")
            }

            Spacer(minLength: 40)
        }
        .padding(18)
        .frame(maxWidth: .infinity, minHeight: 210, alignment: .topLeading)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }

    private var systemLogCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("System Log")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.white.opacity(0.66))
                .textCase(.uppercase)

            LogLine(time: "14:22:01", message: "Model 'Med-Seg v2' initialized.")
            LogLine(time: "14:22:04", message: "Detected: Cuff Placement. Confidence 0.93")
            LogLine(time: "14:22:15", message: "Action Verified: Arm Position correct.")
        }
        .padding(18)
        .frame(maxWidth: .infinity, minHeight: 130, alignment: .topLeading)
        .background(Color(red: 0.16, green: 0.16, blue: 0.17))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private var workflowStepsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Review Workflow Steps")
                    .font(.system(size: 22, weight: .semibold))
                Spacer()
                HStack(spacing: 8) {
                    Image(systemName: "chevron.left")
                    Image(systemName: "chevron.right")
                }
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.secondary)
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 14), count: 4), spacing: 14) {
                WorkflowStepCard(
                    number: "STEP 1",
                    icon: "person.crop.rectangle",
                    title: "Placement Accuracy",
                    description: "Analyzing initial cuff orientation on the upper arm segment."
                )
                WorkflowStepCard(
                    number: "STEP 2",
                    icon: "bandage",
                    title: "Securing Tension",
                    description: "Detection of velcro engagement and surface tension levels."
                )
                WorkflowStepCard(
                    number: "STEP 3",
                    icon: "power",
                    title: "Device Activation",
                    description: "Confirmation of power trigger and LCD calibration glow."
                )
                WorkflowStepCard(
                    number: "STEP 4",
                    icon: "wave.3.right",
                    title: "Data Transmission",
                    description: "Verifying BLE handshake and result logging in cloud storage."
                )
            }
        }
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
                currentPage = .packages
            } label: {
                Label("Choose a SOUP Package", systemImage: "shippingbox.fill")
            }
            .buttonStyle(PrimaryLaunchButtonStyle())

            Button {
                currentPage = .pa3
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

    private func navigate(to page: AppPage) {
        if currentPage == .pa2 {
            currentPage = .pa3
        } else {
            currentPage = page
        }
    }

    private func advancePA2IfNeeded() {
        if currentPage == .pa2 {
            currentPage = .pa3
        }
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

private struct MockupImageView: View {
    let fileName: String

    var body: some View {
        if let image = findImage(named: fileName) {
            Image(nsImage: image)
                .resizable()
                .scaledToFit()
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.black.opacity(0.08), lineWidth: 1)
                )
        } else {
            VStack(spacing: 10) {
                Image(systemName: "photo.badge.exclamationmark")
                    .font(.system(size: 38))
                    .foregroundStyle(.secondary)
                Text("Missing mockup image")
                    .font(.system(size: 15, weight: .semibold))
                Text(fileName)
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, minHeight: 320)
            .background(Color(nsColor: .windowBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(Color.black.opacity(0.08), lineWidth: 1)
            )
        }
    }

    private func findImage(named name: String) -> NSImage? {
        ProjectImageLoader.image(named: name, in: "AppPages")
    }
}

private enum PackageArtworkKind {
    case photo(String)
    case industrial
    case lab
}

private struct CategoryChip: View {
    let title: String
    let selected: Bool

    var body: some View {
        Text(title)
            .font(.system(size: 11, weight: selected ? .semibold : .regular))
            .foregroundStyle(selected ? .white : Color(red: 0.42, green: 0.42, blue: 0.44))
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(selected ? Color(red: 0.0, green: 0.31, blue: 0.62) : Color(red: 0.92, green: 0.91, blue: 0.925))
            .clipShape(Capsule())
    }
}

private struct PackageStoreCard: View {
    let title: String
    let description: String
    let badge: String
    let price: String
    let meta: String
    let installs: String
    let artwork: PackageArtworkKind
    let actionIcon: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack(alignment: .topLeading) {
                PackageArtwork(kind: artwork)

                Label(badge, systemImage: badge == "Advanced" ? "flask" : "checkmark.seal")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 5)
                    .background(.white.opacity(0.88))
                    .clipShape(Capsule())
                    .padding(10)
            }
            .frame(height: 150)
            .clipped()

            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .top, spacing: 8) {
                    Text(title)
                        .font(.system(size: 14, weight: .bold, design: .serif))
                        .foregroundStyle(Color(red: 0.08, green: 0.08, blue: 0.09))
                        .lineLimit(2)
                        .fixedSize(horizontal: false, vertical: true)

                    Spacer(minLength: 6)

                    Text(price)
                        .font(.system(size: 8, weight: .bold))
                        .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(Color(red: 0.93, green: 0.93, blue: 0.94))
                        .clipShape(Capsule())
                }

                Text(description)
                    .font(.system(size: 11))
                    .foregroundStyle(Color(red: 0.34, green: 0.34, blue: 0.36))
                    .lineSpacing(2)
                    .lineLimit(4)
                    .fixedSize(horizontal: false, vertical: true)

                Spacer(minLength: 8)

                Divider()

                HStack(spacing: 10) {
                    Image(systemName: meta == "All Local" ? "globe" : "cloud")
                    Text(meta)
                    Image(systemName: "arrow.down.to.line.compact")
                    Text(installs)
                    Spacer()

                    Button {} label: {
                        Image(systemName: actionIcon)
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(.white)
                            .frame(width: 32, height: 32)
                            .background(Color(red: 0.0, green: 0.31, blue: 0.62))
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }
                .font(.system(size: 10))
                .foregroundStyle(Color(red: 0.46, green: 0.46, blue: 0.48))
            }
            .padding(18)
            .frame(minHeight: 188, alignment: .topLeading)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }
}

private struct PackageArtwork: View {
    let kind: PackageArtworkKind

    var body: some View {
        switch kind {
        case .photo(let name):
            if let image = ProjectImageLoader.image(named: name, in: "img") {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFill()
                    .overlay(.black.opacity(0.14))
            } else {
                industrialFallback
            }
        case .industrial:
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.08, green: 0.17, blue: 0.19),
                        Color(red: 0.22, green: 0.31, blue: 0.32)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                IndustrialGrid()
                    .opacity(0.35)
                Image(systemName: "fanblades.fill")
                    .font(.system(size: 46, weight: .light))
                    .foregroundStyle(.white.opacity(0.45))
            }
        case .lab:
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.0, green: 0.13, blue: 0.16),
                        Color(red: 0.0, green: 0.45, blue: 0.55)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                LabGlasswareDrawing()
                    .padding(14)
            }
        }
    }

    private var industrialFallback: some View {
        ZStack {
            Color(red: 0.10, green: 0.16, blue: 0.18)
            IndustrialGrid()
                .opacity(0.35)
        }
    }
}

private struct LabGlasswareDrawing: View {
    var body: some View {
        GeometryReader { geometry in
            Canvas { context, size in
                let cyan = Color.cyan.opacity(0.78)
                let dim = Color.cyan.opacity(0.28)

                var bench = Path()
                bench.move(to: CGPoint(x: 0, y: size.height * 0.78))
                bench.addLine(to: CGPoint(x: size.width, y: size.height * 0.78))
                context.stroke(bench, with: .color(dim), lineWidth: 2)

                for index in 0..<5 {
                    let x = size.width * (0.18 + CGFloat(index) * 0.16)
                    let tube = CGRect(x: x, y: size.height * 0.28, width: size.width * 0.06, height: size.height * 0.48)
                    context.stroke(Path(roundedRect: tube, cornerRadius: 7), with: .color(cyan), lineWidth: 2)

                    var liquid = Path()
                    liquid.move(to: CGPoint(x: tube.minX + 3, y: tube.maxY - 20 - CGFloat(index % 3) * 7))
                    liquid.addLine(to: CGPoint(x: tube.maxX - 3, y: tube.maxY - 20 - CGFloat(index % 3) * 7))
                    context.stroke(liquid, with: .color(cyan), lineWidth: 2)
                }

                let flask = CGRect(x: size.width * 0.60, y: size.height * 0.20, width: size.width * 0.22, height: size.height * 0.50)
                context.stroke(Path(roundedRect: flask, cornerRadius: 8), with: .color(cyan), lineWidth: 2)

                var neck = Path()
                neck.move(to: CGPoint(x: flask.midX, y: size.height * 0.08))
                neck.addLine(to: CGPoint(x: flask.midX, y: flask.minY))
                context.stroke(neck, with: .color(cyan), lineWidth: 2)
            }
            .frame(width: geometry.size.width, height: geometry.size.height)
        }
    }
}

private struct PackagePromoBanner: View {
    var body: some View {
        HStack(spacing: 26) {
            VStack(alignment: .leading, spacing: 14) {
                Text("NEW ARRIVAL")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundStyle(Color(red: 0.0, green: 0.62, blue: 1.0))

                Text("Complete PPE detection and exclusionary zone monitoring updated for YOLOx models.")
                    .font(.system(size: 19, weight: .regular, design: .serif))
                    .foregroundStyle(.white.opacity(0.90))
                    .lineSpacing(4)
                    .frame(maxWidth: 360, alignment: .leading)

                Button("Explore Package") {}
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(.black)
                    .padding(.horizontal, 26)
                    .padding(.vertical, 11)
                    .background(.white)
                    .clipShape(Capsule())
                    .buttonStyle(.plain)
            }

            Spacer(minLength: 20)

            ZStack(alignment: .bottomLeading) {
                LinearGradient(
                    colors: [
                        Color(red: 0.07, green: 0.18, blue: 0.19),
                        Color(red: 0.18, green: 0.27, blue: 0.25)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )

                IndustrialGrid()
                    .opacity(0.20)

                Image(systemName: "figure.stand")
                    .font(.system(size: 90, weight: .light))
                    .foregroundStyle(Color.yellow.opacity(0.85))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                Label("LIVE ANALYSIS", systemImage: "dot.radiowaves.left.and.right")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 9)
                    .padding(.vertical, 6)
                    .background(Color(red: 0.0, green: 0.31, blue: 0.62).opacity(0.90))
                    .clipShape(Capsule())
                    .padding(16)
            }
            .frame(width: 430, height: 220)
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        }
        .padding(30)
        .frame(maxWidth: .infinity, minHeight: 260, alignment: .leading)
        .background(.black)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

private enum ProjectImageLoader {
    static func image(named name: String, in folder: String) -> NSImage? {
        let fileManager = FileManager.default
        let root = PythonRuntimeLocator.projectRoot()
        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath)
        let candidates = [
            Bundle.main.resourceURL?.appendingPathComponent("\(folder)/\(name)"),
            Bundle.main.resourceURL?.appendingPathComponent(folder == "AppPages" ? "AppPages/\(name)" : "img/\(name)"),
            root.appendingPathComponent("doc/\(folder)/\(name)"),
            cwd.appendingPathComponent("doc/\(folder)/\(name)").standardizedFileURL,
            cwd.appendingPathComponent("../doc/\(folder)/\(name)").standardizedFileURL,
        ].compactMap { $0 }

        return candidates
            .first { fileManager.fileExists(atPath: $0.path) }
            .flatMap { NSImage(contentsOf: $0) }
    }
}

private struct SidebarItem: View {
    let icon: String
    let title: String
    let selected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 9) {
                Image(systemName: icon)
                    .font(.system(size: 14, weight: .medium))
                    .frame(width: 20)
                Text(title)
                    .font(.system(size: 13, weight: selected ? .semibold : .regular))
                Spacer()
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
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

private struct StatBox: View {
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
            Text(label)
                .font(.system(size: 10))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 11)
        .background(Color(nsColor: .controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(Color.black.opacity(0.06), lineWidth: 1)
        )
    }
}

private struct LogLine: View {
    let time: String
    let message: String

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text(time)
                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                .foregroundStyle(Color(red: 0.16, green: 0.59, blue: 1.0))
            Text(message)
                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                .foregroundStyle(.white)
                .lineLimit(2)
        }
    }
}

private struct WorkflowStepCard: View {
    let number: String
    let icon: String
    let title: String
    let description: String

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            ZStack(alignment: .topLeading) {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [
                                Color(red: 0.88, green: 0.89, blue: 0.86),
                                Color(red: 0.72, green: 0.76, blue: 0.70)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )

                Image(systemName: icon)
                    .font(.system(size: 34, weight: .regular))
                    .foregroundStyle(.white.opacity(0.86))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                Text(number)
                    .font(.system(size: 8, weight: .bold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 4)
                    .background(.black.opacity(0.35))
                    .clipShape(Capsule())
                    .padding(8)
            }
            .aspectRatio(1.36, contentMode: .fit)

            VStack(alignment: .leading, spacing: 5) {
                Text(title)
                    .font(.system(size: 12, weight: .semibold))
                    .lineLimit(1)
                Text(description)
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack(spacing: 5) {
                Image(systemName: "checkmark.circle")
                Text("Passed")
            }
            .font(.system(size: 10, weight: .semibold))
            .foregroundStyle(Color(red: 0.0, green: 0.31, blue: 0.62))
        }
        .padding(10)
        .background(Color(nsColor: .windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
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
