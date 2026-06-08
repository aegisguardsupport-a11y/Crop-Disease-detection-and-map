# AgroRadar — App Screen Design Inventory

> **Purpose:** Provide the UI/UX designer with a complete, screen-by-screen breakdown of every view in the AgroRadar mobile app, including layout, components, states, and visual notes.

---

## Table of Contents

1. [Auth Flow](#1-auth-flow)
   - Login Screen
   - OTP Verification Screen
2. [Onboarding Flow](#2-onboarding-flow)
   - Name Input Screen
   - First Plot Setup Screen
3. [Main App (Tabbed)](#3-main-app-tabbed)
   - Dashboard (Home)
   - Disease Map
   - Upload / Report Flow
   - Profile
   - Notifications
4. [Sub-Screens](#4-sub-screens)
   - Report Detail Screen
5. [Shared Bottom Sheets](#5-shared-bottom-sheets)
   - Edit Details Sheet
   - Map Filter Sheet
6. [Summary for Designer](#6-summary-for-designer)

---

## 1. Auth Flow

### Login Screen
- **Route:** `/login`
- **Layout:** Vertically centered, single-column layout with subtle gradient branding.
- **Visual Elements:**
  - **App Logo:** Styled 🌾 icon within a rounded square (gradient background).
  - **Header:** "Welcome to AgroRadar" (large, bold).
  - **Subheader:** "Detect, report, and track crop diseases together."
  - **Input Field:** Phone number input with +91 fixed prefix.
  - **CTA:** "Send OTP" (primary gradient button).
  - **Footer:** Demo usage hint (`Demo: use +91 9999999999...`).
- **States:**
  - *Default:* Empty input.
  - *Loading:* Button text changes to "Sending OTP…", disabled state.
  - *Error:* Inline red text below input (e.g., "Enter a 10-digit phone number").

### OTP Verification Screen
- **Route:** `/otp`
- **Layout:** Centered content, consistent with Login Screen.
- **Visual Elements:**
  - **Back Button:** Text link "‹ Back".
  - **Header:** "Enter 6-digit code".
  - **Subheader:** "Sent to +91 {phone}".
  - **Input:** 6-digit OTP input box (auto-focus).
  - **Resend Timer:** Disabled text link with countdown (e.g., "Resend in 25s").
  - **CTA:** "Verify" (primary gradient button).
- **States:**
  - *Default:* Empty input.
  - *Typing:* Auto-submits when 6th digit is entered.
  - *Loading:* Button shows "Verifying…".
  - *Error:* Inline red text (e.g., "Invalid code").
  - *Resend Activated:* Timer expires, text link turns active (brand color).

---

## 2. Onboarding Flow

### Name Input Screen
- **Route:** `/name`
- **Layout:** Step indicator (Step 1 of 2) at top, vertically centered input area.
- **Visual Elements:**
  - **Step Indicator:** Text label "Step 1 of 2".
  - **Header:** "What should we call you?"
  - **Subheader:** "Helps neighboring farmers recognize your reports."
  - **Input Field:** "e.g. Ramesh Patil" (auto-capitalize words).
  - **CTAs:** Split footer — "Skip" (ghost button) and "Continue" (gradient button).
- **States:**
  - *Empty:* Placeholder visible.
  - *Error:* Red border + error text below field (e.g., "Tell us what to call you.").
  - *Loading:* Continue button shows "Saving…".

### First Plot Setup Screen
- **Route:** `/first-plot`
- **Layout:** Step indicator (Step 2 of 2) at top, feature card in the middle, stacked CTAs at the bottom.
- **Visual Elements:**
  - **Step Indicator:** Text label "Step 2 of 2".
  - **Header:** "Add your first plot".
  - **Subheader:** "We'll alert you when a disease outbreak is detected near it."
  - **Feature Card:** Icon (layers) + headline "Plot-based alerts" + description.
  - **CTAs:** "Add a plot" (gradient) and "I'll do this later" (tertiary link).
- **States:**
  - *Default:* As described above.
  - *Plot Form Modal:* Tapping "Add a plot" slides up the Plot Form Bottom Sheet.

---

## 3. Main App (Tabbed)

### Dashboard (Home)
- **Route:** `/ (index)`
- **Layout:** Scrollable vertical feed with multiple distinct sections.
- **Visual Elements:**
  - **Greeting Header:** "Good morning, {Name}" + user avatar (tappable, leads to Profile).
  - **Outbreak Summary Card:** Alert-style card showing nearby outbreak count and a "View on map" link.
  - **Quick Upload CTA:** Prominent tappable card or large button to initiate a new report.
  - **Recent Reports Section:** List of user's last 3-5 uploaded reports (thumbnail, crop name, date).
  - **Empty State:** "No reports yet" with a "Scan first crop" prompt.
- **Interactions:** Pull-to-refresh on the entire feed.

### Disease Map
- **Route:** `/map`
- **Layout:** Full-screen interactive map with overlaid UI controls.
- **UI Overlays:**
  - **Search Bar:** Top center, with a search icon and placeholder text.
  - **Filter Chips:** Horizontal scrollable list beneath the search bar (Severity, Crop, etc.).
  - **Floating Action Button (FAB):** Bottom right, a "+" icon to add a new report.
  - **User Location Button:** Floating button to re-center the map on the user's current location.
- **Map Markers:**
  - Disease reports shown as pins.
  - Pins require distinct visual coding by **severity** (Color/Shape).
  - Tapping a pin opens the **Report Detail Bottom Sheet**.
- **Interactions:** Pinch to zoom, drag to pan, tap pin for details, long-press map to initiate a report.

### Upload / Report Flow
- **Route:** `/upload`
- **Layout:** State-managed full-screen flow (4 steps).
This is the most complex screen and is broken down into 4 sub-states:

#### Step 1: Capture
- **Layout:** Full-screen Camera Preview.
- **UI Overlays:**
  - **Top Bar:** Close (X) button, "Step 1 of 4" label, Flash toggle.
  - **Bottom Bar:** Large shutter button, gallery icon (left), symmetry spacer (right).
  - **Secondary State:** If camera permission is denied, displays a permission request card with "Allow camera" and "Choose from gallery" buttons.

#### Step 2: Analyzing
- **Layout:** Centered vertical stack.
- **Visual Elements:**
  - Thumbnail of the captured image (140x140px).
  - Large brand-colored spinner.
  - "Analyzing your photo" heading.
  - Status checklist card (e.g., "✓ Image quality good", "✓ Leaf detected", "● Identifying disease…").

#### Step 3: Result
- **Layout:** Scrollable content with a sticky bottom CTA.
- **Visual Elements:**
  - Crop image thumbnail.
  - Detected disease name (headline).
  - Confidence score (e.g., "Cloud diagnosis · 94% match").
  - Severity badge and status chips.
  - **Alternative State (Low Confidence):** "Pick the closest match" with a list of candidate diseases and their confidence percentages.
  - **Recommendations:** Scrollable list of actionable advice cards.
  - "Wrong diagnosis? Edit details" link.
  - **Share Toggle:** "Share to public map" (on/off toggle).
  - **Sticky Footer:** "Confirm & submit" button.

#### Step 4: Submitted
- **Layout:** Centered success view with bottom CTAs.
- **Visual Elements:**
  - Animated gradient checkmark icon.
  - "Submitted" heading.
  - Subtitle text (e.g., "Visible to nearby agronomists and farmers.").
  - Summary card (Crop, Disease, Date).
  - **CTAs:** "View on map" and "Report another" / "View this report".

### Profile
- **Route:** `/profile`
- **Layout:** Scrollable settings page.
- **Visual Elements:**
  - **User Card:** Large avatar, full name, verified badge, phone number.
  - **Stats Row:** "Reports submitted", "Plots" (tappable, opens Plot management).
  - **Plots Section:** List of saved plots (if any), "Add plot" button, empty state description.
  - **Settings List Grouped by Card:**
    - Notifications (with current status, e.g., "On")
    - Alert radius (with current distance, e.g., "5 km")
    - Language (with current selection, e.g., "English")
    - Location (with current location text)
  - **Destructive Action:** "Sign out" button (outlined, red/danger text).

### Notifications
- **Route:** `/notifications`
- **Layout:** Scrollable grouped list (grouped by day).
- **Visual Elements:**
  - **Header:** "Alerts" + subheader "Outbreaks and updates from your region".
  - **Mark All Read:** Text link at the top right if unread items exist.
  - **Filter Chips:** "All", "Unread", "Outbreaks", etc.
  - **Notification Cards:** Icon, title, body, timestamp, unread indicator.
  - **Empty State:** "All clear in your area" with an emoji (🌾) and a "Adjust alert radius" action.

---

## 4. Sub-Screens

### Report Detail Screen
- **Route:** `/reports/{id}`
- **Layout:** Detailed, long-form scrollable view.
- **Visual Elements:**
  - **Header:** Back button (rounded border), "Report" title, More options (⋯).
  - **Hero Image:** Large, high-quality photo of the affected crop.
  - **Info Card:** 
    - Confidence ring visualization (large).
    - Detected disease name (headline).
    - Severity badge.
    - Processing date (e.g., "Analyzed 2 hours ago").
  - **Notes Card:** User-added notes (if present).
  - **Recommendations Section:**
    - Header "Recommended actions".
    - "Re-run" analysis link.
    - List of specific recommendations.
  - **Actions Component:** "Upload another" and "View on map" CTAs.
  - **Disclaimer:** Small text at the bottom regarding AI advisory nature.
- **States:**
  - *Loading:* Centered spinner.
  - *Error:* "Couldn't load report" with a Retry button.
  - *Processing:* Shows a processing state with the image and a status message.

---

## 5. Shared Bottom Sheets

### Edit Details Bottom Sheet
- **Usage:** Upload flow (Result step), Report Detail.
- **Content:**
  - Disease name text input.
  - Severity selector (Low / Medium / High pills or slider).
  - Additional notes multiline text input.

### Map Filter Bottom Sheet
- **Usage:** Map screen (triggered by search or filter icon).
- **Content:**
  - Severity checkboxes (multi-select).
  - Crop type multi-select dropdown/chips.
  - Time range selector (e.g., Last 24 hours, Last week).

---

## 6. Summary for Designer

The following table outlines the design priority and key notes for each screen to be created.

| Screen | Priority | Key Design Notes |
| :--- | :--- | :--- |
| **Login** | High | Clean, simple, strong branding with gradient. |
| **OTP** | High | Secure feel, easy-to-use 6-digit input, clear states. |
| **Onboarding** | High | Minimalist 2-step flow, friendly and inviting. |
| **Dashboard** | Critical | High visual hierarchy for alerts/CTAs. Needs empty and loading states. |
| **Map** | Critical | Custom map pin designs for severity levels (Low/Med/High). Clear filter controls. |
| **Upload Flow** | Critical | 4-step linear flow. Needs strong progress indication and clear feedback during analysis. |
| **Report Detail** | Critical | Dense data (medical/agricultural). Excellent typography is key. Needs skeleton/error states. |
| **Profile** | Medium | Standard settings layout. Grouped list items in cards. |
| **Notifications** | Medium | Clear distinction between read/unread states. |

### Design System Requirements
To ensure consistency, the following system elements must be defined:

1.  **Color-Coded Severity:** A consistent palette for severity levels.
    - `Low:` Green
    - `Medium:` Amber/Orange
    - `High:` Red
2.  **Map Markers/Pins:** A family of custom icons/shapes for map pins that clearly communicate the severity and type of the disease report.
3.  **Loading & Success States:** A library of animations or visual indicators for spinners, checkmarks, and skeleton screens.
4.  **Bottom Sheet Pattern:** A consistent visual for all bottom sheets (rounded top corners, drag handle, darkened backdrop, animation style).
5.  **Typography Scale:** A clear hierarchy for Headings (e.g., disease names), Body Text (e.g., recommendations), and Meta Text (e.g., dates, confidence scores).