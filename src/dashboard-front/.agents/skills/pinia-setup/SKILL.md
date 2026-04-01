---
id: pinia-setup
name: pinia-setup
description: 基于 Pinia 的全局状态管理规范，包含 UserStore、AppStore 的标准定义
---

# 全局状态管理规范 (Pinia)

推荐使用 **Setup Store** 语法（类似 Composition API），比 Options API 更灵活。

## 基础模式

```typescript
// src/store/user.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null);
  const loading = ref(false);

  const fetchUserInfo = async () => {
    if (userInfo.value) return userInfo.value;
    loading.value = true;
    try {
      userInfo.value = await http.get('/user/info');
    } finally {
      loading.value = false;
    }
  };

  return { userInfo, loading, fetchUserInfo };
});
```

## 组件中使用

```typescript
<script setup lang="ts">
import { useUserStore } from '@/store/user';
import { storeToRefs } from 'pinia';

const userStore = useUserStore();
// 使用 storeToRefs 保持响应性
const { userInfo, loading } = storeToRefs(userStore);
// Action 直接调用
userStore.fetchUserInfo();
</script>
```

## 常见错误

| 错误 | 解决 |
|------|------|
| 解构丢失响应性 | 用 `storeToRefs()` |
| 多次实例化 | Store 单例，直接 `useXxxStore()` |

## 📦 按需加载资源

| 资源 | URI |
|-----|-----|
| 完整 Store 模板 | `./assets/store-template.ts` |


---
## 📦 可用资源

- `./assets/store-template.ts`

> 根据 SKILL.md 中的 IF-THEN 规则判断是否需要加载
