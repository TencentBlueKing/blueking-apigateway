/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

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
