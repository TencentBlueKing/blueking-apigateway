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
  <BkDialog
    :is-show="batchApplyDialogConf.isShow"
    theme="primary"
    :mask-close="false"
    :width="640"
    :loading="batchApplyDialogConf.isLoading"
    :title="title"
    @closed="handleClose"
  >
    <template #default>
      <AgTable
        v-model:table-data="tableData"
        local-page
        show-cell-empty-content
        :size="'small'"
        :max-height="300"
        :columns="approvalColumns"
      />
      <BkForm
        ref="batchApprovalFormRef"
        :model="formData"
        form-type="vertical"
        class="m-t-20px"
      >
        <BkFormItem
          :label="t('备注')"
          :rules="
            [
              {
                required: true,
                message: t('请输入备注'),
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
        :loading="['approved'].includes(formData.status ?? '') && batchApplyDialogConf.isLoading"
        @click="handleApprovedPermission"
      >
        {{ t("全部通过") }}
      </BkButton>
      <BkButton
        :loading="['rejected'].includes(formData.status ?? '') && batchApplyDialogConf.isLoading"
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

<script lang="tsx" setup>
import { Form } from 'bkui-vue';
import type { TableRowData } from '@blueking/tdesign-ui';
import { t } from '@/locales';
import type { IFormMethod } from '@/types/common';
import { useFeatureFlag } from '@/stores';
import AgTable from '@/components/ag-table/Index.vue';

type IDialogParams = {
  isShow: boolean
  isLoading: boolean
};

type IActionParams = {
  status?: string
  comment?: string
  ids?: number[]
  part_resource_ids?: Record<string, unknown>
};

interface IProps {
  title?: string
  selections?: any[]
  dialogParams?: IDialogParams
  actionParams?: IActionParams
}

interface IEmits {
  (e: 'approved'): void
  (e: 'rejected'): void
  (e: 'update:dialogParams', value: IDialogParams): void
  (e: 'update:actionParams', value: IActionParams): void
}

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

const emits = defineEmits<IEmits>();

const featureFlagStore = useFeatureFlag();

const batchApprovalFormRef = ref<InstanceType<typeof Form> & IFormMethod>();
const approvalColumns = shallowRef([
  {
    title: t('蓝鲸应用ID'),
    colKey: 'bk_app_code',
    ellipsis: true,
  },
  {
    title: t('申请人'),
    colKey: 'applied_by',
    ellipsis: true,
    cell: (_: unknown, { row }: { row: TableRowData }) =>
      featureFlagStore.isEnableDisplayName && !!row.applied_by
        ? <span><bk-user-display-name user-id={row.applied_by} /></span>
        : <span>{row.applied_by || '--'}</span>,
  },
  {
    title: t('申请时间'),
    colKey: 'created_time',
    ellipsis: true,
    width: 260,
  },
]);

const tableData = computed(() => selections);

const batchApplyDialogConf = computed({
  get: () => dialogParams,
  set: (params: IDialogParams) => {
    emits('update:dialogParams', params);
  },
});

const formData = computed({
  get: () => actionParams,
  set: (form: IActionParams) => {
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
  batchApprovalFormRef.value?.clearValidate();
};

defineExpose({
  batchApprovalFormRef,
  handleClose,
});
</script>
