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
  <div class="custom-plugin-form-wrapper">
    <template
      v-for="(field, fieldIndex) of renderFormItem"
      :key="fieldIndex"
    >
      <BkFormItem
        :label="field?.title ?? field?.name"
        :property="field?.name"
        :description="field.description ?? ''"
        :label-width="field['ui:props']?.labelWidth ?? 150"
        :required="field['ui:rules']?.includes('required')"
      >
        <div
          class="flex items-center flex-wrap"
          :class="{
            'array-no-data': isArrayDataType(field) && !formData?.[field.name]?.length,
            'single-form-item': !isArrayDataType(field),
            'grid!': isBasicDataTypes(field.type),
            [`form-${[field.name]}`]: !!field.name
          }"
        >
          <!-- 如果是数据类型代表可以新增、删除 -->
          <template v-if="isArrayDataType(field)">
            <div
              v-for="(item, index) in getPropSchema(formData?.[field.name])"
              :key="`${field.name}-${index}`"
              class="flex items-center mb-8px custom-plugin-form-item"
            >
              <BkFormItem
                :property="`${field.name}[${index}].${displayKey}`"
                :rules="renderFormatArrayFormItem(field, item, displayKey)"
              >
                <BkInput
                  v-model="item[displayKey]"
                  :placeholder="renderPropertyName(field, displayKey)"
                  :maxlength="renderPropertyMaxLen(field, displayKey)"
                />
              </BkFormItem>
              <BkFormItem
                v-if="isMultipleRow(item)"
                :property="`${field.name}[${index}].${displayValue}`"
                :rules="renderFormatArrayFormItem(field, item, displayValue)"
              >
                <BkInput
                  v-model="item[displayValue]"
                  :placeholder="renderPropertyName(field, displayValue)"
                  :maxlength="renderPropertyMaxLen(field, displayValue)"
                />
              </BkFormItem>
              <i
                class="default-operate-btn mb-12px mr-10px apigateway-icon icon-ag-minus-circle-shape"
                @click="() => handleRemoveItem(field, index)"
              />
            </div>
            <i
              class="default-operate-btn mb-20px apigateway-icon icon-ag-plus-circle-shape"
              @click="handleAddItem(field)"
            />
          </template>
          <!-- 基本数据类型自定义组件 -->
          <template v-if="isBasicDataTypes(field.type)">
            <component
              :is="getComponent(field.type)"
              v-model="formData[field.name]"
              :disabled="disabled"
              :value="formData[field.name]"
              :property="field.name"
              :max="field.maxLength"
              :min="field.minLength ?? field['ui:component']?.min"
              :suffix="field['ui:component']?.unit"
              :required="field['ui:rules']?.includes('required')"
              :rules="renderFormatFormItem(field)"
              @input="(e: HTMLInputElement) => handleInput(field, e)"
            />
          </template>
        </div>
      </BkFormItem>
    </template>
  </div>
</template>

<script setup lang="ts">
import { isObject } from 'lodash-es';
import type { ComponentMap, ICorsFormData, IHeaderWriteFormData, ISchema } from '@/components/plugin-manage/schema-type';
import { getDuplicateKeys } from '@/utils/duplicateKeys';
import InputComponent from '@/components/plugin-manage/components/InputComponent.vue';
import InputNumberComponent from '@/components/plugin-manage/components/InputNumberComponent.vue';
import SwitchComponent from '@/components/plugin-manage/components/SwitchComponent.vue';

type ICustomFormData = IHeaderWriteFormData & ICorsFormData;

interface IProps {
  disabled?: boolean
  displayKey?: string
  displayValue?: string
  routeMode?: string
  schema?: ISchema
}

interface IEmits {
  (e: 'add'): [value: ICustomFormData]
  (e: 'remove'): {
    field: ICustomFormData
    index: number
  }
}

const formData = defineModel<ICorsFormData>('modelValue', {
  type: Object,
  required: true,
});

const {
  schema = {},
  disabled = false,
  displayKey = 'key',
  displayValue = 'value',
  routeMode = '',
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const renderFormItem = computed(() => {
  const isObjectProperties = isObject(schema?.properties);
  if (isObjectProperties) {
    // 为每个属性添加name字段，用于区分properties下的key
    return Object.entries(schema?.properties).map(([name, params]) => ({
      ...params as any,
      name,
    }));
  }
  return [];
});

const renderRouteCustomReg = computed(() => {
  const routeMap = {
    'bk-cors': () => {
      return { message: t('format_bk_cors_allow_origins_by_regex') };
    },
    'bk-header-rewrite': () => {
      return { message: t('format_bk_header_rewrite_by_regex') };
    },
  };
  return routeMap[routeMode]?.() ?? routeMap['bk-header-rewrite']();
});

const getComponent = (name?: string) => {
  const typeMap: ComponentMap = {
    string: () => InputComponent,
    number: () => InputNumberComponent,
    integer: () => InputNumberComponent,
    boolean: () => SwitchComponent,
  };
  return typeMap[name]?.() ?? typeMap['string']();
};

// 如果是基本数据类型的组件如string、boolean、number
const isBasicDataTypes = (type: string) => {
  return ['string', 'boolean', 'number', 'integer'].includes(type);
};

// 判断当前属性字段是否是数组类型
const isArrayDataType = (field: ISchema) => {
  return Array.isArray(formData?.[field.name]) || ['array'].includes(field.type);
};

// 获取不同表单插件的属性
const renderInputProperty = (row: ISchema, name: string) => {
  return row?.items?.properties?.[name] ?? row;
};

// 设置不同表单插件的title
const renderPropertyName = (field: ISchema, name: string) => {
  const curProperty = renderInputProperty(field, name);
  return curProperty?.title ?? curProperty?.name;
};

// 设置不同表单插件的最大长度
const renderPropertyMaxLen = (field: ISchema, name: string) => {
  const curProperty = renderInputProperty(field, name);
  return curProperty?.maxLength ?? curProperty?.items?.maxLength;
};

// 设置不同表单插件的pattern校验
const renderPropertyPattern = (field: ISchema) => {
  const curProperty = renderInputProperty(field, displayKey);
  return curProperty?.pattern ?? curProperty?.items?.pattern;
};

const renderFormatFormItem = (row: ISchema) => {
  const isRequired = row['ui:rules']?.includes('required') ?? false;
  const results = [
    {
      required: isRequired,
      message: t('请输入{inputValue}', { inputValue: renderPropertyName(row, row.name) }),
      validator: (value: string | number | boolean) => {
        // 非string类型的其他基本类型都会存在有默认值，所以无需校验
        const isString = typeof value === 'string';
        if (!isRequired || (isString && !!value?.trim()) || !isString) {
          return true;
        }
        return false;
      },
    },
  ];
  return results;
};

const renderFormatArrayFormItem = (
  row: ISchema,
  child: {
    key?: string
    value?: string
  },
  name: string,
) => {
  // 处理不同数组表单项的自定义校验提示语
  const { message } = renderRouteCustomReg.value;
  const results = [
    {
      required: true,
      message: `${t('请输入{inputValue}', { inputValue: renderPropertyName(row, name) })}`,
    },
    {
      message,
      trigger: 'change',
      validator: () => {
        if (![displayKey].includes(name)) return true;
        if ([displayKey].includes(name)) {
          const patternReg = new RegExp(renderPropertyPattern(row));
          return patternReg.test(child[displayKey]);
        }
        return true;
      },
    },
    {
      message: t('{inputKey}存在重复项', { inputKey: child[name] }),
      trigger: 'change',
      validator: () => {
        const duplicateList = getDuplicateKeys(formData.value?.[row.name], 'key');
        if ([displayKey].includes(name) && duplicateList?.includes(child[name])) {
          return false;
        }
        return true;
      },
    },
  ];
  return results;
};

// 获取当前层级的字段配置
const getPropSchema = (schemaData) => {
  return Array.isArray(schemaData) ? schemaData : [];
};

const isMultipleRow = (field) => {
  return Object.keys(field ?? {}).length > 1;
};

const handleInput = (field: ISchema, value: string | number) => {
  if (isArrayDataType(field)) {
    return;
  }
  if (typeof formData.value[field?.name] !== undefined) {
    formData.value[field?.name] = value;
  }
};
const handleAddItem = (field) => {
  if (!['array'].includes(field.type)) {
    return;
  }
  emit('add', field);
};

const handleRemoveItem = (field: ICustomFormData, index: number) => {
  if (!['array'].includes(field.type)) {
    return;
  }
  emit('remove', {
    field,
    index,
  });
};

const getFormData = () => {
  return formData.value;
};

defineExpose({ getFormData });
</script>

<style lang="scss" scoped>
.custom-plugin-form-item {
  gap: 16px;
  width: calc(100% - 16px);
  min-width: 300px;

  .bk-form-item {
    flex: 1;

    .bk-input {
      width: 100%;
    }
  }
}

.default-operate-btn {
  color: #979ba5;
  font-size: 16px;
  cursor: pointer;
}

.custom-plugin-form-wrapper {

  :deep(.bk-form-item) {
    margin-bottom: 12px;

    .single-form-item {

      &:has(.bk-form-item.is-error) ~ .bk-form-error {
        display: none !important;
      }

      &:has(+ .bk-form-error),
      &:has(~ .bk-form-error) {
        .bk-form-item {
          margin-bottom: 0;
        }
      }
    }

  }

  :deep(.array-no-data) {
    padding-top: 8px;

    &:has(+ .bk-form-error),
    &:has(~ .bk-form-error) {
      .bk-form-item {
        margin-bottom: 12px;
      }
    }

      ~ .bk-form-error,
    .bk-form-error {
      position: relative;
    }
  }

  :deep(.single-form-item) {
    ~ .bk-form-error,
    .bk-form-error {
      position: relative;
    }
  }
}

</style>
