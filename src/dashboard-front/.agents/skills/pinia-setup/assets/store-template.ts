/**
 * Pinia Store 标准模版
 * 使用 Setup Store 语法 (推荐)
 */

import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
// @ts-ignore
import { get, post } from '@/http';

// 类型定义
interface User {
  id: number;
  name: string;
  email: string;
  avatar?: string;
}

/**
 * 用户 Store
 * 命名规范: use + 模块名 + Store
 */
export const useUserStore = defineStore('user', () => {
  // ========== State ==========
  const currentUser = ref<User | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // ========== Getters ==========
  const isLoggedIn = computed(() => !!currentUser.value);
  const username = computed(() => currentUser.value?.name ?? '');

  // ========== Actions ==========

  /**
   * 获取当前用户信息
   */
  const fetchUser = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      const data = await get<User>('/user/info');
      currentUser.value = data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * 用户登录
   */
  const login = async (credentials: { username: string; password: string }) => {
    isLoading.value = true;
    error.value = null;

    try {
      const data = await post<{ token: string; user: User }>('/user/login', credentials);
      localStorage.setItem('token', data.token);
      currentUser.value = data.user;
      return data;
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * 退出登录
   */
  const logout = () => {
    localStorage.removeItem('token');
    currentUser.value = null;
  };

  /**
   * 重置 Store
   */
  const $reset = () => {
    currentUser.value = null;
    isLoading.value = false;
    error.value = null;
  };

  return {
    // State
    currentUser,
    isLoading,
    error,
    // Getters
    isLoggedIn,
    username,
    // Actions
    fetchUser,
    login,
    logout,
    $reset
  };
});

// ========== 使用示例 ==========
/*
<script setup lang="ts">
import { useUserStore } from '@/stores/user';
import { storeToRefs } from 'pinia';

const userStore = useUserStore();

// 解构响应式状态 (使用 storeToRefs 保持响应性)
const { currentUser, isLoggedIn, isLoading } = storeToRefs(userStore);

// Actions 可以直接解构
const { login, logout, fetchUser } = userStore;

// 调用 Action
await fetchUser();
</script>
*/
