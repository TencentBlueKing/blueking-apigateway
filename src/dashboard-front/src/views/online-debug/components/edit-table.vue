<template>
  <bk-table
    class="variable-table"
    ref="bkTableRef"
    row-hover="auto"
    :data="tableData"
    show-overflow-tooltip
    @cell-click="handleCellClick"
    :cell-class="getCellClass"
    border="outer">
    <bk-table-column :width="55" type="selection" align="center" />
    <bk-table-column :label="t('参数名')" prop="name">
      <template #default="{ row, column, index }">
        <div class="td-text" v-if="!row?.isEdit">
          {{ row?.name }}
        </div>
        <template v-else>
          <bk-popover
            placement="top-start"
            trigger="click"
            theme="light"
            :is-show="isShowVarPopover"
            :content="t('变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符') "
            :popover-delay="[300, 0]"
          >
            <bk-form :ref="(el: HTMLElement) => setRefs(el, `name-${index}`)" :model="row" label-width="0">
              <bk-form-item
                :rules="varRules.name"
                property="name"
                error-display-type="tooltips"
                class="table-form-item">
                <bk-input
                  v-model="row.name"
                  :clearable="false"
                  class="edit-input"
                  @blur="handleCellBlur(index)"
                  :ref="(el: HTMLElement) => setInputRefs(el, `name-input-${index}-${column?.index}`)"
                />
              </bk-form-item>
            </bk-form>
          </bk-popover>
        </template>

      </template>
    </bk-table-column>
    <bk-table-column :label="t('参数值')" prop="value">
      <template #default="{ row, column, index }">
        <div class="td-text" v-if="!row?.isEdit">
          {{ row?.value }}
        </div>
        <template v-else>
          <bk-form :ref="(el: HTMLElement) => setRefs(el, `value-${index}`)" :model="row" label-width="0">
            <bk-form-item
              :rules="varRules.value"
              property="value"
              error-display-type="tooltips"
              class="table-form-item">
              <bk-input
                v-model="row.value"
                :clearable="false"
                class="edit-input"
                @blur="handleCellBlur(index)"
                :ref="(el: HTMLElement) => setInputRefs(el, `value-input-${index}-${column?.index}`)"
              />
            </bk-form-item>
          </bk-form>
        </template>
      </template>
    </bk-table-column>
    <bk-table-column :label="t('类型')" prop="type">
      <template #default="{ row, column, index }">
        <div
          class="td-text"
          @click="(event) => handleCellClick({ event, column, rowIndex: index })"
          v-if="!row?.isEdit">
          <bk-tag
            theme="info"
            @click="(event) => handleCellClick({ event, column, rowIndex: index })">
            {{ row?.type }}
          </bk-tag>
        </div>
        <template v-else>
          <bk-form :ref="(el: HTMLElement) => setRefs(el, `type-${index}`)" :model="row" label-width="0">
            <bk-form-item
              :rules="varRules.type"
              property="type"
              error-display-type="tooltips"
              class="table-form-item">
              <bk-select
                class="edit-select"
                :clearable="false"
                :filterable="false"
                v-model="row.type"
                @change="handleCellBlur(index)"
                :ref="(el: HTMLElement) => setInputRefs(el, `type-input-${index}-${column?.index}`)"
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
      </template>
    </bk-table-column>
    <bk-table-column :label="t('说明')" prop="instructions">
      <template #default="{ row, column, index }">
        <div class="td-text" v-if="!row?.isEdit">
          {{ row?.instructions }}
        </div>
        <template v-else>
          <bk-form :ref="(el: HTMLElement) => setRefs(el, `instructions-${index}`)" :model="row" label-width="0">
            <bk-form-item
              :rules="varRules.instructions"
              property="instructions"
              error-display-type="tooltips"
              class="table-form-item">
              <bk-input
                v-model="row.instructions"
                :clearable="false"
                class="edit-input"
                @blur="handleCellBlur(index)"
                :ref="(el: HTMLElement) => setInputRefs(el, `instructions-input-${index}-${column?.index}`)"
              />
            </bk-form-item>
          </bk-form>
        </template>
      </template>
    </bk-table-column>
    <bk-table-column :label="t('操作')">
      <template #default="{ row, index }">
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
import { ref, nextTick, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps({
  list: {
    type: Array,
    default: [],
  },
});

const isShowVarPopover = ref(false);

const formRefs = ref(new Map());
const setRefs = (el: any, name: string) => {
  if (el) {
    formRefs.value?.set(name, el);
  }
};

const formInputRef = ref(new Map());
const setInputRefs = (el: any, name: string) => {
  if (el) {
    formInputRef.value?.set(name, el);
  }
};
const getDefaultTbRow = () => {
  return {
    name: '',
    value: '',
    type: '',
    instructions: '',
    isEdit: true,
  };
};

const tableData = ref<any>(props?.list?.length ? props.list : [getDefaultTbRow()]);

const typeList = ref<any[]>([
  {
    label: 'Number',
    value: 'number',
  },
  {
    label: 'String',
    value: 'string',
  },
  {
    label: 'Boolean',
    value: 'boolean',
  },
]);

const getCellClass = (payload: any) => {
  if (payload.index !== 5) {
    return 'custom-table-cell';
  }
  return '';
};

const handleCellClick = async ({ event, column, rowIndex }: any) => {
  event.stopPropagation();
  const { field, index } = column;
  if (!field) {
    return;
  };
  tableData.value[rowIndex].isEdit = true;
  nextTick(() => {
    if (field === 'type') {
      // formInputRef.value?.get(`${field}-input-${rowIndex}-${index}`)?.showPopover();
      // formInputRef.value?.get(`${field}-input-${rowIndex}-${index}`)?.focus();
    } else {
      formInputRef.value?.get(`${field}-input-${rowIndex}-${index}`)?.focus();
    }
  });
};

const validateRow = async (index: number) => {
  let flag = true;
  await formRefs.value?.get(`name-${index}`)?.validate()
    .then(() => {}, () => {
      flag = false;
    });
  await formRefs.value?.get(`value-${index}`)?.validate()
    .then(() => {}, () => {
      flag = false;
    });
  await formRefs.value?.get(`type-${index}`)?.validate()
    .then(() => {}, () => {
      flag = false;
    });
  await formRefs.value?.get(`instructions-${index}`)?.validate()
    .then(() => {}, () => {
      flag = false;
    });

  return flag;
};

const handleCellBlur = async (index: number) => {
  if (await validateRow(index)) {
    tableData.value[index].isEdit = false;
  }
};

const addRow = (index: number) => {
  tableData.value?.splice(index + 1, 0, getDefaultTbRow());
};

const delRow = (index: number) => {
  tableData.value?.splice(index, 1);
};

const getTableData = () => {
  return tableData.value;
};

const varRules = {
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator(value: any) {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,49}$/;
        return reg.test(value);
      },
      message: t('由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符'),
      trigger: 'blur',
    },
    {
      validator(value: any) {
        // 去重
        const alikeArr: any = tableData.value?.filter((item: any) => item.name === value);
        if (alikeArr?.length > 1) {
          return false;
        }
        return true;
      },
      message: t('变量名不可重复'),
      trigger: 'blur',
    },
  ],
  value: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  type: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'change',
    },
  ],
  instructions: [
    {
      required: false,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => props.list,
  (v) => {
    // console.log('table: ', v);
    const list: any[] = [];
    v?.forEach((item: any) => {
      list.push({
        isEdit: false,
        name: item.name,
        value: '',
        instructions: item.description,
        required: item.required,
        type: item.schema?.type,
        options: item.schema?.enum || [],
        default: item.schema?.default,
      });
    });

    if (!list?.length) {
      tableData.value = [getDefaultTbRow()];
    } else {
      tableData.value = list;
    }
  },
  {
    deep: true,
    immediate: true,
  },
);

defineExpose({
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
    .angle-up {
      display: none !important;
    }
    &:hover {
      border: 1px solid #A3C5FD;
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
          .table-form-item {
            margin-bottom: 0;
            .bk-form-content {
              line-height: 42px;
              .bk-input {
                height: 42px;
                line-height: 42px;
                border: 0;
                &.is-focused {
                  border: 1px solid #3A84FF;
                }
                &--text {
                  padding: 0 16px;
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
