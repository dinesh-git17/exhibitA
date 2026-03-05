import GameplayKit
import SwiftUI
import UIKit

/// Programmatic paper-noise texture overlay for reading surfaces.
/// Design Doc S6.4, S6.7: fractalNoise, 3 octaves, tileable, no bitmap assets.
struct PaperNoiseView: View {
    @Environment(\.colorScheme) private var colorScheme

    private static let lightOpacity = 0.04
    private static let darkOpacity = 0.025
    private static let tileSize = 256

    var body: some View {
        Image(uiImage: Self.noiseImage)
            .resizable(resizingMode: .tile)
            .opacity(
                colorScheme == .light
                    ? Self.lightOpacity : Self.darkOpacity,
            )
            .allowsHitTesting(false)
            .accessibilityHidden(true)
    }

    // MARK: - Noise Generation

    private static let noiseImage: UIImage = generateNoiseTexture()

    private static func generateNoiseTexture() -> UIImage {
        let source = GKPerlinNoiseSource(
            frequency: 4.0,
            octaveCount: 3,
            persistence: 0.5,
            lacunarity: 2.0,
            seed: 0,
        )
        let noise = GKNoise(source)
        let map = GKNoiseMap(
            noise,
            size: vector_double2(16.0, 16.0),
            origin: vector_double2(0.0, 0.0),
            sampleCount: vector_int2(
                Int32(tileSize),
                Int32(tileSize),
            ),
            seamless: true,
        )

        let pixels = rasterizeNoiseMap(map)
        return imageFromGrayscalePixels(pixels)
    }

    private static func rasterizeNoiseMap(
        _ map: GKNoiseMap,
    )
        -> [UInt8]
    {
        var pixels = [UInt8](repeating: 0, count: tileSize * tileSize)
        for y in 0 ..< tileSize {
            for x in 0 ..< tileSize {
                let value = map.value(
                    at: vector_int2(Int32(x), Int32(y)),
                )
                let normalized = (value + 1.0) * 0.5
                let clamped = min(max(normalized, 0.0), 1.0)
                pixels[y * tileSize + x] = UInt8(clamped * 255)
            }
        }
        return pixels
    }

    private static func imageFromGrayscalePixels(
        _ pixels: [UInt8],
    )
        -> UIImage
    {
        let data = Data(pixels)
        guard let provider = CGDataProvider(data: data as CFData)
        else {
            let message =
                "Failed to create CGDataProvider for paper noise"
            preconditionFailure(message)
        }

        guard let cgImage = CGImage(
            width: tileSize,
            height: tileSize,
            bitsPerComponent: 8,
            bitsPerPixel: 8,
            bytesPerRow: tileSize,
            space: CGColorSpaceCreateDeviceGray(),
            bitmapInfo: CGBitmapInfo(
                rawValue: CGImageAlphaInfo.none.rawValue,
            ),
            provider: provider,
            decode: nil,
            shouldInterpolate: false,
            intent: .defaultIntent,
        )
        else {
            let message =
                "Failed to create CGImage for paper noise"
            preconditionFailure(message)
        }

        return UIImage(cgImage: cgImage)
    }
}

// MARK: - View Extension

extension View {
    /// Overlays programmatic paper-noise texture at design-specified opacity.
    /// Light mode: 3-5%. Dark mode: 2-3%.
    func paperNoise() -> some View {
        overlay { PaperNoiseView() }
    }

}
