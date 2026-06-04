/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <div>
    <!-- 无自定义插槽 -->
    <template v-if="!slots.customDisplayName">
      <BkPopover
        theme="dark"
        placement="left"
        :popover-delay="0"
      >
        <BkTag class="min-w-20px max-w-full overflow-hidden truncate">
          <bk-user-display-name
            v-if="isEnabledUserName"
            :user-id="userId"
          />
          <template v-else>
            {{ userId || '--' }}
          </template>
        </BkTag>
        <template #content>
          <div>
            <bk-user-display-name
              v-if="isEnabledUserName"
              :user-id="userId"
            />
            <span v-else>
              {{ userId || '--' }}
            </span>
          </div>
        </template>
      </BkPopover>
    </template>

    <!-- 自定义插槽 -->
    <template v-if="slots.customDisplayName">
      <slot name="customDisplayName" />
    </template>
  </div>
</template>

<script setup lang="tsx">
interface IUserDisplayNameProps {
  /** 用户ID，支持字符串或数组 */
  userId?: string | string[]
  // 是否需要显示多租户成员
  isEnableDisplayName?: boolean
}

const {
  userId = '',
  isEnableDisplayName = false,
} = defineProps<IUserDisplayNameProps>();

const slots = useSlots();

const isEnabledUserName = computed(() => isEnableDisplayName && Boolean(userId));
</script>
