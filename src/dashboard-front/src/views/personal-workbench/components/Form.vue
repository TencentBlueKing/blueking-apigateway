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
  <div class="personal-workbench-form">
    <BkButton
      v-if="isShowSelection"
      v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: selectedRows.length > 0 }"
      theme="primary"
      :disabled="!selectedRows.length"
      class="batch-approval"
      @click="handleBatchApply"
    >
      {{ t("批量审批") }}
    </BkButton>

    <BkForm
      class="search-form"
      label-width="auto"
    >
      <BkFormItem
        :label="t('申请时间')"
        class="form-item form-item--date"
      >
        <DatePicker
          :key="dateKey"
          v-model="dateValue"
          type="datetimerange"
          clearable
          :placeholder="t('请选择申请时间')"
          use-shortcut-text
          :shortcuts="shortcutsRange"
          :shortcut-selected-index="shortcutSelectedIndex"
          @change="handleChange"
          @clear="handleClear"
          @shortcut-change="handleShortcutChange"
          @pick-success="handlePickerConfirm"
          @selection-mode-change="handleSelectionModeChange"
        />
      </BkFormItem>
      <BkFormItem
        :label="t('蓝鲸应用 ID')"
        class="form-item"
      >
        <BkInput
          v-model="formData.bk_app_code"
          clearable
          :placeholder="t('请输入应用 ID')"
        />
      </BkFormItem>
      <template v-if="isShowApplicant">
        <BkFormItem
          :label="t('申请人')"
          property="applied_by"
          :required="false"
          class="form-item"
        >
          <BkUserSelector
            v-if="featureFlagStore.isTenantMode"
            v-model="formData.applied_by"
            :api-base-url="envStore.tenantUserDisplayAPI"
            :tenant-id="getTenantId"
            :multiple="false"
            :placeholder="t('请输入用户')"
          />
          <StaffSelector
            v-else
            v-model="formData.applied_by"
            :class="[{ 'is-exist-member': formData.applied_by?.length > 0 }]"
            :copyable="false"
            :placeholder="t('请输入用户')"
            has-delete-icon
          />
        </BkFormItem>
      </template>
    </BkForm>
  </div>
</template>

<script setup lang="tsx">
import { DatePicker } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import type { FilterValue } from '@blueking/tdesign-ui';
import { t } from '@/locales';
import {
  useEnv,
  useFeatureFlag,
  useUserInfo,
} from '@/stores';
import { RECENT_DATE_PRESETS, useDatePicker } from '@/hooks';
import { DEFAULT_FORM_DATA } from '@/views/personal-workbench/common/constants';
import type { IPersonalWorkbenchFilter, IPersonalWorkbenchUIState } from '@/services/types/query/personal-workbench.ts';
import BkUserSelector from '@blueking/bk-user-selector';
import StaffSelector from '@/components/user/staff-selector';

interface IProps {
  isShowSelection?: boolean
  isShowApplicant?: boolean
  selectedRows?: IPersonalWorkbenchUIState[]
}

interface IEmits {
  'batch-approval': [void]
}

const formData = defineModel<FilterValue | IPersonalWorkbenchFilter>('formData', {
  type: Object,
  // 对象默认值需用工厂函数，避免各实例共享并修改同一个常量
  default: () => cloneDeep(DEFAULT_FORM_DATA),
});

const {
  isShowSelection = false,
  isShowApplicant = true,
  selectedRows = [],
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const envStore = useEnv();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleClear,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
  applySelectedRange,
  resetSelection,
} = useDatePicker(formData, { presets: ['today', ...RECENT_DATE_PRESETS] });

const dateKey = ref('dateKey');

const getTenantId = computed(() => userStore?.info?.tenant_id as string);

/**
 * 设置日期选择：计算本次查询的秒级区间并写入查询参数
 * - 未选择：清空时间条件
 * - 无法得到有效区间：提示错误，保留原有时间条件
 * @returns 时间条件是否有效
 */
const handleSearchTimeRange = () => applySelectedRange();

const handleBatchApply = () => {
  emit('batch-approval');
};

const handlePickerConfirm = () => {
  handleConfirm();
};

const handleResetFormData = () => {
  // 恢复默认（不限时间）后重建日期组件
  resetSelection();
  dateKey.value = String(+new Date());
  handleSearchTimeRange();
};

defineExpose({
  handleSearchTimeRange,
  handleResetFormData,
});
</script>

<style lang="scss" scoped>
.personal-workbench-form {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  min-height: 32px;
  flex-wrap: wrap;

  .batch-approval {
    flex-shrink: 0;
    width: auto;
  }

  .search-form {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 24px;
    flex: 1;
    min-width: 0;

    :deep(.bk-form-item) {
      margin: 0;
      display: flex;
      align-items: center;
      flex: 1;
      min-width: 0;
      max-width: fit-content;

      .bk-form-label {
        width: auto;
        white-space: nowrap;
        text-align: right;
        padding-right: 8px;
      }

      .bk-form-content {
        width: 230px;

        .bk-date-picker,
        .bk-input,
        .bk-user-selector,
        .member-selector {
          width: 100%;
        }
      }

      &.form-item--date .bk-form-content {
        // 选择具体时间范围后文本较长（约 300px），230px 会被截断
        width: 320px;
      }
    }
  }
}
</style>
