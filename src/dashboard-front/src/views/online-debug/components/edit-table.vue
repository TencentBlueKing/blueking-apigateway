<template>
  <bk-table
    class="variable-table"
    ref="bkTableRef"
    row-hover="auto"
    :data="tableData"
    :checked="checkedList"
    @select="handleSelect"
    @select-all="handleSelectAll"
    :cell-class="getCellClass"
    border="outer">
    <bk-table-column :width="55" type="selection" align="center" />
    <bk-table-column :label="t('参数名')" prop="name">
      <template #default="{ row, column, index }">
        <bk-form :ref="(el: HTMLElement | null) => setRefs(el, `name-${index}`)" :model="row" label-width="0">
          <bk-form-item
            property="name"
            error-display-type="tooltips"
            class="table-form-item">
            <bk-input
              v-if="type !== 'headers'"
              v-model="row.name"
              :clearable="false"
              class="edit-input"
              @blur="handleCellBlur(index)"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `name-input-${index}-${column?.index}`)"
            />
            <bk-select
              v-else
              class="edit-select"
              :clearable="false"
              v-model="row.name"
              @change="handleNameChange(index, row.name)"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `name-input-${index}-${column?.index}`)"
            >
              <bk-option
                v-for="item in headersNameList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </bk-select>
          </bk-form-item>
        </bk-form>
      </template>
    </bk-table-column>
    <bk-table-column :label="t('参数值')" prop="value">
      <template #default="{ row, column, index }">
        <bk-form :ref="(el: HTMLElement | null) => setRefs(el, `value-${index}`)" :model="row" label-width="0">
          <bk-form-item
            property="value"
            error-display-type="tooltips"
            class="table-form-item">
            <bk-select
              v-if="!!row?.options?.length"
              class="edit-select"
              :clearable="false"
              v-model="row.value"
              @change="handleCellBlur(index)"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `value-input-${index}-${column?.index}`)"
            >
              <bk-option
                v-for="item in row.options"
                :id="item"
                :key="item"
                :name="item"
              />
            </bk-select>
            <bk-input
              v-else
              v-model="row.value"
              :clearable="false"
              class="edit-input"
              @blur="handleCellBlur(index)"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `value-input-${index}-${column?.index}`)"
            />
          </bk-form-item>
        </bk-form>
      </template>
    </bk-table-column>
    <bk-table-column :label="t('类型')" prop="type">
      <template #default="{ row, column, index }">
        <bk-form :ref="(el: HTMLElement | null) => setRefs(el, `type-${index}`)" :model="row" label-width="0">
          <bk-form-item
            property="type"
            error-display-type="tooltips"
            class="table-form-item">
            <bk-select
              class="edit-select"
              :clearable="false"
              :filterable="false"
              v-model="row.type"
              @change="handleCellBlur(index)"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `type-input-${index}-${column?.index}`)"
            >
              <bk-option
                v-for="item in typeList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </bk-select>
          </bk-form-item>
        </bk-form>
      </template>
    </bk-table-column>
    <bk-table-column :label="t('说明')" prop="instructions">
      <template #default="{ row, column, index }">
        <bk-form :ref="(el: HTMLElement | null) => setRefs(el, `instructions-${index}`)" :model="row" label-width="0">
          <bk-form-item
            property="instructions"
            error-display-type="tooltips"
            class="table-form-item">
            <bk-input
              v-model="row.instructions"
              :clearable="false"
              class="edit-input"
              @blur="handleCellBlur(index)"
              :ref="(el: HTMLElement | null) => setInputRefs(el, `instructions-input-${index}-${column?.index}`)"
            />
          </bk-form-item>
        </bk-form>
      </template>
    </bk-table-column>
    <bk-table-column :label="t('操作')">
      <template #default="{ index }">
        <i
          class="tb-btn add-btn apigateway-icon icon-ag-plus-circle-shape"
          @click="addRow(index)"></i>
        <i
          class="tb-btn delete-btn apigateway-icon icon-ag-minus-circle-shape"
          @click="delRow(index)"></i>
      </template>
    </bk-table-column>
  </bk-table>
</template>

<script lang="ts" setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import headersNames from '@/common/headers-name';
import headersValues from '@/common/headers-value';

const { t } = useI18n();

interface RowType {
  id?: number;
  name: string;
  value: string;
  type: string;
  instructions: string;
  isEdit?: boolean;
  required?: boolean;
  options?: unknown;
  default?: string;
}

interface SelectPayload {
  row: RowType;
  index: number;
  checked: boolean;
  data: RowType[];
}

const props = defineProps({
  list: {
    type: Array<RowType>,
    default: [],
  },
  type: {
    type: String,
    required: false,
  },
});

const emit = defineEmits(['change']);

const formRefs = ref(new Map());
const setRefs = (el: HTMLElement | null, name: string) => {
  if (el) {
    formRefs.value?.set(name, el);
  }
};

const formInputRef = ref(new Map());
const setInputRefs = (el: HTMLElement | null, name: string) => {
  if (el) {
    formInputRef.value?.set(name, el);
  }
};
const getDefaultTbRow = () => {
  return {
    name: '',
    value: '',
    type: 'string',
    instructions: '',
    isEdit: true,
  };
};

const tableData = ref<RowType[]>(props?.list?.length ? props.list : [getDefaultTbRow()]);
const checkedList = ref<RowType[]>([]);
const typeList = ref<{label: string, value: string}[]>([
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

const headersNameList = computed(() => (headersNames.map((item: string) => ({ label: item, value: item }))));

const getCellClass = (payload: {index: number;}) => {
  if (payload.index !== 5) {
    return 'custom-table-cell';
  }
  return '';
};

const handleCellBlur = async (index: number) => {
  tableData.value[index].isEdit = false;
};

const handleNameChange = (index: number, name: string) => {
  if (['Accept', 'Content-Type'].includes(name)) {
    tableData.value[index].options = headersValues;
  } else {
    tableData.value[index].options = [];
  }

  tableData.value[index].value = '';
  handleCellBlur(index);
};

const addRow = (index: number) => {
  const row = { ...getDefaultTbRow(), id: +new Date() };
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

  list?.forEach(async (item: RowType) => {
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

const handleSelect = ({ row, checked }: SelectPayload) => {
  if (checked) {
    checkedList.value = [...checkedList.value, row];
  } else {
    const { id } = row;
    checkedList.value = checkedList.value?.filter(item => item.id !== id);
  }
};

const handleSelectAll = ({ checked, data }: SelectPayload) => {
  if (checked) {
    checkedList.value = data;
  } else {
    checkedList.value = [];
  }
};

watch(
  () => props.list,
  (v) => {
    const list: RowType[] = [];
    v?.forEach((item: any) => {
      list.push({
        isEdit: false,
        id: +new Date(),
        name: item.name,
        value: item.schema?.default || '',
        instructions: item.description,
        required: !!item.required,
        type: item.schema?.type || 'string',
        options: item.schema?.enum || [],
        default: item.schema?.default,
      });
    });

    if (!list?.length) {
      tableData.value = [{ ...getDefaultTbRow(), id: +new Date() }];
    } else {
      tableData.value = list;
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
    padding: 0 16px;
  }
  :deep(.bk-form-error-tips) {
    transform: translate(-50%, 4px);
  }
  :deep(.bk-table-body-content) {
    .custom-table-cell {
      .cell {
        padding: 0;
        &:hover {
          cursor: pointer;
        }
        .bk-form {
          line-height: 42px;
          margin-bottom: -1px;
          .table-form-item {
            margin-bottom: 0;
            .bk-form-content {
              line-height: 42px;
              .bk-input {
                height: 42px;
                line-height: 42px;
                border: 0;
                &--text {
                  padding: 0 16px;
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
      }
    }
  }
}
</style>
