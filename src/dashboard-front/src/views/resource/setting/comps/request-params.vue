<template>
  <div class="request-params-table-wrapper">
    <div style="margin-bottom: 24px;">
      <BkCheckbox v-model="disabled">{{ t('该资源无请求参数') }}</BkCheckbox>
    </div>
    <bk-table
      v-if="!disabled"
      ref="tableRef"
      :cell-class="getCellClass"
      :data="tableData"
      :border="['outer', 'row']"
      class="variable-table"
      row-hover="auto"
      @vue:mounted="handleTableMounted"
    >
      <bk-table-column :label="t('参数名')" prop="name">
        <template #default="{ row, column, index }">
          <bk-form :ref="(el: HTMLElement | null) => setRefs(el, 'name-', index)" :model="row" label-width="0">
            <bk-form-item
              class="table-form-item"
              error-display-type="tooltips"
              property="name"
            >
              <bk-input
                :ref="(el: HTMLElement | null) => setInputRefs(el, `name-input-`, index, column?.index)"
                v-model="row.name"
                :clearable="false"
                class="edit-input"
                :disabled="row.in === 'body'"
              />
            </bk-form-item>
          </bk-form>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('位置')" prop="in" width="100">
        <template #default="{ row, column, index }">
          <bk-form
            :ref="(el: HTMLElement | null) => setRefs(el, 'in-', index)"
            :model="row"
            label-width="0"
          >
            <bk-form-item
              class="table-form-item"
              error-display-type="tooltips"
              property="in"
            >
              <bk-select
                :ref="(el: HTMLElement | null) => setInputRefs(el, 'in-input-', index, column?.index)"
                v-model="row.in"
                :clearable="false"
                :filterable="false"
                class="edit-select"
                @change="() => handleInChange(row)"
              >
                <bk-option
                  v-for="item in inList"
                  :id="item.value"
                  :key="item.value"
                  :name="item.label"
                  :disabled="tableData.find((dataRow) => dataRow.in === 'body') && item.value === 'body'"
                />
              </bk-select>
            </bk-form-item>
          </bk-form>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('类型')" prop="type" width="100">
        <template #default="{ row, column, index }">
          <bk-form
            :ref="(el: HTMLElement | null) => setRefs(el, 'type-', index)"
            :model="row"
            label-width="0"
          >
            <bk-form-item
              class="table-form-item"
              error-display-type="tooltips"
              property="type"
            >
              <bk-select
                :ref="(el: HTMLElement | null) => setInputRefs(el, 'type-input-', index, column?.index)"
                v-model="row.type"
                :clearable="false"
                :filterable="false"
                class="edit-select"
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
      <bk-table-column :label="t('必填')" prop="required" width="100">
        <template #default="{ row, column, index }">
          <bk-form
            :ref="(el: HTMLElement | null) => setRefs(el, 'required-', index)"
            :model="row"
            label-width="0"
          >
            <bk-form-item
              class="table-form-item"
              error-display-type="tooltips"
              property="required"
            >
              <BkSwitcher
                :ref="(el: HTMLElement | null) => setInputRefs(el, 'required-input-', index, column?.index)"
                v-model="row.required"
                style="margin-left: 16px;"
                theme="primary"
              />
            </bk-form-item>
          </bk-form>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('默认值')" prop="default">
        <template #default="{ row, column, index }">
          <bk-form
            :ref="(el: HTMLElement | null) => setRefs(el, `default-`, index)"
            :model="row"
            label-width="0"
          >
            <bk-form-item
              class="table-form-item"
              error-display-type="tooltips"
              property="default"
            >
              <bk-input
                :ref="(el: HTMLElement | null) => setInputRefs(el, 'default-input-', index, column?.index)"
                v-model="row.default"
                :clearable="false"
                class="edit-input"
              />
            </bk-form-item>
          </bk-form>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('备注')" prop="description">
        <template #default="{ row, column, index }">
          <bk-form
            :ref="(el: HTMLElement | null) => setRefs(el, 'description-', index)"
            :model="row"
            label-width="0"
          >
            <bk-form-item
              class="table-form-item"
              error-display-type="tooltips"
              property="description"
            >
              <bk-input
                :ref="(el: HTMLElement | null) => setInputRefs(el, 'description-input-', index, column?.index)"
                v-model="row.description"
                :clearable="false"
                class="edit-input"
              />
            </bk-form-item>
          </bk-form>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('操作')" fixed="right" width="110">
        <template #default="{ row, index }">
          <AgIcon
            v-if="row.in === 'body'"
            v-bk-tooltips="t('添加字段')"
            class="tb-btn add-btn"
            name="plus-circle-shape"
            @click="() => addField(row)"
          />
          <AgIcon
            v-bk-tooltips="t('删除参数')"
            class="tb-btn delete-btn"
            name="minus-circle-shape"
            @click="() => delRow(row, index)"
          />
        </template>
      </bk-table-column>
      <template #expandRow="row">
        <div v-if="row?.in === 'body'">
          <RequestParamsTable v-model="row.body" />
        </div>
      </template>
    </bk-table>
    <div v-if="!disabled" class="add-param-btn-row">
      <bk-button
        text
        theme="primary"
        @click="() => addRow()"
      >
        <AgIcon name="add-small" />
        {{ t('新增参数') }}
      </bk-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  nextTick,
  onMounted,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import AgIcon from '@/components/ag-icon.vue';
import _ from 'lodash';
import RequestParamsTable from '@/views/resource/setting/comps/request-params-table.vue';
import {
  JSONSchema7,
  JSONSchema7TypeName,
} from 'json-schema';

interface ITableRow {
  id: string;
  name: string;
  in: string;
  type: JSONSchema7TypeName;
  required?: boolean;
  default?: string;
  description: string;
  body?: IBodyRow[];
}

interface IBodyRow {
  id: string,
  name: string,
  type: JSONSchema7TypeName,
  required?: boolean,
  default?: string,
  description: string,
  body?: IBodyRow[];
}

interface IProp {
  detail?: {
    schema: {
      parameters?: {
        description?: string,
        in: string,
        name: string,
        required?: boolean,
        schema: JSONSchema7,
      }[],
      requestBody?: {
        content: {
          'application/json': {
            schema: JSONSchema7,
          }
        },
        description?: string,
        required?: boolean,
      },
    };
  }
}

const disabled = defineModel<boolean>('is-no-params', {
  default: false,
});

const { detail } = defineProps<IProp>();

const { t } = useI18n();
const tableRef = ref();
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

const tableData = ref<ITableRow[]>([
  {
    id: _.uniqueId(),
    name: '',
    in: 'header',
    type: 'string',
    required: false,
    default: '',
    description: '',
  },
]);
const inList = ref([
  {
    label: 'Header',
    value: 'header',
  },
  {
    label: 'Query',
    value: 'query',
  },
  {
    label: 'Path',
    value: 'path',
  },
  {
    label: 'Body',
    value: 'body',
  },
]);

const typeList = ref([
  {
    label: 'String',
    value: 'string',
  },
  {
    label: 'Number',
    value: 'number',
  },
  {
    label: 'Boolean',
    value: 'boolean',
  },
  {
    label: 'Array',
    value: 'array',
  },
  {
    label: 'Object',
    value: 'object',
  },
]);

watch(() => detail, () => {
  if (detail?.schema) {
    tableData.value = [];
    if (detail.schema.parameters?.length) {
      tableData.value = detail.schema.parameters.map(parameter => (
        {
          id: _.uniqueId(),
          name: parameter.name,
          in: parameter.in,
          type: parameter.schema.type,
          required: parameter.required ?? false,
          default: '',
          description: parameter.description ?? '',
        }
      ));
    }
    if (detail.schema.requestBody) {
      const body = detail.schema.requestBody;
      const row = {
        id: _.uniqueId(),
        name: t('根节点'),
        in: 'body',
        type: 'object' as JSONSchema7TypeName,
        required: body.required ?? false,
        description: body.description ?? '',
      };
      const subBody = convertSchemaToBodyRow(body?.content?.['application/json']?.schema);
      if (subBody) {
        Object.assign(row, {
          body: subBody,
        });
      }
      tableData.value.push(row);
    }
    nextTick(() => {
      tableRef.value?.setAllRowExpand(true);
    });
  }
});

const convertSchemaToBodyRow = (schema: JSONSchema7) => {
  if (!schema) {
    return null;
  }
  const body: IBodyRow[] = [];
  if (Object.keys(schema.properties || {}).length) {
    for (const propertyName in schema.properties) {
      const property = schema.properties[propertyName];
      const row: IBodyRow = {
        id: _.uniqueId(),
        name: propertyName,
        type: schema.type as JSONSchema7TypeName,
        required: schema.required?.includes(propertyName) ?? false,
        default: '',
        description: property.description ?? '',
      };
      if (Object.keys(property.properties || {}).length) {
        row.body = convertSchemaToBodyRow(property);
      }
      body.push(row);
    }
  } else {
    return null;
  }
  return body;
};

const genRow = () => {
  return {
    id: _.uniqueId(),
    name: '',
    in: 'header',
    type: 'string',
    required: false,
    default: '',
    description: '',
    isEdit: true,
  };
};

const genBodyRow = (id?: string) => {
  return {
    id: id || _.uniqueId(),
    name: '',
    type: 'string' as JSONSchema7TypeName,
    required: false,
    default: '',
    description: '',
    isEdit: true,
  };
};

const getCellClass = (payload: { index: number; }) => {
  if (payload.index !== 6) {
    return 'custom-table-cell';
  }
  return '';
};

const handleInChange = (row: ITableRow) => {
  const _row = tableData.value.find(data => data.id === row.id);
  if (row.in === 'body') {
    _row.name = t('根节点');
    if (_row.body) {
      _row.body.push(genBodyRow());
    } else {
      _row.body = [genBodyRow()];
    }
  } else {
    _row.name = '';
  }
  nextTick(() => {
    tableRef.value?.setAllRowExpand(true);
  });
};

const addRow = () => {
  tableData.value.push(genRow());
};

const delRow = (row: ITableRow, index: number) => {
  if (tableData.value.length === 1) {
    Message({
      theme: 'warning',
      message: t('至少需要保留一行！'),
    });
    return;
  }
  tableData.value?.splice(index, 1);
};

const addField = (row: ITableRow) => {
  const bodyRow = tableData.value.find(data => data.id === row.id);
  if (bodyRow) {
    if (bodyRow.body) {
      bodyRow.body.push(genBodyRow());
    } else {
      bodyRow.body = [genBodyRow()];
    }
  }
};

const genParameters = () => tableData.value.map(row => genParameterFromRow(row)).filter(item => item);

const genParameterFromRow = (row: ITableRow) => {
  if ([
    'path',
    'query',
    'header',
  ].includes(row.in)) {
    const parameter = {
      in: row.in,
      name: row.name,
      description: row.description,
    };
    if (row.required) {
      Object.assign(parameter, {
        required: true,
      });
    }
    const schema = {
      type: row.type,
    };
    if (row.default !== undefined && row.default !== null && row.default !== '') {
      Object.assign(schema, {
        default: row.type === 'number' ? Number(row.default) : row.default,
      });
    }
    Object.assign(parameter, { schema });
    return parameter;
  }
  return null;
};

const genBody = () => {
  const bodyRow = tableData.value.find(row => row.in === 'body');
  if (bodyRow) {
    const requestBody = {
      description: bodyRow.description,
      required: bodyRow.required,
      content: {
        'application/json': {},
      },
    };
    const schema: JSONSchema7 = {};
    Object.assign(schema, genSchemaFromBodyRow(bodyRow));
    Object.assign(requestBody.content['application/json'], { schema });
    return requestBody;
  }
  return null;
};

const genSchemaFromBodyRow = (row: IBodyRow) => {
  const schema: JSONSchema7 = {
    type: row.type,
  };

  if (row.description) {
    schema.description = row.description;
  }

  if (row.body?.length) {
    if (row.body.some(item => item.required)) {
      schema.required = row.body.filter(item => item.required).map(item => item.name);
    }
    schema.properties = {};
    row.body.forEach((item) => {
      Object.assign(schema.properties, {
        [item.name]: genSchemaFromBodyRow(item),
      });
    });
  }
  return schema;
};

const handleTableMounted = () => {
  tableRef.value?.setAllRowExpand(true);
};

onMounted(() => {
  tableRef.value?.setAllRowExpand(true);
});

defineExpose({
  getValue: () => {
    const parameters = genParameters();
    const requestBody = genBody();
    return {
      parameters,
      requestBody,
    };
  },
});
</script>

<style lang="scss" scoped>
.request-params-table-wrapper {
  padding-bottom: 22px;
}

.tb-btn {
  font-size: 14px;
  color: #c4c6cc;
  cursor: pointer;

  &:hover {
    color: #979ba5;
  }

  &.add-btn {
    margin-right: 16px;
  }
}

.edit-input.bk-input {
  border: none;
  height: 100%;

  &.is-focused:not(.is-readonly) {
    border: 1px solid #3a84ff;
    box-shadow: none;
  }

  &:hover {
    border: 1px solid #a3c5fd;
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
    border-radius: 0;

    .angle-up {
      display: none !important;
    }

    &:hover {
      border: 1px solid #a3c5fd;

      .angle-up {
        display: inline-flex !important;
      }
    }
  }

  &.is-focus {
    :deep(.bk-input) {
      border: 1px solid #3a84ff;

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
                border-radius: 0;

                &:hover {
                  border: 1px solid #a3c5fd;
                }

                &.is-focused {
                  border: 1px solid #3a84ff;
                }
              }

              .bk-select {
                &:hover {
                  .bk-input {
                    border: 1px solid #a3c5fd;
                  }
                }

                &.is-focus {
                  .bk-input {
                    border: 1px solid #3a84ff;
                  }
                }
              }
            }

            &.is-error {
              .bk-form-content {
                .bk-input--text {
                  background: #fee;
                }
              }
            }
          }
        }
      }
    }
  }

  .custom-table-cell {
    .cell {
      padding: 0;
    }
  }
}

.add-param-btn-row {
  padding-left: 14px;
  height: 42px;
  align-content: center;
  border: 1px solid #dcdee5;
  border-top: none;
}
</style>
