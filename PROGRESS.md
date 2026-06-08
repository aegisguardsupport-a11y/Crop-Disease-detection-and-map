# Project Progress — Crop Disease Report Mapping System

> **Last updated:** 2026-05-29
> **Current version:** v11 — On-device AI (offline TFLite)
> **Status:** ✅ 11 versions complete. Offline crop-disease inference now runs fully on-device as a cloud fallback. Requires a native dev build (not Expo Go).

This is the living source of truth for what's done, what's partial, what's missing, and where the technical debt lives. Update at the end of every version (see "Update protocol" at the bottom).

---

## Quick status

| Version | Title | Status |
| ------- | ----- | ------ |
| v1 | Foundation Setup | ✅ Done |
| v2 | Authentication | ✅ Done |
| v3 | Home Dashboard UI | ✅ Done |
| v4 | Report Upload (camera + Cloudinary + offline queue) | ✅ Done |
| v5 | AI Disease Detection (mock AI, async processing, result screen) | ✅ Done |
| v6 | Realtime Outbreak Map (live markers, clustering, heatmap, outbreak zones) | ✅ Done |
| v7 | Outbreak Engine (intelligent detection, escalation, resolution, detail UI) | ✅ Done |
| v8 | Notifications System + Plots (in-app banners, push, plot-based fan-out, lite onboarding) | ✅ Done |
| v9 | Offline Support (idempotent uploads, query persistence, connectivity UI, on-device AI placeholder) | ✅ Done |
| v10 | Polish, Performance & Demo (error boundary, demo seed, deployment, branded splash) | ✅ Done |
| v11 | On-device AI (offline TFLite classifier, 139 classes, cloud fallback) | ✅ Done |

---

## Stack snapshot

| Layer | Tech | Version |
| ----- | ---- | ------- |
| Monorepo | pnpm workspaces + Turborepo | pnpm 10.33, turbo 2.9 |
| Language | TypeScript (strict, `noUncheckedIndexedAccess`) | 5.9 |
| Backend | NestJS | 10.4 |
| ORM / DB | Prisma + Postgres (Neon) | Prisma 5.22 |
| Auth | passport-jwt + @nestjs/jwt | passport-jwt 4 |
| Logging | nestjs-pino + pino-pretty | nestjs-pino 4.4 |
| Realtime | @nestjs/websockets + Socket.IO | socket.io 4.8 |
| Image hosting | Cloudinary (signed direct upload) | cloudinary 2.x |
| Backend HTTP client | axios (FastAPI integration) | axios 1.x |
| Validation | Zod (env) + class-validator (DTOs) | zod 3.24 |
| Mobile runtime | Expo SDK + Expo Router | SDK 56, Router 56.2 |
| RN | React Native + React | RN 0.85, React 19.2 |
| Styling | NativeWind v5 + Tailwind v4 (via react-native-css) | NW 5.0.0-preview.2 |
| State | Zustand | 5.x |
| Server state | TanStack Query | 5.x |
| HTTP | axios + interceptors | 1.x |
| Lists | @shopify/flash-list | 2.3 |
| Icons | lucide-react-native + react-native-svg | lucide 1.16 |
| Effects | expo-linear-gradient + expo-glass-effect | both 56.x |
| Native input | expo-image-picker + expo-camera APIs | 56.0.14 |
| Geolocation | expo-location | 56.0.14 |
| Image compression | expo-image-manipulator | 56.0.15 |
| On-device inference | react-native-fast-tflite (JSI/Nitro) + react-native-nitro-modules | tflite 3.0.1 / nitro 0.35.9 |
| On-device model | CPL MobileNetV3-Small TFLite (139 crop::disease classes, 1.22 MB) | float32 [0,255] |
| JPEG decode (preprocess) | jpeg-js + buffer | jpeg-js 0.4 / buffer 6.0 |
| File storage | expo-file-system (`Paths` / `File` / `Directory` API) | 56.0.7 |
| Maps | react-native-maps | 1.27.2 |
| Map clustering | supercluster (Mapbox) | 8.0.1 |
| Cron / scheduling | @nestjs/schedule | 4.1.x |
| Push notifications | expo-server-sdk + expo-notifications | server 3.10 / mobile 56.0.14 |
| Connectivity | @react-native-community/netinfo | 12.0.1 |
| Query persistence | @tanstack/react-query-persist-client + async-storage-persister | 5.100.x |
| Idempotency keys | uuid | 14.0 |
| Error boundaries | react-error-boundary | 6.1 |
| Storage | expo-secure-store + @react-native-async-storage/async-storage | 56.x / 2.x |

---

## Current end-to-end behavior

1. Cold boot → native splash → in-app gradient splash with brand mark → auth store hydrates from SecureStore + AsyncStorage; offline-queue store hydrates from AsyncStorage in parallel.
2. Unauthenticated → `/(auth)/login` → enter `9999999999` → backend creates `OtpToken` row in Neon → push to `/(auth)/otp`.
3. Enter `123456` → backend marks token consumed, upserts `User`, signs JWT (7d expiry) → token to SecureStore, user to AsyncStorage → router redirects to `/(app)`.
4. Tab navigator with 5 tabs (Home, Map, Upload-FAB, Alerts, Profile) inside a glass floating bar.
5. Home dashboard fetches mock data via `useDashboard` (700ms simulated latency to show shimmer), pull-to-refresh works, sections animate in staggered.
6. **Upload tab** — pick photo (camera or gallery) → choose crop from searchable bottom sheet of 25 crops → location auto-detected via GPS or manually pinned on `MapView` → optional notes (≤500) → submit:
   - **Online:** image is compressed (≤1600px, JPEG q=0.7) → uploaded directly to Cloudinary using a server-issued signature → backend `POST /reports` returns immediately with `processingStatus=PENDING` → `useCreateReport` seeds the detail query and `router.replace`s to `/reports/[id]`.
   - **Offline:** image is compressed and copied into `documentDirectory/uploads/` → enqueued in the persistent `upload.queue.v1` store → user sees "Queued" state.
   - **Analysis engine chain (report-flow):** the analyzing step tries cloud first (8s timeout); if cloud fails or times out, the **on-device TFLite classifier** (v11) runs the bundled MobileNetV3 model fully offline and returns a real `crop::disease` diagnosis + confidence + curated severity/recommendations (badge: "On-device AI"); only if that's also unavailable does it fall to manual entry. Requires a native dev build — not Expo Go.
7. **Result screen `/reports/[id]`** — shows the `ProcessingState` (scanline animation + corner brackets + cycling status text) while `processingStatus ∈ {PENDING, PROCESSING}`. TanStack Query polls `GET /reports/:id` every 3s; polling stops on terminal status. Backend's `ReportsProcessor` (fire-and-forget) calls `AiService` which routes to `MockAiClient` or `FastApiAiClient` based on `AI_PROVIDER` env. On success, the row is updated with `disease`, `confidence`, `severity`, `recommendations`, `processedAt`. The screen swaps to the success layout: animated `ConfidenceRing` (SVG arc gauge), severity badge (with pulsing dot for HIGH), recommendations list (staggered glass cards), action row (View on map, Share, New report). On AI failure, the screen shows a retry CTA which calls `POST /reports/:id/reprocess`.
8. **Map tab `/map`** — full-screen `MapView` (Apple Maps on iOS, Google Maps on Android with custom dark JSON style in dark mode). On mount: `useUserLocation` requests permission and watches at 30s/100m, `useNearbyReports` fetches from `GET /reports/nearby` with the current region as query, `useRealtimeReports` subscribes to socket events, `useOutbreaks` seeds outbreak zones, `useActivePlots` renders the user's own plots as small home-tinted markers. Reports are clustered via `supercluster`; each visible cluster renders as `MapCluster` (count + dominant-severity color), each leaf as `MapMarker` (severity-colored, custom emoji, pulsing ring on HIGH). Outbreak zones render via `OutbreakZoneLayer` (severity-tinted `Circle` + animated hotspot core + pill marker). Heatmap layer (`react-native-maps`'s native `<Heatmap>`) renders severity-weighted points. Floating glass controls: locate-me, layer toggle, filter sheet (with "Show resolved" + outbreak severity / time-window options). Top: a glass `ConnectionPill` showing live status + report count. Tap a report marker → `ReportDetailSheet`; tap an outbreak zone → `OutbreakDetailSheet`.
9. **Filter sheet** — Time window (24h / 7d / 30d / All) + multi-select severity / crop / disease (the disease list is dynamically built from currently visible reports). Filters apply both server-side (single-select cases sent in the query) and client-side (multi-select / live socket data). Bottom CTA shows the live count of matching reports.
10. **Realtime backend** — When a Report's AI analysis succeeds, `ReportsProcessor` emits `report.created` over Socket.IO globally and hands off to `OutbreakProcessor.handleNewReport`. The processor either attaches the report to a matching active zone (recomputing centroid + severity), creates a new zone if ≥`OUTBREAK_CREATE_THRESHOLD` (default 5) same-disease SUCCESS reports exist within `OUTBREAK_CREATE_RADIUS_KM` (default 3km) in the last 24h, or does nothing yet. Severity escalates from `LOW` → `MEDIUM` at `OUTBREAK_ESCALATE_THRESHOLD` (default 10) reports → `HIGH` at `OUTBREAK_HIGH_REPORT_COUNT` (default 20) or `OUTBREAK_HIGH_SEVERITY_COUNT` (default 5) HIGH-severity contributing reports. `OutbreakScheduler` runs every 2 minutes and resolves zones with no new reports for `OUTBREAK_DEACTIVATE_HOURS` (default 48), emitting `outbreak.resolved`. `map.updated` ticks (throttled, ≤1/5s) accompany every event. WebSocket connections are JWT-protected via `io.use(...)` middleware and joined into per-user rooms (`user:${userId}`).
11. **Notifications fan-out** — Every outbreak/report processor event passes through `NotificationsFanoutService`:
    - `outbreak.created` → finds users whose **active plots** are within `zone.radius + NOTIFICATION_NEARBY_BUFFER_KM` (5km default), filters by preferences, dedups against last 24h, persists `Notification` rows, emits `notification.created` per user (per-user socket room), and pushes via Expo.
    - `outbreak.escalated` → notifies only users previously notified about that outbreak.
    - `outbreak.resolved` → same recipient set as escalated.
    - `report.created` (HIGH severity only) → users with active plots within 5km of the report, excluding the reporter themselves.
12. **Onboarding (lite)** — After OTP verify, first-time users with no name AND no plots are routed to `/(onboarding)/name` → `/(onboarding)/first-plot`. They can skip; the choice is persisted in AsyncStorage as `onboarding.skipped.v1`. Plot management is also exposed permanently in the Profile tab.
11. **Outbreak detail sheet** — Tap any zone marker on the map → `OutbreakDetailSheet` opens (45% / 92% snap). Hero shows disease name, severity badge, active/resolved tag. Stats grid: total reports, HIGH-severity count, radius (km), last-report time-ago. Affected crops chips (with emoji). Mini map preview (lite mode, non-interactive) showing the zone circle. List of up to 8 most recent contributing reports — tap any to navigate to its full report screen. Prevention guidance pulled from the first contributing report's recommendations.
12. Drainer (`useOfflineQueue`) listens to `NetInfo`; once connected it walks `pending` items, retries each with the same Cloudinary + reports pipeline, applies exponential backoff (1m, 5m, 15m, 1h, 6h capped) on failure, and stops after 5 attempts. The `PendingUploadsSection` on the upload screen shows queue items with retry / discard.
13. Any 401 from axios → global `setUnauthorizedHandler` runs `logout()` → SecureStore + AsyncStorage cleared, socket disconnected → router redirects to login.
14. Logout from Profile tab works the same way; explicit user-initiated.
15. `/health` is the only public endpoint; everything else (auth, uploads, reports, /reports/nearby, /outbreaks, /outbreaks/:id, future routes) requires `Authorization: Bearer <jwt>` and is enforced globally via `JwtAuthGuard` registered as `APP_GUARD` (opt-out via `@Public()`).

---

## Per-version detail

### v1 — Foundation Setup ✅

**Backend**
- NestJS app with global `ValidationPipe`, `AllExceptionsFilter`, `TransformInterceptor` (consistent `{ success, data, timestamp }` envelope).
- `PrismaModule` (lifecycle hooks + `healthCheck()` via `SELECT 1`).
- `HealthController` returning `{ status, uptime, timestamp, db }`.
- `RealtimeGateway` (Socket.IO, polling + websocket).
- Zod env validation that refuses to boot with bad env.
- Helmet, compression, CORS from env.
- Initial Prisma migration `20260526091446_init` — `User` model with `UserRole` enum and `(state, district)` index.

**Mobile**
- Expo Router scaffold with strict TS + `@/*` path alias.
- NativeWind v5 + Tailwind v4 wired via `withNativewind` Metro plugin and CSS-first `global.css`.
- Theme tokens in `src/theme/` (colors, spacing, radii, shadows, animations, typography), mirrored into Tailwind via CSS variables.
- Providers stacked in `app/_layout.tsx`: GestureHandler → SafeArea → Query → Theme → Socket → BottomSheetModal → NavTheme.
- 8 reusable components: Button, Input, Card, Loader, ScreenContainer, BottomSheetWrapper, EmptyState, SectionHeader.
- Services scaffolded: axios client (with auth header attach), Socket.IO singleton, secure-store + async-storage helpers.
- Zustand auth store stub (no persistence yet).
- Showcase home screen rendering all 8 components + live `/health` polling.

### v2 — Authentication ✅

**Backend**
- New migration `20260526100650_auth_v2`: nullable `name/district/state`, new `OtpToken` model with TTL (5 min) + attempts cap (5).
- `AuthModule` wires `JwtModule` (async, env-driven secret + expiry) and `PassportModule`.
- `AuthService` — stateful mock OTP: only `9999999999` is accepted; only `123456` verifies; user is upsert-ed on first verify.
- `AuthController` — `POST /auth/send-otp` + `POST /auth/verify-otp` (both `@Public()`); `GET /auth/me` (protected).
- DTOs (`SendOtpDto`, `VerifyOtpDto`) with class-validator regex for 10-digit phone + 6-digit OTP.
- `JwtStrategy` extracts Bearer, validates user still exists, attaches to `req.user`.
- `JwtAuthGuard` rewritten on top of `passport-jwt`, registered as `APP_GUARD` so every route is protected by default.
- `@Public()` decorator + Reflector lookup, also marks `/health`.

**Mobile**
- Auth store: `hydrate / setSession / setUser / logout`. Token in SecureStore, user in AsyncStorage. `isAuthenticated` derived flag.
- `_layout.tsx` runs `hydrate()` on boot and holds the splash + brand-gradient overlay until done; calls `setUnauthorizedHandler(logout)` so any 401 anywhere triggers logout.
- Route groups `(auth)` and `(app)` with `<Redirect />`-based gating in their `_layout.tsx`.
- `features/auth/` feature module:
  - `api/auth.api.ts` — typed `sendOtp / verifyOtp / me`.
  - `hooks/` — `useSendOtp`, `useVerifyOtp` (commits session on success), `useMe`.
  - `components/` — `AuthCard` (glassmorphism via `expo-glass-effect`), `GradientButton` (linear-gradient + haptics), `PhoneInput` (fixed +91, 10-digit mask), `OtpInput` (6 cells, autofocus, reanimated shake on error, hidden master input for paste/SMS autofill).
- Login + OTP screens with gradient backdrops, demo creds shown inline.
- Logout button on home (later moved to Profile in v3).

### v3 — Home Dashboard UI ✅

**Navigation**
- `(app)/_layout.tsx` switched from `Stack` to `Tabs` with custom `tabBar` prop.
- `components/navigation/tab-bar.tsx` — 5 tabs in a floating glass bar (16px gutter), active icon fill, selection haptics on tab press, FAB-style center upload button.
- `tab-bar-icon.tsx` uses `lucide-react-native` (`House / Map / Plus / Bell / User`).

**Dashboard (`features/dashboard/`)**
- `types.ts` — `Severity`, `Report`, `Outbreak`, `Trend`, `Alert`, `DashboardSummary`, `DashboardData`.
- `mocks/dashboard.mock.ts` — 3 outbreaks, 5 reports, 4 trends, 4 alerts, summary.
- `api/dashboard.api.ts` — fake service with 700ms `sleep` so shimmer is visible.
- `hooks/use-dashboard.ts` (TanStack Query, 60s staleTime), `hooks/use-greeting.ts`.

**Reusable cards (memoized)**: `OutbreakCard`, `ReportCard`, `StatCard` (raf counter + sparkline), `NotificationPreviewCard`.

**Sections**: `GreetingHeader`, `OutbreakSummary`, `QuickUploadCTA`, `RecentReports`, `DiseaseTrends`, `NearbyAlerts`.

**New primitives**: `Skeleton` (shimmer), `Avatar` (initials).

**Other tab screens**: `map.tsx` placeholder, `upload.tsx` visual-only (replaced in v4), `notifications.tsx` full FlashList, `profile.tsx`.

**Verification:** typecheck/lint/iOS bundle (6.6MB, 3826 modules) clean.

### v4 — Report Upload ✅

**Backend**
- Migration `20260526111932_add_reports`:
  - `Report` model — `userId` FK with cascade, `cropType`, `imageUrl`, `imagePublicId`, optional `notes`, `latitude/longitude`, `createdAt/updatedAt`, indexes on `(userId, createdAt)` and `(latitude, longitude)`.
  - `User.reports` back-relation.
- `CloudinaryModule` — `CloudinaryService` configures the SDK from env, signs `{ timestamp, folder }` via `cloudinary.utils.api_sign_request`. `CloudinaryController` exposes `POST /uploads/signature`.
- `ReportsModule` — DTOs (`CreateReportDto`, `ListReportsQueryDto`), `ReportsService` (create, cursor-paginated list, ownership-scoped findById), `ReportsController` (`POST /reports` 201, `GET /reports?scope`, `GET /reports/:id`).
- New env vars: `CLOUDINARY_*`. Validated in `env.schema.ts`.

**Mobile — `features/upload-report/`**
- `types.ts`, `api/cloudinary.api.ts`, `api/reports.api.ts`.
- `hooks/`: `useImagePicker`, `useCurrentLocation`, `useCreateReport` (state machine), `useOfflineQueue` (NetInfo-driven drainer with backoff).
- `store/offline-queue.store.ts` — Zustand + manual AsyncStorage persistence; resets stuck `uploading` items on hydrate.
- `utils/`: `compress-image.ts` (`ImageManipulator.manipulate` API, ≤1600px JPEG q=0.7), `file-storage.ts` (Paths/File/Directory), `upload-states.ts` (labels + backoff schedule).
- `components/`: `ImagePickerCard`, `CropPickerRow`, `CropPickerSheet`, `LocationCard`, `MapPickerSheet` (react-native-maps + draggable marker), `NotesInput`, `UploadProgress`, `UploadSuccess` (replaced in v5), `PendingUploadsSection`.
- `_layout.tsx` hydrates queue store and runs `useOfflineQueue(isAuthenticated && bootDone)`.
- `constants/crops.ts` — 25 crops with `{ id, name, emoji, category }`.

**Verification:** 7 backend curl scenarios green, typecheck/lint clean, iOS bundle 6.9MB / 3926 modules.

### v5 — AI Disease Detection ✅

**Backend — schema additions**
- Migration `20260526115349_add_disease_diagnosis`:
  - New enums `Severity` (LOW/MEDIUM/HIGH) and `ProcessingStatus` (PENDING/PROCESSING/SUCCESS/FAILED).
  - `Report` extended with `disease String?`, `confidence Float?`, `severity Severity?`, `recommendations String[] @default([])`, `processingStatus ProcessingStatus @default(PENDING)`, `aiError String?`, `processedAt DateTime?`. Index on `processingStatus` for future job sweepers.
- New env vars: `AI_PROVIDER` enum (`mock | fastapi`, default `mock`). Validated in `env.schema.ts`.

**Backend — `modules/ai/`**
- `clients/ai.client.ts` — `AiClient` interface every provider implements.
- `clients/mock-ai.client.ts` — deterministic mock. Same `(imageUrl, cropType)` always yields the same diagnosis. 1.5–2.2s simulated latency. ~12% chance of "Healthy crop", otherwise picks from per-crop catalog. Confidence has small jitter (±3) on top of catalog base.
- `clients/fastapi.client.ts` — real client. Posts `{ image_url, crop_type, notes }` to `${FASTAPI_URL}/predict`, 35s timeout (with 10s buffer above the expected 25s upstream latency). Tolerates response shape variations (severity casing, 0–1 vs 0–100 confidence). Returns `{ ok: false, errorCode: TIMEOUT|UPSTREAM_ERROR|INVALID_RESPONSE|UNKNOWN }` on failure.
- `disease-catalog.ts` — 9 crops with 1–2 diseases each (Tomato, Potato, Rice, Wheat, Maize, Cotton, Grape, Chili, Onion). Each entry has `disease`, `baseConfidence`, `severity`, and 3–5 recommendations covering cultural / chemical / monitoring. `GENERIC_FALLBACK` and `HEALTHY_RESULT` for crops without entries.
- `ai.service.ts` — facade. Reads `AI_PROVIDER`, picks client, calls `analyze`. On retryable failure (TIMEOUT or UPSTREAM_ERROR), retries once. Always returns a normalized `AnalysisResult`.
- `ai.module.ts` — registers all clients + `AiService`. Exports `AiService`.

**Backend — reports flow change**
- `reports.processor.ts` (NEW) — `schedule(report)` is fire-and-forget; runs the AI call and persists the result. Errors are caught and persisted as `FAILED` so the user always lands on a valid result screen.
- `reports.service.ts` — `create()` now persists with `PROCESSING_STATUS=PENDING` and calls `processor.schedule(report)` before returning. New `reprocess(userId, id)` method: refuses while `PROCESSING`, otherwise resets row to `PENDING` and re-schedules.
- `reports.controller.ts` — adds `POST /reports/:id/reprocess` (owner-only). All other routes unchanged.
- `reports.module.ts` — imports `AiModule`, registers `ReportsProcessor`.
- The HTTP request to `POST /reports` now returns immediately (~50ms instead of 25+ seconds).

**Mobile — types**
- `Report` extended with `disease | confidence | severity | recommendations | processingStatus | aiError | processedAt` (matching the Prisma shape).
- `Severity` and `ProcessingStatus` types added alongside.
- `severityVisuals` updated to accept both lowercase (mock) and uppercase (backend) severity strings; case-insensitive normalization happens once.

**Mobile — `features/disease-analysis/`**
- `api/disease.api.ts` — `getReport(id)`, `reprocess(id)`.
- `hooks/use-report.ts` — TanStack Query keyed by `['reports', id]` with conditional `refetchInterval` (3s while non-terminal, false on SUCCESS/FAILED). Companion `useReprocessReport` mutation that updates the cache directly on success.
- `components/`:
  - `confidence-ring.tsx` — animated SVG gauge. 270° arc, gradient stroke (brand → severity color), animated `strokeDashoffset` via reanimated `useAnimatedProps`, paired with a raf-driven counter for the centered number.
  - `processing-state.tsx` — full-screen scan effect over the photo: dimming overlay, animated horizontal scan line (1.6s up + 1.6s down infinite), four corner brackets, glass "Analyzing" pill with pulsing dot, cycling status text below.
  - `result-hero.tsx` — image with severity colored top strip + bottom gradient + "AI · Diagnosis" corner badge.
  - `severity-badge.tsx` — colored pill; pulses dot when severity is HIGH.
  - `recommendations-list.tsx` — staggered glass cards with sparkle icon container; empty-state when none.
  - `result-actions.tsx` — three secondary buttons: View on map (navigates to `/map`), Share (RN `Share` API with diagnosis text), New report (back to `/upload`).

**Mobile — wiring**
- New route `app/reports/[id].tsx`. Header with back button, gradient backdrop, branches on `processingStatus`:
  - PENDING/PROCESSING → `<ProcessingState>` (no spinner; the scan animation IS the spinner).
  - SUCCESS → `<SuccessContent>`: hero, glass card with confidence ring + disease + severity badge + processed-time, optional notes block, "What we recommend" header + `<RecommendationsList>`, `<ResultActions>`, advisory disclaimer.
  - FAILED → glass error card with `aiError` text and a "Retry analysis" button hitting `useReprocessReport`.
- `useCreateReport` updated: on backend create success it seeds `queryClient.setQueryData(['reports', id], created)` and `router.replace`s to the detail route. The legacy `<UploadSuccess>` overlay is no longer rendered (file kept for reference but not imported).
- Upload screen no longer needs a "handleReset" path — navigation away handles cleanup.

**Verification**
- Backend curl smoke: `POST /reports` returns immediately with `PENDING`; 3s later `GET /reports/:id` returns `SUCCESS` with disease populated; `POST /reports/:id/reprocess` flips to PENDING and re-runs cleanly.
- Backend typecheck/lint clean.
- Mobile typecheck/lint clean.
- iOS bundle 6.9MB / 3926 modules clean.

### v6 — Realtime Outbreak Map ✅

**Backend — schema additions**
- Migration `20260526123454_add_outbreak_zones`:
  - New `OutbreakZone` model: `disease`, `centerLat / centerLng`, `radiusMeters` (default 5000), `reportCount`, `highCount`, `severity`, `firstSeenAt / lastSeenAt`. Indexes on `(centerLat, centerLng)` and `(disease, lastSeenAt)`.

**Backend — `modules/realtime/`**
- `realtime.gateway.ts` extended with `JwtService` injection and `afterInit` registration of the WS middleware.
- `realtime.service.ts` — emit helpers (`reportCreated`, `outbreakCreated`, `outbreakUpdated`) plus a throttled `map.updated` tick (max once / 5s) so a flurry of reports doesn't spam clients.
- `ws-jwt.middleware.ts` — `io.use(...)` middleware that verifies the handshake `auth.token` (or `Authorization: Bearer ...` header fallback) via `JwtService.verifyAsync`. Attaches the payload to `socket.data.user`. Rejected handshakes trigger Socket.IO's reconnect loop.
- `realtime.module.ts` now imports `AuthModule` to get `JwtService` and exports `RealtimeService`.

**Backend — reports / outbreak detection**
- `geo.util.ts` — `boundingBox(lat, lng, radiusKm)` and `haversineKm(...)` helpers used by `findNearby` + outbreak detection.
- `dto/nearby-reports-query.dto.ts` — `lat`, `lng`, `radiusKm` (1–1000, default 50), `limit` (1–500, default 200), optional `disease / cropType / severity / since`.
- `reports.controller.ts` — adds `GET /reports/nearby` (auth-protected, but not ownership-scoped — the map shows all SUCCESS reports).
- `reports.service.ts.findNearby` — bbox pre-filter via Postgres index, haversine refinement in memory, only returns `processingStatus=SUCCESS` reports. Limits the candidate fetch to 3× the request limit (max 1500).
- `reports.processor.ts`:
  - On AI SUCCESS, calls `realtime.reportCreated(updated)` to broadcast the row.
  - Runs `detectOutbreak(updated)`: looks for an existing OutbreakZone within 5km for the same disease; if found, bumps `reportCount`, `highCount`, peak `severity`, and `lastSeenAt`. Otherwise, if there are ≥3 SUCCESS reports of the same disease within 5km in the last 24h, creates a new zone centered on the new report and emits `outbreak.created`.
  - **Startup sweeper** (`OnModuleInit`) — resets any `processingStatus=PROCESSING` rows whose `updatedAt` is older than 5 minutes back to `PENDING`, protecting against process crashes mid-AI.
- `reports.module.ts` now imports `RealtimeModule`.

**Backend — events**

| Event | Payload | When |
|---|---|---|
| `report.created` | `{ report }` | After `ReportsProcessor` writes SUCCESS for a report |
| `outbreak.created` | `{ zone }` | When a fresh OutbreakZone is created |
| `outbreak.updated` | `{ zone }` | When an existing zone's counts change |
| `map.updated` | `{ at: ISO }` | Throttled (5s) tick after any of the above |

**Mobile — `features/map-system/`**
- `types.ts` — `OutbreakZone`, `NearbyReportsResponse`, `MapLayerMode` (`markers | heatmap | both`), `DateWindow` (`24h | 7d | 30d | all`), `MapFilters`, `MapRegion`.
- `api/nearby.api.ts` — `mapApi.nearby({ lat, lng, radiusKm, limit, severity, cropType, disease, since })`.
- `store/live-reports.store.ts` — Zustand id-keyed map of `Report` and `OutbreakZone`. **In-memory cap of 1000 reports** — trims oldest by `createdAt` when exceeded. Exposes `setMany`, `upsertReport`, `upsertOutbreak`, `setOutbreaks`, `clear`.
- `store/map-filters.store.ts` — Zustand filter state (`crops`, `diseases`, `severities`, `window`, `layerMode`). Includes `hasActiveFilters()` selector and `windowToSinceIso(window)` helper.
- `utils/`:
  - `haversine.ts` — `haversineKm` + `formatDistanceKm`.
  - `cluster.ts` — `buildClusterIndex(reports)`, `getClusters(index, region)`, `regionToZoom(region)`. Uses `supercluster` (Mapbox engine) with `radius: 60`, severity-aware reducer that aggregates `highCount / mediumCount / lowCount` per cluster.
  - `map-style.ts` — custom dark Google Maps JSON (Android only; iOS Apple Maps handles dark mode automatically).
- `hooks/`:
  - `useUserLocation(enabled)` — requests permission, one-shot fetch, then `watchPositionAsync` at 30s / 100m. Returns `{ location, permission, refresh }`.
  - `useNearbyReports(params)` — TanStack Query, `staleTime=15s`, **`refetchInterval=30s` polling fallback** (safety net if the socket drops without us noticing). Seeds the `live-reports` store on each fetch.
  - `useRealtimeReports()` — subscribes to `report.created`, `outbreak.created`, `outbreak.updated` and pushes into the live store.
- `components/`:
  - `MapMarker` — severity-colored 32×32 disc with white border + crop emoji. Pulse ring (reanimated `withRepeat`) only on HIGH severity for performance.
  - `MapCluster` — count + dominant-severity color (HIGH > MEDIUM > LOW). Sized 40 / 48 / 56 by count buckets. `1.2k` formatting at ≥1000.
  - `OutbreakZoneOverlay` — translucent `Circle` overlay (severity-tinted) + pulsing badge `Marker` showing disease + report count.
  - `HeatmapLayer` — wraps `react-native-maps`'s `<Heatmap>`. Severity-weighted (HIGH=1.0, MEDIUM=0.6, LOW=0.3). Skipped automatically when 0 reports.
  - `ConnectionPill` — glass pill, top-left. Pulsing green dot + "Live · N reports" when connected; static amber + "Offline" when not.
  - `MapControls` — vertical stack of three glass icon buttons: Locate-me, Layer toggle (cycles markers → heatmap → both), Filter (with brand-color dot when filters are active).
  - `MapFilterSheet` — `BottomSheetModal` (85% snap). Time window quick-chips, multi-select severity / crop / disease (disease list dynamically built from currently visible reports). Footer: Reset + "Show N reports" CTA.
  - `ReportDetailSheet` — `BottomSheetModal` (38% / 92% snap). Crop image, mini `ConfidenceRing`, `SeverityBadge`, distance pill, time-ago, farmer notes, recommendations (re-uses v5 components), and "Open full report" → `/reports/[id]`.

**Mobile — types**
- New `src/types/supercluster.d.ts` — inline type declarations for `supercluster@8.0.1`. The community `@types/supercluster` package didn't resolve cleanly under our pnpm setup, so we declare exactly what we use (~50 lines).

**Mobile — map screen rebuild (`app/(app)/map.tsx`)**
- Full-screen `MapView` (`provider=PROVIDER_GOOGLE` on Android, default Apple Maps on iOS). `customMapStyle` applies the dark JSON only on Android in dark mode. `showsUserLocation` enabled.
- One-shot recenter on the user's current location when `useUserLocation` first resolves.
- Region debouncing: `onRegionChangeComplete` writes to state; the `nearby` query keys off the region so panning refetches with a new center.
- Memoized cluster index recomputes when filtered reports change. Cluster tap animates the camera to the supercluster expansion zoom.
- Layer toggle cycles between markers / heatmap / both (defaults to markers).
- Permission-denied banner at the bottom with an "Allow" button.
- All `<Marker>`s use `tracksViewChanges={false}` to avoid render storms during pan.

**Mobile — dashboard real data swap**
- `features/dashboard/api/dashboard.api.ts` now fetches `reportsApi.list({ scope: 'mine', limit: 5 })`, maps each to the dashboard's local `Report` shape (severity uppercase → lowercase), and replaces the `recentReports` section. Falls back to mock seed data if the network call fails or the user has no reports yet so the demo always looks alive. Outbreaks / trends / alerts / summary remain mocked.

**Verification**
- Backend curl: `GET /reports/nearby?lat=18.52&lng=73.85&radiusKm=100` returns the seeded report; severity filter applies correctly.
- Backend typecheck / lint clean.
- Mobile typecheck / lint clean (1 cosmetic axios warning carried over).
- iOS bundle 7.0MB.

### v7 — Outbreak Engine ✅

**Backend — schema migration `outbreak_engine_v7`**
- Renamed v6 columns: `centerLat → latitude`, `centerLng → longitude`, `radiusMeters (Int) → radius (Float)`. Default radius now 3000m (the v7 create radius).
- Added `affectedCropTypes String[] @default([])` so the detail sheet can show "Tomato + Potato" without re-querying.
- Added `active Boolean @default(true)` and `resolvedAt DateTime?` to support the deactivation lifecycle.
- Dropped `firstSeenAt` (subsumed by `createdAt`).
- New index `(active, lastSeenAt)` for the scheduler's sweep query.

**Backend — env additions**
- `OUTBREAK_CREATE_THRESHOLD` (default 5)
- `OUTBREAK_CREATE_RADIUS_KM` (default 3)
- `OUTBREAK_ESCALATE_THRESHOLD` (default 10)
- `OUTBREAK_ESCALATE_RADIUS_KM` (default 5)
- `OUTBREAK_HIGH_REPORT_COUNT` (default 20)
- `OUTBREAK_HIGH_SEVERITY_COUNT` (default 5)
- `OUTBREAK_DEACTIVATE_HOURS` (default 48)

All validated by Zod, with sane defaults. Changing them is one env edit + restart away.

**Backend — `modules/outbreak/`**
- `outbreak.module.ts` — wires the controller, service, processor, and scheduler. Imports `RealtimeModule`. Exports `OutbreakService` + `OutbreakProcessor`.
- `dto/list-outbreaks-query.dto.ts` — `active` (default true), `disease`, `severity`, `since` (default 30d ago), `limit`.
- `outbreak.controller.ts` — `GET /outbreaks` and `GET /outbreaks/:id`. Both auth-protected.
- `outbreak.service.ts` — `list(query)` filtered by `lastSeenAt >= since`, sorted by `lastSeenAt desc`. `findById(id)` returns `{ zone, contributingReports }` with up to 20 most recent same-disease SUCCESS reports inside the zone.
- `outbreak.processor.ts` — single entry point `handleNewReport(report)` called by `ReportsProcessor` after AI SUCCESS. Decides between attach / create / no-op:
  - **Attach** — finds the closest active zone for this disease whose radius covers the report; running-average centroid update, increments report/high counts, recomputes severity, broadens crop list, updates `lastSeenAt`, may expand radius to escalate radius. Emits `outbreak.updated`.
  - **Create** — fires when no zone matches AND ≥`CREATE_THRESHOLD` SUCCESS reports of the same disease exist within `CREATE_RADIUS_KM` in the last 24h. Centroid = mean of those contributing reports. Emits `outbreak.created`.
  - **Severity rule** — `HIGH` if `reportCount ≥ HIGH_REPORT_COUNT` OR `highCount ≥ HIGH_SEVERITY_COUNT`; `MEDIUM` if `reportCount ≥ ESCALATE_THRESHOLD`; `LOW` otherwise.
  - `deactivateStaleZones()` — bulk-resolves zones whose `lastSeenAt < now - DEACTIVATE_HOURS`. Emits `outbreak.resolved` per zone.
- `outbreak.scheduler.ts` — `@Cron('*/2 * * * *')` calls `deactivateStaleZones()` every 2 minutes. Logs failures but doesn't crash the app.
- `common/utils/geo.utils.ts` — moved here from `reports/geo.util.ts`. Adds `rollingCentroid(prior, priorCount, next)` for incremental centroid updates.

**Backend — refactor**
- `ReportsProcessor.detectOutbreak` removed. Now calls `this.outbreak.handleNewReport(updated)` after persisting AI success. Cleaner separation: reports own AI, outbreaks own clustering.
- `RealtimeService.outbreakResolved(zone)` added — emits `outbreak.resolved` and ticks `map.updated`.
- `app.module.ts` registers `ScheduleModule.forRoot()` and `OutbreakModule`.
- Existing `Reports` calls / endpoints unchanged.

**Backend — endpoints**

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/outbreaks` | protected | List zones (defaults: `active=true`, `since=30d ago`, `limit=200`). |
| GET | `/outbreaks/:id` | protected | Single zone + up to 20 contributing reports. |

**Backend — events**

| Event | Payload | When |
|---|---|---|
| `report.created` | `{ report }` | After AI SUCCESS (unchanged from v6) |
| `outbreak.created` | `{ zone }` | When `OutbreakProcessor` creates a fresh zone |
| `outbreak.updated` | `{ zone }` | When an existing zone's centroid / counts / severity / radius change |
| `outbreak.resolved` | `{ zone }` | When the scheduler marks a zone `active=false` |
| `map.updated` | `{ at: ISO }` | Throttled (5s) tick after any of the above |

**Mobile — `features/outbreak-system/`**
- `api/outbreak.api.ts` — `list({ active, disease, severity, since, limit })`, `findById(id)`. Returns `OutbreakZone[]` and `{ zone, contributingReports }` respectively.
- `hooks/use-outbreaks.ts` — `useOutbreaks(params)` (initial fetch + 60s polling fallback, seeds the live store) and `useOutbreak(id)` (single zone with contributing reports).
- `components/`:
  - `outbreak-zone-layer.tsx` — replaces v6's `OutbreakZoneOverlay`. Renders the severity-tinted `Circle` plus a `Marker` whose body uses `HotspotAnimation`; the marker has a small pill underneath showing disease + report count. Tap → opens detail sheet via the `onPress` callback.
  - `hotspot-animation.tsx` — the dramatic v7 outbreak pulse: 3 staggered concentric rings continuously radiating outward, severity-colored, with a glowing core dot. HIGH severity pulses faster (1.2s) than MEDIUM (1.5s) than LOW (1.8s).
  - `severity-indicator.tsx` — reusable severity badge (compact / expanded variants, optional progress ring). Used in the outbreak sheet hero and exposed for future use in lists / dashboard.
  - `outbreak-detail-sheet.tsx` — bottom sheet with hero (disease + severity + active/resolved tag + close), 4-stat glass grid (reports / high count / radius / last-seen), affected-crop chips with emoji, mini lite-mode `MapView` showing the zone circle, contributing-reports list (image thumbnails, navigates to `/reports/[id]`), prevention guidance (sourced from the first contributing report's `recommendations`).

**Mobile — store + realtime updates**
- `live-reports.store.ts` adds `removeOutbreak(id)` action. `clear()` already wiped both maps so no change needed there.
- `useRealtimeReports` extended to subscribe to `outbreak.resolved` and call `removeOutbreak` on the resolved zone's id. Other socket subscriptions unchanged.
- `OutbreakZone` type updated to v7 shape (`latitude / longitude / radius / affectedCropTypes / active / resolvedAt / createdAt / updatedAt`).

**Mobile — wiring**
- `app/(app)/map.tsx` — imports `OutbreakZoneLayer` + `OutbreakDetailSheet`, holds a separate sheet ref + selected-outbreak state, renders zones from the live store with an `active`-or-`showResolved` filter. Uses `useOutbreaks({ active: showResolved ? undefined : true })` to seed the store on mount.
- `MapFilterSheet` — adds a new "Outbreak status" section with two chips (Active only / Show resolved). The store's `hasActiveFilters()` now treats `showResolved=true` as an active filter (badges the filter button).
- `dashboard.api.ts` — fetches `outbreakApi.list({ active: true, limit: 200 })` and overrides `summary.activeOutbreaks` + `summary.highSeverityZones` with the real counts. Falls back to mock numbers on failure.

**Verification**
- Backend curl: 0 zones initially → submit 5 + 6 = 11 Tomato reports near (18.52, 73.86) → 1 zone created with `disease="Tomato Late Blight"`, `severity=HIGH`, `reportCount=6`, `highCount=6`, `affectedCropTypes=["Tomato"]`, `active=true`. `GET /outbreaks/:id` returns zone + 6 contributing reports. (Zone count below 11 because the deterministic mock AI distributes uploads across multiple Tomato diseases — this is the engine working correctly: only same-disease reports cluster.)
- Backend typecheck / lint clean.
- Mobile typecheck / lint clean (1 cosmetic axios warning carried over).
- iOS bundle 7MB.

### v8 — Notifications System + Plots ✅

**Backend — schema migration `notifications_system_v8`**
- New enums: `NotificationType` (OUTBREAK / REPORT / WARNING / SYSTEM), `DevicePlatform` (IOS / ANDROID / WEB).
- New `Plot` model: `userId` FK with cascade, `name`, `latitude / longitude`, `cropTypes String[]`, `areaAcres?`, `active`, `createdAt / updatedAt`. Indexes on `(userId, active)` and `(latitude, longitude)`. Soft-delete via `active=false` to preserve notification provenance.
- New `Notification` model: `userId` FK, `type`, `title`, `body`, `severity?`, optional `latitude / longitude`, `data Json?`, `read / readAt`, `createdAt`. Indexes on `(userId, read, createdAt)` + `(userId, createdAt)`.
- New `PushToken` model: `userId` FK, unique `token`, `platform`, `lastSeenAt`. Idempotent re-binding on register.
- New `NotificationPreferences` model: per-user, defaults all-enabled, optional `quietHoursStart / quietHoursEnd` (schema only, no UI in v8).

**Backend — env additions**
- `EXPO_ACCESS_TOKEN` (optional, raises Expo's anon push rate limit)
- `NOTIFICATION_NEARBY_BUFFER_KM` (default 5)
- `NOTIFICATION_DEDUP_WINDOW_HOURS` (default 24)
- `NOTIFICATION_REPORT_TRIGGER_RADIUS_KM` (default 5)
- `PLOT_MAX_PER_USER` (default 20)

**Backend — `modules/plots/`**
- `PlotsController` — owner-scoped `GET /plots`, `GET /plots/:id`, `POST /plots`, `PATCH /plots/:id`, `DELETE /plots/:id` (soft-delete).
- `PlotsService` — enforces `PLOT_MAX_PER_USER` (count of active plots) on create. Returns plots ordered by `(active desc, createdAt desc)`.
- DTOs validate name (1-60), lat/lng, optional cropTypes + areaAcres.

**Backend — `modules/notifications/`**
- `NotificationsService` — paginated `list`, `unreadCount`, `markRead`, `markAllRead`, `remove`, `createForUsers(userIds, template)` (batched createMany + per-user emit + push).
- `NotificationsFanoutService` — single integration point for processors. `handleOutbreakCreated`, `handleOutbreakEscalated`, `handleOutbreakResolved`, `handleHighSeverityReport`. Geographic match via `Plot` bbox + haversine; preferences filter via `NotificationPreferences` row (default = enabled); dedup against `Notification.data->>'outbreakId'` in last 24h; reporter excluded from their own report's fan-out.
- `PushService` — wraps `expo-server-sdk`, batches up to 100, prunes invalid tokens (`DeviceNotRegistered` / `InvalidCredentials`). Push failures are caught silently — never block the persisted Notification + WS event.
- `PushTokenService` — idempotent register-or-refresh (handles same token rebinding to a different user).
- `NotificationPreferencesService` — upsert pattern; reads default-enabled if no row exists.
- `NotificationsController` — `GET /notifications`, `GET /notifications/unread-count`, `PATCH /notifications/:id/read`, `PATCH /notifications/read-all`, `DELETE /notifications/:id`, `POST /users/me/push-token`, `DELETE /users/me/push-token`, `GET /users/me/preferences`, `PATCH /users/me/preferences`.
- `templates.ts` — `outbreakCreatedTemplate`, `outbreakEscalatedTemplate`, `outbreakResolvedTemplate`, `highSeverityReportTemplate`. Severity-aware copy.

**Backend — realtime extensions**
- `RealtimeGateway.handleConnection` — joins each authed socket into `user:${userId}` room; per-user notification events target only that room.
- `RealtimeService` — added `notificationCreated / notificationRead / notificationReadAll / notificationDeleted` (per-user) and `outbreakResolved` (global, throttled).
- `OutbreakProcessor` — calls `fanout.handleOutbreakCreated` after `createZone`, `fanout.handleOutbreakEscalated` after severity bump in `attachToZone`, `fanout.handleOutbreakResolved` after sweeper marks inactive.
- `ReportsProcessor` — after AI SUCCESS + outbreak detection, calls `fanout.handleHighSeverityReport(updated)` if severity is HIGH.

**Backend — auth**
- Second demo phone added: `8888888888` (same OTP `123456`). Used for fan-out smoke tests where two distinct users are required.

**Backend — users module**
- `UsersService.updateMe` (name / district / state).
- `UsersController` — `GET /users/me`, `PATCH /users/me`. Used by mobile onboarding.

**Mobile — `features/plots/`**
- `api/plots.api.ts` — typed CRUD against the new endpoints.
- `hooks/use-plots.ts` — `usePlots`, `useActivePlots`, `useCreatePlot`, `useUpdatePlot`, `useDeletePlot` (all invalidate the `['plots']` query on success).
- `components/`:
  - `plot-card.tsx` — list row, Layers icon container, displays name + coords + crop chips + active state.
  - `plot-form-sheet.tsx` — bottom sheet (85% snap) with name input, location row (current display + GPS button + "Pick on map" button), crop multi-select chips, gradient save / red delete (when editing). Reuses the existing `MapPickerSheet` for map selection.
- `onboarding-storage.ts` — AsyncStorage helper for the `onboarding.skipped.v1` flag.

**Mobile — onboarding**
- New `(onboarding)` route group with its own gate.
- `name.tsx` — Step 1/2: large header, single-input AuthCard for the user's name, "Continue" → patches `/users/me`, navigates to first-plot. "Skip for now" link.
- `first-plot.tsx` — Step 2/2: gradient hero, glass info card explaining plot-based alerts, "Add a plot" gradient CTA opens `PlotFormSheet`, "I'll do this later" link sets `onboarding.skipped` and goes to `/`.
- `(app)/_layout.tsx` — checks plots query + onboarding-skipped flag; first-time users with no name AND no plots are redirected to `/name`. Subsequent visits skip the redirect.
- Logout clears the skipped flag so a fresh login can re-onboard.

**Mobile — `features/notifications/`**
- `api/notifications.api.ts` — typed `list / unreadCount / markRead / markAllRead / remove / registerPushToken / revokePushToken`.
- `store/notifications.store.ts` — Zustand id-keyed map + `unreadCount`. Persisted to AsyncStorage as `notifications.cache.v1`. Cap at 200 most-recent items, trimmed by `createdAt`. Hydrate on boot for instant badge.
- `hooks/`:
  - `useNotifications` (TanStack `useInfiniteQuery`, 30 per page, seeds the store).
  - `useUnreadCount` (queries `/notifications/unread-count` every 60s + reads cached store value).
  - `useMarkNotificationRead`, `useMarkAllRead`, `useDeleteNotification`.
  - `useRealtimeNotifications` — subscribes to all 4 `notification.*` events; `onNotification` callback feeds the in-app banner stack.
  - `usePushRegistration` — requests permission, fetches `getExpoPushTokenAsync`, POSTs to backend, listens for token rotation. Foreground OS-banner suppression via `Notifications.setNotificationHandler` so the in-app banner is the only thing shown when the app is foregrounded.
- `providers/notifications-provider.tsx` — top-level provider that hydrates the store, mounts `useRealtimeNotifications`, and renders `InAppBannerStack` (max 3 visible, FadeInUp/FadeOutUp). Mounted inside the auth gate so the socket exists.
- `components/`:
  - `notification-card.tsx` — severity-tinted icon container (AlertTriangle/Camera/Info), unread brand dot, time-ago.
  - `notification-badge.tsx` — pulsing red pill with count (or `99+`) for the tab bar.
  - `in-app-banner.tsx` — glass card with severity-tinted icon, auto-dismisses after 4.5s, tap navigates by deep-link (outbreakId → /map, reportId → /reports/[id]). Stack helper hook `useBannerStack`.
  - `notification-filter.tsx` — filter chips: All / Unread / Outbreaks / Reports / Warnings / System.

**Mobile — wiring**
- `app/_layout.tsx` — wraps the auth gate with `<NotificationsProvider enabled={isAuthenticated}>`. `usePushRegistration()` runs once auth is ready.
- `app/(app)/notifications.tsx` — rebuilt from scratch. Header with "Mark all read" CTA when unread > 0, filter chips row, `FlashList` of `NotificationCard`s with infinite scroll + pull-to-refresh + long-press to delete. Empty state messaging suggests adding plots when the feed is empty.
- `tab-bar.tsx` — Bell tab now overlays a `NotificationBadge` driven by `useUnreadCount` when count > 0. Pulsing animation for emphasis.
- `app/(app)/profile.tsx` — added "Your plots" section with `PlotCard` list + "Add plot" button. Tap a plot to edit; pencil/trash actions via the form sheet.
- `app/(app)/map.tsx` — renders the user's active plots as small home-iconed markers (translucent brand-tinted disc), so users see their fields alongside disease reports.
- `auth.api.ts` — added `updateMe(payload)` for the onboarding name screen.

**Verification**
- Backend curl smoke: User A (9999...) and User B (8888...) authenticate. User B registers a plot near (18.52, 73.86). User A submits 5 Tomato reports nearby. After AI processing, User B receives 2 `REPORT` notifications (one per HIGH-severity diagnosis the mock AI returned), User A receives 0 (reporter excluded). `PATCH /notifications/:id/read` flips read state correctly.
- Backend typecheck / lint clean.
- Mobile typecheck / lint clean (1 cosmetic axios warning carried over).
- iOS bundle 7.2MB.

### v9 — Offline Support ✅

**Backend — schema migration `add_report_client_id`**
- Added optional `clientId String?` to `Report` with composite unique index `(userId, clientId)`. NULLs are treated as distinct by Postgres so legacy clients (no `clientId`) are unaffected.
- `ReportsService.create` now checks for existing `(userId, clientId)` before inserting; returns the existing row when found. Idempotent retry semantics — the offline drainer can safely re-POST the same draft after any failure mode.
- `CreateReportDto` accepts optional `clientId` (≤64 chars).

**Mobile — `features/offline-sync/`**
- `store/network.store.ts` — global Zustand store mirroring `NetInfo`. Exposes a 4-state machine: `online | offline | unstable | unknown`. `hydrate()` returns the unsubscribe so callers can wire it into a single `useEffect` cleanup.
- `store/sync-status.store.ts` — derived view: `phase` (idle / syncing / failed), `queueDepth`, `lastSyncedAt`, `lastError`. Drives every offline UI surface from a single source.
- `hooks/use-network-connectivity.ts` — single-call hydration helper mounted in `_layout.tsx`.
- `utils/persistent-storage.ts` — namespace-prefixed, versioned AsyncStorage wrapper with `load / save / remove / clearAll`. Drop-in MMKV/SQLite swap point. Includes a `CACHE_KEYS` registry for collision-free key management.
- `components/`:
  - `OfflineBanner` — slides in from the top via reanimated `FadeInDown / FadeOutUp` whenever `state ∈ {offline, unstable}` or sync is mid-flight with queued items. Glass-morph card with pulsing icon, severity-colored tint (warning when offline, brand when syncing). Lives above all routes inside the auth gate.
  - `SyncIndicator` — pill / inline badge with 4 tones (idle / syncing / offline / failed). Reads from both stores so it auto-updates as state changes.
  - `QueueStatusCard` — actionable card showing pending / uploading / failed counts, last error, last-synced timestamp, and a "Retry now" button when `failed` items exist. Surfaces on the upload screen below the form.

**Mobile — query persistence**
- `providers/query-provider.tsx` rebuilt on `PersistQueryClientProvider`:
  - Persister: `createAsyncStoragePersister` with key `crop-disease.cache.react-query.v1`, throttle 1s.
  - `gcTime: 7 days` so cached queries survive long enough to be useful offline.
  - `buster: 'v9.1'` cache-busts on schema bumps.
  - `maxAge: 24h` drops stale offline caches.
  - Mutations are NOT persisted — the upload queue handles the only mutation that needs durability.

**Mobile — idempotent uploads**
- `useCreateReport` generates a `uuid` once per draft and stamps it on:
  - `ReportDraft.clientId` (persisted via the queue),
  - `reportsApi.create({ clientId, ... })` on the immediate POST,
  - the queued `QueueItem` so the drainer can retry with the same key.
- `useOfflineQueue.processItem` includes `clientId` on retry — backend dedupes, so even if the previous attempt actually succeeded server-side and the response was lost, the retry returns the same row instead of creating a duplicate.

**Mobile — live-reports persistence**
- `useLiveReportsStore` adds `hydrate()` and a debounced `schedulePersist()` writing to `crop-disease.cache.live-reports.v1`. Map shows the last-known reports + outbreak zones immediately on cold boot before any network call resolves.

**Mobile — sync-status integration**
- `useOfflineQueue` writes phase transitions (`syncing` / `idle` / `failed`) and queue depth into `useSyncStatusStore` as it processes items. `markSynced()` fires after a successful drain; `setError()` after a failed one with the last error message.
- `useOfflineQueueStore` adds `retryAll()` action — clears cooldown + failed status + attempt counts so the next drainer pass picks every item up immediately. Wired to the "Retry now" button on `QueueStatusCard`.

**Mobile — wiring**
- `app/_layout.tsx` now:
  - Calls `useNetworkConnectivity()` once at the top.
  - Hydrates the live-reports store alongside auth + queue.
  - Renders `<OfflineBanner />` above all routes inside the authenticated tree.
- `app/(app)/upload.tsx` adds `<QueueStatusCard onRetryAll={retryAll} />` below the existing `PendingUploadsSection`.

**Mobile — `features/offline-ai/` placeholder**
- New module documenting the future on-device inference contract:
  - `OfflineAiClient` interface mirrors the server-side `AiClient`.
  - `OfflineAnalysisRequest / Success / Failure` DTOs with `errorCode: 'UNAVAILABLE' | 'MODEL_NOT_LOADED' | 'INFERENCE_FAILED'`.
  - `offlineAiClient` stub: `isAvailable()` returns `false`, `analyze()` returns `errorCode: UNAVAILABLE`. Lets the upload pipeline wire in today as a fallback path that turns on for free when v10+ ships a TFLite/ONNX model.

**Verification**
- Backend curl idempotency smoke test (4 scenarios):
  - Same `clientId` twice → returns same `Report.id` (✓ idempotency works).
  - Different `clientId` → new row created (✓ different keys are distinct).
  - No `clientId` (legacy) → multiple rows allowed (✓ backwards compat).
- Backend typecheck / lint clean.
- Mobile typecheck / lint clean (1 cosmetic axios warning carried over).
- iOS bundle 7.3MB.

### v10 — Polish, Performance & Demo ✅

**Backend**
- New `DEMO_MODE` env (default `true` in `.env.example`, off by default in `env.schema`'s prod-style validation). When on:
  - `MockAiClient` latency drops from 1500–2200 ms → 500–900 ms.
  - Healthy-crop chance drops from 12% → 3%; AI biases toward HIGH-severity catalog entries on the same crop. Demo outcomes feel dramatic without being random.
- New `GIT_SHA` and `BUILD_TIME` env vars (set by CI). Surfaced via the new `GET /version` public endpoint alongside `nodeEnv`, `demoMode`, and `startedAt`.
- `OutbreakService.list` gets a 30 s in-memory cache keyed on the query shape. Invalidated on every outbreak mutation in `OutbreakProcessor` (create / attach / resolve). Drops Neon load on the dashboard polling cycle without compromising freshness.
- New `apps/backend/src/scripts/seed-demo.ts` + `pnpm --filter backend seed:demo`:
  - Idempotent on `(userId, clientId)` for reports and `(userId, name)` for plots.
  - Creates 2 demo users (Ramesh + Sunita) with names + 3 plots clustered around Pune / Nashik / Sangli.
  - Inserts 26 reports producing 3 outbreak zones (HIGH Pune Tomato Late Blight, MEDIUM Nashik Rice Bacterial Leaf Blight, LOW Sangli Cotton Bollworm) plus 4 below-threshold Wheat singletons and 3 healthy reports.
  - Inserts 5 historical notifications for the demo user (mix of read + unread).
- New `common/utils/logger.ts` — drop-in Sentry/Datadog swap point.
- `apps/backend/Dockerfile` (multi-stage, non-root, runs `prisma migrate deploy` then `dist/main.js`).
- `apps/backend/Procfile` and `.dockerignore` for Railway / generic-PaaS deployment.

**Mobile — error handling + stability**
- `react-error-boundary` wired at the app root via `<AppErrorBoundary>`. Renders a branded gradient fallback with "Try again" CTA + dev-only stack message. All uncaught render errors flow through `logger.error` (single Sentry hook-up point later).
- Axios interceptor rewritten:
  - Single retry on 5xx with 200–400 ms jitter (only for idempotent POSTs and GETs).
  - Errors normalize into a `NormalizedApiError` shape attached as `error.normalized`. Codes: `NETWORK_OFFLINE / TIMEOUT / UNAUTHORIZED / CONFLICT / BAD_REQUEST / SERVER_ERROR / UNKNOWN`.
  - `normalizeApiError(err)` exported so any feature hook can branch cleanly without sniffing axios internals.
- Socket layer: `getSocket()` is now token-aware. If the persisted auth token has changed since the last connection (e.g. logout + re-login with a different account), the stale socket is torn down and a fresh one is created with the new token. `disconnectSocket()` removes all listeners before disconnecting. Connect / disconnect / connect_error events are logged via `logger`.
- New `utils/logger.ts` mirroring the backend abstraction. Replaces ad-hoc `console.warn` calls in the api client and socket service.

**Mobile — UX polish**
- `Stack` screenOptions per route group:
  - `(app)` → `slide_from_right` (iOS-standard).
  - `reports/[id]` → `slide_from_bottom` (modal feel for the result screen).
  - `(auth)` and `(onboarding)` → `fade` (entry feels snappier).
- `useCreateReport` fires `Haptics.notificationAsync(Success)` on AI success, `Warning` on offline-queue fallback. Errors elsewhere flow through the new `Toast` provider.
- `expo-image` polish on `ReportCard`: `cachePolicy="memory-disk"`, `recyclingKey={report.id}`, blurhash placeholder for instant first paint on slow networks. Transition bumped to 250 ms.
- `processing-state.tsx` migrated from RN `Animated.Image` to `expo-image` with disk caching — same image now cached after first view across the app.
- New `features/toast/` provider — glass card stack anchored at the bottom, max 3 visible, severity-tinted icons (Success / Warning / Error / Info), success/warning/error tones trigger matching haptics. ~170 lines, no new deps.

**Mobile — branding**
- `app.json` rewritten:
  - `name: "Crop Disease Mapping"` (was `"mobile"`).
  - `slug: "crop-disease-mapping"` (was `"mobile"`).
  - `bundleIdentifier: "com.cropdisease.mapping"` (iOS), `package: "com.cropdisease.mapping"` (Android).
  - `scheme: "cropdisease"` for deep links.
  - Splash background `#047857` (brand-700 — was Expo blue `#208AEF`).
  - Android adaptive icon background updated to brand green `#10b981`.
  - Splash image width 96px (slightly larger).
- New `apps/mobile/eas.json` with `development`, `preview`, `production` build profiles. Ready for `eas build` once the Expo project ID is configured.

**Mobile — code cleanup**
- `features/upload-report/components/upload-success.tsx` deleted (carried since v5 but unused after the result-screen route landed in v5/v6). Component index updated.
- 1 carried-over cosmetic axios lint warning addressed with a justified `eslint-disable` comment + explanatory note (`axios.create` and `axios.isAxiosError` are the documented entry points; the lint plugin's heuristic is wrong here).
- 1 carried-over warning about unused `Plot` import in fanout service cleaned up.

**Verification**
- Backend: `/health` green, `/version` returns `demoMode: true`, `/outbreaks?active=true` returns 5 zones (3 from seed + 2 organic from earlier smoke tests).
- Backend typecheck / lint fully clean.
- Mobile typecheck / lint fully clean (zero warnings, zero errors).
- iOS bundle 7.3 MB.
- Demo seed runs idempotently — second invocation reports `0 created, 26 updated`.

**Documentation**
- New `docs/DEMO_RUNBOOK.md` — 90-second core flow narrative, two-account setup, curl cheat sheet, fallback-if-network-fails plan, talking points by stage.
- `docs/GEO_MAPPING_FLOW.md` (v8 deliverable, used in PPT).
- `docs/METHODOLOGY_WORKFLOW.md` and `docs/METHODOLOGY_WORKFLOW_DIAGRAM.md` (v8 deliverables, used in PPT).

### v11 — On-device AI (offline TFLite) ✅

Replaced the v9 `offline-ai` placeholder with a real on-device crop-disease classifier. The model runs fully offline (zero network calls in the inference path) and slots into the existing `cloud → on-device → manual` engine chain as the fallback after cloud — no call-site changes were needed beyond passing candidates through.

**Model (from the `cpl_leaf_doctor_handoff` package)**
- MobileNetV3-Small student (distilled from a 93.6%-accurate EfficientNetB2 teacher), TFLite, dynamic-range int8 quantized, **1.22 MB**.
- **139 classes** spanning ~24 crops, labels formatted `crop::disease` (e.g. `tomato::Tomato___Late_blight`).
- Test-set accuracy (9,802 held-out images): **87.4% top-1 / 97.8% top-3**.
- Input contract: `(1, 224, 224, 3)` float32, pixels in **[0, 255]** (NOT [0,1] — MobileNetV3 normalizes internally), bilinear resize. Output: `(1, 139)` float32 softmax.

**Dependencies (`apps/mobile/package.json`)**
- `react-native-fast-tflite@3.0.1` — JSI/Nitro inference engine (CoreML on iOS, Android GPU/NNAPI delegates, CPU fallback).
- `react-native-nitro-modules@0.35.9` — required peer for fast-tflite v3 (matches its nitrogen 0.35.x codegen).
- `jpeg-js@^0.4.4` + `buffer@^6.0.3` — pure-JS JPEG decode for preprocessing.
- **Version correction:** the hand-off template targeted Expo SDK 52 / RN 0.76 with `react-native-fast-tflite@^1.6.0` + the `useTensorflowModel` hook. This app is SDK 56 / RN 0.85 / React 19 / New Arch, so we used fast-tflite **v3** (`loadTensorflowModel()` + `model.run([ArrayBuffer])`) and its nitro-modules peer instead. The old version/API would not have worked.

**Native config**
- `metro.config.js` — `config.resolver.assetExts.push('tflite')` so the model bundles as a static asset and `require(...)` resolves to an on-device file path.
- `app.config.ts` — registered the `react-native-fast-tflite` plugin (`enableCoreMLDelegate: true`, `enableAndroidGpuLibraries: true`) and added `assetBundlePatterns: ['assets/**/*']` so the `.tflite` ships inside the binary.

**Model assets → `apps/mobile/assets/models/`**
- `cpl_crop_disease.tflite` (1.22 MB, the float32 [0,255] default build — not the int8 variant).
- `cpl_id_to_label.json` (139-class id → label map).

**Feature code — `features/offline-ai/`** (replaces the v9 stub)
- `preprocess.ts` — resize → 224×224 → RGB `Float32Array` in [0,255]. Uses the SDK 52+ `ImageManipulator.manipulate()` context API (`.resize().renderAsync().saveAsync({ base64 })`), matching `upload-report/utils/compress-image.ts`. The hand-off's deprecated `manipulateAsync` would have broken on SDK 56.
- `labels.ts` — 139-class top-k decoder (`topKPredictions`), loose healthy/fresh-leaf detection (`isHealthyLabel`, handles the dataset's inconsistent `Healthy`/`healthy`/`Healthy Leaf`/`Fresh Leaf`/`Maize healthy`/`onion1` variants), and a `prettyDisease` humanizer (strips `Crop___` prefixes, underscores, trailing artefacts).
- `disease-info.ts` — **curated severity + recommendations lookup** (chosen over a confidence-heuristic or null-severity approach). Ordered keyword-rule matcher grouped by disease type (viruses, bacterial blights/spots/rots, late/early/leaf blight, rusts, mildews, molds/rots, smuts, anthracnose, leaf spots, wilts, insect pests, nutritional/abiotic). Normalizes underscores before matching so every one of the 139 labels resolves to a real `{ severity, recommendations }`; explicit healthy handling first, generic fallback last.
- `offline-ai.client.ts` — replaced the stub `offlineAiClient`. Lazy-loaded + cached singleton model (`loadModel()` tries hardware delegates first, transparently retries CPU-only on delegate failure). `isAvailable()` loads/caches and returns false gracefully if the native module/model is missing (e.g. plain Expo Go). `analyze()` preprocesses → `model.run()` → top-3 decode → maps the top prediction into the existing `OfflineAnalysisSuccess` shape (`disease`, `confidence`, `severity`, `recommendations`, `fromOnDevice: true`, plus `candidates` for the low-confidence picker).

**Wiring**
- `features/report-flow/use-report-flow.ts` — `tryOnDevice()` now passes `r.candidates` through to the `AnalysisResult`, so a low-confidence on-device result (<0.6) drives the same candidate-picker UI the cloud path already uses. Engine ordering unchanged: cloud-first (8s timeout) → on-device → manual.
- The existing `ENGINE_COPY['on-device']` + `EngineBadge` ("On-device AI") light up automatically — no UI changes required.

**Verification**
- Mobile typecheck (`tsc --noEmit`) clean.
- Mobile lint (`expo lint`) fully clean (the two transient `Array<T>` warnings were fixed to `T[]`).
- Confirmed fast-tflite v3 type surface (`loadTensorflowModel`, `TfliteModel`/`TensorflowModel` alias, `run(): Promise<ArrayBuffer[]>`, `TensorflowModelDelegate`) against the installed package.
- Confirmed the bundled-asset `require('../../../assets/models/cpl_crop_disease.tflite')` relative path resolves (alias `@/assets/...` avoided for the binary require because Metro's asset resolver doesn't reliably apply tsconfig path aliases).
- **Not yet runtime-verified on a device** — fast-tflite is a native module, so this needs a native dev build (EAS dev build or `expo prebuild` + `expo run:*`). It cannot run in Expo Go. On-device inference / offline (airplane-mode) behavior should be smoke-tested on a physical device.

---

## Tech debt and rough edges

### Resolved in v11
- v9 "`features/offline-ai/` placeholder stub" → replaced with a real bundled TFLite classifier (139 classes) wired into the report-flow engine chain as the cloud fallback.
- Roadmap "v12+ — On-device AI: wire `offlineAiClient` to a real TFLite/ONNX model" → shipped in v11 (model bundled in-binary, not fetch-on-first-launch).

### Resolved in v10
- Carried-over `axios` default-import lint warning (since v1) — silenced with an explanatory `eslint-disable` (the rule's heuristic is wrong; `axios.create` and `axios.isAxiosError` are the documented entry points).
- Unused `UploadSuccess` component carried since v5 — deleted along with its barrel export.
- Default Expo splash background (`#208AEF` blue) — replaced with brand-700 green.
- Default `mobile` app name and bundle identifier — replaced with branded `Crop Disease Mapping` / `com.cropdisease.mapping`.
- v9 noted "no error boundary" debt — addressed via `react-error-boundary` + branded fallback.
- v6+ noted "no `/version` endpoint" — landed in v10 alongside the `DEMO_MODE` flag.

### Resolved in v9
- v4 "Duplicate Cloudinary asset on backend-failure retry" → addressed via server-side `(userId, clientId)` idempotency. Cloudinary asset can still leak if the first POST never reaches the server, but duplicate Report rows are now impossible.
- v6 "Filters: in-memory only, no persistence" → not directly addressed for filter state, but TanStack Query cache is now persisted so filtered query results survive restarts.
- v7 "`useMe` stale on cold boot" → indirectly improved: persisted query cache means `/auth/me` results survive the cold-boot gap until the network settles.
- v8 "Multi-device notification dedup" → unchanged; notifications still fan out to every device. Acceptable.

### Resolved in v8
- v3+ "No push notifications" → `expo-notifications` wired with permission flow, token registration, foreground suppression handler. Real OS push works in dev/EAS builds; in-app banner via WS works everywhere.
- v3+ "First-login onboarding missing" → lite onboarding (name + first-plot screens) with skip-and-defer behavior persisted in AsyncStorage.
- v3+ "Profile editing not wired" → `PATCH /users/me` available, exposed via the onboarding name step.
- v6 "Live user-location tracking required" → reframed entirely. Plot-based fan-out: notifications target users by their registered plots, not their live location.
- v6 "Per-district rooms / scoping" debt → addressed via per-user rooms (`user:${userId}`) for notification events, which gives us targeted delivery without district modeling.
- v6 "`map.updated` socket event emitted but no client subscriber" → still unresolved (it's a hint event; we use direct `notification.created` instead).

### Resolved in v7
- v6 "outbreak detection is heuristic-only" → real engine with explicit thresholds, escalation rules, deactivation lifecycle.
- v6 "outbreak zone center stays at the first report's coordinates" → running-average centroid recomputed on every contribution.
- v6 "Dashboard outbreaks / trends / alerts still mocked" (partially) → `summary.activeOutbreaks` and `summary.highSeverityZones` now read real `/outbreaks` data; trends + alerts still mocked.
- v6 "no `outbreak.resolved` event" → emitted by the scheduler and consumed by the mobile live store.
- v6 "no scheduled cleanup of stale data" → `OutbreakScheduler` runs every 2 minutes.

### Resolved in v6
- v3+ "Map screen is a placeholder" → fully wired with markers, clusters, heatmap, outbreak zones, filters, detail sheet.
- v3+ "Socket.IO has no real events" → emits `report.created`, `outbreak.created`, `outbreak.updated`, `map.updated` (throttled).
- v3+ "Dashboard data still mocked" (partially) → `recentReports` now reads real `reportsApi.list({ scope: 'mine' })`; outbreaks / trends / alerts / summary still mocked.
- v5 "In-process job queue" → startup sweeper added; crashed PROCESSING rows recover on next boot.
- v5 "WS authentication" → JWT middleware verifies handshake tokens; unauthenticated sockets are rejected.

### Resolved in v5
- v3+ "AI integration not done" → fully wired with provider abstraction, fire-and-forget processing, retry endpoint.
- v4 in-place `UploadSuccess` overlay → replaced by dedicated result screen.
- `severityVisuals` mismatch between mock (`'low'`) and backend (`'LOW'`) → unified case-insensitive.

### Open

| Item | Severity | Notes |
| ---- | -------- | ----- |
| `axios` default-import lint warning | low | False positive from `eslint-plugin-import` against axios's typings. Ignore or silence with override later. |
| Neon DB credentials shared in earlier chat | medium | Rotate the Neon password before any public release. |
| Cloudinary credentials shared in chat | medium | Rotate the Cloudinary API key/secret before public release. |
| Profile editing not wired | medium | Greeting falls back to "Farmer" + "Set your location". |
| First-login onboarding missing | medium | After OTP verify, user lands directly on dashboard with empty profile. |
| Mock OTP only | high (vs prod) | Hardcoded in `auth.service.ts`. Architecture is ready for Twilio/MSG91 swap (single file change). |
| Mock AI only by default | high (vs prod) | `AI_PROVIDER=mock` in dev. `FastApiAiClient` is implemented but the upstream hasn't been validated against a real model yet. Set `AI_PROVIDER=fastapi` once the FastAPI service is up. |
| In-process job queue (no Redis / BullMQ) | medium | `ReportsProcessor.schedule` is still a Node promise — fine for single-instance. The startup sweeper now recovers crashed PROCESSING rows, so this is no longer "high"; just "needs Redis when we scale". |
| Dashboard outbreaks / trends / alerts still mocked | medium | `recentReports` is real now; the rest needs aggregation endpoints (likely `/dashboard/summary`, `/dashboard/trends`). Hits in v7+. |
| Cloudinary signature ratelimiting | medium | `POST /uploads/signature` is unmetered and protected only by JWT. Add `@nestjs/throttler` before public release. |
| `/reports/nearby` is unmetered too | medium | Map will spam this on every pan. Add throttler + per-IP rate limit before public release. Also applies to `/outbreaks` polling. |
| `/reports/nearby` returns ALL users' reports | medium | This is intentional for the map, but means we expose other farmers' raw notes globally. v8+ should consider redacting `notes` from non-owner consumers, or scoping to district. Same applies to `/outbreaks/:id`'s contributingReports. |
| No Cloudinary deletion path | medium | `CloudinaryService.destroy` exists but isn't called. `DELETE /reports/:id` doesn't exist yet. |
| Reports `imageUrl` not validated server-side | medium | Should verify it matches our Cloudinary cloud + folder. |
| No push notifications | medium | `expo-notifications` not wired. v7 deliverable. |
| Outbreak detection is heuristic-only | medium | v7 implemented a proper engine. Still simple by design (no ML, no time-decay weighting). Acceptable for the demo; refine with feature engineering / ML in v8+. |
| Outbreak zone never shrinks | low | Once expanded to ESCALATE_RADIUS_KM, the radius stays. As reports drop off, the zone resolves entirely (scheduler) but doesn't gradually contract. Acceptable. |
| Outbreak prevention guidance is opportunistic | low | The detail sheet shows the *first* contributing report's `recommendations` as "prevention guidance". Better long-term: a separate `prevention-catalog.ts` keyed by disease, with outbreak-level (broad containment) vs single-plant (treatment) variants. |
| `outbreak.resolved` doesn't animate out on the map | low | The marker just disappears. Could fade via reanimated FadeOut. Polish item. |
| Android Google Maps API key not configured | high (Android only) | `react-native-maps` won't render on Android until `expo.android.config.googleMaps.apiKey` is set in `app.json` and a custom dev client is built. iOS works out of the box. |
| In-memory live reports cap = 1000 | low | Hard cap, trimmed by `createdAt`. Well above what a single screen needs. Configurable via store. |
| `StatCard` counter | low | Uses `requestAnimationFrame` + `setState`. Acceptable for now. |
| `useMe` stale on cold boot | low | Trust the cached user; never re-validate. Add `useMe()` invocation in `_layout` after hydrate. |
| No git hooks | low | Skipped for hackathon velocity. |
| No Docker / CI / EAS config | low | Backend is 12-factor. EAS Build is needed before TestFlight + before `react-native-maps` works on Android. |
| No tests | medium | No unit, integration, or E2E tests. At minimum: `MockAiClient` determinism, `ReportsProcessor` happy + failure paths, dashboard hook smoke, Detox auth + upload + result flow. |
| Glass effect platform parity | low | iOS-26+ premium. Android falls back to a solid tint. Acceptable. |
| Health endpoint isn't monitored | low | Fine for demo. |
| Recommendations are plain strings | low | When multilingual support is needed, switch to `{ id, key, params? }` so a translation table can resolve them client-side. v5 wires the storage as `String[]`, easy to migrate. |
| `reprocess` endpoint allows infinite retries | low | No throttle / cooldown. Could be abused. Add a simple "minimum 30s between reprocess attempts" check. |

---

## Partial implementations to circle back to

- **Auth store rehydration race** — on cold boot we trust the persisted user; we never re-validate until a mutation hits the server. Should silently re-fetch `/auth/me` after hydrate.
- **Socket auth** — `getSocket()` reads token from SecureStore once; doesn't re-auth on token refresh.
- **`features/notifications/`** — has a mock list but no read-state persistence; "unread" is static seed data.
- **Dashboard partial-real** — `recentReports` is real, but outbreaks / trends / alerts / summary still come from mocks. Need backend aggregation endpoints.
- **Apps/backend `users` module** — has `UsersService` with `findById/findByPhone` only. No DTOs, controller, or update logic. Profile editing API is needed before the onboarding screen.
- **`useCreateReport` post-Cloudinary failure** — when Cloudinary succeeds but our server's `POST /reports` fails, the queue retries the full pipeline → orphan asset on Cloudinary. Track `imagePublicId` on the queue item so the drainer can skip the upload step on retry.
- **Android Google Maps key** — required for `react-native-maps` and the upload `MapPickerSheet`. v6's map tab is iOS-only until this is configured.
- **`UploadSuccess` component** — no longer used by the upload flow but left in `features/upload-report/components/` for reference. Remove or replace with a "Report submitted" toast in a future cleanup pass.
- **`FastApiAiClient` not exercised** — the contract is implemented (POSTs `{ image_url, crop_type, notes }` to `/predict`) but it has not been validated against a real model yet. Validate request/response shapes once the FastAPI service comes online.
- **No "your reports" list** — the user has no UI to see their past reports apart from immediately after upload. Trivial to add by listing `reportsApi.list({ scope: 'mine' })` somewhere (likely Profile or a new tab).
- **`processedAt` not used in the dashboard** — the dashboard's mock data uses `createdAt` for time-ago. When real data lands, prefer `processedAt` for the "Analyzed Xh ago" tag.
- **Reprocess preserves stale fields** — `reprocess` resets `processingStatus` to `PENDING` and clears `aiError`, but leaves the prior `disease/confidence/severity/recommendations` populated until the new analysis writes over them. UI shows the stale result during PENDING/PROCESSING. Acceptable — feels like "re-analyzing the previous result" — but worth confirming desired UX.
- **`map.updated` socket event** — emitted (throttled) but no client subscriber yet. Could drive a small "fresh data available" badge that refetches on tap.
- **Outbreak detection uses report `latitude/longitude` not movement-aware centers** — when many reports cluster around a single zone, the zone center stays at the first report's coordinates. v7 should recompute the centroid as new reports come in.
- **Multi-select filters are client-only** — the server's `/reports/nearby` accepts a single `severity / cropType / disease` value. When the user picks multiple, only the first is sent server-side and the rest are filtered client-side in the live store. Fine for hackathon scale; replace with `IN` arrays when needed.
- **Dashboard trends + alerts still mocked** — `summary.activeOutbreaks` and `summary.highSeverityZones` are real (v7), and `recentReports` is real (v6). Disease trends + alerts still come from `mockDashboard`. Need their own aggregation endpoints.
- **Resolved zones aren't surfaced on the dashboard** — only the map's "Show resolved" toggle exposes them. A "recently resolved" widget could go on the home screen as a peace-of-mind signal.
- **Outbreak zone radius doesn't contract** — only grows on escalation. As contributing reports age out the zone resolves entirely (scheduler) but doesn't gradually shrink. Acceptable.

---

## What's left (rough roadmap)

### v12 — Admin / Officer flows (next)
- Officer role report verification queue.
- Broadcast alert UI (drives `alert.created` events with notification fan-out).
- Role-based UI gating (`@CurrentUser().role` server-side, store-driven on client).
- Authority-issued advisories shown alongside outbreak alerts.

### On-device AI — follow-ups (core shipped in v11)
- Reconcile on-device diagnosis with the server-side diagnosis on next sync (currently the cloud result wins when online; on-device only fills in when cloud fails/times out).
- Consider prefer-on-device-when-offline ordering to skip the 8s cloud wait when `network.store` reports offline (deliberately kept cloud-first in v11).
- Optional: fetch-on-first-launch / OTA model updates instead of bundling in-binary, if the model grows or needs frequent retraining.
- Optional: swap the pure-JS JPEG decode for `react-native-vision-camera` + `vision-camera-resize-plugin` if realtime (>5 fps) camera classification is ever needed.

### Cross-cutting (any version)
- Profile editing UI for district / state / area.
- Real OTP provider (Twilio / MSG91) — single-file swap in `AuthService.sendOtp`.
- Real FastAPI integration (set `AI_PROVIDER=fastapi`, validate response shapes).
- Rate-limit `/uploads/signature`, `/reports/nearby`, `/reports/:id/reprocess`, `/outbreaks`, `/notifications`.
- `DELETE /reports/:id` + Cloudinary asset cleanup.
- Validate `imageUrl` host server-side (must match our Cloudinary cloud + folder).
- Privacy pass on `/reports/nearby` and `/outbreaks/:id` (redact `notes` from non-owners, or scope to district).
- "Your reports" list screen.
- Notification preferences UI (schema exists from v8).
- Quiet hours enforcement on push (schema exists from v8).
- Outbreak prevention catalog (separate from per-report disease recommendations).
- Replace dashboard's mocked trends + alerts with backend aggregation endpoints.
- E2E test setup (Detox).
- EAS Build + Submit configuration; Google Maps Android key; EAS project ID for Expo push tokens in production.
- CI workflow (typecheck + lint + test on PR).
- Docker config when deployment target is decided.
- Sentry / error tracking.
- Analytics (PostHog / Amplitude) for key flows.

---

## How to run

```bash
pnpm install

# fill apps/backend/.env with DATABASE_URL (Neon), CLOUDINARY_*, AI_PROVIDER
pnpm --filter backend prisma:migrate

# in two terminals (or via turbo)
pnpm --filter backend dev
pnpm --filter mobile dev
# or both: pnpm dev
```

Environment switches:
- `AI_PROVIDER=mock` (default) — instant deterministic AI; perfect for demo.
- `AI_PROVIDER=fastapi` — calls `${FASTAPI_URL}/predict`. 35s client timeout (the upstream may take ~25s).

> **Note for Android dev**: `react-native-maps` requires a Google Maps API key set under `expo.android.config.googleMaps.apiKey` in `app.json` and a custom dev client. On iOS it works out of the box with Apple Maps.

> **Note on on-device AI (v11)**: `react-native-fast-tflite` is a native module, so the offline classifier does **not** run in Expo Go. Build a dev client once, then iterate normally:
> ```bash
> # cloud build (no local native toolchain needed):
> pnpm --filter mobile exec eas build --profile development --platform android
> # or local prebuild + run:
> pnpm --filter mobile exec expo prebuild
> pnpm --filter mobile exec expo run:android   # or run:ios
> ```
> Install on a physical device (TFLite is fiddly on the iOS simulator), then `pnpm --filter mobile dev` and scan with the dev client. To verify offline: airplane mode → Report tab → capture a leaf → cloud times out (8s) → "On-device AI" result.

Demo credentials: phone `9999999999`, OTP `123456`.

---

## Decisions log

A running list of every architectural / product / tooling decision we've made across all versions. Each entry briefly states the **decision**, the alternatives considered, and the rationale. Add to this list (don't rewrite per version) at the end of every version.

### Architecture & infrastructure

- **Monorepo via pnpm workspaces + Turborepo** — picked over npm workspaces (no caching) and two-separate-projects (no shared types path). Gives task-level caching, future packages/types workspace, and is hackathon-friendly.
- **TypeScript strict everywhere** with `noUncheckedIndexedAccess`, `noImplicitOverride`, shared `tsconfig.base.json`. Catches bugs at compile time and ages well.
- **Neon (managed Postgres) is the only database environment** — no Docker, no local Postgres. Backend remains 12-factor / portable so a containerized deploy is a one-shot when the time comes.
- **No Docker config in this phase** — explicitly deferred. App stays portable for later containerization.
- **No git hooks (husky / lint-staged / commitlint)** — skipped for hackathon velocity. Add when collaboration grows.
- **No CI / EAS Build / tests in this phase** — explicit scope cut. Will land before TestFlight / public release.

### Backend

- **NestJS 10** as the backend framework. Module system, DI, decorators map cleanly to the project's needs.
- **Prisma + Postgres** over alternatives — typed query builder, migrations are git-tracked SQL.
- **Zod for env validation** — backend refuses to boot on bad/missing env. Catches deployment misconfigs immediately.
- **`nestjs-pino` for logging** — structured JSON in prod, pretty-printed in dev. Picked over the built-in NestJS Logger.
- **Global response envelope** `{ success, data, timestamp }` via `TransformInterceptor` — uniform shape for all clients.
- **Global `AllExceptionsFilter`** with consistent error envelope (`statusCode`, `message`, `error`, `path`, `timestamp`).
- **Helmet + compression + env-driven CORS** at bootstrap.
- **Class-validator DTOs** with bounded lengths, regex'd phone/OTP, lat/lng validators.

### Auth

- **`passport-jwt` + `@nestjs/passport`** for JWT auth — canonical NestJS pattern over a hand-rolled `@nestjs/jwt`-only guard.
- **Global `JwtAuthGuard` registered as `APP_GUARD`** — every route is protected by default; opt-out via `@Public()`. Safer default than per-route opt-in.
- **Stateful mock OTP** (DB-backed `OtpToken` with TTL + attempts cap) over a stateless hardcoded check — closer to a real implementation, easier to swap for Twilio/MSG91 later.
- **Demo credentials hardcoded for hackathon**: phone `9999999999`, OTP `123456`. Only this phone is accepted by `send-otp`.
- **`User.name / district / state` are nullable** so a first-login user can exist without onboarding.
- **`UserRole` Prisma enum** (FARMER / ADMIN) — not strings.
- **Composite index `(state, district)`** on User for future regional queries.
- **JWT in SecureStore, user payload in AsyncStorage** — token is sensitive, user is cheap-to-read on boot.
- **Auth store hydrates on boot before splash hides** — eliminates auth flicker.
- **Single global `setUnauthorizedHandler` in axios** — any 401 anywhere triggers `logout()` and redirect.

### Mobile architecture

- **Expo SDK 56 + Expo Router** — file-based routing with typed routes; `(auth)` and `(app)` route groups gated by `<Redirect />`.
- **Path alias `@/*` → `./src/*`** in both `tsconfig.json` and `babel.config.js`.
- **Folder structure:** feature-based modules under `src/features/<name>/{api,hooks,components,store,utils,types.ts}`. Each feature is a self-contained vertical slice.
- **State split:** Zustand for client state (auth, offline queue), TanStack Query for server state (reports, dashboard). No global Redux-style store.
- **Theme tokens centralized** in `src/theme/*` and mirrored into Tailwind via CSS variables in `global.css` — single source of truth for design tokens.
- **`@/tw` re-exports of `react-native-css` className-enabled components** — single import surface; native RN components are NOT used directly when className is needed.

### Styling

- **NativeWind v5 + Tailwind v4** via `react-native-css` (CSS-first config in `global.css`, no `tailwind.config.js`). Picked over NativeWind v4 + Tailwind v3 for future-proofing.
- **Heavy glassmorphism** via `expo-glass-effect` everywhere it makes sense (auth cards, dashboard cards, tab bar, upload screen, result screen). Explicit project decision: prioritize visual quality, accept iOS-26+ as the target — Android falls back to a solid tint.
- **Brand palette + status colors** as semantic tokens (`brand-{50..900}`, `success / warning / danger / info`). Severity colors used consistently: green = low, amber = medium, red = high.
- **Dark mode is automatic** via `@media (prefers-color-scheme: dark)` and glass `colorScheme="auto"` — not a user-toggle for v1–v5.

### UI / animation

- **Pure reanimated** for all animations (FadeIn, scan line, ring sweep, pulse, etc.). Picked over `moti` to avoid an extra dep — everything we need is trivial in raw reanimated.
- **Custom shimmer Skeleton** (~50 lines, reanimated + LinearGradient) instead of `react-native-skeleton-placeholder`.
- **Custom animated TabBar** with `tabBar` prop on Expo Router's `Tabs` — picked over `NativeTabs` (less Android polish, less customizable).
- **Center FAB-style Upload tab** — gradient circle elevated above the bar; explicit choice over a flat tab or modal.
- **lucide-react-native for icons** — names align with the spec (House / Map / Plus / Bell / User), tree-shakeable, cross-platform.
- **`@shopify/flash-list` for horizontal scrolls only** (recent reports, notifications). Short fixed-length lists use plain `View` mapping — FlashList overhead isn't worth it.
- **Native splash held until in-app hydration completes**, plus a brief gradient brand-mark splash while auth + queue stores hydrate. No flicker.
- **Inline error messages, no toast library** — keeps deps lean for v2–v5.
- **Action buttons = secondary tile group** on result screen (View on map / Share / New report). RN's built-in `Share` API; no extra dep.

### Upload pipeline

- **Cloudinary direct client upload with server-signed signature** — `POST /uploads/signature` returns a short-lived signature; client uploads straight to Cloudinary. Picked over backend proxy (doubles bandwidth) and unsigned preset (insecure).
- **Real Cloudinary credentials in `.env`** for the demo, with `imagePublicId` stored on each report so future deletes can clean up assets.
- **`expo-image-picker`** for both camera + gallery — single API, simpler than `expo-camera` + `expo-media-library`.
- **`react-native-maps` (1.27.2)** for the location picker — proven, draggable markers; needs Google Maps API key on Android.
- **Image compression: longest edge ≤ 1600px, JPEG q=0.7** via `expo-image-manipulator`. Typical 4MB → ~400KB.
- **Compressed image copied to `documentDirectory/uploads/<id>.<ext>`** before enqueueing — survives cache eviction.
- **Persistent offline queue under key `upload.queue.v1`** in AsyncStorage. Items stuck in `uploading` are reset to `pending` on hydrate so a crash mid-upload is recoverable.
- **Exponential backoff (1m → 5m → 15m → 1h → 6h, max 5 attempts)** for queue retries — gentler on battery + Cloudinary free tier limits.
- **NetInfo-driven drainer** — drains on initial mount and on every connectivity change.
- **Single tall scrollable upload form** with sectioned glass cards. Picked over a multi-step Photo→Crop→Location→Review wizard for speed.
- **Real upload progress percentage** via axios `onUploadProgress` (0–100%) — picked over an indeterminate spinner.
- **+91 only, country selector visually disabled** — defer real country selector to a later version.
- **25-crop centralized catalog** in `constants/crops.ts` with `{ id, name, emoji, category }`. Single source of truth.
- **Validation rules**: image required (JPEG/PNG/HEIC), crop required from catalog, location required (GPS or map-picked), notes optional ≤500 chars.
- **`Reports` Prisma model** with FK cascade to User, indexes on `(userId, createdAt)` and `(latitude, longitude)`.
- **`GET /reports` defaults to `scope=mine`** — district / "all" feed is a v6 deliverable.

### AI / disease detection

- **Fire-and-forget async processing** for the AI call (vs sync inside `POST /reports`) — FastAPI may take ~25s; we cannot block the HTTP response. `POST /reports` returns immediately with `processingStatus=PENDING`; mobile polls.
- **Mobile polling cadence: 3 seconds** while non-terminal status. Auto-stops on SUCCESS or FAILED.
- **Provider abstraction via `AiClient` interface** with two implementations: `MockAiClient` and `FastApiAiClient`. Picked by `AI_PROVIDER` env (mock | fastapi). Real swap is a single env change.
- **`AiService` retries once on retryable failure** (TIMEOUT, UPSTREAM_ERROR). After retry, returns a structured failure for the caller to persist.
- **Failures persist as `processingStatus=FAILED` with `aiError`** — the user always lands on a valid result screen with a retry CTA.
- **Mock AI is deterministic** by `hash(imageUrl + cropType)` — same upload always yields the same diagnosis; demos are reproducible. ~12% chance of "Healthy crop" for variety.
- **Disease catalog covers 9 crops** (Tomato, Potato, Rice, Wheat, Maize, Cotton, Grape, Chili, Onion) with full disease + 3–5 recommendation entries. Other crops fall through to `GENERIC_FALLBACK`.
- **`Severity` as a Prisma enum** (LOW / MEDIUM / HIGH) — type-safe over strings.
- **`recommendations` stored as Postgres `String[]`** — queryable, Prisma-typed. Migrating to a richer object shape (`{ key, params }`) is straightforward when multilingual support lands.
- **`processingStatus` field added** to disambiguate "still processing" from "processed but no result".
- **`POST /reports/:id/reprocess`** is owner-only and refuses while already PROCESSING. No throttle yet (debt).
- **Result screen at dedicated route `/reports/[id]`** — full-screen, shareable URL, history navigation. Picked over the v4 in-place success overlay (now removed from the flow).
- **Pure reanimated scan animation** as the AI loading state — picked over Lottie. Scan line + corner brackets + cycling status text + glass "Analyzing" pill.
- **Animated SVG confidence ring** (270° gauge, gradient stroke, severity-tinted) using `react-native-svg` + reanimated `useAnimatedProps`.
- **No backfill for v4 reports** — pre-v5 rows simply have null disease fields and `processingStatus=PENDING` until visited / reprocessed.
- **On-device model: `react-native-fast-tflite` over TensorFlow.js / ONNX Runtime** (v11) — JSI/Nitro gives direct memory access + native CoreML/Android-GPU delegates; tfjs is too slow for this model size and ONNX RN tooling is heavier. Matches the hand-off package's recommendation.
- **Pinned fast-tflite v3 + nitro-modules, NOT the hand-off's v1.6** (v11) — the hand-off template was built for Expo SDK 52 / RN 0.76 with the `useTensorflowModel` hook. This app is SDK 56 / RN 0.85 / React 19 / New Arch, which requires fast-tflite v3 (`loadTensorflowModel()` + `model.run()`) and its `react-native-nitro-modules` peer. Pinned exact versions (`3.0.1` / `0.35.9`) because native codegen is version-sensitive.
- **Model bundled in-binary (assetBundlePatterns) over fetch-on-first-launch** (v11) — at 1.22 MB it's well under store limits, so bundling guarantees true offline-on-first-run with zero download step. Revisit if the model grows.
- **Curated keyword-rule severity/recommendations lookup over confidence-heuristic or null-severity** (v11) — the TFLite model only outputs `disease + confidence`, but the `OfflineAnalysisSuccess` contract needs `severity` + `recommendations`. An ordered keyword matcher grouped by disease type covers all 139 classes with real agronomic guidance while staying maintainable (vs 139 hand-copied blocks).
- **Reused the v9 `OfflineAiClient` contract verbatim** (v11) — implementing the existing interface means zero changes to the `cloud → on-device → manual` engine chain in `use-report-flow.ts` (only addition: passing `candidates` through). The "On-device AI" badge/copy from v9 light up for free.
- **Engine ordering kept cloud-first, on-device fallback** (v11) — on-device kicks in only when cloud fails/times out (8s). Prefer-on-device-when-offline was considered but deferred to keep the change low-risk; the higher-accuracy cloud model wins whenever reachable.
- **Bundled `.tflite` required via relative path, not the `@/assets` alias** (v11) — Metro's asset resolver doesn't reliably apply tsconfig path aliases to binary `require()`s; the relative path is the proven pattern.
- **Input pixels kept at [0, 255] float32** (v11) — MobileNetV3 has an internal normalization layer; passing [0,1] produces confidently-wrong predictions. `preprocess.ts` preserves the hand-off's documented input contract.

### Out of scope / deferred

- **Real OTP provider (Twilio / MSG91)** — defer to post-hackathon. Architecture is ready for a single-file swap in `AuthService.sendOtp`.
- **Profile editing UI** beyond name (district / state / area) — deferred. Schema accepts these fields; expose later.
- **Notification preferences UI** — schema only in v8; UI deferred.
- **Quiet hours enforcement on push** — schema only in v8; logic deferred.
- **Multi-device notification dedup** — same user logged in on phone + tablet receives the WS event on both (intentional for sync) but Expo also sends push to both. Acceptable for v8; consider device-aware muting later.
- **Admin / officer flows** — v9 deliverable.
- **DELETE /reports/:id + Cloudinary asset cleanup** — deferred.
- **Rate-limiting `/uploads/signature`, `/reports/nearby`, `/reports/:id/reprocess`, `/outbreaks`, `/notifications`** — deferred.
- **Server-side validation that `imageUrl` host matches our Cloudinary cloud** — deferred.
- **BullMQ / Redis-backed job queue** — deferred. Single-instance Node promise queue + startup sweeper + outbreak scheduler is acceptable for the hackathon.

### Outbreak engine (v7)

- **Schema rename over additive change** — `centerLat → latitude`, `centerLng → longitude`, `radiusMeters (Int) → radius (Float)`. Cleaner long-term naming; the cost was one row in DB to migrate. `@map` aliasing was rejected as hidden tax.
- **Added `active`, `resolvedAt`, `affectedCropTypes` to OutbreakZone** instead of deriving them on demand. Storage is cheap; the detail sheet uses all three on initial render and we'd otherwise need a join + aggregate every time.
- **Detection thresholds promoted to env vars** (`OUTBREAK_CREATE_THRESHOLD` etc.). Tunable per environment without redeploys; defaults match the v7 spec verbatim (5/3km, 10/5km, 48h).
- **Stricter v7 thresholds** (5+ within 3km / 24h to create) over v6's looser rule (3+ within 5km). Fewer false positives, later alerts — the right tradeoff for a system that will be acted on.
- **Severity formula folds in `highCount`** — a zone with mostly HIGH-severity contributing reports escalates to HIGH faster than one with mostly LOW. Two thresholds (`HIGH_REPORT_COUNT` and `HIGH_SEVERITY_COUNT`) — either trips it.
- **`@nestjs/schedule` cron sweep over lazy "check on every report"** — zones in quiet areas never see another report, so lazy-check would leave them lingering. Cron runs every 2 minutes; query is indexed on `(active, lastSeenAt)`.
- **`@Cron('*/2 * * * *')` literal expression** — `CronExpression.EVERY_2_MINUTES` doesn't exist in @nestjs/schedule's enum; the literal is equivalent and clearer anyway.
- **Running-average centroid** — when attaching a report to a zone, the centroid is recomputed as `((prior * priorCount) + newPoint) / (priorCount + 1)`. Drifts toward the densest area over time; cheap, deterministic. Picked over bbox-midpoint (less responsive) and "leave original center" (clearly wrong as the zone evolves).
- **Closest-zone wins on overlap** — if a report lands inside multiple active zones (rare with 3km radii), it attaches to the zone with the smallest center-to-report distance. Not merging — explicit decision; merge logic adds significant complexity for a corner case.
- **`OutbreakProcessor.handleNewReport` is the single integration point** — `ReportsProcessor` calls it after AI SUCCESS, decoupling AI from clustering. Future v8 outbreak escalation push notifications can hook in here.
- **Removed v6's inline `detectOutbreak` from ReportsProcessor** — clean separation. Reports own AI + persistence, outbreaks own clustering + lifecycle.
- **Real `geo.utils.ts` lives in `common/utils/`** — moved out of `reports/` since both reports and outbreak modules use it. Adds `rollingCentroid` helper.
- **`OutbreakScheduler` uses `OnModuleInit`-free design** — only the `@Cron` decorator. Scheduling starts when ScheduleModule kicks in; no manual lifecycle.
- **`outbreak.resolved` event over a "resolved" flag in `outbreak.updated`** — semantic clarity; mobile uses `removeOutbreak` rather than checking `active=false` on every update payload.
- **GET /outbreaks/:id returns `{ zone, contributingReports }` in one round trip** — saves a follow-up request when opening the detail sheet. Limit of 20 contributing reports keeps the payload small.
- **Mobile reused v5 `RecommendationsList` for prevention guidance** — sources from the first contributing report's `recommendations`. Acceptable for v7; a separate "prevention catalog" for outbreak-level (containment vs treatment) is a v8+ refinement.
- **`OutbreakZoneLayer` (v7) replaces `OutbreakZoneOverlay` (v6)** — same role, richer rendering: `HotspotAnimation` core + disease/count pill underneath. v6 component deleted, not deprecated.
- **`HotspotAnimation` uses 3 staggered concentric rings** with severity-modulated cadence (HIGH=1.2s, MEDIUM=1.5s, LOW=1.8s). Picked over a single ring (less dramatic) and over Lottie (extra dep).
- **`SeverityIndicator` is a standalone reusable badge** — exported from `outbreak-system`, not duplicated. Compact / expanded variants + optional progress ring.
- **Mini lite-mode `MapView` in the detail sheet** instead of an image snapshot — accurate to the actual zone, no preprocessing pipeline. `pointerEvents="none"` keeps it from interfering with sheet gestures.
- **"Show resolved" filter as a chip pair, not a checkbox** — matches the existing chip aesthetic; selecting "Show resolved" toggles `hasActiveFilters()` so the filter button shows the active dot.
- **Dashboard summary swap is partial** — `activeOutbreaks` and `highSeverityZones` come from real `/outbreaks` data; `reportsThisWeek`, trends, and alerts still mocked. Hits the "looks alive" goal without needing aggregation endpoints yet.
- **No `geolib` dependency** — kept the hand-rolled haversine helpers from v6, added `rollingCentroid`. Zero new deps for ~50 lines of utility code.
- **No new mobile store** — extended `live-reports.store` with `removeOutbreak` rather than splitting into a separate `outbreak.store`. Single source of truth for everything map-related.
- **Heuristic over ML** — outbreak detection is rule-based by design for the hackathon. Architecture cleanly supports a v8+ swap (the `OutbreakProcessor.handleNewReport` interface stays; only the body changes).

### Notifications + Plots (v8)

- **Plot-based fan-out, not user-location tracking** — major architectural shift away from the original "store user lat/lng + periodic POST" plan. Farmers register their plots once during onboarding (or anytime from Profile); notifications target users whose **active plots** intersect the trigger area. Aligns with how real agri apps work (KisanSuvidha, Plantix), eliminates a privacy-questionable continuous-tracking subsystem, supports multi-plot users naturally, and gives us an anchor for future district analytics.
- **Soft-delete plots** (`active=false`) over hard delete — preserves notification provenance ("you were notified because of plot X" remains valid even if plot X is later removed). Hard delete becomes an admin-only operation later.
- **`PLOT_MAX_PER_USER=20` cap** enforced server-side in `PlotsService.create`. UX guardrail; raise via env if needed.
- **`Plot.cropTypes String[]` is metadata only in v8** — not used for notification filtering. Reserved for richer recommendations / per-crop analytics later.
- **Notification fan-out as a dedicated service** (`NotificationsFanoutService`) called by both processors, not inline. Encapsulates the geographic match + dedup + preferences filter so processors stay focused on their domain.
- **Pre-create one Notification row per recipient** at fan-out time (vs lazy "compute on read"). Simple read-side queries, accurate unread tracking, easier offline cache. Slight write amplification accepted for clarity.
- **Per-user socket rooms** — `RealtimeGateway.handleConnection` joins `user:${sub}`. `notification.created` and friends use `server.to(...).emit(...)`. Tiny change with big future leverage (alerts, direct messages, role-targeted broadcasts).
- **Foreground delivery via WS, background via Expo push** — `Notifications.setNotificationHandler` returns `shouldShowAlert: false` so OS notifications never duplicate the in-app banner when the app is foregrounded.
- **Anonymous Expo push tier** — no `EXPO_ACCESS_TOKEN` required for the demo. Set the env var when production rate limits matter.
- **Push failures are silent** — `PushService` catches everything; the persisted Notification + WS event always succeed. Push is best-effort.
- **HIGH-only `report.created` notifications** — gating against demo noise. Spec said "new nearby disease report" without a severity threshold; we picked HIGH to keep the demo clean. Tunable via `NOTIFICATION_REPORT_TRIGGER_RADIUS_KM` + the severity check in fanout.
- **Reporter excluded from their own report's fan-out** — the upload result screen already tells them the report is in; an extra notification would feel redundant.
- **24h dedup window** keyed by `Notification.data->>'outbreakId'` — prevents spamming the same user about the same outbreak even if it churns. `severity escalated` and `resolved` events bypass dedup since they're materially different states.
- **Mark-read on tap** is the standard UX. Long-press deletes (no swipe gesture component to keep the dependency footprint flat). Filter chips at the top of the list (All / Unread / Outbreaks / Reports / Warnings / System).
- **Mobile cache cap = 200 most recent notifications** in AsyncStorage. Older items via server pagination only.
- **`useUnreadCount` polls every 60s** as a safety net for socket drops; the cached store value drives the badge for instant updates.
- **In-app banner stack — max 3 visible** with FadeInUp/FadeOutUp. Honest stacking instead of "3 new alerts" collapse — users see what actually happened. Banners auto-dismiss after 4.5s, swipe/tap dismisses early. Each banner deep-links: `outbreakId` → `/map`, `reportId` → `/reports/[id]`.
- **Lite onboarding (2 screens, skippable)** over mandatory full onboarding — keeps the auth → app journey tight while still nudging users to add a plot. Skip choice persists in AsyncStorage as `onboarding.skipped.v1` so we don't re-prompt on every cold boot. Plot management is also permanently exposed in Profile.
- **Onboarding skipped flag is cleared on logout** so re-login flows back through onboarding for new accounts on the same device.
- **Profile gets a "Your plots" section** with `PlotCard` list + "Add plot" CTA. Tap a plot card → opens the same `PlotFormSheet` in edit mode (with delete action). The form sheet reuses v4's `MapPickerSheet` for "Pick on map".
- **User's own plots render on the Map tab** as small home-iconed translucent brand-tinted markers — gives a visceral "this outbreak is X km from my Tomato field" effect without any extra UI.
- **Demo phone added: 8888888888** — required for fan-out smoke testing (you need two distinct authenticated users). Same OTP `123456`. One-line change in `AuthService.DEMO_PHONES`.
- **`UsersController` finally exists** — `GET /users/me`, `PATCH /users/me`. Used by onboarding's name screen. Foundation for the deferred profile-editing UI.
- **NotificationPreferences schema only, no UI** — categories (`outbreakAlerts`, `reportAlerts`, `severityEscalations`, `resolvedAlerts`) + `quietHoursStart/End`. Server reads + filters; mobile UI to toggle them is a v9+ task.
- **No notification grouping** — each event is its own row. A flurry of escalations on one outbreak shows multiple notifications. Acceptable; introduce server-side grouping (`group_id`) when scale demands it.
- **No `alert.created` event yet** — that's the v9 admin/officer broadcast event. Architecture is ready (just another `template` + `fanout.handle*`).

### Realtime / map (v6)

- **Socket.IO middleware (`io.use`) for JWT** instead of a `@nestjs/passport` WS guard — simpler, no extra adapter, reuses the same `JwtService` config as HTTP auth. The middleware runs once at handshake; rejected handshakes trigger the client's normal reconnect loop.
- **Mobile reuses the existing `getSocket()` singleton** in `services/socket/`, which already reads the token from SecureStore and sets `auth.token` in the handshake — no client changes needed for v6.
- **Global broadcasts (no rooms)** — `report.created`, `outbreak.created`, `outbreak.updated` go to every connected client. Each client filters in-memory via the live store. Per-district rooms are a v8+ optimization when scale demands it.
- **Throttled `map.updated` tick (max once / 5s)** — emitted alongside any of the above events. Clients can use it as a "hint to refetch" trigger without subscribing to per-report events. Currently emitted but not consumed (debt).
- **Outbreak detection heuristic** — ≥3 SUCCESS reports of the same disease within 5km in the last 24h create an `OutbreakZone`. Subsequent reports of the same disease within 5km of an existing zone bump its counts. Deliberately simple — refined in v7+. Severity is the peak across contributing reports.
- **Startup sweeper** — `OnModuleInit` resets PROCESSING rows older than 5 minutes back to PENDING. Doesn't re-trigger AI; the next visit / reprocess does. Makes process crashes recoverable without external infra.
- **`react-native-maps` (1.27.2)** over `expo-maps` (newer, less battle-tested) and `Mapbox` (cost / token complexity). Apple Maps on iOS by default; `PROVIDER_GOOGLE` on Android.
- **Custom dark Google Maps style on Android only** — Apple Maps doesn't accept JSON styles but handles dark mode automatically via the OS color scheme.
- **`supercluster` (Mapbox engine) directly** instead of `react-native-map-clustering` (abandoned ~2 years, breaks on RN 0.76+). ~80 lines of glue, full control over cluster appearance.
- **Native `<Heatmap>`** from `react-native-maps` — severity-weighted points (HIGH=1.0, MEDIUM=0.6, LOW=0.3). Picked over custom Circle-based density buckets for simplicity.
- **Layer toggle: markers / heatmap / both** — explicit user control rather than always-both, both for perf on low-end Android and for visual hierarchy on iOS.
- **Live data store as Zustand id-keyed map**, not TanStack Query cache. Socket events are frequent and granular; a dedicated store gives O(1) upsert without churning query keys.
- **In-memory cap of 1000 reports** — trimmed by `createdAt` desc when exceeded. Bounded memory regardless of session length.
- **30s polling fallback on `/reports/nearby`** in addition to socket subscriptions — cheap insurance for socket drops that don't trigger explicit reconnect events.
- **Filters: in-memory only** for v6. No AsyncStorage persistence — defer to v7+ if users ask.
- **Multi-select filters apply server-side only when single-valued**; otherwise the request sends the rest as undefined and the client filters the live store. Pragmatic compromise; clean up when the server accepts `IN` arrays.
- **Date filter: 4 quick chips** (24h / 7d / 30d / All) instead of a date picker. Faster on mobile, covers 90% of use.
- **Marker detail sheet reuses v5 `disease-analysis` components** (`ConfidenceRing`, `SeverityBadge`, `RecommendationsList`) verbatim — consistent UX, no duplicate components.
- **Glass-morphism for all map UI overlays** (connection pill, controls, sheets) — visual continuity with the rest of the app.
- **`tracksViewChanges={false}`** on every `<Marker>` — make-or-break perf knob; without it the map re-renders all markers on every region change.
- **Outbreak zone center = first report's coordinates** — simple, deterministic, but not centroid-aware. Will recompute centroids in v7+.
- **`/reports/nearby` is auth-protected but not ownership-scoped** — every authenticated user sees all SUCCESS reports on the map. Intentional for the demo; revisit privacy / district scoping for production (v8+).

### Offline Support (v9)

- **Server-side idempotency via `(userId, clientId)` unique key** — the cleanest possible "exactly-once" guarantee for retries. NULL `clientId` is preserved (Postgres treats NULLs as distinct) so legacy / sync-only clients can still post.
- **`clientId` lives on the queue item, not generated per attempt** — same uuid persists through every retry of the same draft. The drainer is therefore truly idempotent: if the previous POST actually succeeded but the response was lost, the retry returns the existing row instead of creating a duplicate.
- **TanStack Query persistence over hand-rolled cache** — `@tanstack/react-query-persist-client` + `query-async-storage-persister` was chosen over manually persisting individual stores. Single configuration, zero per-query work, automatic cache busting via `buster` field, automatic stale eviction via `maxAge`.
- **`gcTime: 7 days, maxAge: 24h`** — gcTime must be ≥ persistence age, otherwise queries are GC'd before they're rehydrated. The 24h max-age is honest: stale offline data is fine for a few hours, not days.
- **Mutations not persisted** — only the upload mutation needs durability, and we already have a hand-built queue for that. Persisting mutations would muddle the contract.
- **Network state as a 4-value enum** (`online | offline | unstable | unknown`) over a boolean — `isInternetReachable` from NetInfo is tri-state (true/false/null); collapsing that to a boolean loses the "haven't probed yet" signal that drives the banner UX.
- **Sync-status store as a derived view** — keeps the queue store the single source of truth for queue items themselves, while UI surfaces (banner, indicator, queue card) read a normalized status from one place. Saves N components from re-deriving the same state.
- **Versioned, namespace-prefixed `persistentStorage` wrapper** — `crop-disease.cache.<name>.v<n>`. Bump the version to nuke old shapes; namespace-prefix lets us `clearAll()` on logout without touching unrelated AsyncStorage keys.
- **Drop-in MMKV/SQLite swap point** — every consumer reads/writes through `persistentStorage`, so the underlying driver is one file change. Did NOT add MMKV today (extra dependency, requires native build).
- **Live-reports store persists in-memory cache** — debounced (500ms) to avoid hammering AsyncStorage during socket bursts. Bounded by the existing 1000-item cap so persisted data stays small.
- **Uploading items reset to `pending` on hydrate** — already shipped in v4; calling it out as the recovery story for crashed mid-upload state.
- **`OfflineBanner` lives above the auth-gated tree, not above the splash** — pre-auth users see no banner. They have nothing to sync.
- **`QueueStatusCard` is action-oriented; `SyncIndicator` is informational** — the card has the "Retry now" CTA, the indicator just communicates state. Two components instead of one mega-component.
- **`retryAll` mutation on the queue store** clears `nextAttemptAt` AND `attempts`, so even items that hit the 5-attempt cap can be retried after the user gets a stable network. Honest UX: if the user explicitly asks to retry, we should actually retry.
- **`offlineAiClient` ships as a stub, not as a no-op** — the interface is real, the failure mode is structured (`errorCode: UNAVAILABLE`). v10+ can wire a TFLite/ONNX implementation in without touching the upload flow.
- **Did NOT install MMKV** — explicit decision to stay on AsyncStorage for v9. MMKV requires native module linking; the persistence abstraction (`persistentStorage`) lets us swap whenever the cost is worth it.
- **Did NOT implement background fetch** (`expo-background-fetch` / iOS BGTask) — out of scope for v9. The drainer fires on `NetInfo` events and on app foreground, which covers ~90% of real-world reconnects.
- **No conflict resolution UI** — server is authoritative; on retry the server returns the existing row, which the mobile already accepts as success. No diverging state to merge.

### Polish, Performance & Demo (v10)

- **`DEMO_MODE` env flag over a hard-coded fork** — the same code path serves real and demo. In demo mode: faster mock AI, biased toward HIGH severity for visible drama, healthy-crop chance dropped from 12% to 3%. Production deploys flip one env var.
- **Default `DEMO_MODE=true` in `.env.example`, default `false` in `env.schema`** — anyone cloning the repo gets the demo experience out of the box, but real deploys are explicit. Honest defaults at both layers.
- **30 s in-memory cache on `OutbreakService.list`** instead of Redis — single-instance is the hackathon reality. The cache is invalidated explicitly on every outbreak mutation in the processor, so freshness is event-driven not just TTL-driven.
- **Idempotent demo seed** keyed by `(userId, clientId)` for reports and `(userId, name)` for plots — the script can be re-run between demos without leaving stale data behind. Re-runs report `0 created, N updated`.
- **Demo seed via `pnpm` script, not a protected endpoint** — security through inaccessibility (the script needs DB credentials, no public surface area). Skipped HTTP-callable seed to avoid the attack surface.
- **`/version` endpoint exposed publicly via `@Public()`** — useful for support, demo verification, and later for rolling-deployment health checks. Includes `gitSha`, `buildTime`, `nodeEnv`, `demoMode`, `startedAt`.
- **`react-error-boundary` over hand-rolled component** — gives us the `useErrorHandler` hook for free and the integration point for any future Sentry adapter is well-known. ~12 KB.
- **Single retry for 5xx with 200–400 ms jitter** — covers transient Neon wake-up failures and demo-day network blips without tipping into "DDoS your own backend" territory. Bounded at 1 retry. POST retries gated on the presence of `clientId` (idempotent).
- **Errors normalized at the interceptor, not at the call site** — every feature hook now branches on `error.normalized.code` instead of doing its own classification. Single source of truth.
- **Token-aware socket reconnect** — `getSocket()` compares the live token with the connection's auth token; if they differ, the socket is torn down (with `removeAllListeners()`) before a fresh connection is made. Eliminates the v8 ghost-listener risk on logout-then-relogin.
- **Toast provider is hand-rolled (170 lines), not `sonner-native`** — every primitive (glass, reanimated entry/exit, severity tints, lucide icons, expo-haptics) was already in the tree. The cost of adding a third-party toast lib was higher than rolling our own.
- **Route transitions vary by group** — `(app)` slides from right (iOS-standard for tabs), `reports/[id]` slides from bottom (modal feel for the result screen which is a "completion"), `(auth)` and `(onboarding)` fade (entry feels snappier when there's no prior context).
- **Haptics on success/warning/error (not info)** — calling `Haptics.notificationAsync()` for every toast is overkill. Reserved for state transitions that deserve a tactile beat.
- **Splash background is brand-700 (`#047857`)** — the leftover Expo blue (`#208AEF`) was a v1 carryover. A green splash is the first signal the app is "agriculture", not "generic Expo template". Single-line change with high visual impact.
- **App scheme is `cropdisease`** for deep links — used by the in-app banner deep-link handler and ready for OS-level URL schemes.
- **Multi-stage Dockerfile (builder → runner)** — non-root user, runtime image only ships `dist/`, `node_modules/`, `prisma/`. Includes `prisma migrate deploy` in the entrypoint so deployments self-migrate.
- **`.dockerignore` carefully scoped** — explicitly excludes `.env`, `.git`, `dist`, etc. Prevents accidental secret leaks into the image.
- **Did NOT add MMKV / Lottie / fast-image** — every previous version held this line. v10 keeps it. AsyncStorage + reanimated + expo-image cover everything we need.
- **Did NOT install Sentry** — would need an account + DSN. Logger abstraction (mobile + backend) is the swap-in point.
- **Did NOT wire EAS project ID** — we don't have an EAS project yet. `app.json` and `eas.json` are configured, but a real `expo build` requires `expo init` against the EAS dashboard first. Documented in `DEMO_RUNBOOK.md`.

---

## Update protocol

After every shipped version:

1. Bump **Last updated** and **Current version** at the top.
2. Update the **Quick status** table.
3. Add a new entry under **Per-version detail** with the same structure as the previous entries.
4. Update **Current end-to-end behavior** if user-visible flow changed.
5. Update **Stack snapshot** if new tech entered the project.
6. Move any items that are now done from **Tech debt** / **Partial implementations** / **What's left** to the resolved sub-section, and add any new debt the version introduced.
7. **Append any new decisions to the Decisions log** (don't rewrite — just add). Group them under the existing categories or create a new one if needed.
8. If the **How to run** steps changed, update them.
