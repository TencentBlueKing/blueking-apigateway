/*
* TencentBlueKing is pleased to support the open source community by making
* 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
* Copyright (C) Tencent. All rights reserved.
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
import { CollapseLeft } from 'bkui-vue/lib/icon';
import { getLoginURL } from '@/utils';
import { useEnv, useFeatureFlag, useUserInfo } from '@/stores';

import BkLoginUserinfo, { ActionItem } from '@blueking/login-userinfo';
import '@blueking/login-userinfo/vue3/vue3.css';

const { t } = useI18n();
const userInfoStore = useUserInfo();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();

const userinfo = computed(() => ({
  name: userInfoStore?.info?.display_name || userInfoStore?.info?.username,
  email: '',
  organization: userInfoStore.info.tenant_id ? userInfoStore.info.tenant_id : undefined,
  timezone: userInfoStore.info.time_zone,
}));

const handleBkUserClick = () => {
  window.open(envStore.env.BK_USER_PERSONAL_CENTER_LINK);
};

const handleLogout = () => {
  location.href = getLoginURL(envStore.env.BK_LOGIN_URL, location.origin, 'small');
};
</script>

<template>
  <div>
    <BkLoginUserinfo :userinfo="userinfo">
      <template v-if="!featureFlagStore.isEnableDisplayName">
        {{ userInfoStore?.info?.display_name || userInfoStore?.info?.username }}
      </template>
      <template v-else>
        <bk-user-display-name
          :user-id="userInfoStore?.info?.username || userInfoStore?.info?.display_name"
          :api-base-url="envStore?.tenantUserDisplayAPI"
        />
      </template>
      <template #action>
        <ActionItem
          v-if="envStore.env.BK_USER_PERSONAL_CENTER_LINK"
          @click="handleBkUserClick"
        >
          <template #icon>
            <AgIcon name="user-circle" />
          </template>
          {{ t('个人设置') }}
        </ActionItem>
        <ActionItem
          theme="danger"
          @click="handleLogout"
        >
          <template #icon>
            <CollapseLeft />
          </template>
          {{ t('退出登录') }}
        </ActionItem>
      </template>
    </BkLoginUserinfo>
  </div>
</template>
