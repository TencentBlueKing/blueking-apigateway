<script setup lang="ts">
import { ref } from 'vue';
import { useUser } from '@/store/user';
import { logout } from '@/common/auth';
import { AngleDownLine } from 'bkui-vue/lib/icon';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const user = useUser();
const userInfo = ref(user.user);
</script>

<template>
  <bk-popover
    ext-cls="user-home"
    placement="bottom-end"
    theme="light"
    :arrow="false"
  >
    <div class="user-name">
      {{ userInfo.username }}
      <angle-down-line class="pl5" />
    </div>
    <template #content>
      <div
        class="logout"
        @click="logout"
      >{{t('退出登录')}}</div>
    </template>
  </bk-popover>
</template>

<style lang="scss" scoped>
.user-home {
  z-index: 1000;
  font-size: 14px;
}
.user-name {
  cursor: pointer;
  display: flex;
  align-items: center;
}
.user-name:hover {
  color: #fff;
}
.logout {
  display: inline-block;
  text-align: center;
  width: 50px;
  cursor: pointer;
  color: #63656E;
}
</style>
