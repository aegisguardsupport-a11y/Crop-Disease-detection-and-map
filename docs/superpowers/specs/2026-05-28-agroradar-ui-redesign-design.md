# AgroRadar UI Redesign — Design Spec

**Date:** 2026-05-28
**Status:** Approved by user, ready for planning
**Scope:** Complete visual and interaction redesign of the AgroRadar mobile app (`apps/mobile`). No architectural changes to backend or data layer.

---

## 1. Goal

Replace the current dark-leaning UI with a clean, light, beautiful interface that feels professional to agronomists and approachable to farmers. The app's primary purpose — capturing and acting on crop disease reports — must be obvious from any screen.

## 2. Audience

Mixed:

- **Agronomists / extension workers** — primary. Comfortable with apps, want fast scanning, real data, useful filters.
- **Farmers** — secondary. May use the app one-handed, in sunlight, with mixed app literacy.

Defaults skew toward simple, large, visual; capability is exposed where it earns its keep (filters on Map, full report detail, treatment instructions).

## 3. Visual identity — "Soft Sage"

| Token | Value | Usage |
|---|---|---|
| `bg` | `#fbfaf7` | App background (off-white, warm) |
| `surface` | `#ffffff` | Cards, sheets, inputs |
| `surfaceMuted` | `#fdfcf7` | Section backgrounds, drawer fills |
| `border` | `#efeae0` | Default 1px card / input border |
| `borderStrong` | `#e8e4dc` | Phone-frame / bottom-sheet edges |
| `text` | `#0b1220` | Headings, primary text |
| `textMuted` | `#475569` | Secondary text, body copy |
| `textSubtle` | `#64748b` | Labels, metadata, captions |
| `textFaint` | `#94a3b8` | Placeholders, disabled |
| `brand500` | `#10b981` | Primary brand (emerald) |
| `brand600` | `#0d9488` | Primary brand end (teal) |
| `brand900` | `#064e3b` | Hero numbers, deep accents |
| `brandTint` | `#ecfdf5` | Subtle brand backgrounds |
| `success` | `#047857` / `#ecfdf5` | Severity Low pill |
| `warning` | `#92400e` / `#fef3c7` | Severity Medium / High pill |
| `danger` | `#b91c1c` / `#fee2e2` | Severity Critical pill |

**Signature gradient (used sparingly):**
`linear-gradient(135deg, #10b981 → #0d9488)`

Used only on:
1. Primary CTA buttons
2. The center FAB in the tab bar
3. Hero-card radial glow (very subtle radial behind big numbers)
4. Active filter chips and active toggle states
5. The loading splash

There is **no second gradient family**. This is what makes it Soft Sage instead of Vibrant Earth.

**Typography**
- System font stack: SF Pro on iOS, Roboto on Android. No custom font files.
- Weights used: 600, 700, 800 only.
- Headings ≥ 14px get `letter-spacing: -0.02em`.
- Uppercase labels: 11px, weight 700–800, `letter-spacing: 1.4px`.
- Body: 13–14px, line-height 1.5. Subtitles: 11–12px.

**Radii**
- Cards: 12–14px
- Buttons / inputs: 12px
- Sheets: 24px (top corners only)
- Avatars / icons in glow: 999px or 14–18px

**Shadows** (soft, single source)
- Cards: `0 1px 2px rgba(15,23,42,0.03)`
- Hover / press lift: add `0 8px 24px rgba(15,23,42,0.06)`
- Primary CTA: `0 6px 14px rgba(13,148,136,0.32)`
- Bottom-sheet header: `0 -8px 24px rgba(15,23,42,0.08)`

**Motion (Reanimated)**
- Section enter on screen mount: `FadeInDown` with 60–80ms stagger.
- Press feedback: `scale: 0.97` over 120ms (existing `pressable-scale.tsx` reused).
- Bottom sheet: snap points 25% / 60% / 92%.
- Splash: existing emerald glow + breathing scale, kept (it works).
- No bouncy, no spring overshoot. Easing is `inOut(ease)` everywhere.

## 4. Information architecture

Five tabs, unchanged from today, but the center one is elevated:

```
Home   |  Map   |  [ Report ]   |  Alerts   |  Profile
```

`[ Report ]` is a **raised gradient FAB** integrated into the tab bar (translateY -16px, 48–52px square, 16px radius, 3px white border, gradient background, primary CTA shadow). It opens the report flow regardless of current tab.

The remaining four tabs use simple icon + label, equal weight, with the active tab tinted brand teal.

**Routes** (Expo Router) keep their existing structure:
- `(app)/index` — Home
- `(app)/map` — Map
- `(app)/upload` — Report flow target. Tapping the center FAB navigates here from any tab; the screen now renders the multi-step report flow (Capture → Analyzing → Result → Submitted) as internal state rather than separate routes, so deep links and back navigation behave predictably.
- `(app)/notifications` — Alerts
- `(app)/profile` — Profile
- `(auth)/login`, `(auth)/otp`
- `(onboarding)/name`, `(onboarding)/first-plot`
- `reports/[id]`

## 5. Screen specs

### 5.1 Home

**Layout — Hero-first.** Three things, in this order:

1. **Greeting header** — name + location + weather snippet on the left, avatar (tappable → Profile) on the right. ~64px tall.
2. **Outbreak hero card** — white card, ~120–140px, with subtle radial green glow. Inside:
   - Uppercase label `TODAY · 5 KM RADIUS`
   - Big number (34px, weight 800, color `brand900`)
   - Two pills: trend (`Stable`/`Rising`/`Falling`) and `+N new`
   - One-line context underneath: "Tomato leaf curl flagged on 3 nearby plots"
3. **Primary CTA** — full-width gradient button "Report a disease" with subtitle "Camera + AI in 30s" and a soft rounded square icon on the right. This is **redundant** with the FAB on purpose — first-launch users will see it before they understand the FAB.
4. **Latest in your area** — white card with `View all` link in the title row, two list rows (thumb + crop · disease + distance · time + severity pill).

Pull-to-refresh tinted brand teal. Existing `useDashboard` hook provides data.

Components reused/replaced:
- `GreetingHeader` — keep, restyle.
- `OutbreakSummary` → becomes the hero card.
- `QuickUploadCTA` → becomes the gradient CTA.
- `RecentReports` → becomes the "Latest in your area" card, capped at 3 rows.
- `DiseaseTrends`, `NearbyAlerts` → **removed from Home.** Trends move to Profile (later spec). NearbyAlerts move to Notifications.

### 5.2 Map

**Layout — Bottom-sheet pattern.**

- Map fills the screen edge-to-edge (existing `react-native-maps`).
- **Top bar:** floating search input (`Search area or crop…`) + filter icon button. Both white, 12px radius, soft shadow.
- **Filter chip rail:** below the search bar, horizontal scroll. Chips: `All`, `Tomato`, `Wheat`, `High`, `7d`, etc. Active = gradient fill, inactive = white + 1px border.
- **FAB stack on right:** locate-me, heatmap toggle, zoom + / zoom − (4 icons stacked).
- **Bottom sheet** (existing `@gorhom/bottom-sheet`): snap points 25% (peek), 60% (default), 92% (fullscreen list). Header: "N reports in view" + sort label. Rows reuse the same pattern as Home's `Latest in your area`.
- Tapping a marker / cluster expands the sheet to 60% scrolled to that report.

Heatmap, clustering, live socket updates, filters store — all existing in `features/map-system`. Only the visual treatment of `MapControls`, `MapMarker`, `ReportPreviewCard`, `HeatmapLayer`, `MapFilters`, `ConnectionIndicator` changes.

`ConnectionIndicator` becomes a small pill on the search bar's left when disconnected, instead of a separate floating element.

### 5.3 Report flow (the FAB)

Four screens. Tapping the FAB pushes a modal stack with `slide_from_bottom`.

**Step 1 — Capture**
- Full-bleed camera view (existing `expo-image-picker` camera or a dedicated capture screen — implementation decides).
- Bottom controls: gallery icon (left), large gradient shutter button (center, 52px circle), flash icon (right).
- Subtle hint text: "Frame the affected leaf".
- Top-left close icon to cancel.

**Step 2 — Analyzing**
- Photo thumbnail at top (90px tall, rounded).
- Centered conic-gradient spinner.
- Title: "Analyzing your photo"
- Subtitle changes based on engine:
  - Online: **"Using our high-accuracy cloud model…"**
  - Offline: **"Using on-device AI · works without internet…"**
- Status chip list: "✓ Image quality good · ✓ Leaf detected · ● Identifying disease".

**Engine selection logic:**
1. Try `apps/backend` FastAPI endpoint (network + auth headers).
2. On failure (network error, 5xx, timeout > 8s), fall back to `features/offline-ai/offline-ai.client.ts`.
3. On both failing, jump straight to step 3 in **manual mode**: no AI fields filled, fields are editable, no badge shown.

**Step 3 — Result**
The most important new screen. It must:

- Show diagnosis prominently: thumbnail + crop · disease name (12–13px, weight 800) + small subtitle (`Tomato · viral · 94% match`).
- Show severity pill (`Low`/`Medium`/`High`/`Critical`) and a status pill (`Spreading`/`Localized`/`Contained`).
- **Engine badge:**
  - Online → pill "Cloud AI · 94%"
  - Offline → pill "On-device AI · 88%"
  - Manual → no badge
- "Recommended actions" card with the brand glow background and a numbered list (1. 2. 3. …) rendered from the API's `recommendations` field. Markdown supported (bold, links). Maximum 5 items shown, "Show more" expands the rest.
- **"Wrong diagnosis? Edit details"** link below the actions card. Opens an inline editable form (crop dropdown, disease text input, severity chips, notes textarea). Saving updates the report data; engine badge becomes "Edited by you".
- **Map-share toggle** card at the bottom: title "Add to outbreak map", subtitle "Helps nearby farmers", switch defaults to ON. Off keeps the report private (still saved to history under Profile).
- **Confirm & submit** primary CTA (gradient).

**Low-confidence handling:** If AI confidence < 60%, the result screen shows up to three candidate diseases as selectable cards instead of one diagnosis. Treatment instructions only appear after the farmer picks. Headline becomes "Pick the closest match".

**Step 4 — Submitted**
- Centered green-gradient checkmark circle (64px), drop-shadow.
- "Submitted" + subtitle ("Visible to nearby agronomists and farmers" / "Saved to your history" if private).
- Recap card: severity pill + crop · disease + location + "just now".
- Two CTAs: ghost "View on map" and primary "Report another".

### 5.4 Report detail (`reports/[id]`)

Modal route opened from anywhere. Header with back arrow + "Report" + overflow menu (`⋯`).

- Photo banner (80–120px, rounded 12px). Top-right overlays severity pill and the engine badge from the original analysis.
- Title: crop · disease (13px, weight 800).
- Subtitle: location coords + relative time.
- "Recommended actions" card (same as step 3).
- Reporter row: small circular avatar + name + "Farmer / Agronomist · verified". Right side: confirmation count pill (`+1 confirmed`).
- Action footer: ghost "Confirm" + primary "View on map".

### 5.5 Notifications

- Header: "Alerts" h1 + right-aligned "Mark all read" link.
- Day labels: `TODAY`, `YESTERDAY`, `THIS WEEK`, `EARLIER`.
- Notification card variants:
  - **Critical** — left border 3px solid danger, amber thumb, severity pill on right.
  - **Confirmation** — emerald icon thumb (`✓`), no border accent.
  - **System / map update** — amber icon thumb, lower opacity (0.85).
- Empty state: 64px green-glow tile with `🌾`, "All clear in your area" + "We'll alert you when nearby outbreaks need attention." + ghost CTA "Adjust alert radius".
- Tap any item → relevant deep link (report detail, map at coordinate, settings).

### 5.6 Profile

- Hero: 56px avatar (gradient, initials), name (13px, weight 800), phone, two pills (`Agronomist`/`Farmer` and `Verified` if applicable).
- Section "Your activity" — list card with two rows: "Reports submitted · N", "Plots · N". Each row navigates further.
- Section "Settings" — list card: Notifications, Alert radius, Language, then a destructive "Sign out" row in `danger` red.
- Optional later: "Disease trends in your area" replaces the old Home dashboard widget (out of scope for v1 redesign, just leave the section header reserved).

### 5.7 Auth

**Login**
- Top half: 48px gradient logo tile + "Welcome to AgroRadar" + tagline "Detect, report, and track crop diseases together".
- Bottom half: phone input (flag + country code + number), primary "Send OTP", small terms text below.
- Layout uses `flex: 1` for the centered top, fixed bottom group.

**OTP**
- Centered: title "Enter 6-digit code" + subtitle "Sent to +91 …".
- 6 digit boxes — filled = brand-tint background + brand teal border, focused = 2px brand teal border. Existing `OtpInput` keeps the API.
- "Resend in 0:24" → "Resend code" link.
- Bottom: primary "Verify" button. Disabled (beige) until 6 digits entered.

### 5.8 Onboarding

**Name (1 / 2)**
- Title "What should we call you?" + helper text.
- Single text input, 2px brand teal focus border.
- Footer: ghost "Skip" + primary "Continue" (2:1 width ratio).

**First plot (2 / 2)**
- Title "Add your first plot" + helper.
- Plot name input.
- Crop chip selector (multi-select, gradient fill when active).
- Inline mini-map preview with a draggable gradient pin (existing `react-native-maps` smaller instance).
- Footer: ghost "Skip" + primary "Save plot".

### 5.9 Loading and error states (cross-cutting)

- **Skeleton:** beige `#f1efe7 → #fafaf6 → #f1efe7` shimmer at 1.4s linear infinite. Shapes mirror the real layout. Wrap in existing `Skeleton` component.
- **Empty state:** 64px tile with green radial glow + emoji or icon, title (11px weight 800), subtext (9px muted), optional ghost CTA. Existing `EmptyState` restyled.
- **Error / offline banner:** persistent strip at the top, amber gradient (`#fef3c7 → #fde68a`), 1px `#fcd34d` border, dot + "You're offline · 3 reports queued · will sync when connected". Existing `OfflineBanner` restyled.
- **In-screen error:** uses the empty-state pattern with `⚠` glyph and a primary "Retry" ghost button.

## 6. Component inventory — what changes

This is the practical change list for engineers. Every existing component listed here is **kept and restyled** unless marked `[remove]`.

**`components/ui/`** (atomic primitives)
- `Button` — add gradient variant, ghost variant, dim/disabled variant. Press scale 0.97. Loading = inline spinner replacing label.
- `Card` — add `glow` prop for radial-green hero variant. Default border `#efeae0`, radius 14, padding 12–14.
- `Input` — light only, 12px radius, focus = 2px brand-teal border, label support, error state with red border + helper.
- `Avatar` — gradient default, initial letter, ring on verified.
- `Skeleton` — shimmer values updated to beige tones.
- `Loader` — conic-gradient ring (replaces the existing implementation).
- `PressableScale` — keep as is.

**`components/feedback/`**
- `EmptyState` — new visual: glow tile + title + sub + ghost CTA.
- `BottomSheetWrapper` — keep, default snap points adjusted to 25/60/92, light theme.

**`components/layout/`**
- `ScreenContainer` — light bg, safe-area aware.
- `SectionHeader` — h2-style with optional right-aligned link.

**`components/navigation/`**
- `TabBar` — rebuilt: 5 cells, 3rd is the FAB wrapper with `translateY(-16px)`. Active tab uses gradient icon background. Existing tab bar in `components/navigation/tab-bar.tsx` is replaced.
- `TabBarIcon` — restyled icon container.

**`features/dashboard/components/`**
- `GreetingHeader`, `OutbreakSummary`, `QuickUploadCTA`, `RecentReports` — restyled per §5.1.
- `DiseaseTrends`, `NearbyAlerts` — `[remove from Home]`. Logic kept; `DiseaseTrends` becomes a Profile screen (later); `NearbyAlerts` data feeds Notifications. The components themselves can be deleted from Home composition but kept in the feature folder for reuse.

**`features/map-system/components/`**
- `MapControls` — vertical FAB stack on the right (locate, heatmap, zoom +/−).
- `MapFilters` — chip rail variant (top of map) replaces the existing UI; full sheet of filter sections still available via the gear icon.
- `MapMarker`, `HeatmapLayer` — colors aligned to severity tokens.
- `ReportPreviewCard` — same pattern as `RecentReports` row + tap to open detail.
- `ConnectionIndicator` — tiny pill that lives inside the search bar.

**`features/disease-analysis/components/`** (the report flow)
- Major rework. Need: `CaptureScreen`, `AnalyzingScreen`, `ResultScreen`, `SubmittedScreen` — broken into sub-components for the badge, recommendations card, edit-details inline form, candidate-picker (low confidence), map-share toggle.

**`features/upload-report/components/`**
- The non-AI parts (manual fallback form, plot location picker, image picker) are reused inside the new flow as the manual mode. Visuals updated to the new tokens.

**`features/notifications/components/`** — restyled per §5.5.

**`features/auth/components/`** — `AuthCard`, `GradientButton`, `OtpInput`, `PhoneInput` restyled per §5.7. `GradientButton` should merge into the new `Button` `gradient` variant.

**`features/plots/components/`** — `PlotCard`, `PlotFormSheet` restyled per §5.8. The crop chip selector becomes a standalone `ChipSelector` primitive (it appears in 3+ places).

**`features/toast/`** — light styling; success uses brand-tint, error uses danger-tint, info uses info-tint.

**`features/offline-sync/components/`** — `OfflineBanner`, `QueueCard`, `SyncStatusIndicator` restyled per §5.9.

**`theme/`** — `colors.ts`, `spacing.ts`, `radii.ts`, `shadows.ts`, `typography.ts` rewritten to the new tokens. Light-only (no dark theme path; `dark-mode` removed from scope).

**`global.css`** — Tailwind tokens regenerated to mirror `colors.ts`.

## 7. Out of scope

- Backend API changes. The FastAPI disease-detection endpoint is wired exactly as today.
- New features (no new tabs, no new entities). Trends widget on Profile is a placeholder section, not built in this redesign.
- Internationalization beyond what already exists (a Language setting row in Profile is shown but copy stays English).
- Tablet-specific layouts. App stays portrait phone-first.
- Dark mode. Project moves to light-only. The existing `dark` theme entries in `theme/colors.ts` are deleted along with the dark-mode `useColorScheme` branch in `_layout.tsx`; the app force-applies the light theme on launch.

## 8. Implementation principles

- **No new dependencies.** Everything is already installed (`@gorhom/bottom-sheet`, `expo-linear-gradient`, `lucide-react-native`, `react-native-reanimated`, `nativewind`, `expo-haptics`, `expo-image`).
- Update theme tokens first (`theme/`, `global.css`). Every other change inherits.
- Build the FAB-tab-bar early; everything else lives inside it.
- Restyle in this order to keep the app shippable mid-flight:
  1. Theme tokens + global.css
  2. UI primitives (`Button`, `Card`, `Input`, `Avatar`, `Skeleton`, `Loader`, `EmptyState`)
  3. Tab bar with FAB
  4. Home screen
  5. Report flow (capture → analyzing → result → submitted)
  6. Map screen
  7. Notifications
  8. Profile
  9. Auth + Onboarding
  10. Report detail
  11. Cross-cutting states (offline banner, toast)
- No feature flags. Branches are short — restyle a screen, verify with `pnpm --filter mobile typecheck` and `expo start`, move on.
- Respect `apps/mobile/AGENTS.md`: read https://docs.expo.dev/versions/v56.0.0/ before writing code that touches Expo APIs (camera, permissions, notifications).

## 9. Acceptance criteria

The redesign is done when:

1. Every route in `apps/mobile/src/app/**` renders in the new visual system with no traces of the old dark navy palette.
2. Tapping the center FAB on any tab opens the report flow.
3. The report flow demonstrates online → offline → manual fallback successfully (mocked FastAPI call) and shows the correct engine badge in each case.
4. The map screen has search, filter chips, FAB stack, and a draggable bottom sheet listing reports in view.
5. Skeleton, empty, error, and offline states use the new visual treatment.
6. `pnpm --filter mobile typecheck` and `pnpm --filter mobile lint` pass.
7. The app boots, signs in via OTP, completes onboarding, submits a report, and views it on the map without runtime errors.
