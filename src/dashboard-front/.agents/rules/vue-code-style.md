---
# 注意不要修改本文头文件，如修改，CodeBuddy（内网版）将按照默认逻辑设置
type: always
---
# Vue 3 编码规范

## 基本原则

- 全面拥抱 **Composition API** 和 **`<script setup>`** 语法
- 严格的 **TypeScript** 类型检查
- 逻辑复用优先使用 **Composables**
- 规范等级：【必须】= MUST/REQUIRED，【推荐】= SHOULD，【可选】= MAY

## 1. 组件文件结构【必须】

- 单文件组件 (SFC) 必须使用 `<script setup lang="ts">`，如果使用了 jsx 语法，则 lang 可以为 tsx
- `<style>` 标签默认带有 scoped，lang 默认为 scss
- 顶级标签顺序统一为：`<template>` -> `<script>` -> `<style>`
- 文件名必须使用 PascalCase (大驼峰)

```vue
<!-- 好的示例: UserProfile.vue -->

<template>
  <!-- 模板代码 -->
</template>

<script setup lang="ts">
  // 逻辑代码
</script>

<style scoped lang="scss">
/* 样式代码 */
</style>

<!-- 错误示例: user-profile.vue -->
<template>
  <!-- 模板在前 -->
</template>
<script>
// 使用了 Options API 或未标记 setup
export default {}
</script>
```

## 2. 响应式数据【推荐】

- 优先使用 `ref` 而不是 `reactive`，以保持解构时的响应性一致性
- 变量名不需要加 `Ref` 后缀
- 访问 `ref` 值时必须使用 `.value` (在 script 中)

```typescript
// 好的示例
const count = ref(0);
const user = ref<User>({ name: 'John' });

function increment() {
  count.value++;
}

// 错误示例
const state = reactive({ count: 0 }); // 解构会丢失响应性
const countRef = ref(0); // 匈牙利命名法是不必要的
```

## 3. Props 定义 【必须】
- 必须使用基于类型的声明 (Type-based Declaration)
- props 的类型必须单独用一个 interface 声明，并且通过泛型传到 defineProps 方法中
- 必须使用响应式 Props 解构 (Vue 3.3+) 设置默认值
- 不允许使用 withDefaults 方法
- 禁止使用运行时声明 (Runtime Declaration)

## 4. Emits 定义【必须】

- 必须使用基于类型的声明 (Type-based Declaration)
- emits 的类型必须单独用一个 interface 声明，并且通过泛型传到 defineEmits 方法中

```typescript
// 好的示例
interface IProps {
  msg: string
  count?: number
}

interface IEmits {
  change: [id: number]
  update: [value: string]
}

// 使用泛型定义
const { 
  msg = 'hello',
  count = undefined,
} = defineProps<Props>();

const emit = defineEmits<IEmits>();

// 错误示例
const props = defineProps({
  msg: String,
  count: { type: Number, default: 0 }
});
```

## 5. 组件命名与引用【必须】

- 组件文件名使用 PascalCase (如 `MyComponent.vue`)
- 在模板中使用组件时，必须使用 PascalCase 自闭合标签 (如果无内容)
- 保持组件名由多个单词组成，避免与 HTML 元素冲突

```vue
<!-- 好的示例 -->
<template>
  <MyComponent />
  <UserProfile :user="user" />
</template>

<!-- 错误示例 -->
<template>
  <my-component></my-component> <!-- 这种写法仅用于 DOM 模板 -->
  <user /> <!-- 单个单词，容易冲突 -->
</template>
```

## 6. 模板语法【推荐】

- 指令简写：必须使用 `:` 代替 `v-bind:`，`@` 代替 `v-on:`，`#` 代替 `v-slot:`
- 模板中避免复杂的 JavaScript 表达式，应提取为 `computed`
- 超过 3 个属性时，每个属性一行

```vue
<!-- 好的示例 -->
<template>
  <BaseButton
    :disabled="isSubmitting"
    :label="buttonLabel"
    @click="handleSubmit"
  />
  <div>{{ formattedDate }}</div>
</template>

<!-- 错误示例 -->
<template>
  <BaseButton v-on:click="handleSubmit" v-bind:disabled="isSubmitting" label="Submit" />
  <div>{{ new Date(date).toLocaleDateString() }}</div>
</template>
```

## 7. 计算属性与监听器【必须】

- 必须使用 `computed` 处理派生状态
- 禁止在 `computed` 中执行副作用 (如 API 请求、DOM 修改)
- 副作用必须放在 `watch` 或 `watchEffect` 中

```typescript
// 好的示例
const fullName = computed(() => `${firstName.value} ${lastName.value}`);

watch(id, async (newId) => {
  await fetchUserData(newId);
});

// 错误示例
const fullName = computed(() => {
  saveLog(); // 副作用！
  return firstName.value + lastName.value;
});
```

## 8. 指令使用规范【必须】

- `v-for` 必须配合 `:key` 使用
- 禁止在同一元素上同时使用 `v-if` 和 `v-for` (性能问题)
- 如果需要过滤列表，请使用 `computed` 预先过滤

```vue
<!-- 好的示例 -->
<template>
  <ul v-if="list.length">
    <li v-for="item in activeList" :key="item.id">
      {{ item.name }}
    </li>
  </ul>
</template>

<!-- 错误示例 -->
<template>
  <ul>
    <!-- v-if 优先级高于 v-for (Vue2) 或低于 (Vue3)，容易混淆且性能差 -->
    <li v-for="item in list" :key="item.id" v-if="item.isActive">
      {{ item.name }}
    </li>
  </ul>
</template>
```

## 9. `<script>`内的ref、宏及其他要素的代码顺序【必须】

- `<script>` 内的要素要遵循以下顺序排放：

1. TypeScript 类型定义
2. defineModel
3. defineProps
4. defineEmits
5. pinia stores
6. hooks
7. ref/reactive 变量（不含模板引用）
8. 模板引用 ref/useTemplateRef
9. 普通 let/const 变量
10. computed
11. watch/watchEffect
12. 各类 function
13. defineExpose

- 注意，如果 watch 配置了 `immediate: true` 并且在回调中使用了组件内的某个 function，那么这个 function 可以放到这个 watch 前面

## 10. 组件内的方法声明优先使用箭头函数【必须】
- 比如使用 `const someFunc = () => {}`
- 而不是 `function someFunc {}`

## 11. 带参数的事件处理器使用箭头函数包裹【推荐】
```vue
<!-- 好的示例 -->
<UserInfo
  @done="(123) => handleDone(123)"
/>

<!-- 坏的示例 -->
<UserInfo
  @done="handleDone(123)"
/>


```

## 12. 模板引用优先使用 `useTemplateRef` 创建【推荐】