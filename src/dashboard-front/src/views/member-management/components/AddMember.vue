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
    :title="t('新增成员')"
    :width="720"
    quick-close
    render-directive="if"
  >
    <div class="member-add-slider">
      <BkForm
        form-type="vertical"
        :model="formData"
      >
        <BkFormItem
          :label="t('用户名')"
          property="usernames"
          required
          :error-display-type="'normal'"
        >
          <MemberSelector
            v-if="!featureFlagStore.isTenantMode"
            v-model="formData.usernames"
            :placeholder="t('请输入人员名称搜索')"
            has-delete-icon
            @change="handleMemberChange"
          />
          <BkUserSelector
            v-else
            v-model="formData.usernames"
            :api-base-url="envStore.tenantUserDisplayAPI"
            multiple
            :tenant-id="userStore.info.tenant_id || ''"
            @change="handleTenantUserChange"
          />
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
import MemberSelector from '@/components/member-selector';
import BkUserSelector from '@blueking/bk-user-selector';
import { createGatewayMembers } from '@/services/source/gateway-member.ts';
import { useEnv, useFeatureFlag, useGateway, useUserInfo } from '@/stores';
import PermissionModel from './PermissionModel.vue';
import {
  getRoleLabel,
  getRolePermissions,
} from '../utils';
import { MEMBER_ROLES, type MemberRole } from '@/constants/gateway-permission';

const isShow = defineModel<boolean>('isShow', { default: false });

const emit = defineEmits<{
  done: []
}>();

const { t } = useI18n();
const route = useRoute();
const gatewayStore = useGateway();
const userStore = useUserInfo();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();

const submitting = ref(false);
const formData = ref<{
  usernames: string[]
  role: MemberRole
}>({
  usernames: [],
  role: 'operator',
});

const apigwId = computed(() => Number(route.params.id));
const isAIGateway = computed(() => gatewayStore.isAIGateway);

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
    usernames: [],
    role: 'operator',
  };
};

const handleMemberChange = (member: string[]) => {
  formData.value.usernames = member;
};

const handleTenantUserChange = (members: { id: string }[]) => {
  formData.value.usernames = members.map(member => member.id);
};

const handleCancel = () => {
  isShow.value = false;
};

const handleConfirm = async () => {
  if (submitting.value) {
    return;
  }
  if (!formData.value.usernames.length) {
    Message({
      theme: 'error',
      message: t('请选择人员'),
    });
    return;
  }

  submitting.value = true;
  try {
    const data = [...new Set(formData.value.usernames)].map(username => ({
      username,
      role: formData.value.role,
    }));
    const { created, skipped } = await createGatewayMembers(apigwId.value, data);
    Message({
      theme: skipped.length ? 'warning' : 'success',
      message: skipped.length
        ? t('已添加 {created} 名成员，以下成员已存在，已跳过并保留原角色：{usernames}', {
          created: created.length,
          usernames: skipped.map(member => member.username).join(', '),
        })
        : t('添加成功'),
    });
    isShow.value = false;
    emit('done');
  }
  catch {
    // 错误由统一 HTTP 封装提示，保留表单以便重试。
  }
  finally {
    submitting.value = false;
  }
};

</script>

<style lang="scss" scoped>
.member-add-slider {
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
