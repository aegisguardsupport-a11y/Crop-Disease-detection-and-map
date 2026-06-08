# Mobile — AgroRadar

Expo + Expo Router app with NativeWind v5 (Tailwind v4), Zustand, TanStack Query, axios, and Socket.IO.

## Setup

```bash
cp .env.example .env
pnpm install
pnpm dev          # or: pnpm android | pnpm ios | pnpm web
```

## Scripts

- `pnpm dev` — start Metro
- `pnpm android` / `pnpm ios` / `pnpm web` — start with a specific target
- `pnpm typecheck` — TypeScript only
- `pnpm lint` — Expo's ESLint runner
- `pnpm clean` — clear `.expo` and `dist`

## Environment

`.env` (or shell env) values prefixed with `EXPO_PUBLIC_` are inlined at bundle time:

| Var                       | Default                  | Description                          |
| ------------------------- | ------------------------ | ------------------------------------ |
| `EXPO_PUBLIC_API_URL`     | `http://localhost:3000`  | NestJS backend base URL              |
| `EXPO_PUBLIC_SOCKET_URL`  | `http://localhost:3000`  | Socket.IO endpoint                   |

## Folder structure

```
src/
├── app/                # Expo Router routes
│   ├── _layout.tsx     # Root providers (Query, Theme, Socket, BottomSheet)
│   └── index.tsx       # Component showcase home screen
├── components/
│   ├── ui/             # Button, Input, Card, Loader
│   ├── layout/         # ScreenContainer, SectionHeader
│   └── feedback/       # BottomSheetWrapper, EmptyState
├── features/           # Feature modules (placeholder)
├── hooks/              # useColorScheme, useTheme, useDebouncedValue
├── providers/          # QueryProvider, ThemeProvider, SocketProvider
├── services/
│   ├── api/            # axios + interceptors, health endpoint
│   ├── socket/         # Socket.IO singleton
│   └── storage/        # SecureStore + AsyncStorage helpers
├── store/              # Zustand auth scaffold
├── theme/              # Design tokens (colors, spacing, radii, shadows, typography, animations)
├── tw/                 # react-native-css component re-exports (className-enabled)
├── constants/          # APP_NAME, STORAGE_KEYS, QUERY_KEYS, ROUTES, env
├── types/              # User, ApiResponse
├── utils/              # cn, formatters, error normalization
├── offline/            # Placeholder for offline-first features
└── global.css          # Tailwind v4 entry + design tokens
```

## Styling

This app uses **NativeWind v5 + Tailwind v4** via `react-native-css`. Tailwind config is CSS-first (see `src/global.css`) — there is no `tailwind.config.js`.

Use the components exported from `@/tw` whenever you need `className`:

```tsx
import { View, Text } from '@/tw';

<View className="rounded-2xl bg-surface p-4">
  <Text className="text-base font-semibold text-text">Hello</Text>
</View>
```

Theme color tokens (configurable in `global.css`): `bg`, `surface`, `surface-elevated`, `border`, `border-strong`, `text`, `text-muted`, `text-subtle`, `text-inverse`, `brand-*`, `success`, `warning`, `danger`, `info`.
