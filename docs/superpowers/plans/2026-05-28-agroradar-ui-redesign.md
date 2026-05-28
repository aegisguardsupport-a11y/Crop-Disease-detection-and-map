# AgroRadar UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace AgroRadar's current dark UI with a clean, light "Soft Sage" design system across every screen of `apps/mobile`, while restructuring the report flow into a 4-step Capture → Analyzing → Result → Submitted sequence backed by a cloud-AI / on-device-AI / manual fallback chain.

**Architecture:** Light-only theme driven by a single set of CSS variables (`global.css`) and TypeScript tokens (`theme/colors.ts`). No new dependencies — every visual is built from `expo-linear-gradient`, `nativewind`, `react-native-reanimated`, `lucide-react-native`, `@gorhom/bottom-sheet`, and `expo-image-picker` already in `package.json`. The center FAB in the tab bar becomes the primary entry to the report flow. Dark-mode code paths are removed entirely.

**Tech Stack:** Expo SDK 56, Expo Router, React Native 0.85, NativeWind v5, Tailwind v4, Reanimated 4, TanStack Query, Zustand.

**Source spec:** `docs/superpowers/specs/2026-05-28-agroradar-ui-redesign-design.md`

**Read first:** `apps/mobile/AGENTS.md` instructs that any code touching Expo APIs (camera, permissions, notifications) must be checked against https://docs.expo.dev/versions/v56.0.0/. Do this before Task 7.

**Verification commands** (re-run after each task):
- `pnpm --filter mobile typecheck`
- `pnpm --filter mobile lint`
- `pnpm --filter mobile dev` and visually verify the touched screens on a device or simulator

---

## Task 1: Theme tokens & global.css — Soft Sage palette

**Files:**
- Modify: `apps/mobile/src/theme/colors.ts`
- Modify: `apps/mobile/src/theme/shadows.ts`
- Modify: `apps/mobile/src/theme/radii.ts`
- Modify: `apps/mobile/src/global.css`
- Modify: `apps/mobile/src/hooks/use-color-scheme.ts`
- Modify: `apps/mobile/src/hooks/use-theme.ts`
- Modify: `apps/mobile/src/providers/theme-provider.tsx`
- Modify: `apps/mobile/src/app/_layout.tsx`

- [ ] **Step 1: Replace `theme/colors.ts` with the Soft Sage palette (light only)**

```ts
/**
 * Color tokens for the AgroRadar app — Soft Sage (light-only).
 * Mirrored into Tailwind theme via global.css CSS variables.
 */
export const palette = {
  brand: {
    50: '#ecfdf5',
    100: '#d1fae5',
    200: '#a7f3d0',
    300: '#6ee7b7',
    400: '#34d399',
    500: '#10b981',
    600: '#0d9488',
    700: '#047857',
    800: '#065f46',
    900: '#064e3b',
  },
  status: {
    success: '#047857',
    successTint: '#ecfdf5',
    warning: '#92400e',
    warningTint: '#fef3c7',
    danger: '#b91c1c',
    dangerTint: '#fee2e2',
    info: '#1d4ed8',
    infoTint: '#dbeafe',
  },
} as const;

export const lightColors = {
  bg: '#fbfaf7',
  surface: '#ffffff',
  surfaceMuted: '#fdfcf7',
  surfaceElevated: '#ffffff',
  border: '#efeae0',
  borderStrong: '#e8e4dc',
  text: '#0b1220',
  textMuted: '#475569',
  textSubtle: '#64748b',
  textFaint: '#94a3b8',
  textInverse: '#ffffff',
  primary: palette.brand[600],
  primaryStart: palette.brand[500],
  primaryEnd: palette.brand[600],
  primaryDeep: palette.brand[900],
  primaryTint: palette.brand[50],
  success: palette.status.success,
  successTint: palette.status.successTint,
  warning: palette.status.warning,
  warningTint: palette.status.warningTint,
  danger: palette.status.danger,
  dangerTint: palette.status.dangerTint,
  info: palette.status.info,
  infoTint: palette.status.infoTint,
} as const;

export type ThemePalette = typeof lightColors;
export type ColorScheme = 'light';

/** Light-only after redesign. The export shape is kept for backwards compat. */
export const themes: Record<ColorScheme, ThemePalette> = {
  light: lightColors,
};
```

- [ ] **Step 2: Update `theme/shadows.ts` for the new shadow scale**

```ts
import { Platform, ViewStyle } from 'react-native';

type Shadow = Pick<
  ViewStyle,
  'shadowColor' | 'shadowOffset' | 'shadowOpacity' | 'shadowRadius' | 'elevation'
>;

const make = (
  shadowColor: string,
  shadowOpacity: number,
  shadowRadius: number,
  offsetY: number,
  elevation: number,
): Shadow => ({
  shadowColor,
  shadowOffset: { width: 0, height: offsetY },
  shadowOpacity,
  shadowRadius,
  elevation: Platform.OS === 'android' ? elevation : 0,
});

/**
 * Soft, single-source shadow scale for the Soft Sage theme.
 * `cta` and `ctaSoft` use the brand-teal color so primary buttons feel "lifted".
 */
export const shadows = {
  none: make('transparent', 0, 0, 0, 0),
  card: make('#0f172a', 0.03, 2, 1, 1),
  cardHover: make('#0f172a', 0.06, 24, 8, 4),
  sheet: make('#0f172a', 0.08, 24, -8, 8),
  cta: make('#0d9488', 0.32, 14, 6, 6),
  ctaSoft: make('#0d9488', 0.18, 10, 4, 4),
} as const;

export type ShadowToken = keyof typeof shadows;
```

- [ ] **Step 3: Add a `2xl` radius for sheets in `theme/radii.ts`**

```ts
export const radii = {
  none: 0,
  xs: 4,
  sm: 6,
  md: 10,
  lg: 12,
  xl: 14,
  '2xl': 20,
  '3xl': 24,
  full: 9999,
} as const;

export type RadiusToken = keyof typeof radii;
```

- [ ] **Step 4: Replace `global.css` to mirror new tokens and remove dark mode**

```css
@import 'tailwindcss/theme.css' layer(theme);
@import 'tailwindcss/preflight.css' layer(base);
@import 'tailwindcss/utilities.css';

/* Platform-specific font families (per react-native-css media queries) */
@media android {
  :root {
    --font-mono: monospace;
    --font-rounded: normal;
    --font-serif: serif;
    --font-sans: normal;
  }
}

@media ios {
  :root {
    --font-mono: ui-monospace;
    --font-serif: ui-serif;
    --font-sans: system-ui;
    --font-rounded: ui-rounded;
  }
}

/* AgroRadar — Soft Sage design tokens (light-only) */
:root {
  /* Brand */
  --color-brand-50: #ecfdf5;
  --color-brand-100: #d1fae5;
  --color-brand-200: #a7f3d0;
  --color-brand-300: #6ee7b7;
  --color-brand-400: #34d399;
  --color-brand-500: #10b981;
  --color-brand-600: #0d9488;
  --color-brand-700: #047857;
  --color-brand-800: #065f46;
  --color-brand-900: #064e3b;

  /* Surfaces */
  --color-bg: #fbfaf7;
  --color-surface: #ffffff;
  --color-surface-muted: #fdfcf7;
  --color-surface-elevated: #ffffff;
  --color-border: #efeae0;
  --color-border-strong: #e8e4dc;

  /* Text */
  --color-text: #0b1220;
  --color-text-muted: #475569;
  --color-text-subtle: #64748b;
  --color-text-faint: #94a3b8;
  --color-text-inverse: #ffffff;

  /* Status */
  --color-success: #047857;
  --color-success-tint: #ecfdf5;
  --color-warning: #92400e;
  --color-warning-tint: #fef3c7;
  --color-danger: #b91c1c;
  --color-danger-tint: #fee2e2;
  --color-info: #1d4ed8;
  --color-info-tint: #dbeafe;
}

/* Register design tokens as Tailwind theme colors */
@layer theme {
  @theme {
    --color-brand-50: var(--color-brand-50);
    --color-brand-100: var(--color-brand-100);
    --color-brand-200: var(--color-brand-200);
    --color-brand-300: var(--color-brand-300);
    --color-brand-400: var(--color-brand-400);
    --color-brand-500: var(--color-brand-500);
    --color-brand-600: var(--color-brand-600);
    --color-brand-700: var(--color-brand-700);
    --color-brand-800: var(--color-brand-800);
    --color-brand-900: var(--color-brand-900);

    --color-bg: var(--color-bg);
    --color-surface: var(--color-surface);
    --color-surface-muted: var(--color-surface-muted);
    --color-surface-elevated: var(--color-surface-elevated);
    --color-border: var(--color-border);
    --color-border-strong: var(--color-border-strong);

    --color-text: var(--color-text);
    --color-text-muted: var(--color-text-muted);
    --color-text-subtle: var(--color-text-subtle);
    --color-text-faint: var(--color-text-faint);
    --color-text-inverse: var(--color-text-inverse);

    --color-success: var(--color-success);
    --color-success-tint: var(--color-success-tint);
    --color-warning: var(--color-warning);
    --color-warning-tint: var(--color-warning-tint);
    --color-danger: var(--color-danger);
    --color-danger-tint: var(--color-danger-tint);
    --color-info: var(--color-info);
    --color-info-tint: var(--color-info-tint);

    --font-display:
      Inter, ui-sans-serif, system-ui, sans-serif, 'Apple Color Emoji',
      'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';

    --radius-xs: 4px;
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 12px;
    --radius-xl: 14px;
    --radius-2xl: 20px;
    --radius-3xl: 24px;
  }
}
```

- [ ] **Step 5: Force light scheme by replacing `hooks/use-color-scheme.ts`**

```ts
import type { ColorScheme } from '@/theme/colors';

/**
 * After the v10 redesign, AgroRadar is light-only. This hook is kept as the
 * single import point so existing call sites don't need to be touched.
 */
export function useColorScheme(): ColorScheme {
  return 'light';
}
```

- [ ] **Step 6: Simplify `hooks/use-theme.ts`**

```ts
import { lightColors, type ThemePalette } from '@/theme/colors';

/** Returns the active palette. Light-only after redesign. */
export function useTheme(): ThemePalette {
  return lightColors;
}
```

- [ ] **Step 7: Simplify `providers/theme-provider.tsx`**

```tsx
import { createContext, useContext, type ReactNode } from 'react';

import { lightColors, type ColorScheme, type ThemePalette } from '@/theme/colors';

interface ThemeContextValue {
  scheme: ColorScheme;
  colors: ThemePalette;
}

const VALUE: ThemeContextValue = { scheme: 'light', colors: lightColors };
const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  return <ThemeContext.Provider value={VALUE}>{children}</ThemeContext.Provider>;
}

export function useThemeContext(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useThemeContext must be used inside <ThemeProvider>');
  return ctx;
}
```

- [ ] **Step 8: Force light status bar in `app/_layout.tsx`**

In `apps/mobile/src/app/_layout.tsx`, replace the lines:

```tsx
const scheme = useColorScheme();
const navTheme = scheme === 'dark' ? DarkTheme : DefaultTheme;
```

with:

```tsx
const navTheme = DefaultTheme;
```

And replace:

```tsx
<StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
```

with:

```tsx
<StatusBar style="dark" />
```

Remove the now-unused `useColorScheme` import (`react-native`) and `DarkTheme` import (`expo-router`).

- [ ] **Step 9: Run typecheck and lint**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile lint
```

Expected: PASS. Some warnings about unused `dark` references in feature components are fine — they'll be cleaned in subsequent tasks.

- [ ] **Step 10: Commit**

```bash
git add apps/mobile/src/theme apps/mobile/src/global.css apps/mobile/src/hooks/use-color-scheme.ts apps/mobile/src/hooks/use-theme.ts apps/mobile/src/providers/theme-provider.tsx apps/mobile/src/app/_layout.tsx
git commit -m "feat(mobile): introduce Soft Sage theme tokens, drop dark mode"
```

---

## Task 2: UI primitives — Button, Card, Input, Avatar, Skeleton, Loader, EmptyState

**Files:**
- Modify: `apps/mobile/src/components/ui/button.tsx`
- Modify: `apps/mobile/src/components/ui/card.tsx`
- Modify: `apps/mobile/src/components/ui/input.tsx`
- Modify: `apps/mobile/src/components/ui/avatar.tsx`
- Modify: `apps/mobile/src/components/ui/skeleton.tsx`
- Modify: `apps/mobile/src/components/ui/loader.tsx`
- Modify: `apps/mobile/src/components/feedback/empty-state.tsx`
- Create: `apps/mobile/src/components/ui/chip.tsx`
- Create: `apps/mobile/src/components/ui/section-label.tsx`
- Modify: `apps/mobile/src/components/ui/index.ts`

- [ ] **Step 1: Replace `components/ui/button.tsx` with the gradient-aware Button**

```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { forwardRef } from 'react';
import { ActivityIndicator } from 'react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';

type Variant = 'gradient' | 'solid' | 'ghost' | 'destructive';
type Size = 'sm' | 'md' | 'lg';

const sizeContainer: Record<Size, string> = {
  sm: 'h-10 px-4 rounded-xl',
  md: 'h-12 px-5 rounded-xl',
  lg: 'h-14 px-6 rounded-2xl',
};

const sizeLabel: Record<Size, string> = {
  sm: 'text-sm font-bold',
  md: 'text-base font-bold',
  lg: 'text-base font-bold',
};

export interface ButtonProps {
  label: string;
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  leftSlot?: React.ReactNode;
  rightSlot?: React.ReactNode;
  className?: string;
  haptic?: boolean;
  fullWidth?: boolean;
  testID?: string;
}

/**
 * Soft Sage button.
 * - `gradient` (default) — emerald→teal gradient with brand shadow. Primary CTA.
 * - `ghost` — white with brand-tint border + brand-teal text.
 * - `solid` — solid surface, dark text. For neutral confirmations.
 * - `destructive` — danger background, white text.
 */
export const Button = forwardRef<React.ComponentRef<typeof PressableScale>, ButtonProps>(
  function Button(
    {
      label,
      variant = 'gradient',
      size = 'md',
      loading = false,
      disabled = false,
      onPress,
      leftSlot,
      rightSlot,
      className,
      haptic = true,
      fullWidth = true,
      testID,
    },
    ref,
  ) {
    const isDisabled = disabled || loading;
    const hapticIntensity = !haptic
      ? 'none'
      : variant === 'destructive'
        ? 'medium'
        : variant === 'gradient'
          ? 'light'
          : 'selection';
    const labelTone =
      variant === 'gradient' || variant === 'destructive'
        ? 'text-white'
        : variant === 'ghost'
          ? 'text-brand-600'
          : 'text-text';

    const containerBase = cn(
      'flex-row items-center justify-center gap-2 overflow-hidden',
      sizeContainer[size],
      fullWidth && 'self-stretch',
      isDisabled && 'opacity-60',
      className,
    );

    const inner = loading ? (
      <ActivityIndicator
        color={variant === 'gradient' || variant === 'destructive' ? '#fff' : palette.brand[600]}
      />
    ) : (
      <>
        {leftSlot ? <View className="mr-1">{leftSlot}</View> : null}
        <Text className={cn(sizeLabel[size], labelTone)}>{label}</Text>
        {rightSlot ? <View className="ml-1">{rightSlot}</View> : null}
      </>
    );

    if (variant === 'gradient') {
      return (
        <PressableScale
          ref={ref}
          accessibilityRole="button"
          accessibilityState={{ disabled: isDisabled, busy: loading }}
          disabled={isDisabled}
          onPress={onPress}
          haptic={hapticIntensity}
          pressedScale={size === 'lg' ? 0.97 : 0.96}
          testID={testID}
          className={containerBase}
          style={{
            shadowColor: palette.brand[600],
            shadowOffset: { width: 0, height: 6 },
            shadowOpacity: isDisabled ? 0 : 0.32,
            shadowRadius: 14,
            elevation: isDisabled ? 0 : 6,
          }}
        >
          <LinearGradient
            colors={[palette.brand[500], palette.brand[600]]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={{ position: 'absolute', inset: 0 }}
          />
          {inner}
        </PressableScale>
      );
    }

    const bg =
      variant === 'destructive'
        ? 'bg-danger'
        : variant === 'ghost'
          ? 'border border-brand-200 bg-surface'
          : 'bg-surface border border-border';

    return (
      <PressableScale
        ref={ref}
        accessibilityRole="button"
        accessibilityState={{ disabled: isDisabled, busy: loading }}
        disabled={isDisabled}
        onPress={onPress}
        haptic={hapticIntensity}
        pressedScale={size === 'lg' ? 0.97 : 0.96}
        testID={testID}
        className={cn(containerBase, bg)}
      >
        {inner}
      </PressableScale>
    );
  },
);
```

- [ ] **Step 2: Replace `components/ui/card.tsx` with glow + light variants**

```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { type ReactNode } from 'react';
import { type ViewStyle } from 'react-native';

import { View } from '@/tw';
import { palette } from '@/theme/colors';
import { shadows, type ShadowToken } from '@/theme/shadows';
import { cn } from '@/utils/cn';

type Variant = 'flat' | 'elevated' | 'outlined' | 'glow';

const variantClasses: Record<Variant, string> = {
  flat: 'bg-surface border border-border',
  elevated: 'bg-surface border border-border',
  outlined: 'bg-bg border border-border',
  glow: 'bg-surface border border-border overflow-hidden',
};

export interface CardProps {
  children: ReactNode;
  variant?: Variant;
  shadow?: ShadowToken;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  className?: string;
  style?: ViewStyle;
}

const padClass = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-5',
};

/**
 * Soft Sage card.
 * Use `glow` for hero data cards (subtle brand-tinted radial highlight in
 * the background). Otherwise use `flat`.
 */
export function Card({
  children,
  variant = 'flat',
  shadow = 'card',
  padding = 'md',
  className,
  style,
}: CardProps) {
  return (
    <View
      className={cn('rounded-xl', variantClasses[variant], padClass[padding], className)}
      style={[shadows[shadow], style]}
    >
      {variant === 'glow' ? (
        <LinearGradient
          pointerEvents="none"
          colors={[`${palette.brand[400]}26`, 'transparent']}
          start={{ x: 0.1, y: 0.1 }}
          end={{ x: 0.85, y: 0.9 }}
          style={{ position: 'absolute', inset: 0 }}
        />
      ) : null}
      <View>{children}</View>
    </View>
  );
}
```

- [ ] **Step 3: Restyle `components/ui/input.tsx` for the light theme**

Replace the body of `Input` (keep the `forwardRef` signature and props identical) with:

```tsx
return (
  <View className={cn('gap-1.5', className)}>
    {label ? (
      <Text className="text-xs font-bold uppercase tracking-[1.4px] text-text-subtle">
        {label}
      </Text>
    ) : null}

    <View
      className={cn(
        'flex-row items-center rounded-xl border bg-surface px-3',
        multiline ? 'min-h-24 py-3 items-start' : 'h-12',
        focused && !hasError ? 'border-brand-600' : 'border-border',
        focused && !hasError ? 'border-2' : 'border',
        hasError && 'border-danger',
        !editable && 'opacity-60',
      )}
    >
      {leftSlot ? <View className="mr-2">{leftSlot}</View> : null}

      <TextInput
        ref={ref}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={theme.textFaint}
        secureTextEntry={secureTextEntry}
        autoCapitalize={autoCapitalize}
        keyboardType={keyboardType}
        editable={editable}
        multiline={multiline}
        onFocus={() => {
          setFocused(true);
          onFocus?.();
        }}
        onBlur={() => {
          setFocused(false);
          onBlur?.();
        }}
        testID={testID}
        className="flex-1 text-base text-text"
        style={{ color: theme.text }}
      />

      {rightSlot ? <View className="ml-2">{rightSlot}</View> : null}
    </View>

    {hasError ? (
      <Text className="text-xs font-medium text-danger">{error}</Text>
    ) : helper ? (
      <Text className="text-xs text-text-subtle">{helper}</Text>
    ) : null}
  </View>
);
```

- [ ] **Step 4: Replace `components/ui/avatar.tsx` with gradient initial avatar**

```tsx
import { LinearGradient } from 'expo-linear-gradient';

import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';

export interface AvatarProps {
  name?: string | null;
  fallback?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** When true, draws a thin success ring around the avatar. */
  verified?: boolean;
  className?: string;
}

const sizeClass: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'h-8 w-8',
  md: 'h-11 w-11',
  lg: 'h-14 w-14',
  xl: 'h-16 w-16',
};

const textClass: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'text-xs',
  md: 'text-base',
  lg: 'text-xl',
  xl: 'text-2xl',
};

function getInitials(name?: string | null, fallback = '?'): string {
  if (!name) return fallback;
  const parts = name.trim().split(/\s+/u).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? '').join('') || fallback;
}

/**
 * Soft Sage gradient avatar. Initials only — image upload not in scope.
 * `verified` adds a thin success-tinted ring.
 */
export function Avatar({ name, fallback, size = 'md', verified, className }: AvatarProps) {
  return (
    <View
      className={cn(
        'items-center justify-center overflow-hidden rounded-full',
        sizeClass[size],
        verified && 'border-2 border-success',
        className,
      )}
    >
      <LinearGradient
        colors={[palette.brand[400], palette.brand[600]]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={{ position: 'absolute', inset: 0 }}
      />
      <Text className={cn('font-bold text-white', textClass[size])}>
        {getInitials(name, fallback)}
      </Text>
    </View>
  );
}
```

- [ ] **Step 5: Update `components/ui/skeleton.tsx` shimmer to beige tones**

In `apps/mobile/src/components/ui/skeleton.tsx`:

Replace the `View` className `'overflow-hidden bg-surface'` with `'overflow-hidden bg-border'` so the skeleton base is the warm beige, and update the `LinearGradient` colors block to:

```tsx
<LinearGradient
  colors={['transparent', 'rgba(232,228,220,0.6)', 'rgba(250,250,246,0.9)', 'rgba(232,228,220,0.6)', 'transparent']}
  locations={[0, 0.4, 0.5, 0.6, 1]}
  start={{ x: 0, y: 0.5 }}
  end={{ x: 1, y: 0.5 }}
  style={{ flex: 1 }}
/>
```

- [ ] **Step 6: Replace `components/ui/loader.tsx` with a conic-gradient ring**

```tsx
import { useEffect } from 'react';
import { type ViewStyle } from 'react-native';
import Animated, {
  cancelAnimation,
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from 'react-native-reanimated';

import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';

export interface LoaderProps {
  label?: string;
  size?: number;
  fullscreen?: boolean;
  className?: string;
  style?: ViewStyle;
}

/**
 * Brand-tinted spinner. Two concentric arcs rotating at different speeds.
 * Replaces the prior ActivityIndicator-based loader for visual continuity
 * with the rest of the Soft Sage system.
 */
export function Loader({ label, size = 48, fullscreen, className, style }: LoaderProps) {
  const angle = useSharedValue(0);

  useEffect(() => {
    angle.value = withRepeat(
      withTiming(1, { duration: 1100, easing: Easing.linear }),
      -1,
      false,
    );
    return () => cancelAnimation(angle);
  }, [angle]);

  const ringStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${angle.value * 360}deg` }],
  }));

  const stroke = Math.max(3, Math.round(size * 0.1));

  return (
    <View
      className={cn(
        'items-center justify-center gap-3',
        fullscreen && 'absolute inset-0 bg-bg/80',
        !fullscreen && 'p-4',
        className,
      )}
      style={style}
    >
      <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
        <Animated.View
          style={[
            {
              position: 'absolute',
              width: size,
              height: size,
              borderRadius: size / 2,
              borderWidth: stroke,
              borderColor: palette.brand[100],
              borderTopColor: palette.brand[500],
              borderRightColor: palette.brand[600],
            },
            ringStyle,
          ]}
        />
      </View>
      {label ? <Text className="text-xs font-medium text-text-muted">{label}</Text> : null}
    </View>
  );
}
```

- [ ] **Step 7: Restyle `components/feedback/empty-state.tsx`**

Replace the file with:

```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { type ReactNode } from 'react';

import { Button } from '@/components/ui/button';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';

export interface EmptyStateProps {
  icon?: ReactNode;
  emoji?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

/**
 * Soft Sage empty state — glow tile + title + sub + optional ghost CTA.
 */
export function EmptyState({
  icon,
  emoji,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <View
      className={cn('items-center gap-3 px-6 py-12', className)}
    >
      <View className="h-16 w-16 items-center justify-center overflow-hidden rounded-2xl border border-border bg-surface">
        <LinearGradient
          pointerEvents="none"
          colors={[`${palette.brand[400]}33`, 'transparent']}
          start={{ x: 0.2, y: 0.2 }}
          end={{ x: 0.9, y: 0.9 }}
          style={{ position: 'absolute', inset: 0 }}
        />
        {icon ?? <Text className="text-3xl">{emoji ?? '🌾'}</Text>}
      </View>
      <Text className="text-center text-base font-bold text-text">{title}</Text>
      {description ? (
        <Text className="max-w-[260px] text-center text-sm leading-5 text-text-muted">
          {description}
        </Text>
      ) : null}
      {actionLabel && onAction ? (
        <Button
          label={actionLabel}
          variant="ghost"
          size="sm"
          onPress={onAction}
          fullWidth={false}
          className="mt-2"
        />
      ) : null}
    </View>
  );
}
```

- [ ] **Step 8: Create `components/ui/chip.tsx`**

```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { type ReactNode } from 'react';

import { PressableScale } from '@/components/ui/pressable-scale';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';

type Tone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger' | 'info';

export interface ChipProps {
  label: string;
  active?: boolean;
  tone?: Tone;
  onPress?: () => void;
  leftSlot?: ReactNode;
  className?: string;
}

const toneInactive: Record<Tone, string> = {
  neutral: 'bg-surface border border-border',
  brand: 'bg-brand-50 border border-brand-100',
  success: 'bg-success-tint border border-success-tint',
  warning: 'bg-warning-tint border border-warning-tint',
  danger: 'bg-danger-tint border border-danger-tint',
  info: 'bg-info-tint border border-info-tint',
};

const toneText: Record<Tone, string> = {
  neutral: 'text-text-muted',
  brand: 'text-brand-700',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  info: 'text-info',
};

/**
 * Pill / chip used for filters, severity badges, and small status indicators.
 * Active state always uses the brand gradient regardless of tone (this is what
 * "selected" means visually).
 */
export function Chip({ label, active = false, tone = 'neutral', onPress, leftSlot, className }: ChipProps) {
  const baseClass = cn(
    'flex-row items-center gap-1 rounded-full px-3 py-1.5',
    !active && toneInactive[tone],
    className,
  );

  const labelClass = cn(
    'text-xs font-bold',
    active ? 'text-white' : toneText[tone],
  );

  if (active) {
    return (
      <PressableScale onPress={onPress} disabled={!onPress} pressedScale={0.96} haptic="selection">
        <View className={cn(baseClass, 'overflow-hidden')}>
          <LinearGradient
            colors={[palette.brand[500], palette.brand[600]]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={{ position: 'absolute', inset: 0 }}
          />
          {leftSlot}
          <Text className={labelClass}>{label}</Text>
        </View>
      </PressableScale>
    );
  }

  if (!onPress) {
    return (
      <View className={baseClass}>
        {leftSlot}
        <Text className={labelClass}>{label}</Text>
      </View>
    );
  }

  return (
    <PressableScale onPress={onPress} pressedScale={0.96} haptic="selection">
      <View className={baseClass}>
        {leftSlot}
        <Text className={labelClass}>{label}</Text>
      </View>
    </PressableScale>
  );
}
```

- [ ] **Step 9: Create `components/ui/section-label.tsx`**

```tsx
import { Text } from '@/tw';
import { cn } from '@/utils/cn';

export interface SectionLabelProps {
  children: string;
  className?: string;
}

/** Uppercase, tracked, brand-teal label for hero card eyebrows and section eyebrows. */
export function SectionLabel({ children, className }: SectionLabelProps) {
  return (
    <Text
      className={cn(
        'text-[11px] font-bold uppercase tracking-[1.4px] text-brand-700',
        className,
      )}
    >
      {children}
    </Text>
  );
}
```

- [ ] **Step 10: Update `components/ui/index.ts` to export new primitives**

Add to the file:

```ts
export * from './chip';
export * from './section-label';
```

(Keep existing exports.)

- [ ] **Step 11: Run typecheck and lint**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile lint
```

Expected: PASS. The `Button` API change (added `gradient` variant) may trigger lint errors at call sites that pass the old `variant="primary"` — this is expected; those sites get fixed in later tasks. If TypeScript fails on those existing sites, temporarily add `'primary' | 'secondary'` to the `Variant` type union with a deprecation comment so the build stays green:

```ts
type Variant = 'gradient' | 'solid' | 'ghost' | 'destructive' | 'primary' | 'secondary';
```

Map them at the start of the component:

```ts
const effectiveVariant = variant === 'primary' ? 'gradient' : variant === 'secondary' ? 'solid' : variant;
```

These aliases get removed in Task 13.

- [ ] **Step 12: Commit**

```bash
git add apps/mobile/src/components
git commit -m "feat(mobile): rebuild UI primitives for Soft Sage theme"
```

---

## Task 3: Tab bar — light glass + raised gradient FAB

**Files:**
- Modify: `apps/mobile/src/components/navigation/tab-bar.tsx`
- Modify: `apps/mobile/src/components/navigation/tab-bar-icon.tsx`
- Modify: `apps/mobile/src/app/(app)/_layout.tsx`

- [ ] **Step 1: Replace `tab-bar.tsx` with the new light tab bar**

The new tab bar is a 5-cell light card. The 3rd cell (the `upload` route) is rendered as a raised gradient FAB; the other 4 are flat icon+label cells. Replace the entire file with:

```tsx
import type { BottomTabBarProps } from 'expo-router/build/react-navigation/bottom-tabs';
import * as Haptics from 'expo-haptics';
import { LinearGradient } from 'expo-linear-gradient';
import { useEffect } from 'react';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { PressableScale } from '@/components/ui/pressable-scale';
import { NotificationBadge } from '@/features/notifications/components/notification-badge';
import { useUnreadCount } from '@/features/notifications/hooks/use-notifications';
import { useTheme } from '@/hooks/use-theme';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

import { TabBarIcon, type TabIconName } from './tab-bar-icon';

const ROUTE_TO_ICON: Record<string, TabIconName> = {
  index: 'house',
  map: 'map',
  upload: 'plus',
  notifications: 'bell',
  profile: 'user',
};

const ROUTE_TO_LABEL: Record<string, string> = {
  index: 'Home',
  map: 'Map',
  upload: 'Report',
  notifications: 'Alerts',
  profile: 'Profile',
};

export function TabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const unreadCount = useUnreadCount();

  return (
    <View
      pointerEvents="box-none"
      style={{
        position: 'absolute',
        left: 16,
        right: 16,
        bottom: insets.bottom > 0 ? insets.bottom : 12,
      }}
    >
      <View
        className="flex-row items-center justify-between rounded-[22px] border border-border bg-surface px-2 py-2"
        style={{
          shadowColor: '#0f172a',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.06,
          shadowRadius: 16,
          elevation: 8,
        }}
      >
        {state.routes.map((route, index) => {
          const { options } = descriptors[route.key];
          const isFocused = state.index === index;
          const iconName = ROUTE_TO_ICON[route.name] ?? 'house';
          const label = ROUTE_TO_LABEL[route.name] ?? route.name;
          const isFab = iconName === 'plus';

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });
            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name, route.params);
            }
          };

          const onLongPress = () => {
            navigation.emit({ type: 'tabLongPress', target: route.key });
          };

          if (isFab) {
            return (
              <FabTab
                key={route.key}
                label={options.tabBarAccessibilityLabel ?? label}
                onPress={onPress}
                onLongPress={onLongPress}
              />
            );
          }

          const tint = isFocused ? theme.primary : theme.textSubtle;

          return (
            <RegularTab
              key={route.key}
              accessibilityLabel={options.tabBarAccessibilityLabel ?? label}
              isFocused={isFocused}
              iconName={iconName}
              label={label}
              tint={tint}
              onPress={onPress}
              onLongPress={onLongPress}
              badge={
                iconName === 'bell' && unreadCount > 0 ? (
                  <NotificationBadge count={unreadCount} size="sm" />
                ) : null
              }
            />
          );
        })}
      </View>
    </View>
  );
}

interface RegularTabProps {
  accessibilityLabel: string;
  isFocused: boolean;
  iconName: TabIconName;
  label: string;
  tint: string;
  onPress: () => void;
  onLongPress: () => void;
  badge: React.ReactNode;
}

function RegularTab({
  accessibilityLabel,
  isFocused,
  iconName,
  label,
  tint,
  onPress,
  onLongPress,
  badge,
}: RegularTabProps) {
  const focused = useSharedValue(isFocused ? 1 : 0);

  useEffect(() => {
    focused.value = withTiming(isFocused ? 1 : 0, { duration: 180 });
  }, [focused, isFocused]);

  const iconBgStyle = useAnimatedStyle(() => ({
    opacity: focused.value,
  }));

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityState={isFocused ? { selected: true } : {}}
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      onLongPress={onLongPress}
      pressedScale={0.92}
      haptic="selection"
      className="flex-1 items-center justify-center gap-1 rounded-2xl px-2 py-2"
    >
      <View className="overflow-hidden rounded-lg" style={{ width: 28, height: 28, alignItems: 'center', justifyContent: 'center' }}>
        <Animated.View
          pointerEvents="none"
          style={[
            { position: 'absolute', inset: 0, borderRadius: 8, overflow: 'hidden' },
            iconBgStyle,
          ]}
        >
          <LinearGradient
            colors={[`${palette.brand[500]}26`, `${palette.brand[600]}26`]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={{ position: 'absolute', inset: 0 }}
          />
        </Animated.View>
        <View>
          <TabBarIcon name={iconName} focused={isFocused} color={tint} size={20} />
          {badge ? (
            <View style={{ position: 'absolute', top: -4, right: -8 }}>{badge}</View>
          ) : null}
        </View>
      </View>
      <Text
        className="text-[10px] font-bold"
        style={{ color: tint, letterSpacing: 0.3 }}
        numberOfLines={1}
      >
        {label}
      </Text>
    </PressableScale>
  );
}

interface FabTabProps {
  label: string;
  onPress: () => void;
  onLongPress: () => void;
}

/**
 * The center "Report" raised FAB. Sits ~16px above the bar with a brand-tinted
 * shadow, gradient background, and a 3px white ring so it visually separates
 * from the bar.
 */
function FabTab({ label, onPress, onLongPress }: FabTabProps) {
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={() => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => undefined);
        onPress();
      }}
      onLongPress={onLongPress}
      haptic="none"
      pressedScale={0.92}
      className="items-center"
      style={{ transform: [{ translateY: -16 }], width: 56 }}
    >
      <View
        className="h-14 w-14 items-center justify-center overflow-hidden rounded-2xl border-[3px] border-surface"
        style={{
          shadowColor: palette.brand[600],
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.45,
          shadowRadius: 14,
          elevation: 12,
        }}
      >
        <LinearGradient
          colors={[palette.brand[500], palette.brand[600]]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{ position: 'absolute', inset: 0 }}
        />
        <TabBarIcon name="plus" focused color="#ffffff" size={26} />
      </View>
    </PressableScale>
  );
}
```

- [ ] **Step 2: Update `components/navigation/tab-bar-icon.tsx` (remove dark-tinted gradient export)**

Replace the file with:

```tsx
import { Bell, House, Map, Plus, User } from 'lucide-react-native';

export type TabIconName = 'house' | 'map' | 'plus' | 'bell' | 'user';

interface TabBarIconProps {
  name: TabIconName;
  focused: boolean;
  color: string;
  size?: number;
}

const ICONS: Record<TabIconName, typeof House> = {
  house: House,
  map: Map,
  plus: Plus,
  bell: Bell,
  user: User,
};

export function TabBarIcon({ name, focused, color, size = 24 }: TabBarIconProps) {
  const Icon = ICONS[name];
  return (
    <Icon
      size={size}
      color={color}
      strokeWidth={focused ? 2.4 : 2}
      fill={focused && name !== 'plus' ? `${color}1A` : 'transparent'}
    />
  );
}
```

- [ ] **Step 3: Update `(app)/_layout.tsx` tab labels**

In `apps/mobile/src/app/(app)/_layout.tsx`, change the Upload tab label:

```tsx
<Tabs.Screen name="upload" options={{ title: 'Report' }} />
```

(Currently it says `'Upload'`.)

- [ ] **Step 4: Verify on device**

```bash
pnpm --filter mobile dev
```

Open the app, log in, and confirm:
1. The bottom bar is light, not dark.
2. The center cell renders as a raised gradient pill.
3. Tapping the center cell opens the existing upload screen.
4. Other tabs animate the brand-tinted background under their icon when focused.

- [ ] **Step 5: Commit**

```bash
git add apps/mobile/src/components/navigation apps/mobile/src/app/(app)/_layout.tsx
git commit -m "feat(mobile): light tab bar with raised gradient Report FAB"
```

---

## Task 4: Splash + AppErrorBoundary — light theme

**Files:**
- Modify: `apps/mobile/src/app/_layout.tsx` (the `Splash` component at the bottom)
- Modify: `apps/mobile/src/components/error-boundary/app-error-boundary.tsx`

- [ ] **Step 1: Restyle the `Splash` function in `app/_layout.tsx`**

Replace the gradient colors in `Splash` from `[palette.brand[700], palette.brand[900], '#0b1220']` to `[palette.brand[50], palette.surface, '#fbfaf7']` (light gradient background) and update the inner ring/text styles. Replace the body of `Splash`'s returned JSX with:

```tsx
return (
  <View className="flex-1 bg-bg">
    <LinearGradient
      colors={[palette.brand[50], '#ffffff', '#fbfaf7']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={{ position: 'absolute', inset: 0 }}
    />
    <View className="flex-1 items-center justify-center gap-4">
      <View style={{ width: 120, height: 120, alignItems: 'center', justifyContent: 'center' }}>
        <Animated.View
          pointerEvents="none"
          style={[
            {
              position: 'absolute',
              width: 120,
              height: 120,
              borderRadius: 60,
              backgroundColor: palette.brand[400],
              opacity: 0.25,
            },
            glowStyle,
          ]}
        />
        <Animated.View entering={FadeIn.duration(450)} style={breatheStyle}>
          <View
            className="h-20 w-20 items-center justify-center overflow-hidden rounded-3xl border border-border"
            style={{
              shadowColor: palette.brand[600],
              shadowOffset: { width: 0, height: 8 },
              shadowOpacity: 0.25,
              shadowRadius: 18,
              elevation: 8,
            }}
          >
            <LinearGradient
              colors={[palette.brand[400], palette.brand[600]]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={{ position: 'absolute', inset: 0 }}
            />
            <Text className="text-4xl">🌾</Text>
          </View>
        </Animated.View>
      </View>
      <Animated.View entering={FadeIn.delay(150).duration(450)} className="items-center gap-1">
        <Text className="text-xl font-bold text-text">{APP_NAME}</Text>
        <Text className="text-[11px] font-bold uppercase tracking-[3px] text-brand-700">
          Crop intelligence
        </Text>
      </Animated.View>
    </View>
  </View>
);
```

- [ ] **Step 2: Restyle `app-error-boundary.tsx` `DefaultFallback` to the light theme**

Replace the `DefaultFallback` component with:

```tsx
function DefaultFallback({ error, resetErrorBoundary }: FallbackProps) {
  const isDev = __DEV__;
  const message = error instanceof Error ? error.message : String(error);
  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView style={{ flex: 1 }}>
        <View className="flex-1 items-center justify-center gap-6 px-8">
          <Animated.View entering={FadeIn.duration(400)}>
            <View className="h-20 w-20 items-center justify-center rounded-3xl border border-danger/30 bg-danger-tint">
              <AlertTriangle size={36} color={palette.status.danger} strokeWidth={2.2} />
            </View>
          </Animated.View>

          <Animated.View entering={FadeIn.delay(120).duration(400)} className="items-center gap-2">
            <Text className="text-2xl font-bold text-text">Something went wrong</Text>
            <Text className="text-center text-sm text-text-muted">
              We hit an unexpected error. Tap below to try again — your work is saved locally.
            </Text>
            {isDev ? (
              <Text className="mt-3 text-center text-xs text-text-faint" numberOfLines={6}>
                {message}
              </Text>
            ) : null}
          </Animated.View>

          <Animated.View entering={FadeIn.delay(220).duration(400)}>
            <Button
              label="Try again"
              variant="gradient"
              size="md"
              fullWidth={false}
              leftSlot={<RefreshCw size={16} color="#ffffff" strokeWidth={2.4} />}
              onPress={resetErrorBoundary}
            />
          </Animated.View>
        </View>
      </SafeAreaView>
    </View>
  );
}
```

Update the imports at the top: remove `LinearGradient`, `Pressable`, and `palette` if unused; add `Button` from `@/components/ui/button`. Add `palette` import (still needed for `status.danger`).

- [ ] **Step 3: Run typecheck**

```bash
pnpm --filter mobile typecheck
```

- [ ] **Step 4: Commit**

```bash
git add apps/mobile/src/app/_layout.tsx apps/mobile/src/components/error-boundary
git commit -m "feat(mobile): light splash + light error boundary"
```

---

## Task 5: Home screen — Hero-first layout

**Files:**
- Modify: `apps/mobile/src/app/(app)/index.tsx`
- Modify: `apps/mobile/src/features/dashboard/components/greeting-header.tsx`
- Modify: `apps/mobile/src/features/dashboard/components/outbreak-summary.tsx`
- Modify: `apps/mobile/src/features/dashboard/components/quick-upload-cta.tsx`
- Modify: `apps/mobile/src/features/dashboard/components/recent-reports.tsx`
- Modify: `apps/mobile/src/features/dashboard/components/index.ts`

- [ ] **Step 1: Restyle `greeting-header.tsx` for the light theme**

Replace the file with:

```tsx
import Animated, { FadeIn } from 'react-native-reanimated';

import { Avatar } from '@/components/ui/avatar';
import { PressableScale } from '@/components/ui/pressable-scale';
import { SectionLabel } from '@/components/ui/section-label';
import { Text, View } from '@/tw';
import type { User } from '@/types/user';

import { useGreeting } from '../hooks/use-greeting';

interface GreetingHeaderProps {
  user: User | null;
  onPressAvatar?: () => void;
}

export function GreetingHeader({ user, onPressAvatar }: GreetingHeaderProps) {
  const greeting = useGreeting();
  const displayName = user?.name ?? 'Farmer';
  const location =
    [user?.district, user?.state].filter(Boolean).join(', ') || 'Set your location';

  return (
    <Animated.View entering={FadeIn.duration(300)}>
      <View className="flex-row items-center justify-between gap-3">
        <View className="flex-1 gap-1">
          <SectionLabel>{greeting}</SectionLabel>
          <Text className="text-2xl font-bold tracking-tight text-text" numberOfLines={1}>
            {displayName}
          </Text>
          <View className="flex-row items-center gap-1.5">
            <Text className="text-sm">📍</Text>
            <Text className="flex-1 text-xs text-text-muted" numberOfLines={1}>
              {location}
            </Text>
          </View>
        </View>
        <PressableScale
          accessibilityRole="button"
          accessibilityLabel="Open profile"
          onPress={onPressAvatar}
          haptic="selection"
          pressedScale={0.92}
        >
          <Avatar name={user?.name} fallback="🌾" size="md" />
        </PressableScale>
      </View>
    </Animated.View>
  );
}
```

- [ ] **Step 2: Replace `outbreak-summary.tsx` with the hero card**

```tsx
import { router } from 'expo-router';

import { Card } from '@/components/ui/card';
import { Chip } from '@/components/ui/chip';
import { PressableScale } from '@/components/ui/pressable-scale';
import { SectionLabel } from '@/components/ui/section-label';
import { Skeleton } from '@/components/ui/skeleton';
import { Text, View } from '@/tw';

import type { DashboardSummary } from '../types';

interface OutbreakSummaryProps {
  summary?: DashboardSummary;
  loading?: boolean;
}

/**
 * The Home hero card. Big number = active outbreaks today within 5km, with
 * a stable/rising/falling pill, a "+N new" pill, and a context line.
 */
export function OutbreakSummary({ summary, loading }: OutbreakSummaryProps) {
  if (loading || !summary) {
    return <Skeleton height={140} rounded="xl" />;
  }

  const newCount = summary.reportsThisWeek ?? 0;
  const trend: { label: string; tone: 'success' | 'warning' | 'info' } =
    summary.activeOutbreaks <= 3
      ? { label: 'Stable', tone: 'success' }
      : summary.activeOutbreaks > 10
        ? { label: 'Rising', tone: 'warning' }
        : { label: 'Active', tone: 'info' };

  return (
    <PressableScale
      accessibilityRole="button"
      onPress={() => router.push('/map')}
      pressedScale={0.99}
      haptic="selection"
    >
      <Card variant="glow" padding="lg">
        <SectionLabel>Today · 5 km radius</SectionLabel>
        <View className="mt-2 flex-row items-end justify-between">
          <Text
            className="font-extrabold text-brand-900"
            style={{ fontSize: 44, lineHeight: 48, letterSpacing: -1.6 }}
          >
            {summary.activeOutbreaks}
          </Text>
          <View className="flex-row gap-2 pb-2">
            <Chip label={trend.label} tone={trend.tone} />
            {newCount > 0 ? <Chip label={`+${newCount} new`} tone="warning" /> : null}
          </View>
        </View>
        <Text className="mt-2 text-xs text-text-muted">
          {summary.highSeverityZones > 0
            ? `${summary.highSeverityZones} high-severity zones nearby`
            : 'No high-severity zones near you'}
        </Text>
      </Card>
    </PressableScale>
  );
}
```

- [ ] **Step 3: Replace `quick-upload-cta.tsx` with a single gradient CTA**

```tsx
import { router } from 'expo-router';
import { Camera } from 'lucide-react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { LinearGradient } from 'expo-linear-gradient';

import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

export function QuickUploadCTA() {
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel="Report a disease"
      onPress={() => router.push('/upload')}
      haptic="light"
      pressedScale={0.97}
      className="overflow-hidden rounded-2xl"
      style={{
        shadowColor: palette.brand[600],
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.32,
        shadowRadius: 16,
        elevation: 8,
      }}
    >
      <LinearGradient
        colors={[palette.brand[500], palette.brand[600]]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={{ position: 'absolute', inset: 0 }}
      />
      <View className="flex-row items-center justify-between gap-3 px-5 py-4">
        <View className="flex-1 gap-0.5">
          <Text className="text-base font-extrabold text-white">Report a disease</Text>
          <Text className="text-xs font-medium text-white/80">Camera + AI in 30s</Text>
        </View>
        <View className="h-11 w-11 items-center justify-center rounded-xl bg-white/20">
          <Camera size={22} color="#ffffff" strokeWidth={2.2} />
        </View>
      </View>
    </PressableScale>
  );
}
```

- [ ] **Step 4: Replace `recent-reports.tsx` with a 3-row vertical list**

```tsx
import { router } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { Pressable } from 'react-native';

import { Card } from '@/components/ui/card';
import { Chip } from '@/components/ui/chip';
import { Skeleton } from '@/components/ui/skeleton';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { timeAgo } from '@/utils/severity';

import type { Report } from '../types';

interface RecentReportsProps {
  reports?: Report[];
  loading?: boolean;
}

const SEVERITY_TONE: Record<string, 'success' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
};

export function RecentReports({ reports, loading }: RecentReportsProps) {
  if (loading || !reports) {
    return (
      <View className="gap-2">
        <View className="flex-row items-center justify-between px-1">
          <Text className="text-base font-bold text-text">Latest in your area</Text>
        </View>
        <Skeleton height={180} rounded="xl" />
      </View>
    );
  }

  const top = reports.slice(0, 3);

  return (
    <View className="gap-2">
      <View className="flex-row items-center justify-between px-1">
        <Text className="text-base font-bold tracking-tight text-text">
          Latest in your area
        </Text>
        <Pressable accessibilityRole="button" onPress={() => router.push('/notifications')}>
          <Text className="text-xs font-bold text-brand-700">View all</Text>
        </Pressable>
      </View>

      <Card padding="none">
        {top.length === 0 ? (
          <View className="px-4 py-6">
            <Text className="text-sm text-text-muted">No nearby reports yet.</Text>
          </View>
        ) : (
          top.map((r, i) => (
            <Pressable
              key={r.id}
              accessibilityRole="button"
              onPress={() => router.push({ pathname: '/reports/[id]', params: { id: r.id } })}
            >
              <View
                className={`flex-row items-center gap-3 px-4 py-3 ${
                  i > 0 ? 'border-t border-border' : ''
                }`}
              >
                <View className="h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
                  <Text className="text-lg">🌿</Text>
                </View>
                <View className="flex-1 gap-0.5">
                  <Text className="text-sm font-bold text-text" numberOfLines={1}>
                    {r.cropType} · {r.disease ?? 'Diagnosing…'}
                  </Text>
                  <Text className="text-xs text-text-subtle">{timeAgo(r.createdAt)}</Text>
                </View>
                {r.severity ? (
                  <Chip label={r.severity[0] + r.severity.slice(1).toLowerCase()} tone={SEVERITY_TONE[r.severity] ?? 'warning'} />
                ) : null}
                <ChevronRight size={16} color={palette.brand[700]} strokeWidth={2.2} />
              </View>
            </Pressable>
          ))
        )}
      </Card>
    </View>
  );
}
```

- [ ] **Step 5: Update `(app)/index.tsx` Home composition**

Replace the file with:

```tsx
import { router } from 'expo-router';
import { RefreshControl, ScrollView } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  GreetingHeader,
  OutbreakSummary,
  QuickUploadCTA,
  RecentReports,
} from '@/features/dashboard/components';
import { useDashboard } from '@/features/dashboard/hooks';
import { useTheme } from '@/hooks/use-theme';
import { useAuthStore } from '@/store/auth.store';
import { View } from '@/tw';

export default function HomeScreen() {
  const user = useAuthStore((s) => s.user);
  const theme = useTheme();
  const { data, isPending, isRefetching, refetch } = useDashboard();

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{
            paddingHorizontal: 16,
            paddingTop: 8,
            paddingBottom: 140,
            gap: 20,
          }}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor={theme.primary}
              colors={[theme.primary]}
            />
          }
        >
          <Animated.View entering={FadeInDown.duration(400)}>
            <GreetingHeader user={user} onPressAvatar={() => router.push('/profile')} />
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(80).duration(400)}>
            <OutbreakSummary summary={data?.summary} loading={isPending} />
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(160).duration(400)}>
            <QuickUploadCTA />
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(240).duration(400)}>
            <RecentReports reports={data?.recentReports} loading={isPending} />
          </Animated.View>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 6: Update `features/dashboard/components/index.ts`**

Remove exports for `DiseaseTrends` and `NearbyAlerts` from the Home barrel — they're no longer rendered on Home but the files themselves can stay in case they get reused later. Confirm only these are exported:

```ts
export * from './greeting-header';
export * from './outbreak-summary';
export * from './quick-upload-cta';
export * from './recent-reports';
```

- [ ] **Step 7: Run typecheck and verify on device**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile dev
```

Open Home and confirm: light off-white background, greeting + avatar at the top, single hero card with a big green number, gradient CTA, then a list of up to 3 reports.

- [ ] **Step 8: Commit**

```bash
git add apps/mobile/src/app/(app)/index.tsx apps/mobile/src/features/dashboard
git commit -m "feat(mobile): hero-first Home screen in Soft Sage"
```

---


## Task 6: Map screen — light theme + bottom-sheet pattern

**Files:**
- Modify: `apps/mobile/src/app/(app)/map.tsx`
- Modify: `apps/mobile/src/features/map-system/components/connection-pill.tsx`
- Modify: `apps/mobile/src/features/map-system/components/map-controls.tsx`
- Modify: `apps/mobile/src/features/map-system/components/map-marker.tsx`
- Modify: `apps/mobile/src/features/map-system/components/map-cluster.tsx`
- Modify: `apps/mobile/src/features/map-system/components/report-detail-sheet.tsx`
- Modify: `apps/mobile/src/features/map-system/components/map-filter-sheet.tsx`
- Modify: `apps/mobile/src/features/map-system/utils/map-style.ts`
- Create: `apps/mobile/src/features/map-system/components/map-search-bar.tsx`
- Create: `apps/mobile/src/features/map-system/components/map-filter-chips.tsx`
- Create: `apps/mobile/src/features/map-system/components/reports-in-view-sheet.tsx`
- Modify: `apps/mobile/src/features/map-system/components/index.ts`

- [ ] **Step 1: Read the current Map components before changing them**

Run:

```bash
ls apps/mobile/src/features/map-system/components
```

Open each file referenced in the imports of `apps/mobile/src/app/(app)/map.tsx` and skim it. Note the props of `ConnectionPill`, `MapControls`, `MapMarker`, `MapCluster`, `ReportDetailSheet`, and `MapFilterSheet` — they will be reused. Only their internal styling changes.

- [ ] **Step 2: Restyle `connection-pill.tsx`**

Replace its component body with a light pill that fits inside the search bar's left side. The component should accept `isConnected: boolean` and `reportCount: number` (existing API) and render:

```tsx
import { Wifi, WifiOff } from 'lucide-react-native';

import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

interface ConnectionPillProps {
  isConnected: boolean;
  reportCount: number;
}

export function ConnectionPill({ isConnected, reportCount }: ConnectionPillProps) {
  if (isConnected) {
    return (
      <View className="flex-row items-center gap-1.5 rounded-full bg-success-tint px-2.5 py-1">
        <View className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: palette.status.success }} />
        <Text className="text-[11px] font-bold text-success">Live · {reportCount}</Text>
      </View>
    );
  }
  return (
    <View className="flex-row items-center gap-1.5 rounded-full bg-warning-tint px-2.5 py-1">
      <WifiOff size={11} color={palette.status.warning} strokeWidth={2.2} />
      <Text className="text-[11px] font-bold text-warning">Offline</Text>
    </View>
  );
}
```

- [ ] **Step 3: Restyle `map-controls.tsx` to a vertical FAB stack**

The existing component already takes `layerMode`, `filtersActive`, `onLocate`, `onLayerToggle`, `onFilter`. Replace its return to render a vertical column of 38x38 white buttons with soft shadow:

```tsx
import { Layers, Locate, SlidersHorizontal } from 'lucide-react-native';

import { PressableScale } from '@/components/ui/pressable-scale';
import { View } from '@/tw';
import { palette } from '@/theme/colors';

interface MapControlsProps {
  layerMode: 'markers' | 'heatmap' | 'both';
  filtersActive: boolean;
  onLocate: () => void;
  onLayerToggle: () => void;
  onFilter: () => void;
}

const FabBtn = ({
  active,
  onPress,
  children,
}: {
  active?: boolean;
  onPress: () => void;
  children: React.ReactNode;
}) => (
  <PressableScale
    accessibilityRole="button"
    onPress={onPress}
    pressedScale={0.92}
    haptic="selection"
    className="h-10 w-10 items-center justify-center rounded-xl border border-border bg-surface"
    style={{
      shadowColor: '#0f172a',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.08,
      shadowRadius: 12,
      elevation: 4,
    }}
  >
    {children}
    {active ? (
      <View
        style={{
          position: 'absolute',
          top: 4,
          right: 4,
          width: 6,
          height: 6,
          borderRadius: 3,
          backgroundColor: palette.brand[600],
        }}
      />
    ) : null}
  </PressableScale>
);

export function MapControls({
  layerMode,
  filtersActive,
  onLocate,
  onLayerToggle,
  onFilter,
}: MapControlsProps) {
  const layerActive = layerMode !== 'markers';
  return (
    <View className="gap-2">
      <FabBtn onPress={onLocate}>
        <Locate size={18} color={palette.brand[700]} strokeWidth={2.2} />
      </FabBtn>
      <FabBtn active={layerActive} onPress={onLayerToggle}>
        <Layers size={18} color={layerActive ? palette.brand[600] : palette.brand[700]} strokeWidth={2.2} />
      </FabBtn>
      <FabBtn active={filtersActive} onPress={onFilter}>
        <SlidersHorizontal size={18} color={filtersActive ? palette.brand[600] : palette.brand[700]} strokeWidth={2.2} />
      </FabBtn>
    </View>
  );
}
```

- [ ] **Step 4: Update `map-marker.tsx` and `map-cluster.tsx` to use Soft Sage tokens**

Both components already accept `severity` / count props. Update internal colors to map severities to brand-tinted dots with white borders:

For `MapMarker` — replace the existing fill colors with:
- `LOW` → `palette.status.success` (#047857)
- `MEDIUM` → `palette.status.warning` (#92400e) — but for vibrancy on a light map, use `#d97706` instead. Add `const SEVERITY_FILL = { LOW: '#047857', MEDIUM: '#d97706', HIGH: '#dc2626' }` near the top of the file and use it.
- `HIGH` → `#dc2626`

Borders: 2px white. Pulse halo: same fill color at 30% opacity (existing logic, just colors swapped).

For `MapCluster` — the cluster bubble background should be the brand gradient when `highCount === 0` and a danger gradient (`#f97316 → #dc2626`) when `highCount > 0`. Number text stays white.

- [ ] **Step 5: Restyle `report-detail-sheet.tsx` and `map-filter-sheet.tsx`**

These use `@gorhom/bottom-sheet`. Update background and handle styles by passing:

```tsx
backgroundStyle={{ backgroundColor: '#ffffff', borderTopLeftRadius: 24, borderTopRightRadius: 24, borderWidth: 1, borderColor: '#efeae0', borderBottomWidth: 0 }}
handleIndicatorStyle={{ backgroundColor: '#e8e4dc', width: 36 }}
```

to both `BottomSheetModal` instances. Replace any internal text colors using `text-white` with `text-text` and `text-white/60` with `text-text-muted`.

- [ ] **Step 6: Replace `map-style.ts` darkMapStyle with a light style**

Rename the export from `darkMapStyle` to `lightMapStyle` and replace its contents with a Soft Sage map style. For Android (Google Maps):

```ts
/**
 * Light map style with off-white roads and muted greens.
 * Pulled from Snazzy Maps "Subtle Grayscale" base, tinted toward our palette.
 */
export const lightMapStyle = [
  { elementType: 'geometry', stylers: [{ color: '#fbfaf7' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#475569' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#fbfaf7' }] },
  { featureType: 'administrative.land_parcel', stylers: [{ visibility: 'off' }] },
  { featureType: 'landscape.natural', elementType: 'geometry', stylers: [{ color: '#eef3ec' }] },
  { featureType: 'poi', elementType: 'geometry', stylers: [{ color: '#eef3ec' }] },
  { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#64748b' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#dcebd9' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#ffffff' }] },
  { featureType: 'road.arterial', elementType: 'labels', stylers: [{ visibility: 'off' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#f3f1ea' }] },
  { featureType: 'road.local', stylers: [{ visibility: 'simplified' }] },
  { featureType: 'transit', stylers: [{ visibility: 'off' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#dceaf3' }] },
] as const;

/** Backwards-compat alias — some imports still reference darkMapStyle. */
export const darkMapStyle = lightMapStyle;
```

- [ ] **Step 7: Create `map-search-bar.tsx`**

```tsx
import { Search, SlidersHorizontal } from 'lucide-react-native';
import { Pressable } from 'react-native';

import { ConnectionPill } from '@/features/map-system/components/connection-pill';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

interface MapSearchBarProps {
  isConnected: boolean;
  reportCount: number;
  onPressSearch: () => void;
  onPressFilter: () => void;
}

export function MapSearchBar({
  isConnected,
  reportCount,
  onPressSearch,
  onPressFilter,
}: MapSearchBarProps) {
  return (
    <View className="flex-row items-center gap-2">
      <Pressable
        accessibilityRole="button"
        onPress={onPressSearch}
        className="flex-1 flex-row items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2.5"
        style={{
          shadowColor: '#0f172a',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.08,
          shadowRadius: 12,
          elevation: 4,
        }}
      >
        <Search size={16} color={palette.brand[700]} strokeWidth={2.2} />
        <Text className="flex-1 text-sm font-medium text-text-faint" numberOfLines={1}>
          Search area or crop…
        </Text>
        <ConnectionPill isConnected={isConnected} reportCount={reportCount} />
      </Pressable>
      <Pressable
        accessibilityRole="button"
        onPress={onPressFilter}
        className="h-11 w-11 items-center justify-center rounded-xl border border-border bg-surface"
        style={{
          shadowColor: '#0f172a',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.08,
          shadowRadius: 12,
          elevation: 4,
        }}
      >
        <SlidersHorizontal size={18} color={palette.brand[700]} strokeWidth={2.2} />
      </Pressable>
    </View>
  );
}
```

- [ ] **Step 8: Create `map-filter-chips.tsx`**

```tsx
import { ScrollView } from 'react-native';

import { Chip } from '@/components/ui/chip';
import { useMapFiltersStore } from '@/features/map-system/store/map-filters.store';
import { View } from '@/tw';

const SEVERITY_OPTIONS = [
  { value: 'LOW', label: 'Low' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HIGH', label: 'High' },
] as const;

const WINDOW_OPTIONS = [
  { value: '24h' as const, label: '24h' },
  { value: '7d' as const, label: '7d' },
  { value: '30d' as const, label: '30d' },
  { value: 'all' as const, label: 'All time' },
];

/**
 * Horizontal chip rail for the map's most-used filters. The full filter sheet
 * (severity + crop + disease + advanced) remains accessible via the gear icon.
 */
export function MapFilterChips() {
  const filters = useMapFiltersStore();

  const allActive =
    filters.severities.length === 0 &&
    filters.crops.length === 0 &&
    filters.diseases.length === 0 &&
    filters.window === 'all';

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={{ paddingHorizontal: 16, gap: 6 }}
    >
      <Chip
        label="All"
        active={allActive}
        onPress={() => filters.reset()}
      />
      {SEVERITY_OPTIONS.map((opt) => {
        const active = filters.severities.includes(opt.value);
        return (
          <Chip
            key={opt.value}
            label={opt.label}
            active={active}
            tone="warning"
            onPress={() => filters.toggleSeverity(opt.value)}
          />
        );
      })}
      <View className="w-px self-stretch bg-border" />
      {WINDOW_OPTIONS.map((opt) => (
        <Chip
          key={opt.value}
          label={opt.label}
          active={filters.window === opt.value}
          onPress={() => filters.setWindow(opt.value)}
        />
      ))}
    </ScrollView>
  );
}
```

If `useMapFiltersStore` does not expose `toggleSeverity` and `setWindow`, add thin wrappers there. Read `apps/mobile/src/features/map-system/store/map-filters.store.ts` first; the existing actions `setSeverities` and `setWindow` are likely sufficient — adapt the chip handlers accordingly:

```tsx
onPress={() => {
  const next = active
    ? filters.severities.filter((s) => s !== opt.value)
    : [...filters.severities, opt.value];
  filters.setSeverities(next);
}}
```

- [ ] **Step 9: Create `reports-in-view-sheet.tsx`**

```tsx
import BottomSheet, { BottomSheetFlatList, BottomSheetView } from '@gorhom/bottom-sheet';
import { router } from 'expo-router';
import { ChevronRight } from 'lucide-react-native';
import { forwardRef, useMemo } from 'react';
import { Pressable } from 'react-native';

import { Chip } from '@/components/ui/chip';
import { EmptyState } from '@/components/feedback';
import { Text, View } from '@/tw';
import type { Report } from '@/features/upload-report/types';
import { palette } from '@/theme/colors';
import { timeAgo } from '@/utils/severity';

interface Props {
  reports: Report[];
}

const SEVERITY_TONE: Record<string, 'success' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
};

/**
 * Persistent bottom sheet listing the reports currently visible on the map.
 * Snap points: 25%, 60%, 92%. Closing isn't allowed — it's a list view, not
 * a modal.
 */
export const ReportsInViewSheet = forwardRef<BottomSheet, Props>(function ReportsInViewSheet(
  { reports },
  ref,
) {
  const snapPoints = useMemo(() => ['25%', '60%', '92%'], []);

  return (
    <BottomSheet
      ref={ref}
      index={0}
      snapPoints={snapPoints}
      enablePanDownToClose={false}
      backgroundStyle={{
        backgroundColor: '#ffffff',
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
        borderColor: '#efeae0',
        borderWidth: 1,
        borderBottomWidth: 0,
      }}
      handleIndicatorStyle={{ backgroundColor: '#e8e4dc', width: 36 }}
    >
      <BottomSheetView style={{ paddingHorizontal: 16, paddingBottom: 8 }}>
        <View className="flex-row items-center justify-between">
          <Text className="text-base font-bold tracking-tight text-text">
            {reports.length} reports in view
          </Text>
          <Text className="text-xs text-text-subtle">Sort: newest</Text>
        </View>
      </BottomSheetView>

      {reports.length === 0 ? (
        <EmptyState
          emoji="🗺"
          title="No reports in view"
          description="Pan the map to see disease reports in another area."
        />
      ) : (
        <BottomSheetFlatList
          data={reports}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 32 }}
          ItemSeparatorComponent={() => <View className="h-2" />}
          renderItem={({ item }) => (
            <Pressable
              accessibilityRole="button"
              onPress={() => router.push({ pathname: '/reports/[id]', params: { id: item.id } })}
            >
              <View className="flex-row items-center gap-3 rounded-xl border border-border bg-surface px-3 py-3">
                <View className="h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
                  <Text className="text-lg">🌿</Text>
                </View>
                <View className="flex-1 gap-0.5">
                  <Text className="text-sm font-bold text-text" numberOfLines={1}>
                    {item.cropType} · {item.disease ?? 'Diagnosing…'}
                  </Text>
                  <Text className="text-xs text-text-subtle">{timeAgo(item.createdAt)}</Text>
                </View>
                {item.severity ? (
                  <Chip
                    label={item.severity[0] + item.severity.slice(1).toLowerCase()}
                    tone={SEVERITY_TONE[item.severity] ?? 'warning'}
                  />
                ) : null}
                <ChevronRight size={16} color={palette.brand[700]} strokeWidth={2.2} />
              </View>
            </Pressable>
          )}
        />
      )}
    </BottomSheet>
  );
});
```

- [ ] **Step 10: Update `(app)/map.tsx` to use the new components**

The existing screen has a lot of business logic (region tracking, clustering, socket subscription). Keep all of it. Only replace the *presentation* layer:

1. Remove the `colorScheme === 'dark'` branch on `customMapStyle`. Always pass `lightMapStyle` on Android.
2. Replace the top status pill block with `<MapSearchBar />`.
3. Add a row of `<MapFilterChips />` directly under the search bar.
4. Replace the dark "permission denied" banner styling with a light amber banner using `bg-warning-tint border border-warning-tint` and `text-warning`.
5. Add a persistent `<ReportsInViewSheet ref={listSheetRef} reports={filteredReports} />` mounted at the bottom of the screen.
6. Remove `useColorScheme` import (now unused).

The full new `map.tsx` is too long to inline here in one block — apply the changes via `Edit` calls, one per replacement.

After the edits, the top of the JSX tree should look approximately like:

```tsx
<SafeAreaView edges={['top']} pointerEvents="box-none" style={{ position: 'absolute', top: 0, left: 0, right: 0 }}>
  <View pointerEvents="box-none" className="gap-2 px-4 pt-2">
    <MapSearchBar
      isConnected={isConnected}
      reportCount={filteredReports.length}
      onPressSearch={() => filterSheetRef.current?.present()}
      onPressFilter={() => filterSheetRef.current?.present()}
    />
    <MapFilterChips />
  </View>
</SafeAreaView>
```

And at the bottom:

```tsx
<ReportsInViewSheet ref={listSheetRef} reports={filteredReports} />
```

(`listSheetRef` is `useRef<BottomSheet>(null)` — import `BottomSheet` from `@gorhom/bottom-sheet`.)

- [ ] **Step 11: Update `features/map-system/components/index.ts`**

Add:

```ts
export * from './map-search-bar';
export * from './map-filter-chips';
export * from './reports-in-view-sheet';
```

- [ ] **Step 12: Run typecheck and verify on device**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile dev
```

On the Map tab, confirm: light map style (Android), search bar + filter button at top, filter chip rail beneath, vertical FAB stack on the right, persistent sheet at the bottom listing reports.

- [ ] **Step 13: Commit**

```bash
git add apps/mobile/src/features/map-system apps/mobile/src/app/(app)/map.tsx
git commit -m "feat(mobile): light Map screen with search bar, filter chips, and reports sheet"
```

---


## Task 7: Report flow â€” Capture â†’ Analyzing â†’ Result â†’ Submitted

This is the most behaviorally significant change. The existing `(app)/upload.tsx` becomes a router that drives a four-step internal state machine. Most of the AI engine wiring is new and is documented inline.

**Files:**
- Modify: `apps/mobile/src/app/(app)/upload.tsx` (replaced with the state-machine shell)
- Create: `apps/mobile/src/features/report-flow/types.ts`
- Create: `apps/mobile/src/features/report-flow/use-report-flow.ts`
- Create: `apps/mobile/src/features/report-flow/screens/capture-screen.tsx`
- Create: `apps/mobile/src/features/report-flow/screens/analyzing-screen.tsx`
- Create: `apps/mobile/src/features/report-flow/screens/result-screen.tsx`
- Create: `apps/mobile/src/features/report-flow/screens/submitted-screen.tsx`
- Create: `apps/mobile/src/features/report-flow/components/engine-badge.tsx`
- Create: `apps/mobile/src/features/report-flow/components/recommendations-card.tsx`
- Create: `apps/mobile/src/features/report-flow/components/severity-pill.tsx`
- Create: `apps/mobile/src/features/report-flow/components/share-toggle-card.tsx`
- Create: `apps/mobile/src/features/report-flow/components/edit-details-sheet.tsx`
- Create: `apps/mobile/src/features/report-flow/index.ts`
- Read first: https://docs.expo.dev/versions/v56.0.0/sdk/imagepicker/ for Expo SDK 56 camera/picker behavior.

- [ ] **Step 1: Define the flow state types**

Create `apps/mobile/src/features/report-flow/types.ts`:

```ts
import type { Severity } from '@/features/upload-report/types';

export type FlowStep = 'capture' | 'analyzing' | 'result' | 'submitted';

export type AnalysisEngine = 'cloud' | 'on-device' | 'manual';

export interface AnalysisResult {
  engine: AnalysisEngine;
  /** Diagnosed disease (e.g., "Tomato leaf curl"). May be null in manual mode. */
  disease: string | null;
  /** 0..1 confidence from the engine. Null in manual mode. */
  confidence: number | null;
  severity: Severity | null;
  /** Treatment / action recommendations rendered as a numbered list. */
  recommendations: string[];
  /** Optional alternate candidates when confidence is low (<0.6). */
  candidates?: { disease: string; confidence: number }[];
  /** Free text from the engine (e.g., "Spreading", "Localized"). */
  status?: 'spreading' | 'localized' | 'contained';
  /** Set by the user via "Edit details". When true, badge becomes "Edited by you". */
  edited?: boolean;
}

export interface CapturedImage {
  uri: string;
  width: number;
  height: number;
}

export interface FlowLocation {
  latitude: number;
  longitude: number;
  accuracy?: number | null;
}

export interface FlowState {
  step: FlowStep;
  image: CapturedImage | null;
  cropType: string | null;
  notes: string;
  location: FlowLocation | null;
  result: AnalysisResult | null;
  /** When true, the report is submitted publicly to the outbreak map. */
  shareToMap: boolean;
  /** Diagnostic info on submission. */
  submittedReportId: string | null;
}

export const LOW_CONFIDENCE_THRESHOLD = 0.6;
```

- [ ] **Step 2: Create the flow controller hook**

Create `apps/mobile/src/features/report-flow/use-report-flow.ts`. This hook owns the entire flow state, the engine fallback chain, and the submit handoff to the existing `useCreateReport` mutation.

```ts
import { useCallback, useReducer } from 'react';

import { offlineAiClient } from '@/features/offline-ai';
import { useCreateReport } from '@/features/upload-report/hooks/use-create-report';
import { logger } from '@/utils/logger';

import {
  AnalysisEngine,
  AnalysisResult,
  CapturedImage,
  FlowLocation,
  FlowState,
  FlowStep,
} from './types';

type Action =
  | { type: 'SET_IMAGE'; image: CapturedImage; cropType: string | null }
  | { type: 'SET_STEP'; step: FlowStep }
  | { type: 'SET_RESULT'; result: AnalysisResult }
  | { type: 'PATCH_RESULT'; patch: Partial<AnalysisResult> }
  | { type: 'SET_LOCATION'; location: FlowLocation | null }
  | { type: 'SET_NOTES'; notes: string }
  | { type: 'SET_SHARE'; share: boolean }
  | { type: 'SET_SUBMITTED'; reportId: string }
  | { type: 'RESET' };

const initialState: FlowState = {
  step: 'capture',
  image: null,
  cropType: null,
  notes: '',
  location: null,
  result: null,
  shareToMap: true,
  submittedReportId: null,
};

function reducer(state: FlowState, action: Action): FlowState {
  switch (action.type) {
    case 'SET_IMAGE':
      return { ...state, image: action.image, cropType: action.cropType, step: 'analyzing' };
    case 'SET_STEP':
      return { ...state, step: action.step };
    case 'SET_RESULT':
      return { ...state, result: action.result, step: 'result' };
    case 'PATCH_RESULT':
      return state.result ? { ...state, result: { ...state.result, ...action.patch } } : state;
    case 'SET_LOCATION':
      return { ...state, location: action.location };
    case 'SET_NOTES':
      return { ...state, notes: action.notes };
    case 'SET_SHARE':
      return { ...state, shareToMap: action.share };
    case 'SET_SUBMITTED':
      return { ...state, step: 'submitted', submittedReportId: action.reportId };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

interface UseReportFlowOptions {
  cloudAnalyze: (image: CapturedImage, cropType: string | null) => Promise<AnalysisResult>;
}

const CLOUD_TIMEOUT_MS = 8000;

export function useReportFlow({ cloudAnalyze }: UseReportFlowOptions) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const create = useCreateReport();

  /**
   * Engine chain: cloud -> on-device -> manual. Each stage's failure is
   * logged and we move on. When all engines fail, transition to result in
   * manual mode (no badge, empty diagnosis fields).
   */
  const runAnalysis = useCallback(
    async (image: CapturedImage, cropType: string | null) => {
      const tryCloud = async (): Promise<AnalysisResult | null> => {
        try {
          const result = await Promise.race([
            cloudAnalyze(image, cropType),
            new Promise<never>((_, reject) =>
              setTimeout(() => reject(new Error('cloud-timeout')), CLOUD_TIMEOUT_MS),
            ),
          ]);
          return { ...result, engine: 'cloud' };
        } catch (err) {
          logger.warn('[report-flow] cloud analyze failed', err);
          return null;
        }
      };

      const tryOnDevice = async (): Promise<AnalysisResult | null> => {
        try {
          if (!(await offlineAiClient.isAvailable())) return null;
          const r = await offlineAiClient.analyze({
            localImageUri: image.uri,
            cropType: cropType ?? '',
          });
          if (!r.ok) return null;
          return {
            engine: 'on-device',
            disease: r.disease,
            confidence: r.confidence,
            severity: r.severity,
            recommendations: r.recommendations,
          };
        } catch (err) {
          logger.warn('[report-flow] on-device analyze failed', err);
          return null;
        }
      };

      const cloud = await tryCloud();
      if (cloud) {
        dispatch({ type: 'SET_RESULT', result: cloud });
        return;
      }
      const onDevice = await tryOnDevice();
      if (onDevice) {
        dispatch({ type: 'SET_RESULT', result: onDevice });
        return;
      }
      dispatch({
        type: 'SET_RESULT',
        result: {
          engine: 'manual',
          disease: null,
          confidence: null,
          severity: null,
          recommendations: [],
        },
      });
    },
    [cloudAnalyze],
  );

  const setImage = useCallback(
    (image: CapturedImage, cropType: string | null = null) => {
      dispatch({ type: 'SET_IMAGE', image, cropType });
      void runAnalysis(image, cropType);
    },
    [runAnalysis],
  );

  const submit = useCallback(async () => {
    if (!state.image || !state.location || !state.cropType || !state.result) return;
    const r = state.result;
    const reportId = await create.submit({
      picked: { uri: state.image.uri, width: state.image.width, height: state.image.height },
      cropTypeId: state.cropType,
      cropTypeName: state.cropType,
      notes: state.notes.trim() || undefined,
      location: state.location,
      diseaseHint: r.disease ?? undefined,
      severityHint: r.severity ?? undefined,
      shareToMap: state.shareToMap,
    } as Parameters<typeof create.submit>[0]);
    if (reportId) dispatch({ type: 'SET_SUBMITTED', reportId });
  }, [state, create]);

  return {
    state,
    setImage,
    setStep: (step: FlowStep) => dispatch({ type: 'SET_STEP', step }),
    setLocation: (location: FlowLocation | null) => dispatch({ type: 'SET_LOCATION', location }),
    setNotes: (notes: string) => dispatch({ type: 'SET_NOTES', notes }),
    setShare: (share: boolean) => dispatch({ type: 'SET_SHARE', share }),
    patchResult: (patch: Partial<AnalysisResult>) => dispatch({ type: 'PATCH_RESULT', patch }),
    submit,
    create,
    reset: () => dispatch({ type: 'RESET' }),
  };
}

export type UseReportFlow = ReturnType<typeof useReportFlow>;

export const ENGINE_COPY: Record<AnalysisEngine, { subtitle: string; badge: string }> = {
  cloud: {
    subtitle: 'Using our high-accuracy cloud modelâ€¦',
    badge: 'Cloud AI',
  },
  'on-device': {
    subtitle: 'Using on-device AI Â· works without internetâ€¦',
    badge: 'On-device AI',
  },
  manual: {
    subtitle: 'Fill in the details yourself.',
    badge: 'Edited by you',
  },
};
```

> **Implementation note:** if `useCreateReport().submit()` does not yet accept `diseaseHint`, `severityHint`, and `shareToMap`, extend its parameter type at `apps/mobile/src/features/upload-report/hooks/use-create-report.ts`. Add the three optional fields and pass them through in the request body.


- [ ] **Step 3: Stub the cloud analyze function**

Read `apps/mobile/src/features/disease-analysis/api/disease.api.ts` first. Add an `analyzeImage` function (or rename/wrap an existing one) that calls the FastAPI endpoint and maps the response into `AnalysisResult`. Endpoint contract per the spec:

```
POST /v1/diseases/analyze
{ imageUrl | imageBase64, cropType? }
-> { disease, confidence, severity, recommendations[], status?, candidates? }
```

Implementation:

```ts
import type { AnalysisResult } from '@/features/report-flow/types';
import { apiClient } from '@/services/api/client';

interface AnalyzeBody {
  imageBase64?: string;
  imageUrl?: string;
  cropType?: string;
}

export async function analyzeImage(args: AnalyzeBody): Promise<AnalysisResult> {
  const { data } = await apiClient.post('/v1/diseases/analyze', args);
  return {
    engine: 'cloud',
    disease: data.disease,
    confidence: data.confidence,
    severity: data.severity,
    recommendations: data.recommendations ?? [],
    status: data.status,
    candidates: data.candidates,
  };
}
```

If the name clashes, place this in `apps/mobile/src/features/disease-analysis/api/analyze-image.ts` and re-export it from the feature's `api/index.ts`.

- [ ] **Step 4: Build the engine badge component**

Create `apps/mobile/src/features/report-flow/components/engine-badge.tsx`:

```tsx
import { Cloud, Pencil, Smartphone } from 'lucide-react-native';

import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

import type { AnalysisEngine } from '../types';
import { ENGINE_COPY } from '../use-report-flow';

interface EngineBadgeProps {
  engine: AnalysisEngine;
  confidence?: number | null;
}

const ICONS = {
  cloud: Cloud,
  'on-device': Smartphone,
  manual: Pencil,
} as const;

export function EngineBadge({ engine, confidence }: EngineBadgeProps) {
  const Icon = ICONS[engine];
  const pct =
    confidence !== null && confidence !== undefined
      ? `${Math.round(confidence * 100)}%`
      : null;

  return (
    <View
      className="flex-row items-center gap-1 self-start rounded-full border border-brand-100 bg-brand-50 px-2.5 py-1"
    >
      <Icon size={11} color={palette.brand[700]} strokeWidth={2.4} />
      <Text className="text-[11px] font-bold text-brand-700">
        {ENGINE_COPY[engine].badge}
        {pct ? ` Â· ${pct}` : ''}
      </Text>
    </View>
  );
}
```

- [ ] **Step 5: Build the severity pill, recommendations card, and share toggle**

Create `apps/mobile/src/features/report-flow/components/severity-pill.tsx`:

```tsx
import { Chip } from '@/components/ui/chip';
import type { Severity } from '@/features/upload-report/types';

const TONE: Record<Severity, 'success' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
};

const LABEL: Record<Severity, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};

export function SeverityPill({ severity }: { severity: Severity }) {
  return <Chip label={`Severity: ${LABEL[severity]}`} tone={TONE[severity]} />;
}
```

Create `apps/mobile/src/features/report-flow/components/recommendations-card.tsx`:

```tsx
import { Card } from '@/components/ui/card';
import { SectionLabel } from '@/components/ui/section-label';
import { Text, View } from '@/tw';

interface RecommendationsCardProps {
  items: string[];
  emphasized?: boolean;
}

export function RecommendationsCard({ items, emphasized = true }: RecommendationsCardProps) {
  if (!items.length) return null;
  return (
    <Card variant={emphasized ? 'glow' : 'flat'} padding="md">
      <SectionLabel>Recommended actions</SectionLabel>
      <View className="mt-2 gap-2">
        {items.slice(0, 5).map((item, i) => (
          <View key={`${i}-${item.slice(0, 20)}`} className="flex-row items-start gap-2.5">
            <View className="mt-0.5 h-5 w-5 items-center justify-center rounded-full bg-success-tint">
              <Text className="text-[10px] font-bold text-success">{i + 1}</Text>
            </View>
            <Text className="flex-1 text-sm leading-5 text-text">{item}</Text>
          </View>
        ))}
      </View>
    </Card>
  );
}
```

Create `apps/mobile/src/features/report-flow/components/share-toggle-card.tsx`:

```tsx
import { Switch } from 'react-native';

import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

interface ShareToggleCardProps {
  value: boolean;
  onChange: (next: boolean) => void;
}

export function ShareToggleCard({ value, onChange }: ShareToggleCardProps) {
  return (
    <View className="flex-row items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3">
      <View className="flex-1 gap-0.5">
        <Text className="text-sm font-bold text-text">Add to outbreak map</Text>
        <Text className="text-xs text-text-muted">Helps nearby farmers act early.</Text>
      </View>
      <Switch
        value={value}
        onValueChange={onChange}
        trackColor={{ false: '#e8e4dc', true: palette.brand[500] }}
        thumbColor="#ffffff"
      />
    </View>
  );
}
```


- [ ] **Step 6: Build the Capture screen**

Create `apps/mobile/src/features/report-flow/screens/capture-screen.tsx`. Per `apps/mobile/AGENTS.md`, confirm the SDK 56 ImagePicker API at https://docs.expo.dev/versions/v56.0.0/sdk/imagepicker/ before writing this. The API stable points are `launchCameraAsync` and `launchImageLibraryAsync` returning `{ canceled, assets }`.

```tsx
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { Image as ImageIcon, X, Zap } from 'lucide-react-native';
import { Pressable } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PressableScale } from '@/components/ui/pressable-scale';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

import type { CapturedImage } from '../types';

interface Props {
  onCaptured: (image: CapturedImage) => void;
  onCancel: () => void;
}

const PICKER_OPTIONS: ImagePicker.ImagePickerOptions = {
  mediaTypes: ImagePicker.MediaTypeOptions.Images,
  allowsEditing: true,
  aspect: [1, 1],
  quality: 0.85,
};

export function CaptureScreen({ onCaptured, onCancel }: Props) {
  const launch = async (mode: 'camera' | 'library') => {
    const result =
      mode === 'camera'
        ? await ImagePicker.launchCameraAsync(PICKER_OPTIONS)
        : await ImagePicker.launchImageLibraryAsync(PICKER_OPTIONS);
    if (result.canceled || !result.assets[0]) return;
    const a = result.assets[0];
    onCaptured({ uri: a.uri, width: a.width, height: a.height });
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top', 'bottom']} style={{ flex: 1 }}>
        <View className="flex-row items-center justify-between px-4 py-2">
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Close"
            onPress={() => {
              onCancel();
              router.back();
            }}
            className="h-10 w-10 items-center justify-center rounded-full border border-border bg-surface"
          >
            <X size={18} color={palette.brand[700]} strokeWidth={2.2} />
          </Pressable>
          <Text className="text-xs font-bold uppercase tracking-[1.4px] text-brand-700">
            Step 1 of 4
          </Text>
          <View className="h-10 w-10" />
        </View>

        <Animated.View
          entering={FadeIn.duration(300)}
          className="mx-4 mb-4 flex-1 items-center justify-center overflow-hidden rounded-3xl border border-border bg-surface"
        >
          <View className="items-center gap-3 px-8">
            <View className="h-20 w-20 items-center justify-center rounded-3xl bg-brand-50">
              <ImageIcon size={36} color={palette.brand[600]} strokeWidth={2} />
            </View>
            <Text className="text-lg font-bold text-text">Take a photo</Text>
            <Text className="text-center text-sm text-text-muted">
              Frame the affected leaf so it fills the square. Natural light works best.
            </Text>
          </View>
        </Animated.View>

        <View className="flex-row items-center justify-around px-4 pb-2">
          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Choose from gallery"
            onPress={() => void launch('library')}
            haptic="selection"
            className="h-12 w-12 items-center justify-center rounded-full border border-border bg-surface"
          >
            <ImageIcon size={20} color={palette.brand[700]} strokeWidth={2.2} />
          </PressableScale>

          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Capture photo"
            onPress={() => void launch('camera')}
            haptic="medium"
            pressedScale={0.92}
            className="h-20 w-20 items-center justify-center overflow-hidden rounded-full border-[4px] border-surface"
            style={{
              shadowColor: palette.brand[600],
              shadowOffset: { width: 0, height: 10 },
              shadowOpacity: 0.45,
              shadowRadius: 16,
              elevation: 12,
            }}
          >
            <View
              style={{ position: 'absolute', inset: 0, backgroundColor: palette.brand[600] }}
            />
          </PressableScale>

          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Tips"
            onPress={() => undefined}
            haptic="selection"
            className="h-12 w-12 items-center justify-center rounded-full border border-border bg-surface"
          >
            <Zap size={20} color={palette.brand[700]} strokeWidth={2.2} />
          </PressableScale>
        </View>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 7: Build the Analyzing screen**

Create `apps/mobile/src/features/report-flow/screens/analyzing-screen.tsx`. The screen optimistically shows the cloud copy. If the cloud fails and on-device runs, the result arrives within ~2s and the screen flips to result, so a single subtitle is acceptable.

```tsx
import { Image } from 'expo-image';
import Animated, { FadeIn } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '@/components/ui/card';
import { Loader } from '@/components/ui/loader';
import { Text, View } from '@/tw';

import type { CapturedImage } from '../types';

interface Props {
  image: CapturedImage;
}

export function AnalyzingScreen({ image }: Props) {
  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top', 'bottom']} style={{ flex: 1 }}>
        <View className="flex-row items-center justify-center px-4 py-2">
          <Text className="text-xs font-bold uppercase tracking-[1.4px] text-brand-700">
            Step 2 of 4
          </Text>
        </View>

        <View className="flex-1 items-center justify-center gap-5 px-6">
          <Animated.View
            entering={FadeIn.duration(300)}
            className="overflow-hidden rounded-2xl border border-border"
          >
            <Image
              source={{ uri: image.uri }}
              style={{ width: 140, height: 140 }}
              contentFit="cover"
            />
          </Animated.View>
          <Loader size={56} />
          <View className="items-center gap-1">
            <Text className="text-base font-bold text-text">Analyzing your photo</Text>
            <Text className="text-center text-sm text-text-muted">
              Using our high-accuracy cloud modelâ€¦
            </Text>
          </View>
          <Card padding="sm" className="self-stretch">
            <View className="gap-1">
              <Text className="text-xs text-text-muted">âœ“ Image quality good</Text>
              <Text className="text-xs text-text-muted">âœ“ Leaf detected</Text>
              <Text className="text-xs text-text-muted">â— Identifying diseaseâ€¦</Text>
            </View>
          </Card>
        </View>
      </SafeAreaView>
    </View>
  );
}
```


- [ ] **Step 8: Build the Result screen**

Create `apps/mobile/src/features/report-flow/screens/result-screen.tsx`. This bundles diagnosis hero + severity + engine badge + recommendations + edit link + share toggle + Confirm button. If `result.candidates` exists and confidence < 0.6, render the candidate-picker variant instead.

```tsx
import { Image } from 'expo-image';
import { Pencil } from 'lucide-react-native';
import { Pressable, ScrollView } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { Chip } from '@/components/ui/chip';
import { SectionLabel } from '@/components/ui/section-label';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

import { EngineBadge } from '../components/engine-badge';
import { RecommendationsCard } from '../components/recommendations-card';
import { SeverityPill } from '../components/severity-pill';
import { ShareToggleCard } from '../components/share-toggle-card';
import { LOW_CONFIDENCE_THRESHOLD } from '../types';
import type { AnalysisResult, CapturedImage } from '../types';

interface Props {
  image: CapturedImage;
  result: AnalysisResult;
  shareToMap: boolean;
  submitting: boolean;
  onShareChange: (next: boolean) => void;
  onEdit: () => void;
  onPickCandidate: (disease: string) => void;
  onConfirm: () => void;
}

export function ResultScreen({
  image,
  result,
  shareToMap,
  submitting,
  onShareChange,
  onEdit,
  onPickCandidate,
  onConfirm,
}: Props) {
  const lowConfidence =
    result.candidates &&
    result.candidates.length > 0 &&
    result.confidence !== null &&
    result.confidence < LOW_CONFIDENCE_THRESHOLD;

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <View className="flex-row items-center justify-center px-4 py-2">
          <Text className="text-xs font-bold uppercase tracking-[1.4px] text-brand-700">
            Step 3 of 4
          </Text>
        </View>

        <ScrollView
          contentContainerStyle={{ padding: 16, paddingBottom: 32, gap: 16 }}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View
            entering={FadeInDown.duration(300)}
            className="flex-row items-center gap-3"
          >
            <Image
              source={{ uri: image.uri }}
              style={{ width: 64, height: 64, borderRadius: 12 }}
              contentFit="cover"
            />
            <View className="flex-1 gap-1">
              <Text className="text-lg font-extrabold tracking-tight text-text">
                {lowConfidence ? 'Pick the closest match' : result.disease ?? 'Manual entry'}
              </Text>
              {result.engine !== 'manual' && result.confidence !== null ? (
                <Text className="text-xs text-text-subtle">
                  {result.engine === 'cloud' ? 'Cloud diagnosis' : 'On-device diagnosis'} Â·{' '}
                  {Math.round(result.confidence * 100)}% match
                </Text>
              ) : null}
            </View>
          </Animated.View>

          <View className="flex-row flex-wrap gap-2">
            {result.severity ? <SeverityPill severity={result.severity} /> : null}
            {result.status ? (
              <Chip
                label={result.status[0].toUpperCase() + result.status.slice(1)}
                tone="brand"
              />
            ) : null}
            <EngineBadge engine={result.engine} confidence={result.confidence ?? undefined} />
          </View>

          {lowConfidence ? (
            <View className="gap-2">
              <SectionLabel>Possible matches</SectionLabel>
              {result.candidates!.map((c) => (
                <Pressable
                  key={c.disease}
                  accessibilityRole="button"
                  onPress={() => onPickCandidate(c.disease)}
                  className="flex-row items-center justify-between rounded-xl border border-border bg-surface px-4 py-3"
                >
                  <Text className="flex-1 text-sm font-bold text-text">{c.disease}</Text>
                  <Text className="text-xs font-bold text-brand-700">
                    {Math.round(c.confidence * 100)}%
                  </Text>
                </Pressable>
              ))}
            </View>
          ) : (
            <RecommendationsCard items={result.recommendations} />
          )}

          <Pressable
            accessibilityRole="button"
            onPress={onEdit}
            className="flex-row items-center gap-2 self-start rounded-full border border-border bg-surface px-3 py-2"
          >
            <Pencil size={12} color={palette.brand[700]} strokeWidth={2.4} />
            <Text className="text-xs font-bold text-brand-700">
              Wrong diagnosis? Edit details
            </Text>
          </Pressable>

          <ShareToggleCard value={shareToMap} onChange={onShareChange} />
        </ScrollView>

        <View className="border-t border-border bg-surface px-4 py-3">
          <Button
            label={submitting ? 'Submittingâ€¦' : 'Confirm & submit'}
            variant="gradient"
            size="lg"
            loading={submitting}
            onPress={onConfirm}
          />
        </View>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 9: Build the Submitted screen**

Create `apps/mobile/src/features/report-flow/screens/submitted-screen.tsx`:

```tsx
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { Check } from 'lucide-react-native';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

import { SeverityPill } from '../components/severity-pill';
import type { AnalysisResult } from '../types';

interface Props {
  result: AnalysisResult;
  cropType: string | null;
  shareToMap: boolean;
  reportId: string | null;
  onAnother: () => void;
}

export function SubmittedScreen({ result, cropType, shareToMap, reportId, onAnother }: Props) {
  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top', 'bottom']} style={{ flex: 1 }}>
        <View className="flex-1 items-center justify-center gap-5 px-6">
          <Animated.View entering={FadeIn.duration(400)}>
            <View
              className="h-20 w-20 items-center justify-center overflow-hidden rounded-full"
              style={{
                shadowColor: palette.brand[600],
                shadowOffset: { width: 0, height: 12 },
                shadowOpacity: 0.4,
                shadowRadius: 18,
                elevation: 10,
              }}
            >
              <LinearGradient
                colors={[palette.brand[500], palette.brand[600]]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={{ position: 'absolute', inset: 0 }}
              />
              <Check size={36} color="#ffffff" strokeWidth={2.6} />
            </View>
          </Animated.View>

          <Animated.View
            entering={FadeInDown.delay(100).duration(400)}
            className="items-center gap-1"
          >
            <Text className="text-2xl font-extrabold tracking-tight text-text">Submitted</Text>
            <Text className="text-center text-sm text-text-muted">
              {shareToMap
                ? 'Visible to nearby agronomists and farmers.'
                : 'Saved to your history. Not added to the public map.'}
            </Text>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(180).duration(400)} className="self-stretch">
            <Card padding="md">
              <View className="flex-row flex-wrap items-center gap-2">
                {result.severity ? <SeverityPill severity={result.severity} /> : null}
                <Text className="text-sm font-bold text-text">
                  {cropType ?? 'â€”'} Â· {result.disease ?? 'Manual entry'}
                </Text>
              </View>
              <Text className="mt-1 text-xs text-text-subtle">just now</Text>
            </Card>
          </Animated.View>
        </View>

        <View className="gap-2 px-4 pb-4">
          <Button label="View on map" variant="ghost" onPress={() => router.replace('/map')} />
          <Button
            label={reportId ? 'View this report' : 'Report another'}
            variant="gradient"
            onPress={() =>
              reportId
                ? router.replace({ pathname: '/reports/[id]', params: { id: reportId } })
                : onAnother()
            }
          />
        </View>
      </SafeAreaView>
    </View>
  );
}
```


- [ ] **Step 10: Wire the screens in `(app)/upload.tsx`**

Replace `apps/mobile/src/app/(app)/upload.tsx` with the state-machine shell:

```tsx
import { router } from 'expo-router';
import { useEffect, useRef } from 'react';

import { analyzeImage } from '@/features/disease-analysis/api';
import {
  AnalyzingScreen,
  CaptureScreen,
  EditDetailsSheet,
  ResultScreen,
  SubmittedScreen,
} from '@/features/report-flow';
import type { EditDetailsSheetHandle } from '@/features/report-flow/components/edit-details-sheet';
import { useReportFlow } from '@/features/report-flow/use-report-flow';
import { useCurrentLocation } from '@/features/upload-report/hooks';
import { View } from '@/tw';

export default function UploadScreen() {
  const flow = useReportFlow({
    cloudAnalyze: (image, cropType) =>
      analyzeImage({ imageUrl: image.uri, cropType: cropType ?? undefined }),
  });

  const editSheetRef = useRef<EditDetailsSheetHandle>(null);

  const locationCtl = useCurrentLocation(true);
  useEffect(() => {
    if (locationCtl.location) flow.setLocation(locationCtl.location);
  }, [locationCtl.location, flow]);

  const submitting =
    flow.create.state === 'uploading' || flow.create.state === 'compressing';

  let body: React.ReactNode = null;
  switch (flow.state.step) {
    case 'capture':
      body = <CaptureScreen onCaptured={flow.setImage} onCancel={flow.reset} />;
      break;
    case 'analyzing':
      body = flow.state.image ? <AnalyzingScreen image={flow.state.image} /> : <View />;
      break;
    case 'result':
      body =
        flow.state.image && flow.state.result ? (
          <ResultScreen
            image={flow.state.image}
            result={flow.state.result}
            shareToMap={flow.state.shareToMap}
            submitting={submitting}
            onShareChange={flow.setShare}
            onEdit={() => editSheetRef.current?.present()}
            onPickCandidate={(disease) =>
              flow.patchResult({ disease, candidates: undefined, confidence: 1 })
            }
            onConfirm={() => void flow.submit()}
          />
        ) : (
          <View />
        );
      break;
    case 'submitted':
      body = flow.state.result ? (
        <SubmittedScreen
          result={flow.state.result}
          cropType={flow.state.cropType}
          shareToMap={flow.state.shareToMap}
          reportId={flow.state.submittedReportId}
          onAnother={() => {
            flow.reset();
            router.replace('/upload');
          }}
        />
      ) : (
        <View />
      );
      break;
  }

  return (
    <>
      {body}
      {flow.state.result ? (
        <EditDetailsSheet
          ref={editSheetRef}
          initial={flow.state.result}
          onSave={flow.patchResult}
        />
      ) : null}
    </>
  );
}
```

- [ ] **Step 11: Build the edit-details sheet**

Create `apps/mobile/src/features/report-flow/components/edit-details-sheet.tsx`:

```tsx
import { BottomSheetModal, BottomSheetView } from '@gorhom/bottom-sheet';
import { forwardRef, useImperativeHandle, useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Chip } from '@/components/ui/chip';
import { Input } from '@/components/ui/input';
import { SectionLabel } from '@/components/ui/section-label';
import { Text, View } from '@/tw';
import type { Severity } from '@/features/upload-report/types';

import type { AnalysisResult } from '../types';

interface Props {
  initial: AnalysisResult;
  onSave: (patch: Partial<AnalysisResult>) => void;
}

export interface EditDetailsSheetHandle {
  present: () => void;
  dismiss: () => void;
}

const SEVERITIES: Severity[] = ['LOW', 'MEDIUM', 'HIGH'];
const TONE: Record<Severity, 'success' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
};

export const EditDetailsSheet = forwardRef<EditDetailsSheetHandle, Props>(
  function EditDetailsSheet({ initial, onSave }, ref) {
    const sheetRef = useRef<BottomSheetModal>(null);
    const [disease, setDisease] = useState(initial.disease ?? '');
    const [severity, setSeverity] = useState<Severity | null>(initial.severity);

    useImperativeHandle(ref, () => ({
      present: () => sheetRef.current?.present(),
      dismiss: () => sheetRef.current?.dismiss(),
    }));

    return (
      <BottomSheetModal
        ref={sheetRef}
        snapPoints={['62%']}
        backgroundStyle={{
          backgroundColor: '#ffffff',
          borderTopLeftRadius: 24,
          borderTopRightRadius: 24,
        }}
        handleIndicatorStyle={{ backgroundColor: '#e8e4dc', width: 36 }}
      >
        <BottomSheetView style={{ paddingHorizontal: 16, paddingBottom: 24, gap: 12 }}>
          <Text className="text-lg font-bold text-text">Edit details</Text>
          <Input
            label="Disease"
            value={disease}
            onChangeText={setDisease}
            placeholder="e.g. Tomato leaf curl"
          />
          <View>
            <SectionLabel>Severity</SectionLabel>
            <View className="mt-2 flex-row gap-2">
              {SEVERITIES.map((s) => (
                <Chip
                  key={s}
                  label={s[0] + s.slice(1).toLowerCase()}
                  active={severity === s}
                  onPress={() => setSeverity(s)}
                  tone={TONE[s]}
                />
              ))}
            </View>
          </View>
          <Button
            label="Save changes"
            variant="gradient"
            onPress={() => {
              onSave({ disease: disease || null, severity, edited: true });
              sheetRef.current?.dismiss();
            }}
          />
        </BottomSheetView>
      </BottomSheetModal>
    );
  },
);
```

- [ ] **Step 12: Create `features/report-flow/index.ts` barrel**

```ts
export * from './screens/capture-screen';
export * from './screens/analyzing-screen';
export * from './screens/result-screen';
export * from './screens/submitted-screen';
export * from './components/engine-badge';
export * from './components/recommendations-card';
export * from './components/severity-pill';
export * from './components/share-toggle-card';
export * from './components/edit-details-sheet';
export * from './use-report-flow';
export * from './types';
```

- [ ] **Step 13: Run typecheck and walk the flow on device**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile dev
```

End-to-end test (FastAPI service still down):
1. Tap the Report FAB â†’ CaptureScreen renders.
2. Tap shutter or library â†’ analyzing renders for ~8s (cloud timeout) then drops to manual mode (no badge).
3. ResultScreen lets you tap "Edit details" to fill in disease + severity, toggle map share, then Confirm.
4. Submitted screen renders, "View this report" navigates to `reports/[id]`.

Then with the FastAPI service mocked to return a valid response (or temporarily hardcode `cloudAnalyze` to resolve immediately): confirm cloud badge appears, recommendations render, low-confidence path shows candidates.

- [ ] **Step 14: Commit**

```bash
git add apps/mobile/src/features/report-flow apps/mobile/src/app/(app)/upload.tsx apps/mobile/src/features/disease-analysis/api
git commit -m "feat(mobile): four-step report flow with cloud/on-device/manual fallback"
```

---



## Task 8: Notifications screen

**Files:**
- Modify: `apps/mobile/src/app/(app)/notifications.tsx`
- Modify: `apps/mobile/src/features/notifications/components/notification-card.tsx`
- Modify: `apps/mobile/src/features/notifications/components/notification-filter.tsx`
- Modify: `apps/mobile/src/features/notifications/components/notification-badge.tsx`
- Create: `apps/mobile/src/features/notifications/components/day-label.tsx`
- Modify: `apps/mobile/src/features/notifications/components/index.ts`
- Create: `apps/mobile/src/features/notifications/utils/group-by-day.ts`

- [ ] **Step 1: Create the day-grouping helper**

Create `apps/mobile/src/features/notifications/utils/group-by-day.ts`:

```ts
import type { Notification } from '../api/notifications.api';

export type DayBucket = 'today' | 'yesterday' | 'this-week' | 'earlier';

export interface NotificationGroup {
  bucket: DayBucket;
  label: string;
  items: Notification[];
}

const DAY_MS = 24 * 60 * 60 * 1000;

function bucketOf(createdAtIso: string): DayBucket {
  const createdAt = new Date(createdAtIso).getTime();
  const now = Date.now();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStart = today.getTime();
  if (createdAt >= todayStart) return 'today';
  if (createdAt >= todayStart - DAY_MS) return 'yesterday';
  if (createdAt >= now - 7 * DAY_MS) return 'this-week';
  return 'earlier';
}

const LABELS: Record<DayBucket, string> = {
  today: 'Today',
  yesterday: 'Yesterday',
  'this-week': 'This week',
  earlier: 'Earlier',
};

const ORDER: DayBucket[] = ['today', 'yesterday', 'this-week', 'earlier'];

/**
 * Bucket notifications into Today / Yesterday / This week / Earlier so the
 * list reads as a timeline. Empty buckets are dropped.
 */
export function groupByDay(items: Notification[]): NotificationGroup[] {
  const map: Record<DayBucket, Notification[]> = {
    today: [],
    yesterday: [],
    'this-week': [],
    earlier: [],
  };
  for (const item of items) {
    map[bucketOf(item.createdAt)].push(item);
  }
  return ORDER
    .filter((b) => map[b].length > 0)
    .map((b) => ({ bucket: b, label: LABELS[b], items: map[b] }));
}
```

- [ ] **Step 2: Create the day label component**

Create `apps/mobile/src/features/notifications/components/day-label.tsx`:

```tsx
import { SectionLabel } from '@/components/ui/section-label';
import { View } from '@/tw';

export function DayLabel({ children }: { children: string }) {
  return (
    <View className="px-1 pb-1 pt-3">
      <SectionLabel>{children}</SectionLabel>
    </View>
  );
}
```

- [ ] **Step 3: Restyle `notification-card.tsx`**

Replace the file with the Soft Sage variants (critical / confirmation / system):

```tsx
import { CheckCircle2, Layers, TriangleAlert } from 'lucide-react-native';
import { Pressable } from 'react-native';

import { Chip } from '@/components/ui/chip';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';
import { cn } from '@/utils/cn';
import { timeAgo } from '@/utils/severity';

import type { Notification } from '../api/notifications.api';

interface Props {
  notification: Notification;
  onPress: (n: Notification) => void;
}

const ICON_BY_TYPE = {
  OUTBREAK_NEAR: { Icon: TriangleAlert, tint: palette.status.danger, bg: '#fee2e2' },
  REPORT_CONFIRMED: { Icon: CheckCircle2, tint: palette.status.success, bg: '#ecfdf5' },
  SYSTEM: { Icon: Layers, tint: palette.status.warning, bg: '#fef3c7' },
} as const;

function pickIcon(type: string) {
  return (ICON_BY_TYPE as Record<string, (typeof ICON_BY_TYPE)[keyof typeof ICON_BY_TYPE]>)[type] ?? ICON_BY_TYPE.SYSTEM;
}

export function NotificationCard({ notification, onPress }: Props) {
  const { Icon, tint, bg } = pickIcon(notification.type);
  const isCritical = notification.type === 'OUTBREAK_NEAR';
  const unread = !notification.read;

  return (
    <Pressable accessibilityRole="button" onPress={() => onPress(notification)}>
      <View
        className={cn(
          'flex-row items-start gap-3 rounded-xl border bg-surface p-3',
          unread ? 'border-brand-100' : 'border-border',
        )}
        style={{
          borderLeftWidth: isCritical ? 3 : 1,
          borderLeftColor: isCritical ? palette.status.danger : undefined,
        }}
      >
        <View
          className="h-10 w-10 items-center justify-center rounded-xl"
          style={{ backgroundColor: bg }}
        >
          <Icon size={18} color={tint} strokeWidth={2.2} />
        </View>
        <View className="flex-1 gap-0.5">
          <Text className="text-sm font-bold text-text" numberOfLines={2}>
            {notification.title}
          </Text>
          {notification.body ? (
            <Text className="text-xs text-text-muted" numberOfLines={2}>
              {notification.body}
            </Text>
          ) : null}
          <Text className="mt-1 text-[11px] text-text-subtle">
            {timeAgo(notification.createdAt)}
          </Text>
        </View>
        {isCritical ? <Chip label="High" tone="danger" /> : null}
        {unread ? (
          <View
            style={{
              width: 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: palette.brand[600],
              marginTop: 6,
            }}
          />
        ) : null}
      </View>
    </Pressable>
  );
}
```

- [ ] **Step 4: Restyle `notification-filter.tsx`**

The component already exposes `value` + `onChange` props with values `'all' | 'unread' | NotificationType`. Replace its body with horizontal `Chip` buttons:

```tsx
import { ScrollView } from 'react-native';

import { Chip } from '@/components/ui/chip';

export type NotificationFilterValue =
  | 'all'
  | 'unread'
  | 'OUTBREAK_NEAR'
  | 'REPORT_CONFIRMED'
  | 'SYSTEM';

interface Props {
  value: NotificationFilterValue;
  onChange: (next: NotificationFilterValue) => void;
}

const OPTIONS: { value: NotificationFilterValue; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'unread', label: 'Unread' },
  { value: 'OUTBREAK_NEAR', label: 'Outbreaks' },
  { value: 'REPORT_CONFIRMED', label: 'Confirmations' },
  { value: 'SYSTEM', label: 'System' },
];

export function NotificationFilter({ value, onChange }: Props) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={{ gap: 6 }}
    >
      {OPTIONS.map((opt) => (
        <Chip
          key={opt.value}
          label={opt.label}
          active={value === opt.value}
          onPress={() => onChange(opt.value)}
        />
      ))}
    </ScrollView>
  );
}
```

- [ ] **Step 5: Restyle `notification-badge.tsx` for light theme**

Open the file and update the background to `palette.brand[600]` and the text color to white. Keep the API (`count: number`, `size?: 'sm' | 'md'`) identical so the tab-bar import still works.

- [ ] **Step 6: Update `notifications/components/index.ts`**

Add:

```ts
export * from './day-label';
```

- [ ] **Step 7: Replace `(app)/notifications.tsx`**

```tsx
import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { RefreshControl, ScrollView } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { EmptyState } from '@/components/feedback';
import { Loader } from '@/components/ui/loader';
import { PressableScale } from '@/components/ui/pressable-scale';
import {
  DayLabel,
  type NotificationFilterValue,
  NotificationCard,
  NotificationFilter,
} from '@/features/notifications/components';
import {
  useDeleteNotification,
  useMarkAllRead,
  useMarkNotificationRead,
  useNotifications,
} from '@/features/notifications/hooks';
import type { Notification, NotificationType } from '@/features/notifications/api/notifications.api';
import { useNotificationsStore } from '@/features/notifications/store/notifications.store';
import { groupByDay } from '@/features/notifications/utils/group-by-day';
import { useTheme } from '@/hooks/use-theme';
import { Text, View } from '@/tw';

export default function NotificationsScreen() {
  const theme = useTheme();
  const [filter, setFilter] = useState<NotificationFilterValue>('all');

  const { unreadOnly, type } = useMemo<{
    unreadOnly?: boolean;
    type?: NotificationType;
  }>(() => {
    if (filter === 'all') return {};
    if (filter === 'unread') return { unreadOnly: true };
    return { type: filter };
  }, [filter]);

  const query = useNotifications({ unreadOnly, type });
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllRead();
  const remove = useDeleteNotification();

  const unreadCount = useNotificationsStore((s) => s.unreadCount);

  const items: Notification[] = query.data?.pages.flatMap((p) => p.items) ?? [];
  const groups = useMemo(() => groupByDay(items), [items]);

  const handlePress = (n: Notification) => {
    if (!n.read) markRead.mutate(n.id);
    const data = n.data as Record<string, unknown> | null;
    const reportId = data?.reportId as string | undefined;
    const outbreakId = data?.outbreakId as string | undefined;
    if (reportId) {
      router.push({ pathname: '/reports/[id]', params: { id: reportId } });
    } else if (outbreakId) {
      router.push('/map');
    }
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <View className="px-4 pt-2">
          <View className="flex-row items-end justify-between gap-3">
            <View className="flex-1">
              <Text className="text-3xl font-extrabold tracking-tight text-text">Alerts</Text>
              <Text className="text-sm text-text-muted">
                Outbreaks and updates from your region
              </Text>
            </View>
            {unreadCount > 0 ? (
              <PressableScale
                accessibilityRole="button"
                onPress={() => markAllRead.mutate()}
                disabled={markAllRead.isPending}
                haptic="selection"
                pressedScale={0.94}
              >
                <Text className="text-xs font-bold text-brand-700">Mark all read</Text>
              </PressableScale>
            ) : null}
          </View>
          <View className="mt-3">
            <NotificationFilter value={filter} onChange={setFilter} />
          </View>
        </View>

        {query.isPending ? (
          <View className="flex-1 items-center justify-center">
            <Loader size={40} />
          </View>
        ) : items.length === 0 ? (
          <View className="flex-1 items-center justify-center">
            <EmptyState
              emoji="ðŸŒ¾"
              title="All clear in your area"
              description="We'll alert you when nearby outbreaks need attention."
              actionLabel="Adjust alert radius"
              onAction={() => router.push('/profile')}
            />
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 140 }}
            refreshControl={
              <RefreshControl
                refreshing={query.isRefetching}
                onRefresh={() => query.refetch()}
                tintColor={theme.primary}
              />
            }
            onScroll={(e) => {
              const { layoutMeasurement, contentOffset, contentSize } = e.nativeEvent;
              if (
                layoutMeasurement.height + contentOffset.y >= contentSize.height - 200 &&
                query.hasNextPage &&
                !query.isFetchingNextPage
              ) {
                void query.fetchNextPage();
              }
            }}
            scrollEventThrottle={200}
          >
            {groups.map((group, gi) => (
              <View key={group.bucket}>
                <DayLabel>{group.label}</DayLabel>
                <View className="gap-2">
                  {group.items.map((item, i) => (
                    <Animated.View
                      key={item.id}
                      entering={FadeInDown.delay((gi * 100 + i) * 30).duration(260)}
                    >
                      <NotificationCard notification={item} onPress={handlePress} />
                    </Animated.View>
                  ))}
                </View>
              </View>
            ))}
            {query.isFetchingNextPage ? <Loader size={32} /> : null}
          </ScrollView>
        )}
      </SafeAreaView>
    </View>
  );
}
```

> The existing file had an unused `remove` mutation wired to `onLongPress`. We've dropped it for v1 simplicity. Re-introduce it later via a long-press handler on `NotificationCard` if needed.

- [ ] **Step 8: Verify and commit**

```bash
pnpm --filter mobile typecheck
```

Visually inspect the Notifications tab: light cards, day labels, severity-coded thumbnails, empty state with brand-glow tile.

```bash
git add apps/mobile/src/features/notifications apps/mobile/src/app/(app)/notifications.tsx
git commit -m "feat(mobile): light Notifications screen with day grouping"
```

---



## Task 9: Profile screen

**Files:**
- Modify: `apps/mobile/src/app/(app)/profile.tsx`
- Modify: `apps/mobile/src/features/plots/components/plot-card.tsx`
- Modify: `apps/mobile/src/features/plots/components/plot-form-sheet.tsx`

- [ ] **Step 1: Replace `(app)/profile.tsx`**

```tsx
import { BottomSheetModal } from '@gorhom/bottom-sheet';
import { router } from 'expo-router';
import { Bell, ChevronRight, Globe, MapPin, Plus, Radius, Shield } from 'lucide-react-native';
import { useRef, useState } from 'react';
import { Pressable, ScrollView } from 'react-native';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Avatar } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Chip } from '@/components/ui/chip';
import { SectionLabel } from '@/components/ui/section-label';
import type { Plot } from '@/features/plots/api/plots.api';
import { PlotCard, PlotFormSheet } from '@/features/plots/components';
import { useActivePlots } from '@/features/plots/hooks/use-plots';
import { onboardingStorage } from '@/features/plots/onboarding-storage';
import { MapPickerSheet } from '@/features/upload-report/components/map-picker-sheet';
import { useAuthStore } from '@/store/auth.store';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

export default function ProfileScreen() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { data: plots } = useActivePlots();

  const [editingPlot, setEditingPlot] = useState<Plot | null>(null);
  const formRef = useRef<BottomSheetModal>(null);
  const mapPickerRef = useRef<BottomSheetModal>(null);

  const location = [user?.district, user?.state].filter(Boolean).join(', ') || 'Not set';
  const role = (user?.role ?? 'farmer').toLowerCase();
  const roleLabel = role[0].toUpperCase() + role.slice(1);

  const handleLogout = async () => {
    await onboardingStorage.setSkipped(false);
    await logout();
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 140, gap: 16 }}
        >
          <Animated.View entering={FadeIn.duration(300)} className="items-center gap-2 pt-4">
            <Avatar name={user?.name} fallback="ðŸŒ¾" size="xl" verified />
            <Text className="text-2xl font-extrabold tracking-tight text-text">
              {user?.name ?? 'Welcome'}
            </Text>
            <Text className="text-sm text-text-muted">+91 {user?.phone ?? 'â€”'}</Text>
            <View className="flex-row gap-2">
              <Chip label={roleLabel} active />
              <Chip label="Verified" tone="success" />
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(80).duration(400)}>
            <SectionLabel>Your activity</SectionLabel>
            <View className="mt-2">
              <Card padding="none">
                <ListRow
                  icon={<Shield size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Reports submitted"
                  value="â€”"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<MapPin size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Plots"
                  value={String(plots?.length ?? 0)}
                  onPress={() => formRef.current?.present()}
                />
              </Card>
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(140).duration(400)}>
            <View className="flex-row items-center justify-between px-1">
              <SectionLabel>Plots</SectionLabel>
              <Pressable
                accessibilityRole="button"
                onPress={() => {
                  setEditingPlot(null);
                  formRef.current?.present();
                }}
              >
                <View className="flex-row items-center gap-1">
                  <Plus size={12} color={palette.brand[700]} strokeWidth={2.4} />
                  <Text className="text-xs font-bold text-brand-700">Add plot</Text>
                </View>
              </Pressable>
            </View>
            <View className="mt-2 gap-2">
              {plots && plots.length > 0 ? (
                plots.map((plot) => (
                  <PlotCard
                    key={plot.id}
                    plot={plot}
                    onPress={(p) => {
                      setEditingPlot(p);
                      formRef.current?.present();
                    }}
                  />
                ))
              ) : (
                <View className="items-center gap-2 rounded-xl border border-dashed border-border bg-surface-muted px-4 py-6">
                  <Text className="text-sm font-bold text-text">No plots yet</Text>
                  <Text className="max-w-[260px] text-center text-xs text-text-muted">
                    Add your first field to start receiving outbreak notifications.
                  </Text>
                </View>
              )}
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(200).duration(400)}>
            <SectionLabel>Settings</SectionLabel>
            <View className="mt-2">
              <Card padding="none">
                <ListRow
                  icon={<Bell size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Notifications"
                  value="On"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<Radius size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Alert radius"
                  value="5 km"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<Globe size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Language"
                  value="English"
                  onPress={() => undefined}
                />
                <ListRow
                  icon={<MapPin size={18} color={palette.brand[700]} strokeWidth={2.2} />}
                  label="Location"
                  value={location}
                  onPress={() => undefined}
                />
              </Card>
            </View>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(260).duration(400)}>
            <Pressable
              accessibilityRole="button"
              onPress={handleLogout}
              className="flex-row items-center justify-center rounded-xl border border-danger-tint bg-surface px-4 py-3"
            >
              <Text className="text-sm font-bold text-danger">Sign out</Text>
            </Pressable>
          </Animated.View>
        </ScrollView>
      </SafeAreaView>

      <PlotFormSheet
        ref={formRef}
        plot={editingPlot}
        onOpenMapPicker={() => mapPickerRef.current?.present()}
      />
      <MapPickerSheet
        ref={mapPickerRef}
        initialLocation={null}
        onConfirm={() => formRef.current?.present()}
      />
    </View>
  );
}

interface ListRowProps {
  icon: React.ReactNode;
  label: string;
  value?: string;
  onPress?: () => void;
  destructive?: boolean;
}

function ListRow({ icon, label, value, onPress, destructive }: ListRowProps) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress}>
      <View className="flex-row items-center gap-3 border-t border-border px-4 py-3 first:border-t-0">
        <View className="h-9 w-9 items-center justify-center rounded-xl bg-brand-50">{icon}</View>
        <View className="flex-1">
          <Text
            className={destructive ? 'text-sm font-bold text-danger' : 'text-sm font-bold text-text'}
          >
            {label}
          </Text>
          {value ? <Text className="text-xs text-text-muted">{value}</Text> : null}
        </View>
        {onPress ? <ChevronRight size={16} color={palette.brand[700]} strokeWidth={2.2} /> : null}
      </View>
    </Pressable>
  );
}
```

- [ ] **Step 2: Restyle `plot-card.tsx`**

Open `apps/mobile/src/features/plots/components/plot-card.tsx` and change:
- The container from a dark glass card to `rounded-xl border border-border bg-surface` with the standard card shadow (shadow `'card'`).
- Title text from `text-white` to `text-text`.
- Subtitles from `text-white/60` to `text-text-subtle`.
- Any LinearGradient backgrounds to a flat brand-tint background `bg-brand-50` for the icon tile.

- [ ] **Step 3: Restyle `plot-form-sheet.tsx`**

Update the sheet's `backgroundStyle` and `handleIndicatorStyle` to:

```tsx
backgroundStyle={{ backgroundColor: '#ffffff', borderTopLeftRadius: 24, borderTopRightRadius: 24 }}
handleIndicatorStyle={{ backgroundColor: '#e8e4dc', width: 36 }}
```

Replace any `text-white` / `text-white/60` with `text-text` / `text-text-muted`. Replace gradient buttons inside with the new `<Button variant="gradient" />` and `<Button variant="ghost" />`.

- [ ] **Step 4: Verify and commit**

```bash
pnpm --filter mobile typecheck
```

Visual check on Profile.

```bash
git add apps/mobile/src/app/(app)/profile.tsx apps/mobile/src/features/plots
git commit -m "feat(mobile): light Profile screen with sections + light Plots sheets"
```

---

## Task 10: Auth â€” Login + OTP

**Files:**
- Modify: `apps/mobile/src/app/(auth)/login.tsx`
- Modify: `apps/mobile/src/app/(auth)/otp.tsx`
- Modify: `apps/mobile/src/features/auth/components/auth-card.tsx`
- Modify: `apps/mobile/src/features/auth/components/gradient-button.tsx`
- Modify: `apps/mobile/src/features/auth/components/otp-input.tsx`
- Modify: `apps/mobile/src/features/auth/components/phone-input.tsx`

- [ ] **Step 1: Convert `auth-card.tsx` to a light wrapper**

Open `apps/mobile/src/features/auth/components/auth-card.tsx`. Replace the dark glass container with a flat light card:

```tsx
import { type ReactNode } from 'react';

import { Card } from '@/components/ui/card';

export function AuthCard({ children }: { children: ReactNode }) {
  return (
    <Card padding="md" shadow="card">
      {children}
    </Card>
  );
}
```

- [ ] **Step 2: Make `gradient-button.tsx` an alias for `<Button variant="gradient">`**

```tsx
import { Button } from '@/components/ui/button';

interface GradientButtonProps {
  label: string;
  loading?: boolean;
  disabled?: boolean;
  onPress: () => void;
}

/** @deprecated Use <Button variant="gradient" /> directly. Kept for diff continuity. */
export function GradientButton({ label, loading, disabled, onPress }: GradientButtonProps) {
  return (
    <Button
      label={label}
      variant="gradient"
      size="lg"
      loading={loading}
      disabled={disabled}
      onPress={onPress}
    />
  );
}
```

- [ ] **Step 3: Restyle `otp-input.tsx`**

Open the file. Update the digit-cell styling so:
- Empty cell: `border border-border bg-surface text-text`
- Filled: `border-2 border-brand-600 bg-brand-50 text-text`
- Focused (next-to-fill): `border-2 border-brand-600 bg-surface text-text`
- Error wraps: outer container gets `border-danger`

Keep the rest of the API (props: `value`, `onChangeText`, `error?`, `onComplete?`).

- [ ] **Step 4: Restyle `phone-input.tsx`**

Replace dark borders with `border-border` and dark text with `text-text`. The flag/country-code prefix stays as a `<Text>` with `text-text` and `font-bold`.

- [ ] **Step 5: Replace `(auth)/login.tsx`**

```tsx
import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { LinearGradient } from 'expo-linear-gradient';

import { PhoneInput } from '@/features/auth/components/phone-input';
import { useSendOtp } from '@/features/auth/hooks/use-send-otp';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import { normalizeError } from '@/utils/errors';

const DEMO_PHONE = '9999999999';

export default function LoginScreen() {
  const [phone, setPhone] = useState('');
  const [error, setError] = useState<string | undefined>();
  const sendOtp = useSendOtp();

  const handleSubmit = async () => {
    setError(undefined);
    if (phone.length !== 10) {
      setError('Enter a 10-digit phone number');
      return;
    }
    try {
      await sendOtp.mutateAsync({ phone });
      router.push({ pathname: '/otp', params: { phone } });
    } catch (err) {
      setError(normalizeError(err).message);
    }
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView style={{ flex: 1 }}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View className="flex-1 items-center justify-center gap-3 px-6 pt-6">
            <Animated.View entering={FadeIn.duration(400)}>
              <View
                className="h-14 w-14 items-center justify-center overflow-hidden rounded-2xl border border-border"
                style={{
                  shadowColor: palette.brand[600],
                  shadowOffset: { width: 0, height: 10 },
                  shadowOpacity: 0.32,
                  shadowRadius: 18,
                  elevation: 8,
                }}
              >
                <LinearGradient
                  colors={[palette.brand[400], palette.brand[600]]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={{ position: 'absolute', inset: 0 }}
                />
                <Text className="text-2xl">ðŸŒ¾</Text>
              </View>
            </Animated.View>
            <Animated.View entering={FadeInDown.delay(80).duration(400)} className="items-center gap-1">
              <Text className="text-3xl font-extrabold tracking-tight text-text">
                Welcome to AgroRadar
              </Text>
              <Text className="max-w-[260px] text-center text-sm text-text-muted">
                Detect, report, and track crop diseases together.
              </Text>
            </Animated.View>
          </View>

          <Animated.View entering={FadeInDown.delay(160).duration(400)} className="gap-3 px-4 pb-6">
            <Text className="text-xs font-bold uppercase tracking-[1.4px] text-text-subtle">
              Phone number
            </Text>
            <PhoneInput value={phone} onChangeText={setPhone} error={error} />
            <Button
              label={sendOtp.isPending ? 'Sending OTPâ€¦' : 'Send OTP'}
              variant="gradient"
              size="lg"
              loading={sendOtp.isPending}
              onPress={handleSubmit}
            />
            <Text className="text-center text-xs text-text-faint">
              Demo: use +91 {DEMO_PHONE}. By continuing you agree to our Terms & Privacy.
            </Text>
          </Animated.View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 6: Replace `(auth)/otp.tsx`**

```tsx
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { OtpInput } from '@/features/auth/components/otp-input';
import { useSendOtp } from '@/features/auth/hooks/use-send-otp';
import { useVerifyOtp } from '@/features/auth/hooks/use-verify-otp';
import { Text, View } from '@/tw';
import { normalizeError } from '@/utils/errors';

const RESEND_SECONDS = 30;

export default function OtpScreen() {
  const params = useLocalSearchParams<{ phone?: string }>();
  const phone = params.phone ?? '';
  const [otp, setOtp] = useState('');
  const [error, setError] = useState<string | undefined>();
  const [secondsLeft, setSecondsLeft] = useState(RESEND_SECONDS);

  const verifyOtp = useVerifyOtp();
  const sendOtp = useSendOtp();

  useEffect(() => {
    if (secondsLeft <= 0) return undefined;
    const id = setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [secondsLeft]);

  const handleSubmit = async (code = otp) => {
    setError(undefined);
    if (code.length !== 6) {
      setError('Enter the 6-digit code');
      return;
    }
    if (!phone) {
      setError('Missing phone number. Please go back and try again.');
      return;
    }
    try {
      await verifyOtp.mutateAsync({ phone, otp: code });
    } catch (err) {
      setError(normalizeError(err).message);
      setOtp('');
    }
  };

  const handleResend = async () => {
    if (secondsLeft > 0 || !phone) return;
    setError(undefined);
    try {
      await sendOtp.mutateAsync({ phone });
      setSecondsLeft(RESEND_SECONDS);
    } catch (err) {
      setError(normalizeError(err).message);
    }
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView style={{ flex: 1 }}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View className="px-4 pt-3">
            <Pressable
              onPress={() => router.back()}
              accessibilityRole="button"
              accessibilityLabel="Back"
              className="self-start"
            >
              <Text className="text-sm font-bold text-brand-700">â€¹ Back</Text>
            </Pressable>
          </View>

          <View className="flex-1 items-center justify-center gap-5 px-6">
            <Animated.View entering={FadeInDown.duration(400)} className="items-center gap-1">
              <Text className="text-2xl font-extrabold tracking-tight text-text">
                Enter 6-digit code
              </Text>
              <Text className="text-sm text-text-muted">Sent to +91 {phone}</Text>
            </Animated.View>

            <OtpInput
              value={otp}
              onChangeText={setOtp}
              error={error}
              onComplete={handleSubmit}
            />

            <Pressable accessibilityRole="button" onPress={handleResend} disabled={secondsLeft > 0 || sendOtp.isPending}>
              <Text
                className={
                  secondsLeft > 0
                    ? 'text-sm font-bold text-text-faint'
                    : 'text-sm font-bold text-brand-700'
                }
              >
                {secondsLeft > 0
                  ? `Resend in ${secondsLeft}s`
                  : sendOtp.isPending
                    ? 'Sendingâ€¦'
                    : 'Resend code'}
              </Text>
            </Pressable>
          </View>

          <View className="gap-2 px-4 pb-6">
            <Button
              label={verifyOtp.isPending ? 'Verifyingâ€¦' : 'Verify'}
              variant="gradient"
              size="lg"
              loading={verifyOtp.isPending}
              disabled={otp.length !== 6}
              onPress={() => handleSubmit()}
            />
            <Text className="text-center text-xs text-text-faint">
              Demo OTP: 123456
            </Text>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 7: Verify and commit**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile dev
```

Walk login â†’ OTP. Confirm light theme everywhere, gradient logo tile, gradient buttons, OTP digit boxes that turn brand-teal when filled.

```bash
git add apps/mobile/src/app/(auth) apps/mobile/src/features/auth
git commit -m "feat(mobile): light Login + OTP screens"
```

---



## Task 11: Onboarding â€” Name + First plot

**Files:**
- Modify: `apps/mobile/src/app/(onboarding)/name.tsx`
- Modify: `apps/mobile/src/app/(onboarding)/first-plot.tsx`
- Modify: `apps/mobile/src/app/(onboarding)/_layout.tsx` (only if it set a dark background)

- [ ] **Step 1: Replace `(onboarding)/name.tsx`**

```tsx
import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SectionLabel } from '@/components/ui/section-label';
import { authApi } from '@/features/auth/api/auth.api';
import { onboardingStorage } from '@/features/plots/onboarding-storage';
import { useAuthStore } from '@/store/auth.store';
import { Text, View } from '@/tw';

export default function OnboardingNameScreen() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [name, setName] = useState(user?.name ?? '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNext = async () => {
    setError(null);
    const trimmed = name.trim();
    if (!trimmed) return setError('Tell us what to call you.');
    setBusy(true);
    try {
      const updated = await authApi.updateMe({ name: trimmed });
      await setUser(updated);
      router.push('/first-plot');
    } catch (err) {
      setError((err as Error).message ?? 'Could not save your name');
    } finally {
      setBusy(false);
    }
  };

  const handleSkip = async () => {
    await onboardingStorage.setSkipped(true);
    router.replace('/');
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView style={{ flex: 1 }}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View className="px-4 pt-3">
            <SectionLabel>Step 1 of 2</SectionLabel>
          </View>

          <View className="flex-1 justify-center gap-3 px-4">
            <Animated.View entering={FadeInDown.duration(400)} className="gap-2">
              <Text className="text-3xl font-extrabold tracking-tight text-text">
                What should we call you?
              </Text>
              <Text className="text-sm text-text-muted">
                Helps neighboring farmers recognize your reports.
              </Text>
            </Animated.View>

            <Animated.View entering={FadeInDown.delay(100).duration(400)}>
              <Input
                value={name}
                onChangeText={setName}
                placeholder="e.g. Ramesh Patil"
                autoCapitalize="words"
                error={error ?? undefined}
              />
            </Animated.View>
          </View>

          <View className="flex-row gap-3 px-4 pb-6">
            <Button label="Skip" variant="ghost" size="lg" onPress={handleSkip} fullWidth />
            <View className="flex-[2]">
              <Button
                label={busy ? 'Savingâ€¦' : 'Continue'}
                variant="gradient"
                size="lg"
                loading={busy}
                onPress={handleNext}
              />
            </View>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 2: Replace `(onboarding)/first-plot.tsx`**

```tsx
import { BottomSheetModal } from '@gorhom/bottom-sheet';
import { router } from 'expo-router';
import { Layers } from 'lucide-react-native';
import { useRef } from 'react';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { SectionLabel } from '@/components/ui/section-label';
import { onboardingStorage } from '@/features/plots/onboarding-storage';
import { PlotFormSheet } from '@/features/plots/components/plot-form-sheet';
import { MapPickerSheet } from '@/features/upload-report/components/map-picker-sheet';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';

export default function OnboardingFirstPlotScreen() {
  const formRef = useRef<BottomSheetModal>(null);
  const mapPickerRef = useRef<BottomSheetModal>(null);

  const finish = async () => {
    await onboardingStorage.setSkipped(true);
    router.replace('/');
  };

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView style={{ flex: 1 }}>
        <View className="px-4 pt-3">
          <SectionLabel>Step 2 of 2</SectionLabel>
        </View>

        <View className="flex-1 justify-center gap-4 px-4">
          <Animated.View entering={FadeInDown.duration(400)} className="gap-2">
            <Text className="text-3xl font-extrabold tracking-tight text-text">
              Add your first plot
            </Text>
            <Text className="text-sm text-text-muted">
              We&apos;ll alert you when a disease outbreak is detected near it. You can add more
              plots anytime from your profile.
            </Text>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(100).duration(400)}>
            <Card padding="md">
              <View className="flex-row items-center gap-3">
                <View className="h-12 w-12 items-center justify-center rounded-xl bg-brand-50">
                  <Layers size={22} color={palette.brand[700]} strokeWidth={2} />
                </View>
                <View className="flex-1 gap-0.5">
                  <Text className="text-sm font-bold text-text">Plot-based alerts</Text>
                  <Text className="text-xs text-text-muted">
                    No live tracking. Only fields you register.
                  </Text>
                </View>
              </View>
            </Card>
          </Animated.View>
        </View>

        <View className="gap-2 px-4 pb-6">
          <Button
            label="Add a plot"
            variant="gradient"
            size="lg"
            onPress={() => formRef.current?.present()}
          />
          <Button label="I'll do this later" variant="ghost" size="md" onPress={finish} />
        </View>
      </SafeAreaView>

      <PlotFormSheet
        ref={formRef}
        onSaved={() => {
          void onboardingStorage.setSkipped(true);
          router.replace('/');
        }}
        onOpenMapPicker={() => mapPickerRef.current?.present()}
      />
      <MapPickerSheet
        ref={mapPickerRef}
        initialLocation={null}
        onConfirm={() => formRef.current?.present()}
      />
    </View>
  );
}
```

- [ ] **Step 3: Inspect `(onboarding)/_layout.tsx`**

If the file applies a dark background or status-bar style, change to light. Most onboarding stacks just use `<Stack screenOptions={{ headerShown: false }} />` â€” leave it untouched if so.

- [ ] **Step 4: Verify and commit**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile dev
```

Trigger onboarding (sign up with a fresh phone number). Confirm both screens render light, with brand-teal focus borders on inputs and gradient CTAs.

```bash
git add apps/mobile/src/app/(onboarding)
git commit -m "feat(mobile): light onboarding screens"
```

---

## Task 12: Report detail screen

**Files:**
- Modify: `apps/mobile/src/app/reports/[id].tsx`
- Modify: `apps/mobile/src/features/disease-analysis/components/result-hero.tsx`
- Modify: `apps/mobile/src/features/disease-analysis/components/severity-badge.tsx`
- Modify: `apps/mobile/src/features/disease-analysis/components/recommendations-list.tsx`
- Modify: `apps/mobile/src/features/disease-analysis/components/result-actions.tsx`
- Modify: `apps/mobile/src/features/disease-analysis/components/processing-state.tsx`
- Modify: `apps/mobile/src/features/disease-analysis/components/confidence-ring.tsx`

- [ ] **Step 1: Restyle `result-hero.tsx`**

Open the file. Replace dark backgrounds with `bg-surface`, dark borders with `border-border`. Change any `text-white` to `text-text` and `text-white/60` to `text-text-muted`. The image banner should remain rounded-xl but on a white background instead of dark.

- [ ] **Step 2: Restyle `severity-badge.tsx`**

Replace internals with the shared `<Chip>` component:

```tsx
import { Chip } from '@/components/ui/chip';
import type { Severity } from '@/features/upload-report/types';

const TONE: Record<Severity, 'success' | 'warning' | 'danger'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
};

const LABEL: Record<Severity, string> = {
  LOW: 'Low severity',
  MEDIUM: 'Medium severity',
  HIGH: 'High severity',
};

export function SeverityBadge({ severity }: { severity: Severity | null | undefined }) {
  if (!severity) return null;
  return <Chip label={LABEL[severity]} tone={TONE[severity]} />;
}
```

- [ ] **Step 3: Restyle `recommendations-list.tsx`**

Replace its internals with the new `RecommendationsCard` from `features/report-flow`:

```tsx
import { RecommendationsCard } from '@/features/report-flow';

export function RecommendationsList({ items }: { items: string[] | null | undefined }) {
  return <RecommendationsCard items={items ?? []} />;
}
```

- [ ] **Step 4: Restyle `result-actions.tsx`, `processing-state.tsx`, `confidence-ring.tsx`**

For each:
- Replace `bg-bg/X` overlays with `bg-surface`.
- Replace `text-white*` with `text-text*`.
- Replace `border-white/X` with `border-border`.
- Replace `LinearGradient` colors that used `palette.brand[700/900/'#0b1220']` with the new gradient `[palette.brand[500], palette.brand[600]]`.
- For `confidence-ring.tsx`, the SVG ring stroke colors should map LOW â†’ `palette.status.success`, MEDIUM â†’ `#d97706`, HIGH â†’ `#dc2626`. Track stroke is `palette.brand[100]`.

- [ ] **Step 5: Replace `app/reports/[id].tsx` with the light layout**

```tsx
import { router, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, MoreHorizontal, RefreshCw } from 'lucide-react-native';
import { ScrollView } from 'react-native';
import Animated, { FadeIn, FadeInDown } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loader } from '@/components/ui/loader';
import { PressableScale } from '@/components/ui/pressable-scale';
import { SectionLabel } from '@/components/ui/section-label';
import { ConfidenceRing } from '@/features/disease-analysis/components/confidence-ring';
import { ProcessingState } from '@/features/disease-analysis/components/processing-state';
import { RecommendationsList } from '@/features/disease-analysis/components/recommendations-list';
import { ResultActions } from '@/features/disease-analysis/components/result-actions';
import { ResultHero } from '@/features/disease-analysis/components/result-hero';
import { SeverityBadge } from '@/features/disease-analysis/components/severity-badge';
import { useReport, useReprocessReport } from '@/features/disease-analysis/hooks/use-report';
import { palette } from '@/theme/colors';
import { Text, View } from '@/tw';
import { timeAgo } from '@/utils/severity';

export default function ReportDetailScreen() {
  const params = useLocalSearchParams<{ id?: string }>();
  const id = params.id;

  const { data: report, isPending, isError, refetch } = useReport(id);
  const reprocess = useReprocessReport(id);

  return (
    <View className="flex-1 bg-bg">
      <SafeAreaView edges={['top']} style={{ flex: 1 }}>
        <View className="flex-row items-center justify-between px-4 py-2">
          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="Back"
            onPress={() => router.back()}
            haptic="selection"
            pressedScale={0.92}
            className="h-10 w-10 items-center justify-center rounded-full border border-border bg-surface"
          >
            <ChevronLeft size={20} color={palette.brand[700]} strokeWidth={2.2} />
          </PressableScale>
          <Text className="text-base font-bold text-text">Report</Text>
          <PressableScale
            accessibilityRole="button"
            accessibilityLabel="More"
            onPress={() => undefined}
            haptic="selection"
            pressedScale={0.92}
            className="h-10 w-10 items-center justify-center rounded-full border border-border bg-surface"
          >
            <MoreHorizontal size={18} color={palette.brand[700]} strokeWidth={2.2} />
          </PressableScale>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ padding: 16, paddingBottom: 140, gap: 16 }}
        >
          {isPending ? (
            <View className="items-center justify-center py-20">
              <Loader size={48} />
            </View>
          ) : isError || !report ? (
            <View className="items-center gap-3 py-10">
              <Text className="text-base font-bold text-text">Couldn&apos;t load report</Text>
              <Button label="Retry" variant="ghost" onPress={() => refetch()} fullWidth={false} />
            </View>
          ) : report.processingStatus === 'PENDING' || report.processingStatus === 'PROCESSING' ? (
            <Animated.View entering={FadeIn.duration(400)}>
              <ProcessingState imageUrl={report.imageUrl} cropType={report.cropType} />
            </Animated.View>
          ) : (
            <>
              <Animated.View entering={FadeIn.duration(400)}>
                <ResultHero
                  imageUrl={report.imageUrl}
                  cropType={report.cropType}
                  severity={report.severity}
                />
              </Animated.View>

              <Animated.View entering={FadeInDown.delay(100).duration(400)}>
                <Card padding="md">
                  <View className="flex-row items-center gap-4">
                    <ConfidenceRing
                      value={report.confidence ?? 0}
                      severity={report.severity}
                      size={120}
                      strokeWidth={10}
                    />
                    <View className="flex-1 gap-1">
                      <SectionLabel>Detected</SectionLabel>
                      <Text className="text-lg font-extrabold tracking-tight text-text">
                        {report.disease ?? 'Unknown'}
                      </Text>
                      <SeverityBadge severity={report.severity} />
                      {report.processedAt ? (
                        <Text className="mt-1 text-[11px] text-text-subtle">
                          Analyzed {timeAgo(report.processedAt)}
                        </Text>
                      ) : null}
                    </View>
                  </View>
                </Card>
              </Animated.View>

              {report.notes ? (
                <Animated.View entering={FadeInDown.delay(160).duration(400)}>
                  <Card padding="md">
                    <SectionLabel>Your notes</SectionLabel>
                    <Text className="mt-1 text-sm leading-5 text-text">{report.notes}</Text>
                  </Card>
                </Animated.View>
              ) : null}

              <Animated.View entering={FadeInDown.delay(200).duration(400)} className="gap-2">
                <View className="flex-row items-center justify-between px-1">
                  <Text className="text-base font-bold tracking-tight text-text">
                    Recommended actions
                  </Text>
                  <PressableScale
                    accessibilityRole="button"
                    accessibilityLabel="Re-run analysis"
                    onPress={() => reprocess.mutate()}
                    disabled={reprocess.isPending}
                    haptic="selection"
                    pressedScale={0.95}
                  >
                    <View className="flex-row items-center gap-1">
                      <RefreshCw size={12} color={palette.brand[700]} strokeWidth={2.4} />
                      <Text className="text-xs font-bold text-brand-700">
                        {reprocess.isPending ? 'Re-analyzingâ€¦' : 'Re-run'}
                      </Text>
                    </View>
                  </PressableScale>
                </View>
                <RecommendationsList items={report.recommendations} />
              </Animated.View>

              <Animated.View entering={FadeInDown.delay(260).duration(400)}>
                <ResultActions
                  report={report}
                  onUploadAnother={() => router.replace('/upload')}
                  onViewOnMap={() => router.push('/map')}
                />
              </Animated.View>

              <Animated.View entering={FadeInDown.delay(320).duration(400)}>
                <Text className="px-2 text-[11px] text-text-subtle">
                  AI predictions are advisory. For high-severity diagnoses, consult your local
                  agricultural extension officer.
                </Text>
              </Animated.View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}
```

- [ ] **Step 6: Verify and commit**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile dev
```

Submit a report through the new flow, then tap "View this report" on the Submitted screen. Confirm the detail screen renders light with the confidence ring + recommendations + actions.

```bash
git add apps/mobile/src/app/reports/[id].tsx apps/mobile/src/features/disease-analysis
git commit -m "feat(mobile): light Report detail screen"
```

---



## Task 13: Cross-cutting â€” Offline banner, Toast, Queue card

**Files:**
- Modify: `apps/mobile/src/features/offline-sync/components/offline-banner.tsx`
- Modify: `apps/mobile/src/features/offline-sync/components/queue-status-card.tsx`
- Modify: `apps/mobile/src/features/offline-sync/components/sync-status-indicator.tsx`
- Modify: `apps/mobile/src/features/toast/toast.tsx`

- [ ] **Step 1: Restyle `offline-banner.tsx`**

Replace the dark/red strip with a light amber banner. The component is rendered persistently in `app/_layout.tsx` and currently animates in/out â€” keep that logic.

```tsx
import { CloudOff } from 'lucide-react-native';
import Animated, { FadeInDown, FadeOutUp } from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useNetworkStore } from '@/features/offline-sync/store/network.store';
import { useOfflineQueueStore } from '@/features/upload-report/store/offline-queue.store';
import { Text, View } from '@/tw';
import { palette } from '@/theme/colors';

export function OfflineBanner() {
  const isOnline = useNetworkStore((s) => s.isOnline);
  const queueSize = useOfflineQueueStore((s) => s.items.length);
  if (isOnline) return null;

  return (
    <Animated.View
      entering={FadeInDown.duration(220)}
      exiting={FadeOutUp.duration(220)}
      style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 100 }}
      pointerEvents="box-none"
    >
      <SafeAreaView edges={['top']}>
        <View className="mx-3 mt-1 flex-row items-center gap-2 rounded-xl border border-warning-tint bg-warning-tint px-3 py-2">
          <CloudOff size={14} color={palette.status.warning} strokeWidth={2.4} />
          <Text className="text-xs font-bold text-warning">You&apos;re offline</Text>
          {queueSize > 0 ? (
            <Text className="text-xs text-warning/80">
              Â· {queueSize} report{queueSize === 1 ? '' : 's'} queued Â· will sync when connected
            </Text>
          ) : (
            <Text className="text-xs text-warning/80">Â· cached data shown</Text>
          )}
        </View>
      </SafeAreaView>
    </Animated.View>
  );
}
```

> Confirm the actual store names (`useNetworkStore`, `useOfflineQueueStore`) and field paths against the existing files before editing â€” adapt selectors if names differ.

- [ ] **Step 2: Restyle `queue-status-card.tsx` and `sync-status-indicator.tsx`**

For each:
- Replace dark backgrounds with `bg-surface` + `border border-border`.
- Replace `text-white*` with `text-text*`.
- Replace progress bars: track `bg-border`, fill `bg-brand-500` (or use the gradient via `LinearGradient`).
- Use the new `<Button variant="ghost" />` for retry / cancel actions.
- Severity-tinted dots for sync status: idle = `text-subtle`, syncing = `brand`, error = `danger`.

- [ ] **Step 3: Restyle `features/toast/toast.tsx`**

Replace dark surface with white. Tone-tinted left border:

```tsx
// Inside the existing Toast container â€” adjust styles only.
const TONE_STYLES: Record<'success' | 'error' | 'info', { tint: string; border: string; text: string; bg: string }> = {
  success: {
    tint: '#047857',
    border: '#a7f3d0',
    text: '#047857',
    bg: '#ecfdf5',
  },
  error: {
    tint: '#b91c1c',
    border: '#fecaca',
    text: '#b91c1c',
    bg: '#fee2e2',
  },
  info: {
    tint: '#1d4ed8',
    border: '#bfdbfe',
    text: '#1d4ed8',
    bg: '#dbeafe',
  },
};
```

Then in render, the toast container becomes:

```tsx
<View
  style={{
    backgroundColor: tone.bg,
    borderColor: tone.border,
    borderWidth: 1,
    borderLeftWidth: 4,
    borderLeftColor: tone.tint,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
  }}
>
  <Text style={{ color: tone.text, fontSize: 14, fontWeight: '700' }}>{message}</Text>
</View>
```

Keep the existing positioning, dismissal, and animation logic untouched â€” only swap the inner styles.

- [ ] **Step 4: Verify and commit**

Manually toggle airplane mode on the device to verify the offline banner renders. Trigger a successful upload and confirm the success toast renders in light style.

```bash
pnpm --filter mobile typecheck
git add apps/mobile/src/features/offline-sync apps/mobile/src/features/toast
git commit -m "feat(mobile): light offline banner, queue card, and toast"
```

---

## Task 14: Cleanup â€” remove deprecated dark-mode artifacts

**Files:**
- Modify: `apps/mobile/src/components/ui/button.tsx` (remove the temporary `'primary' | 'secondary'` aliases from Task 2 Step 11)
- Modify: `apps/mobile/src/features/auth/components/gradient-button.tsx` (delete the file once all call sites use `<Button variant="gradient">`)
- Modify: `apps/mobile/src/features/auth/components/index.ts` (remove the `gradient-button` export)
- Modify: `apps/mobile/src/components/ui/index.ts` (sanity check exports)
- Audit: every `*.tsx` file under `apps/mobile/src` for leftover `text-white`, `bg-bg/X`, `palette.brand[700]`-as-background usage that doesn't belong.

- [ ] **Step 1: Remove the deprecated Button variant aliases**

In `apps/mobile/src/components/ui/button.tsx` revert the `Variant` type to:

```ts
type Variant = 'gradient' | 'solid' | 'ghost' | 'destructive';
```

Delete the `effectiveVariant` mapping line.

- [ ] **Step 2: Find and replace remaining call sites**

```bash
pnpm --filter mobile typecheck
```

Any failing import/site that says `variant="primary"` or `variant="secondary"`:
- `variant="primary"` â†’ `variant="gradient"`
- `variant="secondary"` â†’ `variant="solid"`

- [ ] **Step 3: Delete `gradient-button.tsx` and update its barrel**

```bash
rm apps/mobile/src/features/auth/components/gradient-button.tsx
```

In `apps/mobile/src/features/auth/components/index.ts`, remove the line:

```ts
export * from './gradient-button';
```

Re-run typecheck â€” any reference to `GradientButton` should now fail. Replace each with `<Button variant="gradient" size="lg" />`.

- [ ] **Step 4: Sweep for stray dark-theme styles**

Run grep across the codebase:

```bash
rg "text-white" apps/mobile/src/
rg "bg-bg/" apps/mobile/src/
rg "border-white" apps/mobile/src/
rg "palette.brand\[(7|8|9)" apps/mobile/src/ --no-heading
```

For each match, decide:
- **Keep** â€” text on a gradient surface (e.g., gradient buttons, the FAB) legitimately uses `text-white`.
- **Replace** â€” text on a light surface uses `text-text` / `text-text-muted` instead.
- **Backgrounds** â€” any `bg-bg/X` or dark-tinted background outside the splash gradient should be `bg-surface` or `bg-surface-muted`.
- **`palette.brand[700â€“900]` as a background** â€” replace with `palette.brand[500â€“600]` or use the gradient. (`palette.brand[700]` as an icon/text color is fine.)

Apply edits one-by-one. Re-run typecheck after each batch.

- [ ] **Step 5: Verify and commit**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile lint
```

```bash
git add apps/mobile/src
git commit -m "chore(mobile): remove deprecated dark-mode artifacts and Button aliases"
```

---

## Task 15: Acceptance verification

**Goal:** Walk every spec acceptance criterion and confirm it passes on a real device or simulator.

- [ ] **Step 1: Typecheck and lint pass**

```bash
pnpm --filter mobile typecheck
pnpm --filter mobile lint
```

Expected: both PASS with zero errors. (Warnings about unused imports in feature components that were partially restyled are acceptable; fix them inline as you find them.)

- [ ] **Step 2: Cold boot + auth + onboarding**

```bash
pnpm --filter mobile clean
pnpm --filter mobile dev
```

On a fresh install:
1. Splash renders light with the gradient logo and breathing glow.
2. Login screen renders light. Enter `9999999999` â†’ tap Send OTP â†’ demo OTP `123456` â†’ Verify.
3. Onboarding Name step renders light. Enter a name â†’ Continue.
4. Onboarding First Plot renders light. Skip or add a plot.

Acceptance ref: Â§9 item 7.

- [ ] **Step 3: Tab bar + FAB**

From any tab (Home, Map, Notifications, Profile), tap the center gradient FAB. Confirm it opens the report flow Capture screen. Acceptance ref: Â§9 item 2.

- [ ] **Step 4: Report flow with all three engines**

Test the engine fallback chain:

1. **Cloud success** â€” temporarily replace the body of `analyzeImage` with a hardcoded resolution returning a valid `AnalysisResult`. Run the flow. Confirm:
   - Analyzing screen says "Using our high-accuracy cloud modelâ€¦"
   - Result screen badge reads "Cloud AI Â· NN%"
   - Recommendations card lists numbered items
   - Map-share toggle defaults to ON
   - Confirm & submit lands on the success screen
2. **On-device** â€” restore `analyzeImage` to call the real (unavailable) endpoint, but in `offlineAiClient`, temporarily change `isAvailable()` to return `true` and `analyze()` to return a valid result. Run the flow. Confirm engine badge says "On-device AI Â· NN%".
3. **Manual** â€” restore `offlineAiClient` to its original stub (returns `UNAVAILABLE`). Run the flow. Confirm:
   - Analyzing screen runs for ~8s (cloud timeout) then transitions to result with no badge.
   - All result fields are empty.
   - "Edit details" sheet allows entering disease + severity.
   - Confirm & submit succeeds.

Acceptance ref: Â§9 item 3.

- [ ] **Step 5: Map screen**

Open the Map tab. Confirm:
- Light map style (Android) â€” off-white background, light roads, muted greens.
- Search bar and filter button at top with soft shadow.
- Filter chip rail beneath: All / Tomato / Wheat / High / 7d / etc.
- Vertical FAB stack on the right: locate, layer, filter buttons.
- Persistent bottom sheet listing reports in view, draggable between 25%/60%/92%.

Tap a marker â†’ bottom sheet expands and the corresponding report row scrolls into view (or report-detail sheet pops; either is acceptable).

Acceptance ref: Â§9 item 4.

- [ ] **Step 6: Loading / empty / offline states**

- Pull-to-refresh on Home â†’ confirm brand-teal spinner.
- Filter Notifications by an empty type â†’ confirm empty state with `ðŸŒ¾` glow tile and "Adjust alert radius" ghost button.
- Toggle airplane mode â†’ confirm light amber offline banner across the top, persists across tabs.
- Submit a report while offline â†’ confirm queue card on `(app)/upload` reflects the queued item.

Acceptance ref: Â§9 item 5.

- [ ] **Step 7: No traces of old dark navy palette**

Visually scan every screen one more time. Look for:
- Any white-on-navy pill or chip.
- Any glass/blur surface that hasn't been replaced.
- Any stray `text-white` on a light background.

If you find one, fix it inline and re-run typecheck.

Acceptance ref: Â§9 item 1.

- [ ] **Step 8: Final commit**

If you made any cleanup edits during verification:

```bash
git add apps/mobile/src
git commit -m "chore(mobile): final cleanup after redesign verification"
```

If everything passed without edits: nothing to commit. The redesign is complete.

- [ ] **Step 9: Push the branch**

(Only if the user has explicitly asked to push.)

```bash
git push -u origin <branch-name>
```

---

## Done

Every screen now lives in the Soft Sage light theme:

- Theme tokens, global.css, and the dark-mode code path replaced.
- UI primitives (Button, Card, Input, Avatar, Skeleton, Loader, EmptyState, Chip, SectionLabel) rebuilt for the new system.
- Tab bar with raised gradient Report FAB.
- Splash and error boundary in light theme.
- Home (hero-first), Map (search + chips + reports sheet), Notifications (day groups), Profile (sectioned), Login + OTP, Name + First plot, Report detail.
- Four-step report flow with cloud â†’ on-device â†’ manual fallback and engine badges.
- Offline banner, toast, queue card all light.
- Deprecated artifacts removed.
- Acceptance criteria walked.

