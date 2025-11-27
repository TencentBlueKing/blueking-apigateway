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
  <div class="header-rewrite-wrapper">
    <template
      v-for="(field, fieldIndex) of renderFormItem"
      :key="fieldIndex"
    >
      <BkFormItem
        :label="field.title"
        :property="field.name"
        :description="field.description ?? ''"
      >
        <div
          class="flex items-center flex-wrap"
          :class="{ 'pt-8px': !formData?.[field.name]?.length }"
        >
          <div
            v-for="(item, index) in formData[field.name]"
            :key="`${field.name}-${index}`"
            :class="`flex items-center mb-8px custom-plugin-form-item ${field.name}`"
          >
            <BkFormItem
              :property="`${field.name}[${index}].${displayKey}`"
              :rules="renderFormatFormItem(field, item, displayKey)"
            >
              <BkInput
                v-model="item[displayKey]"
                :placeholder="renderInputProperty(field, displayKey)?.title"
                :maxlength="renderInputProperty(field, displayKey)?.maxLength"
              />
            </BkFormItem>
            <BkFormItem
              v-if="!['remove'].includes(field.name)"
              :property="`${field.name}[${index}].${displayValue}`"
              :rules="renderFormatFormItem(field, item, displayValue)"
            >
              <BkInput
                v-model="item[displayValue]"
                :placeholder="renderInputProperty(field, displayValue)?.title"
                :maxlength="renderInputProperty(field,displayValue)?.maxLength"
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
        </div>
      </BkFormItem>

      <!-- <BkFormItem
        v-if="['remove'].includes(field.name)"
        :label="field.title"
        :property="field.name"
        :description="field.description ?? ''"
        >
        <div
        class="flex items-center flex-wrap"
        :class="[
        {
        'pt-8px': !formData?.[field.name]?.length
        },
        ]"
        >
        <div
        v-for="(item, index) in formData[field.name]"
        :key="`remove-${index}`"
        class="flex items-center mb-8px custom-plugin-form-item remove"
        >
        <BkFormItem
        :property="`remove[${index}].key`"
        :rules="renderFormatFormItem(field, item, displayKey)"
        >
        <BkInput
        v-model="item.key"
        :placeholder="renderInputProperty(field, displayKey)?.title"
        :maxlength="renderInputProperty(field, displayKey)?.maxLength"
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
        </div>
        </BkFormItem> -->
    </template>
  </div>
</template>

<script setup lang="ts">
import { isObject } from 'lodash-es';
import type { IHeaderWriteFormData, ISchema } from '@/components/plugin-manage/schema-type';

interface IProps {
  disabled?: boolean
  displayKey?: string
  displayValue?: string
  routeMode: string
  schema?: ISchema
}

interface IEmits {
  (e: 'add'): [value: IHeaderWriteFormData]
  (e: 'remove'): {
    field: IHeaderWriteFormData
    index: number
  }
}

const formData = defineModel<IHeaderWriteFormData>('modelValue', {
  type: Object,
  default: () => {
    return {
      set: [],
      remove: [],
    };
  },
});

const {
  schema = {},
  displayKey = 'key',
  displayValue = 'value',
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const renderFormItem = computed(() => {
  const isObjectProperties = isObject(schema?.properties);
  if (isObjectProperties) {
    // 为每个属性添加name字段，用于区分set和remove
    return Object.entries(schema?.properties).map(([name, params]) => ({
      ...params as any,
      name,
    }));
  }
  return [];
});

// 校验是否有重复的key
const getDuplicateKeys = (arr: Array<{
  key?: string
  value?: string
}>) => {
  const keyMap = new Map();
  const duplicates = new Set();
  for (const item of arr) {
    const { key } = item;
    const count = (keyMap.get(key) || 0) + 1;
    keyMap.set(key, count);
    if (count > 1) {
      duplicates.add(key);
    }
  }
  return Array.from(duplicates);
};

const renderInputProperty = (row: ISchema, name: string) => {
  return row?.items?.properties?.[name];
};

const renderFormatFormItem = (row: ISchema, child: {
  key?: string
  value?: string
}, name: string) => {
  const results = [
    {
      required: true,
      message: `${t('请输入{inputValue}', { inputValue: `${renderInputProperty(row, name)?.title}` })}`,
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
        const duplicateList = getDuplicateKeys(formData.value?.[row.name]);
        if ([displayKey].includes(name) && duplicateList?.includes(child[name])) {
          return false;
        }
        return true;
      },
    },
  ];
  return results;
};

const handleAddItem = (field) => {
  emit('add', field);
};

const handleRemoveItem = (field: IHeaderWriteFormData, index: number) => {
  emit('remove', {
    field,
    index,
  });
};
</script>

<style lang="scss" scoped>
.custom-plugin-form-item {

  .bk-input {
    width: 332px;
    margin-right: 12px;
  }

  &.remove {

    .bk-input {
      width: 676px;
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
