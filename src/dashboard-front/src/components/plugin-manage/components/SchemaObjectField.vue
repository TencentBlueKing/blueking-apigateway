<template>
  <div class="schema-object-field">
    <template
      v-for="(item, index) in renderFormItem"
      :key="index"
    >
      <BkFormItem
        v-if="renderShowForm(item)"
        :label="item?.title"
        :required="renderRequired"
        :property="renderAllKeys?.[0]"
        :description="item.description ?? ''"
      >
        <template
          v-for="(field, fieldIndex) in renderFields(item)"
          :key="fieldIndex"
        >
          <SchemaFields
            ref="schemaFieldRef"
            v-model="modelField[fieldIndex]"
            :schema="field"
            :disabled="disabled"
          />
        </template>
      </BkFormItem>
    </template>
  </div>
</template>

<script setup lang="ts">
import { isEqual, isObject } from 'lodash-es';
import { type ISchema } from '@/components/plugin-manage/schema-type';
import SchemaFields from './SchemaField.vue';

interface IProps {
  disabled?: boolean
  routeMode: string
  schema?: ISchema
  selectedSchema?: ISchema | null
}

const modelField = defineModel('modelValue', {
  type: [Object, String],
  default: () => {
  },
});

const {
  schema = {},
  selectedSchema = null,
} = defineProps<IProps>();

const schemaFieldRef = ref<InstanceType<typeof SchemaFields> | null>(null);

const schemaOption = computed(() => {
  if (!selectedSchema) {
    if (Array.isArray(schema?.oneOf)) {
      return schema?.oneOf?.[0];
    }
    return schema ?? {};
  }
  return selectedSchema;
});

const renderAllKeys = computed(() => {
  const allKeys = Object.keys(schemaOption.value?.properties ?? {});
  return allKeys;
});

const renderRequired = computed(() => {
  return renderAllKeys.value.some(key => schemaOption.value?.required?.includes(key));
});

const renderFormItem = computed(() => {
  const isOneOf = Array.isArray(schema?.oneOf);
  const isObjectProperties = isObject(schemaOption.value?.properties);
  if (isOneOf) {
    return schema?.oneOf;
  }
  if (isObjectProperties) {
    return Object.values(schemaOption.value?.properties);
  }
  return [];
});

const renderFields = (row) => {
  if (isObject(row?.items?.properties)) {
    return Object.values(row?.items?.properties);
  }
  return row?.properties;
};

const renderShowForm = (row) => {
  return !selectedSchema || isEqual(schemaOption.value, row);
};

defineExpose({ schemaFieldRef });
</script>
