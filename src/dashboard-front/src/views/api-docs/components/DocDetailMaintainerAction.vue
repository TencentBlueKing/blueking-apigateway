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

<template>
  <aside
    class="maintainer-action"
  >
    <Chat
      v-if="showChat"
      :default-user-list="userList"
      :owner="curUser.username"
      :name="chatName"
      :content="chatContent"
      is-query
    />
    <a
      v-else-if="showServiceAccount"
      target="_blank"
      class="link-item"
      :href="basics?.doc_maintainers?.service_account?.link"
    >
      <i class="ag-doc-icon doc-qw text-16px apigateway-icon icon-ag-qw" />
      {{ t('联系') }} {{ basics?.doc_maintainers?.service_account?.name }}
    </a>
  </aside>
</template>

<script lang="ts" setup>
import Chat from '@/components/chat/Index.vue';
import type { IDocBasics } from './DocDetailSideContent.vue';
import { useFeatureFlag, useUserInfo } from '@/stores';

interface IProps { basics?: IDocBasics | null }

const { basics = null } = defineProps<IProps>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();
const userStore = useUserInfo();

const curUser = computed(() => userStore?.info);
const isUserMaintainer = computed(() => basics?.doc_maintainers?.type === 'user');
const showChat = computed(() => (
  isUserMaintainer.value && featureFlagStore.flags.ALLOW_CREATE_APPCHAT
));
const showServiceAccount = computed(() => (
  !isUserMaintainer.value && Boolean(basics?.doc_maintainers?.service_account?.name)
));
const userList = computed(() => {
  const set = new Set([
    curUser.value?.username,
    ...(basics?.maintainers ?? []),
  ]);
  return [...set].filter((s): s is string => !!s);
});
const chatName = computed(() => `${t('[蓝鲸网关API咨询] 网关')}${basics?.name}`);
const chatContent = computed(() => `${t('网关API文档')}:${location.href}`);
</script>

<style lang="scss" scoped>
.maintainer-action {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.link-item {
  font-size: 12px;
  color: #3A84FF;

  i {
    margin-right: 3px;
  }
}
</style>
