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
    class="response-parameter-table"
    :class="{ 'is-readonly': readonly }"
  >
    <div class="response-parameter-table__scroll">
      <table>
        <!-- 响应字段表头：参数名、类型、说明，以及编辑态操作列。 -->
        <thead>
          <tr>
            <th class="name-column pl-12px!">
              {{ t('参数名') }}
            </th>
            <th class="type-column">
              {{ t('类型') }}
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

        <!-- 响应字段树被扁平化为表格行，并通过缩进保留对象和数组层级。 -->
        <tbody>
          <tr
            v-for="item in flatRows"
            :key="item.row.id"
            :class="{
              'is-array-item': item.isArrayItem,
              'is-root': item.isRoot,
            }"
          >
            <!-- 名称列展示层级和类型图标；根节点、数组元素名称不可编辑。 -->
            <td
              class="name-column"
              :class="{
                'control-cell': !readonly && !item.isRoot && !item.isArrayItem,
              }"
            >
              <div
                class="field-name"
                :style="{ paddingLeft: (12 + item.depth * 22) + 'px' }"
              >
                <span
                  class="type-icon"
                  :class="'type-icon--' + item.row.type"
                >
                  {{ getTypeInitial(item.row.type) }}
                </span>
                <span
                  v-if="readonly || item.isRoot || item.isArrayItem"
                  class="readonly-value field-name__text"
                >
                  {{ getFieldName(item) }}
                </span>
                <BkInput
                  v-else
                  v-model="item.row.name"
                  class="field-name__editor"
                  :placeholder="t('字段名')"
                  :status="errors[item.row.id] ? 'error' : undefined"
                  @input="emit('clear-error', item.row.id)"
                >
                  <template
                    v-if="errors[item.row.id]"
                    #suffix
                  >
                    <span
                      v-bk-tooltips="{ content: errors[item.row.id] }"
                      class="field-error-icon-wrapper"
                    >
                      <AgIcon
                        class="field-error-icon"
                        name="exclamation-circle-fill"
                        size="13"
                      />
                    </span>
                  </template>
                </BkInput>
              </div>
            </td>

            <!-- 类型列控制当前节点的 Schema 类型。 -->
            <td
              class="type-column"
              :class="{ 'control-cell': !readonly }"
            >
              <span
                v-if="readonly"
                class="type-tag"
                :class="'type-tag--' + item.row.type"
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

            <!-- 查看态截断过长说明并提供提示，编辑态使用输入框。 -->
            <td
              class="description-column"
              :class="{ 'control-cell': !readonly }"
            >
              <div
                v-if="readonly"
                class="readonly-value"
              >
                <BkOverflowTitle type="tips">
                  {{ item.row.description || '--' }}
                </BkOverflowTitle>
              </div>
              <BkInput
                v-else
                v-model="item.row.description"
                :placeholder="t('schema说明')"
              />
            </td>

            <!-- 操作列提供字段设置、添加子字段和删除当前字段。 -->
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
                  v-bk-tooltips="{ content: t('添加字段') }"
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

    <!-- 根节点为对象时，可从表格底部快速新增一级字段。 -->
    <div
      v-if="!readonly && root.type === 'object'"
      class="add-row"
    >
      <BkButton
        text
        theme="primary"
        @click="addChild(root)"
      >
        <AgIcon name="add-small" />
        {{ t('新增字段') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import FieldSettingsPopover from '../../request-params-v2/components/FieldSettingsPopover.vue';
import {
  createResponseField,
  flattenResponseFields,
  resetResponseFieldForType,
} from '../utils';
import {
  BODY_PARAMETER_TYPES,
  type BodyParameterType,
  type IFlatResponseFieldRow,
  type IResponseFieldRow,
} from '../types';

interface IProps {
  errors?: Record<string, string>
  readonly?: boolean
}

interface IEmits {
  'clear-error': [id: string]
}

const root = defineModel<IResponseFieldRow>({ required: true });

const {
  errors = {},
  readonly = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const flatRows = computed(() => flattenResponseFields(root.value));

/** 获取字段展示名，并为根节点和数组元素提供固定名称。 */
const getFieldName = (item: IFlatResponseFieldRow) => {
  if (item.isRoot) {
    return t('根节点');
  }

  if (item.isArrayItem) {
    return t('数组元素');
  }

  return item.row.name || '--';
};

/** 获取字段类型在名称列中展示的简写图标文本。 */
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

/** 切换字段类型，并为新建的对象或数组补充一个可编辑子字段。 */
const handleTypeChange = (
  row: IResponseFieldRow,
  value: unknown,
) => {
  if (!BODY_PARAMETER_TYPES.includes(value as BodyParameterType)) {
    return;
  }

  const nextType = value as BodyParameterType;
  const previousType = row.type;
  resetResponseFieldForType(row, nextType);

  if (
    previousType !== nextType
    && ['array', 'object'].includes(nextType)
    && !row.children?.length
  ) {
    row.children = [createResponseField()];
  }
};

/** 判断对象能否继续添加属性，或数组是否还缺少元素定义。 */
const canAddChild = (row: IResponseFieldRow) => {
  if (row.type === 'object') {
    return true;
  }

  return row.type === 'array' && !row.children?.length;
};

/** 为对象追加属性；数组仅保留一个元素 Schema。 */
const addChild = (row: IResponseFieldRow) => {
  const child = createResponseField();
  row.children = row.children ?? [];

  if (row.type === 'array') {
    row.children.splice(0, row.children.length, child);
  }
  else {
    row.children.push(child);
  }
};

/** 从父节点移除字段，并清理被删除子树中的全部校验错误。 */
const removeField = (item: IFlatResponseFieldRow) => {
  if (!item.parent) {
    return;
  }

  const index = item.parent.children?.findIndex(child => child.id === item.row.id) ?? -1;

  if (index > -1) {
    flattenResponseFields(item.row).forEach(({ row }) => {
      emit('clear-error', row.id);
    });
    item.parent.children?.splice(index, 1);
  }
};
</script>

<style lang="scss" scoped>
.response-parameter-table {
  min-width: 0;
  border: 1px solid #DCDEE5;

  &__scroll {
    width: 100%;
    overflow-x: auto;
  }

  table {
    width: 100%;
    min-width: 760px;
    border-collapse: collapse;
    table-layout: fixed;
  }

  &.is-readonly table {
    min-width: 560px;
  }

  th,
  td {
    height: 44px;
    padding: 0 12px;
    overflow: hidden;
    font-size: 12px;
    text-align: left;
    border-right: 1px solid #EAEBF0;
    border-bottom: 1px solid #EAEBF0;
    box-sizing: border-box;

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
    width: 36%;
    padding-left: 0;
  }

  .type-column {
    width: 160px;
  }

  .description-column {
    width: auto;
  }

  .operation-column {
    width: 126px;
  }

  &.is-readonly {

    .name-column {
      width: 38%;
    }

    .type-column {
      width: 150px;
    }
  }

  .field-name {
    display: flex;
    align-items: center;
    height: 44px;
    min-width: 0;

    &__text {
      min-width: 0;
    }

    &__editor {
      flex: 1;
      min-width: 0;
    }
  }

  .field-error-icon {
    color: #EA3636;
  }

  .field-error-icon-wrapper {
    display: inline-flex;
    flex: 0 0 32px;
    align-items: center;
    justify-content: center;
    height: 100%;
    line-height: 1;
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

  .readonly-value {
    display: block;
    overflow: hidden;
    line-height: 20px;
    text-overflow: ellipsis;
    word-break: break-all;
    white-space: normal;
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
      font-size: 12px;
      box-sizing: border-box;
    }

    :deep(.bk-input) {
      border: 0;
      border-radius: 0;

      &.is-focused:not(.is-readonly) {
        border: 1px solid #A3C5FD;
        box-shadow: none;
      }
    }

    :deep(.bk-input--text) {
      width: 100%;
      font-size: 12px !important;
      box-sizing: border-box;

      &::placeholder {
        font-size: 12px !important;
      }
    }
  }
}
</style>
