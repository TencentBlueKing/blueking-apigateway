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
  <div class="flex flex-col items-center justify-center h-full gap-16px">
    <BkException
      type="500"
      :title="t('网关加载失败')"
      :description="t('系统错误，请稍后重试')"
    />
    <BkButton
      theme="primary"
      :loading="retrying"
      @click="retry"
    >
      {{ t('重试') }}
    </BkButton>
  </div>
</template>

<script setup lang="ts">
import { getGatewayRetryRoute } from '@/utils/gateway-access-error';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const retrying = ref(false);

const retry = async () => {
  retrying.value = true;
  try {
    // 从异常页返回业务页时，守卫会强制重新查询角色和详情。
    await router.replace(getGatewayRetryRoute(router, Number(route.params.id), route.query.retry));
  }
  finally {
    retrying.value = false;
  }
};
</script>
