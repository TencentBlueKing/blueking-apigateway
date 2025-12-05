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
  <div
    class="relative schema-field"
    :style="schema?.['ui:group']?.style"
  >
    <!-- 标题区域 -->
    <div
      v-if="schema?.['ui:group']?.showTitle"
      :class="`schema-title ${schema?.['ui:group']?.type}`"
    >
      {{ schema.title }}
    </div>
    <div
      v-for="(item, index) in getRenderData"
      :key="`special-${index}`"
      class="grid gap-24px relative schema-rate-limit-item"
      :style="{
        ...layout,
        ...schema?.items?.['ui:group']?.style ?? {}
      }"
      :class="[{
        'mb-24px': isArrayType
      }]"
    >
      <template
        v-for="(propSchema, prop) in getPropSchema"
        :key="prop"
      >
        <component
          :is="getComponent(propSchema['ui:component']?.name)"
          v-model="item[prop]"
          :disabled="disabled"
          :label="propSchema.title"
          :value="item['default']?.[prop] ?? item[prop]"
          :datasource="propSchema['ui:component']?.datasource"
          :min="propSchema['ui:component']?.min"
          :max="propSchema['ui:component']?.max"
          :label-width="propSchema['ui:props']?.labelWidth"
          :required="propSchema['ui:rules']?.includes('required')"
          :property="`${isArrayType ? 'specials' : 'default'}[${index}].${prop}`"
          :rules="renderFormatFormItem(item, propSchema, prop)"
          @input="(e) => handleInput(index, prop, e)"
        />
      </template>
      <template v-if="['array'].includes(schema.type)">
        <AgIcon
          name="delet"
          class="flex color-#979ba5 cursor-pointer delete-icon"
          :disabled="disabled"
          @click.stop="handleRemove(index)"
        />
      </template>
    </div>
    <span
      v-if="!disabled && ['array'].includes(schema.type)"
      class="color-#3a84ff cursor-pointer text-14px"
      @click.stop=" handleAdd"
    >
      <i class="mr-5px apigateway-icon icon-ag-plus-circle-shape" />
      <span>{{ t('添加') }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { getDuplicateKeys } from '@/utils/duplicateKeys';
import type { IRateLimitFormData, ISchema } from '@/components/plugin-manage/schema-type';
import InputComponent from '@/components/plugin-manage/components/InputComponent.vue';
import InputNumberComponent from '@/components/plugin-manage/components/InputNumberComponent.vue';
import SelectComponent from '@/components/plugin-manage/components/SelectComponent.vue';

interface IProps {
  schema?: ISchema
  layout?: Record<string, string>
  disabled?: boolean
}

interface IEmits {
  (e: 'update:modelValue', value: string | number): void
  (e: 'add'): void
  (e: 'remove', index: number): void
}

const modeField = defineModel<IRateLimitFormData>('modelValue');

const {
  schema = {},
  layout = {},
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const isArrayType = computed(() => schema?.type === 'array');

const getRenderData = computed(() => {
  if (isArrayType.value) {
    return [...modeField.value?.rates?.specials ?? []];
  }
  return modeField.value;
});

// 获取当前层级的字段配置
const getPropSchema = computed(() => {
  // 数组类型：字段配置在 schema.items.properties；对象类型：在 schema.properties
  return isArrayType.value ? schema.items?.properties ?? {} : schema?.properties ?? {};
});

const getComponent = (name?: string) => {
  switch (name) {
    case 'bfInput': return InputNumberComponent;
    case 'select': return SelectComponent;
    default: return InputComponent;
  }
};

const renderFormatFormItem = (
  row: ISchema,
  child: {
    'default'?: number
    'type': string
    'title': string
    'pattern'?: string
    'ui:rules': string[]
    'ui:component'?: {
      name: string
      min: number
    }
    'ui:props'?: { labelWidth?: number }
  },
  name: string,
) => {
  const results = [
    {
      required: true,
      message: `${t('请输入{inputValue}', { inputValue: child.title })}`,
      trigger: 'change',
      validator: () => {
        if (isArrayType.value) {
          return !!row[name] && String(row[name]).trim().length > 0;
        }
        else {
          return child['default'] && String(child['default']).trim().length > 0;
        }
        return true;
      },
    },
    {
      required: true,
      message: `${t('请输入{inputValue}', { inputValue: child.title })}`,
      trigger: 'change',
      validator: () => {
        if (isArrayType.value) {
          return !!row[name] && String(row[name]).trim().length > 0;
        }
        else {
          return child['default'] && String(child['default']).trim().length > 0;
        }
        return true;
      },
    },
    {
      message: t('format_bk_rate_limit_bk_app_code'),
      trigger: 'change',
      validator: () => {
        if (!['bk_app_code'].includes(name)) return true;
        if (['bk_app_code'].includes(name) && !/^[a-z][a-z0-9_-]{0,31}$/.test(row[name])) {
          return false;
        }
        return true;
      },
    },
    {
      message: t('{inputKey}存在重复项', { inputKey: row[name] }),
      trigger: 'change',
      validator: () => {
        if (['bk_app_code'].includes(name)) {
          const allItems = modeField.value.rates?.specials ?? [];
          const duplicateList = getDuplicateKeys(allItems, 'bk_app_code');
          const currentValue = row[name];
          const emptyValues = new Set([undefined, null, '']);
          if (emptyValues.has(currentValue)) return true;
          return !duplicateList.includes(currentValue);
        }
        return true;
      },
    },
  ];
  return results;
};

const handleInput = (index: number | string, prop: string, value: string | number) => {
  if (isArrayType.value) {
    // 数组场景：更新 specials 对应项
    const numIndex = typeof index === 'string' ? parseInt(index, 10) : index;
    modeField.value = {
      ...modeField.value,
      rates: {
        ...modeField.value.rates,
        specials: modeField.value.rates.specials.map((item, i) =>
          i === numIndex
            ? {
              ...item,
              [prop]: value,
            }
            : item,
        ),
      },
    };
  }
  else {
    modeField.value.rates.default = Object.assign(modeField.value.rates.default, { [prop]: value });
  }
};

const handleAdd = () => {
  const newItem = Object.fromEntries(
    Object.entries(schema.items.properties).map(([prop, propSchema]) => [
      prop,
      propSchema.default ?? (propSchema.type === 'string' ? '' : 0),
    ]),
  );
  const newSpecials = [...modeField.value.rates.specials, newItem];
  modeField.value = {
    ...modeField.value,
    rates: {
      ...modeField.value.rates,
      specials: newSpecials,
    },
  };
  emit('add', newItem);
};

const handleRemove = (index: number) => {
  const newSpecials = modeField.value.rates.specials.filter((_, i) => i !== index);
  modeField.value.rates.specials = [...newSpecials];
  emit('remove', index);
};
</script>

<style langs="scss" scoped>
.schema-title {
  font-size: 14px;
  font-weight: 600;
  color: #63656e;
  display: flex;
  height: 50px;
  align-items: center;
  padding: 0 24px;
  margin: 0 -24px 8px -24px;
}

:deep(.bk-form-item) {
  margin-top: unset !important;
  margin-bottom: unset !important;

  .bk-form-error {
    position: inherit;
  }
}

.delete-icon {
  position: absolute;
  right: 8px;
  top: 18px !important;

  &:hover {
    color: #3a84ff;
  }
}
</style>
