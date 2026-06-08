# AgroRadar

A monorepo containing the mobile app and backend services for AgroRadar — a crop disease detection and outbreak mapping platform.

## Stack

**Mobile (`apps/mobile`)**

- Expo + Expo Router (TypeScript)
- NativeWind v5 (Tailwind v4) via `react-native-css`
- Zustand (client state) + TanStack Query (server state)
- Axios (HTTP) + Socket.IO client
- @gorhom/bottom-sheet, expo-secure-store, expo-haptics

**Backend (`apps/backend`)**

- NestJS (TypeScript)
- Prisma ORM + PostgreSQL (Neon)
- Socket.IO via `@nestjs/websockets`
- nestjs-pino (structured logging)
- Zod env validation, helmet, compression, CORS, global validation pipe

**Tooling**

- pnpm workspaces + Turborepo
- TypeScript strict mode shared via `tsconfig.base.json`
- ESLint + Prettier

## Prerequisites

- Node.js >= 20
- pnpm >= 9 (`npm i -g pnpm`)
- A Neon PostgreSQL database

## Quick start

```bash
# 1. Install all dependencies
pnpm install

# 2. Configure environment
cp apps/backend/.env.example apps/backend/.env
cp apps/mobile/.env.example apps/mobile/.env
# Edit apps/backend/.env and set DATABASE_URL (Neon connection string)

# 3. Run the initial database migration
pnpm --filter backend prisma:migrate

# 4. Start everything
pnpm dev
```

The backend runs on `http://localhost:3000` and Expo on its default Metro port.

## Workspace scripts

| Command            | Description                                      |
| ------------------ | ------------------------------------------------ |
| `pnpm dev`         | Run dev mode for all apps in parallel            |
| `pnpm build`       | Build all apps                                   |
| `pnpm lint`        | Lint all apps                                    |
| `pnpm typecheck`   | Type-check all apps                              |
| `pnpm format`      | Format the entire repo with Prettier             |
| `pnpm clean`       | Remove build artifacts and node_modules          |

Run a script for one app only:

```bash
pnpm --filter mobile dev
pnpm --filter backend start:dev
```

## Folder structure

```
.
├── apps/
│   ├── mobile/      # Expo app
│   └── backend/     # NestJS API
├── package.json     # workspace root
├── pnpm-workspace.yaml
├── turbo.json
└── tsconfig.base.json
```

See each app's README for details.
