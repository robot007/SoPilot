import SwiftUI

struct LocalVLMPanel: View {
    @ObservedObject var service: VLMModelService
    @State private var deleteCandidate: VLMModel?

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            header
            statusBlock
            modelPicker
            actionButtons
            progressBlock
            errorBlock
            Divider()
            localCopy
            Spacer(minLength: 0)
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
