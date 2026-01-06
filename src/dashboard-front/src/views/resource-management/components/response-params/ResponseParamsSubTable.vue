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
  <div>
    <table
      v-for="row in tableData"
      :key="row.id"
      class="response-params-sub-table"
    >
      <tbody class="table-body">
        <tr class="table-body-row">
          <td class="table-body-row-cell arrow-col">
            <AgIcon name="right-shape" />
          </td>
          <!-- 字段名 -->
          <td
            class="table-body-row-cell name-col"
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
              @input="() => handleNameInput(row.id)"
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
          <!-- 字段备注 -->
          <td
            class="table-body-row-cell description"
            :class="{ 'max-w-250px w-250px': readonly }"
          >
            <div
              v-if="readonly"
              class="readonly-value-wrapper"
            >
              <BkOverflowTitle type="tips">
                {{ row.description || '--' }}
              </BkOverflowTitle>
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
      <tfoot v-if="row?.properties?.length">
        <tr>
          <td
            :colspan="readonly ? 4 : 5"
            class="pl-16px"
          >
            <ResponseParamsSubTable
              ref="recursive-sub-table-ref"
              v-model="row.properties"
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
import { type JSONSchema7TypeName } from 'json-schema';

interface IProps { readonly?: boolean }

interface ITableRow {
  id: string
  name: string
  type: JSONSchema7TypeName
  description: string
  properties?: ITableRow[]
}

const tableData = defineModel<ITableRow[]>();

const { readonly = false } = defineProps<IProps>();

const { t } = useI18n();

const tableRef = ref();
const recursiveSubTableRef = useTemplateRef('recursive-sub-table-ref');

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

const invalidRowIdMap = ref<Record<string, boolean>>({});

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
  const targetRow = tableData.value?.find(data => data.id === row.id);
  if (targetRow) {
    if (targetRow.properties) {
      targetRow.properties.push(genRow());
    }
    else {
      targetRow.properties = [genRow()];
    }
  }
};

const removeField = (row: ITableRow) => {
  const index = tableData.value?.findIndex(data => data.id === row.id);
  if (index !== undefined && index !== -1) {
    tableData.value?.splice(index, 1);
  }
};

const handleTypeChange = (row: ITableRow) => {
  const targetRow = tableData.value?.find(data => data.id === row.id);
  if (targetRow) {
    if (row.type === 'object' || row.type === 'array') {
      targetRow.properties = [genRow()];
    }
    else {
      targetRow.properties = [];
    }
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

const handleNameInput = (rowId: string) => {
  delete invalidRowIdMap.value[rowId];
};

onMounted(() => {
  tableRef.value?.setAllRowExpand(true);
});

defineExpose({
  validate: () => new Promise((resolve, reject) => {
    if (recursiveSubTableRef.value?.validate) {
      recursiveSubTableRef.value.validate().catch(() => {
        reject(false);
      });
    }
    setInvalidRowId();
    if (Object.keys(invalidRowIdMap.value).length > 0) {
      reject(false);
    }
    resolve(true);
  }),
});

</script>

<style lang="scss" scoped>

.response-params-sub-table {
  width: 100%;
  border-collapse: collapse;
  border-spacing: 0;

  .table-body {

    .readonly-value-wrapper {
      padding-left: 16px;
      font-size: 12px;
      cursor: auto;
    }

    .table-body-row {

      .table-body-row-cell {
        height: 42px;
        font-size: 12px;

        &.arrow-col {
          width: 32px;
          text-align: center;
          border-right: none;
        }

        &.name-col {
          border-left: none;

          &.has-error {

            :deep(.bk-input) {

              .bk-input--text {
                background-color: #fff0f1 !important;
              }
            }
          }
        }

        &.type {
          width: 160px;
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

        // 输入框和 placeholder 样式

        :deep(.bk-input) {

          &:hover {
            border: 1px solid #a3c5fd;
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

</style>
