import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct LocalVLMPanel: View {
    @ObservedObject var service: VLMModelService
    @ObservedObject var cameraManager: CameraManager
    @State private var deleteCandidate: VLMModel?

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            header
            statusBlock
            modelPicker
            actionButtons
            downloadPathBlock
            progressBlock
            errorBlock
            Divider()
            if let activeModel = service.activeModel {
                VLMChatPanel(
                    service: service,
                    cameraManager: cameraManager,
                    model: activeModel
                )
                    .id(activeModel.id)
            } else {
                localCopy
                Spacer(minLength: 0)
            }
        }
        .padding(16)
        .frame(width: 330)
        .background(Color(nsColor: .controlBackgroundColor))
        .onAppear {
            if service.models.isEmpty {
                service.refresh()
            }
        }
        .alert(item: $deleteCandidate) { model in
            Alert(
                title: Text("Delete \(model.displayName)?"),
                message: Text(deleteMessage(for: model)),
                primaryButton: .destructive(Text("Delete")) {
                    service.selectedModelId = model.id
                    service.deleteSelectedModel()
                },
                secondaryButton: .cancel()
            )
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Local VLM")
                    .font(.headline)
                Text("FaceBoxDemo")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button {
                service.refresh()
            } label: {
                Image(systemName: "arrow.clockwise")
            }
            .buttonStyle(.borderless)
            .disabled(service.isBusy)
            .help("Refresh local VLM status")
        }
    }

    private var statusBlock: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            Text(service.statusLine)
                .font(.subheadline)
                .lineLimit(2)
        }
        .padding(.vertical, 4)
    }

    private var modelPicker: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Model")
                .font(.caption)
                .foregroundStyle(.secondary)

            Picker("Model", selection: selectedModelBinding) {
                ForEach(service.models) { model in
                    Text(pickerTitle(for: model)).tag(model.id)
                }
            }
            .labelsHidden()
            .disabled(service.models.isEmpty || service.isBusy)

            if let selectedModel {
                Text(selectedModel.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var actionButtons: some View {
        HStack(spacing: 8) {
            Button {
                service.downloadSelectedModel()
            } label: {
                Label("Download", systemImage: "arrow.down.circle")
            }
            .disabled(!canDownload)

            Button {
                service.activateSelectedModel()
            } label: {
                Label(selectedModel?.isActive == true ? "Active" : "Use", systemImage: "checkmark.circle")
            }
            .disabled(!canUse)

            Button {
                deleteCandidate = selectedModel
            } label: {
                Label("Delete", systemImage: "trash")
            }
            .disabled(!canDelete)
        }
        .buttonStyle(.bordered)
    }

    @ViewBuilder
    private var downloadPathBlock: some View {
        if let selectedModel {
            VStack(alignment: .leading, spacing: 4) {
                Text("Download path")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Text(selectedModel.localPath)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
                    .truncationMode(.middle)
                    .textSelection(.enabled)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    @ViewBuilder
    private var progressBlock: some View {
        if selectedIsDownloading {
            HStack(spacing: 8) {
                ProgressView()
                    .controlSize(.small)
                Text("Downloading \(selectedModel?.displayName ?? "model")...")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    @ViewBuilder
    private var errorBlock: some View {
        if let error = service.errorMessage, !error.isEmpty {
            Text(error)
                .font(.caption)
                .foregroundStyle(.red)
                .fixedSize(horizontal: false, vertical: true)
        } else if selectedModel?.downloadFailed == true {
            Text("Download failed. You can retry the download.")
                .font(.caption)
                .foregroundStyle(.red)
        }
    }

    private var localCopy: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Models are stored locally on this Mac.", systemImage: "externaldrive")
            Label("No cloud VLM is used by this setting.", systemImage: "lock")
            Label("Downloaded models can be removed anytime.", systemImage: "trash")
            Label("YOLO and rule-engine decisions do not depend on the VLM.", systemImage: "checklist")
        }
        .font(.caption)
        .foregroundStyle(.secondary)
        .labelStyle(.titleAndIcon)
        .fixedSize(horizontal: false, vertical: true)
    }

    private var selectedModel: VLMModel? {
        service.selectedModel
    }

    private var selectedIsDownloading: Bool {
        guard let selectedModel else { return false }
        return service.downloadingModelId == selectedModel.id || selectedModel.isDownloading
    }

    private var canDownload: Bool {
        guard let selectedModel else { return false }
        return !service.isBusy && !selectedIsDownloading && !selectedModel.isInstalled
    }

    private var canUse: Bool {
        guard let selectedModel else { return false }
        return !service.isBusy && selectedModel.isInstalled && !selectedModel.isActive
    }

    private var canDelete: Bool {
        guard let selectedModel else { return false }
        return !service.isBusy && selectedModel.isInstalled
    }

    private var statusColor: Color {
        if selectedIsDownloading {
            return .blue
        }
        if service.models.contains(where: { $0.isActive }) {
            return .green
        }
        if service.models.contains(where: { $0.isInstalled }) {
            return .orange
        }
        return .secondary
    }

    private var selectedModelBinding: Binding<String> {
        Binding(
            get: { service.selectedModelId ?? service.models.first?.id ?? "" },
            set: { service.selectedModelId = $0 }
        )
    }

    private func pickerTitle(for model: VLMModel) -> String {
        model.recommended ? "\(model.displayName) - Recommended" : model.displayName
    }

    private func deleteMessage(for model: VLMModel) -> String {
        var message = "This removes the local model files from this Mac. You can download it again later."
        if model.isActive {
            message += "\n\nThis model is currently active. Deleting it will turn off Local VLM until another model is selected."
        }
        return message
    }
}

private struct VLMChatPanel: View {
    @ObservedObject var service: VLMModelService
    @ObservedObject var cameraManager: CameraManager
    let model: VLMModel
    private let recentVideoWindowSeconds: TimeInterval = 5
    private let recentVideoMaxFrames = 6
    @State private var draftQuestion = ""
    @State private var systemPrompt = ""
    @State private var systemPromptImportError: String?
    @State private var systemPromptSourceName: String?
    @State private var messages: [VLMChatMessage] = []
    @State private var isWaitingForAnswer = false
    @State private var availableFrameCount = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Image(systemName: "bubble.left.and.bubble.right")
                    .foregroundStyle(.secondary)
                Text("Chat")
                    .font(.headline)
                Spacer()
                Text(model.displayName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }

            Label(videoContextText, systemImage: availableFrameCount < 2 ? "hourglass" : "film.stack")
                .font(.caption)
                .foregroundStyle(.secondary)

            systemPromptBlock

            ScrollView {
                LazyVStack(alignment: .leading, spacing: 8) {
                    ForEach(messages) { message in
                        VLMChatBubble(message: message)
                    }
                    if isWaitingForAnswer {
                        HStack(spacing: 8) {
                            ProgressView()
                                .controlSize(.small)
                            Text("Thinking...")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 2)
            }
            .frame(minHeight: 120)

            HStack(spacing: 8) {
                TextField("Ask \(model.displayName)", text: $draftQuestion)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit(sendQuestion)

                Button {
                    sendQuestion()
                } label: {
                    Image(systemName: "paperplane.fill")
                }
                .buttonStyle(.borderedProminent)
                .disabled(trimmedQuestion.isEmpty || isWaitingForAnswer)
                .help("Send question")
            }
        }
        .frame(maxHeight: .infinity, alignment: .top)
        .onAppear(perform: refreshVideoContext)
        .onReceive(Timer.publish(every: 1, on: .main, in: .common).autoconnect()) { _ in
            refreshVideoContext()
        }
    }

    private var trimmedQuestion: String {
        draftQuestion.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var trimmedSystemPrompt: String {
        systemPrompt.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var videoContextText: String {
        if availableFrameCount < 2 {
            return "warming up video buffer: last 5s / \(availableFrameCount) frame"
                + (availableFrameCount == 1 ? "" : "s")
        }
        return "Using recent video: last 5s / \(availableFrameCount) frames"
    }

    private var systemPromptBlock: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                Label("System prompt", systemImage: "text.alignleft")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer()

                Button {
                    importSystemPrompt()
                } label: {
                    Label("Import .txt", systemImage: "doc.badge.plus")
                }
                .font(.caption)
                .buttonStyle(.bordered)
                .disabled(isWaitingForAnswer)

                Button {
                    systemPrompt = ""
                    systemPromptImportError = nil
                    systemPromptSourceName = nil
                } label: {
                    Image(systemName: "xmark.circle")
                }
                .buttonStyle(.borderless)
                .disabled(trimmedSystemPrompt.isEmpty || isWaitingForAnswer)
                .help("Clear system prompt")
            }

            ZStack(alignment: .topLeading) {
                TextEditor(text: $systemPrompt)
                    .font(.caption)
                    .frame(minHeight: 58, maxHeight: 76)
                    .background(Color(nsColor: .textBackgroundColor))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color(nsColor: .separatorColor).opacity(0.6))
                    )
                    .disabled(isWaitingForAnswer)

                if systemPrompt.isEmpty {
                    Text("Paste system prompt")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                        .padding(.horizontal, 7)
                        .padding(.vertical, 8)
                        .allowsHitTesting(false)
                }
            }

            Text(systemPromptStatusText)
                .font(.caption2)
                .foregroundStyle(systemPromptImportError == nil ? Color.secondary : Color.red)
                .lineLimit(2)
        }
    }

    private var systemPromptStatusText: String {
        if let systemPromptImportError {
            return systemPromptImportError
        }
        if trimmedSystemPrompt.isEmpty {
            return "No system prompt"
        }
        if let systemPromptSourceName {
            return "\(systemPromptSourceName) / \(trimmedSystemPrompt.count) chars"
        }
        return "\(trimmedSystemPrompt.count) chars"
    }

    private func sendQuestion() {
        let question = trimmedQuestion
        guard !question.isEmpty, !isWaitingForAnswer else { return }
        let frames = cameraManager.recentFrameJPEGs(
            windowSeconds: recentVideoWindowSeconds,
            maxFrames: recentVideoMaxFrames
        )
        availableFrameCount = frames.count
        guard !frames.isEmpty else {
            messages.append(
                VLMChatMessage(
                    role: .assistant,
                    text: "No recent camera frames are available yet."
                )
            )
            return
        }

        messages.append(VLMChatMessage(role: .user, text: question))
        draftQuestion = ""
        isWaitingForAnswer = true

        service.askActiveModel(
            question: question,
            frameData: frames,
            systemPrompt: trimmedSystemPrompt
        ) { result in
            isWaitingForAnswer = false
            switch result {
            case .success(let answer):
                messages.append(VLMChatMessage(role: .assistant, text: answer))
            case .failure(let error):
                messages.append(VLMChatMessage(role: .assistant, text: error.localizedDescription))
            }
        }
    }

    private func refreshVideoContext() {
        availableFrameCount = cameraManager.recentFrameJPEGs(
            windowSeconds: recentVideoWindowSeconds,
            maxFrames: recentVideoMaxFrames
        ).count
    }

    private func importSystemPrompt() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.plainText]
        panel.title = "Choose System Prompt"
        panel.prompt = "Use"

        guard panel.runModal() == .OK, let url = panel.url else { return }

        do {
            systemPrompt = try String(contentsOf: url, encoding: .utf8)
            systemPromptSourceName = url.lastPathComponent
            systemPromptImportError = nil
        } catch {
            systemPromptImportError = "Could not read \(url.lastPathComponent)"
        }
    }
}

private struct VLMChatBubble: View {
    let message: VLMChatMessage

    var body: some View {
        HStack {
            if message.role == .user {
                Spacer(minLength: 24)
            }

            Text(message.text)
                .font(.caption)
                .foregroundStyle(.primary)
                .padding(.horizontal, 10)
                .padding(.vertical, 7)
                .background(bubbleBackground)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .textSelection(.enabled)

            if message.role == .assistant {
                Spacer(minLength: 24)
            }
        }
    }

    private var bubbleBackground: Color {
        message.role == .user
            ? Color.accentColor.opacity(0.16)
            : Color(nsColor: .textBackgroundColor)
    }
}

private struct VLMChatMessage: Identifiable, Equatable {
    let id = UUID()
    let role: VLMChatRole
    let text: String
}

private enum VLMChatRole: Equatable {
    case user
    case assistant
}
