<template>
  <div class="request-params-table-wrapper">
    <div v-if="!readonly" style="margin-bottom: 24px;">
      <BkCheckbox v-model="disabled">{{ t('该资源无请求参数') }}</BkCheckbox>
    </div>
    <bk-table
      v-if="!disabled"
      ref="tableRef"
      :cell-class="getCellClass"
      :data="tableData"
      :border="['outer', 'row']"
      class="request-params-table"
      row-hover="auto"
      @vue:mounted="handleTableMounted"
    >
      <bk-table-column :label="t('参数名')" prop="name">
        <template #default="{ row }">
          <div v-if="readonly" class="readonly-value-wrapper">{{ row.name || '--' }}</div>
          <bk-input
            v-else
            v-model="row.name"
            :clearable="false"
            :disabled="row.in === 'body'"
            :placeholder="t('参数名')"
            class="edit-input"
          />
        </template>
      </bk-table-column>
      <bk-table-column :label="t('位置')" prop="in" width="100">
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ inList.find(item => item.value === row.in)?.label || '--' }}
          </div>
          <bk-select
            v-else
            v-model="row.in"
            :clearable="false"
            :filterable="false"
            :placeholder="t('位置')"
            class="edit-select"
            @change="() => handleInChange(row)"
          >
            <bk-option
              v-for="item in inList"
              :id="item.value"
              :key="item.value"
              :disabled="tableData.find((dataRow) => dataRow.in === 'body') && item.value === 'body'"
              :name="item.label"
            />
          </bk-select>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('类型')" prop="type" width="100">
        <template #default="{ row }">
          <div v-if="readonly" class="readonly-value-wrapper">
            {{ typeList.find(item => item.value === row.type)?.label || '--' }}
          </div>
          <bk-select
            v-else
            v-model="row.type"
            :clearable="false"
            :filterable="false"
            class="edit-select"
          >
            <bk-option
              v-for="item in typeList"
              :id="item.value"
              :key="item.value"
              :disabled="isTypeDisabled(row.in, item.value)"
              :name="item.label"
            />
          </bk-select>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('必填')" prop="required" width="100">
        <template #default="{ row }">
          <div v-if="readonly" class="readonly-value-wrapper">{{ row.required ? t('是') : t('否') }}</div>
          <BkSwitcher
            v-else
            v-model="row.required"
            style="margin-left: 16px;"
            theme="primary"
          />
        </template>
      </bk-table-column>
      <bk-table-column :label="t('默认值')" :width="readonly ? 150 : 300" prop="default">
        <template #default="{ row }">
          <div v-if="readonly" class="readonly-value-wrapper">{{ row.default || '--' }}</div>
          <bk-input
            v-else
            v-model="row.default"
            :disabled="row.in === 'body'"
            :clearable="false"
            :placeholder="row.in === 'body' ? '--' : t('默认值')"
            class="edit-input"
          />
        </template>
      </bk-table-column>
      <bk-table-column :label="t('备注')" prop="description" width="300">
        <template #default="{ row }">
          <div v-if="readonly" class="readonly-value-wrapper">{{ row.description || '--' }}</div>
          <bk-input
            v-else
            v-model="row.description"
            :clearable="false"
            :placeholder="t('备注')"
            class="edit-input"
          />
        </template>
      </bk-table-column>
      <bk-table-column v-if="!readonly" :label="t('操作')" fixed="right" width="110">
        <template #default="{ row, index }">
          <AgIcon
            v-if="isAddFieldVisible(row)"
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
          <RequestParamsTable v-model="row.body" :readonly="readonly" />
        </div>
      </template>
    </bk-table>
    <div v-if="!disabled && !readonly" class="add-param-btn-row">
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

interface ISchema {
  parameters?: {
    description?: string,
    in: string,
    name: string,
    required?: boolean,
    schema: JSONSchema7,
    default?: string | number | boolean,
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
}

interface IProp {
  detail?: {
    schema?: ISchema;
    openapi_schema?: ISchema;
  },
  readonly?: boolean,
}

const disabled = defineModel<boolean>('is-no-params', {
  default: false,
});

const {
  detail,
  readonly = false,
} = defineProps<IProp>();

const { t } = useI18n();
const tableRef = ref();

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

const convertPropertyType = (type: string): JSONSchema7TypeName => {
  switch (type) {
    case 'string':
      return 'string';
    case 'boolean':
      return 'boolean';
    case 'array':
      return 'array';
    case 'object':
      return 'object';
    case 'integer':
    case 'number':
      return 'number';
    default:
      return 'string';
  }
};

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
        type: convertPropertyType(property.type),
        required: schema?.required?.includes(propertyName) ?? false,
        default: property.default ?? '',
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

watch(() => detail, () => {
  if (detail?.schema || detail.openapi_schema) {
    const resourceSchema = detail.schema || detail.openapi_schema;
    tableData.value = [];
    if (resourceSchema.parameters?.length) {
      tableData.value = resourceSchema.parameters.map(parameter => (
        {
          id: _.uniqueId(),
          name: parameter.name,
          in: parameter.in,
          type: parameter.schema.type,
          required: parameter.required ?? false,
          default: parameter.schema?.default ?? '',
          description: parameter.description ?? '',
        }
      ));
    }
    if (resourceSchema.requestBody) {
      const body = resourceSchema.requestBody;
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
}, { immediate: true });

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
    _row.type = 'object';
    delete _row.default;

    if (_row.body) {
      _row.body.push(genBodyRow());
    } else {
      _row.body = [genBodyRow()];
    }
  } else {
    if (row.type === 'object' || row.type === 'array') {
      _row.type = 'string';
    }
    delete _row.body;
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

const isAddFieldVisible = (row: ITableRow) => {
  if (row.in === 'body') {
    if (row.type === 'array') {
      return row.body ? row.body.length === 0 : true;
    }
    return true;
  }
  return false;
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

  if (row.default) {
    schema.default = row.default;
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

const isTypeDisabled = (paramIn: string, type: string) => {
  if (paramIn === 'body') {
    return type !== 'object' && type !== 'array';
  }
  return type === 'object' || type === 'array';
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
  font-size: 12px;

  &.is-focused:not(.is-readonly) {
    border: 1px solid #a3c5fd;
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

.request-params-table {
  .readonly-value-wrapper {
    padding-left: 16px;
    font-size: 12px;
    cursor: auto;
  }

  .td-text {
    padding: 0 16px;
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

    // 展开行样式
    .row_expend {
      td {
        border-right: none;
      }

      // 展开行没有内容时，不应渲染，避免出现多余的 1px 高的元素
      &:not(:has(.request-param-body-table)) {
        display: none !important;
      }
    }
  }
}

// 输入框和 placeholder 样式
:deep(.bk-input--text) {
  font-size: 12px !important;
  padding-inline: 16px;

  &::placeholder {
    font-size: 12px !important;
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
