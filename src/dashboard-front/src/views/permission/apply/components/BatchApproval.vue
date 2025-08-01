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
  <BkDialog
    :is-show="batchApplyDialogConf.isShow"
    theme="primary"
    :mask-close="false"
    :width="670"
    :loading="batchApplyDialogConf.isLoading"
    :title="title"
    @closed="handleClose"
  >
    <template #default>
      <BkTable
        :key="selections.length"
        :data="selections"
        :size="'small'"
        :max-height="200"
        :columns="approvalColumns"
        show-overflow-tooltip
      />
      <BkForm
        ref="batchApprovalFormRef"
        :label-width="0"
        :model="formData"
        class="m-t-20px"
      >
        <BkFormItem
          label=""
          :rules="
            [
              {
                required: true,
                message: t('必填项'),
                trigger: 'blur',
              },
            ]
          "
          required
          property="comment"
        >
          <BkInput
            v-model="formData.comment"
            type="textarea"
            :placeholder="t('请输入备注')"
            :maxlength="100"
          />
        </BkFormItem>
      </BkForm>
    </template>
    <template #footer>
      <BkButton
        theme="primary"
        :loading="['approved'].includes(formData.status) && batchApplyDialogConf.isLoading"
        @click="handleApprovedPermission"
      >
        {{ t("全部通过") }}
      </BkButton>
      <BkButton
        :loading="['rejected'].includes(formData.status) && batchApplyDialogConf.isLoading"
        class="m-l-4px"
        @click="handleRejectPermission"
      >
        {{ t("全部驳回") }}
      </BkButton>
      <BkButton
        class="m-l-4px"
        @click="handleClose"
      >
        {{ t("取消") }}
      </BkButton>
    </template>
  </BkDialog>
</template>

<script lang="ts" setup>
import { t } from '@/locales';

interface IProps {
  title?: string
  selections?: any[]
  dialogParams?: {
    isShow: boolean
    isLoading: boolean
  }
  actionParams?: {
    status: string
    comment?: string
    ids: number[]
    part_resource_ids: Record<string, unknown>
  }
}

interface Emits {
  (e: 'approved'): void
  (e: 'rejected'): void
  (e: 'update:dialogParams', value: {
    isShow: boolean
    isLoading: boolean
  })
  (e: 'update:actionParams', value: {
    status: string
    comment?: string
    ids: number[]
    part_resource_ids: Record<string, unknown>
  })
}

type FormMethod = { validate: () => void };

const {
  title = '',
  dialogParams = {
    isShow: false,
    isLoading: false,
  },
  actionParams = {
    ids: [],
    status: '',
    comment: '',
    part_resource_ids: {},
  },
  selections = [],
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const batchApprovalFormRef = ref<InstanceType<typeof BkForm> & FormMethod>();
const approvalColumns = shallowRef([
  {
    label: t('蓝鲸应用ID'),
    field: 'bk_app_code',
  },
  {
    label: t('申请人'),
    field: 'applied_by',
  },
  {
    label: t('申请时间'),
    field: 'created_time',
  },
]);

const batchApplyDialogConf = computed({
  get: () => dialogParams,
  set: (params) => {
    emits('update:dialogParams', params);
  },
});

const formData = computed({
  get: () => actionParams,
  set: (form) => {
    emits('update:actionParams', form);
  },
});

// 全部通过
const handleApprovedPermission = async () => {
  await batchApprovalFormRef.value?.validate();
  emits('approved');
};

// 全部驳回
const handleRejectPermission = async () => {
  await batchApprovalFormRef.value?.validate();
  emits('rejected');
};

const handleClose = () => {
  batchApplyDialogConf.value.isShow = false;
};

defineExpose({
  batchApprovalFormRef,
  handleClose,
});
</script>
