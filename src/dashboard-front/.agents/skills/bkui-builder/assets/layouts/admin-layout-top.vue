<template>
  <div class="admin-layout">
    <bk-navigation
      :header-title="headerTitle"
      navigation-type="top-bottom"
      @toggle="handleToggle"
    >
      <template #header>
        <div class="header-content">
          <!-- 顶部菜单 -->
          <bk-menu mode="horizontal" :active-key="activeMenu" @click="handleMenuClick">
            <bk-menu-item key="home">首页</bk-menu-item>
            <bk-menu-item key="monitor">监控</bk-menu-item>
            <bk-menu-item key="config">配置</bk-menu-item>
          </bk-menu>

          <!-- 右侧用户信息 -->
          <div class="header-right">
            <bk-popover theme="light" trigger="click" placement="bottom-end">
              <div class="user-info">
                <span>{{ username }}</span>
                <DownShape />
              </div>
              <template #content>
                <ul class="user-menu">
                  <li @click="handleLogout">退出登录</li>
                </ul>
              </template>
            </bk-popover>
          </div>
        </div>
      </template>

      <div class="main-content">
        <bk-breadcrumb class="mb20">
          <bk-breadcrumb-item to="/">首页</bk-breadcrumb-item>
          <bk-breadcrumb-item>当前页面</bk-breadcrumb-item>
        </bk-breadcrumb>

        <div class="content-card">
          <!-- [TODO] 业务内容区域 -->
          <slot />
        </div>
      </div>
    </bk-navigation>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { DownShape } from '@bkui-vue/icon';

defineProps<{
  headerTitle?: string;
  username?: string;
}>();

const activeMenu = ref('home');

const handleToggle = (collapsed: boolean) => {
  console.log('Header collapsed:', collapsed);
};

const handleMenuClick = (key: string) => {
  activeMenu.value = key;
};

const handleLogout = () => {
  // TODO: 实现登出逻辑
};
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 20px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 4px;
}

.user-menu {
  padding: 6px 0;
  min-width: 100px;
}

.user-menu li {
  padding: 8px 16px;
  cursor: pointer;
}

.user-menu li:hover {
  background: #f0f1f5;
  color: #3a84ff;
}

.main-content {
  padding: 20px;
  height: 100%;
  overflow: auto;
}

.content-card {
  background: #fff;
  padding: 20px;
  min-height: calc(100% - 60px);
  box-shadow: 0 2px 4px rgba(25, 25, 41, 0.05);
}

.mb20 {
  margin-bottom: 20px;
}
</style>
