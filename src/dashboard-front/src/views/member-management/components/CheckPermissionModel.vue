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
  <BkSideslider
    v-model:is-show="isShow"
    :title="t('权限模型')"
    :width="640"
    quick-close
    render-directive="if"
  >
    <div class="permission-model-slider">
      <PermissionModel
        v-model:highlight-role="highlightRole"
        :ai-gateway="isAIGateway"
      />
    </div>
  </BkSideslider>
</template>

<script setup lang="ts">
import { useGateway } from '@/stores';
import PermissionModel from './PermissionModel.vue';
import type { MemberRole } from '@/constants/gateway-permission';

const isShow = defineModel<boolean>('isShow', { default: false });

const { t } = useI18n();
const gatewayStore = useGateway();

const highlightRole = ref<MemberRole>('administrator');

const isAIGateway = computed(() => gatewayStore.isAIGateway);

watch(isShow, () => {
  if (isShow.value) {
    highlightRole.value = 'administrator';
  }
});

</script>

<style lang="scss" scoped>
.permission-model-slider {
  padding: 20px 24px 24px;
}
</style>
