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
    class="body-parameter-table"
    :class="{ 'is-readonly': readonly }"
  >
    <div class="body-parameter-table__scroll">
      <table>
        <thead>
          <tr>
            <th class="name-column pl-12px!">
              {{ t('字段名称') }}
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
            v-for="item in flatRows"
            :key="item.row.id"
            :class="{
              'is-array-item': item.isArrayItem,
              'is-root': item.isRoot,
            }"
          >
            <td
              class="name-column"
              :class="{
                'control-cell': !readonly && !item.isRoot && !item.isArrayItem,
              }"
            >
              <div
                class="field-name"
                :style="{ paddingLeft: `${12 + item.depth * 22}px` }"
              >
                <span
                  class="type-icon"
                  :class="`type-icon--${item.row.type}`"
                >
                  {{ getTypeInitial(item.row.type) }}
                </span>
                <span
                  v-if="readonly || item.isRoot || item.isArrayItem"
                  class="readonly-value field-name__text"
                >
                  {{ getFieldName(item) }}
                </span>
                <div
                  v-else
                  class="cell-editor field-name__editor"
                >
                  <BkInput
                    v-model="item.row.name"
                    :placeholder="t('字段名')"
                    :status="errors[item.row.id] ? 'error' : undefined"
                    @input="emit('clear-error', item.row.id)"
                  />
                  <span
                    v-if="errors[item.row.id]"
                    class="cell-error"
                  >
                    {{ errors[item.row.id] }}
                  </span>
                </div>
              </div>
            </td>

            <td
              class="type-column"
              :class="{ 'control-cell': !readonly }"
            >
              <span
                v-if="readonly"
                class="type-tag"
                :class="`type-tag--${item.row.type}`"
              >
                {{ item.row.type }}
              </span>
              <BkSelect
                v-else
                :clearable="false"
                :model-value="item.row.type"
                @update:model-value="handleTypeChange(item.row, $event)"
              >
                <BkOption
                  v-for="type in BODY_PARAMETER_TYPES"
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
                {{ getRequired(item) ? t('是') : t('否') }}
              </span>
              <BkSwitcher
                v-else
                :model-value="getRequired(item)"
                size="small"
                theme="primary"
                @update:model-value="handleRequiredChange(item, $event)"
              />
            </td>

            <td
              class="default-column"
              :class="{
                'control-cell': !readonly && !['array', 'object'].includes(item.row.type),
              }"
            >
              <span
                v-if="readonly"
                class="readonly-value"
              >
                {{ formatValue(item.row.options.default) }}
              </span>
              <span
                v-else-if="item.row.type === 'array' || item.row.type === 'object'"
                class="disabled-value"
              >
                --
              </span>
              <BkSelect
                v-else-if="item.row.type === 'boolean'"
                :allow-empty-values="[false]"
                :list="booleanOptions"
                :model-value="item.row.options.default"
                clearable
                @update:model-value="handleDefaultChange(item.row, $event)"
              />
              <BkInput
                v-else
                :model-value="getEditableDefault(item.row)"
                :placeholder="t('默认值')"
                :type="item.row.type === 'number' ? 'number' : 'text'"
                @update:model-value="handleDefaultChange(item.row, $event)"
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
                {{ item.row.description || '--' }}
              </span>
              <BkInput
                v-else
                v-model="item.row.description"
                :placeholder="t('schema说明')"
              />
            </td>

            <td
              v-if="!readonly"
              class="operation-column"
            >
              <div class="row-actions">
                <FieldSettingsPopover
                  v-model:description="item.row.description"
                  v-model:schema="item.row.options"
                  :field-name="item.path"
                  :type="item.row.type"
                />
                <BkButton
                  v-if="canAddChild(item.row)"
                  v-bk-tooltips="{ content: t('添加子字段') }"
                  text
                  @click="addChild(item.row)"
                >
                  <AgIcon
                    name="plus-circle-shape"
                    size="14"
                  />
                </BkButton>
                <BkButton
                  v-if="!item.isRoot"
                  v-bk-tooltips="{ content: t('删除字段') }"
                  class="delete-button"
                  text
                  @click="removeField(item)"
                >
                  <AgIcon
                    name="minus-circle-shape"
                    size="14"
                  />
                </BkButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="!readonly && body.root.type === 'object'"
      class="add-row"
    >
      <BkButton
        text
        theme="primary"
        @click="addChild(body.root)"
      >
        <AgIcon name="add-small" />
        {{ t('新增字段') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import FieldSettingsPopover from './FieldSettingsPopover.vue';
import {
  createRequestField,
  flattenRequestFields,
  resetFieldForType,
} from './request-schema';
import {
  BODY_PARAMETER_TYPES,
  type BodyParameterType,
  type IFlatRequestFieldRow,
  type IRequestBodyState,
  type IRequestFieldRow,
} from './types';

interface IProps {
  errors?: Record<string, string>
  readonly?: boolean
}

interface IEmits {
  'clear-error': [id: string]
}

const body = defineModel<IRequestBodyState>({ required: true });

const {
  errors = {},
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

const flatRows = computed(() => flattenRequestFields(body.value.root));

const formatValue = (value: unknown) => {
  if (value === undefined || value === null || value === '') {
    return '--';
  }

  return typeof value === 'object' ? JSON.stringify(value) : String(value);
};

const getEditableDefault = (row: IRequestFieldRow) => {
  const value = row.options.default;
  return value === undefined || value === null ? '' : String(value);
};

const getFieldName = (item: IFlatRequestFieldRow) => {
  if (item.isRoot) {
    return t('根节点');
  }

  if (item.isArrayItem) {
    return t('数组元素');
  }

  return item.row.name || '--';
};

const getTypeInitial = (type: BodyParameterType) => {
  const initials: Record<BodyParameterType, string> = {
    array: '[]',
    boolean: 'B',
    number: '#',
    object: '{}',
    string: 'S',
  };

  return initials[type];
};

const getRequired = (item: IFlatRequestFieldRow) => {
  return item.isRoot ? body.value.required : item.row.required;
};

const handleRequiredChange = (
  item: IFlatRequestFieldRow,
  value: unknown,
) => {
  if (item.isRoot) {
    body.value.required = Boolean(value);
  }
  else {
    item.row.required = Boolean(value);
  }
};

const handleDefaultChange = (
  row: IRequestFieldRow,
  value: unknown,
) => {
  if (value === '' || value === undefined || value === null) {
    delete row.options.default;
    return;
  }

  row.options.default = row.type === 'number' ? Number(value) : value;
};

const handleTypeChange = (
  row: IRequestFieldRow,
  value: unknown,
) => {
  if (!BODY_PARAMETER_TYPES.includes(value as BodyParameterType)) {
    return;
  }

  resetFieldForType(row, value as BodyParameterType);
};

const canAddChild = (row: IRequestFieldRow) => {
  if (row.type === 'object') {
    return true;
  }

  return row.type === 'array' && !row.children?.length;
};

const addChild = (row: IRequestFieldRow) => {
  const child = createRequestField();
  row.children = row.children ?? [];

  if (row.type === 'array') {
    child.name = '';
    row.children.splice(0, row.children.length, child);
  }
  else {
    row.children.push(child);
  }
};

const removeField = (item: IFlatRequestFieldRow) => {
  if (!item.parent) {
    return;
  }

  const index = item.parent.children?.findIndex(child => child.id === item.row.id) ?? -1;

  if (index > -1) {
    item.parent.children?.splice(index, 1);
    emit('clear-error', item.row.id);
  }
};
</script>

<style lang="scss" scoped>
.body-parameter-table {
  border: 1px solid #DCDEE5;

  &__scroll {
    overflow-x: auto;
  }

  table {
    width: 100%;
    min-width: 1020px;
    border-collapse: collapse;
    table-layout: fixed;
  }

  &.is-readonly table {
    min-width: 800px;
  }

  th,
  td {
    height: 44px;
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
    height: 42px;
    font-weight: 400;
    color: #63656E;
    background: #F5F7FA;
  }

  tbody tr:last-child td {
    border-bottom: 0;
  }

  tbody tr.is-root {
    background: #FAFBFD;
  }

  tbody tr.is-array-item {
    background: #FCFCFD;
  }

  .name-column {
    width: 260px;
    padding-left: 0;
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
    width: 126px;
  }

  .field-name {
    display: flex;
    height: 44px;
    min-width: 0;
    align-items: center;

    &__text {
      min-width: 0;
    }

    &__editor {
      flex: 1;
      min-width: 0;
    }
  }

  .type-icon {
    display: inline-flex;
    flex: 0 0 24px;
    align-items: center;
    justify-content: center;
    height: 24px;
    margin-right: 8px;
    font-size: 10px;
    font-weight: 700;
    color: #3A84FF;
    background: #E1ECFF;
    border-radius: 4px;

    &--array,
    &--object {
      color: #7A4EAB;
      background: #F0E7FA;
    }

    &--number {
      color: #B95D06;
      background: #FFF3E1;
    }

    &--boolean {
      color: #087F5B;
      background: #E6F6F0;
    }
  }

  .type-tag {
    display: inline-flex;
    align-items: center;
    height: 22px;
    padding: 0 8px;
    color: #3A84FF;
    background: #EDF4FF;
    border-radius: 11px;

    &--array,
    &--object {
      color: #7A4EAB;
      background: #F4ECFA;
    }

    &--number {
      color: #B95D06;
      background: #FFF3E1;
    }

    &--boolean {
      color: #087F5B;
      background: #E6F6F0;
    }
  }

  .cell-editor {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .cell-error {
    position: absolute;
    top: 36px;
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

  .disabled-value {
    color: #C4C6CC;
  }

  .row-actions {
    display: flex;
    gap: 2px;
    align-items: center;

    :deep(.bk-button) {
      width: 28px;
      height: 28px;
      min-width: 28px;
      padding: 0;
      color: #63656E;

      &:hover {
        color: #3A84FF;
        background: #E1ECFF;
      }
    }

    .delete-button:hover {
      color: #EA3636;
      background: #FFF0F0;
    }
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
