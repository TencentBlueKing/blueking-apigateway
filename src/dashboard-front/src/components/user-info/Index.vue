<script setup lang="ts">
import { AngleDownLine } from 'bkui-vue/lib/icon';
import { getLoginURL } from '@/utils';
import { useEnv, useUserInfo } from '@/stores';

const { t } = useI18n();
const userInfoStore = useUserInfo();
const envStore = useEnv();

const handleLogout = () => {
  location.href = getLoginURL(envStore.env.BK_LOGIN_URL, location.origin, 'small');
};
</script>

<template>
  <bk-popover
    ext-cls="user-home"
    placement="bottom"
    theme="light"
    :arrow="false"
    disable-outside-click
  >
    <div class="user-name">
      {{ userInfoStore.info.display_name || userInfoStore.info.username }}
      <AngleDownLine class="pl-5px" />
    </div>
    <template #content>
      <div
        class="logout"
        @click="handleLogout"
      >
        {{ t('退出登录') }}
      </div>
    </template>
  </bk-popover>
</template>

<style lang="scss" scoped>
.user-home {
  z-index: 1000;
  font-size: 14px;
}

.user-name {
  display: flex;
  padding-left: 6px;
  cursor: pointer;
  align-items: center;
}

.user-name:hover {
  color: #fff;
}

.logout {
  display: inline-block;
  width: 80px;
  color: #63656e;
  text-align: center;
  cursor: pointer;
}
</style>
