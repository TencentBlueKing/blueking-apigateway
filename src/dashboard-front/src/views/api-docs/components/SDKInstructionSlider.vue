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
  <!--  SDK使用说明 Slider  -->
  <div class="sdk-instruction-slider">
    <BkSideslider
      v-model:is-show="isShow"
      width="960"
      :title="t('SDK 使用说明')"
      quick-close
    >
      <template #default>
        <div class="content-wrap">
          <SdkInstructionContent />
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import SdkInstructionContent from './SDKInstructionContent.vue';

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const { t } = useI18n();

</script>

<style scoped lang="scss">
.sdk-instruction-slider {

  .content-wrap {
    padding: 24px 24px 0;
  }
}
</style>
