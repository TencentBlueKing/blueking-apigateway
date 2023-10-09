<script setup lang="ts">
import {
  ref,
} from 'vue';
import { useUser } from '@/store';
import { getUser } from '@/http';
import { Message } from 'bkui-vue';

// 加载完用户数据才会展示页面
const isLoading = ref(true);
// 获取用户数据
const user = useUser();
getUser()
  .then((data) => {
    user.setUser(data);
    isLoading.value = false;
  })
  .catch(() => {
    Message('获取用户信息失败，请检查后再试');
  });
</script>

<template>
  <bk-loading
    :loading="isLoading"
    :class="{
      'main-loading': isLoading
    }"
  >
    <router-view v-if="!isLoading"></router-view>
  </bk-loading>
</template>

<style lang="scss" scoped>
  .main-loading {
    margin-top: 25vw;
  }
</style>
