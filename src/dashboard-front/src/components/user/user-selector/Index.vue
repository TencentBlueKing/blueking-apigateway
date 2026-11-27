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

<!--
  人员选择器：多租户模式使用 BkUserSelector（当前租户的用户接口），否则使用 StaffSelector。
  v-model 与 change 事件统一为用户名数组；单选时数组至多一个元素。
  未声明的属性（class、copyable 等）透传给实际渲染的选择器。
-->
<template>
  <component
    :is="featureFlagStore.isTenantMode ? BkUserSelector : StaffSelector"
    v-bind="selectorProps"
    @change="handleChange"
  />
</template>

<script lang="ts" setup>
import BkUserSelector from '@blueking/bk-user-selector';
import StaffSelector from '@/components/user/staff-selector';
import { useEnv, useFeatureFlag, useUserInfo } from '@/stores';

interface IProps {
  multiple?: boolean
  // 未传时两种模式各自使用组件默认占位文本
  placeholder?: string
  // 仅 StaffSelector 支持
  hasDeleteIcon?: boolean
}

interface IEmits { change: [usernames: string[]] }

interface ISelectedUser { id: string }

const modelValue = defineModel<string[]>({ default: () => [] });

const {
  multiple = true,
  placeholder = undefined,
  hasDeleteIcon = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const envStore = useEnv();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

const selectorProps = computed(() => {
  if (featureFlagStore.isTenantMode) {
    return {
      // BkUserSelector 单选绑定字符串，多选绑定数组
      modelValue: multiple ? modelValue.value : (modelValue.value[0] ?? ''),
      apiBaseUrl: envStore.tenantUserDisplayAPI,
      tenantId: userStore.info.tenant_id || '',
      multiple,
      placeholder,
    };
  }
  return {
    modelValue: modelValue.value,
    multiple,
    placeholder,
    hasDeleteIcon,
  };
});

// StaffSelector 的 change 返回用户名数组；BkUserSelector 返回用户对象（单选为对象，可能为 null）
const handleChange = (value: string[] | ISelectedUser | ISelectedUser[] | null) => {
  let usernames: string[] = [];
  if (featureFlagStore.isTenantMode) {
    const users = value ? (Array.isArray(value) ? value : [value]) : [];
    usernames = (users as ISelectedUser[]).map(user => user.id);
  }
  else {
    usernames = (value as string[] | null) ?? [];
  }
  modelValue.value = usernames;
  emit('change', usernames);
};
</script>
