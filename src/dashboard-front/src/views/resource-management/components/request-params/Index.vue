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
  <div class="request-params-table-wrapper">
    <div
      v-if="!readonly"
      class="mb-24px"
    >
      <BkCheckbox
        v-model="disabled"
        class="text-14px"
      >
        {{ t('该资源无请求参数') }}
      </BkCheckbox>
    </div>
    <div
      v-if="!readonly && !disabled"
      class="mb-16px"
    >
      <IconButton
        theme="primary"
        @click="handleEditJSON"
      >
        {{ t('通过 JSON 生成') }}
      </IconButton>
    </div>
    <AgTable
      v-if="!disabled"
      :data="tableData"
      class="request-params-table"
      :immediate="false"
      :show-pagination="false"
      bordered
      :expand-icon="false"
      :expanded-row-keys="expandedRowKeys"
    >
      <TableColumn
        :title="t('参数名')"
        prop="name"
      >
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ row.name || '--' }}
          </div>
          <BkInput
            v-else
            v-model="row.name"
            :clearable="false"
            :disabled="row.in === 'body'"
            :placeholder="t('参数名')"
            class="edit-input"
            :class="{ 'has-error': invalidRowIdMap[row.id] }"
            @change="() => clearInvalidState(row.id)"
            @input="() => clearInvalidState(row.id)"
          >
            <template
              v-if="invalidRowIdMap[row.id]"
              #suffix
            >
              <div class="h-full pr-6px bg-#fff0f1 content-center">
                <AgIcon
                  name="exclamation-circle-fill"
                  size="12"
                  class="color-#EA3636 h-12px "
                />
              </div>
            </template>
          </BkInput>
        </template>
      </TableColumn>
      <TableColumn
        :title="t('位置')"
        prop="in"
        width="140"
      >
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ inList.find(item => item.value === row.in)?.label || '--' }}
          </div>
          <BkSelect
            v-else
            v-model="row.in"
            :clearable="false"
            :filterable="false"
            :placeholder="t('位置')"
            class="edit-select"
            @change="() => handleInChange(row)"
          >
            <BkOption
              v-for="item in inList"
              :id="item.value"
              :key="item.value"
              :disabled="tableData.find((dataRow) => dataRow.in === 'body') && item.value === 'body'"
              :name="item.label"
            />
          </BkSelect>
        </template>
      </TableColumn>
      <TableColumn
        :title="t('类型')"
        prop="type"
        width="140"
      >
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ typeList.find(item => item.value === row.type)?.label || '--' }}
          </div>
          <BkSelect
            v-else
            v-model="row.type"
            :clearable="false"
            :filterable="false"
            class="edit-select"
            @change="() => handleTypeChange(row)"
          >
            <BkOption
              v-for="item in typeList"
              :id="item.value"
              :key="item.value"
              :disabled="isTypeDisabled(row.in, item.value)"
              :name="item.label"
            />
          </BkSelect>
        </template>
      </TableColumn>
      <TableColumn
        :title="t('必填')"
        prop="required"
        width="100"
      >
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ row.required ? t('是') : t('否') }}
          </div>
          <BkSwitcher
            v-else
            v-model="row.required"
            :disabled="row.in === 'path'"
            class="ml-16px!"
            theme="primary"
          />
        </template>
      </TableColumn>
      <TableColumn
        :title="t('默认值')"
        :width="readonly ? 160 : 300"
      >
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ row.default || '--' }}
          </div>
          <BkInput
            v-else
            v-model="row.default"
            :disabled="row.in === 'body'"
            :clearable="false"
            :placeholder="row.in === 'body' ? '--' : t('默认值')"
            class="edit-input"
          />
        </template>
      </TableColumn>
      <TableColumn
        :title="t('备注')"
        width="260"
      >
        <template #default="{ row }">
          <div
            v-if="readonly"
            class="readonly-value-wrapper"
          >
            {{ row.description || '--' }}
          </div>
          <BkInput
            v-else
            v-model="row.description"
            :clearable="false"
            :placeholder="t('备注')"
            class="edit-input"
          />
        </template>
      </TableColumn>
      <TableColumn
        v-if="!readonly"
        :title="t('操作')"
        fixed="right"
        width="140"
      >
        <template #default="{ row, index }">
          <div class="pl-16px">
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
          </div>
        </template>
      </TableColumn>
      <template #expandedRow="{row}">
        <div v-if="row?.in === 'body'">
          <RequestParamsTable
            ref="sub-table-ref"
            v-model="row.body"
            :readonly="readonly"
          />
        </div>
      </template>
    </AgTable>
    <div
      v-if="!disabled && !readonly"
      class="add-param-btn-row"
    >
      <BkButton
        text
        theme="primary"
        @click="() => addRow()"
      >
        <AgIcon name="add-small" />
        {{ t('新增参数') }}
      </BkButton>
    </div>
  </div>
  <JsonEditorSlider
    v-model="isEditorSliderVisible"
    @confirm="handleEditorConfirm"
  />
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import { uniqueId } from 'lodash-es';
import RequestParamsTable from './RequestParamsTable.vue';
import {
  type JSONSchema7,
  type JSONSchema7TypeName,
} from 'json-schema';
import toJsonSchema from 'to-json-schema';
import JsonEditorSlider from '../JsonEditorSlider.vue';
import AgTable from '@/components/ag-table/Index.vue';
import { TableColumn } from '@blueking/tdesign-ui';

interface ITableRow {
  id: string
  name: string
  in: string
  type: JSONSchema7TypeName
  required?: boolean
  default?: string
  description: string
  body?: IBodyRow[]
}

interface IBodyRow {
  id: string
  name: string
  type: JSONSchema7TypeName
  required?: boolean
  default?: string
  description: string
  body?: IBodyRow[]
}

interface ISchema {
  parameters?: {
    description?: string
    in: string
    name: string
    required?: boolean
    schema: JSONSchema7
    default?: string | number | boolean
  }[]
  requestBody?: {
    content: { 'application/json': { schema: JSONSchema7 } }
    description?: string
    required?: boolean
  }
}

interface IProp {
  detail?: {
    schema?: ISchema
    openapi_schema?: ISchema
  }
  readonly?: boolean
}

const disabled = defineModel<boolean>('is-no-params', { default: false });

const {
  detail = {},
  readonly = false,
} = defineProps<IProp>();

const { t } = useI18n();

const subTableRef = useTemplateRef('sub-table-ref');

const tableData = ref<ITableRow[]>([
  {
    id: uniqueId(),
    name: '',
    in: 'header',
    type: 'string',
    required: false,
    default: '',
    description: '',
  },
]);
const expandedRowKeys = ref<string[]>([]);

const invalidRowIdMap = ref<Record<string, boolean>>({});

const isEditorSliderVisible = ref(false);

const inList = [
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
];

const typeList = [
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
];

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
        id: uniqueId(),
        name: propertyName,
        type: convertPropertyType(property.type),
        required: schema?.required?.includes(propertyName) ?? false,
        default: property.default ?? '',
        description: property.description ?? '',
      };
      if (Object.keys(property.properties || {}).length) {
        row.body = convertSchemaToBodyRow(property);
      }
      else if (property.type === 'array' && Object.keys(property.items || {}).length) {
        if (property.items.type === 'object') {
          row.body = [{
            id: uniqueId(),
            name: '',
            type: 'object',
            required: false,
            default: '',
            description: property.items.description ?? '',
            body: [],
          }];
          row.body[0].body = convertSchemaToBodyRow(property.items);
        }
        else {
          row.body = convertSchemaToBodyRow(property.items);
        }
      }
      body.push(row);
    }
  }
  else {
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
          id: uniqueId(),
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
        id: uniqueId(),
        name: t('根节点'),
        in: 'body',
        type: 'object' as JSONSchema7TypeName,
        required: body.required ?? false,
        description: body.description ?? '',
      };
      const subBody = convertSchemaToBodyRow(body?.content?.['application/json']?.schema);
      if (subBody) {
        Object.assign(row, { body: subBody });
      }
      tableData.value.push(row);
      expandedRowKeys.value.push(row.id);
    }
  }
}, { immediate: true });

const genRow = () => {
  return {
    id: uniqueId(),
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
    id: id || uniqueId(),
    name: '',
    type: 'string' as JSONSchema7TypeName,
    required: false,
    default: '',
    description: '',
    isEdit: true,
  };
};

const handleInChange = (row: ITableRow) => {
  const _row = tableData.value.find(data => data.id === row.id);
  if (_row) {
    if (row.in === 'body') {
      _row.name = t('根节点');
      _row.type = 'object';
      delete _row.default;

      if (_row.body) {
        _row.body.push(genBodyRow());
      }
      else {
        _row.body = [genBodyRow()];
      }
    }
    else {
      if (row.in === 'path') {
        _row.required = true;
      }
      if (row.type === 'object' || row.type === 'array') {
        _row.type = 'string';
      }
      delete _row.body;
    }
    expandedRowKeys.value.push(_row.id);
  }
};

const handleTypeChange = (row: ITableRow) => {
  const _row = tableData.value.find(data => data.id === row.id);
  if (_row) {
    if (_row.type === 'object' || _row.type === 'array') {
      _row.body = [genBodyRow()];
    }
  }
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
    }
    else {
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
      Object.assign(parameter, { required: true });
    }
    const schema = { type: row.type };
    if (row.default !== undefined && row.default !== null && row.default !== '') {
      Object.assign(schema, { default: row.type === 'number' ? Number(row.default) : row.default });
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
      content: { 'application/json': {} },
    };
    const schema: JSONSchema7 = {};
    Object.assign(schema, genSchemaFromBodyRow(bodyRow));
    Object.assign(requestBody.content['application/json'], { schema });
    return requestBody;
  }
  return null;
};

const genSchemaFromBodyRow = (row: IBodyRow) => {
  const schema: JSONSchema7 = { type: row.type };

  if (row.description) {
    schema.description = row.description;
  }

  if (row.default) {
    schema.default = row.default;
  }

  if (row.body?.length) {
    // 处理 type 为 array 时，schema 需要 items 字段的情况
    if (row.type === 'array' && row.body.length === 1) {
      schema.items = genSchemaFromBodyRow(row.body[0]);
    }
    else {
      if (row.body.some(item => item.required)) {
        schema.required = row.body.filter(item => item.required).map(item => item.name);
      }
      schema.properties = {};
      row.body.forEach((item) => {
        Object.assign(schema.properties, { [item.name]: genSchemaFromBodyRow(item) });
      });
    }
  }
  return schema;
};

const isTypeDisabled = (paramIn: string, type: string) => {
  if (paramIn === 'body') {
    return type !== 'object' && type !== 'array';
  }
  return type === 'object' || type === 'array';
};

const handleEditJSON = () => {
  isEditorSliderVisible.value = true;
};

const handleEditorConfirm = (jsonObject: Record<string, any>) => {
  try {
    const schema = toJsonSchema(jsonObject);

    const row = {
      id: uniqueId(),
      name: t('根节点'),
      in: 'body',
      type: 'object' as JSONSchema7TypeName,
      required: false,
      description: '',
    };

    // 是否已存在 request body 表格行
    const currentBodyRowIndex = tableData.value.findIndex(item => item.in === 'body');
    if (currentBodyRowIndex > -1) {
      Object.assign(row, tableData.value[currentBodyRowIndex]);
    }

    const subBody = convertSchemaToBodyRow(schema);
    if (subBody) {
      Object.assign(row, { body: subBody });
    }

    // 替换行
    if (currentBodyRowIndex > -1) {
      tableData.value[currentBodyRowIndex] = row;
    }
    // 插入新行
    else {
      tableData.value.push(row);
    }
  }
  catch {
    Message({
      theme: 'error',
      message: t('生成 JSON Schema 失败'),
    });
  }
};

const setInvalidRowId = () => {
  invalidRowIdMap.value = {};
  tableData.value?.forEach((row) => {
    if (!row.name) {
      invalidRowIdMap.value[row.id] = true;
    }
  });
};

const clearInvalidState = (rowId: string) => {
  delete invalidRowIdMap.value[rowId];
};

defineExpose({
  getValue: async () => {
    try {
      await subTableRef.value?.validate();

      setInvalidRowId();
      if (Object.keys(invalidRowIdMap.value).length) {
        throw new Error('invalid request params');
      }

      const parameters = genParameters();
      const requestBody = genBody();
      return {
        parameters,
        requestBody,
      };
    }
    catch {
      Message({
        theme: 'warning',
        message: t('请填写完整的请求参数'),
      });
      throw new Error('invalid request params');
    }
  },
});
</script>

<style lang="scss" scoped>

// 默认单元格高度和内边距

:deep(.t-table.t-size-m td) {
  height: 42px;
  padding: 0;
}

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
  height: 100%;
  font-size: 12px;
  border: none;

  &.is-focused:not(.is-readonly) {
    border: 1px solid #a3c5fd;
    box-shadow: none;
  }

  &:hover {
    border: 1px solid #a3c5fd;
  }

  &.has-error {

    :deep(.bk-input--text) {
      background-color: #fff0f1 !important;
    }
  }
}

.edit-select {
  height: 100%;

  :deep(.bk-select-trigger) {
    height: 100%;
  }

  :deep(.bk-input) {
    height: 100%;
    border: none;
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
}

// 输入框和 placeholder 样式

:deep(.bk-input--text) {
  font-size: 12px !important;
  padding-inline: 16px;
  line-height: unset;

  &::placeholder {
    font-size: 12px !important;
  }
}

.add-param-btn-row {
  height: 42px;
  padding-left: 14px;
  border: 1px solid #dcdee5;
  border-top: none;
  align-content: center;
}

:deep(.t-table) {

  .t-table__content {
    border-bottom: none;
    border-radius: 0;

    .t-table__body .t-table__expanded-row .t-table__expanded-row-inner .t-table__row-full-element {
      padding: 0;
    }
  }
}

</style>
