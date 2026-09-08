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
    :title="t('变更角色')"
    :width="720"
    quick-close
    render-directive="if"
  >
    <div class="member-change-slider">
      <BkForm
        form-type="vertical"
        :model="formData"
      >
        <BkFormItem
          :label="t('用户名')"
          property="username"
        >
          <span v-if="!featureFlagStore.isEnableDisplayName">{{ formData.username }}</span>
          <span v-else><bk-user-display-name :user-id="formData.username" /></span>
        </BkFormItem>
        <BkFormItem
          :label="t('角色')"
          property="role"
          required
        >
          <BkRadioGroup v-model="formData.role">
            <BkRadio
              v-for="role in MEMBER_ROLES"
              :key="role"
              :label="role"
            >
              {{ getRoleLabel(role) }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>
      </BkForm>

      <div class="permission-summary">
        <div class="summary-title">
          {{ t('权限内容') }}
        </div>
        <div class="summary-list">
          {{ summaryText }}
        </div>
      </div>

      <PermissionModel
        v-model:highlight-role="formData.role"
        :ai-gateway="isAIGateway"
      />
    </div>
    <template #footer>
      <div class="slider-footer">
        <BkButton
          theme="primary"
          class="min-w-88px"
          :loading="submitting"
          @click="handleConfirm"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton
          class="min-w-88px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </BkSideslider>
</template>

<script setup lang="ts">
import { Message } from 'bkui-vue';
import { usePopInfoBox } from '@/hooks';
import { updateGatewayMember } from '@/services/source/gateway-member.ts';
import { useFeatureFlag, useGateway, useUserInfo } from '@/stores';
import PermissionModel from './PermissionModel.vue';
import type { IMember } from '../types';
import {
  getRoleLabel,
  getRolePermissions,
} from '../utils';
import { MEMBER_ROLES, type MemberRole } from '@/constants/gateway-permission';

interface IProps {
  adminCount?: number
  member?: IMember
}

const isShow = defineModel<boolean>('isShow', { default: false });

const {
  adminCount = 0,
  member = undefined,
} = defineProps<IProps>();

const emit = defineEmits<{
  done: [member: IMember]
}>();

const { t } = useI18n();
const route = useRoute();
const gatewayStore = useGateway();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

const submitting = ref(false);
const formData = ref<{
  username: string
  role: MemberRole
}>({
  username: '',
  role: 'operator',
});

const apigwId = computed(() => Number(route.params.id));
const isAIGateway = computed(() => gatewayStore.isAIGateway);
const currentUsername = computed(() => userStore.info.username);

const summaryText = computed(() => {
  return getRolePermissions(formData.value.role, isAIGateway.value)
    .map(item => item.label)
    .join(', ');
});

watch(isShow, () => {
  if (isShow.value) {
    resetForm();
  }
});

const resetForm = () => {
  formData.value = {
    username: member?.username || '',
    role: member?.role || 'operator',
  };
};

const handleCancel = () => {
  isShow.value = false;
};

const persist = async (memberId: number, role: MemberRole) => {
  if (submitting.value) {
    return false;
  }
  submitting.value = true;
  try {
    const updatedMember = await updateGatewayMember(apigwId.value, memberId, { role });
    isShow.value = false;
    Message({
      theme: 'success',
      message: t('角色变更成功'),
    });
    emit('done', updatedMember);
    return true;
  }
  catch {
    // 错误由统一 HTTP 封装提示，保留表单/确认框以便重试。
    return false;
  }
  finally {
    submitting.value = false;
  }
};

const handleConfirm = async () => {
  const { username, role } = formData.value;
  if (!member || submitting.value) {
    return;
  }
  if (member.role === role) {
    isShow.value = false;
    return;
  }

  if (member.role === 'administrator' && role !== 'administrator' && adminCount <= 1) {
    Message({
      theme: 'error',
      message: t('至少保留一名管理员'),
    });
    return;
  }

  const memberId = member.id;
  if (username === currentUsername.value && role !== 'administrator') {
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: () => t('确认移除自己的管理员权限？'),
      subTitle: t('您已将自己从管理员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！'),
      confirmText: t('确定'),
      cancelText: t('取消'),
      beforeClose: action => action === 'confirm' ? persist(memberId, role) : true,
    });
    return;
  }

  await persist(memberId, role);
};

</script>

<style lang="scss" scoped>
.member-change-slider {
  padding: 20px 24px 8px;
}

.permission-summary {
  padding: 12px 16px;
  margin: 8px 0 16px;
  font-size: 12px;
  line-height: 20px;
  color: #63656e;
  background: #f5f7fa;
  border-radius: 2px;
}

.summary-title {
  margin-bottom: 8px;
  font-weight: 700;
  color: #313238;
}

.slider-footer {
  display: flex;
  gap: 8px;
}
</style>
