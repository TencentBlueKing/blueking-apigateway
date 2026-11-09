# AGENTS.md

## 项目概述

蓝鲸 API 网关管理前端（BlueKing API Gateway Dashboard Frontend）—— 基于 Vue 3 + TypeScript 的单页应用，用于管理 API
网关、资源、环境、权限、插件、MCP 服务器等。位于 `blueking-apigateway` 仓库的 `src/dashboard-front/` 目录下。

## Rules（规则/约束）

- 代码风格需要遵循 `./.agents/rules` 中配置的 rules

## Skills（可用能力/工具）

目录 `./.agents/skills` 中可以找到以下 skills：

| ID                   | 名称           | 场景               |
|----------------------|--------------|------------------|
| `bkui-builder`       | 设计稿还原专家      | UI 开发            |
| `api-standard`       | 统一网络请求       | HTTP 封装          |
| `pinia-setup`        | 全局状态管理       | Pinia            |
| `bkui-cheatsheet`    | BKUI 组件速查    | 快速参考             |
| `tapd-workitem`      | TAPD 单据查询    | 需求/缺陷/任务详情     |

## 技术栈

| 分类      | 技术                        | 版本         |
|---------|---------------------------|------------|
| 框架      | Vue 3 (Composition API)   | ^3.5       |
| 构建工具    | Vite                      | 7.3        |
| 类型系统    | TypeScript                | ~5.8       |
| 状态管理    | Pinia                     | ^3.0       |
| 路由      | Vue Router                | ^4.5       |
| 国际化     | vue-i18n (Composition 模式) | ^11.1      |
| HTTP 请求 | Axios                     | ^1.11      |
| 主 UI 库  | bkui-vue (蓝鲸 UI)          | 2.0.2-beta |
| 辅助 UI 库 | tdesign-vue-next（高级表格）    | ^1.18      |
| 原子化 CSS | UnoCSS + Tailwind v3 预设   | ^66.3      |
| 代码编辑器   | Monaco Editor             | ^0.52      |
| 图表      | ECharts                   | ^5.6       |
| 工具库     | @vueuse/*                 | ^13-14     |

## 常用命令

** 注意应首先使用 `pnpm` 执行命令，没有 `pnpm` 再使用 `npm`

```bash
# 开发（Vite 开发服务器，端口 8888，启用 SSL）
pnpm dev

# 切换到多租户环境开发，根目录要有 `.env.local.tenant` 文件
pnpm dev:tenant

# 构建（跳过类型检查），这是构建的主要方式，因为项目中有遗留的类型错误，所以跳过类型检查
pnpm build-only

# 仅类型检查
pnpm type-check    # vue-tsc --build

# 代码检查
pnpm lint:eslint

# 预览生产构建
pnpm preview
```

> **注意：项目未配置测试框架，没有单元测试或 E2E 测试。**

## 目录结构

```
src/dashboard-front/
├── bin/                        # 构建脚本（nginx 配置、Docker 入口脚本）
├── public/                     # 静态资源
├── src/
│   ├── App.vue                 # 根布局（BkNavigation 导航、菜单、用户信息）
│   ├── main.ts                 # 应用入口（安装 Pinia、Router、bkui-vue、i18n、指令）
│   ├── components/             # 跨模块复用的自定义组件
│   │   ├── base/               # 与业务无关的基础组件（ag- 前缀）
│   │   ├── user/               # 人员选择与成员编辑
│   │   ├── ai/                 # AI 助手入口与对话侧栏
│   │   ├── release/            # 生成资源版本、发布、发布事件与版本对比
│   │   ├── mcp/                # MCP Server 卡片、接入配置、调用链
│   │   └── plugin/             # 插件管理（plugin-manage）与插件表单（plugin-form）
│   ├── constants/              # 常量定义（插件示例、HTTP 头等）
│   ├── directives/             # 自定义指令（clickOutSide、bkTooltips）
│   ├── enums/                  # TypeScript 枚举
│   ├── hooks/                  # 19 个组合式函数
│   ├── images/                 # Logo 和图片资源
│   ├── layout/                 # 5 个布局组件（my-gateway、platform-tools 等）
│   ├── locales/                # 国际化翻译（cn.json、en.json）
│   ├── router/                 # 路由定义，15 个功能模块
│   ├── services/
│   │   ├── http/               # Axios 封装（缓存、CSRF、中间件）
│   │   ├── source/             # API 接口函数，按作用域分目录（见「API 服务层」）
│   │   └── types/              # 接口出入参类型（query / body / responses）
│   ├── stores/                 # 11 个 Pinia Store
│   ├── styles/                 # 全局 SCSS 样式
│   ├── types/                  # 领域类型与视图类型（见「类型系统」）
│   ├── utils/                  # 26 个工具函数
│   └── views/                  # 15 个功能视图模块
├── .env                        # 环境变量模板
├── .env.local                  # 本地开发环境覆盖
├── eslint.config.ts            # ESLint 9 扁平化配置
├── stylelint.config.js         # SCSS/CSS 检查
├── tsconfig.json               # TypeScript 配置入口
├── uno.config.ts               # UnoCSS 配置
├── vite.config.ts              # Vite 配置
├── Dockerfile                  # 多阶段构建（Node 20 → Nginx）
└── package.json                # 依赖与脚本
```

## 架构说明

### 入口与引导

- **`main.ts`** — 创建 Vue 应用，安装 Pinia、Vue Router、bkui-vue（全量引入）、vue-i18n、XSS 过滤指令，注册全局组件 `AgIcon`、
  `AgIconButton`、`AgCopyButton`。
- **`App.vue`** — 根布局，使用 `BkNavigation`（上下导航），包含顶部菜单、语言切换、帮助菜单、用户信息（头部组件位于 `src/layout/app-header/`）。路由变化时获取环境配置和用户信息，通过
  Feature Flag 控制菜单显隐。

### 路由 (`src/router/index.ts`)

每个功能模块导出自己的路由工厂函数（如 `getStageManagementRoutes()`）。主要结构：

| 路径                         | 说明                               |
|----------------------------|----------------------------------|
| `/`                        | 首页（网关列表）                         |
| `/:id`                     | 网关详情布局（`src/layout/my-gateway/`） |
| `/:id/stage-management`    | 环境管理                             |
| `/:id/resource-management` | 资源管理                             |
| `/:id/basic-info`          | 基本信息                             |
| `/:id/backend-services`    | 后端服务                             |
| `/:id/permission`          | 权限管理                             |
| `/:id/operate-data`        | 运营数据                             |
| `/:id/online-debugging`    | 在线调试                             |
| `/:id/audit-log`           | 审计日志                             |
| `/:id/monitor-alarm`       | 监控告警                             |
| `/:id/mcp-server`          | MCP 服务器                          |
| `/platform-tools`          | 平台工具                             |
| `/mcp-market`              | MCP 市场                           |
| `/docs`                    | API 文档                           |

路由使用 `createWebHistory(window.BK_SITE_PATH)` 模式，支持自定义基础路径。

### 状态管理 (`src/stores/`)

基于 Pinia，所有 Store 从 `src/stores/index.ts` 统一导出：

| Store                | 说明                           |
|----------------------|------------------------------|
| `useGateway`         | 当前网关数据（**核心 Store**，大多数视图依赖） |
| `useEnv`             | 环境配置（BK_DASHBOARD_URL、站点路径）  |
| `useUserInfo`        | 当前用户和租户信息                    |
| `useFeatureFlag`     | 功能开关                         |
| `useStage`           | 环境/阶段状态                      |
| `usePermission`      | 权限相关状态                       |
| `useAccessLog`       | 访问日志                         |
| `useAuditLog`        | 审计日志                         |
| `useResourceVersion` | 资源版本                         |
| `useResourceSetting` | 资源配置                         |
| `useStaff`           | 人员管理                         |

### API 服务层 (`src/services/`)

**HTTP 封装** (`http/index.ts`)：

```typescript
// 导出方法：get, post, put, patch, delete, download
// 每次调用创建 Request 实例，经过 Axios 中间件处理
http.get<T>(url, params ?, payload ?):Promise<T>
```

**请求类** (`http/lib/request.ts`)：

- 支持 GET 请求缓存（可配置 TTL）
- 自动注入 CSRF Token（从 Cookie 获取）
- 取消令牌（中断进行中的请求）
- 错误处理策略：`page`（页面级）| `dialog`（弹窗）| `catch`（调用方捕获）
- 上传进度回调

**接口模块** (`source/`)：按接口作用域分目录，`gateway/` 下的文件大体按后端 `apis/web/<module>` 划分（下划线改为短横线）：

```
services/source/
├── platform/            # 平台级接口：account（用户信息）、setting（功能开关、环境变量）、version-log、
│                        #   toolbox（工具箱按请求 ID 查询日志，无需网关权限）
├── external/            # 第三方系统（URL 来自环境变量）：bk-user（用户管理）、chat（拉群、发消息）
├── me/                  # 当前用户：application（可管理的应用）、workbench（个人工作台）
├── gateway/             # /gateways/ 及 /gateways/:id/*
│   ├── gateway.ts       # 网关 CRUD、状态、名称校验、操作指引、发布状态
│   ├── member.ts        # 成员管理、当前用户在网关中的角色
│   ├── label.ts         # 标签
│   ├── stage.ts         # 环境、环境变量、环境后端
│   ├── backend.ts       # 后端服务
│   ├── resource.ts      # 资源 CRUD、导入导出、路径冲突、后端地址校验
│   ├── resource-doc.ts  # 资源文档、文档导入导出
│   ├── resource-version.ts
│   ├── release.ts       # 发布、发布历史、已发布资源及 schema
│   ├── programmable.ts  # 可编程网关部署
│   ├── plugin.ts / permission.ts / sdk.ts / monitor.ts / audit.ts / ai.ts
│   ├── api-test.ts      # 在线调试
│   ├── access-log.ts    # 流水日志（含导出）
│   ├── metrics.ts       # 仪表盘指标、统计报表
│   └── mcp-server/      # server（MCP Server 本体）、permission（应用权限）、log（日志与调用链）、metrics
├── docs/                # /docs/*：gateway（网关文档、网关 SDK 文档）、esb（组件文档）
└── mcp-marketplace.ts   # /mcp-marketplace/*
```

新增接口的规范见「新增 API 服务函数」。

### 组件 (`src/components/`)

- **`base/`**：与业务无关的基础组件，统一使用 `ag-` 前缀，不调用业务接口。包括 `ag-icon`、`ag-icon-button`、
  `ag-copy-button`、`ag-table`、`ag-table-empty`、`ag-sideslider`、`ag-dropdown`、`ag-code-editor`（Monaco）、
  `ag-markdown-editor`（mavon-editor 懒加载）、`ag-markdown-viewer`、`ag-expandable-text`、`ag-status-dot`、`ag-overflow-tags`
- **命名**：目录名使用 kebab-case 并与组件名一致，入口为 `Index.vue`；私有子组件放在该目录的 `components/` 下，
  文件名使用 PascalCase。`ag-` 前缀只用于 `base/`，业务组件使用领域名词命名
- **`user/`**：`user-selector`（人员选择入口，按多租户模式切换 `BkUserSelector` / `staff-selector`，
  v-model 统一为用户名数组）、`staff-selector`（非多租户人员选择，TSX）、`tenant-user-editor`（多租户成员的展示与行内编辑）。
  新增人员选择优先使用 `user-selector`，不要在页面里自行判断 `isTenantMode` 切换两种选择器
- **`ai/`**：`ai-blueking-button`（「问问 AI」入口）、`ai-chat-slider`（AI 对话侧栏）
- **`release/`**：`create-resource-version-slider`、`release-stage-slider`、`publish-event-slider`、`version-diff`，
  由资源管理、环境管理和网关布局共用
- **`mcp/`**：`mcp-server-card`、`mcp-server-toolbar`、`mcp-access-config`、`mcp-access-config-dialog`、
  `mcp-trace-chain`，以及调用链瀑布图模块 `trace-view`（TSX）。`trace-view` 外部只能引用其入口
  `@/components/mcp/trace-view`；`useTrace` Store 与页面需要的瀑布树转换、折叠分组、耗时格式化放在 `@/utils/trace`，
  默认调用链数据 `DEFAULT_TRACE_DATA` 放在 `@/constants/trace`，类型放在 `@/types/trace`，组件内部也从这些位置引用
- **`plugin/`**：`plugin-manage`（插件展示与管理，结构见其 README）、`plugin-form`（15+ 插件专用表单，按插件 code 分目录）
- **全局组件**（在 `main.ts` 注册，无需导入直接使用）：`AgIcon`、`AgIconButton`、`AgCopyButton`
- **放置原则**：`src/components/` 只放被两个及以上功能模块（`views/<模块>`、`layout/<布局>`）复用的组件；
  只被一个模块使用的组件放在该模块的 `components/` 下，只被 `App.vue` 使用的放在 `src/layout/app-header/`。

### 组合式函数 (`src/hooks/`)

| Hook                        | 说明              |
|-----------------------------|-----------------|
| `use-query-list`            | 分页列表查询（含查询参数管理） |
| `use-selection-data`        | 表格选择状态          |
| `use-sidebar`               | 抽屉/侧边栏状态        |
| `use-gate-way-data`         | 网关列表（含搜索）       |
| `use-max-table-limit`       | 视窗自适应分页         |
| `use-date-picker`           | 日期范围选择          |
| `use-tdesign-selection`     | TDesign 表格选择    |
| `use-table-filter-change`   | TDesign 筛选逻辑    |
| `use-table-sort-change`     | TDesign 排序逻辑    |
| `use-stage-data`            | 环境数据状态          |
| `use-text-getter`           | 文本内容获取          |
| `use-table-setting`         | 表格列显隐控制         |
| `use-sticky-bottom`         | 粘性底部            |
| `use-operation-lock`        | 防止并发操作          |
| `use-bk-user-display-name`  | 多租户用户名显示        |
| `use-chart-interval-option` | 图表时间范围          |
| `use-pop-info-box`          | 弹出信息框           |
| `use-bk-user-selector`      | 用户选择器           |

### 国际化 (`src/locales/`)

```typescript
// vue-i18n Composition API 模式
// 语言文件：cn.json (zh-cn，默认), en.json (en)
// 语言由 Cookie `blueking_language` 决定，默认 zh-cn

// 使用方式：
t('key')                    // 直接使用导出的 t 函数
const { t } = useI18n();   // 组合式 API（自动导入）
{
  {
    t('key')
  }
}              // 模板中使用
```

### 样式系统

- **SCSS**：全局样式在 `src/styles/`（base、flex、bkui 覆盖等）
- **UnoCSS + Tailwind v3 预设**：原子化 CSS 工具类（如 `flex items-center gap-16px`）
- **CSS 命名规范**：kebab-case（`^[a-z][a-z0-9_-]+$`，由 stylelint 强制）

### 类型系统

类型按用途分三处存放：

| 位置                                  | 内容                                                                |
|-------------------------------------|-------------------------------------------------------------------|
| `services/source/**`                | 只保留接口签名用到的入参类型（如 `IAuthData`、`IObservabilitySearchParams`）          |
| `services/types/{query,body,responses}/` | 接口出入参类型，按后端 URL 命名（如 `IGatewaysStagesListQuery`、`IStageListOutput`） |
| `src/types/`                        | 领域类型与视图类型，供多个页面、组件、Store 复用                                       |

`src/types/` 文件：

- `common.ts` — 通用类型（IPagination、IDialog、ITableMethod，以及资源导出参数 `IExportParams` 等）
- `gateway.ts` — 网关（Gateway、IApiGateway 等）
- `permission.ts` — 权限（含应用权限导出参数 `IPermissionExportParams`）
- `resource.ts` / `resource-version.ts` — 资源、资源版本（IVersionItem、IDiffData）
- `stage.ts` — 环境（IStageListItem）
- `backend.ts` — 后端服务（IHealthCheck）
- `programmable.ts` — 可编程网关部署事件（IEventResponse 等）
- `access-log.ts` / `audit-log.ts` / `monitor.ts` — 流水日志、操作记录、监控告警
- `metrics.ts` — 指标图表的公共结构（ISeriesItemType、IChartSeries、IInstantValue），以及网关仪表盘、统计报表的类型
- `observability.ts` — MCP Server 可观测：图表数据，以及日志与调用链（ITraceLog、ISpan、ITraceDetail 等）
- `trace.ts` — 调用链瀑布图的数据模型（ISpan、ITraceTree、ITraceListItem、ISpanListItem 等），由 `useTrace` 与
  `components/mcp/trace-view` 共用
- `mcp-server.ts` / `mcp-marketplace.ts` — MCP Server、MCP 市场
- `auto-imports.d.ts` — 由 unplugin-auto-import 自动生成

> `metrics.ts` 与 `observability.ts` 都导出 `IStatisticsType`、`IChartDataType`、`IChartDataLoading`，但字段不同：
> 网关仪表盘用前者，MCP Server 可观测用后者。
>
> `observability.ts` 与 `trace.ts` 都导出 `ISpan`：前者是接口返回的 span，后者在其基础上补充瀑布图需要的层级、
> 折叠、标签等字段。

## 代码风格规范

由 ESLint 9 扁平化配置 + oxlint + stylelint 强制执行：

### 通用规则

| 规则       | 要求                                            |
|----------|-----------------------------------------------|
| 分号       | **必须**（`semi: 'always'`）                      |
| 引号       | **单引号**（`quotes: 'single'`）                   |
| 缩进       | **2 空格**                                      |
| 行宽       | **120 字符**（注释、URL、字符串、模板字符串、正则除外）             |
| 尾逗号      | **多行时必须**（`comma-dangle: 'always-multiline'`） |
| 导入排序     | **强制**（声明排序忽略，成员排序强制）                         |
| 重复导入     | **禁止**                                        |
| `any` 类型 | 允许（`no-explicit-any: 'off'`）                  |

### 对象/数组格式化

- 多行对象属性必须换行（`object-property-newline`）
- 花括号换行规则（`object-curly-newline: multiline`）
- `curly-newline: 'always'`
- 数组方括号换行保持一致（`array-bracket-newline: 'consistent'`）

### Vue 规则

| 规则          | 要求                                                                                                   |
|-------------|------------------------------------------------------------------------------------------------------|
| 脚本语法        | 必须使用 `<script lang="ts" setup>`                                                                      |
| 宏顺序         | `defineOptions` → `defineModel` → `defineProps` → `defineEmits` → `defineSlots`，`defineExpose` 必须在最后 |
| Emits 声明    | 必须使用**类型字面量** (`type-literal`)                                                                       |
| Props 解构    | **强制**                                                                                               |
| 多词组件名       | **已关闭**（`ag-*` 前缀组件不需要）                                                                              |
| 根级 v-if     | **禁止**                                                                                               |
| 未使用的 emit   | **禁止**                                                                                               |
| 未使用的 ref    | **禁止**                                                                                               |
| 组件标签大小写     | PascalCase（`component-name-in-template-casing`）                                                      |
| 块间空行        | **必须**（`padding-line-between-blocks`）                                                                |
| 静态 class 分离 | **强制**（`prefer-separate-static-class`）                                                               |
| 布尔属性简写      | **强制**（`prefer-true-attribute-shorthand`）                                                            |

## 路径别名

| 别名         | 实际路径           |
|------------|----------------|
| `@`        | `./src`        |
| `bkui-lib` | `bkui-vue/lib` |

在 `vite.config.ts` 和 `tsconfig.app.json` 中同步配置。

## 自动导入

通过 `unplugin-auto-import` 插件，以下 API **无需手动导入**即可直接使用：

- **Vue**：`ref`、`reactive`、`computed`、`watch`、`watchEffect`、`onMounted`、`onUnmounted`、`nextTick` 等
- **Vue Router**：`useRouter`、`useRoute`
- **vue-i18n**：`useI18n`

类型声明自动生成于 `src/types/auto-imports.d.ts`。

## 关键开发模式

### 新增 Vue 组件

```vue

<template>
  <div class="my-component">
    <!-- 使用 PascalCase 引用组件 -->
    <BkButton theme="primary" @click="handleClick">
      {{ t('common.confirm') }}
    </BkButton>
  </div>
</template>

<script lang="ts" setup>
  // ref, computed, useRouter, useI18n 等已自动导入，无需手动引入
  const { t } = useI18n();
  const router = useRouter();

  // 宏顺序：defineProps → defineEmits，defineExpose 在最后
  // 用对象结构式声明 Props 及其默认值
  const {
    id,
    name = 'unknown user'
  } = defineProps<{
    id: number;
    name: stirng;
  }>();

  const emit = defineEmits<{
    update: [value: string];
  }>();

  const loading = ref(false);

  const computedData = computed(() => {
    // ...
  });

  onMounted(() => {
    // ...
  });
</script>

<style lang="scss" scoped>
  .my-component {
    // ...
  }
</style>
```

### 新增 API 服务函数

规范：

- **放置位置**：按 URL 前缀放入「API 服务层」中对应的文件。同一个后端接口只定义一次，各页面复用；例如环境列表统一使用
  `gateway/stage.ts` 的 `getStageList`，不要在页面所属模块里重复定义。
- **网关 ID**：作为第一个参数，命名为 `gatewayId: number`。
- **函数命名**：列表 `get{X}List`、详情 `get{X}Detail`、新建 `create{X}`、更新 `update{X}`（PUT）/ `patch{X}`（PATCH）、
  删除 `delete{X}`、批量 `batch{Action}{X}`、导出 `export{X}`、校验 `check{X}`；不要使用 `fetch`、`Apigw` 前缀。
  审批、撤销这类动作接口（POST 到 `.../approval/`、`.../cancel/` 等子路径）按动作语义命名，如 `cancelGatewayApplied`。
  存量代码中还有部分列表、详情接口没有按 `get{X}List` / `get{X}Detail` 命名（如 `getServers`、`getServer`、
  `getReleaseHistories`），新增接口按规范命名即可。
- **写法**：使用箭头函数直接返回 `http.xxx<T>()`，不写 `async`/`await`，GET 请求必须通过泛型声明返回类型；
  统一从 `@/services/http` 引入 `http`；每个文件用 `const path = '/gateways'` 这类常量定义 URL 前缀，不要在函数里写死。
- **参数**：查询参数通过 `params` 传递，不要手动拼接查询串。params 无法表达的检索串（如重复出现的 `include` / `exclude`）
  用 `@/services/http` 导出的 `withExtraQuery(url, extraStr)` 追加，它会在检索串为空时原样返回地址。
  注意 `http.delete` 会把 params 放进请求体；如果后端从查询串读取参数，需要拼在 URL 上（参考 `gateway/permission.ts` 的
  `deleteApiPermission`）。
- **类型**：接口文件只放接口函数和签名用到的入参类型，其余类型按「类型系统」放到 `services/types/` 或 `src/types/`。
- **无副作用**：不要修改调用方传入的对象，也不要在接口函数里触发下载。`application/octet-stream` 响应由
  `http/middleware/response.ts` 统一下载，调用方 `await` 之后提示结果即可。

```typescript
// src/services/source/gateway/xxx.ts
import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type { IXxxListOutput } from '@/services/types/responses/gateways.ts';
import type { IGatewaysXxxListQuery } from '@/services/types/query/gateways.ts';
import type { IXxxInputSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 获取 xxx 列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getXxxList = (gatewayId: number, params: IGatewaysXxxListQuery = {}) =>
  http.get<ICountAndResults<IXxxListOutput>>(`${path}/${gatewayId}/xxx/`, params);

/**
 * 新建 xxx
 * @param gatewayId 网关id
 * @param data 新建参数
 */
export const createXxx = (gatewayId: number, data: IXxxInputSLZ) =>
  http.post(`${path}/${gatewayId}/xxx/`, data);
```

### 新增 Pinia Store

```typescript
// src/stores/xxx.ts
import { defineStore } from 'pinia';

export const useXxx = defineStore('xxx', {
  state: () => ({
    list: [] as XxxItem[],
  }),
  getters: {
    filteredList: (state) => state.list.filter(/* ... */),
  },
  actions: {
    async fetchList(gatewayId: number) {
      this.list = await getXxxList(gatewayId, {});
    },
  },
});
```

### 新增组合式函数 (Hook)

```typescript
// src/hooks/use-xxx.ts
export const useXxx = (fetchFn: () => Promise<any[]>) => {
  const list = ref<any[]>([]);
  const loading = ref(false);

  const fetchData = async () => {
    loading.value = true;
    try {
      list.value = await fetchFn();
    } finally {
      loading.value = false;
    }
  };

  return { list, loading, fetchData };
};
```

### 新增路由模块

```typescript
// src/views/xxx/route.ts
export function getXxxRoutes() {
  return [
    {
      path: 'xxx',
      name: 'xxx',
      component: () => import('./index.vue'),
    },
  ];
}
```

然后在 `src/router/index.ts` 中引入并注册。

### 新增国际化文本

* 通常要展示的中文文本就是 key

在 `src/locales/cn.json` 和 `src/locales/en.json` 中同时添加对应 key：

```json
// cn.json
{
  "标题": "标题",
  "描述": "描述"
}

// en.json
{
  "标题": "Title",
  "描述": "Description"
}
```

## 提交规范

使用 Conventional Commits，由 commitlint 强制检查。允许的类型：

`feat`、`fix`、`perf`、`style`、`docs`、`test`、`refactor`、`build`、`ci`、`chore`、`revert`、`wip`、`workflow`、`types`

格式：`<type>(<scope>): <subject>`

示例：

```
feat(resource): 新增资源批量导入功能
fix(permission): 修复权限列表分页异常
refactor(hooks): 重构 use-query-list 支持自定义排序
```

Pre-commit 钩子自动对暂存的 `.{js,jsx,ts,tsx,vue}` 文件执行 `eslint --fix`。

## 应忽视的目录

* `public/bk_icon_font` ，这里防止静态的图标字体文件，不需要做任何分析和变更

## 注意事项

1. **bkui-vue 为主 UI 库**：表单、按钮、弹窗、导航等优先使用 bkui-vue 组件；仅在需要高级表格功能时使用 tdesign-vue-next。
2. **自定义元素**：`<bk-user-display-name>` 被配置为自定义元素（非 Vue 组件），不会被 Vue 模板编译器解析。
3. **环境变量**：Vite 构建时变量以 `VITE_` 为前缀；运行时全局变量通过 `window.BK_DASHBOARD_URL` 等方式访问。
4. **错误处理**：API 调用的 `payload` 参数可指定 `permission` 字段控制错误处理策略（`page`、`dialog`、`catch`）。
5. **缓存**：仅 GET 请求支持缓存，通过 `payload.cache` 传入 TTL（毫秒）。
   **文件下载**：后端返回 `application/octet-stream` 时，响应拦截器自动下载文件，此时 `http` 的返回值为 `undefined`；
   导出类接口需传 `responseType: 'blob'`，通常配合 `catchError: true` 由调用方处理错误（错误响应体为 Blob）。
6. **Feature Flag**：通过 `useFeatureFlag` Store 管理功能开关，控制菜单和功能的显隐。
