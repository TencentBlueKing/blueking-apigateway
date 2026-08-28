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
  <BkPopover
    :popover-delay="0"
    ext-cls="request-params-field-settings-popover"
    placement="bottom-end"
    theme="light"
    trigger="click"
    width="480"
  >
    <BkButton
      v-bk-tooltips="{ content: t('字段设置') }"
      class="field-settings-trigger"
      text
    >
      <AgIcon
        name="settings"
        size="14"
      />
    </BkButton>

    <template #content>
      <div class="field-settings-panel">
        <div class="field-settings-panel__header">
          <div class="field-settings-panel__title">
            {{ t('字段设置') }}
          </div>
          <div class="field-settings-panel__path">
            {{ fieldName || t('根节点') }} · {{ type }}
          </div>
        </div>

        <div class="field-settings-panel__content">
          <section class="field-settings-panel__section">
            <div class="field-settings-panel__section-title">
              {{ t('基础设置') }}
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('标题') }}
              </label>
              <BkInput
                :model-value="getTextValue('title')"
                :placeholder="t('请输入标题')"
                @update:model-value="updateTextKeyword('title', $event)"
              />
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('说明') }}
              </label>
              <BkInput
                v-model="description"
                :placeholder="t('请输入说明')"
                :rows="3"
                type="textarea"
              />
            </div>

            <div class="field-settings-panel__switch-grid">
              <div class="field-settings-panel__switch-item">
                <span>{{ t('可为空') }}</span>
                <BkSwitcher
                  :model-value="Boolean(schemaOptions.nullable)"
                  size="small"
                  theme="primary"
                  @update:model-value="updateBooleanKeyword('nullable', $event)"
                />
              </div>
              <div class="field-settings-panel__switch-item">
                <span>{{ t('已废弃') }}</span>
                <BkSwitcher
                  :model-value="Boolean(schemaOptions.deprecated)"
                  size="small"
                  theme="primary"
                  @update:model-value="updateBooleanKeyword('deprecated', $event)"
                />
              </div>
              <div class="field-settings-panel__switch-item">
                <span>{{ t('只读') }}</span>
                <BkSwitcher
                  :model-value="Boolean(schemaOptions.readOnly)"
                  size="small"
                  theme="primary"
                  @update:model-value="updateBooleanKeyword('readOnly', $event)"
                />
              </div>
              <div class="field-settings-panel__switch-item">
                <span>{{ t('只写') }}</span>
                <BkSwitcher
                  :model-value="Boolean(schemaOptions.writeOnly)"
                  size="small"
                  theme="primary"
                  @update:model-value="updateBooleanKeyword('writeOnly', $event)"
                />
              </div>
            </div>
          </section>

          <section
            v-if="type === 'string'"
            class="field-settings-panel__section"
          >
            <div class="field-settings-panel__section-title">
              {{ t('字符串约束') }}
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('格式') }}
              </label>
              <BkSelect
                :model-value="getTextValue('format')"
                :placeholder="t('请选择格式')"
                clearable
                @update:model-value="updateTextKeyword('format', $event)"
              >
                <BkOption
                  v-for="format in JSON_SCHEMA_STRING_FORMATS"
                  :id="format"
                  :key="format"
                  :name="format"
                />
              </BkSelect>
            </div>

            <div class="field-settings-panel__form-row">
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最小长度') }}
                </label>
                <BkInput
                  :min="0"
                  :model-value="getNumberValue('minLength')"
                  type="number"
                  @update:model-value="updateNumberKeyword('minLength', $event)"
                />
              </div>
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最大长度') }}
                </label>
                <BkInput
                  :min="0"
                  :model-value="getNumberValue('maxLength')"
                  type="number"
                  @update:model-value="updateNumberKeyword('maxLength', $event)"
                />
              </div>
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('正则表达式') }}
              </label>
              <BkInput
                :model-value="getTextValue('pattern')"
                placeholder="^[a-z]+$"
                @update:model-value="updateTextKeyword('pattern', $event)"
              />
            </div>
          </section>

          <section
            v-if="type === 'number'"
            class="field-settings-panel__section"
          >
            <div class="field-settings-panel__section-title">
              {{ t('数值约束') }}
            </div>

            <div class="field-settings-panel__form-row">
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最小值') }}
                </label>
                <BkInput
                  :model-value="getNumberValue('minimum')"
                  type="number"
                  @update:model-value="updateNumberKeyword('minimum', $event)"
                />
              </div>
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最大值') }}
                </label>
                <BkInput
                  :model-value="getNumberValue('maximum')"
                  type="number"
                  @update:model-value="updateNumberKeyword('maximum', $event)"
                />
              </div>
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('倍数') }}
              </label>
              <BkInput
                :min="0"
                :model-value="getNumberValue('multipleOf')"
                type="number"
                @update:model-value="updateNumberKeyword('multipleOf', $event)"
              />
            </div>
          </section>

          <section
            v-if="type === 'array'"
            class="field-settings-panel__section"
          >
            <div class="field-settings-panel__section-title">
              {{ t('数组约束') }}
            </div>

            <div class="field-settings-panel__form-row">
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最少元素') }}
                </label>
                <BkInput
                  :min="0"
                  :model-value="getNumberValue('minItems')"
                  type="number"
                  @update:model-value="updateNumberKeyword('minItems', $event)"
                />
              </div>
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最多元素') }}
                </label>
                <BkInput
                  :min="0"
                  :model-value="getNumberValue('maxItems')"
                  type="number"
                  @update:model-value="updateNumberKeyword('maxItems', $event)"
                />
              </div>
            </div>

            <div class="field-settings-panel__switch-item">
              <span>{{ t('元素唯一') }}</span>
              <BkSwitcher
                :model-value="Boolean(schemaOptions.uniqueItems)"
                size="small"
                theme="primary"
                @update:model-value="updateBooleanKeyword('uniqueItems', $event)"
              />
            </div>
          </section>

          <section
            v-if="type === 'object'"
            class="field-settings-panel__section"
          >
            <div class="field-settings-panel__section-title">
              {{ t('对象约束') }}
            </div>

            <div class="field-settings-panel__form-row">
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最少属性') }}
                </label>
                <BkInput
                  :min="0"
                  :model-value="getNumberValue('minProperties')"
                  type="number"
                  @update:model-value="updateNumberKeyword('minProperties', $event)"
                />
              </div>
              <div class="field-settings-panel__form-item">
                <label class="field-settings-panel__label">
                  {{ t('最多属性') }}
                </label>
                <BkInput
                  :min="0"
                  :model-value="getNumberValue('maxProperties')"
                  type="number"
                  @update:model-value="updateNumberKeyword('maxProperties', $event)"
                />
              </div>
            </div>

            <div class="field-settings-panel__switch-item">
              <span>{{ t('允许额外属性') }}</span>
              <BkSwitcher
                :model-value="schemaOptions.additionalProperties !== false"
                size="small"
                theme="primary"
                @update:model-value="handleAdditionalPropertiesChange"
              />
            </div>
          </section>

          <section
            v-if="supportsValues"
            class="field-settings-panel__section"
          >
            <div class="field-settings-panel__section-title">
              {{ t('示例与枚举') }}
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('默认值') }}
              </label>
              <BkInput
                v-model="defaultValueInput"
                :placeholder="t('请输入默认值')"
                @blur="commitDefaultValue"
                @enter="commitDefaultValue"
              />
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('示例值') }}
              </label>
              <BkInput
                v-model="exampleValueInput"
                :placeholder="t('请输入示例值')"
                @blur="commitExampleValue"
                @enter="commitExampleValue"
              />
            </div>

            <div class="field-settings-panel__form-item">
              <label class="field-settings-panel__label">
                {{ t('枚举值') }}
              </label>
              <BkInput
                v-model="enumValueInput"
                :placeholder="t('每行输入一个枚举值')"
                :rows="4"
                type="textarea"
                @blur="commitEnumValues"
              />
              <div
                v-if="valueError"
                class="field-settings-panel__error"
              >
                {{ valueError }}
              </div>
            </div>
          </section>
        </div>
      </div>
    </template>
  </BkPopover>
</template>

<script lang="ts" setup>
import {
  type BodyParameterType,
  JSON_SCHEMA_STRING_FORMATS,
} from './types';

interface IProps {
  fieldName?: string
  type: BodyParameterType
}

const schemaOptions = defineModel<Record<string, unknown>>('schema', {
  default: () => ({}),
});

const description = defineModel<string>('description', { default: '' });

const {
  fieldName = '',
  type,
} = defineProps<IProps>();

const { t } = useI18n();

const defaultValueInput = ref('');
const enumValueInput = ref('');
const exampleValueInput = ref('');
const valueError = ref('');

const supportsValues = computed(() => [
  'boolean',
  'number',
  'string',
].includes(type));

const updateKeyword = (
  keyword: string,
  value: unknown,
  shouldDelete = false,
) => {
  const nextSchema = { ...schemaOptions.value };

  if (shouldDelete) {
    delete nextSchema[keyword];
  }
  else {
    nextSchema[keyword] = value;
  }

  schemaOptions.value = nextSchema;
};

const getTextValue = (keyword: string) => {
  const value = schemaOptions.value[keyword];
  return typeof value === 'string' ? value : '';
};

const getNumberValue = (keyword: string) => {
  const value = schemaOptions.value[keyword];
  return typeof value === 'number' ? value : undefined;
};

const updateTextKeyword = (keyword: string, value: unknown) => {
  const text = typeof value === 'string' ? value : '';
  updateKeyword(keyword, text, !text);
};

const updateNumberKeyword = (keyword: string, value: unknown) => {
  if (value === '' || value === undefined || value === null) {
    updateKeyword(keyword, undefined, true);
    return;
  }

  const numberValue = Number(value);

  if (Number.isFinite(numberValue)) {
    updateKeyword(keyword, numberValue);
  }
};

const updateBooleanKeyword = (keyword: string, value: unknown) => {
  const boolValue = Boolean(value);
  updateKeyword(keyword, boolValue, !boolValue);
};

const handleAdditionalPropertiesChange = (value: unknown) => {
  updateKeyword('additionalProperties', false, Boolean(value));
};

const serializeValue = (value: unknown) => {
  if (value === undefined) {
    return '';
  }

  if (type === 'string') {
    return String(value);
  }

  return JSON.stringify(value);
};

const parseValue = (value: string) => {
  if (type === 'string') {
    return value;
  }

  if (type === 'number') {
    const numberValue = Number(value);

    if (!Number.isFinite(numberValue)) {
      throw new Error(t('请输入有效数字'));
    }

    return numberValue;
  }

  if (type === 'boolean') {
    if (value === 'true') {
      return true;
    }

    if (value === 'false') {
      return false;
    }

    throw new Error(t('布尔值只能是 true 或 false'));
  }

  return JSON.parse(value);
};

const commitValue = (
  keyword: 'default' | 'examples',
  value: string,
) => {
  valueError.value = '';

  if (!value) {
    updateKeyword(keyword, undefined, true);
    return;
  }

  try {
    const parsedValue = parseValue(value);
    updateKeyword(keyword, keyword === 'examples' ? [parsedValue] : parsedValue);
  }
  catch (error) {
    valueError.value = error instanceof Error ? error.message : String(error);
  }
};

const commitDefaultValue = () => {
  commitValue('default', defaultValueInput.value);
};

const commitExampleValue = () => {
  commitValue('examples', exampleValueInput.value);
};

const commitEnumValues = () => {
  valueError.value = '';
  const values = enumValueInput.value
    .split('\n')
    .map(value => value.trim())
    .filter(Boolean);

  if (!values.length) {
    updateKeyword('enum', undefined, true);
    return;
  }

  try {
    updateKeyword('enum', values.map(parseValue));
  }
  catch (error) {
    valueError.value = error instanceof Error ? error.message : String(error);
  }
};

watch(
  () => [
    type,
    schemaOptions.value.default,
    schemaOptions.value.enum,
    schemaOptions.value.examples,
  ],
  () => {
    valueError.value = '';
    defaultValueInput.value = serializeValue(schemaOptions.value.default);
    const examples = Array.isArray(schemaOptions.value.examples)
      ? schemaOptions.value.examples
      : [];
    exampleValueInput.value = serializeValue(examples[0]);
    const enumValues = Array.isArray(schemaOptions.value.enum)
      ? schemaOptions.value.enum
      : [];
    enumValueInput.value = enumValues.map(serializeValue).join('\n');
  },
  { immediate: true },
);
</script>

<style lang="scss" scoped>
.field-settings-trigger {
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

.field-settings-panel {
  height: min(600px, calc(100vh - 120px));
  overflow: hidden;
  color: #313238;
  background: #FAFBFD;

  :deep(.bk-input),
  :deep(.bk-select),
  :deep(.bk-select-trigger),
  :deep(.bk-textarea) {
    font-size: 12px;
  }

  :deep(.bk-input--text),
  :deep(textarea) {
    font-size: 12px !important;

    &::placeholder {
      font-size: 12px !important;
    }
  }

  &__header {
    height: 58px;
    padding: 10px 16px;
    background: #FFF;
    border-bottom: 1px solid #DCDEE5;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
  }

  &__path {
    margin-top: 3px;
    overflow: hidden;
    font-family: menlo, monaco, consolas, monospace;
    font-size: 11px;
    color: #979BA5;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__content {
    height: calc(100% - 58px);
    padding: 16px;
    overflow-y: auto;
  }

  &__section {
    padding: 16px;
    margin-bottom: 12px;
    background: #FFF;
    border: 1px solid #EAEBF0;
    border-radius: 4px;
  }

  &__section-title {
    padding-bottom: 10px;
    margin-bottom: 14px;
    font-size: 13px;
    font-weight: 600;
    border-bottom: 1px solid #EAEBF0;
  }

  &__form-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  &__form-item {
    margin-bottom: 14px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__label {
    display: block;
    margin-bottom: 6px;
    font-size: 12px;
    color: #63656E;
  }

  &__switch-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 16px;
    padding-top: 4px;
  }

  &__switch-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 28px;
    font-size: 12px;
    color: #63656E;
  }

  &__error {
    margin-top: 5px;
    font-size: 12px;
    line-height: 18px;
    color: #EA3636;
  }
}
</style>

<style lang="scss">
.request-params-field-settings-popover.bk-popover.bk-pop2-content {
  padding: 0;
}
</style>
