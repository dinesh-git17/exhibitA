#if canImport(PencilKit)
import PencilKit
#endif
import SwiftUI
import UIKit

struct SignaturePadView: View {
    let contentId: String
    let signer: String
    let onSigned: @MainActor (Date) -> Void

    @Environment(\.dismiss) private var dismiss
    @Environment(UploadQueue.self) private var uploadQueue: UploadQueue?

    #if canImport(PencilKit)
    @State private var drawing = PKDrawing()
    #endif
    @State private var canvasIsEmpty = true
    @State private var hasSubmitted = false
    @State private var errorMessage: String?
    @State private var showClearConfirmation = false

    private static let maxPNGBytes = 50_000
    private static let exportPadding: CGFloat = 8
    private static let canvasHeight: CGFloat = 180

    var body: some View {
        #if canImport(PencilKit)
        captureContent
        #else
        fallbackContent
        #endif
    }

    // MARK: - PencilKit Capture

    #if canImport(PencilKit)
    private var captureContent: some View {
        VStack(spacing: 0) {
            Text("Sign Here")
                .font(Theme.Typography.sectionMarker)
                .foregroundStyle(Theme.Colors.Text.primary)
                .padding(.top, Theme.Spacing.lg)
                .padding(.bottom, Theme.Spacing.md)

            SignatureCanvas(drawing: $drawing, isEmpty: $canvasIsEmpty)
                .frame(maxWidth: .infinity)
                .frame(height: Self.canvasHeight)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay {
                    VStack {
                        Spacer()
                        Rectangle()
                            .fill(Theme.Colors.Accent.gold)
                            .frame(height: Theme.Dividers.hairline)
                            .padding(.horizontal, Theme.Spacing.lg)
                            .padding(.bottom, 40)
                    }
                    .allowsHitTesting(false)
                }
                .padding(.horizontal, Theme.Spacing.readingHorizontal)

            Spacer()

            actionButtons
                .padding(.bottom, Theme.Spacing.lg)
        }
        .background {
            Theme.Colors.Background.reading.ignoresSafeArea()
        }
        .paperNoise()
        .alert("Clear Drawing?", isPresented: $showClearConfirmation) {
            Button("Clear", role: .destructive) {
                drawing = PKDrawing()
            }
            Button("Cancel", role: .cancel) {}
        }
        .alert(
            "Upload Failed",
            isPresented: Binding(
                get: { errorMessage != nil },
                set: { if !$0 { errorMessage = nil } }
            )
        ) {
            Button("OK") { errorMessage = nil }
        } message: {
            if let msg = errorMessage {
                Text(msg)
            }
        }
    }

    private var actionButtons: some View {
        HStack(spacing: Theme.Spacing.xxl) {
            Button("Clear") {
                handleClear()
            }
            .font(Theme.Typography.metadata)
            .foregroundStyle(Theme.Colors.Text.secondary)
            .accessibilityHint(canvasIsEmpty ? "Dismisses signature sheet" : "Clears the current drawing")

            Button {
                Task { await handleSign() }
            } label: {
                Text("Sign")
            }
            .font(Theme.Typography.sectionMarker)
            .foregroundStyle(canvasIsEmpty ? Theme.Colors.Text.muted : Theme.Colors.Text.primary)
            .disabled(canvasIsEmpty || hasSubmitted)
            .accessibilityLabel("Sign")
            .accessibilityHint(canvasIsEmpty ? "Draw your signature first" : "Submits your signature")
        }
    }
    #endif

    // MARK: - Fallback

    private var fallbackContent: some View {
        VStack(spacing: Theme.Spacing.md) {
            Text("Signature capture is not available on this device.")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
                .multilineTextAlignment(.center)

            Button("Dismiss") { dismiss() }
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.secondary)
        }
        .padding()
        .background {
            Theme.Colors.Background.reading.ignoresSafeArea()
        }
    }

    // MARK: - Actions

    private func handleClear() {
        if canvasIsEmpty {
            dismiss()
        } else {
            showClearConfirmation = true
        }
    }

    #if canImport(PencilKit)
    private func handleSign() async {
        guard !hasSubmitted, !drawing.strokes.isEmpty else { return }

        guard let pngData = exportPNG() else {
            errorMessage = "Failed to export signature."
            return
        }

        guard pngData.count < Self.maxPNGBytes else {
            errorMessage = "Signature image exceeds size limit."
            return
        }

        let cache = SignatureCache()
        do {
            try await cache.save(png: pngData, contentId: contentId, signer: signer)
        } catch {
            errorMessage = "Failed to save signature locally."
            return
        }

        hasSubmitted = true
        uploadQueue?.enqueue(contentId: contentId, signer: signer)
        onSigned(.now)
        dismiss()
    }

    private func exportPNG() -> Data? {
        guard !drawing.strokes.isEmpty else { return nil }

        let padding = Self.exportPadding
        let bounds = drawing.bounds.insetBy(dx: -padding, dy: -padding)

        let scale = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first?.screen.scale ?? 3.0

        let image = drawing.image(from: bounds, scale: scale)
        guard let data = image.pngData() else { return nil }

        if data.count < Self.maxPNGBytes {
            return data
        }

        let reducedScale: CGFloat = 2.0
        let reduced = drawing.image(from: bounds, scale: reducedScale)
        return reduced.pngData()
    }
    #endif
}

// MARK: - Signature Canvas (UIViewRepresentable)

#if canImport(PencilKit)
private struct SignatureCanvas: UIViewRepresentable {
    @Binding var drawing: PKDrawing
    @Binding var isEmpty: Bool

    private static let inkWidth: CGFloat = 2.5
    private static let canvasPaper = UIColor(
        red: 251.0 / 255.0,
        green: 247.0 / 255.0,
        blue: 240.0 / 255.0,
        alpha: 1.0
    )

    func makeUIView(context: Context) -> PKCanvasView {
        let canvas = PKCanvasView()
        canvas.drawing = drawing
        canvas.delegate = context.coordinator
        canvas.drawingPolicy = .anyInput
        canvas.isRulerActive = false
        canvas.isOpaque = true
        canvas.backgroundColor = Self.canvasPaper
        canvas.overrideUserInterfaceStyle = .light

        let inkColor = UIColor(named: "TextReading") ?? UIColor(
            red: 44.0 / 255.0,
            green: 33.0 / 255.0,
            blue: 24.0 / 255.0,
            alpha: 1.0
        )
        canvas.tool = PKInkingTool(.pen, color: inkColor, width: Self.inkWidth)

        return canvas
    }

    func updateUIView(_ canvas: PKCanvasView, context: Context) {
        if canvas.drawing != drawing {
            canvas.drawing = drawing
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(drawing: $drawing, isEmpty: $isEmpty)
    }

    final class Coordinator: NSObject, PKCanvasViewDelegate {
        private var drawing: Binding<PKDrawing>
        private var isEmpty: Binding<Bool>

        init(drawing: Binding<PKDrawing>, isEmpty: Binding<Bool>) {
            self.drawing = drawing
            self.isEmpty = isEmpty
        }

        func canvasViewDrawingDidChange(_ canvasView: PKCanvasView) {
            drawing.wrappedValue = canvasView.drawing
            isEmpty.wrappedValue = canvasView.drawing.strokes.isEmpty
        }
    }
}
#endif

// MARK: - Previews

#Preview("Signature Pad") {
    SignaturePadView(
        contentId: "art-1",
        signer: "dinesh",
        onSigned: { _ in }
    )
    .presentationDetents([.medium])
}

#Preview("Signature Pad - Dark") {
    SignaturePadView(
        contentId: "art-1",
        signer: "dinesh",
        onSigned: { _ in }
    )
    .presentationDetents([.medium])
    .preferredColorScheme(.dark)
}
