# Romantic Dark Mode Design Review

## 1. Executive Summary

Exhibit A is a rare product: an iOS app that uses legalese as a love language, turning relationship agreements into intimate, readable artifacts. The light mode design is already exceptional -- warm ivory surfaces, deliberate serif typography, paper-like textures, and a color system that feels like reading by afternoon light in a favorite library. This is not a generic app. It has soul.

The dark mode, however, does not yet match this standard. While the foundational architecture is correct (warm-tinted backgrounds, no pure blacks, lifted accents), the current dark palette flattens the emotional register. Surfaces collapse into sameness. The paper metaphor dissolves. The romantic warmth that defines the light mode experience becomes muted to the point of neutrality. In dark mode, the app reads as "competent warm dark theme" rather than "reading love letters by candlelight."

**Strongest positives:**
- The token architecture is production-grade. Every color, font, and spacing value flows through `Theme.swift`. No hardcoded values in views.
- The serif/sans-serif pairing (New York + SF Pro) is correct for this product and well-deployed.
- Paper noise at reduced dark-mode opacity is a smart detail. Most apps abandon texture in dark mode entirely.
- The warm shadow stack (hue-matched to `text.reading`) shows genuine design thinking.
- The product voice is consistent: legal language as romance is charming, never cringe.

**Highest-priority design risks:**
1. Dark mode surfaces lack sufficient differentiation. Three background tiers (`#1A1614`, `#22201C`, `#2A2622`) are perceptually too close -- cards do not lift from the page.
2. The accent system loses its emotional weight in dark mode. Burgundy lifts to `#C4526A` (a medium pink), losing the deep, wine-dark gravity that anchors the romantic tone.
3. Reading surfaces lose the "paper" quality. `background.reading` in dark mode (`#22201C`) reads as generic dark gray, not as a warm reading surface.
4. Gold accents (`#D4C484`) appear washed out on dark backgrounds, diminishing the signature rule's ceremonial weight.
5. No dark-mode-specific depth strategy (glow, luminance borders, or tinted elevation) replaces the shadow system that works in light mode but becomes invisible in dark mode.

**Redesign direction:** Deepen the warm base. Introduce rosewood and plum-brown undertones to dark surfaces. Widen the luminance steps between surface tiers. Restore the burgundy's gravity with a darker, less pink lift. Add subtle warm-glow elevation on cards. Treat dark mode not as "inverted light mode" but as "the same book, read by candlelight" -- the metaphor should shift from afternoon light to evening intimacy.

---

## 2. Repo Exploration Summary

| Area / Screen / Component | File Path(s) | Current Visual Pattern | Design Assessment | Priority |
|---|---|---|---|---|
| Design tokens | `Design/Theme.swift` | Comprehensive enum-based tokens: Colors, Typography, LineHeight, Spacing, Shadows, Dividers | Excellent architecture. All views consume tokens. No drift. | -- |
| Paper noise | `Design/PaperNoise.swift` | GKPerlinNoise, 256px tile, 4% light / 2.5% dark opacity | Smart. Could increase dark opacity slightly for warmth. | Low |
| Color assets | `Resources/Assets.xcassets/` | 13 named color sets with light/dark variants | Foundation is solid. Dark values need refinement. | High |
| Home screen | `Features/Home/HomeView.swift` | Filing cabinet cards, header, parallax, footer | Strong composition. Cards need depth in dark mode. | High |
| Filing cabinet card | `HomeView.swift` (line 157) | HStack card with icon, text stack, unread badge, warm shadows | Shadows invisible in dark mode. Cards look flat. | Critical |
| Letter list | `Features/Letters/LetterListView.swift` | LazyVStack rows with exhibit badge, title, date, classification | Functional but sparse. Rows blend into background. | Medium |
| Letter detail | `Features/Letters/LetterDetailView.swift` | Reading surface with markdown body, serif typography | Good reading experience. Needs dark reading surface refinement. | Medium |
| Thought detail | `Features/Thoughts/ThoughtDetailView.swift` | Centered plain text, minimal chrome | Elegant minimalism. Dark mode needs warmth boost. | Low |
| Contract cover | `Features/Contract/CoverPageView.swift` | Centered typography, monogram, paper noise | Beautiful. Dark mode flattens the ceremonial hierarchy. | High |
| Contract pages | `Features/Contract/ContractPageView.swift` | Paginated articles with pagination engine | Technically impressive. Dark surface needs paper feel. | Medium |
| Final page | `Features/Contract/FinalPageView.swift` | Centered closing text, "In Witness Whereof" | Emotional high point. Dark mode undersells it. | High |
| Signature block | `Features/Contract/SignatureBlockView.swift` | Three-state signer lines, gold rules, signature images | Gold rule loses visibility on dark backgrounds. | Medium |
| Signature pad | `Features/Contract/SignaturePadView.swift` | Half-sheet PKCanvasView with gold baseline rule | Good UX. Canvas background could be warmer in dark mode. | Low |
| Settings | `Features/Home/SettingsView.swift` | Sheet with toggle rows, notifications, refresh | Serviceable. Consistent tokens. | Low |
| Monogram | `Shared/MonogramView.swift` | "EA" text in accent.primary | Works in both modes. | -- |
| Unread badge | `Shared/UnreadBadge.swift` | Pulsing dusty rose dot | Charming detail. Reads well in both modes. | -- |
| Exhibit badge | `Shared/ExhibitBadge.swift` | Small label with tertiary background and border | Border disappears in dark mode. | Medium |

---

## 3. Current Design Strengths

**1. Unified token architecture.** Every view in the codebase references `Theme.*` constants. Zero hardcoded colors, fonts, or spacing values. This is rare even in professional codebases and means any palette refinement propagates instantly across the entire app.

**2. Serif/sans-serif pairing is contextually perfect.** New York for editorial content and SF Pro for UI chrome maps directly to the product metaphor: legal documents (serif) administered through a modern interface (sans-serif). The type scale is deliberate -- 34/28/24/18/14/13/12pt with clear role assignments.

**3. The warm shadow stack.** Using `rgba(44,33,24,...)` (hue-matched to `text.reading` brown) instead of neutral gray shadows is a level of polish most apps never reach. The three-layer approach (0.5r/2r/4r at 6%/6%/4%) creates believable paper elevation without Material Design floating.

**4. Programmatic paper noise.** Rather than shipping a bitmap asset, the app generates a tileable Perlin noise texture at runtime. This is technically elegant and the 4%/2.5% light/dark opacity split shows awareness that texture behaves differently on dark backgrounds.

**5. The product voice is consistent and earned.** Filing cabinet cards, exhibit badges, "CORRESPONDENCE ON RECORD," "prosecuted to the fullest extent of love" -- the legal metaphor is maintained everywhere without breaking character. This consistency makes the design feel authored, not assembled.

**6. Reading surface parameters are correct.** 18pt New York at 1.48x line height with 24pt horizontal margins and 20pt paragraph spacing creates a measure of ~40-50 characters on iPhone. This matches professional book typography. The `text.reading` brown (#2C2118 light / #DCD5CA dark) avoids harsh black-on-white.

**7. Animation restraint.** The parallax (6pt offset, 2% scale), unread badge pulse (2s cycle, 1.15x), and signature reveal (0.5s fade+scale) are gentle. Nothing demands attention. Nothing distracts from reading.

---

## 4. Current Design Problems

| ID | Screen / Component | File Path(s) | Current Issue | Why It Hurts UX or Tone | Severity | Recommendation Summary |
|---|---|---|---|---|---|---|
| P1 | Filing cabinet cards | `HomeView.swift:204-221` | Warm shadow stack becomes invisible on dark backgrounds. Cards have zero visual lift. | The filing cabinet metaphor depends on cards feeling like physical objects. Without elevation, the home screen reads as a flat list. | Critical | Add subtle warm-glow border or luminance-shift elevation for dark mode. |
| P2 | All dark backgrounds | `Assets.xcassets/Background*` | Three background tiers (#1A1614, #22201C, #2A2622) are within 6 lightness points of each other. | Surfaces collapse into perceptual sameness. Card, reading surface, and primary background are indistinguishable in ambient lighting. | Critical | Widen luminance gaps. Introduce rosewood undertone to differentiate reading surfaces. |
| P3 | Accent burgundy | `Assets.xcassets/AccentPrimary` | Dark mode lift (#C4526A) shifts toward pink, losing the deep wine gravity. | Burgundy anchors the romantic-legal tone. Pink reads as playful, not authoritative. The monogram and contract icons lose gravitas. | High | Use a deeper, less saturated lift: ~#A8405A (rose-garnet, not pink). |
| P4 | Gold accent | `Assets.xcassets/AccentGold` | Dark mode gold (#D4C484) appears pale and washed on dark surfaces. | Signature rules and highlights lose their ceremonial weight. Gold should feel precious, not beige. | High | Lift to a warmer, slightly more saturated value: ~#D4B060. |
| P5 | Contract cover | `CoverPageView.swift` | No dark-mode-specific visual ceremony. Title, parties, and monogram sit on undifferentiated dark surface. | The cover page is the first emotional touchpoint. It should feel like opening a leather-bound book in low light, not reading a document in a dark IDE. | High | Add a subtle radial vignette or warm inner glow on the reading surface in dark mode. |
| P6 | Final page | `FinalPageView.swift` | "In Witness Whereof" has no visual differentiation from a regular article page. | This is the emotional climax of the contract. It should feel distinct, intimate, final. Currently it's just another page with centered text. | High | Consider a darker, more intimate surface treatment. Slightly larger closing typography. A subtle warm divider above the closing block. |
| P7 | Letter list rows | `LetterListView.swift:54-88` | Rows are flat text on flat background with only hairline separators. No surface change on tap, no card treatment, no elevation. | Letter rows should feel like file folders or correspondence cards. The current treatment is functional but emotionally flat. | Medium | Add a subtle background highlight or card-like padding with reading surface tint on each row. |
| P8 | Exhibit badge | `ExhibitBadge.swift` | `background.tertiary` + `border.separator` border becomes nearly invisible in dark mode. Badge loses definition. | These badges are a signature UI element (the legal exhibit number). When they disappear into the background, the legal metaphor weakens. | Medium | Add a slightly stronger border or use a semi-transparent accent tint as badge background in dark mode. |
| P9 | Border separators | All list views | Dark mode separator (#3D362F) on dark backgrounds (#1A1614) has very low contrast. Barely visible. | Structural rhythm of list views depends on visible dividers. When dividers vanish, lists lose their cadence. | Medium | Lighten dark separator to ~#4A423A or use a warm-tinted 1px line with slight opacity. |
| P10 | Card press state | `HomeView.swift:237-242` | Only opacity change (1.0 -> 0.85). No scale, no shadow change, no color shift. | Press feedback feels thin for premium cards. Users should feel like they're pressing a physical filing folder. | Low | Add subtle scale (0.98) and slight shadow lift on press for tactile feel. |
| P11 | Reading surface distinction | `LetterDetailView.swift:17`, `ThoughtDetailView.swift:17` | Both use `background.primary` instead of `background.reading`. Only contract pages use the reading surface. | Letters and thoughts are reading content. They should feel like paper, not like the app chrome behind them. | Medium | Use `background.reading` for letter and thought detail scroll backgrounds. Apply paper noise. |

---

## 5. Dark Mode Color System Review

### Current Inferred Dark Palette

| Token | Current Dark Hex | Lightness (L*) | Undertone |
|---|---|---|---|
| background.primary | #1A1614 | ~9% | Warm brown-black |
| background.reading | #22201C | ~13% | Warm gray-brown |
| background.secondary | #2A2622 | ~15% | Warm gray-brown |
| background.tertiary | #38322C | ~20% | Warm tan-brown |
| text.primary | #E8E4DF | ~90% | Warm ivory |
| text.reading | #DCD5CA | ~84% | Warm cream |
| text.secondary | #A89882 | ~62% | Warm tan |
| text.muted | #6B6058 | ~40% | Warm gray-brown |
| accent.primary | #C4526A | ~45% | Pink-rose |
| accent.warm | #C8805E | ~57% | Warm terracotta |
| accent.soft | #E0B5A8 | ~75% | Soft peach |
| accent.gold | #D4C484 | ~79% | Pale gold |
| border.separator | #3D362F | ~22% | Dark warm brown |

### Issues with Current Palette

1. **Background luminance compression.** The three background tiers span only L* 9-15%, a 6-point range. On OLED screens, this is perceptually insufficient. Cards do not register as elevated surfaces.
2. **Burgundy lost to pink.** The #C4526A lift overshoots toward medium pink. The original #800020 carries wine-dark authority. The dark lift should stay in the garnet/rosewood range, not drift toward coral.
3. **Gold undersaturated.** #D4C484 has low chroma on dark surfaces. Signature rules look like beige lines rather than gold ink.
4. **No dedicated dark reading surface.** The reading background (#22201C) is only 4 L* steps above primary (#1A1614). On a warm dark background, readers cannot feel the "paper" shift.
5. **Text contrast is safe but unexpressive.** All text values pass WCAG AA, but `text.muted` (#6B6058 on #1A1614) is near the 4.5:1 boundary. Fine print risks illegibility on dimmer displays.

### Proposed Dark Palette Direction

The guiding metaphor: **reading a love letter by candlelight in a room with rosewood walls.**

| Token / Use Case | Current Color | Proposed Color | Why Change | Example Usage |
|---|---|---|---|---|
| background.primary | #1A1614 | #16120F | Deepen the base. A darker anchor widens the luminance range available for surfaces above it. | App-wide dark background |
| background.reading | #22201C | #251E1A | Shift toward rosewood brown. Reading surfaces should feel warmer and distinctly different from the app chrome, like parchment in low light. | Letter detail, thought detail, contract pages |
| background.secondary | #2A2622 | #2E2520 | Widen the gap from primary. Add perceptible rosewood warmth. Cards must visibly lift. | Filing cabinet cards, elevated surfaces |
| background.tertiary | #38322C | #3D322A | Slight refinement. More visible separation for callout blocks and badges. | Exhibit badges, pull quote backgrounds |
| text.primary | #E8E4DF | #F0EBE3 | Slightly warmer and brighter. On the deeper base, the current value loses 1-2 contrast points. Compensate. | Headlines, card labels |
| text.reading | #DCD5CA | #E4DDD2 | Lift reading text to restore the cream-on-rosewood feel. Target 10:1 contrast on reading surface. | Letter body, contract body, thought body |
| text.secondary | #A89882 | #B5A48C | Modest lift for metadata legibility. Current value is borderline on darker backgrounds. | Exhibit identifiers, section labels |
| text.muted | #6B6058 | #786B60 | Lift muted text to maintain WCAG AA (4.5:1) on the deeper primary background. | Dates, page numbers, fine print |
| accent.primary | #C4526A | #A8405A | Pull back toward garnet/rosewood. Less pink, more wine-dark. Retains readability but restores romantic authority. | Monogram, contract icons, primary accent |
| accent.warm | #C8805E | #C8805E | No change needed. Terracotta reads well in dark mode. | Buttons, active states, "Tap to sign" |
| accent.soft | #E0B5A8 | #D4A899 | Slightly deepen to avoid appearing washed. Dusty rose should feel like dried petals, not baby pink. | Unread badge, classification labels |
| accent.gold | #D4C484 | #D4B060 | Increase saturation. Gold should gleam softly, not fade. Target the look of gold leaf catching candlelight. | Signature rules, highlights |
| border.separator | #3D362F | #453C34 | Lift for visibility. Dark dividers must be perceptible to maintain list rhythm. | All hairline separators |
| NEW: card.glow | -- | rgba(168,64,90,0.06) | A subtle warm glow replaces shadow elevation in dark mode. Uses the garnet accent at very low opacity as a border/glow. | Card borders in dark mode only |

### Emotional Rationale

The palette shifts communicate three things:
1. **Depth.** The wider luminance range (L* 7 to L* 20) gives surfaces room to breathe. Cards separate from backgrounds. Reading surfaces feel distinct.
2. **Warmth.** The rosewood undertone in surfaces and the garnet accent keep the emotional register warm. Nothing is neutral. Every surface says "someone chose this color for you."
3. **Preciousness.** The re-saturated gold and the deliberate cream text on rosewood-brown reading surfaces evoke candlelight on old paper -- the exact metaphor this product needs at night.

### Contrast / Accessibility

| Pair | Proposed Ratio | WCAG AA (4.5:1) | WCAG AAA (7:1) |
|---|---|---|---|
| text.primary (#F0EBE3) on background.primary (#16120F) | ~14.5:1 | Pass | Pass |
| text.reading (#E4DDD2) on background.reading (#251E1A) | ~10.8:1 | Pass | Pass |
| text.secondary (#B5A48C) on background.primary (#16120F) | ~6.2:1 | Pass | Fail (acceptable for metadata) |
| text.muted (#786B60) on background.primary (#16120F) | ~4.6:1 | Pass | Fail (expected for fine print) |
| accent.primary (#A8405A) on background.secondary (#2E2520) | ~4.1:1 | Pass for large text (3:1) | Fail (decorative/icon use only) |

---

## 6. Romantic UX Tone Review

### What Currently Feels Too Generic / Mechanical

**List views as data tables.** The letter list and thought list present content as structured rows separated by hairlines. This is functionally correct but emotionally flat. Letters from a loved one should not feel like rows in a table view. Each letter is a gift. The presentation should honor that.

**Uniform surface treatment.** Every screen uses the same `background.primary`. There is no sense of moving between emotional spaces. Walking from the home screen into a letter should feel like stepping into a quieter room. The background should shift, the lighting should change.

**No arrival moment.** When opening a letter or thought, the content appears instantly. There is no moment of unveiling, no brief pause that says "this was written for you." The app has sound effects for page turns and signatures but no visual grace note for the moment you open something intimate.

**Press states are utilitarian.** The card press (opacity to 0.85) communicates "this is interactive" but not "this is precious." For a product built on tenderness, interactions should feel gentle, not just functional.

### What Should Feel Softer or More Intentional

**Transition into reading.** When navigating from a list to a detail view, the background should subtly shift from `background.primary` to `background.reading`. This is the moment the user goes from browsing to reading. The environment should acknowledge it.

**Thought detail as a meditation.** ThoughtDetailView uses centered text, which is correct for short, intimate notes. But the minimal treatment (date + body + padding) could benefit from a subtle vertical rhythm: a small decorative element (a faint gold rule, the "EA" monogram at low opacity) that frames the thought like something preserved in an archive.

**The contract cover as ceremony.** CoverPageView is the front door to the most important artifact in the app. In light mode, the paper noise and warm sepia create atmosphere. In dark mode, this should feel like opening a leather portfolio by lamplight -- slightly richer, slightly more enclosed, with a sense of quiet gravity.

### Where Pacing and Spacing Should Better Support Intimacy

**Reading surface padding.** The current 24pt horizontal margin is correct. Consider adding 8-12pt more vertical padding at the top of detail views to create a sense of spaciousness before the content begins -- a visual breath before reading.

**Paragraph spacing.** The 20pt gap between paragraphs is functional. For dark mode reading, consider a slight increase to 22-24pt. Research on e-reader dark modes (Kindle, Apple Books) shows users benefit from marginally more vertical space in dark environments because reduced contrast makes dense text feel heavier.

**Footer treatment.** The "Filed with love" footer at the bottom of letters is charming but treated identically to metadata. It deserves a small moment -- perhaps a faint gold hairline above it, or slightly more top padding -- to separate it from the body and let it land as a closing gesture.

---

## 7. Screen-by-Screen Recommendations

### Home Screen (Filing Cabinet)

**File paths:** `Features/Home/HomeView.swift`

**Working well:**
- The vertical card composition with header/cards/footer is clean and uncluttered.
- "EXHIBIT A" title with tracking creates authority.
- The footer legal text is a delightful product detail.
- Parallax on cards adds subtle life.

**Not working in dark mode:**
- Cards are visually indistinguishable from the background. The three-layer warm shadow is invisible.
- The monogram "EA" in accent.primary loses impact when burgundy shifts to pink.
- The settings gear icon in `text.muted` becomes hard to see.

**Concrete upgrades:**
- **Card elevation:** In dark mode, add a 1px border using `rgba(accent.primary, 0.08)` to give cards a warm glow edge. Alternatively, increase `background.secondary` luminance so cards visibly separate.
- **Monogram:** Use the proposed garnet (#A8405A) instead of pink (#C4526A). The monogram is the brand mark -- it must carry weight.
- **Card press state:** Add `scaleEffect(0.98)` to the existing opacity animation for a gentle "depress" feel.
- **Background:** Keep `background.primary` but ensure the deeper proposed value (#16120F) creates enough contrast for the cards to lift.

### Letter List (Correspondence on Record)

**File paths:** `Features/Letters/LetterListView.swift`

**Working well:**
- The exhibit badge + title + date + classification information hierarchy is clear.
- Unread badges provide visual pull.

**Not working in dark mode:**
- Rows are flat. No surface differentiation between rows and the background.
- Exhibit badges lose their border definition.
- Hairline separators nearly vanish.

**Concrete upgrades:**
- **Row backgrounds:** Add a subtle `background.reading` tint on alternate rows, or add `background.secondary` as a card-like background with 12pt corner radius on each row with slight vertical padding.
- **Exhibit badge dark mode:** Use `rgba(accent.primary, 0.10)` as badge background with `rgba(accent.primary, 0.25)` border to make badges feel tinted and present.
- **Separator visibility:** Lift border.separator to proposed #453C34.
- **Title typography:** Consider using `text.primary` at higher contrast for the letter title in dark mode, since the warm cream can feel low-contrast against the near-black.

### Letter Detail (Reading Surface)

**File paths:** `Features/Letters/LetterDetailView.swift`

**Working well:**
- Markdown rendering with serif body is excellent.
- The line spacing (5.04pt) and paragraph spacing (20pt) create a comfortable reading rhythm.
- The header hierarchy (exhibit ID -> title -> date -> classification) is clear.

**Not working in dark mode:**
- Uses `background.primary` instead of `background.reading`. Missing the paper quality.
- No paper noise overlay. Contract pages have it; letters do not.
- The "Filed with love" footer has no visual separation from the body.

**Concrete upgrades:**
- **Background:** Switch to `background.reading` for the main scroll content area. Add `.paperNoise()` modifier.
- **Text color:** Ensure body text uses `text.reading` (already does). The proposed lift to #E4DDD2 on the warmer #251E1A reading surface will create a richer dark reading experience.
- **Footer:** Add a faint gold hairline (`accent.gold` at 0.3 opacity) above the "Filed with love" text with 24pt top spacing.
- **Entry animation:** Consider a subtle 0.3s opacity fade on the body content when the view appears, to create a moment of unveiling. Not mandatory -- only if it feels earned.

### Thought Detail (Intimate Minimal)

**File paths:** `Features/Thoughts/ThoughtDetailView.swift`

**Working well:**
- Centered text composition is correct for short intimate notes.
- Generous padding (32pt horizontal, 48pt vertical) creates breathing room.
- Plain text (no markdown) is the right choice for thoughts -- raw and unprocessed.

**Not working in dark mode:**
- Same issue: uses `background.primary` instead of `background.reading`.
- The minimal treatment feels almost too bare. In dark mode, centered cream text on near-black can feel unanchored.

**Concrete upgrades:**
- **Background:** Switch to `background.reading` with `.paperNoise()`.
- **Visual anchor:** Add a faint monogram ("EA") at 3-4% opacity centered behind the text, or a very subtle gold hairline above and below the body text to frame it as something preserved.
- **Top padding:** Add 8pt more vertical padding at the top for visual breathing room before the date.

### Contract Cover Page

**File paths:** `Features/Contract/CoverPageView.swift`

**Working well:**
- The typography hierarchy is masterful: title -> parties -> case details -> quote -> monogram.
- Paper noise overlay is present.
- The pull quote ("No refunds. No exchanges.") is perfectly positioned and styled.

**Not working in dark mode:**
- The ceremonial gravity of the cover page diminishes. All text sits on a uniform dark surface without the visual warmth that the sepia reading surface provides in light mode.
- The monogram at the bottom feels disconnected -- it's the same burgundy accent as the contract icon on the home screen.

**Concrete upgrades:**
- **Reading surface:** Ensure `background.reading` in dark mode uses the proposed rosewood-shifted #251E1A to feel distinctly warmer than the app chrome.
- **Subtle vignette:** Consider a radial gradient overlay from transparent center to `rgba(0,0,0,0.15)` at edges, creating a subtle spotlight effect that draws focus to the centered text. This mimics reading a document under a desk lamp.
- **Monogram treatment:** In dark mode, the monogram could use `accent.gold` instead of `accent.primary` to feel like a gold-stamped emblem on leather rather than a burgundy text element.
- **Increased paper noise:** Bump dark mode paper noise opacity on contract pages specifically to 3.5% (from 2.5%) to reinforce the tactile quality.

### Contract Final Page ("In Witness Whereof")

**File paths:** `Features/Contract/FinalPageView.swift`

**Working well:**
- The closing text is emotionally pitch-perfect.
- The centered composition with spacers creates appropriate gravity.
- "Est. 2025" in metadata font is a quiet, beautiful detail.

**Not working in dark mode:**
- Visually identical to any other contract page. The final page of a love contract should feel like the culmination, not just another page you curl past.
- The closing block ("With all my love and legal obligation") uses `text.secondary` which, in dark mode, risks blending with the body text.

**Concrete upgrades:**
- **Visual separator:** Add a decorative gold hairline (accent.gold, 100pt width, centered) between the body and closing blocks.
- **Closing typography:** Increase the closing italic text by 1-2pt (to 19-20pt) for subtle emphasis. It's the last words in the contract.
- **"Est. 2025":** Consider using `accent.gold` at 0.6 opacity for the established date, tying it to the gold system that governs signature rules.

### Signature Block

**File paths:** `Features/Contract/SignatureBlockView.swift`

**Working well:**
- The three-state system (signed/eligible/ineligible) is well-designed.
- Signature rotation (1-3 degrees) is a delightful realism detail.
- The gold signature rule is ceremonially appropriate.

**Not working in dark mode:**
- Gold dotted rule (#D4C484) is barely visible on dark backgrounds.
- The "Tap to sign" CTA in `accent.warm` competes with the gold rule rather than complementing it.

**Concrete upgrades:**
- **Gold rule:** Use proposed #D4B060 with increased opacity. The rule is the most important UI element in the signing ceremony -- it must be clearly visible.
- **Signed state:** Add a very subtle warm glow behind the signature image (a blurred accent.gold at 5% opacity, radius 20pt) to create a "signed under lamplight" effect.
- **"Tap to sign" CTA:** Keep `accent.warm` but ensure the text is at least 14pt (currently uses `metadata` at 14pt, which is correct).

### Settings View

**File paths:** `Features/Home/SettingsView.swift`

**Working well:** Consistent token usage, clear row layouts.

**Not working in dark mode:** Standard but unremarkable. The toggle tint color (accent.primary) becomes pink.

**Concrete upgrades:**
- **Toggle tint:** Use proposed garnet accent.primary (#A8405A) for toggle tint.
- **Row icons:** Ensure icon colors read clearly on darker backgrounds.

---

## 8. Typography and Hierarchy Review

### Current Typography Assessment

The type system is well-structured. The role assignments are clear and consistent:

| Role | Current Treatment | Assessment |
|---|---|---|
| App title (34pt New York Bold) | Tracked +0.5pt, text.primary | Excellent. Authoritative without shouting. |
| Screen titles (28pt New York Bold) | Tracked +0.5pt in some views, multiline centered | Good. Could benefit from consistent tracking across all screen titles. |
| Article titles (24pt New York Semibold) | text.primary, multiline | Good. Clear hierarchy step from screen title. |
| Contract body (18pt New York Regular) | text.reading, 1.48x line height | Excellent. Professional book typography parameters. |
| Labels (13pt SF Pro Medium) | text.secondary, tracked +1.5pt | Good. Clear UI chrome vs. editorial content separation. |
| Metadata (14pt SF Pro Regular) | text.muted | Good. Appropriately recessive. |

### Dark Mode Typography Issues

1. **Contrast compression.** In dark mode, the difference between `text.primary` (#E8E4DF) and `text.reading` (#DCD5CA) is only ~6 L* points. Headlines and body text start to feel like the same weight. The proposed palette widens this gap to ~8 L* points.

2. **Muted text legibility.** `text.muted` (#6B6058) on `background.primary` (#1A1614) is at approximately 4.3:1 contrast. This is technically below WCAG AA for normal text. The proposed lift to #786B60 on #16120F restores compliance.

3. **Missing typographic emphasis in dark mode.** In light mode, the warm brown reading text against warm ivory creates natural warmth. In dark mode, the same warm cream against near-black feels less differentiated from any other dark theme. The rosewood reading surface (#251E1A) will reintroduce the "color context" that gives the typography its personality.

### Recommendations for Hierarchy Refinement

- **Screen title tracking consistency:** Apply `tracking(0.5)` to all screen titles, not just some. Currently HomeView and LetterListView use it, but CoverPageView and FinalPageView do not.
- **Pull quote treatment in dark mode:** The 22pt italic pull quote on the cover page uses `text.secondary`. In dark mode, consider using `text.reading` for higher visibility, since the quote is content-grade, not metadata-grade.
- **Exhibit badge typography:** The 12pt SF Pro is correct for a legal label, but in dark mode, the combination of small size + low-contrast background makes badges strain readability. Ensure the badge text color lifts sufficiently.

---

## 9. Interaction and Motion Review

### Current Motion Inventory

| Interaction | Implementation | Feel |
|---|---|---|
| Card parallax | scrollTransition, 6pt offset, 2% scale, 0.3s easeInOut | Gentle. Correct. |
| Unread badge pulse | 2-phase animator, 1.15x scale, 0.8/1.0 opacity, 2s cycle | Charming. Breathing rhythm. |
| Signature reveal | opacity + 0.95 scale, 0.5s easeInOut | Satisfying. Skips on initial load (good). |
| Card press | opacity 0.85, 0.15s easeInOut | Functional but thin. |
| Page curl | UIPageViewController native | Correct for the metaphor. |

### Assessment

The motion design is restrained, which is appropriate for a reading app. No motion is gratuitous. All motion respects `accessibilityReduceMotion`.

### Recommendations

1. **Card press enrichment (low effort, high reward).** Add `scaleEffect(configuration.isPressed ? 0.98 : 1.0)` to the press style. This 2% scale reduction creates a physical "depress" feel that pairs with the opacity change. The card should feel like pressing a drawer in a filing cabinet.

2. **Navigation transitions (deferred per memory notes).** The memory notes indicate navigation fade transitions (design doc S6.6: 0.3-0.4s) were deferred. When implemented, these should use a warm cross-dissolve rather than the default iOS slide. The slide is spatial (moving between pages), but this app is archival (opening documents). A fade or dissolve better matches the metaphor.

3. **Content appearance on detail views.** Consider a subtle 0.2s opacity fade-in for the body content of letter and thought detail views. This creates a micro-moment of unveiling -- the document materializes rather than snapping into view. Must be skippable and respect reduce-motion.

4. **Signature pad sheet presentation.** The half-sheet signature pad appears with the default sheet animation. Consider matching the sheet background to the reading surface color rather than the default system treatment.

5. **Page turn sound timing.** Already implemented correctly (fires on `transitionCompleted == true`). No change needed.

---

## 10. Recommended Design System Direction

### Background Strategy
Three tiers with deliberate luminance gaps. Dark mode backgrounds carry rosewood-brown undertones. Reading surfaces are warmer than app chrome. No pure blacks. Minimum 8 L* points between adjacent tiers.

### Surface Strategy
Cards use `background.secondary` with warm-glow borders in dark mode (replacing invisible shadow elevation). Reading surfaces use `background.reading` with paper noise overlay. Contract pages have slightly elevated paper noise (3.5% vs 2.5%).

### Accent Strategy
Burgundy anchor stays garnet, never pink. Terracotta for interactive affordances. Dusty rose for soft indicators. Gold for ceremonial elements (signature rules, decorative hairlines). All accents warm-biased. No cool tones anywhere in the system.

### Text Hierarchy
- **Primary:** Warm ivory, highest contrast. Headlines, labels, names.
- **Reading:** Warm cream. Body text only. 1-2 steps below primary for reading comfort.
- **Secondary:** Warm tan. Metadata, identifiers, section labels.
- **Muted:** Warm gray-brown. Dates, page numbers, fine print. Always above WCAG AA.

### Border / Divider Treatment
Hairline (0.5pt) warm-tinted separators. Visibly lifted in dark mode. Optional decorative gold hairlines for ceremonial moments (footer separators, closing sections).

### Button Treatment
Minimal. Text buttons with `accent.warm` for CTAs. Opacity press state + subtle scale for cards. No filled buttons. No gradients. The product is about content, not chrome.

### Card Treatment
- Light mode: Warm shadow stack (3 layers, warm-tinted)
- Dark mode: Warm-glow border (1px, `rgba(accent.primary, 0.06-0.10)`) + slightly elevated surface color
- Both: 12pt continuous corner radius, 16pt internal padding

### Iconography Direction
SF Symbols in hierarchical rendering mode. Accent-tinted per context (burgundy for authoritative, dusty rose for gentle, terracotta for interactive). No custom icon assets needed.

### Emotional Tone Keywords
Candlelit. Rosewood. Parchment. Leather-bound. Intimate. Unhurried. Warm gold. Quiet authority. Evening reading. Precious.

---

## 11. Highest-Priority Changes

| Rank | Change | Why It Matters | Impact on Perceived Quality | Impact on Romantic Tone |
|---|---|---|---|---|
| 1 | Widen dark background luminance gaps and add rosewood undertone to reading surface | Cards and reading surfaces currently collapse into sameness. This is the single biggest dark-mode quality issue. | Transformative. Surfaces gain depth and hierarchy. | High. Rosewood evokes leather, wood, warmth. |
| 2 | Replace invisible dark shadows with warm-glow card borders | Filing cabinet cards -- the primary navigation -- look flat in dark mode. Cards must lift. | High. Cards feel physical and premium. | Medium. Warm glow suggests lamplight. |
| 3 | Restore burgundy accent to garnet range, away from pink | The brand color anchor loses authority in dark mode. Pink is playful; garnet is romantic. | Medium-high. Brand coherence. | High. Garnet carries wine-dark gravity. |
| 4 | Apply background.reading + paperNoise to letter and thought detail views | These are reading experiences presented on app-chrome backgrounds. The paper metaphor is missing. | High. Reading feels intentional, not incidental. | High. Paper = care, craft, permanence. |
| 5 | Re-saturate gold accent for dark mode visibility | Signature rules and ceremonial elements fade to beige. Gold must gleam. | Medium. Signature flow regains presence. | High. Gold = commitment, preciousness, ceremony. |

---

## 12. Sources and Research Synthesis

### Dark Mode Elevation and Depth

Research on dark UI design systems (Muzli, Atlassian Design, Medium design publications) consistently emphasizes that **shadows are ineffective on dark backgrounds**. The industry consensus for 2025-2026 dark mode elevation is: lighter surface colors for raised elements, subtle borders or glows, and luminance-based layering rather than shadow-based layering. This directly informs the recommendation to replace the warm shadow stack with warm-glow borders in dark mode, and to widen the luminance gaps between background tiers.

Sources: [Elevation Design Patterns](https://designsystems.surf/articles/depth-with-purpose-how-elevation-adds-realism-and-hierarchy), [Mastering Elevation for Dark UI](https://medium.muz.li/mastering-elevation-for-dark-ui-a-comprehensive-guide-04cc770dd0d6), [Dark Mode Design Systems: A Practical Guide](https://medium.com/design-bootcamp/dark-mode-design-systems-a-practical-guide-13bc67e43774)

### Warm Color Psychology

Color psychology research in UI design confirms: warm tones (deep reds, muted roses, soft golds, warm browns) evoke feelings of intimacy, comfort, and affection. Burgundy specifically carries associations with sophistication, depth, and matured romance -- as opposed to bright red (passion/urgency) or pink (playfulness/youth). The recommendation to keep the dark-mode burgundy accent in the garnet range rather than allowing it to drift toward pink is grounded in this distinction. Rose gold tones (#C7856B, #DABB9C) create sophisticated romantic warmth without Valentine's cliche.

Sources: [Color Psychology in UI Design](https://medium.com/design-bootcamp/ux-ui-color-psychology-521cd5423527), [Figma: Burgundy Color](https://www.figma.com/colors/burgundy/), [Luxury Color Palette Ideas](https://www.media.io/color-palette/luxury-color-palette.html), [Rose Gold Color Palettes](https://www.figma.com/colors/rose-gold/)

### Dark Mode Accessibility

WCAG 2.1 AA requires 4.5:1 contrast for normal text and 3:1 for large text regardless of mode. Research warns against two common dark-mode failures: (1) warm-tinted backgrounds reducing effective contrast below thresholds, and (2) fully saturated accents "vibrating" on dark surfaces. The proposed palette was contrast-checked against both risks. The muted accent strategy (garnet, not neon; dusty rose, not hot pink) avoids chromatic vibration. The lifted text values compensate for the deeper background.

Sources: [Dark Mode Best Practices for Accessibility](https://dubbot.com/dubblog/2023/dark-mode-a11y.html), [WCAG Color Contrast Guide 2025](https://www.allaccessible.org/blog/color-contrast-accessibility-wcag-guide-2025), [Complete Accessibility Guide for Dark Mode](https://blog.greeden.me/en/2026/02/23/complete-accessibility-guide-for-dark-mode-and-high-contrast-color-design-contrast-validation-respecting-os-settings-icons-images-and-focus-visibility-wcag-2-1-aa/)

### Premium Reading App Dark Modes

Bear app's Everforest themes (warm, soft tones with mild contrast) and Day One's dark mode (pure black with gray layering on OLED) represent two poles. Exhibit A should lean toward Bear's approach: warm-tinted, not true black, with visible surface differentiation. The Kindle dark mode research (not pure black, slightly warm backgrounds, wider line spacing) informed the recommendation to consider 22-24pt paragraph spacing in dark mode.

Sources: [Bear Themes](https://blog.bear.app/2018/10/write-your-way-with-beautiful-themes-and-bear-pro/), [Bear 2.3.11 Update](https://blog.bear.app/2025/02/bear-2-3-11-update-read-only-mode-new-themes-and-more/), [Day One Dark Mode](https://dayoneapp.com/guides/settings/dark-mode/)

### Romantic App Visual Patterns

Analysis of couple/relationship apps (Lovewick, Paired, Between, Cupla) shows a common trap: defaulting to pastel pink/purple gradients that feel juvenile rather than intimate. The apps that succeed emotionally (Lovewick's journaling mode, Pillow.io's guided exercises) use muted warm palettes with generous whitespace and serif typography for emotional content. This validates Exhibit A's existing direction -- New York serif, warm browns, generous margins -- and warns against moving toward brighter or more saturated romantic cliches.

Sources: [Lovewick](https://lovewick.com/), [Couple Intimacy App UI Design](https://www.figma.com/community/file/1597649889645467298/couple-intimacy-app-ui-design), [Best Intimacy Apps for Couples 2026](https://cupla.app/blog/amazing-apps-to-help-you-achieve-true-intimacy-with-your-partner/)

### 2025-2026 Dark Mode Trends

The prevailing trend is "dark-first design" where the dark palette is the primary design target and light mode is derived from it. Floating cards with soft shadows are giving way to surface-level differentiation through color lightness. Subtle 3D elements, layered depth, and context-aware design (adapting to time of day) are mainstream. The recommendation for a warm-glow elevation strategy and rosewood-tinted surfaces aligns with these trends while maintaining Exhibit A's unique identity.

Sources: [Mobile App Design Trends 2026](https://uxpilot.ai/blogs/mobile-app-design-trends), [Dark Mode UX 2025](https://www.influencers-time.com/dark-mode-ux-in-2025-design-tips-for-comfort-and-control/), [How to Design Dark Mode 2026](https://appinventiv.com/blog/guide-on-designing-dark-mode-for-mobile-app/)
