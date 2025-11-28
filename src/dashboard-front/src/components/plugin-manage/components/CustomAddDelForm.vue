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
            'pt-8px': isArrayDataType(field) && !formData?.[field.name]?.length,
            'grid!': isBasicDataTypes(field.type)
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
                  :maxlength="renderPropertyMaxLen(field,displayValue)"
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
              :rules="renderFormatFormItem(field, field.name)"
              @input="(e) => handleInput(field, e)"
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
  routeMode: string
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

const isArrayDataType = (field: ISchema) => {
  return Array.isArray(formData?.[field.name]) || ['array'].includes(field.type);
};

const renderInputProperty = (row: ISchema, name: string) => {
  return row?.items?.properties?.[name] ?? row;
};

const renderPropertyName = (field: ISchema) => {
  const curProperty = renderInputProperty(field, displayKey);
  return curProperty?.title ?? curProperty?.name;
};

const renderPropertyMaxLen = (field: ISchema) => {
  const curProperty = renderInputProperty(field, displayKey);
  return curProperty?.maxLength ?? curProperty?.items?.maxlength;
};

const renderFormatFormItem = (
  row: ISchema,
  name: string,
) => {
  const isRequired = row['ui:rules']?.includes('required');
  const results = [
    {
      required: isRequired,
      message: `${t('请输入{inputValue}', { inputValue: `${renderPropertyName(row, name)}` })}`,
    },
    {
      message: t('格式错误, 需匹配正则 \"^[\\w-]+$\"'),
      trigger: 'change',
      validator: () => {
        // console.log(row, 5);
        // if (['key'].includes(name)) {
        //   return /^[\w-]+$/.test(row[displayKey]);
        // }
        return true;
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
  const results = [
    {
      required: true,
      message: `${t('请输入{inputValue}', { inputValue: `${renderPropertyName(row, name)}` })}`,
    },
    {
      message: t('格式错误, 需匹配正则 \"^[\\w-]+$\"'),
      trigger: 'change',
      validator: () => {
        if (['key'].includes(name)) {
          return /^[\w-]+$/.test(child[displayKey]);
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

  }
  else {
    if (typeof formData.value[field?.name] !== undefined) {
      formData.value[field?.name] = value;
    }
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

// 为两个区域添加间距
:deep(.bk-form-item) {
  margin-bottom: 12px;
}
</style>
