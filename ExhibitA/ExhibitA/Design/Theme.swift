import SwiftUI
import UIKit

/// Canonical design token layer for Exhibit A.
/// All color, typography, spacing, and shadow constants consumed by downstream views.
/// Design Doc references: S6.1, S6.2, S6.3, S6.4.
enum Theme {
    // MARK: - Colors (Design Doc S6.2)

    enum Colors {
        enum Background {
            /// Warm ivory #F2EFEA / dark #1A1614
            static var primary: Color {
                Color("BackgroundPrimary")
            }

            /// Paper-like sepia #F8F1E3 / dark #22201C
            static var reading: Color {
                Color("BackgroundReading")
            }

            /// Elevated cards #F3ECE4 / dark #2A2622
            static var secondary: Color {
                Color("BackgroundSecondary")
            }

            /// Callouts, pull quotes #E7DECD / dark #38322C
            static var tertiary: Color {
                Color("BackgroundTertiary")
            }
        }

        enum Text {
            /// Near-black #1A1A1A / warm off-white #E8E4DF
            static var primary: Color {
                Color("TextPrimary")
            }

            /// Warm dark brown #2C2118 / warm cream #DCD5CA
            static var reading: Color {
                Color("TextReading")
            }

            /// Sepia brown #5F4B32 / warm muted #A89882
            static var secondary: Color {
                Color("TextSecondary")
            }

            /// Warm gray-brown #8C7B6B / muted #6B6058
            static var muted: Color {
                Color("TextMuted")
            }
        }

        enum Accent {
            /// Burgundy #800020 / lifted #C4526A
            static var primary: Color {
                Color("AccentPrimary")
            }

            /// Terracotta #A65E46 / lifted #C8805E
            static var warm: Color {
                Color("AccentWarm")
            }

            /// Dusty rose #DCA1A1 / lifted #E0B5A8
            static var soft: Color {
                Color("AccentSoft")
            }

            /// Muted literary gold #CBB674 / lifted #D4C484
            static var gold: Color {
                Color("AccentGold")
            }
        }

        enum Border {
            /// Hairline separator #D6CFC5 / dark #3D362F
            static var separator: Color {
                Color("BorderSeparator")
            }
        }
    }

    // MARK: - UIKit Interop

    enum UIColors {
        static var backgroundPrimary: UIColor {
            guard let color = UIColor(named: "BackgroundPrimary") else {
                let message = "Asset catalog missing: BackgroundPrimary"
                preconditionFailure(message)
            }
            return color
        }
    }

    // MARK: - Typography (Design Doc S6.3)

    //
    // New York (serif) for editorial content. SF Pro (default) for UI chrome.
    // Sizes are baseline defaults at the Large accessibility setting.
    // Dynamic Type scaling is applied at the view layer via @ScaledMetric.

    enum Typography {
        /// New York XL Bold 34pt -- app title
        static var appTitle: Font {
            .system(size: 34, weight: .bold, design: .serif)
        }

        /// New York XL Bold 28pt -- screen titles
        static var screenTitle: Font {
            .system(size: 28, weight: .bold, design: .serif)
        }

        /// New York Large Semibold 24pt -- article titles
        static var articleTitle: Font {
            .system(size: 24, weight: .semibold, design: .serif)
        }

        /// New York Small Regular 18pt -- contract body
        static var contractBody: Font {
            .system(size: 18, weight: .regular, design: .serif)
        }

        /// New York Small Semibold 18pt -- section markers
        static var sectionMarker: Font {
            .system(size: 18, weight: .semibold, design: .serif)
        }

        /// New York Small Regular Italic 18pt -- legal preambles
        static var legalPreamble: Font {
            .system(size: 18, weight: .regular, design: .serif)
                .italic()
        }

        /// New York Large Regular Italic 22pt -- pull quotes
        static var pullQuote: Font {
            .system(size: 22, weight: .regular, design: .serif)
                .italic()
        }

        /// SF Pro Text Medium 13pt -- labels/classifications
        static var label: Font {
            .system(size: 13, weight: .medium)
        }

        /// SF Pro Text Regular 14pt -- dates and metadata
        static var metadata: Font {
            .system(size: 14, weight: .regular)
        }

        /// SF Pro Text Regular 12pt -- page numbers
        static var pageNumber: Font {
            .system(size: 12, weight: .regular)
        }
    }

    // MARK: - Line Height (Design Doc S6.3)

    enum LineHeight {
        /// 1.12x -- app title, screen titles
        static let tight: CGFloat = 1.12
        /// 1.18x -- article titles
        static let article: CGFloat = 1.18
        /// 1.48x -- contract body, section markers, legal preambles
        static let reading: CGFloat = 1.48
        /// 1.35x -- pull quotes
        static let pullQuote: CGFloat = 1.35
        /// 1.30x -- labels, page numbers
        static let ui: CGFloat = 1.30
        /// 1.35x -- dates and metadata
        static let metadata: CGFloat = 1.35
    }

    // MARK: - Spacing (Design Doc S6.3, S6.4 -- 8pt grid)

    enum Spacing {
        static let grid: CGFloat = 8
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
        static let xxl: CGFloat = 48

        /// Reading surface horizontal margins (Design Doc S6.3: 20-24pt)
        static let readingHorizontal: CGFloat = 24
        /// Paragraph spacing between body blocks (Design Doc S6.3: 18-22pt)
        static let paragraphSpacing: CGFloat = 20
    }

    // MARK: - Shadows (Design Doc S6.2, S6.4)

    //
    // Warm-tinted, layered. Shadow hue matches text.reading (#2C2118).
    // CSS: 0 1px 1px rgba(44,33,24,0.06),
    //      0 2px 4px rgba(44,33,24,0.06),
    //      0 4px 8px rgba(44,33,24,0.04)

    enum Shadows {
        struct Layer {
            let color: Color
            let radius: CGFloat
            let x: CGFloat
            let y: CGFloat
        }

        static let card: [Layer] = [
            Layer(
                color: warmShadow(opacity: 0.06),
                radius: 0.5,
                x: 0,
                y: 1,
            ),
            Layer(
                color: warmShadow(opacity: 0.06),
                radius: 2,
                x: 0,
                y: 2,
            ),
            Layer(
                color: warmShadow(opacity: 0.04),
                radius: 4,
                x: 0,
                y: 4,
            ),
        ]

        private static func warmShadow(opacity: Double) -> Color {
            Color(
                .sRGB,
                red: 44.0 / 255.0,
                green: 33.0 / 255.0,
                blue: 24.0 / 255.0,
                opacity: opacity,
            )
        }
    }

    // MARK: - Dividers (Design Doc S6.4)

    enum Dividers {
        /// Hairline separator width (0.5pt)
        static let hairline: CGFloat = 0.5
    }
}
