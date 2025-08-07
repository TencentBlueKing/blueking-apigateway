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
  <div class="response-params-table-wrapper">
    <BkCollapse
      v-model="activeIndex"
      class="table-collapse"
      use-card-theme
    >
      <BkCollapsePanel name="currentCollapse">
        <template #header>
          <div class="panel-header">
            <AngleUpFill
              :class="[activeIndex.includes('currentCollapse') ? 'panel-header-show' : 'panel-header-hide']"
            />
            <div
              v-if="!isEditingCode"
              class="title"
            >
              {{ response.code }}
            </div>
            <div
              v-else
              class="pl-14px"
              @click.stop
            >
              <BkInput
                v-model="localCode"
                :placeholder="t('请输入状态码')"
                @blur="handleCodeInputBlur"
                @enter="handleCodeInputDone"
              />
            </div>
            <div
              v-if="!readonly"
              class="sub-title"
            >
              <AgIcon
                class="icon-btn"
                name="edit-line"
                size="15"
                @click.stop="handleEditCode"
              />
              <AgIcon
                class="icon-btn"
                name="delet"
                size="15"
                @click.stop="handleDelete"
              />
            </div>
          </div>
        </template>
        <template #content>
          <div class="response-table-wrapper">
            <table
              v-for="row in tableData"
              :key="row.id"
              class="response-table"
            >
              <thead class="table-head">
                <tr class="table-head-row">
                  <th class="table-head-row-cell arrow-col" />
                  <th class="table-head-row-cell name-col">
                    {{ t('参数名') }}
                  </th>
                  <th class="table-head-row-cell type-col">
                    {{ t('类型') }}
                  </th>
                  <th
                    :style="readonly ? 'width: 150px' : ''"
                    class="table-head-row-cell description-col"
                  >
                    {{ t('备注') }}
                  </th>
                  <th
                    v-if="!readonly"
                    class="table-head-row-cell actions-col"
                  >
                    {{ t('操作') }}
                  </th>
                </tr>
              </thead>
              <tbody class="table-body">
                <tr class="table-body-row">
                  <td class="table-body-row-cell arrow-col">
                    <AgIcon
                      v-if="row.type === 'object'"
                      :class="{ expanded: row.properties?.length }"
                      class="expand-icon"
                      name="right-shape"
                    />
                  </td>
                  <!-- 字段名 -->
                  <td class="table-body-row-cell name-col">
                    <div
                      v-if="readonly"
                      class="readonly-value-wrapper"
                    >
                      {{ row.name || '--' }}
                    </div>
                    <BkInput
                      v-else
                      v-model="row.name"
                      :placeholder="t('字段名')"
                      disabled
                    />
                  </td>
                  <!-- 字段类型 -->
                  <td class="table-body-row-cell type-col">
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
                      @change="handleTypeChange"
                    >
                      <BkOption
                        v-for="item in typeList"
                        :id="item.value"
                        :key="item.value"
                        :name="item.label"
                      />
                    </BkSelect>
                  </td>
                  <!-- 字段备注 -->
                  <td
                    :style="readonly ? 'width: 150px' : ''"
                    class="table-body-row-cell description-col"
                  >
                    <div
                      v-if="readonly"
                      class="readonly-value-wrapper"
                    >
                      {{ row.description || '--' }}
                    </div>
                    <BkInput
                      v-else
                      v-model="row.description"
                      :placeholder="t('备注')"
                    />
                  </td>
                  <!-- 字段操作 -->
                  <td
                    v-if="!readonly"
                    class="table-body-row-cell actions-col"
                  >
                    <AgIcon
                      v-if="isAddFieldVisible(row)"
                      v-bk-tooltips="t('添加字段')"
                      class="tb-btn add-btn"
                      name="plus-circle-shape"
                      @click="() => addField(row)"
                    />
                    <AgIcon
                      v-bk-tooltips="t('删除字段')"
                      class="tb-btn delete-btn"
                      name="minus-circle-shape"
                      @click="() => removeField(row)"
                    />
                  </td>
                </tr>
              </tbody>
              <tfoot v-if="row?.properties?.length">
                <tr>
                  <td
                    :colspan="readonly ? 4 : 5"
                    class="pl-16px"
                  >
                    <ResponseParamsSubTable
                      v-model="row.properties"
                      :readonly="readonly"
                    />
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </template>
      </BkCollapsePanel>
    </BkCollapse>
  </div>
</template>

<script lang="ts" setup>
import { uniqueId } from 'lodash-es';
import {
  type JSONSchema7,
  type JSONSchema7TypeName,
} from 'json-schema';
import { Message } from 'bkui-vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import ResponseParamsSubTable from './ResponseParamsSubTable.vue';

interface ITableRow {
  id: string
  name: string
  type: JSONSchema7TypeName
  description: string
  properties?: ITableRow[]
}

interface IProps {
  response: IResponse
  readonly?: boolean
}

interface IResponse {
  id: string
  code: string
  body: {
    description: string
    content?: { 'application/json': { schema: JSONSchema7 } }
  }
}

const {
  response,
  readonly = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  'delete': []
  'change-code': [code: string]
}>();

const { t } = useI18n();

const tableData = ref<ITableRow[]>([]);
const activeIndex = ref<string[]>(['currentCollapse']);
const tableRef = ref();
const localCode = ref('');
const isEditingCode = ref(false);

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
  const body: ITableRow[] = [];
  if (Object.keys(schema.properties || {}).length) {
    for (const propertyName in schema.properties) {
      const property = schema.properties[propertyName];
      const row: ITableRow = {
        id: uniqueId(),
        name: propertyName,
        type: convertPropertyType(property.type),
        description: property.description ?? '',
      };
      if (Object.keys(property.properties || {}).length) {
        row.properties = convertSchemaToBodyRow(property);
      }
      body.push(row);
    }
  }
  else {
    return null;
  }
  return body;
};

watch(() => response, () => {
  if (response) {
    tableData.value = [];
    const { body } = response;
    const row = {
      id: uniqueId(),
      name: t('根节点'),
      type: 'object' as JSONSchema7TypeName,
      description: body.description ?? '',
    };
    // 响应没有响应体的情况（不会有 content 字段）
    if (body.content?.['application/json']?.schema) {
      const { type } = body.content['application/json'].schema;
      if (type === 'object') {
        const rowProperties = convertSchemaToBodyRow(body?.content?.['application/json']?.schema);
        if (rowProperties) {
          Object.assign(row, { properties: rowProperties });
        }
      }
    }
    tableData.value.push(row);
    nextTick(() => {
      tableRef.value?.setAllRowExpand(true);
    });
  }
}, { immediate: true });

const genRow = () => {
  return {
    id: uniqueId(),
    name: '',
    type: 'string' as JSONSchema7TypeName,
    description: '',
  };
};

const isAddFieldVisible = (row: ITableRow) => {
  if (row.type === 'object' || row.type === 'array') {
    if (row.type === 'array') {
      return row.properties ? row.properties.length === 0 : true;
    }
    return true;
  }
  return false;
};

const addField = (row: ITableRow) => {
  const targetRow = tableData.value.find(data => data.id === row.id);
  if (targetRow) {
    if (targetRow.properties) {
      targetRow.properties.push(genRow());
    }
    else {
      targetRow.properties = [genRow()];
    }
  }
};

const handleTypeChange = () => {
  const rootRow = tableData.value[0];
  if (rootRow.type === 'object') {
    if (rootRow.properties?.length) {
      rootRow.properties.push(genRow());
    }
    else {
      rootRow.properties = [genRow()];
    }
  }
  else {
    rootRow.properties = [];
  }
};

const genBody = () => {
  const bodyRow = tableData.value[0];
  const requestBody = { description: bodyRow.description };
  if (bodyRow.properties?.length) {
    const schema: JSONSchema7 = {};
    Object.assign(schema, genSchema(bodyRow));
    Object.assign(requestBody, { content: { 'application/json': { schema } } });
  }
  return requestBody;
};

const genSchema = (row: ITableRow) => {
  const schema: JSONSchema7 = { type: row.type };

  if (row.description) {
    schema.description = row.description;
  }

  if (row.properties?.length) {
    schema.properties = {};
    row.properties.forEach((item) => {
      Object.assign(schema.properties, { [item.name]: genSchema(item) });
    });
  }
  return schema;
};

const removeField = (row: ITableRow) => {
  if (tableData.value.length === 1) {
    Message({
      theme: 'warning',
      message: t('至少需要保留一行！'),
    });
    return;
  }
  const index = tableData.value.findIndex(data => data.id === row.id);
  if (index !== -1) {
    tableData.value.splice(index, 1);
  }
};

const handleEditCode = () => {
  localCode.value = response.code;
  isEditingCode.value = true;
};

const handleCodeInputBlur = () => {
  isEditingCode.value = false;
  localCode.value = response.code;
};

const handleCodeInputDone = () => {
  if (!localCode.value) {
    Message({
      theme: 'warning',
      message: t('请输入合法的状态码'),
    });
    isEditingCode.value = false;
    return;
  }
  if (localCode.value) {
    emit('change-code', localCode.value);
  }
  isEditingCode.value = false;
};

const handleDelete = () => {
  emit('delete');
};

onMounted(() => {
  tableRef.value?.setAllRowExpand(true);
});

defineExpose({
  getValue: () => ({
    code: response.code,
    body: genBody(),
  }),
});
</script>

<style lang="scss" scoped>

.response-params-table-wrapper {

  :deep(.table-collapse) {
    margin-bottom: 0 !important;

    .bk-collapse-item {
      margin-bottom: 0 !important;
      box-shadow: none !important;

      .bk-collapse-content {
        padding: 0 !important;
      }
    }

    .panel-header {
      display: flex;
      align-items: center;
      padding: 0 24px 8px 0;
      cursor: pointer;

      .title {
        margin-left: 14px;
        font-size: 14px;
        font-weight: 700;
        color: #313238;
      }

      .sub-title {
        margin-left: 12px;
        font-size: 14px;
        color: #979ba5;

        .icon-btn {
          margin: 0 4px;

          &:hover {
            color: #3a84ff;
          }
        }
      }

      .panel-header-show {
        transform: rotate(0deg);
        transition: .2s;
      }

      .panel-header-hide {
        transform: rotate(-90deg);
        transition: .2s;
      }
    }
  }
}

.response-table-wrapper {
  padding-top: 8px;
  padding-left: 18px;
  margin-left: 30px;
  border-left: 1px solid #eaebf0;
}

.response-table {
  width: 100%;
  border: 1px solid #dcdee5;
  border-collapse: collapse;
  border-spacing: 0;

  .table-head-row-cell,
  .table-body-row-cell {
    height: 42px;
    font-size: 12px;

    &.arrow-col {
      width: 32px;

      .expand-icon.expanded {
        transform: rotate(90deg);
      }
    }

    &.type-col {
      width: 160px;
    }

    &.name-col {
      border-left: none;
    }

    &.description-col {
      width: 300px;
    }

    &.actions-col {
      width: 110px;
    }
  }

  .table-head-row-cell {
    padding-left: 16px;
    font-weight: normal;
    color: #313238;
    background-color: #fafbfd;
    border-bottom: 1px solid #dcdee5;

    &:hover {
      background-color: #f0f1f5;
    }
  }

  .table-body {

    .readonly-value-wrapper {
      padding-left: 16px;
      font-size: 12px;
      cursor: auto;
    }

    .table-body-row {

      .table-body-row-cell {

        &.arrow-col {
          text-align: center;
        }

        &.actions-col {
          width: 110px;
          padding-left: 16px;
        }

        :deep(.bk-select),
        :deep(.bk-select-trigger),
        :deep(.bk-input),
        :deep(.bk-input--text) {
          height: 100%;
          border: none;
        }

        // 输入框和 placeholder 样式

        :deep(.bk-input) {

          &:hover {
            border: 1px solid #a3c5fd;
          }

          &.is-disabled {
            background-color: #fff;

            &:hover {
              border: none;
            }
          }

          &.is-focused:not(.is-readonly) {
            border: 1px solid #a3c5fd;
            box-shadow: none;
          }

          .bk-input--text {
            font-size: 12px !important;
            background-color: #fff;
            padding-inline: 16px;

            &::placeholder {
              font-size: 12px !important;
            }
          }
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
      }
    }
  }
}

.add-param-btn-row {
  height: 42px;
  padding-left: 14px;
  border: 1px solid #dcdee5;
  border-top: none;
  align-content: center;
}
</style>
