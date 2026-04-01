<template>
  <div class="admin-layout">
    <bk-navigation
      :header-title="headerTitle"
      :side-title="sideTitle"
      navigation-type="left-right"
      need-menu
      default-open
      @toggle="handleToggle"
    >
      <template #header>
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
      </template>

      <template #menu>
        <!-- ⚠️ 注意: 使用 opened-keys，不是 default-open-keys -->
        <bk-menu :active-key="activeMenu" :opened-keys="openedKeys" @click="handleMenuClick">
          <!-- [TODO] 根据实际菜单结构填充 -->
          <bk-menu-item key="home">
            <template #icon><Home /></template>
            首页
          </bk-menu-item>
          <bk-menu-group id="group1" name="功能模块">
            <bk-menu-item key="list">列表页</bk-menu-item>
            <bk-menu-item key="detail">详情页</bk-menu-item>
          </bk-menu-group>
        </bk-menu>
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
import { Home, DownShape } from '@bkui-vue/icon';

defineProps<{
  headerTitle?: string;
  sideTitle?: string;
  username?: string;
}>();

const activeMenu = ref('home');
const openedKeys = ref(['group1']);

const handleToggle = (collapsed: boolean) => {
  console.log('Sidebar collapsed:', collapsed);
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

.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  padding-right: 20px;
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
