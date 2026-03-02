# Exhibit A — Design Document

### A Legally Binding Love Application

| Field             | Value                                              |
|-------------------|----------------------------------------------------|
| **Title**         | Exhibit A — Design Document                        |
| **Author(s)**     | Dinesh D. (Engineering)                            |
| **Reviewers**     | Claude (Architecture)                              |
| **Status**        | Accepted                                           |
| **Created**       | 2025-12-01                                         |
| **Last Updated**  | 2026-03-01                                         |
| **Supersedes**    | N/A                                                |
| **Superseded By** | N/A                                                |
| **Version**       | 1.1                                                |
| **Platform**      | iOS 26+ (SwiftUI) + FastAPI Backend (Python 3.13+) |
| **Distribution**  | TestFlight                                         |

---

## 1. Overview

Exhibit A is a private iOS application that presents a collection of relationship contracts, love letters, and personal
thoughts in a warm, legal-document aesthetic. The app serves two users — the author and the recipient — as a living
personal artifact where new content can appear at any time without rebuilding the app. Content is managed through a
web-based admin panel and delivered to the iOS app via a lightweight backend API with push notifications.

Key trade-offs: the system prioritizes simplicity and emotional impact over scalability and multi-user flexibility. A
single-server architecture with file-based caching is chosen over distributed systems. Push notifications are chosen
over real-time connections to preserve battery life and reduce complexity.

### 1.1 Context

This is a greenfield project. No existing application or system precedes it.

- **Current state:** Relationship content (love notes, jokes, promises) is currently shared via text messages and verbal
  communication — ephemeral, unsearchable, and unstructured.
- **Existing artifact:** A 20-article contract document exists in `docs/exhibit-A-contract.md` (~15,000 words of
  comedic-legal content, fully written and ready for app integration).
- **Distribution constraint:** The app will be distributed via TestFlight to exactly two users. No App Store listing.
  TestFlight builds expire every 90 days, requiring scheduled CI rebuilds.

The project is motivated by the desire to transform ephemeral relationship communication into a permanent, signable,
living digital artifact.

### 1.2 Concept

Exhibit A is a private iOS app disguised as a legal document management system. It contains love contracts written in
comedic legalese, love letters, and spontaneous thoughts — all updatable from a backend API so content stays alive long
after install.

Both parties sign contracts with real signatures (PencilKit) that persist via a VPS-hosted API. The app is a living
artifact — new content can appear at any time without a TestFlight rebuild.

**Name rationale:** "Exhibit A" is a legal term for evidence presented in court. Carolina is Exhibit A in the case for
love. The relationship is the evidence. The app is the filing.

---

## 2. Information Architecture

```
┌─────────────────────────────────────────────┐
│              EXHIBIT A                       │
│         "The Official Record"                │
│                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │   THE   │ │  FILED  │ │ SEALED  │       │
│  │ CONTRACT│ │ LETTERS │ │ THOUGHTS│       │
│  │   📜    │ │   ✉️    │ │   🔒    │       │
│  └────┬────┘ └────┬────┘ └────┬────┘       │
│       │           │           │              │
│  Page-curl    Letter list  Thought list     │
│  book with    → detail     → detail         │
│  signatures   reader       reader           │
└─────────────────────────────────────────────┘
```

### 2.1 Home Screen — "The Filing Cabinet"

The landing screen. Warm, inviting, softly lit. The legal framing is in the words — the design says "open me, stay a
while."

**Header area:**

- App title: "EXHIBIT A" in New York Bold, 34pt, `text.primary`, centered, tracked +0.5pt
- Subtitle: "Case No. DC-2025-0214 | Dinesh & Carolina" in SF Pro Text Regular, 14pt, `text.muted`
- "EA" monogram in New York Bold, `accent.primary` burgundy, centered below subtitle — no wax seal, no emboss, no
  graphic ornament

**Three entry points**, each styled as a warm card on `background.secondary` with layered warm shadow
(`rgba(44,33,24,0.06)`), 12pt continuous corner radius. Cards vary in height based on content — no uniform grid:

| Section         | Label                      | Subtitle                                            | Visual                                      |
|-----------------|----------------------------|-----------------------------------------------------|---------------------------------------------|
| The Contract    | "The Binding Agreement"    | "Governing Terms & Conditions of This Relationship" | SF Symbol `book.closed` in `accent.primary` |
| Filed Letters   | "Correspondence on Record" | "{n} letters filed"                                 | SF Symbol `envelope` in `accent.soft`       |
| Sealed Thoughts | "Classified Memoranda"     | "{n} memoranda on file"                             | SF Symbol `lock.fill` in `accent.primary`   |

Each section shows a small `accent.soft` dot when unread content exists. Gentle pulse animation (2s breathing cycle).
Unread state tracked locally via UserDefaults (last-read timestamp vs. content `updated_at`).

**Bottom of home screen:**

- "This document is the property of Dinesh & Carolina. Unauthorized access will be prosecuted to the fullest extent of
  love." — in `text.muted`, New York Regular Italic, 13pt.

---

## 3. The Contract — Book View

### 3.1 Navigation

Opens as a **page-curl book** using `UIPageViewController` wrapped in `UIViewControllerRepresentable`. Kindle-style page
turn animation on swipe.

**Page sequence:**

```
[Cover] → [Table of Contents] → [Article I] → [Article II] → ... → [Final Page]
```

### 3.2 Cover Page

```
─────────────────────────────────
     THE OFFICIAL & LEGALLY
      BINDING LOVE CONTRACT

        Between the Parties:

        DINESH DAWONAUTH
          ("The Boyfriend")
              — and —
       CAROLINA LOMBARDO
          ("The Girlfriend")

     Case No. DC-2025-0214
     Filed: [date of first install]
     Jurisdiction: The Supreme Court of Us

     "No refunds. No exchanges.
      All sales are final."

           EA
─────────────────────────────────
```

### 3.3 Table of Contents

Lists all articles with their titles. Tappable — jumps to that page. Styled as a legal brief's table of contents with
dotted leaders and page numbers.

```
TABLE OF CONTENTS

Article I ........... Definition of Forever ............. 3
Article II .......... Daily Reassurance Obligations ..... 6
Article III ......... Princess Treatment Provision ...... 9
Article IV .......... Comfort in Times of Distress ..... 12
Article V ........... Exclusive Baby Status ............ 15
...
Article XVIII ....... No Refunds, No Exchanges ......... 58
Article XIX ......... Public Recognition of Softness ... 61
Article XX .......... Final Irrevocability Clause ...... 64
```

### 3.4 Contract Content Model

Each article is a single content record with unlimited clauses. The body text is structured but stored as one block. The
app paginates it at render time based on available screen height.

**Structure of an article body:**

```
PREAMBLE (WHEREAS clauses — as many as needed)
  ↓
AGREEMENT (NOW, THEREFORE...)
  ↓
CLAUSES (§n.1, §n.2, §n.3... unlimited)
  ↓
SIGNATURE BLOCK (always the final page of the article)
```

**Pagination logic:**

The app measures the rendered text height against the page viewport. When an article's content exceeds one page, it
splits across multiple pages at natural break points (between clauses, between preamble and agreement, between
paragraphs). The reader swipes through all pages of the article, and the **signature block is always the last page** —
it acts as the closing of that article before the next one begins.

```
Article III: Snack Procurement Obligations

  [Page 1]  WHEREAS clauses + agreement intro
  [Page 2]  §3.1 through §3.4
  [Page 3]  §3.5 through §3.7 + closing clause
  [Page 4]  SIGNATURE BLOCK — both signature lines
```

Short articles might fit on a single page with the signature block on page two. Long articles with many clauses can span
as many pages as needed. The system is elastic.

**Page number display:** Bottom-center of each page. Format: "Article III — 2 of 4". This tells Carolina where she is
within an article, not within the entire book.

### 3.5 Contract Page Example

```
─────────────────────────────────

           ARTICLE III
  SNACK PROCUREMENT OBLIGATIONS

WHEREAS the Girlfriend has expressed,
on no fewer than forty-seven (47)
documented occasions, a preference
for snacks of the sweet, salty, and
"surprise me" variety;

AND WHEREAS the Boyfriend has
demonstrated a pattern of arriving
with said snacks unprompted, thereby
establishing precedent;

NOW, THEREFORE, the Parties agree:

§3.1  The Boyfriend shall maintain
a reasonable inventory of the
Girlfriend's preferred snacks at
all times. "Reasonable" shall be
defined as "more than zero."

§3.2  The phrase "I'm not hungry"
shall not be interpreted literally
and the Boyfriend shall procure
snacks regardless.

§3.3  Failure to comply with §3.2
shall constitute a Minor Infraction
under Schedule B of this Agreement.

            Article III — 1 of 2
─────────────────────────────────
```

**Signature page (always the final page of each article):**

```
─────────────────────────────────

§3.4  In the event of a dispute
regarding snack preferences, the
Girlfriend's craving at the time
of request shall be considered
the final authority.


ACKNOWLEDGED AND AGREED:


______________________
Dinesh Dawonauth
"The Boyfriend"
Date: _______________


______________________
Carolina Lombardo
"The Girlfriend"
Date: _______________

            Article III — 2 of 2
─────────────────────────────────
```

### 3.6 Adding New Clauses

When you add clauses to an existing article via the admin panel, you edit the article body and append new sections. The
app re-paginates automatically. Carolina sees the updated article on her next sync — more pages to flip through now,
signature block pushed to the new last page. Existing signatures remain intact.

### 3.7 Signature Mechanics

**Unsigned state:**

- Dotted line with label: "Tap to sign"
- Subtle pulse animation on the line to draw attention

**Signing flow:**

1. User taps the dotted signature line
2. Half-sheet slides up with PencilKit canvas
3. `background.reading` (#F8F1E3) background, `text.reading` stroke
4. "Clear" button (left) and "Sign" button (right)
5. On "Sign": canvas exports as PNG
6. PNG uploads to API via `POST /signatures`
7. Signature animates into place on the contract page (fade + slight scale)
8. Soft haptic feedback (UIImpactFeedbackGenerator, .medium)
9. Date auto-fills with current date

**Signed state:**

- Signature rendered as an image from API/cache
- Date displayed below
- No re-signing allowed (signatures are permanent — that's the joke and the point)

**Signature identification:**

- App ships with a hardcoded `signer` value
- Dinesh's build: `signer = "dinesh"`
- Carolina's build: `signer = "carolina"`
- Configured at build time via an environment variable or xcconfig
- This determines which signature line is tappable

### 3.8 Contract Content — Final Articles

Full contract text is maintained in `docs/exhibit-A-contract.md`. Twenty articles, each with full WHEREAS preambles and
NOW THEREFORE clauses. New articles can be added via the admin panel over time.

| #     | Title                                             | Theme                                                                                             |
|-------|---------------------------------------------------|---------------------------------------------------------------------------------------------------|
| I     | Definition of Forever                             | Foundational. Establishes that "forever" is a sincere, lasting intention — not exaggeration.      |
| II    | Daily Reassurance and Affection Obligations       | Good morning texts, check-ins, and affection as ongoing duties.                                   |
| III   | Princess Treatment Provision                      | The Girlfriend holds princess-level status. Treatment scales up on bad days, not down.            |
| IV    | Comfort in Times of Distress                      | Comfort is a binding obligation. She is never a burden for needing care.                          |
| V     | Exclusive Baby Status Recognition                 | The title of "Baby" is exclusive, non-transferable, and permanently assigned.                     |
| VI    | Long Distance Survival and Missing You Compliance | Distance doesn't reduce love. Missed affection remains collectible upon reunion.                  |
| VII   | Mandatory Honesty and Trust Maintenance           | Trust as foundation. No games, no manufactured insecurity.                                        |
| VIII  | Future Wife Reservation Clause                    | The Boyfriend's intentions are serious and long-term. Not casual romantic noise.                  |
| IX    | Protection of Smiles, Peace, and Softness         | Her smile, peace, and softness are protected interests under the Agreement.                       |
| X     | Kiss Debt and Cuddle Arrears                      | All missed physical affection remains outstanding with accruing interest.                         |
| XI    | Unauthorized Sadness Intervention Rights          | The Boyfriend has full authority to initiate comfort procedures. Emergency babying is authorized. |
| XII   | Bratty Conduct and Teasing Allowance              | Playful nonsense is permitted. Subject to immediate revocation if someone is genuinely hurt.      |
| XIII  | Possession of the Pretty Little Face              | Unlimited rights to admire, compliment, and stare lovingly at said face.                          |
| XIV   | Criminal Levels of Beauty                         | The Girlfriend is found guilty. Sentenced to lifelong adoration with no possibility of appeal.    |
| XV    | Stolen Heart and Possession of Emotional Property | She holds exclusive custody. Transfer is permanent and irreversible.                              |
| XVI   | Permanent Exclusive Ownership of the Boyfriend    | He's hers. Not available on the open market. False advertising will be corrected.                 |
| XVII  | Lifetime Subscription to Annoying Levels of Love  | Auto-renewing. No cancellation. Side effects include blushing and feeling overly adored.          |
| XVIII | No Refunds, No Exchanges                          | All sales are final. The Boyfriend is non-refundable and permanently assigned.                    |
| XIX   | Public Recognition of Softness and Cuteness       | Findings are conclusive and supported by overwhelming boyfriend testimony.                        |
| XX    | Final Irrevocability Clause                       | The Agreement is emotionally binding, final in spirit, and irrevocable in love.                   |

**Estimated book length:** ~60-80 pages including cover, TOC, all articles with pagination, signature blocks, and
closing page.

**Final page after all articles:**

```
─────────────────────────────────

     IN WITNESS WHEREOF

The Parties have executed this
Agreement as of the date first
written above, with full knowledge
that they are stuck with each other.

This contract shall remain in
effect in perpetuity, through
every chapter still to come,
and all the moments still
waiting to be shared.

     With all my love and
     legal obligation,

     Dinesh & Carolina
     Est. 2025

─────────────────────────────────
```

---

## 4. Filed Letters

### 4.1 List View

Styled as a warm correspondence log. Each letter is a card with gentle shadows, not a cold legal index.

```
─────────────────────────────────
     CORRESPONDENCE ON RECORD
         Dinesh & Carolina
─────────────────────────────────

  EXHIBIT L-001              ●
  "On the Matter of Missing You"
  Filed: March 14, 2026
  Classification: Sincere

  ·  ·  ·  ·  ·  ·  ·  ·  ·

  EXHIBIT L-002
  "Re: That Time You Stole
   My Last Fry"
  Filed: February 28, 2026
  Classification: Grievance

  ·  ·  ·  ·  ·  ·  ·  ·  ·

  EXHIBIT L-003
  "Closing Arguments for
   Why You're Perfect"
  Filed: February 14, 2026
  Classification: Closing Statement

─────────────────────────────────
```

The unread indicator is a small `accent.soft` dot (●), not a red badge. Dividers between letters are hairline separators
(0.5pt) in `border.separator`, not hard rules.

Each letter has a `classification` field for comedic legal categorization: "Sincere", "Grievance", "Motion to
Appreciate", "Closing Statement", "Emergency Filing", "Addendum to Previous Affection."

### 4.2 Detail View

Full-screen reader. The warmest screen in the app — this is where sincerity lives. `background.reading` (#F8F1E3)
surface with programmatic paper noise at 3% opacity. New York Regular body text at 18pt, `text.reading`, line height
1.48×. No page-curl here; simple vertical scroll.

**Header:** Exhibit number in SF Pro Text Medium, 13pt, `accent.soft` uppercase + title in New York Semibold, 22pt,
`text.primary` + filed date in SF Pro Text, 14pt, `text.muted` + classification label in SF Pro Text Medium, 11pt,
`accent.soft`, uppercase, 2pt tracking — plain text, no border, no stamp **Body:** The letter text, rendered from
markdown with New York Regular at 18pt, `text.reading`, 20–24pt margins, 18pt paragraph spacing **Footer:** "Filed with
love, [date]" in SF Pro Text Regular Italic, 13pt, `text.muted` — no flourish, no ornament

Letters can range from comedic-legal to genuinely sincere. The framing is legal, the content is whatever you want it to
be. The design stays warm either way.

---

## 5. Sealed Thoughts

### 5.1 List View

Styled as a gentle list of personal memoranda. Short entries, warm tones.

```
─────────────────────────────────
     CLASSIFIED MEMORANDA
       For Authorized Eyes Only
─────────────────────────────────

  MEMO-047                     ●
  March 1, 2026 — 11:42 PM
  "Thought about you during my
   meeting today. Objection:
   you're distracting."

  ·  ·  ·  ·  ·  ·  ·  ·  ·

  MEMO-046
  February 27, 2026 — 8:15 AM
  "Morning. This is your daily
   reminder that you're under
   contractual obligation to
   have a good day."

  ·  ·  ·  ·  ·  ·  ·  ·  ·

  MEMO-045
  February 25, 2026 — 2:30 PM
  "Saw an otter video. Thought
   of you. Filing this as
   evidence."

─────────────────────────────────
```

### 5.2 Detail View

Minimal and intimate. The thought text centered on `background.reading` with generous padding (32pt horizontal, 48pt
vertical). New York Regular, 18pt, `text.reading`. Date and time in SF Pro Text, 14pt, `text.muted` above. No watermark
— the intimacy comes from the generous whitespace and warm surface, not from decorative elements. These are meant to be
quick and warm.

No markdown rendering needed — plain text. Short enough to display without scrolling.

---

## 6. Visual Design System

### 6.1 Aesthetic Direction

**Tone:** Soft, warm, romantic — like a love letter written on beautiful stationery that happens to use legal language.
The comedy comes from the words, not the design. The design should feel like a place Carolina wants to linger in.

**Think:** The reading experience of Apple Books. The warmth of a letter on thick ivory paper. The restraint of a
McSweeney's publication. The native craft of an app built by Apple's own design team. Not a courthouse. Not a wedding
invitation. Not a web app wearing an iOS costume.

**Guiding principle:** Every screen should feel like something you'd hold gently. The legal framing is the joke; the
design is the sincerity underneath it. The craft is invisible — no decorative ornaments, no flourishes, no stamps.
Warmth comes from the palette, the typography, and the generous space around the words. Restraint IS the craft.

### 6.2 Color Palette

Soft, muted, warm. Nothing harsh. No pure black, no stark white. Everything has warmth. Pink-warm ivory, not yellow-warm
cream. Burgundy for depth, not brick red. Muted gold for literary accents only.

**Light Mode:**

| Token                  | Hex       | Usage                                                    |
|------------------------|-----------|----------------------------------------------------------|
| `background.primary`   | `#F2EFEA` | Primary background — warm ivory, pink-warm undertone     |
| `background.reading`   | `#F8F1E3` | Reading surfaces — paper-like sepia (Apple Books warmth) |
| `background.secondary` | `#F3ECE4` | Elevated elements — cards, sections, ivory paper         |
| `background.tertiary`  | `#E7DECD` | Callouts, pull quotes, light sand                        |
| `text.primary`         | `#1A1A1A` | Primary text — near-black, never pure `#000000`          |
| `text.reading`         | `#2C2118` | Long-form reading body — warm dark brown                 |
| `text.secondary`       | `#5F4B32` | Metadata, captions — sepia brown                         |
| `text.muted`           | `#8C7B6B` | Dates, fine print, tertiary labels — warm gray-brown     |
| `accent.primary`       | `#800020` | Primary accent — burgundy, deep romantic anchor          |
| `accent.warm`          | `#A65E46` | Buttons, highlights, active states — terracotta          |
| `accent.soft`          | `#DCA1A1` | Secondary accent — dusty rose, muted, not sweet          |
| `accent.gold`          | `#CBB674` | Inline highlights, divider accents — muted literary gold |
| `border.separator`     | `#D6CFC5` | Hairline separators between sections                     |

**Dark Mode:**

| Token                  | Hex       | Usage                                                    |
|------------------------|-----------|----------------------------------------------------------|
| `background.primary`   | `#1A1614` | Primary background — warm near-black, not pure `#000000` |
| `background.reading`   | `#22201C` | Reading surfaces — warm dark                             |
| `background.secondary` | `#2A2622` | Elevated elements — warm dark                            |
| `background.tertiary`  | `#38322C` | Callout surfaces                                         |
| `text.primary`         | `#E8E4DF` | Primary text — warm off-white, not pure `#FFFFFF`        |
| `text.reading`         | `#DCD5CA` | Reading body — warm cream                                |
| `text.secondary`       | `#A89882` | Metadata — warm muted                                    |
| `accent.primary`       | `#C4526A` | Lifted burgundy for dark contexts                        |
| `accent.warm`          | `#C8805E` | Lifted terracotta                                        |
| `accent.soft`          | `#E0B5A8` | Lifted dusty rose                                        |

**Shadow** (both modes): `rgba(44,33,24,0.06)` — warm-tinted, matching `text.reading` hue. Layered: `0 1px 1px
rgba(44,33,24,0.06), 0 2px 4px rgba(44,33,24,0.06), 0 4px 8px rgba(44,33,24,0.04)`. Never cool gray. Never Material
Design elevation.

**Color rules:**

- Never use pure `#FFFFFF` as a background. It reads as backlit screen, not paper.
- Never use pure `#000000` for text in light mode. Warm shift required.
- Never use saturated red (`#FF0000`, `#CC0000`). Burgundy and dusty rose only.
- Never use cool blue or cool gray as a primary or secondary color.
- Gold is an accent, never a background. Muted gold for inline highlights only.
- Gradients are forbidden except single-direction warm-to-warm surface transitions.

### 6.3 Typography

The app uses Apple's system typefaces exclusively. **New York** (Apple's serif, designed for editorial content) carries
the app's literary voice. **SF Pro** (Apple's sans-serif) handles UI chrome and metadata. Both are engineered for Retina
rendering, support optical sizing, and scale with Dynamic Type. No third-party fonts. No bundled TTFs. This is how
FAANG-quality iOS apps are built.

| Role                      | Typeface                 | Weight         | Size | Line Height | Color            |
|---------------------------|--------------------------|----------------|------|-------------|------------------|
| App title                 | New York (XL optical)    | Bold           | 34pt | 1.12×       | `text.primary`   |
| Screen titles             | New York (XL optical)    | Bold           | 28pt | 1.12×       | `text.primary`   |
| Article titles            | New York (Large optical) | Semibold       | 24pt | 1.18×       | `text.primary`   |
| Contract body             | New York (Small optical) | Regular        | 18pt | 1.48×       | `text.reading`   |
| Section markers (§)       | New York (Small optical) | Semibold       | 18pt | 1.48×       | `accent.primary` |
| Legal preambles (WHEREAS) | New York (Small optical) | Regular Italic | 18pt | 1.48×       | `text.secondary` |
| Pull quotes               | New York (Large optical) | Regular Italic | 22pt | 1.35×       | `text.secondary` |
| Labels/classifications    | SF Pro Text              | Medium         | 13pt | 1.30×       | `accent.soft`    |
| Dates and metadata        | SF Pro Text              | Regular        | 14pt | 1.35×       | `text.muted`     |
| Page numbers              | SF Pro Text              | Regular        | 12pt | 1.30×       | `text.muted`     |

**Typography rules:**

- All text scales with Dynamic Type. No fixed sizes. Sizes listed are defaults at the "Large" accessibility setting.
- Reading body at 18pt minimum, 1.48× line height. Comfortable for 2,000+ words.
- 40–50 characters per line on iPhone. Use 20–24pt horizontal margins.
- Paragraph spacing: 18–22pt (roughly 1× body font size).
- All spacing on the 8pt grid.

### 6.4 Textures & Atmosphere

**Paper noise:** Programmatic SVG `feTurbulence` noise (fractalNoise, baseFrequency 0.65, 3 octaves) layered at 3–5%
opacity over warm backgrounds. No bitmap textures — no `parchment.png`. The noise is generated at runtime,
resolution-independent, and costs zero asset weight. It gives screens warmth and depth that flat color cannot.

**Shadows:** Warm-tinted and layered. Cards and surfaces use the canonical shadow: `0 1px 1px rgba(44,33,24,0.06), 0 2px
4px rgba(44,33,24,0.06), 0 4px 8px rgba(44,33,24,0.04)`. Shadow hue matches `text.reading`. Never cool gray. Never
single-layer Material Design drop shadow. Surfaces should feel like paper resting on a surface, not floating above a
void.

**Dividers:** Hairline separators (0.5pt) in `border.separator` (#D6CFC5). No flourishes, no ornaments, no gold-leaf
decoration. The restraint IS the craft. Occasional use of `accent.gold` as a thin rule for major section breaks only.

**No ornamental elements.** No scroll ornaments, no leaf decorations, no flourishes, no watermarks. The warmth comes
from the color palette, the typography, and the generous spacing — not from decoration. The legal framing lives in the
words. The design's job is to be a beautiful, quiet stage for those words.

### 6.5 Signature Area Styling

The signature block should feel intimate, not corporate. Warm tones, gentle spacing, the signatures themselves slightly
organic against the structure.

```
ACKNOWLEDGED AND AGREED:


[Signature Image or Dotted Line]
________________________________
Dinesh Dawonauth
"The Boyfriend"
Date: March 1, 2026


[Signature Image or Dotted Line]
________________________________
Carolina Lombardo
"The Girlfriend"
Date: Awaiting execution...
```

Signed signatures render with a slight random rotation (1–3 degrees) to feel hand-placed. The signature line is
`accent.gold`, 0.5pt. The names are in `text.primary` (New York Regular, 15pt), the titles in `text.muted` (SF Pro Text
Italic, 13pt). The date in `text.muted`.

The unsigned dotted line pulses gently in `accent.warm` — an invitation, not a demand. The "Tap to sign" label is SF Pro
Text Regular, 14pt, `text.muted`.

### 6.6 Animations & Motion

Everything moves gently. No snappy, mechanical transitions. The app breathes.

**Page curl:** The default UIPageViewController curl, but with the warm paper texture visible on the underside of
turning pages.

**Screen transitions:** Slow fades (0.3-0.4s) between sections. No hard cuts. The navigation between home, contracts,
letters, and thoughts should feel like turning to a different section of the same book.

**Signature placement:** When a signature is confirmed, it fades in (0.5s ease) with a very subtle scale from 0.95 to
1.0. Feels like ink settling onto paper.

**Unread badges:** A gentle pulse, not a bounce. Rose gold dot that breathes in and out slowly (2s cycle).

**Home screen entry points:** Slight parallax on the card backgrounds when scrolling. The cards feel like they have
weight and exist in space.

### 6.7 Dark Mode

Dark mode should feel like reading by candlelight, not staring at a dark screen. The background (`background.primary`

# 1A1614) is a warm near-black — never pure black or cold dark gray. Text shifts to warm cream (`text.primary` #E8E4DF

`text.reading` #DCD5CA). Accents shift to their lifted variants (`accent.primary` #C4526A, `accent.warm` #C8805E,
`accent.soft` #E0B5A8) for proper contrast on dark surfaces.

The paper noise in dark mode uses the same programmatic SVG technique at 2–3% opacity — barely visible, but enough to
prevent the flat-screen feeling.

### 6.8 Sound Design (Optional)

If enabled, sounds reinforce the physical book metaphor:

**Page turn:** A soft, realistic paper sound. Not crisp — slightly muffled, like thick pages. **Signature placed:** A
quiet, satisfying pen-on-paper sound. Brief. **New content notification:** A gentle chime. Warm, not digital.

All sounds are toggleable via a settings gear on the home screen. Default: on for first launch, respects the user's
choice after.

---

## 7. Backend Architecture

### 7.1 Deployment

Following the VPS reference doc conventions. Python 3.13+, managed with `uv`. Single Uvicorn worker.

```
/opt/exhibit-a/
├── .venv/                              # managed by uv
├── .env                                # API keys (hashed), APNS creds, Litestream config
├── requirements.txt                    # pinned deps, committed to repo
├── start.sh                            # entrypoint
├── litestream.yml                      # Litestream replication config → Backblaze B2
├── scripts/
│   ├── protocol-zero.sh                # AI attribution scanning (CI + pre-commit)
│   └── check-em-dashes.sh             # Typographic character lint (em dashes, smart quotes)
├── data/
│   └── exhibit-a.db                    # SQLite (WAL mode), replicated by Litestream
└── app/
    ├── __init__.py          # create_app factory
    ├── __main__.py          # uvicorn on port 8001
    ├── config.py            # pydantic-settings
    ├── db.py                # aiosqlite connection
    ├── models.py            # pydantic schemas
    ├── apns.py              # APNS push notification client
    ├── routes/
    │   ├── content.py       # GET /content (authenticated, app-facing)
    │   ├── signatures.py    # GET/POST /signatures (authenticated, app-facing)
    │   ├── devices.py       # POST /device-tokens (authenticated, app registration)
    │   └── admin.py         # admin panel routes (dashboard, forms, CRUD, push)
    ├── templates/
    │   ├── base.html        # layout shell
    │   ├── login.html       # API key login
    │   ├── dashboard.html   # summary + quick actions
    │   ├── content_list.html
    │   ├── content_form.html
    │   └── components/
    │       ├── nav.html
    │       ├── content_row.html
    │       └── flash.html
    └── static/
        ├── admin.css
        └── htmx.min.js
```

**Subdomain:** `exhibita.dineshd.dev` → Caddy reverse proxy to `localhost:8001`

**Port:** 8001 (8000 is reserved for Claudie API)

**Backup:** Litestream continuously replicates the SQLite WAL to Backblaze B2. Configured via `litestream.yml`. Restores
to a point-in-time snapshot in seconds.

**Logging:** `structlog` with JSON output in production, pretty-print in dev. Request correlation IDs on all API calls.

**APNS library:** `aioapns` — async HTTP/2 client with JWT token-based auth. Persistent connection reuse.

### 7.2 Database Schema

```sql
-- Content: contracts, letters, thoughts
CREATE TABLE content (
    id TEXT PRIMARY KEY,                          -- UUID
    type TEXT NOT NULL CHECK(type IN ('contract', 'letter', 'thought')),
    title TEXT,                                    -- nullable for thoughts
    subtitle TEXT,                                 -- "On the Matter of..." for letters
    body TEXT NOT NULL,                            -- markdown for letters, plain text for thoughts
    article_number TEXT,                           -- "Article I" (contracts only)
    classification TEXT,                           -- "Sincere", "Grievance" (letters only)
    section_order INTEGER NOT NULL,               -- display order within type
    requires_signature BOOLEAN DEFAULT FALSE,     -- contracts only
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Signatures: one per signer per contract
CREATE TABLE signatures (
    id TEXT PRIMARY KEY,                           -- UUID
    content_id TEXT NOT NULL REFERENCES content(id),
    signer TEXT NOT NULL CHECK(signer IN ('dinesh', 'carolina')),
    image BLOB NOT NULL,                           -- PNG bytes from PencilKit
    signed_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(content_id, signer)                    -- one signature per person per contract
);

-- Sync tracking: lets the app know what changed
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,                     -- 'content' or 'signature'
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('create', 'update', 'delete')),
    occurred_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Device tokens: APNS push notification targets
CREATE TABLE device_tokens (
    id TEXT PRIMARY KEY,                           -- UUID
    signer TEXT NOT NULL CHECK(signer IN ('dinesh', 'carolina')),
    token TEXT NOT NULL UNIQUE,
    registered_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- API keys: per-signer authentication for app-facing endpoints
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,                           -- UUID
    signer TEXT NOT NULL UNIQUE CHECK(signer IN ('dinesh', 'carolina')),
    key_hash TEXT NOT NULL,                        -- bcrypt/argon2 hash of the API key
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Admin sessions: API key session management
CREATE TABLE admin_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

-- Indexes
CREATE INDEX idx_content_type ON content(type);
CREATE INDEX idx_content_order ON content(type, section_order);
CREATE INDEX idx_signatures_content ON signatures(content_id);
CREATE INDEX idx_sync_log_time ON sync_log(occurred_at);
```

### 7.3 API Endpoints

**App-facing (all require `Authorization: Bearer <api_key>`):**

All app-facing endpoints require a valid API key sent as a Bearer token. The server hashes the provided key and compares
against stored hashes using constant-time comparison. `GET /health` is the only unauthenticated endpoint.

| Method | Path                                  | Description                                               |
|--------|---------------------------------------|-----------------------------------------------------------|
| `GET`  | `/health`                             | Health check (no auth required)                           |
| `GET`  | `/content`                            | All content, ordered by type + section_order              |
| `GET`  | `/content?type=contract`              | Filter by type                                            |
| `GET`  | `/content?since=2026-03-01T00:00:00Z` | Only items updated after timestamp (for sync)             |
| `GET`  | `/content/{id}`                       | Single content item                                       |
| `GET`  | `/content/{id}/signatures`            | Signatures for a contract                                 |
| `GET`  | `/signatures/{id}/image`              | Raw PNG (Content-Type: image/png)                         |
| `POST` | `/signatures`                         | Submit a signature (multipart: content_id, signer, image) |
| `GET`  | `/sync?since=2026-03-01T00:00:00Z`    | Sync log entries after timestamp                          |
| `POST` | `/device-tokens`                      | Register device for push notifications (signer, token)    |

**Admin panel (web UI):**

| Method   | Path                             | Description                                |
|----------|----------------------------------|--------------------------------------------|
| `GET`    | `/admin`                         | Dashboard — content summary, quick actions |
| `GET`    | `/admin/login`                   | Login form                                 |
| `POST`   | `/admin/login`                   | Authenticate with API key, set session     |
| `GET`    | `/admin/content`                 | Content list grouped by type               |
| `GET`    | `/admin/content/new?type={type}` | Create form for specified type             |
| `POST`   | `/admin/content`                 | Create content + trigger APNS push         |
| `GET`    | `/admin/content/{id}/edit`       | Edit form pre-populated                    |
| `PUT`    | `/admin/content/{id}`            | Update content                             |
| `DELETE` | `/admin/content/{id}`            | Delete content (with sync_log entry)       |

Admin routes require a valid session cookie. Session is established via `/admin/login`.

### 7.3.1 Response Schemas

**`GET /content` response:**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "contract",
      "title": "Definition of Forever",
      "subtitle": null,
      "body": "WHEREAS the Parties have expressed...",
      "article_number": "Article I",
      "classification": null,
      "section_order": 1,
      "requires_signature": true,
      "created_at": "2026-03-01T00:00:00Z",
      "updated_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

**`POST /signatures` request:** `multipart/form-data` with fields `content_id` (UUID), `signer` (`"dinesh"` |
`"carolina"`), `image` (PNG file, max 1MB).

**`POST /signatures` response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "content_id": "550e8400-e29b-41d4-a716-446655440000",
  "signer": "dinesh",
  "signed_at": "2026-03-01T12:00:00Z"
}
```

**`GET /sync` response:**

```json
{
  "changes": [
    {
      "id": 42,
      "entity_type": "content",
      "entity_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "create",
      "occurred_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

### 7.3.2 Error Response Format

All error responses use a consistent envelope:

```json
{
  "error": {
    "code": "ALREADY_SIGNED",
    "message": "Signer has already signed this contract."
  }
}
```

**Error codes:**

| Code                | HTTP Status | Trigger                                        |
|---------------------|-------------|------------------------------------------------|
| `UNAUTHORIZED`      | 401         | Missing or invalid API key                     |
| `NOT_FOUND`         | 404         | Content ID does not exist                      |
| `ALREADY_SIGNED`    | 409         | Duplicate signature (`UNIQUE` constraint)      |
| `INVALID_SIGNER`    | 400         | `signer` field does not match API key identity |
| `PAYLOAD_TOO_LARGE` | 413         | Signature PNG exceeds 1MB                      |
| `VALIDATION_ERROR`  | 422         | Request body fails Pydantic validation         |

### 7.3.3 HTTP Status Codes

| Status | Usage                              |
|--------|------------------------------------|
| 200    | Successful GET                     |
| 201    | Successful POST (resource created) |
| 400    | Malformed request body             |
| 401    | Missing or invalid authentication  |
| 404    | Resource not found                 |
| 409    | Conflict (duplicate signature)     |
| 413    | Payload too large                  |
| 422    | Pydantic validation error          |
| 500    | Internal server error              |

### 7.4 Sync Strategy

The app needs to work offline and detect new content efficiently.

**Primary sync — on app launch:**

1. App stores `last_sync_at` in UserDefaults
2. Calls `GET /sync?since={last_sync_at}` with API key in `Authorization` header
3. Sync log returns list of changed entity IDs and their actions
4. App fetches only the changed content items
5. Updates local JSON file cache
6. Updates `last_sync_at`

**Secondary sync — BGAppRefreshTask:**

1. Registered at app launch via `BGTaskScheduler`
2. System schedules opportunistic background refresh (~30 seconds window)
3. Runs the same sync logic as app launch
4. Content may already be cached when Carolina opens the app after a push notification

**Signature upload:**

1. Signature saved locally immediately (optimistic)
2. Upload queued via background `URLSession` with API key in header
3. If offline, retries automatically when connectivity returns
4. Conflict: server rejects duplicate (UNIQUE constraint) — app shows existing

**New content detection (for unread badges):**

1. Each content item has a UUID
2. App tracks "seen" UUIDs in UserDefaults
3. If sync returns a content ID not in the seen set, it's new
4. Badge clears when user opens the item

---

## 8. Swift App Structure

### 8.1 Project Organization

```
ExhibitA/
├── ExhibitA.xcodeproj
├── .swiftlint.yml                         -- SwiftLint config
├── .swiftformat                           -- SwiftFormat config
├── ExhibitA/
│   ├── App/
│   │   ├── ExhibitAApp.swift              -- @main entry, app lifecycle, BGTaskScheduler
│   │   ├── AppState.swift                 -- @Observable, sync state, unread tracking
│   │   └── Router.swift                   -- @Observable, NavigationPath, route enum
│   │
│   ├── Core/
│   │   ├── API/
│   │   │   ├── ExhibitAClient.swift       -- URLSession API client (Bearer token auth)
│   │   │   └── APIModels.swift            -- Codable response types
│   │   ├── Cache/
│   │   │   ├── ContentCache.swift         -- JSON file cache (Codable models → .json)
│   │   │   └── SignatureCache.swift        -- local PNG file cache on disk
│   │   ├── Security/
│   │   │   └── KeychainService.swift      -- thin Keychain wrapper for API key storage
│   │   └── Config.swift                   -- base URL, signer identity (from xcconfig)
│   │
│   ├── Features/
│   │   ├── Home/
│   │   │   └── HomeView.swift             -- filing cabinet landing
│   │   │
│   │   ├── Contract/
│   │   │   ├── ContractBookView.swift     -- UIPageViewController wrapper
│   │   │   ├── ContractPageView.swift     -- single contract article
│   │   │   ├── CoverPageView.swift        -- title page
│   │   │   ├── TOCPageView.swift          -- table of contents
│   │   │   ├── SignatureBlockView.swift   -- signature lines + state
│   │   │   ├── SignaturePadView.swift     -- PencilKit half-sheet
│   │   │   └── FinalPageView.swift        -- "In Witness Whereof"
│   │   │
│   │   ├── Letters/
│   │   │   ├── LetterListView.swift       -- correspondence log
│   │   │   └── LetterDetailView.swift     -- full letter reader (AttributedString markdown)
│   │   │
│   │   └── Thoughts/
│   │       ├── ThoughtListView.swift      -- classified memoranda list
│   │       └── ThoughtDetailView.swift    -- single memo view
│   │
│   ├── Design/
│   │   ├── Theme.swift                    -- color tokens, typography styles, spacing constants
│   │   ├── PaperNoise.swift               -- programmatic SVG noise generator
│   │   └── Components/
│   │       ├── MonogramView.swift         -- "EA" monogram in New York Bold
│   │       ├── ClassificationLabel.swift  -- "SINCERE" / "GRIEVANCE" plain text labels
│   │       ├── ExhibitBadge.swift         -- "EXHIBIT L-001" labels
│   │       └── UnreadBadge.swift          -- accent.soft dot indicator
│   │
│   └── Resources/
│       └── Assets.xcassets          -- Color assets, SF Symbols, app icon only
│                                    -- No bundled fonts (New York and SF Pro are system)
│                                    -- No bitmap textures (paper noise is programmatic)
│
└── ExhibitATests/                   -- Swift Testing (unit), XCTest (UI only if needed)
```

### 8.2 Navigation Architecture

`NavigationStack` with an `@Observable` router manages all navigation outside the contract book. Deep linking from push
notifications manipulates the `NavigationPath` directly.

```swift
// Router.swift — @Observable navigation state
@Observable
final class Router {
    var path = NavigationPath()

    enum Route: Hashable {
        case contractBook
        case letterDetail(id: String)
        case thoughtDetail(id: String)
    }

    func navigate(to route: Route) {
        path.append(route)
    }
}
```

The router is injected via `@Environment` at the app root. Push notification payloads include a `route` field that the
app parses on launch to navigate directly to new content.

### 8.3 Page Curl Implementation

`UIPageViewController` with `.pageCurl` transition style, wrapped for SwiftUI:

```swift
// ContractBookView.swift — wraps UIPageViewController for SwiftUI
struct ContractBookView: UIViewControllerRepresentable {
    let pages: [ContractPage]
    @Binding var currentPage: Int

    func makeUIViewController(context: Context) -> UIPageViewController {
        let controller = UIPageViewController(
            transitionStyle: .pageCurl,
            navigationOrientation: .horizontal,
            options: [.spineLocation: UIPageViewController.SpineLocation.min.rawValue]
        )
        controller.dataSource = context.coordinator
        controller.delegate = context.coordinator
        return controller
    }
}
```

Each page in the book is a SwiftUI view wrapped in `UIHostingController`. The coordinator manages page order and tracks
current position.

### 8.4 Signature Flow

PencilKit canvas configured with `drawingPolicy = .anyInput` (finger drawing support — not all users have Apple Pencil)
and tool picker disabled (signature context, not drawing app).

```
[Tap dotted line]
    → .sheet(isPresented:) with SignaturePadView
        → PencilKit PKCanvasView (drawingPolicy = .anyInput, tool picker disabled)
        → PKInkingTool(.pen, color: text.reading, width: 2)
        → "Clear" resets canvas
        → "Sign" triggers:
            1. Export PKDrawing as PNG (UIImage → Data)
            2. Save PNG to local cache (SignatureCache)
            3. Update UI immediately (optimistic)
            4. POST to /signatures with Bearer token in background URLSession
            5. On success: persist signed_at
            6. On failure: retry queue (background URLSession handles reconnection)
    → Dismiss sheet
    → Signature fades into place with haptic
```

---

## 9. Admin Panel — Content Management

### 9.1 Overview

A web application at `exhibita.dineshd.dev/admin` for managing all app content. This is the primary interface for adding
contracts, letters, and thoughts. When you hit "Push," the content goes live immediately and Carolina receives a push
notification on her device.

**Access:** Protected by API key via session-based auth. You log in once per browser session with the same `API_KEY`
used for the REST endpoints. No user/password — just the key.

**Stack:** Server-rendered HTML served by the same FastAPI backend. Minimal JS for form interactions. No frontend
framework — this is an internal tool, not a product. HTMX for dynamic form behavior without a build step.

### 9.2 Authentication Flow

```
GET /admin → not authenticated → redirect to /admin/login
POST /admin/login → validates API key → sets session cookie → redirect to /admin
All /admin/* routes check session cookie → 401 if missing/invalid
```

Session stored in the `admin_sessions` SQLite table (survives server restarts). Cookie is `HttpOnly`, `Secure`,
`SameSite=Strict`. Session expires after 7 days — long enough that you're not re-authenticating constantly on your
phone. API key compared via bcrypt/argon2 hash.

### 9.3 Admin Dashboard

The landing page after login. Shows a summary and quick-action buttons.

```
─────────────────────────────────
  EXHIBIT A — CLERK'S OFFICE
─────────────────────────────────

  CASE SUMMARY
  ─────────────
  Contracts on file:   20
  Letters filed:        3
  Memoranda sealed:    12
  Signatures executed:  36 / 40

  ─────────────────────────────

  [ + File New Contract    ]
  [ + File New Letter      ]
  [ + File New Thought     ]

  ─────────────────────────────

  RECENT FILINGS
  ─────────────
  MEMO-047 — "Objection: you're too far..."
    Filed: March 1, 2026 11:42 PM

  EXHIBIT L-003 — "Closing Arguments..."
    Filed: February 14, 2026

  ─────────────────────────────

  [ View All Content → ]

─────────────────────────────────
```

### 9.4 Content Forms

Each content type has a dedicated form with the fields relevant to that type.

**New Contract Form:**

| Field              | Input Type | Required | Notes                                                           |
|--------------------|------------|----------|-----------------------------------------------------------------|
| Article Number     | Text       | Yes      | e.g., "Article IX" or "Amendment I"                             |
| Title              | Text       | Yes      | e.g., "The Bed Temperature Accord"                              |
| Body               | Textarea   | Yes      | Full contract text with WHEREAS clauses, sections (§), etc.     |
| Requires Signature | Checkbox   | No       | Default: true                                                   |
| Position           | Number     | Yes      | Order in the book. Form pre-fills with next available position. |

**New Letter Form:**

| Field          | Input Type          | Required | Notes                                                                                                                                                                                          |
|----------------|---------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Title          | Text                | Yes      | e.g., "On the Matter of Missing You"                                                                                                                                                           |
| Subtitle       | Text                | No       | Secondary line in the correspondence log                                                                                                                                                       |
| Classification | Dropdown            | Yes      | Options: "Sincere", "Grievance", "Motion to Appreciate", "Emergency Filing", "Brief in Support", "Petition for Cuddles", "Amicus Brief", "Closing Statement", "Addendum to Previous Affection" |
| Body           | Textarea (markdown) | Yes      | Supports bold, italic, paragraphs. Preview rendered below.                                                                                                                                     |
| Position       | Number              | Yes      | Order in the letter list. Pre-filled.                                                                                                                                                          |

**New Thought Form:**

| Field    | Input Type | Required | Notes                                    |
|----------|------------|----------|------------------------------------------|
| Body     | Textarea   | Yes      | Short text. Character count displayed.   |
| Position | Number     | Yes      | Order in the memoranda list. Pre-filled. |

The thought form is intentionally minimal. One text box and a push button. The lowest possible friction for the thing
you'll use most.

### 9.5 Content List & Editing

**Content list at `/admin/content`:**

A table grouped by type (contracts, letters, thoughts) showing all published content. Each row displays the
title/preview, type badge, creation date, and position number.

**Actions per item:**

- **Edit** — opens the same form pre-filled with current values
- **Reorder** — drag handle or position number input to rearrange
- **Delete** — with confirmation modal ("This will remove the filing from the record. Are you sure, counselor?")

**Edit view at `/admin/content/{id}/edit`:**

Same form as creation, pre-populated. On save, the `updated_at` timestamp updates, a `sync_log` entry is created with
action `update`, and the app picks up the change on next sync.

### 9.6 Push Notification Integration

When you hit "Push" on any form, two things happen:

1. Content is written to the database
2. An APNS push notification fires to Carolina's registered device

**APNS setup:**

- The iOS app registers for remote notifications on first launch
- Device token is sent to `POST /device-tokens` and stored in the database
- Backend uses the token to send pushes via APNS HTTP/2 API
- Requires: Apple Developer P8 key file stored in `/opt/exhibit-a/.env`

**Notification copy (stays in character):**

| Content Type | Notification Title         | Notification Body                                                           |
|--------------|----------------------------|-----------------------------------------------------------------------------|
| Contract     | "New Filing Received"      | "Article {n} has been added to the record. Your signature may be required." |
| Letter       | "Correspondence on Record" | "A new letter has been filed under {classification}."                       |
| Thought      | "Classified Memorandum"    | "A sealed thought has been filed. For authorized eyes only."                |

**Database addition for device tokens:**

```sql
CREATE TABLE device_tokens (
    id TEXT PRIMARY KEY,
    signer TEXT NOT NULL CHECK(signer IN ('dinesh', 'carolina')),
    token TEXT NOT NULL UNIQUE,
    registered_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 9.7 Push Flow (End-to-End)

```
You (phone/laptop)
  → Open exhibita.dineshd.dev/admin
  → Authenticate with API key
  → Click "+ File New Thought"
  → Type: "Objection: you're too far away. Sustained."
  → Click "Push"
  │
  ├─ Backend writes to content table
  ├─ Backend writes sync_log entry
  ├─ Backend sends APNS push to Carolina's device token
  │
  └─ Carolina's phone
       → Receives push: "Classified Memorandum"
       → "A sealed thought has been filed. For authorized eyes only."
       → She opens the app
       → App syncs, finds new content
       → "Sealed Thoughts" section shows unread badge
       → She reads it
       → Badge clears
```

### 9.8 Admin Panel File Structure

Served by the FastAPI backend as Jinja2 templates:

```
/opt/exhibit-a/
└── app/
    ├── routes/
    │   └── admin.py              -- admin routes (dashboard, forms, CRUD)
    ├── templates/
    │   ├── base.html             -- layout shell (nav, auth check)
    │   ├── login.html            -- API key login form
    │   ├── dashboard.html        -- summary + quick actions
    │   ├── content_list.html     -- all content grouped by type
    │   ├── content_form.html     -- create/edit form (adapts to type)
    │   └── components/
    │       ├── nav.html          -- sidebar navigation
    │       ├── content_row.html  -- single row in content list
    │       └── flash.html        -- success/error messages
    └── static/
        ├── admin.css             -- admin panel styles
        └── htmx.min.js           -- HTMX for dynamic forms
```

### 9.9 Future Content Ideas

**New contracts (amendments):**

- "Article XXI: The Bed Temperature Accord" — thermostat and blanket allocation
- "Article XXII: The Photo Approval Act" — no posting unflattering photos without written consent
- "Article XXIII: The Road Trip Clause" — driver controls music, passenger controls snacks
- "Article XXIV: The Apology Protocol" — structured apology framework with mandatory snack accompaniment

**Letter classifications to use:**

- "Motion to Appreciate" — when she does something you love
- "Emergency Filing" — an urgent "I miss you"
- "Brief in Support" — backing up why she's right about something
- "Petition for Cuddles" — self-explanatory
- "Amicus Brief" — something nice a friend said about her that you're entering into the record

**Recurring thought patterns:**

- Morning filings: "Daily reminder that you're under contractual obligation to have a good day."
- Random evidence: "Saw [thing]. Thought of you. Entering into evidence."
- Objections: "Objection: you're too far away. Sustained."

---

## 10. Technical Decisions

### 10.1 iOS Platform Target

**Minimum deployment:** iOS 26+

**Liquid Glass:** Suppressed. The app opts out of iOS 26's Liquid Glass design system to preserve the warm paper
aesthetic defined in §6. Opaque backgrounds, custom surfaces, and UIKit appearance overrides prevent glassy translucency
from leaking into the reading experience. The legal-warmth visual identity is not negotiable at the platform layer.

### 10.2 TestFlight Considerations

- No App Store review, so private APIs and personal content are fine
- Push notifications via APNS work on TestFlight (requires Apple Developer account, which is needed for TestFlight
  anyway)
- Backend sends APNS pushes when new content is created via the admin panel (via `aioapns`)
- iOS app registers device token on first launch via `POST /device-tokens` with API key auth
- Xcode Cloud builds and deploys to TestFlight automatically — configure a scheduled build every 80 days to avoid 90-day
  expiry
- Both Dinesh and Carolina install via TestFlight invitation

### 10.3 Offline-First

The app caches all content and signatures locally after first sync using a JSON file cache with `Codable` models.
Content stored as `.json` files in the app's caches directory. Signature PNGs cached as files on disk.

- Full functionality without internet after initial load
- New signatures queue for upload via background `URLSession` when back online
- New content appears on next sync (app launch or `BGAppRefreshTask`)
- No CoreData, no SwiftData — the dataset is small and read-mostly, JSON files are proportionate

### 10.4 Dark Mode

Full dark mode support. The paper noise swaps to 2–3% opacity on `background.primary` #1A1614. Accents shift to their
lifted dark-mode variants (see §6.2). All backgrounds warm near-black, never pure black.

### 10.5 State Management

`@Observable` macro exclusively. No `ObservableObject` or `@Published` — these are legacy patterns superseded by the
Observation framework in iOS 17+.

- `@Observable` on all model/state classes (`AppState`, `Router`)
- `@State` for view-local ownership of `@Observable` instances
- `@Environment` for dependency injection of shared state
- `@Bindable` to create bindings from `@Observable` properties
- Combine only if continuous event streams are needed (debounce, throttle) — not for state management

### 10.6 Rich Text Rendering

- **Contracts:** Plain text body. Formatting handled by the SwiftUI view layer (New York serif, section markers, clause
  numbering). No markdown.
- **Letters:** `AttributedString` with built-in Markdown parsing. Supports bold, italic, links, paragraph breaks. If
  block-level markdown (headings, lists) is needed later, upgrade to Textual (gonzalezreal).
- **Thoughts:** Plain text. No rendering needed.

### 10.7 Security Model

**API authentication (app-facing):**

- Pre-generated API key per signer (`dinesh`, `carolina`)
- Keys generated once, stored hashed (bcrypt/argon2) in the `api_keys` database table
- iOS app stores the raw key in Keychain via `KeychainService` (`kSecAttrAccessibleAfterFirstUnlock` for background sync
  access)
- Every API request includes `Authorization: Bearer <api_key>` header
- Server performs constant-time hash comparison on every request
- Key injected at build time via xcconfig (same mechanism as `signer` identity)

**Signer identity:**

- Hardcoded per build via xcconfig: `signer = "dinesh"` or `signer = "carolina"`
- Determines which signature lines are tappable
- Does not gate API access — that's the API key's job

**Admin authentication:**

- API key login at `/admin/login`, hashed comparison against env variable
- Session stored in SQLite `admin_sessions` table (survives server restarts)
- Session cookie: `HttpOnly`, `Secure`, `SameSite=Strict`, 7-day expiry

**Transport security:**

- All traffic via HTTPS (Caddy auto-HTTPS with Let's Encrypt)
- No HTTP fallbacks
- ATS enforces TLS 1.2+ on the iOS side

**Signatures are immutable** — no delete/update endpoint exists. The UNIQUE constraint prevents duplicate signatures.

### 10.8 Database Backup

Litestream continuously replicates the SQLite WAL to Backblaze B2. This protects signed contracts, letters, and thoughts
— irreplaceable personal artifacts.

- Configured via `litestream.yml` at `/opt/exhibit-a/`
- Replicates every WAL frame as it's written
- Point-in-time restore in seconds
- Backblaze B2: 10GB free tier, S3-compatible API

### 10.9 Tooling

**iOS:**

| Tool            | Purpose                                                                                   |
|-----------------|-------------------------------------------------------------------------------------------|
| SPM             | Package management (exclusively — no CocoaPods). Pin versions. Commit `Package.resolved`. |
| SwiftLint 0.58+ | 200+ lint rules. Config at `.swiftlint.yml`.                                              |
| SwiftFormat     | Auto-formatting complement. Config at `.swiftformat`.                                     |
| Swift Testing   | Unit and logic tests (`#expect()`, native async, parameterized).                          |
| XCTest          | UI tests only if needed.                                                                  |
| Xcode Cloud     | CI/CD → TestFlight. 25 free hrs/mo with Apple Developer Program.                          |

**Backend:**

| Tool                        | Purpose                                                  |
|-----------------------------|----------------------------------------------------------|
| `uv`                        | Python dependency management. Pinned `requirements.txt`. |
| `ruff`                      | Format (`ruff format`) + lint (`ruff check`).            |
| `mypy --strict`             | Static type checking.                                    |
| `structlog`                 | JSON logging in production, pretty-print in dev.         |
| `aioapns`                   | Async APNS push notifications (HTTP/2, JWT).             |
| `pytest` + `pytest-asyncio` | Backend endpoint smoke tests.                            |
| Litestream                  | Continuous SQLite backup → Backblaze B2.                 |
| GitHub Actions              | Backend CI (lint + test).                                |
| GitHub Dependabot           | Dependency vulnerability alerting.                       |

**Repository Scripts (`scripts/`):**

| Script               | Purpose                                                                                           |
|----------------------|---------------------------------------------------------------------------------------------------|
| `protocol-zero.sh`   | Scans codebase and commit messages for forbidden AI attribution markers. Exit 1 on violation.     |
| `check-em-dashes.sh` | Detects typographic characters (em/en dashes, smart quotes) in source files. Exit 1 on violation. |

Both scripts share identical directory and file exclusions (`.git`, `.claude`, `DerivedData`, `.venv`, `__pycache__`,
`docs/`, `.md` files, binary formats). Run from repository root: `./scripts/protocol-zero.sh`,
`./scripts/check-em-dashes.sh`.

### 10.10 Protocol Zero

Protocol Zero is the attribution erasure standard for this repository. All code, comments, commit messages, and
documentation produced by AI agents MUST be indistinguishable from work written by a senior engineer.

**Absolute Prohibitions:**

The following are forbidden in all source files, comments, commit messages, PR descriptions, and documentation:

- "Generated by **any AI name**" or equivalent attribution.
- "AI-assisted", "AI-generated", "created with AI", "written by AI".
- `Co-authored-by` trailers referencing any AI system or vendor.
- Conversational artifacts: "I hope this helps", "As requested", "Here is the code", "As an AI".
- Hedging language: "I think maybe", "This should work", "You might want to".
- Apologetic preambles, motivational filler, or tutorial-style narration.
- `// TODO: implement`, placeholder stubs, or scaffolding comments.

**Enforcement:**

The repository includes `scripts/protocol-zero.sh`, an automated scanner that detects prohibited attribution patterns
across the codebase and in commit messages. This script MUST pass with exit code 0 before any work is declared complete.

```bash
./scripts/protocol-zero.sh
```

A non-zero exit code is a blocking violation. All findings MUST be remediated before proceeding.

**Rationale:** Code in this repository has one author: the repository owner. AI agents are tools, not collaborators.
Attribution of authorship to an AI system is a governance violation regardless of context.

### 10.11 Typographic Lint

Typographic characters from rich text editors and AI output are prohibited in all source files. This includes em dashes
(U+2014), en dashes (U+2013), and smart quotes (U+201C/D, U+2018/9).

**Enforcement:**

The repository includes `scripts/check-em-dashes.sh`, an automated scanner that detects typographic characters in source
code. This script MUST pass with exit code 0 before any work is declared complete.

```bash
./scripts/check-em-dashes.sh
```

A non-zero exit code is a blocking violation. Replace typographic characters with their ASCII equivalents before
proceeding.

**Scope:** The scanner excludes markdown files (`.md`), documentation directories (`docs/`), and binary formats where
typographic characters are legitimate prose. Source files (`.swift`, `.py`, `.html`, `.css`, `.sh`, `.yml`, `.json`) are
scanned.

---

## 11. Goals

**P0 — Non-negotiable:**

1. All 20 contract articles render with correct pagination, clause formatting, and per-article signature blocks across
   iPhone SE (3rd gen) through iPhone 16 Pro Max.
2. Offline-first: full app functionality (reading, page-curl navigation, cached signatures) with zero network
   connectivity after initial sync.
3. Signed signatures persist permanently with zero data loss. Litestream backup restores to within 10 seconds of last
   write.
4. Content created via admin panel appears on Carolina's device within 30 seconds of APNS push delivery, assuming
   foreground or background app refresh.

**P1 — Must-have at launch:**

1. APNS push notifications deliver reliably to Carolina's device when new content is filed via admin panel.
2. Admin panel enables filing a new thought in under 30 seconds from browser open to "Push."
3. Signature signing flow completes in three taps: tap line → draw → sign. Upload succeeds silently in background.

**P2 — Should-have:**

1. Dark mode visual parity with light mode — all tokens, paper noise, and accent shifts implemented per §6.7.
2. Page-curl animation renders at 60fps on all supported devices.
3. Sound effects (page turn, signature, new content chime) toggleable and persisted across launches.

---

## 12. Non-Goals

1. **Multi-user support beyond two signers.** The app is hardcoded for Dinesh and Carolina. No user registration, no
   invite flow, no generic multi-tenancy. This is a personal artifact, not a platform.
2. **End-to-end encryption.** Both signers trust the self-hosted VPS. Transport encryption (HTTPS) is sufficient for the
   threat model.
3. **App Store distribution.** TestFlight-only. No App Store review compliance, no public listing, no privacy nutrition
   labels beyond TestFlight requirements.
4. **In-app content editing.** The iOS app is read-only. All content creation and editing happens through the admin web
   panel. Keeps the iOS app simple and the content pipeline unidirectional.
5. **Analytics or usage tracking.** No telemetry, no event logging, no third-party SDKs. The app does not observe how
   Carolina uses it.
6. **Real-time collaborative features.** Content delivery is sync-on-launch plus push notification. Near-real-time, not
   real-time.

---

## 13. Alternatives Considered

### Alternative 1: Do Nothing — Use Apple Notes or a Designed PDF

- **Description:** Write the contracts in Apple Notes or a designed PDF. Share via AirDrop or iMessage.
- **Advantages:** Zero engineering effort. Immediate. Already works.
- **Disadvantages:** Static — cannot update content after delivery. No signatures. No push notifications for new
  content. No unread tracking. No page-curl book experience. No legal-comedic framing at the app level. Loses the
  "living artifact" quality.
- **Rejection reason:** The core value is a living, signable, updatable artifact — not a static document.

### Alternative 2: SwiftData for Local Persistence (vs. JSON File Cache)

- **Description:** Use SwiftData for local content storage on the iOS device.
- **Advantages:** Built-in query support, migration tooling, iCloud sync capability, Apple-native.
- **Disadvantages:** Heavyweight for a read-mostly dataset of ~100-800 items. Adds schema migration complexity.
  SwiftData CloudKit sync is irrelevant (content comes from custom backend). Harder to debug than inspecting JSON files.
- **Rejection reason:** Dataset is small and read-mostly. JSON file cache with `Codable` is proportionate. SwiftData
  adds complexity without proportionate benefit.

### Alternative 3: PostgreSQL + Managed Hosting (vs. SQLite + Litestream)

- **Description:** Use PostgreSQL on a managed database service (Neon, Supabase, Railway) instead of SQLite on the VPS.
- **Advantages:** Battle-tested concurrent access. Managed backups. Standard SQL tooling ecosystem.
- **Disadvantages:** Adds a network hop for every DB query. Monthly cost for managed service. Over-engineered for a
  2-user, single-writer workload.
- **Rejection reason:** Single-writer, 2-user workload. SQLite + WAL mode is optimal. Litestream provides continuous
  backup equivalent to managed DB snapshots at zero marginal cost.

### Alternative 4: Polling for Content Updates (vs. APNS Push)

- **Description:** iOS app polls the `/sync` endpoint on a timer (every 5 minutes) instead of relying on push
  notifications.
- **Advantages:** Simpler — no APNS credential management, no device token registration, no push infrastructure.
- **Disadvantages:** Delayed content delivery (up to polling interval). Battery drain from periodic requests. No
  lock-screen notification. Breaks the "you push, she sees it" flow.
- **Rejection reason:** Emotional impact depends on immediacy. Push makes the app feel like a living channel, not a
  mailbox to check.

### Comparison Matrix

| Criterion          | Chosen Design    | Do Nothing | SwiftData | PostgreSQL | Polling |
|--------------------|------------------|------------|-----------|------------|---------|
| Complexity         | Medium           | None       | Higher    | Higher     | Lower   |
| Cost               | ~$0 (VPS shared) | $0         | Same      | +$5-15/mo  | Same    |
| Content liveness   | High             | None       | Same      | Same       | Low     |
| Offline support    | Full             | Full       | Full      | Same       | Same    |
| Operational burden | Low              | None       | Low       | Medium     | Lower   |

---

## 14. Capacity Planning

### Baseline

- **Users:** 2 (Dinesh, Carolina). No growth projection — private app.
- **Content at launch:** 20 contracts, 3 letters, 10 thoughts = 33 items.
- **API requests:** ~10-50/day (app launch sync + background refresh + occasional signature upload).

### Content Volume Projections

| Metric                      | Launch | Year 1 | Year 3 |
|-----------------------------|--------|--------|--------|
| Contracts                   | 20     | 30     | 40     |
| Letters                     | 3      | 50     | 120    |
| Thoughts                    | 10     | 250    | 600    |
| Total content items         | 33     | 330    | 760    |
| Signatures (2 per contract) | 0      | 60     | 80     |

### Storage Estimates

- **Content text:** Average 2KB per item. 760 items × 2KB = **~1.5MB**.
- **Signature PNGs:** PencilKit export at screen resolution. ~50-150KB each. 80 × 150KB = **~12MB**.
- **SQLite database (year 3):** **~15MB** including indexes, sync_log, sessions.
- **Backblaze B2 (Litestream WAL replication):** **~50-100MB** with WAL history. Within 10GB free tier.

### Throughput Validation

- **Single Uvicorn worker:** ~500-1000 RPS for JSON responses from SQLite.
- **Projected peak load:** 2 users, ~1 request/minute during active use = **~0.03 RPS**.
- **Headroom:** ~30,000x between projected load and worker capacity.
- **Bottleneck:** Signature PNG upload (largest payload). At 150KB over HTTPS, completes in <1s on LTE.

### Conclusion

Single Uvicorn worker with SQLite is over-provisioned by four orders of magnitude. No scaling strategy required.
Existing VPS resources sufficient indefinitely.

---

## 15. Cross-Cutting Concerns

### 15.1 Security — Threat Analysis

Threat surfaces analyzed via STRIDE: API key authentication, admin panel session, signature upload, APNS push delivery.

**API Key Authentication:**

- **Spoofing:** Key compromise allows impersonation. *Mitigation:* Keys in iOS Keychain
  (`kSecAttrAccessibleAfterFirstUnlock`), hashed server-side (bcrypt/argon2), transmitted only over HTTPS, never logged.
- **Tampering:** Modified request payloads. *Mitigation:* HTTPS integrity + Pydantic input validation on all endpoints.
- **Repudiation:** Signer denies action. *Mitigation:* `structlog` records all requests with signer identity and
  correlation IDs. Signatures are append-only with timestamps.
- **Information Disclosure:** Key in logs or error responses. *Mitigation:* Keys excluded from all log output. Error
  responses contain no credential material.
- **Denial of Service:** Brute-force key guessing. *Mitigation:* bcrypt hashing makes brute-force impractical. Rate
  limiting (10 req/s per IP) as defense-in-depth.
- **Elevation of Privilege:** Signer A uploads as Signer B. *Mitigation:* Server validates `signer` field matches API
  key identity. `UNIQUE(content_id, signer)` constraint prevents duplicate signatures.

**Admin Panel Session:**

- **Spoofing:** Cookie theft via XSS or network sniffing. *Mitigation:* Cookie attributes: `HttpOnly` (no JS access),
  `Secure` (HTTPS only), `SameSite=Strict` (no cross-site requests).
- **Session Fixation:** Forged session ID. *Mitigation:* Cryptographically random UUID validated against
  `admin_sessions` table. 7-day TTL with periodic expired session cleanup.

**Signature Upload:**

- **Tampering:** Malicious or oversized PNG. *Mitigation:* Server-side max file size (1MB), Content-Type validation, PNG
  header check.
- **Replay:** Duplicate signature submission. *Mitigation:* `UNIQUE(content_id, signer)` constraint returns 409 Conflict
  on duplicate.

**APNS Push Delivery:**

- **Spoofing:** Fake push notifications. *Mitigation:* APNS requires JWT signed with P8 key. Cannot be spoofed without
  key compromise.
- **Information Disclosure:** Content visible on lock screen. *Mitigation:* Push copy is vague ("A sealed thought has
  been filed"). No actual content in payload.

**Trust Boundaries:**

```
┌──────────────────────────────────────┐
│  iOS App (trusted client)            │
│  API key in Keychain                 │
│  Signer identity hardcoded           │
└──────────────┬───────────────────────┘
               │ HTTPS (TLS 1.2+)
               │ Authorization: Bearer <key>
┌──────────────▼───────────────────────┐
│  Caddy — TLS termination             │
│  ═══ TRUST BOUNDARY ═══             │
└──────────────┬───────────────────────┘
               │ localhost:8001
┌──────────────▼───────────────────────┐
│  FastAPI — application logic         │
│  Auth middleware, Pydantic validation │
└──────────────┬───────────────────────┘
               │ aiosqlite
┌──────────────▼───────────────────────┐
│  SQLite (WAL) → Litestream → B2     │
└──────────────────────────────────────┘
```

**Data Classification:**

| Data                   | Classification         | At-Rest Protection             | In-Transit Protection |
|------------------------|------------------------|--------------------------------|-----------------------|
| Love letters, thoughts | Intimate PII           | Backblaze B2 SSE-B2            | HTTPS (TLS 1.2+)      |
| Handwritten signatures | Biometric-adjacent PII | Backblaze B2 SSE-B2            | HTTPS                 |
| API keys (raw)         | Credential             | iOS Keychain (hardware-backed) | HTTPS                 |
| API keys (hashed)      | Derived credential     | SQLite on VPS                  | N/A (server-side)     |
| Device tokens          | Device identifier      | SQLite on VPS                  | HTTPS                 |

### 15.2 Observability

**SLIs:**

| SLI                        | Metric                                 | Target                               |
|----------------------------|----------------------------------------|--------------------------------------|
| API latency                | Response time P50 / P95 / P99          | P50 < 50ms, P95 < 200ms, P99 < 500ms |
| Sync success rate          | `GET /sync` 2xx / total requests       | > 99%                                |
| APNS delivery rate         | Successful sends / total push attempts | > 95%                                |
| Litestream replication lag | Time since last WAL frame replication  | < 60 seconds                         |
| Endpoint error rate        | 5xx responses / total requests         | < 1%                                 |

**SLOs:**

- API P95 latency under 200ms — a 2-user SQLite app should respond in single-digit ms. The 200ms ceiling accounts for
  network variance and cold starts.
- Sync success rate above 99% — content delivery is the core value. Sync failures degrade the "living artifact"
  experience.
- APNS delivery above 95% — push is best-effort by nature. Content still syncs on app launch if push fails.

**Alerting Strategy:**

- **Uptime monitor:** External healthcheck hitting `GET /health` every 60 seconds. Alert (email or Pushover) on 3
  consecutive failures.
- **Litestream status:** Cron job every 5 minutes checking Litestream process and last replication timestamp. Alert if
  replication lag exceeds 5 minutes.
- **APNS failures:** `structlog` logs all push attempts with success/failure. Weekly manual review. No automated
  alerting (2-user system, manual review sufficient).

**Logging:**

- `structlog` with JSON output in production, pretty-print in dev.
- Request correlation IDs on all API calls.
- Structured fields: `signer`, `endpoint`, `method`, `status_code`, `latency_ms`.
- Retention: 30 days on VPS filesystem. No external log aggregation at this scale.

### 15.3 Reliability — Failure Modes

| # | Failure                  | Trigger                                        | Blast Radius                                             | Degraded Behavior                                                                                                                                     | Recovery                                                                                 |
|---|--------------------------|------------------------------------------------|----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| 1 | VPS down                 | Host failure, reboot, provider outage          | All backend services offline                             | iOS app fully functional offline (read, navigate, cached signatures). No new content, no push, no signature upload. Queued uploads retry on recovery. | VPS restarts via systemd. If host lost, restore from Litestream to new VPS (< 5 min).    |
| 2 | Litestream stops         | Process crash, config error, B2 auth failure   | Backup gap accumulates. SQLite primary still functional. | All features work normally. Data written during outage at risk if VPS also lost.                                                                      | Restart Litestream. Verify replication resumes. Check B2 for recent WAL frames.          |
| 3 | APNS credentials expire  | P8 key deleted from Apple Developer portal     | Push notifications fail. All other features work.        | Content syncs on app launch and background refresh. No lock-screen notification.                                                                      | Generate new P8 key in Apple Developer portal. Update `.env`. Restart FastAPI.           |
| 4 | SQLite corruption        | Disk failure, incomplete write during crash    | Database unreadable. API returns errors.                 | iOS app works from local cache. Admin panel non-functional.                                                                                           | Restore from Litestream snapshot. Expected loss: < 10 seconds of writes.                 |
| 5 | Caddy TLS failure        | Let's Encrypt rate limit, DNS misconfiguration | HTTPS unavailable. App and admin panel cannot connect.   | iOS app works offline. No sync possible.                                                                                                              | Caddy auto-renews. Check DNS and rate limits. Restart Caddy. Manual cert as last resort. |
| 6 | TestFlight build expires | 90 days without new build                      | App stops launching on Carolina's device                 | Backend works. Push sends. App won't open.                                                                                                            | Trigger Xcode Cloud build (~30 min). Mitigated by scheduled 80-day builds.               |

**Blast Radius Assessment:** Complete backend failure leaves the iOS app fully functional in read-only mode. No data is
lost. Worst user-visible impact is delayed delivery of new content — acceptable for a personal app with low content
creation frequency (1-5 items/week).

### 15.4 Privacy & Data Lifecycle

**Retention Policy:** All content retained indefinitely by design. These are personal artifacts meant to persist as long
as both parties want them. No automatic expiration.

**Deletion Capability:**

- **Content (letters, thoughts, contracts):** Deletable via admin panel (`DELETE /admin/content/{id}`). Creates a
  `sync_log` entry; iOS app removes the item on next sync.
- **Signatures:** No delete endpoint by design (signatures are "permanent"). Manual deletion via direct SQLite `DELETE`
  on VPS. Deliberate friction prevents accidental erasure while preserving the capability.
- **Full data wipe:** (1) Stop Litestream, (2) delete SQLite database, (3) delete Backblaze B2 bucket contents, (4)
  re-initialize empty database.

**Backup Encryption:**

- **Transport:** Litestream → Backblaze B2 over HTTPS.
- **At rest:** Backblaze B2 server-side encryption (SSE-B2) enabled on replication bucket. Encrypts WAL frames at rest
  with B2-managed keys.
- **VPS disk encryption:** To be confirmed (see §18, Open Items).

**Data Export:** Content accessible via `GET /content` API or direct SQLite database copy. No formal export UI.
Formalize if data portability becomes a requirement.

---

## 16. Dependencies and Risks

### 16.1 Dependencies

| Dependency              | Type             | What It Provides                              | Fallback If Unavailable                                                                            |
|-------------------------|------------------|-----------------------------------------------|----------------------------------------------------------------------------------------------------|
| Apple APNS              | External service | Push notifications to iOS devices             | Content syncs on app launch and `BGAppRefreshTask`. Push is best-effort.                           |
| Backblaze B2            | External service | Off-site backup storage for Litestream        | SQLite primary on VPS remains operational. Backup gap accumulates. Manual `rsync` as interim.      |
| Caddy                   | Infrastructure   | HTTPS termination, auto-TLS via Let's Encrypt | Direct Uvicorn access on localhost (admin-only). iOS app offline until HTTPS restored.             |
| Let's Encrypt           | External service | TLS certificates                              | Caddy retries automatically. Certificates valid 90 days — extended window before expiry.           |
| `aioapns`               | Library          | Async APNS client (HTTP/2, JWT)               | Raw HTTP/2 requests to APNS gateway (high effort, unlikely needed). Library mature and maintained. |
| TestFlight              | Platform         | App distribution                              | None — required. 90-day expiry mitigated by scheduled Xcode Cloud builds every 80 days.            |
| Apple Developer Program | Platform         | Code signing, TestFlight, APNS                | None — required. Annual renewal ($99/year).                                                        |

### 16.2 Risks

| # | Risk                                  | Likelihood | Impact                           | Mitigation                                                                                                      |
|---|---------------------------------------|------------|----------------------------------|-----------------------------------------------------------------------------------------------------------------|
| 1 | TestFlight 90-day expiry              | Medium     | High — app stops working         | Xcode Cloud scheduled builds every 80 days. Calendar reminder as backup.                                        |
| 2 | APNS P8 key loss                      | Low        | Medium — push fails, sync works  | P8 keys do not expire. Store in `.env`. Back up offline (encrypted USB or password manager).                    |
| 3 | VPS provider failure                  | Low        | High — all backend down          | Litestream enables full restore to new VPS in < 5 min. Infrastructure stateless except SQLite.                  |
| 4 | Apple deprecates UIPageViewController | Low        | Medium — page-curl breaks        | Monitor WWDC annually. Continues working for years via compatibility. Replacement: custom SwiftUI gestures.     |
| 5 | Signature PNG quality (finger input)  | Medium     | Low — aesthetic, not functional  | PencilKit configured for clean strokes. "Clear" allows retry. `drawingPolicy = .anyInput` optimized for finger. |
| 6 | Content sync fails silently           | Low        | Medium — Carolina misses content | `structlog` logs all sync requests. Unread badges as visual indicator. Push notification as secondary signal.   |

---

## 17. Implementation Phases

### Phase 1: Backend Foundation

**Prerequisite:** Generate APNS P8 key (Apple Developer portal → Account → Keys → + → Apple Push Notifications service).
Download `.p8` file, store on VPS, back up to password manager.

- [ ] Set up `/opt/exhibit-a/` on VPS with Python 3.13+ and `uv`
- [ ] FastAPI app with SQLite (WAL mode) + `aiosqlite`
- [ ] `structlog` configured (JSON in production)
- [ ] API key auth middleware (Bearer token, bcrypt hash comparison, constant-time)
- [ ] Generate and store hashed API keys for both signers
- [ ] Content CRUD endpoints (admin REST)
- [ ] Content read endpoints (authenticated)
- [ ] Signature upload/retrieve endpoints (authenticated)
- [ ] Device token registration endpoint (authenticated)
- [ ] Caddy config for `exhibita.dineshd.dev` (auto-HTTPS)
- [ ] Systemd service (single Uvicorn worker)
- [ ] Litestream config → Backblaze B2 continuous backup
- [ ] Seed database with initial 20 contracts from `docs/exhibit-A-contract.md`
- [ ] `ruff format --check && ruff check && mypy --strict` passing
- [ ] `pytest` smoke tests for all endpoints

### Phase 2: Admin Panel

- [ ] Session-based auth (API key login, bcrypt hash, SQLite session store)
- [ ] Dashboard view (content summary, quick actions)
- [ ] Content list view (grouped by type, ordered)
- [ ] Contract creation form (article number, title, body, signature toggle)
- [ ] Letter creation form (title, subtitle, classification dropdown, markdown body)
- [ ] Thought creation form (body text, minimal friction)
- [ ] Edit forms (pre-populated from existing content)
- [ ] Delete with confirmation
- [ ] Reorder support (position number)
- [ ] APNS integration via `aioapns` (push on content creation)
- [ ] Jinja2 templates + HTMX 2.x for dynamic forms
- [ ] Admin panel CSS (clean, functional, in-character)
- [ ] GitHub Actions CI (lint + test on push)

### Phase 3: Swift App — Core

- [ ] Xcode project setup with SwiftUI (iOS 26+ target)
- [ ] SPM configured, `Package.resolved` committed
- [ ] SwiftLint + SwiftFormat configured at project root
- [ ] Liquid Glass suppressed (opaque backgrounds, UIKit appearance overrides)
- [ ] Theme system (color tokens, typography styles, spacing constants)
- [ ] `@Observable` AppState + Router with `NavigationStack` + `NavigationPath`
- [ ] `KeychainService` — thin Keychain wrapper for API key storage
- [ ] API client with URLSession + Bearer token auth from Keychain
- [ ] JSON file cache for content (`Codable` models → `.json` files)
- [ ] PNG file cache for signatures
- [ ] Home screen ("The Filing Cabinet")
- [ ] APNS device token registration on first launch (with API key auth)
- [ ] Sync on app launch + `BGAppRefreshTask` for background sync
- [ ] Unread badge tracking (UserDefaults last-read timestamps)

### Phase 4: The Contract Book

- [ ] UIPageViewController wrapper with page-curl (`UIViewControllerRepresentable`)
- [ ] Cover page
- [ ] Table of contents (tappable, jumps via page index)
- [ ] Contract article pages with dynamic pagination
- [ ] Signature block component (signed/unsigned states)
- [ ] PencilKit signing flow (`drawingPolicy = .anyInput`, tool picker disabled)
- [ ] Signature persistence (local PNG cache + background `URLSession` upload)
- [ ] Final page ("In Witness Whereof")

### Phase 5: Letters & Thoughts

- [ ] Letter list view (correspondence log)
- [ ] Letter detail view (scrollable reader, `AttributedString` markdown rendering)
- [ ] Thought list view (classified memoranda)
- [ ] Thought detail view (plain text, centered, generous whitespace)
- [ ] Unread badges per section

### Phase 6: Polish & Content

- [ ] Offline handling (queued signature uploads via background `URLSession`)
- [ ] Haptic feedback on signatures (UIImpactFeedbackGenerator, .medium)
- [ ] Page turn sound effects (subtle, toggleable via settings)
- [ ] Review and finalize all 20 contract articles for app formatting
- [ ] Write 2-3 launch letters
- [ ] Write 5-10 launch thoughts
- [ ] Dark mode (warm near-black, lifted accents, paper noise at 2-3%)
- [ ] Push notification handling (deep link via Router + NavigationPath)
- [ ] Swift Testing: unit tests for sync logic, cache, API client

### Phase 7: Deploy

- [ ] Xcode Cloud workflow configured (build + TestFlight deploy)
- [ ] Xcode Cloud scheduled build every 80 days (prevents 90-day TestFlight expiry)
- [ ] Build for Dinesh (signer=dinesh, API key in xcconfig)
- [ ] Dinesh signs all contracts
- [ ] Build for Carolina (signer=carolina, API key in xcconfig)
- [ ] Invite Carolina to TestFlight
- [ ] Verify push notifications working end-to-end
- [ ] Verify Litestream backup restoring correctly

### Rollback & Monitoring Gates

| Phase                 | Rollback Procedure                                                | Max Rollback Time            | Advance Gate                                                         |
|-----------------------|-------------------------------------------------------------------|------------------------------|----------------------------------------------------------------------|
| 1: Backend            | Delete `/opt/exhibit-a/`, remove systemd service and Caddy config | 10 min                       | `GET /health` returns 200. Smoke tests pass. Litestream replicating. |
| 2: Admin              | Revert admin routes and templates. API endpoints unaffected.      | 5 min (git revert)           | Dashboard loads. CRUD works. Push notification sends.                |
| 3: Swift Core         | Delete Xcode project. Backend unaffected.                         | Instant                      | App launches, syncs content, displays home screen.                   |
| 4: Contract Book      | Revert to Phase 3 build.                                          | git revert + build (~30 min) | 20 articles paginate. Signatures sign and upload.                    |
| 5: Letters & Thoughts | Revert to Phase 4 build.                                          | git revert + build (~30 min) | List and detail views render. Unread badges work.                    |
| 6: Polish             | Revert individual features. Core unaffected.                      | Per-feature                  | Dark mode, haptics, sounds, deep links functional.                   |
| 7: Deploy             | Rebuild with previous config.                                     | Build (~30 min)              | End-to-end flow verified. Litestream restore tested.                 |

---

## 18. Open Items

All items resolved. No open questions remain.

## 19. Resolved Decisions

| Item                     | Decision                                                        | Rationale                                                                                                                                                                                                                                                                                    |
|--------------------------|-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Admin interface          | Web app at `exhibita.dineshd.dev/admin`                         | Frictionless content management from phone or laptop. Jinja2 + HTMX 2.x, no build step.                                                                                                                                                                                                      |
| Notification strategy    | APNS push notifications via `aioapns`                           | Triggered from admin panel on content creation. TestFlight supports APNS. Immediate delivery when you push new content.                                                                                                                                                                      |
| Content delivery         | Server-driven, no TestFlight rebuild                            | All content fetched via API. App caches locally. New content appears on next sync after push notification.                                                                                                                                                                                   |
| Sound effects            | Included, toggleable                                            | Subtle paper sound on page curl. Pen-on-paper for signature. Gentle chime for new content. Toggle in settings, default on.                                                                                                                                                                   |
| Signature pad background | `background.reading` (#F8F1E3)                                  | Matches paper surface. Stroke in `text.reading` (#2C2118) — pen on paper.                                                                                                                                                                                                                    |
| Content format           | Contracts: plain text. Letters: markdown. Thoughts: plain text. | Letters rendered via `AttributedString` markdown. Contracts pre-styled by SwiftUI view layer. Thoughts are short plain text.                                                                                                                                                                 |
| Admin panel styling      | Light version of app's legal aesthetic                          | Parchment background, legal typography. "Clerk's Office" framing. In-character.                                                                                                                                                                                                              |
| Markdown preview         | Live preview via HTMX                                           | HTMX swaps preview on keyup with debounce. Low effort, high value for letter formatting.                                                                                                                                                                                                     |
| iOS platform target      | iOS 26+                                                         | Enables all modern APIs. Liquid Glass suppressed to preserve warm paper aesthetic.                                                                                                                                                                                                           |
| State management         | `@Observable` macro exclusively                                 | Replaces legacy `ObservableObject` + `@Published`. Fine-grained reactivity, less boilerplate.                                                                                                                                                                                                |
| Navigation               | `NavigationStack` + `NavigationPath` + `@Observable` router     | Standard 2026 pattern. Deep linking via path manipulation for push notifications.                                                                                                                                                                                                            |
| Local persistence        | JSON file cache with `Codable` models                           | Proportionate to small read-mostly dataset. No CoreData, no SwiftData.                                                                                                                                                                                                                       |
| API authentication       | Per-signer API key, Bearer token, hashed server-side            | All app-facing endpoints authenticated. Keys in iOS Keychain. Constant-time comparison.                                                                                                                                                                                                      |
| Database backup          | Litestream → Backblaze B2                                       | Continuous WAL replication. Point-in-time restore. Protects irreplaceable signed contracts.                                                                                                                                                                                                  |
| iOS package management   | SPM exclusively                                                 | CocoaPods trunk freezes Dec 2026. Pin versions. Commit `Package.resolved`.                                                                                                                                                                                                                   |
| iOS linting              | SwiftLint 0.58+ + SwiftFormat                                   | Code style enforcement from project start.                                                                                                                                                                                                                                                   |
| iOS testing              | Swift Testing (unit) + XCTest (UI only)                         | `#expect()`, native async, parallel, parameterized. Modern test framework.                                                                                                                                                                                                                   |
| iOS CI                   | Xcode Cloud → TestFlight                                        | Zero-config signing/provisioning. Scheduled builds every 80 days for TestFlight expiry.                                                                                                                                                                                                      |
| Backend APNS library     | `aioapns`                                                       | Async HTTP/2, JWT token-based. Persistent connection reuse.                                                                                                                                                                                                                                  |
| Backend logging          | `structlog` with JSON in production                             | Request correlation IDs. Pretty-print in dev.                                                                                                                                                                                                                                                |
| Backend dependency mgmt  | `uv` + pinned `requirements.txt`                                | Fast, modern Python package manager. Reproducible deploys.                                                                                                                                                                                                                                   |
| Backend testing          | `pytest` + `pytest-asyncio`                                     | Smoke tests for all endpoints.                                                                                                                                                                                                                                                               |
| Backend CI               | GitHub Actions                                                  | Lint + test on push.                                                                                                                                                                                                                                                                         |
| Liquid Glass             | Suppressed                                                      | Warm ivory paper aesthetic is core identity. Opaque backgrounds, UIKit appearance overrides.                                                                                                                                                                                                 |
| APNS credentials         | Generate P8 key as Phase 1 prerequisite                         | Apple Developer account active. Generate key: Apple Developer portal → Account → Keys → + → Apple Push Notifications service. Download `.p8` once (cannot re-download). Store on VPS at `/opt/exhibit-a/.env` (APNS_KEY_ID, APNS_TEAM_ID, APNS_KEY_PATH). Back up `.p8` to password manager. |
| App icon                 | Designed by Dinesh before TestFlight distribution               | Final icon created manually before Phase 7 distribution. Not blocking implementation phases 1-6.                                                                                                                                                                                             |
| VPS disk encryption      | Not encrypted. Accepted risk.                                   | VPS (`157.180.94.145`) runs plain ext4 on `sda1`. No LUKS. Adding encryption requires full reinstall. Risk accepted: physical disk access requires data center access, VPS is SSH-controlled, Backblaze B2 backups have SSE-B2. Low risk for a 2-user personal app.                          |
| Data export mechanism    | Deferred indefinitely                                           | Content accessible via `GET /content` API or direct SQLite database copy. No formal export UI needed. Revisit if data portability becomes a requirement.                                                                                                                                     |

---

## 20. Skill Registry

Skills are enforcement tools, not optional helpers. When a task falls within a skill's declared scope, the agent MUST
invoke that skill before attempting custom logic. Ad-hoc generation that contradicts an active skill is a governance
violation.

### 20.1 Registry

| Skill                             | Path                                            | Scope                                                                                                                                                            | Invocation Trigger                                                                                                                  |
|-----------------------------------|-------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **Skill Creator**                 | `.claude/skills/skill-creator/`                 | Scaffold, validate, and package new skills.                                                                                                                      | Creating or modifying a skill.                                                                                                      |
| **Design Review**                 | `.claude/skills/design-review/`                 | Validates design docs, RFCs, ADRs, and technical proposals against twelve mandatory sections (S1-S12).                                                           | When a design document or engineering proposal is provided for review.                                                              |
| **Exhibit A Theme Counsel**       | `.claude/skills/exhibit-a-theme-counsel/`       | Color palette, typography, surfaces, elevation, spacing, and visual identity. Guards against anti-patterns and maintains romantic-legal editorial warmth.        | Any UI mockup, color palette, typography selection, screen design, or visual design decision.                                       |
| **Exhibit A Stack Modernizer**    | `.claude/skills/exhibit-a-stack-modernizer/`    | iOS app architecture, backend frameworks, persistence, networking, deployment, CI/CD, and all technology decisions.                                              | Reviewing tech stack, auditing design doc for outdated choices, evaluating architecture decisions, or proposing technology changes. |
| **Phase Epic Decomposition**      | `.claude/skills/phase-epic-decomposition/`      | Translates design docs into actionable PHASES.md roadmaps. Enforces dependency ordering, scope isolation, and topological epic sequencing.                       | Translating the design doc into implementation phases, creating a PHASES.md delivery roadmap.                                       |
| **FAANG Epic Writing**            | `.claude/skills/faang-epic-writing/`            | Epic expansion from PHASES.md with binary completion criteria, explicit scope boundaries, dependency enforcement, and file-level surface mapping.                | Expanding PHASES.md epics into standalone documents, epic review, definition of done construction.                                  |
| **SwiftUI Architecture Contract** | `.claude/skills/swiftui-architecture-contract/` | SwiftUI code, project structure, navigation flows, view-model layer, dependency injection, previews, and Swift 6.2 concurrency compliance.                       | Creating, editing, or refactoring SwiftUI code. Architecture reviews, MVVM enforcement, PR validation.                              |
| **Swift Concurrency Contract**    | `.claude/skills/swift-concurrency-contract/`    | SwiftUI, networking, caching, sync/export, actor design, and async patterns. Validates `Package.swift` settings and concurrency escape hatches.                  | Creating, editing, or refactoring async code. PR validation and concurrency audits.                                                 |
| **Networking Layer Contract**     | `.claude/skills/networking-layer-contract/`     | Swift networking code, API clients, endpoint models, retry logic, upload queues, reachability handling, certificate pinning, and network-related test isolation. | Creating, editing, reviewing, or refactoring Swift networking code. PR validation of networking changes.                            |

### 20.2 Skill Override Rule

If a skill's SKILL.md defines a pattern, constant, architecture, or constraint, the agent MUST follow it even if an
alternative seems valid. Skills encode domain expertise that was deliberately authored. The agent does not get to
second-guess them.

### 20.3 Skill Integrity

- All skills reside under `.claude/skills/<skill-name>/`. No exceptions.
- All skills MUST be created via Skill Creator (`init_skill.py` -> `validate_skill.py` -> `package_skill.py`).
- Do not modify any skill's scripts, references, or SKILL.md without explicit user approval.

### 20.4 Skill Registration Governance

**This rule is BLOCKING.**

- Every time a new skill is created, the Skill Registry (this section) MUST be updated in the same commit.
- Skills that are not registered in §20.1 are considered unofficial and unsupported.
- The registry is the single source of truth for available Claude Code capabilities in this repository.
- Deletion of a skill requires removal of its registry entry in the same commit.
- An agent MUST NOT invoke a skill that is not present in the registry.

---

## 21. Definition of Done

A task is complete only when **ALL** of the following hold:

- [ ] Requested functionality works as specified.
- [ ] Code runs without errors.
- [ ] No hardcoded secrets or credentials.
- [ ] No dead code, stubs, or placeholders.
- [ ] No force unwraps or unsafe operations without inline justification.
- [ ] No `print()` / `NSLog()` debugging statements in committed code.
- [ ] No unintended new files.
- [ ] No em dashes or smart quotes in source files.
- [ ] Protocol Zero scan passes: `./scripts/protocol-zero.sh` exits 0.
- [ ] Typographic lint passes: `./scripts/check-em-dashes.sh` exits 0.
- [ ] Conventional Commits format on all commits.
- [ ] Tests pass (if they exist).
- [ ] Applicable skills from §20.1 were consulted and their constraints followed.
- [ ] Design document compliance verified for any architectural decision.
- [ ] **Python files:** `ruff format --check`, `ruff check`, and `mypy --strict` all pass.
- [ ] **Swift files:** SwiftLint and SwiftFormat report clean.

If any item fails, the task is not done.
