# Backend — AgroRadar API

NestJS API with Prisma + Postgres (Neon), Socket.IO, and pino logging.

## Setup

```bash
cp .env.example .env
# Fill DATABASE_URL with your Neon connection string

pnpm install
pnpm prisma:generate
pnpm prisma:migrate
pnpm dev
```

## Scripts

- `pnpm dev` — start in watch mode
- `pnpm build` — compile TypeScript to `dist/`
- `pnpm start:prod` — run compiled output
- `pnpm prisma:generate` — generate Prisma Client
- `pnpm prisma:migrate` — apply migrations in dev mode
- `pnpm prisma:studio` — open Prisma Studio
- `pnpm lint`, `pnpm typecheck`

## Endpoints

| Method | Path     | Description                          |
| ------ | -------- | ------------------------------------ |
| GET    | /health  | Liveness + DB connectivity check     |

Socket.IO is exposed on the same origin (default `ws://localhost:3000`).

## Folder structure

```
src/
├── common/         # filters, interceptors, decorators, guards
├── config/         # Zod env validation + config module
├── modules/
│   ├── prisma/     # PrismaService (lifecycle + healthCheck)
│   ├── health/     # GET /health
│   ├── users/      # UsersService scaffold
│   ├── auth/       # auth scaffold (JWT strategy stub)
│   └── realtime/   # Socket.IO gateway
├── types/
├── app.module.ts
└── main.ts
```
