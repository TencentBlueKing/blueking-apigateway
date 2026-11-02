<template>
  <div class="user-rate-limit-form">
    <BkAlert
      v-if="errorMessage"
      class="mb-16px"
      theme="error"
      :title="t(errorMessage)"
    />
    <BkForm
      v-if="!initializationError"
      ref="formRef"
      :model="formData"
      autocomplete="off"
      @validate="handleValidate"
    >
      <section class="rate-limit-card">
        <h3 class="rate-limit-title">
          {{ t('默认用户频率限制') }}
        </h3>
        <div class="rate-limit-row">
          <BkFormItem
            :label="t('次数')"
            :label-width="90"
            property="default.tokens"
            :rules="positiveIntegerRules"
            required
          >
            <BkInput
              :model-value="formData.default.tokens"
              type="number"
              :min="1"
              :precision="0"
              @update:model-value="(value: string | number | null) => formData.default.tokens = Number(value)"
            />
          </BkFormItem>
          <BkFormItem
            :label="t('时间范围')"
            :label-width="90"
            property="default.period"
            :rules="positiveIntegerRules"
            required
          >
            <BkSelect
              v-model="formData.default.period"
              :clearable="false"
            >
              <BkOption
                v-for="option in getPeriodOptions(formData.default.period)"
                :id="option.value"
                :key="option.value"
                :name="option.label"
              />
            </BkSelect>
          </BkFormItem>
        </div>
      </section>

      <section class="rate-limit-card">
        <h3 class="rate-limit-title">
          {{ t('特殊用户频率限制') }}
        </h3>
        <div
          v-for="(row, index) in formData.specials"
          :key="row.id"
          class="rate-limit-row special-rate-limit-row"
        >
          <BkFormItem
            :label="t('次数')"
            :label-width="90"
            :property="`specials[${index}].tokens`"
            :rules="positiveIntegerRules"
            required
          >
            <BkInput
              :model-value="row.tokens"
              type="number"
              :min="1"
              :precision="0"
              @update:model-value="(value: string | number | null) => row.tokens = Number(value)"
            />
          </BkFormItem>
          <BkFormItem
            :label="t('时间范围')"
            :label-width="90"
            :property="`specials[${index}].period`"
            :rules="positiveIntegerRules"
            required
          >
            <BkSelect
              v-model="row.period"
              :clearable="false"
            >
              <BkOption
                v-for="option in getPeriodOptions(row.period)"
                :id="option.value"
                :key="option.value"
                :name="option.label"
              />
            </BkSelect>
          </BkFormItem>
          <BkFormItem
            :label="t('用户名')"
            :label-width="75"
            :property="`specials[${index}].username`"
            :rules="getUsernameRules(row)"
            required
          >
            <MemberSelector
              v-if="!featureFlagStore.isTenantMode"
              :model-value="row.username ? [row.username] : []"
              :multiple="false"
              :placeholder="t('请输入人员名称搜索')"
              has-delete-icon
              @change="members => handleMemberChange(row, members)"
            />
            <BkUserSelector
              v-else
              :model-value="row.username"
              :api-base-url="envStore.tenantUserDisplayAPI"
              :tenant-id="userStore.info.tenant_id || ''"
              :multiple="false"
              :placeholder="t('请选择用户')"
              @change="members => handleTenantUserChange(row, members)"
            />
          </BkFormItem>
          <div class="row-actions">
            <AgIcon
              v-bk-tooltips="t('克隆')"
              name="copy"
              class="row-action"
              @click="cloneRow(row)"
            />
            <AgIcon
              v-bk-tooltips="t('删除')"
              name="delet"
              class="row-action"
              @click="removeRow(index)"
            />
          </div>
        </div>
        <BkButton
          text
          theme="primary"
          class="text-14px!"
          @click="addRow"
        >
          <i class="mr-5px apigateway-icon icon-ag-plus-circle-shape" />
          <span>{{ t('添加') }}</span>
        </BkButton>
      </section>
    </BkForm>
  </div>
</template>

<script setup lang="ts">
import type { Form } from 'bkui-vue';
import BkUserSelector from '@blueking/bk-user-selector';
import MemberSelector from '@/components/member-selector';
import { useEnv, useFeatureFlag, useUserInfo } from '@/stores';
import { PluginEditorError } from '@/components/plugin-manage/config-editor/form-adapter';
import {
  type IUserRateLimitFormData,
  type IUserRateLimitRow,
  createUserRateLimitRow,
  getUserRateLimitConfig,
  getUserRateLimitFormData,
  hasDuplicateUsername,
  isPositiveInteger,
} from './config';

interface IProps {
  data: Record<string, unknown>
}

interface ISelectedUser {
  id: string
}

const { data } = defineProps<IProps>();

const envStore = useEnv();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const { t } = useI18n();
const formData = ref<IUserRateLimitFormData>(getUserRateLimitFormData({}));
const initializationError = ref('');
const submissionError = ref('');
const formRef = ref<InstanceType<typeof Form>>();
const validatedUsernames = new Set<string>();

const errorMessage = computed(() => initializationError.value || submissionError.value);
const positiveIntegerRules = computed(() => [{
  required: true,
  message: t('请输入正整数'),
  trigger: 'change',
  validator: isPositiveInteger,
}]);

watch(() => data, () => {
  validatedUsernames.clear();
  initializationError.value = '';
  submissionError.value = '';
  try {
    formData.value = getUserRateLimitFormData(data);
  }
  catch {
    initializationError.value = '插件配置格式错误，请检查后重试';
  }
}, { immediate: true });

const getPeriodOptions = (period: number) => {
  const options = [
    {
      label: t('秒'),
      value: 1,
    },
    {
      label: t('分'),
      value: 60,
    },
    {
      label: t('时'),
      value: 3600,
    },
    {
      label: t('天'),
      value: 86400,
    },
  ];
  // 回显时保留已有的自定义时间窗口，避免将其替换为预设值。
  if (isPositiveInteger(period) && !options.some(option => option.value === period)) {
    options.push({
      label: `${period} ${t('秒')}`,
      value: period,
    });
  }
  return options;
};

const getUsernameRules = (row: IUserRateLimitRow) => [
  {
    required: true,
    message: t('请选择用户'),
    trigger: 'change',
    validator: () => !!row.username.trim(),
  },
  {
    message: t('用户名不能为 __default'),
    trigger: 'change',
    validator: () => row.username !== '__default',
  },
  {
    message: t('同一用户只能配置一条频率限制'),
    trigger: 'change',
    validator: () => !hasDuplicateUsername(formData.value.specials, row),
  },
];

const handleValidate = (property: string) => {
  if (property.endsWith('.username')) {
    validatedUsernames.add(property);
  }
};

const revalidateUsernames = async (currentRow: IUserRateLimitRow) => {
  // 只刷新当前用户名和已校验的用户名，选人后同步清除关联行的旧重复提示。
  // 次数和周期不参与用户名唯一性校验，未编辑的新行不提前展示错误。
  await nextTick();
  const fields = formData.value.specials.flatMap((row, index) => {
    const field = `specials[${index}].username`;
    return row.id === currentRow.id || validatedUsernames.has(field) ? [field] : [];
  });
  if (!fields.length) {
    return;
  }
  try {
    await formRef.value?.validate(fields);
  }
  catch {
    // 校验失败由对应表单项展示，不产生额外的全局错误提示。
  }
};

const updateUsername = (row: IUserRateLimitRow, username: string) => {
  row.username = username;
  submissionError.value = '';
  void revalidateUsernames(row);
};

const handleMemberChange = (row: IUserRateLimitRow, members: string[] | null) => {
  updateUsername(row, members?.[0] ?? '');
};

const handleTenantUserChange = (row: IUserRateLimitRow, members: ISelectedUser | ISelectedUser[] | null) => {
  const member = Array.isArray(members) ? members[0] : members;
  updateUsername(row, member?.id ?? '');
};

const clearValidate = () => {
  validatedUsernames.clear();
  submissionError.value = '';
  formRef.value?.clearValidate();
};

const addRow = () => {
  formData.value.specials.push(createUserRateLimitRow('', 200, 1));
};

const cloneRow = (row: IUserRateLimitRow) => {
  formData.value.specials.push(createUserRateLimitRow('', row.tokens, row.period));
};

const removeRow = (index: number) => {
  formData.value.specials.splice(index, 1);
  nextTick(clearValidate);
};

const getValue = async () => {
  submissionError.value = '';
  if (initializationError.value) {
    throw new PluginEditorError(initializationError.value);
  }
  if (!await formRef.value?.validate()) {
    throw new Error('表单校验失败');
  }
  try {
    return getUserRateLimitConfig(formData.value);
  }
  catch (error) {
    submissionError.value = error instanceof PluginEditorError ? error.message : '插件配置转换失败';
    throw error;
  }
};

defineExpose({
  getValue,
  clearValidate,
});
</script>

<style lang="scss" scoped>
.rate-limit-card {
  padding: 10px 20px 20px 16px;
  margin-bottom: 24px;
  background: #f5f7fa;
}

.rate-limit-title {
  display: flex;
  align-items: center;
  height: 50px;
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #63656e;
}

.rate-limit-row {
  position: relative;
  display: grid;
  grid-template-columns: 250px 200px;
  gap: 24px;
  padding: 10px 56px 10px 10px;
  margin-bottom: 24px;

  &.special-rate-limit-row {
    grid-template-columns: 250px 200px minmax(200px, 1fr);
    background: #fff;
  }

  :deep(.bk-form-item) {
    min-width: 0;
    margin-top: 0;
    margin-bottom: 0;
  }
}

.row-actions {
  position: absolute;
  top: 18px;
  right: 8px;
  display: flex;
  gap: 12px;
}

.row-action {
  color: #979ba5;
  cursor: pointer;

  &:hover {
    color: #3a84ff;
  }
}
</style>
