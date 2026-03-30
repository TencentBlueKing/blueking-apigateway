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
│   ├── components/             # 60+ 自定义组件
│   │   ├── ag-*/               # ag- 前缀可复用组件
│   │   ├── plugin-form/        # 15+ 插件配置表单
│   │   └── plugin-manage/      # 插件管理 UI
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
│   │   ├── source/             # ~28 个 API 服务模块
│   │   └── types/              # HTTP 响应类型
│   ├── stores/                 # 11 个 Pinia Store
│   ├── styles/                 # 全局 SCSS 样式
│   ├── types/                  # TypeScript 接口/类型定义
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
  `IconButton`、`CopyButton`、`CardContainer`。
- **`App.vue`** — 根布局，使用 `BkNavigation`（上下导航），包含顶部菜单、语言切换、用户信息。路由变化时获取环境配置和用户信息，通过
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
| `/components`              | 组件管理                             |
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

**API 服务模块** (`source/*.ts`)：约 28 个模块，每个导出带类型的函数：

```typescript
// 示例：services/source/resource.ts
export async function getResourceList(apigwId: number, params: {}) {
  return await http.get(`/gateways/${apigwId}/resources/`, params);
}
```

主要模块包括：`gateway`、`resource`、`stage`、`permission`、`mcp-server`、`mcp-market`、`plugin-manage`、`online-debugging`、
`audit-log`、`access-log`、`monitor`、`backend-services`、`ai`、`docs` 等。

### 组件 (`src/components/`)

- **`ag-*` 前缀组件**：可复用自定义组件（ag-icon、ag-editor、ag-table、ag-dropdown、ag-sideslider、ag-mcp-card 等）
- **`plugin-form/`**：15+ 插件配置表单（cors、rate-limit、ip-restriction、header-rewrite、api-breaker 等）
- **`plugin-manage/`**：插件展示与管理 UI
- **TSX 组件**：`member-selector`、`table-header-filter`、`custom-table-header-filter` 等
- **全局组件**（在 `main.ts` 注册，无需导入直接使用）：`AgIcon`、`IconButton`、`CopyButton`、`CardContainer`

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

### 类型系统 (`src/types/`)

- `common.ts` — 通用类型（IPagination、IDialog、ITableMethod 等）
- `gateway.ts` — 网关相关类型（Gateway、GatewayListItem 等）
- `permission.ts` — 权限类型
- `resource.ts` — 资源类型
- `auto-imports.d.ts` — 由 unplugin-auto-import 自动生成

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

```typescript
// src/services/source/xxx.ts
import http from '../http';

// 接口函数直接调用 http 方法，返回类型通过泛型指定
export async function getXxxList(apigwId: number, params: Record<string, any>) {
  return await http.get<XxxListResponse>(`/gateways/${apigwId}/xxx/`, params);
}

export async function createXxx(apigwId: number, data: CreateXxxParams) {
  return await http.post(`/gateways/${apigwId}/xxx/`, data);
}
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
    async fetchList(apigwId: number) {
      this.list = await getXxxList(apigwId, {});
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
6. **Feature Flag**：通过 `useFeatureFlag` Store 管理功能开关，控制菜单和功能的显隐。
