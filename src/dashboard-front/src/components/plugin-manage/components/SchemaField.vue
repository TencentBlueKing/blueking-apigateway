<template>
  <Suspense>
    <template #default>
      <component
        :is="componentInfo?.component"
        ref="comRef"
        v-model="modelValue"
        v-bind="finalComponentProps"
        :schema="schema"
        :selected-schema="selectedSchema"
        @input="handleInput"
        @add="handleAddFormItem"
        @remove="handleRemoveFormItem"
      />
    </template>
  </Suspense>
</template>

<script setup lang="ts">
import { ComponentMap, type IHeaderWriteFormData, type ISchema, defaultComponentMap } from '@/components/plugin-manage/schema-type';

type ICustomFormData = IHeaderWriteFormData & Record<string, any>;

interface IProps {
  disabled?: boolean
  routeMode?: string
  schema?: ISchema
  componentMap?: Partial<ComponentMap>
  selectedSchema?: ISchema | null
}

interface IEmits {
  (e: 'input', value: string): void
  (e: 'add', value: ICustomFormData): void
  (e: 'remove', params: {
    field: ICustomFormData
    index: number
  }): void
}

const modelValue = defineModel('modelValue', {
  required: false,
  type: [Array, Object, String],
});

const {
  routeMode = '',
  disabled = false,
  schema = {},
  componentMap = {},
  selectedSchema = null,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const comRef = ref<InstanceType<typeof component> | null>(null);

const { t } = useI18n();

// 组件映射
const componentsMap = {
  ...defaultComponentMap,
  ...componentMap,
};

const componentInfo = computed(() => {
  const typeComponent = componentsMap[routeMode] ?? componentsMap[schema.type] ?? componentsMap.string;
  if (typeof typeComponent === 'function') {
    return typeComponent();
  }
  else {
    return {
      component: typeComponent,
      props: {},
    };
  }
});

const componentProps = computed(() => {
  const compProps: Record<string, any> = {
    disabled,
    placeholder: schema.title || `${t('请输入')}${schema.title ?? ''}`,
    routeMode,
  };

  if (['string'].includes(schema.type)) {
    compProps.type = schema.format || 'text';
    if (schema.pattern) compProps.pattern = schema.pattern;
    if (schema.maxLength) compProps.maxlength = schema.maxLength;
    if (schema.minLength) compProps.minlength = schema.minLength;
    // 从 schema.ui.props 合并额外属性，如 rows
    if (schema['ui:component']?.type) Object.assign(compProps, schema['ui:component']);
  }

  if (['number', 'integer'].includes(schema.type)) {
    if (schema?.minimum && typeof schema?.minimum === 'number') compProps.min = schema.minimum;
    if (schema?.maximum && typeof schema?.maximum === 'number') compProps.max = schema.maximum;
    if (schema?.step && typeof schema?.step === 'number') compProps.step = schema.step;
  }

  if (schema.enum && ['select', 'radio'].includes(schema.format)) {
    compProps.options = schema.enum.map((value: any) => ({
      label: value,
      value,
    }));
    if (schema.format === 'radio') {
      compProps.modelValue = modelValue.value;
      compProps['onUpdate:modelValue'] = (val: any) => {
        modelValue.value = val;
      };
    }
  }
  return compProps;
});

// 合并默认属性和动态属性
const finalComponentProps = computed(() => {
  // componentInfo.value.props 是来自映射表的默认属性
  // componentProps.value 是你根据 schema 计算出的动态属性
  const result = {
    ...componentInfo.value?.props,
    ...componentProps.value,
    'modelValue': modelValue.value,
    'onUpdate:modelValue': (value: Record<string, any> | string) => {
      modelValue.value = value;
    },
  };
  return result;
});

const handleInput = (val: string) => {
  emit('input', val);
};

const handleAddFormItem = (field) => {
  emit('add', field);
};

const handleRemoveFormItem = (field) => {
  emit('remove', field);
};

defineExpose({ comRef });
</script>
