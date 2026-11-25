# 设计稿还原检查清单 (Quality Checklist)

> 编写或改造页面后，逐项核对视觉还原与本仓规范。

## 1. 布局与组件选型

- [ ] **复用既有布局**：业务页接入 `src/layout/` 中对应布局，未重复嵌套 `<BkNavigation>`
- [ ] **组件标签规范**：模板内全部使用 PascalCase（如 `<BkButton>`、`<AgTable>`），无 kebab-case 组件标签
- [ ] **布尔属性简写**：使用 `clearable`、`text`、`required`、`show-settings`，未写 `:xxx="true"`
- [ ] **列表表格选型**：带分页/筛选/列设置/自适应高度的表格使用 `@/components/base/ag-table` 的 `<AgTable>`，传入稳定的 `cache-identifier`
- [ ] **抽屉与人员选择**：侧滑抽屉优先 `<AgSideslider>`，人员选择统一使用 `<UserSelector>`（不自行判断 `isTenantMode`）

## 2. 工具栏与筛选

- [ ] **左侧操作区**：新建等主按钮在左侧，使用 `<BkButton theme="primary">`
- [ ] **右侧筛选区**：胶囊切换（`<BkRadioGroup type="capsule">`）/ Tab + 搜索框在右侧，使用 UnoCSS（如 `flex items-center justify-between gap-16px mb-16px`）
- [ ] **搜索框图标**：使用 `#suffix` 插槽放置 `bkui-vue/lib/icon` 的 `<Search />` 或 `<AgIcon>`（**禁止**从 `@bkui-vue/icon` 导入）
- [ ] **日期范围筛选**：列表日期筛选复用 `useDatePicker`，查询前调用 `applySelectedRange()`；禁止使用 `new Date(文本)` 解析

## 3. 表格与操作列

- [ ] **泛型与类型**：列定义使用 `ITableColumn<IRow>[]` 或 `defineTableColumns<IRow>([...])`，表格引用使用 `useTemplateRef<IAgTableInstance<IRow>>('tableRef')`
- [ ] **列筛选/排序/设置**：按 [AgTable 指南](../../../../src/components/base/ag-table/README.md) 配置 `filter`、`sorter`、`show-settings` 与 `cache-identifier`
- [ ] **操作列按钮**：文字操作按钮使用 `<BkButton theme="primary" text>` / `<BkButton theme="danger" text>`
- [ ] **状态切换**：表格内开关（`<BkSwitcher>`）优先使用受控 `:model-value` + `@change`（接口失败易回滚），避免直接双向修改行对象字段
- [ ] **溢出省略**：长文本开启 `ellipsis: true`，自定义单元格溢出提示复用 `AgTable` 的 `handleCellEnter` / `handleCellLeave`

## 4. 状态、图表与安全

- [ ] **状态标签**：按语义选用 `<BkTag theme="info | success | warning | danger">` 或 `<AgStatusDot>`
- [ ] **空态与加载**：`<AgTable>` 内置空态/错误态；非表格区域使用 `<BkException>` 与 `<BkLoading>` / `v-bkloading`
- [ ] **图表按需引入**：使用 `@/utils/echarts` 的 `createChart`，卸载时 `dispose()`，禁止 `import * as echarts from 'echarts'`
- [ ] **XSS 安全**：不直接用 `v-html` 渲染不可信内容，必要时使用 `v-xss` 指令或做清洗
- [ ] **国际化**：所有可见文案使用 `t('...')`，并同步维护 `src/locales/cn.json` 与 `src/locales/en.json`（参考 `i18n-maintainer`）

## 5. 样式与代码质量

- [ ] **SFC 结构**：顺序为 `<template>` → `<script setup lang="ts|tsx">` → `<style lang="scss" scoped>`
- [ ] **样式规范**：优先 UnoCSS 原子类；自定义类使用 kebab-case 且采用类选择器，克制 `:deep()`，避免 `!important`
- [ ] **类型命名**：所有 `interface` 以 `I` 开头，新增代码避免 `any`
- [ ] **校验通过**：执行 `pnpm type-check`、`pnpm lint:ci:oxlint`、`pnpm lint:ci`
