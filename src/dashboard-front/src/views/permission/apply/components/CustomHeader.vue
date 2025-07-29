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
<template>
  <div class="flex items-center justify-between top-bar">
    <div class="flex items-center top-left-wrapper">
      <div class="title">
        {{ t('权限审批') }}
      </div>
    </div>
    <div class="flex items-center top-right-wrapper">
      <BkButton
        text
        theme="primary"
        @click="handleNavRecordPage"
      >
        <AgIcon
          name="cc-history"
          class="m-r-6px"
        />
        {{ t('审批历史') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';

const { t } = useI18n();
const router = useRouter();

const handleNavRecordPage = () => {
  router.push({ name: 'PermissionRecord' });
};

</script>

<style lang="scss" scoped>
.top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #ffffff;
  top: -1px;

  .top-left-wrapper {
    .title {
      font-size: 16px;
      color: #313238;
    }
  }

  .top-right-wrapper {
    font-size: 12px;
  }
}
</style>
