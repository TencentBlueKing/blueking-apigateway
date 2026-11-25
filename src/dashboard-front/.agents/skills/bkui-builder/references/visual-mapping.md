# 视觉特征与组件映射规则

> 按设计稿视觉特征快速映射到本仓对应的组件与属性配置。所有模板组件统一使用 **PascalCase** 与布尔属性简写。

---

## 1. 图标映射

1. **优先使用全局 `<AgIcon>`**：本仓自定义图标与业务图标通过 `<AgIcon name="..." />` 渲染；首屏立即可见的图标优先字体模式，避免等待异步加载的 SVG 雪碧图。
2. **`bkui-vue` 内置图标**：仅从 `bkui-vue/lib/icon`（或别名 `bkui-lib/icon`）按需导入，**严禁**从 `@bkui-vue/icon` 导入。

常用 `bkui-vue/lib/icon` 导出名：
- **箭头/方向**：`AngleDown`、`AngleUp`、`AngleLeft`、`AngleRight`、`AngleDownFill`、`AngleUpFill`、`AngleDownLine`、`AngleDoubleLeft`、`AngleDoubleRight`、`DownShape`、`UpShape`、`LeftShape`、`RightShape`、`DownSmall`、`ArrowsLeft`、`ArrowsRight`
- **通用操作**：`Search`、`Plus`、`Close`、`CloseLine`、`Copy`、`CopyShape`、`Del`、`EditLine`、`Upload`、`Share`、`Transfer`、`Done`
- **文件/文档**：`Folder`、`FolderOpen`、`FolderShape`、`FolderShapeOpen`、`DocFill`、`TextFile`、`TextFill`、`Code`、`PdfFill`、`ExcelFill`、`ImageFill`、`VideoFill`、`AudioFill`、`ArchiveFill`
- **状态/提示**：`Info`、`InfoLine`、`Help`、`HelpFill`、`HelpDocumentFill`、`Warn`、`Error`、`Success`、`ExclamationCircleShape`
- **功能图标**：`CogShape`、`DataShape`、`Eye`、`Unvisible`、`Funnel`、`Ellipsis`、`Loading`、`Spinner`、`CollapseLeft`、`FixLine`、`FixShape`、`TreeApplicationShape`

```vue
<template>
  <BkMenuItem key="log-collect">
    <template #icon>
      <Search />
    </template>
    {{ t('日志采集') }}
  </BkMenuItem>
</template>

<script setup lang="ts">
import { Search } from 'bkui-vue/lib/icon';

const { t } = useI18n();
</script>
```

---

## 2. 表格特征映射

本仓列表页统一使用泛型组件 `<AgTable>`（从 `@/components/base/ag-table` 导入，完整 API 见 [AgTable 指南](../../../../src/components/base/ag-table/README.md)）：

| 视觉特征 | `<AgTable>` 配置 |
| --- | --- |
| 表头漏斗图标（筛选） | 列配置 `filter: { type: 'single' \| 'multiple', showConfirmAndReset: true, list: [{ label, value }] }` |
| 表头上下箭头（排序） | 列配置 `sorter: true` |
| 右上角齿轮（列设置） | `show-settings` + 稳定的 `cache-identifier="XxxList"` |
| 行复选框与已选提示条 | `show-selection` + `show-first-full-row` + `v-model:selected-row-keys` |
| 长文本溢出省略 | 列配置 `ellipsis: true` |
| 滑动开关列 | `cell` 中渲染 `<Switcher modelValue={row.enabled} theme="primary" size="small" onChange={...} />` |
| 操作列文字按钮 | `<Button theme="primary" text>`（编辑）/ `<Button theme="danger" text>`（删除） |

> 仅无需分页、筛选与列设置的极简静态表格才直接使用 `<BkTable>`。

---

## 3. 筛选与切换组件识别（Radio Capsule vs Tab）

| 视觉特征 | 组件 | 说明 |
| --- | --- | --- |
| 选项被边框包裹、选项间有竖线分隔（纯筛选） | `<BkRadioGroup type="capsule">` | 胶囊单选按钮组 |
| 选项下方有下划线高亮，切换不同内容面板 | `<BkTab type="unborder-card">` | 无边框 Tab（使用 `v-model:active`） |
| 选项带卡片边框，切换不同内容面板 | `<BkTab type="card">` | 卡片 Tab（使用 `v-model:active`） |

```vue
<!-- 胶囊筛选 -->
<BkRadioGroup
  v-model="activeFilter"
  type="capsule"
>
  <BkRadioButton label="all">
    {{ t('全部') }}
  </BkRadioButton>
  <BkRadioButton label="enabled">
    {{ t('启用') }}
  </BkRadioButton>
</BkRadioGroup>

<!-- Tab 切换面板：注意用 v-model:active，不是 v-model -->
<BkTab
  v-model:active="activeTab"
  type="unborder-card"
>
  <BkTabPanel
    name="basic"
    :label="t('基本信息')"
  >
    ...
  </BkTabPanel>
</BkTab>
```

---

## 4. Tag、开关、状态点与 Alert 映射

### `<BkTag>` 颜色映射

| 视觉样式 | 组件配置 | 常见场景 |
| --- | --- | --- |
| 蓝色背景 | `<BkTag theme="info">` | 系统内置、信息标识 |
| 绿色背景 | `<BkTag theme="success">` | 正常、启用、成功 |
| 橙色背景 | `<BkTag theme="warning">` | 警告、待处理 |
| 红色背景 | `<BkTag theme="danger">` | 错误、失败、危险 |
| 灰色描边 | `<BkTag type="stroke">` | 普通标签 |

### 状态指示点与开关

| 视觉特征 | 组件 | 关键属性 |
| --- | --- | --- |
| 带圆点的状态文字 | `<AgStatusDot>` | 本仓基础组件（`@/components/base/ag-status-dot/Index.vue`） |
| 圆角滑动开关（绿色） | `<BkSwitcher>` | 默认主题 |
| 圆角滑动开关（蓝色） | `<BkSwitcher theme="primary">` | 蓝色主题 |
| 方形勾选框 / 圆形单选 | `<BkCheckbox>` / `<BkRadio>` | - |

### 提示条（`<BkAlert>`）

| 视觉特征 | 组件 |
| --- | --- |
| 蓝色信息提示条 | `<BkAlert theme="info">` |
| 绿色成功提示条 | `<BkAlert theme="success">` |
| 黄色警告提示条 | `<BkAlert theme="warning">` |
| 红色错误提示条 | `<BkAlert theme="error">` |

---

## 5. 抽屉与弹窗

- **编辑/新建复杂表单**：优先使用 `<AgSideslider>`（`v-model:is-show`），保持与本仓交互一致；
- **轻量确认/简单表单**：使用 `<BkDialog v-model:is-show="visible">`；
- **二次删除确认**：使用本仓 `usePopInfoBox` 或 `InfoBox`。
