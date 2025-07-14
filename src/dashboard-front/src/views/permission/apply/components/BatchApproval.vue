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
    <BkTable
      :key="selections.length"
      :data="selections"
      :size="'small'"
      style="max-height: 200px"
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
