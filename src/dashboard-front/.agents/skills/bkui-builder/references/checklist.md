# 设计稿还原检查清单 (Quality Checklist)

> 💡 生成代码后，逐项核对设计稿

## 0. 主题/配色 (最高优先级)

- [ ] **导航栏背景色**: 深色(深蓝/深灰) vs 浅色(白色/浅灰)
  - 深色 → 必须使用 `admin-layout-dark.vue` 模版
  - 必须覆盖 CSS 变量: `--header-bg-color`, `--nav-bg-color`
- [ ] **顶部导航栏颜色**: 是否与设计稿一致？
- [ ] **侧边栏背景颜色**: 是否与设计稿一致？

## 1. 顶部导航区

- [ ] **Logo + 产品名**: 使用 `side-title` 或 `#side-header` 插槽
- [ ] **业务选择器**: 若有下拉选择业务，使用 `<bk-select>` 放在 side-header
- [ ] **顶部水平菜单**: 检索/监控/管理等，使用 `<bk-menu mode="horizontal">`
  - 深色背景下菜单文字颜色需覆盖为白色
- [ ] **右侧工具图标**: 帮助/通知/设置图标用 `@bkui-vue/icon`
- [ ] **用户下拉**: 使用 `<bk-dropdown>` 包裹用户名

## 2. 侧边栏菜单

- [ ] **菜单图标**: 每个菜单项是否有图标？使用 `#icon` 插槽
- [ ] **菜单分组**: 使用 `<bk-menu-group name="分组名">`，不是 div
- [ ] **分组标题样式**: 深色主题下分组名需设置为浅色
- [ ] **当前选中高亮**: 使用 `:active-key` 绑定当前路由
- [ ] **默认展开**: 使用 `:opened-keys="['group-id']"` 控制

## 3. 表格相关

- [ ] **列筛选图标** (漏斗) → `filter: { list: [...] }`
- [ ] **列排序图标** (↑↓) → `sort: true`
- [ ] **列设置按钮** (齿轮) → `:settings="true"`
- [ ] **操作列** → `<bk-button text theme="primary">编辑</bk-button>`
- [ ] **开关 vs 勾选** → `<bk-switcher>` vs `<bk-checkbox>`
- [ ] **分页位置** → `showTotalCount: true, location: 'left'`
- [ ] **溢出省略** → `showOverflowTooltip: true`

## 4. 工具栏布局

- [ ] **左侧按钮**: 新建按钮通常在左侧，`<bk-button theme="primary">`
- [ ] **右侧筛选**: Tab + 搜索框通常在右侧
- [ ] **Tab 样式**:
  - 普通下划线 → `type="border-card"` (默认)
  - 无边框卡片 → `type="unborder-card"`
  - 边框按钮组 → `type="card"` + 自定义样式
- [ ] **Tab 筛选带数量**: 如"全部(24)"，使用动态 label `:label="\`全部(${count})\`"`
- [ ] **搜索框 placeholder**: 与设计稿文案一致
- [ ] **搜索框图标位置**: 使用 `#suffix` 插槽放 `<Search />`

## 5. 表单/筛选
- [ ] **搜索框图标**: 使用 `#suffix` 插槽放 `<Search />` 图标
- [ ] **筛选条件**: 是 Select 下拉还是 Tab 切换？
- [ ] **按钮样式**: 主按钮 `theme="primary"`，次按钮无 theme 或 `outline`

## 6. 状态展示
- [ ] **状态标签**: 使用 `<bk-tag>` 还是纯文字？颜色是否匹配？
- [ ] **空状态**: 无数据时是否显示 `<bk-exception type="empty">`？
- [ ] **加载状态**: 是否需要 `v-bkloading` 指令？

## 7. 布局细节
- [ ] **间距**: 卡片/区块间距是否使用 `mt16`, `mb16` 等原子类？
- [ ] **对齐**: 标题左对齐？操作按钮右对齐？
- [ ] **分隔线**: 是否需要 `<bk-divider>`？
- [ ] **Alert 提示**: 页面顶部提示条使用 `<bk-alert>`

## 8. 颜色/主题
- [ ] **Switch 颜色**: 蓝色用 `theme="primary"`，绿色是默认色
- [ ] **Tag 样式**: 是背景色 Tag 还是纯文字/链接？
- [ ] **Tag 主题**: `theme="info"` (蓝), `success` (绿), `warning` (橙), `danger` (红)
- [ ] **链接颜色**: 蓝色可点击文字用 `<bk-link theme="primary">`
