# AGENTS.md

## Project Overview

BlueKing API Gateway Dashboard Frontend — a Vue 3 + TypeScript SPA for managing API gateways, resources, stages, permissions, plugins, MCP servers, and more. Part of the larger `blueking-apigateway` monorepo under `src/dashboard-front/`.

## Commands

```bash
# Development (Vite dev server on dev-t.paas3-dev.bktencent.com:8888, basic SSL enabled)
npm run dev

# Preview (uses index.dev.html)
npm run preview

# Production build (type-check + vite build, runs in parallel)
npm run build

# Build without type checking
npm run build-only

# Type checking only
npm run type-check    # vue-tsc --build

# Lint (runs oxlint then eslint sequentially)
npm run lint

# Lint individually
npm run lint:oxlint   # oxlint . --fix -D correctness --ignore-path .gitignore
npm run lint:eslint   # eslint . --fix
```

No test framework is configured — there are no unit or e2e tests.

## Architecture

### Entry & Bootstrap

- `main.ts` — Creates Vue app, installs Pinia, Vue Router, bkui-vue (full import), vue-i18n, mavon-editor, XSS filter directive, and registers global components (`AgIcon`, `IconButton`, `CopyButton`, `CardContainer`).
- `App.vue` — Root layout with `BkNavigation` (top-bottom nav), header menu, language toggle, user info. Fetches environment config and user info on route changes. Feature flags control menu visibility.
- HTML entry points: `index.dev.html` / `index.prod.html` — the `replace-index-html.js` script copies the appropriate one to `index.html` before dev/build (backs up existing `index.html`).
- Build also includes `default.html` as a secondary Rollup input (see `vite.config.ts`).

### Routing (`src/router/index.ts`)

Each feature module exports its own route factory function (e.g., `getStageManagementRoutes()`). Main structure:
- `/` — Home (gateway list)
- `/:id` — Gateway detail layout (`src/layout/my-gateway/`), children: stage-management, resource-management, basic-info, backend-services, permission, operate-data, online-debugging, audit-log, monitor-alarm, mcp-server
- `/platform-tools`, `/mcp-market`, `/components`, `/docs` — Top-level sections with their own layouts under `src/layout/`

### State Management (`src/stores/`)

Pinia stores, all re-exported from `src/stores/index.ts`:
- `useEnv` — Environment config (BK_DASHBOARD_URL, site paths)
- `useUserInfo` — Current user & tenant info
- `useFeatureFlag` — Feature flag toggles
- `useGateway` — Current gateway data (central to most views)
- `useStage`, `usePermission`, `useAccessLog`, `useAuditLog`, `useResourceVersion`, `useResourceSetting`, `useStaff`

### API Layer (`src/services/`)

- `http/index.ts` — Exports an HTTP handler with methods: `get`, `post`, `put`, `patch`, `delete`, `download`. Each call creates a `Request` instance that goes through axios with request/response middleware.
- `http/lib/request.ts` — Core request class. Supports caching, cancel tokens, upload progress, and permission-based error handling (`page` | `dialog` | `catch`).
- `source/*.ts` — ~28 service modules (gateway, resource, stage, permission, mcp-server, mcp-market, plugin-manage, etc.). Each defines API functions that call `http.get('/gateways/...', params)`.

### UI Components

Two UI libraries in use:
- **bkui-vue** (BlueKing UI) — Primary component library, fully imported
- **tdesign-vue-next** (via `@blueking/tdesign-ui`) — Used for advanced tables and some form components

Custom components in `src/components/` follow `ag-*` naming: `ag-icon`, `ag-editor`, `ag-table`, `ag-dropdown`, `ag-sideslider`, `ag-mcp-card`, etc.

### Hooks (`src/hooks/`)

Composables for common patterns (see `src/hooks/index.ts`): `use-query-list` (paginated data), `use-selection-data` (table selection), `use-table-filter-change`, `use-table-sort-change`, `use-sidebar` (drawer state), `use-gate-way-data` (gateway list with search), `use-max-table-limit` (viewport-based pagination), `use-date-picker`, `use-tdesign-selection`, `use-stage-data`, `use-text-getter`, `use-table-setting`, `use-sticky-bottom`, `use-operation-lock`, `use-mcp-config-divide-ratio`, `use-bk-user-display-name`.

### i18n (`src/locales/`)

vue-i18n with Composition API mode. Locale files live in `src/locales/cn.json` and `src/locales/en.json`, mapped to `zh-cn` (default/fallback) and `en`. Language set via `blueking_language` cookie. Use `t('key')` from the exported `t` function or `useI18n()` (auto-imported).

### Styling

- SCSS for component/global styles (`src/styles/`)
- UnoCSS with Tailwind v3 preset (`uno.config.ts`) for utility classes
- CSS class naming: kebab-case (`^[a-z][a-z0-9_-]+$`, enforced by stylelint)

## Code Style Rules

Enforced by ESLint flat config (`eslint.config.ts`) + oxlint + stylelint:

- **Semicolons required**, single quotes, 2-space indent, 120-char max line length
- **Trailing commas** in multiline (comma-dangle: always-multiline)
- **Sort imports** (declaration sort ignored, member sort enforced)
- **No duplicate imports**
- **Vue**: `<script setup>` with TypeScript. Macro order: `defineOptions` → `defineModel` → `defineProps` → `defineEmits` → `defineSlots`, `defineExpose` last. Emits declared as type-literal. Props destructuring enforced. Multi-word component names rule disabled.
- **Object/array formatting**: newlines enforced for multiline objects/arrays, consistent bracket newlines

## Commit Conventions

Conventional commits enforced by commitlint. Allowed types: `feat`, `fix`, `perf`, `style`, `docs`, `test`, `refactor`, `build`, `ci`, `chore`, `revert`, `wip`, `workflow`, `types`.

Pre-commit hook runs lint-staged (ESLint --fix on staged `.{js,jsx,ts,tsx,vue}` files).

## Path Aliases

`@` → `./src` (configured in both vite.config.ts and tsconfig.app.json). Also `bkui-lib` → `bkui-vue/lib`.

## Auto-Imports

`vue`, `vue-router`, and `useI18n` from `vue-i18n` are auto-imported via `unplugin-auto-import` — no need to explicitly import `ref`, `computed`, `watch`, `onMounted`, `useRouter`, etc. Type declarations generated at `src/types/auto-imports.d.ts`.

## Key Patterns

- **Service functions** take a base path and call `http.get(url, params, payload)`. The `payload` object can include `cache`, `timeout`, `permission` (error handling strategy), and `onUploadProgress`.
- **Views** are organized as feature modules in `src/views/<feature>/`, each with its own `route.ts` and sub-components.
- **Layouts** in `src/layout/` provide the sidebar navigation for each top-level section (my-gateway, platform-tools, mcp-market, etc.).
- **Global components** registered in `main.ts`: `AgIcon`, `IconButton`, `CopyButton`, `CardContainer` — available without import.
- **Custom element**: `<bk-user-display-name>` is treated as a custom element (not parsed as Vue component) in the Vue template compiler config.
