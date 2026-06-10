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
  <BkDialog
    :is-show="applyActionDialogConf.isShow"
    theme="primary"
    :width="640"
    :quick-close="false"
    header-position="left"
    :title="applyActionDialogConf.title"
    :loading="applyActionDialogConf.isLoading"
    @confirm="handleSubmitApprove"
    @closed="handleClose"
  >
    <BkForm
      ref="approveFormRef"
      :label-width="90"
      :model="formData"
      :rules="rules"
      class="mt-8px mr-16px mb-24px"
    >
      <BkFormItem
        label="备注"
        property="comment"
        required
      >
        <BkAlert
          v-if="isGateway"
          class="mb-12px"
          :theme="alertTheme"
          :title="approveFormMessage"
        />
        <BkInput
          v-model="formData.comment"
          type="textarea"
          placeholder="请输入备注"
          :rows="4"
          :maxlength="100"
        />
      </BkFormItem>
    </BkForm>
  </BkDialog>
</template>

<script lang="ts" setup>
import { Form } from 'bkui-vue';
import { t } from '@/locales';
import type { IFormMethod } from '@/types/common';
import type { IFomDataQuery, IPermission } from '@/services/types/query/personal-workbench.ts';

type IDialogConfig = {
  isShow: boolean
  isLoading: boolean
  title: string
};

interface IProps {
  isGateway?: boolean
  curPermission: IPermission
}

interface IEmits {
  (e: 'approved'): [void]
}

// 表单数据
const formData = defineModel<IFomDataQuery>('formData', {
  type: Object,
  default: () => ({
    ids: [],
    status: '',
    comment: '',
    part_resource_ids: {},
  }),
});

// 弹窗配置
const applyActionDialogConf = defineModel<IDialogConfig>('dialogConfig', {
  type: Object,
  default: () => ({
    isShow: false,
    isLoading: false,
    title: '',
  }),
});

const { curPermission, isGateway = true } = defineProps<IProps>();

const emits = defineEmits<IEmits>();

// 表单校验规则
const rules = {
  comment: [
    {
      required: true,
      message: t('请输入备注'),
      trigger: 'blur',
    },
  ],
};

const approveFormRef = ref<InstanceType<typeof Form> & IFormMethod>();

// 警告框主题
const alertTheme = computed(() => {
  if (curPermission.grant_dimension === 'api') {
    return formData.value.status === 'approved' ? 'warning' : 'error';
  }
  return 'warning';
});

// 提示文案
const approveFormMessage = computed(() => {
  const {
    bk_app_code = '',
    selection = [],
    resources = [],
  } = curPermission ?? {};
  const selectLength = selection.length;
  const resourceLength = resources.length;
  const isApproved = formData.value.status === 'approved';

  if (curPermission.grant_dimension === 'api') {
    if (isApproved) {
      return t('应用将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批');
    }
    return t('应用将按网关申请全部驳回');
  }

  if (isApproved) {
    if (selectLength && selectLength < resourceLength) {
      const rejectLength = resourceLength - selectLength;
      return t('应用{bk_app_code} 申请{resourceLength}个权限，通过{selectLength}个，驳回{rejectLength}个', {
        bk_app_code,
        resourceLength,
        selectLength,
        rejectLength,
      });
    }

    return t('应用{bk_app_code} 申请{resourceLength}个权限，全部通过', {
      bk_app_code,
      resourceLength,
    });
  }
  return t('应用{bk_app_code} 申请{resourceLength}个权限，全部驳回', {
    bk_app_code,
    resourceLength,
  });
});

// 提交审批
const handleSubmitApprove = async () => {
  await approveFormRef.value?.validate();
  emits('approved');
};

// 关闭弹窗
const handleClose = () => {
  approveFormRef.value?.clearValidate();
  applyActionDialogConf.value.isShow = false;
};

defineExpose({
  approveFormRef,
  handleClose,
});
</script>
