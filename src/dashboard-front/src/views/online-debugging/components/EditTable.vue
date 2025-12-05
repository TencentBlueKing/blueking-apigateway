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
  <BkTable
    class="variable-table"
    :cell-class="getCellClass"
    :checked="checkedList"
    :data="tableData"
    border="outer"
    row-hover="auto"
    @select="handleSelect"
    @select-all="handleSelectAll"
  >
    <BkTableColumn
      :width="55"
      type="selection"
      align="center"
    />
    <BkTableColumn
      :label="t('参数名')"
      prop="name"
    >
      <template #default="{ row, column, index }">
        <BkForm
          :ref="(el: HTMLElement | null) => setRefs(el, 'name-', index)"
          :model="row"
          label-width="0"
          class="table-cell-form"
        >
          <BkFormItem
            property="name"
            error-display-type="tooltips"
            class="table-form-item"
          >
            <BkInput
              v-if="type !== 'headers'"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `name-input-`, index, column?.index)"
              v-model="row.name"
              :clearable="false"
              class="edit-input"
            />
            <BkSelect
              v-else
              :ref="(el: HTMLElement | null) => setInputRefs(el, `name-input-`, index, column?.index)"
              :key="componentKey"
              v-model="row.name"
              class="edit-select"
              allow-create
              filterable
              @change="() => handleNameChange(index, row.name)"
              @input="() => handleHeaderKeySelectBlur(row, `name-input-`, index, column?.index)"
              @blur="() => handleHeaderKeySelectBlur(row, `name-input-`, index, column?.index)"
              @select="(value: string) => handleHeaderKeySelect(row, value)"
            >
              <BkOption
                v-for="item in headersNameList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </BkSelect>
          </BkFormItem>
        </BkForm>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('参数值')"
      prop="value"
    >
      <template #default="{ row, column, index }">
        <BkForm
          :ref="(el: HTMLElement | null) => setRefs(el, `value-`, index)"
          :model="row"
          label-width="0"
          class="table-cell-form"
        >
          <BkFormItem
            property="value"
            error-display-type="tooltips"
            class="table-form-item"
          >
            <BkSelect
              v-if="!!row?.options?.length"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `value-input-`, index, column?.index)"
              v-model="row.value"
              class="edit-select"
              :clearable="false"
            >
              <BkOption
                v-for="item in row.options"
                :id="item"
                :key="item"
                :name="item"
              />
            </BkSelect>
            <BkInput
              v-else
              :ref="(el: HTMLElement | null) => setInputRefs(el, 'value-input-', index, column?.index)"
              v-model="row.value"
              :clearable="false"
              class="edit-input"
            />
          </BkFormItem>
        </BkForm>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('类型')"
      prop="type"
    >
      <template #default="{ row, column, index }">
        <BkForm
          :ref="(el: HTMLElement | null) => setRefs(el, 'type-', index)"
          :model="row"
          label-width="0"
          class="table-cell-form"
        >
          <BkFormItem
            property="type"
            error-display-type="tooltips"
            class="table-form-item"
          >
            <BkSelect
              :ref="(el: HTMLElement | null) => setInputRefs(el, 'type-input-', index, column?.index)"
              v-model="row.type"
              class="edit-select"
              :clearable="false"
              :filterable="false"
            >
              <BkOption
                v-for="item in typeList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </BkSelect>
          </BkFormItem>
        </BkForm>
      </template>
    </BkTableColumn>
    <BkTableColumn
      :label="t('说明')"
      prop="instructions"
    >
      <template #default="{ row, column, index }">
        <BkForm
          :ref="(el: HTMLElement | null) => setRefs(el, 'instructions-', index)"
          :model="row"
          label-width="0"
          class="table-cell-form"
        >
          <BkFormItem
            property="instructions"
            error-display-type="tooltips"
            class="table-form-item"
          >
            <BkInput
              :ref="(el: HTMLElement | null) => setInputRefs(el, 'instructions-input-', index, column?.index)"
              v-model="row.instructions"
              :clearable="false"
              class="edit-input"
            />
          </BkFormItem>
        </BkForm>
      </template>
    </BkTableColumn>
    <BkTableColumn :label="t('操作')">
      <template #default="{ index }">
        <AgIcon
          class="tb-btn add-btn"
          name="plus-circle-shape"
          @click="() => addRow(index)"
        />
        <AgIcon
          class="tb-btn delete-btn"
          name="minus-circle-shape"
          @click="() => delRow(index)"
        />
      </template>
    </BkTableColumn>
  </BkTable>
</template>

<script lang="ts" setup>
import { useFeatureFlag, useUserInfo } from '@/stores';
import { Message } from 'bkui-vue';
import AgIcon from '@/components/ag-icon/Index.vue';
import headersNames from '@/constants/headers-name';
import headersValues from '@/constants/headers-value';

interface IProps {
  list?: Array<IRowType>
  type?: string
}

interface IRowType {
  id?: number | string
  name: string
  value: string
  type: string
  instructions: string
  required?: boolean
  options?: unknown
  default?: string
}

interface ISelectPayload {
  row: IRowType
  index: number
  checked: boolean
  data: IRowType[]
}

const {
  list = [],
  type = '',
} = defineProps<IProps>();

const emit = defineEmits<{ change: [data: IRowType[]] }>();

const { t } = useI18n();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

const getDefaultTbRow = () => {
  return {
    name: '',
    value: '',
    type: 'string',
    instructions: '',
  };
};
const tableData = ref<IRowType[]>(list?.length ? list : [getDefaultTbRow()]);
const checkedList = ref<IRowType[]>([]);
const typeList = ref<{
  label: string
  value: string
}[]>([
  {
    label: 'string',
    value: 'string',
  },
  {
    label: 'number',
    value: 'number',
  },
  {
    label: 'boolean',
    value: 'boolean',
  },
]);

const componentKey = ref(0);

const formRefs = ref(new Map());
const setRefs = (el: HTMLElement | null, prefix: string, index: number) => {
  if (el && index !== undefined) {
    formRefs.value?.set(`${prefix}${index}`, el);
  }
};

const formInputRef = ref(new Map());
const setInputRefs = (el: HTMLElement | null, prefix: string, index: number, columnIndex: number) => {
  if (el && index !== undefined && columnIndex !== undefined) {
    formInputRef.value?.set(`${prefix}${index}-${columnIndex}`, el);
  }
};

const headersNameList = computed(() => (headersNames.map((item: string) => ({
  label: item,
  value: item,
}))));

const generateUniqueId = () => {
  return `${Date.now().toString(36)}-${Math.random().toString(36).substring(2)}`;
};

const getCellClass = (payload: { index: number }) => {
  if (payload.index !== 5) {
    return 'custom-table-cell';
  }
  return '';
};

const handleNameChange = (index: number, name: string) => {
  if (['Accept', 'Content-Type'].includes(name)) {
    tableData.value[index].options = headersValues;
  }
  else {
    tableData.value[index].options = [];
  }

  tableData.value[index].value = '';
};

const addRow = (index: number) => {
  const row = {
    ...getDefaultTbRow(),
    id: generateUniqueId(),
  };
  tableData.value?.splice(index + 1, 0, row);
  checkedList.value = [...checkedList.value, row];
};

const delRow = (index: number) => {
  if (tableData.value.length === 1) {
    Message({
      theme: 'warning',
      message: t('至少需要保留一行！'),
    });
    return;
  }
  const row = tableData.value[index];
  checkedList.value = checkedList.value.filter(item => item.id !== row.id);
  tableData.value?.splice(index, 1);
};

const validate = async () => {
  const list = tableData.value;
  let flag = true;

  list?.forEach(async (item: IRowType) => {
    if (item?.required) {
      if (!item.name) {
        flag = false;
        Message({
          theme: 'error',
          message: t('请确认{name}参数名输入正确', { name: item.name }),
        });
      }

      if (!item.value) {
        flag = false;
        Message({
          theme: 'error',
          message: t('请确认{name}参数值输入正确', { name: item.name }),
        });
      }
    }
  });
  return flag;
};

const getTableData = () => {
  return checkedList.value;
};

const handleSelect = ({ row, checked }: ISelectPayload) => {
  if (checked) {
    checkedList.value = [...checkedList.value, row];
  }
  else {
    const { id } = row;
    checkedList.value = checkedList.value?.filter(item => item.id !== id);
  }
};

const handleSelectAll = ({ checked, data }: ISelectPayload) => {
  if (checked) {
    checkedList.value = data;
  }
  else {
    checkedList.value = [];
  }
};

watch(
  () => list,
  (v) => {
    const list: IRowType[] = [];
    v?.forEach((item: any) => {
      list.push({
        id: generateUniqueId(),
        name: item.name,
        value: item.schema?.default || item.value || '',
        instructions: item.description || item.instructions,
        required: !!item.required,
        type: item.schema?.type || item.type || 'string',
        options: item.schema?.enum || item.options || [],
        default: item.schema?.default || item.default,
      });
    });

    if (!list?.length) {
      tableData.value = [{
        ...getDefaultTbRow(),
        id: generateUniqueId(),
      }];
    }
    else {
      tableData.value = list;
    }

    if (type === 'headers' && featureFlagStore.isTenantMode) {
      tableData.value.unshift({
        id: generateUniqueId(),
        name: 'x-bk-tenant-id',
        value: userStore.info?.tenant_id || '',
        instructions: t('租户id'),
        required: false,
        type: 'string',
        default: userStore.info?.tenant_id || '',
      });
    }

    checkedList.value = [...tableData.value];
  },
  {
    deep: true,
    immediate: true,
  },
);

watch(
  () => tableData.value,
  () => {
    emit('change', checkedList.value);
  },
  {
    deep: true,
    immediate: true,
  },
);

// Headers 选择器失焦后，去获取用户手动输入的值
const handleHeaderKeySelectBlur = (row: IRowType, inputRefNamePrefix: string, index: number, columnIndex: number) => {
  try {
    if (inputRefNamePrefix && index !== undefined && columnIndex !== undefined) {
      const selectRef = formInputRef.value.get(`${inputRefNamePrefix}${index}-${columnIndex}`);
      if (!selectRef?.curSearchValue) {
        row.name = '';
        selectRef?.handleClear();
      }
      else {
        row.name = selectRef?.curSearchValue || '';
      }
    }
  }
  catch (error) {
    console.log(error);
  }
};

const handleHeaderKeySelect = (row: IRowType, value: string) => {
  setTimeout(() => {
    row.name = value;
    componentKey.value += 1;
  });
};

defineExpose({
  validate,
  getTableData,
});
</script>

<style lang="scss" scoped>
.tb-btn {
  font-size: 14px;
  color: #C4C6CC;
  cursor: pointer;
  &:hover {
    color: #979BA5;
  }
  &.add-btn {
    margin-right: 16px;
  }
}

.edit-input.bk-input {
  border: none;
  height: 100%;
  &.is-focused:not(.is-readonly) {
    border: 1px solid #3A84FF;
    box-shadow: none;
  }
  &:hover {
    border: 1px solid #A3C5FD;
  }
}

.edit-select {
  height: 100%;
  :deep(.bk-select-trigger) {
    height: 100%;
  }
  :deep(.bk-input) {
    border: none;
    height: 100%;
    border-radius: 0px;
    .angle-up {
      display: none !important;
    }
    &:hover {
      border: 1px solid #A3C5FD;
      .angle-up {
        display: inline-flex !important;
      }
    }
  }
  &.is-focus {
    :deep(.bk-input) {
    border: 1px solid #3A84FF;
    .angle-up {
      display: inline-flex !important;
    }
  }
  }
}

.variable-table {
  .td-text {
    //padding: 0 16px;
  }

  :deep(.bk-form-error-tips) {
    transform: translate(-50%, 4px);
  }

  :deep(.bk-form.table-cell-form) {
    line-height: 42px;
    .bk-form-item.table-form-item {
      margin-bottom: 0;
      .bk-form-content {
        line-height: 42px !important;
        .bk-input {
          height: 42px;
          line-height: 42px;
          border: 0;
          .bk-input--text {
            //padding: 0 16px;
          }
        }
        .edit-input.bk-input {
          border-radius: 0px;
          &:hover {
            border: 1px solid #A3C5FD;
          }
          &.is-focused {
            border: 1px solid #3A84FF;
          }
        }
        .bk-select {
          &:hover {
            .bk-input {
              border: 1px solid #A3C5FD;
            }
          }
          &.is-focus {
            .bk-input {
              border: 1px solid #3A84FF;
            }
          }
        }
      }
      &.is-error {
        .bk-form-content {
          .bk-input--text {
            background: #FFEEEE;
          }
        }
      }
    }
  }

  :deep(.bk-table-body-content) {
    .custom-table-cell {
      .cell {
        padding: 0;
        &:hover {
          cursor: pointer;
        }
      }
    }
  }

  :deep(.bk-scrollbar .bk__rail-x) {
    display: none;
    opacity: 0
  }
}
</style>
