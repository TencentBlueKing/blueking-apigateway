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
  <div class="resource-version-top">
    <BkTab
      :active="resourceVersionStore.tabActive || 'edition'"
      type="unborder-card"
      @change="handleChange"
    >
      <BkTabPanel
        name="edition"
        :label="t('版本列表')"
      />
      <BkTabPanel
        v-if="featureFlagStore.flags.ALLOW_UPLOAD_SDK_TO_REPOSITORY"
        name="sdk"
        :label="t('SDK 列表')"
      />
    </BkTab>
  </div>
</template>

<script setup lang="ts">
import { useFeatureFlag, useResourceVersion } from '@/stores';

const { t } = useI18n();
const resourceVersionStore = useResourceVersion();
const featureFlagStore = useFeatureFlag();

const handleChange = (key: string) => {
  resourceVersionStore.setTabActive(key);
};
</script>

<style lang="scss">
.resource-version-top {
  display: flex;
  padding: 0 24px;
  margin-top: -10px;
  font-size: 12px;
  background-color: #fff;
  border-bottom: 1px solid #dcdee5;
  box-shadow: 0 3px 4px rgb(64 112 203 / 5.88%);
  justify-content: flex-start;
  align-items: center;

  .bk-tab--top .bk-tab-header-item {
    padding: 0 10px;
    font-size: 14px;
  }

  .bk-tab--unborder-card .bk-tab-header {
    border-bottom: none;
  }

  .bk-tab-content {
    padding: 0;
  }
}
</style>
