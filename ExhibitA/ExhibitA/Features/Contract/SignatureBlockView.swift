import SwiftUI
import UIKit

struct SignatureBlockView: View {
    let contentId: String

    @Environment(AppState.self) private var appState
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var activeSigner: SignerIdentifier?
    @State private var cachedImages: [String: UIImage] = [:]
    @State private var hasPerformedInitialLoad = false

    private static let signers: [(name: String, role: String, id: String)] = [
        (name: "Dinesh Dawonauth", role: "The Boyfriend", id: "dinesh"),
        (name: "Carolina Lombardo", role: "The Girlfriend", id: "carolina"),
    ]

    private static let revealDuration: TimeInterval = 0.5
    private static let revealScale: CGFloat = 0.95

    var body: some View {
        VStack(spacing: 0) {
            Text("ACKNOWLEDGED AND AGREED")
                .font(Theme.Typography.sectionMarker)
                .foregroundStyle(Theme.Colors.Text.primary)
                .tracking(1.5)
                .multilineTextAlignment(.center)
                .accessibilityAddTraits(.isHeader)
                .padding(.bottom, Theme.Spacing.xxl)

            ForEach(Array(Self.signers.enumerated()), id: \.element.id) { index, signer in
                signerLineView(signer: signer)
                    .padding(.bottom, index == 0 ? Theme.Spacing.xl : 0)
            }
        }
        .frame(maxWidth: .infinity)
        .sheet(item: $activeSigner) { signer in
            SignaturePadView(
                contentId: contentId,
                signer: signer.id,
                onSigned: { date in
                    appState.markSigned(contentId: contentId, signer: signer.id, at: date)
                }
            )
            .presentationDetents([.medium])
            .presentationDragIndicator(.hidden)
            .interactiveDismissDisabled()
        }
        .task(id: signatureStateKey) {
            await loadCachedImages()
        }
    }

    // MARK: - Signer Line Router

    @ViewBuilder
    private func signerLineView(
        signer: (name: String, role: String, id: String)
    ) -> some View {
        let isSigned = appState.isSigned(contentId: contentId, signer: signer.id)
        let isEligible = !isSigned && Config.signerIdentity == signer.id

        if isSigned {
            signedLineView(signer: signer)
        } else if isEligible {
            eligibleLineView(signer: signer)
        } else {
            ineligibleLineView(signer: signer)
        }
    }

    // MARK: - Signed State

    private func signedLineView(
        signer: (name: String, role: String, id: String)
    ) -> some View {
        VStack(spacing: Theme.Spacing.xs) {
            if let image = cachedImages[signer.id] {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(height: 60)
                    .rotationEffect(signatureRotation(for: signer.id))
                    .transition(
                        .opacity.combined(with: .scale(scale: Self.revealScale))
                    )
                    .accessibilityHidden(true)
            }

            signatureRule

            Text(signer.name)
                .font(.system(size: 15, weight: .regular, design: .serif))
                .foregroundStyle(Theme.Colors.Text.primary)

            Text("(\"\(signer.role)\")")
                .font(.system(size: 13, weight: .regular).italic())
                .foregroundStyle(Theme.Colors.Text.muted)

            if let date = appState.signedDate(contentId: contentId, signer: signer.id) {
                Text("Date: \(date.formatted(.dateTime.month(.wide).day().year()))")
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
            }
        }
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(signer.name), \(signer.role), signed")
    }

    // MARK: - Unsigned Eligible (Tappable)

    private func eligibleLineView(
        signer: (name: String, role: String, id: String)
    ) -> some View {
        Button {
            activeSigner = SignerIdentifier(id: signer.id)
        } label: {
            VStack(spacing: Theme.Spacing.xs) {
                dottedRule

                Text(signer.name)
                    .font(.system(size: 15, weight: .regular, design: .serif))
                    .foregroundStyle(Theme.Colors.Text.primary)

                Text("(\"\(signer.role)\")")
                    .font(.system(size: 13, weight: .regular).italic())
                    .foregroundStyle(Theme.Colors.Text.muted)

                Text("Tap to sign")
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Accent.warm)
            }
            .multilineTextAlignment(.center)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(signer.name), \(signer.role)")
        .accessibilityHint("Tap to open signature capture")
    }

    // MARK: - Unsigned Ineligible

    private func ineligibleLineView(
        signer: (name: String, role: String, id: String)
    ) -> some View {
        VStack(spacing: Theme.Spacing.xs) {
            dottedRule
                .opacity(0.5)

            Text(signer.name)
                .font(.system(size: 15, weight: .regular, design: .serif))
                .foregroundStyle(Theme.Colors.Text.primary)

            Text("(\"\(signer.role)\")")
                .font(.system(size: 13, weight: .regular).italic())
                .foregroundStyle(Theme.Colors.Text.muted)

            Text("Awaiting signature")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(signer.name), \(signer.role), awaiting signature")
    }

    // MARK: - Line Elements

    private var signatureRule: some View {
        Rectangle()
            .fill(Theme.Colors.Accent.gold)
            .frame(width: 200, height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }

    private var dottedRule: some View {
        SignatureDottedLine()
            .stroke(
                Theme.Colors.Accent.gold,
                style: StrokeStyle(lineWidth: Theme.Dividers.hairline, dash: [4, 3])
            )
            .frame(width: 200, height: 1)
            .accessibilityHidden(true)
    }

    // MARK: - Helpers

    private func signatureRotation(for signer: String) -> Angle {
        let seed = signer.utf8.reduce(0) { $0 &+ Int($1) }
        let degrees = 1.0 + Double(seed % 3)
        return .degrees(seed % 2 == 0 ? degrees : -degrees)
    }

    private var signatureStateKey: String {
        let stateKey = Self.signers.map {
            appState.isSigned(contentId: contentId, signer: $0.id) ? "1" : "0"
        }.joined()
        let syncKey = Int(appState.lastSyncAt?.timeIntervalSince1970 ?? 0)
        return "\(stateKey)_\(syncKey)"
    }

    private func loadCachedImages() async {
        let cache = SignatureCache()
        var newImages: [String: UIImage] = [:]

        for signer in Self.signers {
            guard appState.isSigned(contentId: contentId, signer: signer.id),
                  cachedImages[signer.id] == nil
            else { continue }

            if let data = await cache.load(contentId: contentId, signer: signer.id),
               let image = UIImage(data: data) {
                newImages[signer.id] = image
            }
        }

        guard !newImages.isEmpty else { return }

        if hasPerformedInitialLoad {
            let revealAnimation: Animation? = reduceMotion
                ? nil
                : .easeInOut(duration: Self.revealDuration)
            withAnimation(revealAnimation) {
                for (id, image) in newImages {
                    cachedImages[id] = image
                }
            }
        } else {
            for (id, image) in newImages {
                cachedImages[id] = image
            }
            hasPerformedInitialLoad = true
        }
    }
}

// MARK: - Signer Identifier

private struct SignerIdentifier: Identifiable {
    let id: String
}

// MARK: - Dotted Line Shape

private struct SignatureDottedLine: Shape {
    nonisolated func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: 0, y: rect.midY))
        path.addLine(to: CGPoint(x: rect.width, y: rect.midY))
        return path
    }
}

// MARK: - Previews

#Preview("Unsigned - Dinesh Build") {
    SignatureBlockView(contentId: "art-1")
        .environment(AppState())
        .padding()
}

#Preview("Signed - One Signer") {
    let state = AppState()
    let _ = state.markSigned(
        contentId: "art-1",
        signer: "dinesh",
        at: Calendar.current.date(
            from: DateComponents(year: 2025, month: 2, day: 14)
        ) ?? .now
    )
    SignatureBlockView(contentId: "art-1")
        .environment(state)
        .padding()
}

#Preview("Dark Mode") {
    SignatureBlockView(contentId: "art-1")
        .environment(AppState())
        .padding()
        .preferredColorScheme(.dark)
}
