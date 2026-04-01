<template>
  <div class="admin-layout admin-layout--dark">
    <bk-navigation
      :header-title="headerTitle"
      :side-title="sideTitle"
      navigation-type="left-right"
      need-menu
      default-open
      @toggle="handleToggle"
    >
      <template #side-header>
        <div class="side-header">
          <img v-if="logo" :src="logo" class="logo" />
          <span class="title">{{ sideTitle }}</span>
          <!-- 业务选择器 (如有下拉选择业务) -->
          <bk-select
            v-if="showBizSelector"
            v-model="currentBiz"
            class="biz-selector"
            :clearable="false"
            size="small"
          >
            <bk-option
              v-for="biz in bizList"
              :key="biz.id"
              :value="biz.id"
              :label="biz.name"
            />
          </bk-select>
        </div>
      </template>

      <template #header>
        <div class="header-nav">
          <!-- 顶部水平菜单 (检索/监控策略/仪表盘/管理) -->
          <bk-menu
            mode="horizontal"
            :active-key="activeNav"
            class="top-menu"
            @click="handleNavClick"
          >
            <bk-menu-item key="search">检索</bk-menu-item>
            <bk-menu-item key="monitor">监控策略</bk-menu-item>
            <bk-menu-item key="dashboard">仪表盘</bk-menu-item>
            <bk-menu-item key="manage">管理</bk-menu-item>
          </bk-menu>

          <!-- 右侧工具区 -->
          <div class="header-right">
            <!-- 工具图标 -->
            <div class="header-icons">
              <span class="icon-item"><DocFill /></span>
              <span class="icon-item"><Help /></span>
              <span class="icon-item"><Info /></span>
            </div>
            <!-- 用户下拉 -->
            <bk-dropdown trigger="click">
              <div class="user-info">
                <span>{{ username }}</span>
                <DownShape />
              </div>
              <template #content>
                <bk-dropdown-menu>
                  <bk-dropdown-item @click="handleLogout">退出登录</bk-dropdown-item>
                </bk-dropdown-menu>
              </template>
            </bk-dropdown>
          </div>
        </div>
      </template>

      <template #menu>
        <!-- ⚠️ 注意: 使用 opened-keys，不是 default-open-keys -->
        <bk-menu :active-key="activeMenu" :opened-keys="openedKeys" @click="handleMenuClick">
          <!-- 日志接入分组 -->
          <bk-menu-group id="log-access" name="日志接入">
            <bk-menu-item key="log-collect">
              <template #icon><DataShape /></template>
              日志采集
            </bk-menu-item>
          </bk-menu-group>

          <!-- 日志清洗分组 -->
          <bk-menu-group id="log-clean" name="日志清洗">
            <bk-menu-item key="wash-list">
              <template #icon><TextFile /></template>
              清洗列表
            </bk-menu-item>
            <bk-menu-item key="wash-template">
              <template #icon><CopyShape /></template>
              清洗模板
            </bk-menu-item>
            <bk-menu-item key="desensitize">
              <template #icon><FixShape /></template>
              日志脱敏
            </bk-menu-item>
            <bk-menu-item key="grok">
              <template #icon><CogShape /></template>
              Grok 管理
            </bk-menu-item>
          </bk-menu-group>

          <!-- 日志归档分组 -->
          <bk-menu-group id="log-archive" name="日志归档">
            <bk-menu-item key="archive-store">
              <template #icon><FolderOpen /></template>
              归档仓库
            </bk-menu-item>
            <bk-menu-item key="archive-list">
              <template #icon><TextFile /></template>
              归档列表
            </bk-menu-item>
            <bk-menu-item key="archive-trace">
              <template #icon><ArchiveFill /></template>
              归档回溯
            </bk-menu-item>
          </bk-menu-group>

          <!-- 日志提取分组 -->
          <bk-menu-group id="log-extract" name="日志提取">
            <bk-menu-item key="extract-config">
              <template #icon><CogShape /></template>
              日志提取配置
            </bk-menu-item>
            <bk-menu-item key="extract-task">
              <template #icon><Upload /></template>
              日志提取任务
            </bk-menu-item>
          </bk-menu-group>

          <!-- ES 集群分组 -->
          <bk-menu-group id="es-cluster" name="ES 集群">
            <bk-menu-item key="cluster-manage">
              <template #icon><TreeApplicationShape /></template>
              集群管理
            </bk-menu-item>
          </bk-menu-group>

          <!-- 订阅分组 -->
          <bk-menu-group id="subscription" name="订阅">
            <bk-menu-item key="subscribe-manage">
              <template #icon><Share /></template>
              订阅管理
            </bk-menu-item>
          </bk-menu-group>
        </bk-menu>
      </template>

      <div class="main-content">
        <slot />
      </div>
    </bk-navigation>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
// ⚠️ 正确导入方式：从 bkui-vue/lib/icon 导入（从源码提取的真实图标名称）
import {
  DownShape,
  DataShape,
  TextFile,
  CopyShape,
  FixShape,
  CogShape,
  FolderOpen,
  ArchiveFill,
  Upload,
  TreeApplicationShape,
  Share,
  Help,
  Info,
  DocFill
} from 'bkui-vue/lib/icon';

defineProps<{
  headerTitle?: string;
  sideTitle?: string;
  username?: string;
  logo?: string;
  showBizSelector?: boolean;
  bizList?: Array<{ id: string; name: string }>;
}>();

const activeNav = ref('manage');
const activeMenu = ref('grok');
const openedKeys = ref(['log-clean']);
const currentBiz = ref('');

const handleToggle = (collapsed: boolean) => {
  console.log('Sidebar collapsed:', collapsed);
};

const handleNavClick = (key: string) => {
  activeNav.value = key;
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

/* ========== 深色主题核心样式 ========== */

/* 顶部导航栏深色背景 */
.admin-layout--dark :deep(.bk-navigation-header) {
  background-color: #2D3F5E !important;
}

/* 侧边栏深色背景 */
.admin-layout--dark :deep(.bk-navigation-wrapper) {
  --nav-bg-color: #1a1a2e;
  --nav-text-color: #fff;
}

.admin-layout--dark :deep(.bk-navigation-side) {
  background-color: #1a1a2e !important;
}

/* 侧边栏菜单样式 */
.admin-layout--dark :deep(.bk-navigation-side .bk-menu) {
  background-color: transparent;
  --menu-bg-color: transparent;
  --menu-text-color: rgba(255, 255, 255, 0.8);
  --menu-active-color: #3a84ff;
  --menu-hover-bg: rgba(255, 255, 255, 0.1);
}

.admin-layout--dark :deep(.bk-navigation-side .bk-menu-item) {
  color: rgba(255, 255, 255, 0.8);
}

.admin-layout--dark :deep(.bk-navigation-side .bk-menu-item:hover),
.admin-layout--dark :deep(.bk-navigation-side .bk-menu-item.is-active) {
  background-color: rgba(58, 132, 255, 0.2);
  color: #fff;
}

.admin-layout--dark :deep(.bk-menu-group__title) {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

/* ========== 顶部水平菜单样式 ========== */

.header-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.top-menu {
  background: transparent !important;
  border: none !important;
}

.admin-layout--dark .top-menu :deep(.bk-menu-item) {
  color: rgba(255, 255, 255, 0.8);
  border: none;
}

.admin-layout--dark .top-menu :deep(.bk-menu-item:hover),
.admin-layout--dark .top-menu :deep(.bk-menu-item.is-active) {
  color: #fff;
  background: transparent;
}

.admin-layout--dark .top-menu :deep(.bk-menu-item.is-active::after) {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 2px;
  background-color: #3a84ff;
}

/* ========== 右侧工具区 ========== */

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-right: 20px;
}

.header-icons {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.8);
  transition: color 0.2s;
}

.icon-item:hover {
  color: #fff;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 4px;
  color: rgba(255, 255, 255, 0.8);
}

.user-info:hover {
  color: #fff;
}

/* ========== 侧边栏头部 ========== */

.side-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  color: #fff;
}

.side-header .logo {
  width: 28px;
  height: 28px;
}

.side-header .title {
  font-size: 16px;
  font-weight: 500;
}

.biz-selector {
  width: 100px;
  margin-left: 8px;
}

.admin-layout--dark .biz-selector :deep(.bk-input) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

/* ========== 主内容区 ========== */

.main-content {
  padding: 20px;
  height: 100%;
  overflow: auto;
  background-color: #f5f7fa;
}
</style>
