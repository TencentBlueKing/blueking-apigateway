---
# 注意不要修改本文头文件，如修改，CodeBuddy（内网版）将按照默认逻辑设置
type: always
---
# Vue 3 编码规范

## 基本原则

- 全面拥抱 **Composition API** 与 **`<script setup lang="ts">`**（Vue 3.5+）。
- 保持单一数据源（one source of truth），派生状态一律用 `computed`，副作用集中在 `watch` / `watchEffect` 与事件处理器中。
- 数据流默认遵循 **Props Down / Events Up**，双向绑定优先使用 `defineModel`。
- 逻辑复用区分职责：含响应式状态或生命周期的逻辑抽为 **Composable**（`src/hooks/`），纯无状态计算保持为普通工具函数（`src/utils/`）。
- 规范等级：【必须】= MUST/REQUIRED，【推荐】= SHOULD，【可选】= MAY。

## 1. 组件文件结构与命名【必须】

- 单文件组件（SFC）必须使用 `<script setup lang="ts">`，含 JSX 语法时使用 `<script setup lang="tsx">`。
- `<style>` 标签默认带 `scoped` 且 `lang="scss"`（即 `<style lang="scss" scoped>`）。
- 顶级块顺序统一为本仓约定：**`<template>` → `<script>` → `<style>`**（与存量 SFC 保持一致，由 ESLint `vue/block-order` 强制检查）。
- 文件命名：
  - 目录型组件/页面入口统一命名为 `Index.vue`（目录名使用 kebab-case）；
  - 独立业务组件与私有子组件文件使用 **PascalCase**（如 `UserProfile.vue`、`CreateSlider.vue`）。
  - ESLint 已关闭 `vue/multi-word-component-names` 以兼容 `Index.vue`、`Detail.vue` 等入口组件；非入口通用组件仍建议保持多词命名以避免与原生 HTML 标签冲突。
- 自动导入：Vue、Vue Router 与 `useI18n` 的运行时 API 已通过 `unplugin-auto-import` 自动导入，无需手动 `import { ref, computed } from 'vue'`（纯类型仍需 `import type`）。

```vue
<!-- 好的示例: UserProfile.vue -->
<template>
  <div class="user-profile">
    <!-- 模板代码 -->
  </div>
</template>

<script setup lang="ts">
// 逻辑代码（ref / computed / useI18n 等已自动导入）
</script>

<style lang="scss" scoped>
.user-profile {
  /* 样式代码 */
}
</style>
```

## 2. 响应式数据选型【推荐】

按数据变更方式与体积选择合适的响应式原语，避免无脑深层代理：

| 原语 | 适用场景 | 注意事项 |
| --- | --- | --- |
| `shallowRef` | 原始值（`string`/`number`/`boolean`）、仅整体替换的大数据（如表格 `columns`、长列表、Trace 树）、第三方非响应实例或动态组件 | 仅替换 `.value` 触发更新；嵌套属性变更不响应 |
| `ref` | 需要深层响应且可能整体替换的对象/数组、Composable 返回的响应式状态 | 在 `<script>` 中通过 `.value` 访问 |
| `reactive` | 表单对象等以**原位修改属性为主**、极少整体替换的单状态对象 | **禁止直接解构**（需解构时用 `toRefs()`）；`watch` 单个属性必须传 getter（`watch(() => form.name, ...)`） |
| `markRaw` | 第三方 SDK / 图表 / 编辑器实例（如 ECharts、Monaco），禁止被 Vue Proxy 代理 | 可直接存普通变量或配合 `shallowRef` |

- 普通响应式状态变量名不需要加 `Ref` 匈牙利后缀（模板引用如 `formRef`、`tableRef` 除外）。

```typescript
interface IUser {
  id: number
  name: string
}

// 好的示例
const loading = shallowRef(false);
const user = ref<IUser | null>(null);
const form = reactive({
  name: '',
  description: '',
});

watch(() => form.name, (newName) => {
  // 监听 reactive 单个属性必须使用 getter
  console.log(newName);
});

// 错误示例
const { name } = form; // 直接解构 reactive 会丢失响应性
watch(form.name, () => {}); // 非响应式 source，不会触发监听
const loadingRef = shallowRef(false); // 非模板引用不需要 Ref 后缀
```

## 3. Props、Model 与 Emits 定义【必须】

### 3.1 Props

- 必须使用**基于类型的声明**（Type-based Declaration），禁止运行时声明。
- 必须使用 **Vue 3.5+ 响应式 Props 解构**设置默认值，禁止使用 `withDefaults`（由 ESLint `vue/define-props-destructuring` 强制检查）。
- 常规对象 Props 优先声明为 `interface IProps`（遵循 `ts-style.md` 的 `I` 前缀约束）；联合/交叉类型可用 `type`。
- 仅对可选属性（`?`）赋默认值，不为必填属性提供默认值。
- **关键避坑**：
  - 将解构出的 prop 传入 `watch()` 或 composable 时，**必须用 getter 包裹**（`watch(() => count, ...)`），直接传 `watch(count, ...)` 会丢失响应性；
  - Vue 对可选 `boolean` prop 做布尔转换：父组件未传时运行时为 `false` 而非 `undefined`；如需区分“未设置 / 显式关闭”，显式声明默认值或使用 `boolean | null` / 联合类型。

### 3.2 双向绑定（`defineModel`）

- Vue 3.4+ 双向绑定优先使用 `defineModel<T>()`，不再手写 `modelValue` prop + `update:modelValue` emit。
- 修改对象类型 `model` 的内部字段不会自动触发 `update` 事件；需要通知父组件时整体替换或显式 emit。

### 3.3 Emits

- 必须使用**类型字面量成员语法**（`eventName: [arg: Type]`），禁止运行时数组声明及旧版调用签名 `(e: 'eventName', arg: Type): void`。
- 简单组件允许内联 `defineEmits<{ ... }>()`（可被 ESLint `vue/define-emits-declaration: 'type-literal'` 完整校验每个事件签名）；事件较多或需复用时可抽离 `interface IEmits`（同样保持类型字面量成员语法）。

```typescript
interface IProps {
  id: number
  title?: string
  disabled?: boolean
}

const isShow = defineModel<boolean>('isShow', { default: false });

const {
  id,
  title = '',
  disabled = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  change: [id: number]
  update: [value: string]
}>();

// 正确：解构的 prop 传入 watch 必须使用 getter
watch(() => id, (nextId) => {
  emit('change', nextId);
});

// 错误：直接传入解构变量会丢失响应性
// watch(id, (nextId) => { ... });
```

## 4. 组件引用、模板与安全规范【必须】

- **组件标签与属性**：
  - 模板中使用组件必须使用 **PascalCase**，无内容时使用自闭合标签（如 `<BkButton />`、`<UserProfile :user="user" />`）；
  - 指令使用简写：`:` 代替 `v-bind:`、`@` 代替 `v-on:`、`#` 代替 `v-slot:`；
  - 布尔属性必须使用简写（如 `clearable`、`disabled`，禁止 `:disabled="true"`）；
  - 静态 `class` 与动态 `:class` 分离书写；
  - 超过 3 个属性时每个属性独占一行。
- **模板保持声明式**：
  - 避免在模板中书写复杂表达式或直接调用 `.filter()` / `.sort()`，应提取为 `computed`；
  - `:style` 对象键名推荐使用 camelCase（如 `{ fontSize: `${size}px` }`）。
- **列表与条件渲染**：
  - `v-for` 必须配稳定的原始值 `:key`（如 `item.id`）；**可增删/重排列表禁止使用数组下标 `index` 作为 `:key`**；
  - **禁止在同一元素上同时使用 `v-if` 和 `v-for`**：在 **Vue 3 中 `v-if` 优先级高于 `v-for`**（与 Vue 2 相反），同元素混用时 `v-if` 无法访问循环变量会直接出错；过滤列表用 `computed`，整表显隐将 `v-if` 放在外层容器或 `<template v-if>`；
  - 按切换频率选择 `v-if` 与 `v-show`：高频切换用 `v-show`，低频或初始渲染开销大用 `v-if`；
  - 禁止在组件根元素使用 `v-if`（ESLint `vue/no-root-v-if`）。
- **模板事件处理器**：
  - 仅传静态或循环参数时直接写内联调用（如 `@done="handleDone(item.id)"`），Vue 模板编译器会自动包装并缓存；
  - 需要同时接收事件载荷与额外参数时，使用箭头函数或 `$event`（如 `@change="(val) => handleToggle(row, val)"` 或 `@change="handleToggle(row, $event)"`）；
  - 原生 DOM 事件回调必须显式标注事件类型（如 `event: MouseEvent`、`event: Event`）。
- **XSS 安全**：
  - 禁止对不可信或用户输入的 HTML 直接使用 `v-html`，需使用本仓已注册的 `v-xss` 指令或经清洗后再渲染。

```vue
<!-- 好的示例 -->
<template>
  <ul v-if="activeList.length">
    <li
      v-for="item in activeList"
      :key="item.id"
    >
      <BkButton
        theme="primary"
        :disabled="isSubmitting"
        text
        @click="handleSelect(item.id)"
      >
        {{ item.name }}
      </BkButton>
    </li>
  </ul>
</template>

<!-- 错误示例 -->
<template>
  <ul>
    <!-- Vue 3 中 v-if 优先级高于 v-for，此时 item 未定义会直接报错 -->
    <li
      v-for="item in list"
      v-if="item.isActive"
      :key="item.id"
    >
      {{ item.name }}
    </li>
  </ul>
</template>
```

## 5. 计算属性与监听器【必须】

- 必须使用 `computed` 处理派生状态，**禁止**用 `watch` / `watchEffect` 去同步赋值派生 `ref`。
- 禁止在 `computed` 中执行副作用（API 请求、修改其他状态、DOM 操作）；对数组排序/反转前先浅拷贝（如 `[...list.value].sort(...)`），避免原地修改源数组。
- 副作用（异步请求、外部订阅、日志等）放在 `watch` / `watchEffect` 或事件处理器中。
- 需要“初始化执行 + 依赖变更重跑”时优先使用 `{ immediate: true }`，避免 `onMounted` 与 `watch` 重复调用。
- **异步 `watch` 必须处理竞态清理**：使用 Vue 3.5+ 的 `onWatcherCleanup`（或 `onCleanup` 参数）取消旧请求或丢弃过期结果。

```typescript
const query = shallowRef('');
const results = shallowRef<IItem[]>([]);

watch(query, async (keyword) => {
  const controller = new AbortController();
  let active = true;
  onWatcherCleanup(() => {
    active = false;
    controller.abort();
  });

  const data = await searchItems(keyword, controller.signal);
  if (active) {
    results.value = data;
  }
}, { immediate: true });
```

## 6. 模板引用与命令式访问【推荐】

- 组件通信优先使用 Props / Emits，仅在聚焦、滚动、表单 `validate()`、表格 `fetchData()` 等命令式操作时使用模板引用，子组件通过 `defineExpose` 仅暴露必要 API。
- Vue 3.5+ 优先使用 `useTemplateRef('refName')`：
  - **泛型组件**（如 `AgTable`）必须显式传入实例接口：`useTemplateRef<IAgTableInstance<IRow>>('tableRef')`，不要用 `InstanceType<typeof GenericComp>`；
  - **`v-for` 列表引用**不适用 `useTemplateRef`，仍使用 `ref<(HTMLElement | null)[]>([])`；
  - 模板引用在挂载前及 `v-if` 销毁后均为 `null`，访问必须使用可选链 `?.`。

## 7. `<script>` 代码组织与函数声明【必须/推荐】

- **编译器宏顺序【必须】**（与 ESLint `vue/define-macros-order` 严格对齐）：
  1. 类型定义（`interface IProps` 等）
  2. 顶部宏：`defineOptions` → `defineModel` → `defineProps` → `defineEmits` → `defineSlots`
  3. 业务逻辑代码
  4. `defineExpose`（必须位于 `<script setup>` 最后）
- **逻辑组织【推荐】**：宏之后**允许并推荐按逻辑关注点（Logical Concern）**聚合同一功能相关的 `ref`/state、`computed`、`watch` 与方法（handlers），保持高内聚，不再机械按语法类别拆散；复杂独立工作流直接抽离为 Composable。
- **函数声明【推荐】**：`<script setup>` 内常规函数可使用 `function handleXxx()`（支持函数提升，配合 `watch(..., { immediate: true })` 无 TDZ 问题）或 `const handleXxx = () => {}`，单文件内保持风格一致即可。

```typescript
// 好的示例：宏在顶部，业务代码按关注点聚合
// --- 关注点 1：搜索筛选 ---
const keyword = shallowRef('');
const normalizedKeyword = computed(() => keyword.value.trim());
function handleSearch() {
  // ...
}

// --- 关注点 2：新建弹窗 ---
const dialogVisible = shallowRef(false);
function handleOpenDialog() {
  dialogVisible.value = true;
}
```

## 8. Provide/Inject、Composable 与 Store 边界【推荐】

- **Provide / Inject**：仅在多个后代组件共享依赖且中间层只需透传时使用；必须配合强类型 `InjectionKey<IXxxContext>`，对外暴露 `readonly` 状态与显式变更方法。
- **Composable（`src/hooks/`）**：
  - 命名以 `use` 开头，返回包含 `ref` 的普通对象（禁止直接返回 `reactive` 对象）；
  - 外部只读消费的状态用 `readonly()` 包装并通过方法修改；
  - 通用复用型入参使用 `MaybeRefOrGetter<T>` 并通过 `toValue()` / `toRef()` 归一化；
  - 内部注册的监听器、定时器、请求必须在 `onUnmounted` / `onScopeDispose` 中清理；
  - **纯无状态工具函数必须放在 `src/utils/`**，不要包装成 `useXxx`。
- **Pinia Store（`src/stores/`）**：
  - 默认使用 **Option Store**，复杂场景（需 `watch`、组合多个 Store/Composable、维护内部非响应式 `Map`/Promise 等）允许使用 **Setup Store**；
  - Setup Store 必须 `return` 全部响应式 state（不得隐藏“私有” `ref`），如需重置需显式实现 `$reset()`；
  - 组件内解构 state / getters 必须使用 `storeToRefs(store)`，actions 直接解构；
  - 禁止在模块顶层调用 `useXxx()`，防止触发 `getActivePinia` 错误。

## 9. 样式规范【推荐】

- 优先使用 **UnoCSS 原子类**处理常规间距、排版与 Flex/Grid 布局（如 `flex items-center gap-16px mb-16px`）。
- 组件局部样式写在 `<style lang="scss" scoped>` 中，选择器遵循 kebab-case（由 stylelint 检查）。
- scoped CSS 中优先使用**类选择器**而非元素选择器（减少属性选择器匹配开销）；克制使用 `:deep()`，避免滥用 `!important`。
