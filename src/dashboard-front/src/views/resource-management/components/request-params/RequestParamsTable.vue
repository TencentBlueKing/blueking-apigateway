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
  <div class="request-param-body-table">
    <table
      v-for="row in tableData"
      :key="row.id"
      class="request-body-table"
    >
      <tbody class="table-body">
        <tr class="table-body-row">
          <td class="table-body-row-cell">
            <AgIcon name="right-shape" />
          </td>
          <!-- 字段名 -->
          <td
            class="table-body-row-cell"
            :class="{ 'has-error': invalidRowIdMap[row.id] }"
          >
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
          </td>
          <!-- 字段类型 -->
          <td class="table-body-row-cell type">
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
              @change="() => handleTypeChange(row)"
            >
              <BkOption
                v-for="item in typeList"
                :id="item.value"
                :key="item.value"
                :name="item.label"
              />
            </BkSelect>
          </td>
          <!-- 字段必填 -->
          <td class="table-body-row-cell required">
            <div
              v-if="readonly"
              class="readonly-value-wrapper"
            >
              {{ row.required ? t('是') : t('否') }}
            </div>
            <BkSwitcher
              v-else
              v-model="row.required"
              theme="primary"
              class="ml-16px!"
            />
          </td>
          <!-- 字段默认值 -->
          <td
            :style="readonly ? 'width: 150px' : undefined"
            class="table-body-row-cell default"
          >
            <div
              v-if="readonly"
              class="readonly-value-wrapper"
            >
              {{ row.default || '--' }}
            </div>
            <BkInput
              v-else
              v-model="row.default"
              :placeholder="t('默认值')"
            />
          </td>
          <!-- 字段备注 -->
          <td class="table-body-row-cell description">
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
            class="table-body-row-cell actions"
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
      <tfoot v-if="row.body?.length">
        <tr>
          <td
            :colspan="readonly ? 6 : 7"
            class="pl-16px"
          >
            <RequestParamsTable
              ref="recursive-sub-table-refs"
              v-model="row.body"
              :readonly="readonly"
            />
          </td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script lang="ts" setup>
import { uniqueId } from 'lodash-es';

const tableData = defineModel<IBodyRow[]>();

const { readonly = false } = defineProps<IProps>();

interface IProps { readonly?: boolean }

const { t } = useI18n();

interface IBodyRow {
  id: string
  name: string
  type: string
  required: boolean
  default: string
  description: string
  isEdit: boolean
  body?: IBodyRow[]
}

const recursiveSubTableRef = useTemplateRef('recursive-sub-table-refs');

const invalidRowIdMap = ref<Record<string, boolean>>({});

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

const genBodyRow = (id?: string) => {
  return {
    id: id || uniqueId(),
    name: '',
    type: 'string',
    required: false,
    default: '',
    description: '',
    isEdit: true,
  };
};

const handleTypeChange = (row: IBodyRow) => {
  const _row = tableData.value!.find(data => data.id === row.id);
  if (_row) {
    if (_row.type !== 'object' && _row.type !== 'array') {
      delete _row.body;
    }
    else {
      _row.body = [genBodyRow()];
    }
  }
};

const isAddFieldVisible = (row: IBodyRow) => {
  if (row.type === 'object' || row.type === 'array') {
    if (row.type === 'array') {
      return row.body ? row.body.length === 0 : true;
    }
    return true;
  }
  return false;
};

const addField = (row: IBodyRow) => {
  const bodyRow = tableData.value!.find(data => data.id === row.id);
  if (bodyRow) {
    if (bodyRow.body) {
      bodyRow.body.push(genBodyRow());
    }
    else {
      bodyRow.body = [genBodyRow()];
    }
  }
};

const removeField = (row: IBodyRow) => {
  const index = tableData.value!.findIndex(data => data.id === row.id);
  if (index !== -1) {
    tableData.value!.splice(index, 1);
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
  validate: () => {
    if (recursiveSubTableRef.value?.[0]) {
      return recursiveSubTableRef.value[0].validate().then(() => new Promise((resolve, reject) => {
        setInvalidRowId();
        if (Object.keys(invalidRowIdMap.value).length > 0) {
          reject('invalid request params');
        }
        resolve(true);
      }));
    }
    return new Promise((resolve, reject) => {
      setInvalidRowId();
      if (Object.keys(invalidRowIdMap.value).length > 0) {
        reject('invalid request params');
      }
      resolve(true);
    });
  },
});

</script>

<style lang="scss" scoped>
.bk-table .bk-table-body table tbody tr td {
  border-bottom: none !important;
}

.request-body-table {
  border-collapse: collapse;
  border-spacing: 0;

  .table-body {

    td {
      border-top: 1px solid #dcdee5;
      border-bottom: none !important;
    }

    .readonly-value-wrapper {
      padding-left: 16px;
      font-size: 12px;
      cursor: auto;
    }

    .table-body-row {

      .table-body-row-cell {
        height: 42px;

        &:first-child {
          width: 32px;
          text-align: center;
        }

        &.type {
          width: 100px;
        }

        &.required {
          width: 100px;
        }

        &.default {
          width: 300px;
        }

        &.description {
          width: 300px;
        }

        &.actions {
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

        :deep(.bk-input):hover {
          border: 1px solid #a3c5fd;
        }

        :deep(.bk-input.is-focused:not(.is-readonly)) {
          border: 1px solid #a3c5fd;
          box-shadow: none;
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

        &.has-error {

          :deep(.bk-input--text) {
            background-color: #fff0f1 !important;
          }
        }
      }
    }
  }
}

</style>
