# 视觉特征映射规则

> 按需加载，用于精确还原设计稿细节

---

## 0. 主题识别（优先判断）

### 深色主题 vs 浅色主题

| 视觉特征 | 深色主题 | 浅色主题 |
|---------|---------|---------|
| **侧边栏背景** | 深蓝黑 (#1a1a2e ~ #2c2c3e) | 白色/浅灰 |
| **顶部导航** | 深色背景 (#2c2c3e) | 白色背景 |
| **表格背景** | 深灰 (#2c2c3e) | 白色 |
| **文字颜色** | 浅色 (rgba(255,255,255,0.8)) | 深色 (#63656e) |

**深色侧边栏 CSS（必须添加）：**
```css
.admin-layout--dark :deep(.bk-navigation) {
  --bk-navigation-bg-color: #1a1a2e;
}
.admin-layout--dark :deep(.bk-menu) {
  --menu-bg-color: transparent;
  --menu-text-color: rgba(255,255,255,0.8);
  --menu-active-bg-color: rgba(58,132,255,0.2);
  --menu-active-text-color: #fff;
}
.admin-layout--dark :deep(.bk-table) {
  --table-bg-color: #2c2c3e;
  --table-header-bg-color: #252535;
}
```

---

## 1. 菜单图标

当菜单项左侧有图标时，使用 `#icon` 插槽：

```vue
<script setup>
// ⚠️ 正确导入方式 - 只能从 bkui-vue/lib/icon 导入
import { Search, Plus, Close, Edit, Delete, Setting } from 'bkui-vue/lib/icon';
</script>

<template>
  <bk-menu-item key="log-collect">
    <template #icon><Search /></template>
    日志采集
  </bk-menu-item>
</template>
```

### 可用图标列表（从源码提取）

**箭头/方向：**
`AngleDown`, `AngleUp`, `AngleLeft`, `AngleRight`, `AngleDownFill`, `AngleUpFill`, `AngleDownLine`, `AngleDoubleLeft`, `AngleDoubleRight`, `DownShape`, `UpShape`, `LeftShape`, `RightShape`, `DownSmall`, `ArrowsLeft`, `ArrowsRight`

**通用操作：**
`Search`, `Plus`, `Close`, `CloseLine`, `Copy`, `CopyShape`, `Del`, `EditLine`, `Upload`, `Share`, `Transfer`, `Done`

**文件/文档：**
`Folder`, `FolderOpen`, `FolderShape`, `FolderShapeOpen`, `DocFill`, `TextFile`, `TextFill`, `Code`, `PdfFill`, `ExcelFill`, `ImageFill`, `VideoFill`, `AudioFill`, `ArchiveFill`

**状态/提示：**
`Info`, `InfoLine`, `Help`, `HelpFill`, `HelpDocumentFill`, `Warn`, `Error`, `Success`, `ExclamationCircleShape`

**功能图标：**
`CogShape`, `DataShape`, `Eye`, `Unvisible`, `Funnel`, `Ellipsis`, `Loading`, `Spinner`, `CollapseLeft`, `FixLine`, `FixShape`, `TreeApplicationShape`

**完整导入示例：**
```typescript
import { Search, Plus, Close, CogShape, FolderOpen, Funnel, EditLine, Del, Help } from 'bkui-vue/lib/icon';
```

> ⚠️ CSS 类名备选：`<i class="bk-icon icon-search"></i>`
> ❌ 错误路径：`import { X } from '@bkui-vue/icon'`

---

## 2. 表格列特征

| 表头特征 | 列配置 |
|---------|-------|
| 漏斗图标 (筛选) | `filter: { list: [{ text, value }] }` |
| 箭头图标 (排序) | `sort: true` 或 `sort: { value: 'desc' }` |
| 齿轮图标 (设置) | 表格属性 `:settings="true"` |

### 表格操作列

| 视觉特征 | 组件 | 代码 |
|---------|-----|------|
| **蓝色/绿色滑动开关** | `<bk-switcher>` | `<template #enabled="{ row }"><bk-switcher v-model="row.enabled" /></template>` |
| **"编辑" 文字链接** | `<bk-button text>` | `<bk-button theme="primary" text>编辑</bk-button>` |
| **"删除" 文字链接（红色）** | `<bk-button text>` | `<bk-button theme="danger" text>删除</bk-button>` |

⚠️ **常见错误**：
- ❌ 操作列显示 `true/false` 文本 → ✅ 应该用 `<bk-switcher>`
- ❌ 操作列空白 → ✅ 必须添加"编辑""删除"按钮
- ❌ 按钮有边框 → ✅ 必须加 `text` 属性

---

## 3. 顶部水平菜单

当顶部有检索/监控/仪表盘等菜单时：

```vue
<bk-menu mode="horizontal" :active-key="activeNav">
  <bk-menu-item key="search">检索</bk-menu-item>
</bk-menu>
```

---

## 4. Tag 颜色映射

| 视觉颜色 | bk-tag 配置 | 使用场景 |
|---------|------------|---------|
| 蓝色背景 (如"内置") | `<bk-tag theme="info">` | 系统内置标识 |
| 绿色背景 (如"自定义") | `<bk-tag theme="success">` | 用户自定义标识 |
| 橙色背景 (如"警告") | `<bk-tag theme="warning">` | 警告状态 |
| 红色背景 (如"危险") | `<bk-tag theme="danger">` | 错误/危险状态 |
| 灰色边框 | `<bk-tag type="stroke">` | 普通标签 |

## 开关组件识别

| 视觉特征 | 组件 | 关键属性 |
|---------|-----|---------|
| 圆角滑动开关（绿色） | `<bk-switcher>` | 默认绿色 |
| 圆角滑动开关（蓝色） | `<bk-switcher theme="primary">` | 蓝色主题 |
| 方形勾选框 | `<bk-checkbox>` | - |
| 圆形单选 | `<bk-radio>` | - |

## 分页布局识别

| 视觉特征 | 配置 |
|---------|-----|
| 左侧显示"共计 XX 条" | `:show-total-count="true"` + `location="left"` |
| 右侧显示"每页 XX 条" | 默认配置 |
| 紧凑小尺寸分页 | `size="small"` |

## 筛选组件识别 (Tab vs Radio Capsule)

**⚠️ 关键区分：看是否有分隔线 + 是否切换内容面板**

| 视觉特征 | 组件 | 说明 |
|---------|-----|------|
| **选项之间有竖线分隔** | `bk-radio-group type="capsule"` | 胶囊样式 Radio |
| 选项下方有内容面板切换 | `bk-tab` | Tab 组件 |
| 选项有下划线高亮 | `bk-tab type="unborder-card"` | Tab 无边框样式 |

### 胶囊样式 Radio（用于筛选）

当看到选项被边框包裹、**选项之间有竖线分隔**时，使用 Radio Capsule：

```vue
<bk-radio-group v-model="activeFilter" type="capsule">
  <bk-radio-button label="all">全部(24)</bk-radio-button>
  <bk-radio-button label="enabled">启用(10)</bk-radio-button>
  <bk-radio-button label="disabled">停用(14)</bk-radio-button>
</bk-radio-group>
```

### Tab（用于切换内容面板）

当选项下方有对应的内容区域需要切换显示时，使用 Tab：

```vue
<bk-tab v-model:active="activeTab" type="unborder-card">
  <bk-tab-panel name="basic" label="基本信息">内容1</bk-tab-panel>
  <bk-tab-panel name="config" label="配置信息">内容2</bk-tab-panel>
</bk-tab>
```

> ⚠️ Tab 常见错误：`v-model="activeTab"` → 正确：`v-model:active="activeTab"`

## 5. 提示信息 (Alert)

| 视觉特征 | 组件 |
|---------|-----|
| 蓝色背景提示条 | `<bk-alert theme="info">` |
| 绿色成功提示 | `<bk-alert theme="success">` |
| 黄色警告提示 | `<bk-alert theme="warning">` |
| 红色错误提示 | `<bk-alert theme="error">` |

---

> 完整代码示例 → 加载 `code-snippets.md`
