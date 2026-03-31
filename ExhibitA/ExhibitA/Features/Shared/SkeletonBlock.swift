import SwiftUI

struct SkeletonBlock: View {
    var width: CGFloat? = nil
    var height: CGFloat = 14

    private static let fillOpacity: Double = 0.12

    var body: some View {
        RoundedRectangle(cornerRadius: 4, style: .continuous)
            .fill(Theme.Colors.Text.muted.opacity(Self.fillOpacity))
            .frame(width: width, height: height)
            .frame(maxWidth: width == nil ? .infinity : nil, alignment: .leading)
    }
}
