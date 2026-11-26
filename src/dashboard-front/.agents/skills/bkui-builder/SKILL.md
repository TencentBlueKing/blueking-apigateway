---
id: bkui-builder
name: bkui-builder
category: engineering
description: 蓝鲸 MagicBox 3.0 + 本仓基础组件（AgTable / AgSideslider / AgIcon / UnoCSS）页面搭建与设计稿还原规范
tags: [vue3, bkui-vue, ag-table, rules, template]
---

# 蓝鲸 MagicBox 3.0 页面搭建与设计稿还原规则

面向 `src/dashboard-front/` 的 UI 开发规则，已对齐本仓 [AGENTS.md](../../../AGENTS.md)、[vue-code-style.md](../../rules/vue-code-style.md)、[ts-style.md](../../rules/ts-style.md) 与 [AgTable 指南](../../../src/components/base/ag-table/README.md)。

## 核心约束

1. **复用既有页面布局**：本仓顶级壳层由 `App.vue` 与 `src/layout/`（`my-gateway`、`platform-tools`、`docs`、`mcp-market`、`personal-workbench`）提供，新增业务页直接接入对应路由布局，不要在页面内自建 `<BkNavigation>` 外壳。仅在新增顶级布局时使用 `<BkNavigation>`。
2. **组件选型优先级**：
   - 常规交互组件（按钮、表单、弹窗、标签、开关等）：优先使用 `bkui-vue` 组件，禁用裸原生 `<table>` / `<button>` 替代业务控件；
   - 数据表格：列表页与需分页/筛选/列设置/自适应高度的表格统一使用本仓泛型组件 `<AgTable>`（从 `@/components/base/ag-table` 导入）；仅极简静态展示表可使用 `<BkTable>`；
   - 侧滑抽屉 / 人员选择 / 图标：优先使用 `<AgSideslider>`、`<UserSelector>`（`@/components/user/user-selector/Index.vue`）与全局注册的 `<AgIcon>` / `<AgIconButton>` / `<AgCopyButton>`。
3. **严格遵循本仓 SFC 与 ESLint 规范**：
   - 块顺序：`<template>` → `<script setup lang="ts">`（含 JSX 时 `lang="tsx"`）→ `<style lang="scss" scoped>`；
   - 模板组件标签必须使用 **PascalCase**（如 `<BkButton>`、`<BkInput>`），布尔属性必须使用简写（如 `clearable`、`text`、`required`）；
   - Vue / Vue Router / `useI18n` API 已通过 `unplugin-auto-import` 自动导入，无需手动引入；
   - 所有 `interface` 必须以 `I` 开头；面向用户的文案必须使用 `t('...')` 国际化；
   - 间距与 Flex 布局优先使用 **UnoCSS 工具类**（如 `flex items-center gap-16px mb-16px`），避免手写 `mb16`/`mt20` 类名和行内 `style`，克制使用 `:deep()`。

## 还原流程

1. **分析设计稿**：识别页面归属布局、是否为列表页（`<AgTable>`）/ 详情页 / 表单向导 / 图表页，以及涉及的筛选、抽屉、状态标签和图标。
2. **按需加载本地参考资源**：

| 场景 | 本地路径 |
| --- | --- |
| 列表页（`<AgTable>` + 筛选工具栏 + 弹窗表单） | `./assets/pages/table-page.vue` |
| 概览 / 仪表盘页（卡片 + 按需 ECharts） | `./assets/pages/dashboard-page.vue` |
| 详情页（概览头 + 折叠分组） | `./assets/pages/detail-page.vue` |
| 分步表单向导 | `./assets/pages/wizard-form.vue` |
| 视觉特征与组件映射 | `./references/visual-mapping.md` |
| 常用代码片段 | `./references/code-snippets.md` |
| 交付前质量检查清单 | `./references/checklist.md` |

3. **编码与自检**：对照 `./references/checklist.md` 检查交互细节、国际化、类型和样式，再执行本仓校验命令。

## 图标使用

- 优先使用全局组件 `<AgIcon name="..." />`（首屏可见图标优先字体模式，避免依赖异步加载的 SVG 雪碧图）。
- 需要使用 `bkui-vue` 内置图标时，必须从 `bkui-vue/lib/icon`（或别名 `bkui-lib/icon`）导入：

```typescript
// 正确
import { Close, Plus, Search } from 'bkui-vue/lib/icon';
// 错误：禁止 import { Search } from '@bkui-vue/icon';
```
