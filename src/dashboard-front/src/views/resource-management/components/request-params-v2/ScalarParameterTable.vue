<!--
  TencentBlueKing is pleased to support the open source community by making
  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
  Copyright (C) Tencent. All rights reserved.
  Licensed under the MIT License (the "License"); you may not use this file except
  in compliance with the License. You may obtain a copy of the License at

  http://opensource.org/licenses/MIT

  Unless required by applicable law or agreed to in writing, software distributed under
  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
  either express or implied. See the License for the specific language governing permissions and
  limitations under the License.

  We undertake not to change the open source license (MIT license) applicable
  to the current version of the project delivered to anyone in the future.
-->

<template>
  <div
    class="scalar-parameter-table"
    :class="{ 'is-readonly': readonly }"
  >
    <div class="scalar-parameter-table__scroll">
      <table>
        <thead>
          <tr>
            <th class="name-column">
              {{ t('参数名') }}
            </th>
            <th class="type-column">
              {{ t('类型') }}
            </th>
            <th class="required-column">
              {{ t('必填') }}
            </th>
            <th class="default-column">
              {{ t('默认值') }}
            </th>
            <th class="description-column">
              {{ t('schema说明') }}
            </th>
            <th
              v-if="!readonly"
              class="operation-column"
            >
              {{ t('操作') }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="row in rows"
            :key="row.id"
          >
            <td
              class="name-column"
              :class="{ 'control-cell': !readonly }"
            >
              <span
                v-if="readonly"
                class="readonly-value"
              >
                {{ row.name || '--' }}
              </span>
              <div
                v-else
                class="cell-editor"
              >
                <BkInput
                  v-model="row.name"
                  :placeholder="t('参数名')"
                  :status="errors[row.id] ? 'error' : undefined"
                  @input="emit('clear-error', row.id)"
                />
                <span
                  v-if="errors[row.id]"
                  class="cell-error"
                >
                  {{ errors[row.id] }}
                </span>
              </div>
            </td>

            <td
              class="type-column"
              :class="{ 'control-cell': !readonly }"
            >
              <span
                v-if="readonly"
                class="type-tag"
                :class="`type-tag--${row.type}`"
              >
                {{ row.type }}
              </span>
              <BkSelect
                v-else
                :clearable="false"
                :model-value="row.type"
                @update:model-value="handleTypeChange(row, $event)"
              >
                <BkOption
                  v-for="type in SCALAR_PARAMETER_TYPES"
                  :id="type"
                  :key="type"
                  :name="type"
                />
              </BkSelect>
            </td>

            <td class="required-column">
              <span
                v-if="readonly"
                class="readonly-value"
              >
                {{ row.required ? t('是') : t('否') }}
              </span>
              <BkSwitcher
                v-else
                v-model="row.required"
                :disabled="location === 'path'"
                size="small"
                theme="primary"
              />
            </td>

            <td
              class="default-column"
              :class="{ 'control-cell': !readonly }"
            >
              <span
                v-if="readonly"
                class="readonly-value"
              >
                {{ formatValue(row.options.default) }}
              </span>
              <BkSelect
                v-else-if="row.type === 'boolean'"
                :allow-empty-values="[false]"
                :list="booleanOptions"
                :model-value="row.options.default"
                clearable
                @update:model-value="handleDefaultChange(row, $event)"
              />
              <BkInput
                v-else
                :model-value="getEditableDefault(row)"
                :placeholder="t('默认值')"
                :type="row.type === 'number' ? 'number' : 'text'"
                @update:model-value="handleDefaultChange(row, $event)"
              />
            </td>

            <td
              class="description-column"
              :class="{ 'control-cell': !readonly }"
            >
              <span
                v-if="readonly"
                class="readonly-value"
              >
                {{ row.description || '--' }}
              </span>
              <BkInput
                v-else
                v-model="row.description"
                :placeholder="t('schema说明')"
              />
            </td>

            <td
              v-if="!readonly"
              class="operation-column"
            >
              <div class="row-actions">
                <FieldSettingsPopover
                  v-model:description="row.description"
                  v-model:schema="row.options"
                  :field-name="`${location}.${row.name || '--'}`"
                  :type="row.type"
                />
                <BkButton
                  v-bk-tooltips="{ content: t('删除参数') }"
                  class="delete-button"
                  text
                  @click="removeRow(row.id)"
                >
                  <AgIcon
                    name="minus-circle-shape"
                    size="14"
                  />
                </BkButton>
              </div>
            </td>
          </tr>

          <tr v-if="!rows.length">
            <td
              :colspan="readonly ? 5 : 6"
              class="empty-cell"
            >
              {{ t('暂无数据') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="!readonly"
      class="add-row"
    >
      <BkButton
        text
        theme="primary"
        @click="addRow"
      >
        <AgIcon name="add-small" />
        {{ t('新增参数') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import FieldSettingsPopover from './FieldSettingsPopover.vue';
import { createRequestParameter } from './request-schema';
import {
  type IRequestParameterRow,
  type ParameterLocation,
  SCALAR_PARAMETER_TYPES,
  type ScalarParameterType,
} from './types';

interface IProps {
  errors?: Record<string, string>
  location: ParameterLocation
  readonly?: boolean
}

interface IEmits {
  'clear-error': [id: string]
}

const rows = defineModel<IRequestParameterRow[]>({ default: () => [] });

const {
  errors = {},
  location,
  readonly = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const booleanOptions = [
  {
    label: 'true',
    value: true,
  },
  {
    label: 'false',
    value: false,
  },
];

const formatValue = (value: unknown) => {
  if (value === undefined || value === null || value === '') {
    return '--';
  }

  return typeof value === 'object' ? JSON.stringify(value) : String(value);
};

const getEditableDefault = (row: IRequestParameterRow) => {
  const value = row.options.default;
  return value === undefined || value === null ? '' : String(value);
};

const handleDefaultChange = (
  row: IRequestParameterRow,
  value: unknown,
) => {
  if (value === '' || value === undefined || value === null) {
    delete row.options.default;
    return;
  }

  row.options.default = row.type === 'number' ? Number(value) : value;
};

const handleTypeChange = (
  row: IRequestParameterRow,
  value: unknown,
) => {
  if (!SCALAR_PARAMETER_TYPES.includes(value as ScalarParameterType)) {
    return;
  }

  row.type = value as ScalarParameterType;
  row.options = {};
};

const addRow = () => {
  rows.value.push(createRequestParameter(location));
};

const removeRow = (id: string) => {
  const index = rows.value.findIndex(row => row.id === id);

  if (index > -1) {
    rows.value.splice(index, 1);
    emit('clear-error', id);
  }
};
</script>

<style lang="scss" scoped>
.scalar-parameter-table {
  border: 1px solid #DCDEE5;

  &__scroll {
    overflow-x: auto;
  }

  table {
    width: 100%;
    min-width: 920px;
    border-collapse: collapse;
    table-layout: fixed;
  }

  &.is-readonly table {
    min-width: 800px;
  }

  th,
  td {
    height: 42px;
    padding: 0 12px;
    font-size: 12px;
    text-align: left;
    border-right: 1px solid #EAEBF0;
    border-bottom: 1px solid #EAEBF0;

    &:last-child {
      border-right: 0;
    }
  }

  th {
    font-weight: 400;
    color: #63656E;
    background: #F5F7FA;
  }

  tbody tr:last-child td {
    border-bottom: 0;
  }

  .name-column {
    width: 190px;
  }

  .type-column {
    width: 130px;
  }

  .required-column {
    width: 78px;
    text-align: center;
  }

  .default-column {
    width: 180px;
  }

  .description-column {
    width: auto;
  }

  .operation-column {
    width: 92px;
  }

  .cell-editor {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .cell-error {
    position: absolute;
    top: 34px;
    left: 0;
    z-index: 2;
    padding: 2px 6px;
    color: #EA3636;
    background: #FFF0F0;
    border-radius: 2px;
    box-shadow: 0 2px 6px rgb(0 0 0 / 10%);
  }

  .readonly-value {
    display: block;
    line-height: 20px;
    word-break: break-all;
    white-space: normal;
  }

  .type-tag {
    display: inline-flex;
    align-items: center;
    height: 22px;
    padding: 0 8px;
    color: #3A84FF;
    background: #EDF4FF;
    border-radius: 11px;

    &--number {
      color: #B95D06;
      background: #FFF3E1;
    }

    &--boolean {
      color: #087F5B;
      background: #E6F6F0;
    }
  }

  .row-actions {
    display: flex;
    gap: 4px;
    align-items: center;
  }

  .delete-button {
    width: 28px;
    height: 28px;
    min-width: 28px;
    padding: 0;
    color: #63656E;

    &:hover {
      color: #EA3636;
      background: #FFF0F0;
    }
  }

  .empty-cell {
    height: 88px;
    color: #979BA5;
    text-align: center;
  }

  .add-row {
    display: flex;
    align-items: center;
    height: 42px;
    padding-left: 12px;
    border-top: 1px solid #DCDEE5;
  }

  .control-cell {
    padding: 0;

    :deep(.bk-input),
    :deep(.bk-select),
    :deep(.bk-select-trigger) {
      width: 100%;
      height: 100%;
    }

    :deep(.bk-input) {
      font-size: 12px;
      border: 0;
      border-radius: 0;

      &.is-focused:not(.is-readonly) {
        border: 1px solid #A3C5FD;
        box-shadow: none;
      }
    }

    :deep(.bk-input--text) {
      font-size: 12px !important;

      &::placeholder {
        font-size: 12px !important;
      }
    }
  }
}
</style>
