<template>
  <div class="key-value-pairs">
    <BkForm
      v-for="(pair, index) in internalValue"
      :key="index"
      ref="forms"
      :model="pair"
      :rules="rules"
      v-bind="$attrs"
      class="key-value-form"
    >
      <div class="pair-row">
        <BkFormItem
          property="key"
          class="form-item"
        >
          <BkInput
            v-model="pair.key"
            :placeholder="t('键')"
            :maxlength="1024"
          />
        </BkFormItem>

        <BkFormItem
          property="value"
          class="form-item"
        >
          <BkInput
            v-model="pair.value"
            :placeholder="t('值')"
            :maxlength="1024"
          />
        </BkFormItem>

        <div class="action-buttons">
          <AgIcon
            class="icon-btn cursor-pointer"
            color="#979BA5"
            name="minus-circle-shape"
            size="18"
            @click="removePair(index)"
          />
          <AgIcon
            v-if="index === internalValue.length - 1"
            class="icon-btn cursor-pointer"
            color="#979BA5"
            name="plus-circle-shape"
            size="18"
            @click="addPair"
          />
        </div>
      </div>
    </BkForm>

    <div
      v-if="internalValue?.length === 0"
      class="add-initial"
    >
      <AgIcon
        class="icon-btn cursor-pointer"
        color="#979BA5"
        name="plus-circle-shape"
        size="18"
        @click="addPair"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Form } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';

interface KeyValuePair {
  key: string
  value: string
}

interface IProps { modelValue?: KeyValuePair[] }

const { modelValue = [] } = defineProps<IProps>();

const emit = defineEmits<{ 'update:modelValue': [KeyValuePair[]] }>();

const { t } = useI18n();

const formRefs = useTemplateRef<InstanceType<typeof Form>[]>('forms');

const internalValue = ref<KeyValuePair[]>([]);

watch(
  () => modelValue,
  (newVal) => {
    if (JSON.stringify(newVal) !== JSON.stringify(internalValue.value)) {
      internalValue.value = newVal.length > 0 ? cloneDeep(newVal) : [];
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(internalValue, (newVal) => {
  emit('update:modelValue', newVal);
}, { deep: true });

const rules = {
  key: [
    {
      required: true,
      message: t('请输入键名'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^[\w-]+$/.test(value),
      message: t('允许输入：字母、数字、下划线_、连字符-'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => internalValue.value.filter(item => item.key === value).length <= 1,
      message: t('键名已存在'),
      trigger: 'blur',
    },
  ],
  value: [
    {
      required: true,
      message: t('请输入键值'),
      trigger: 'blur',
    },
  ],
};

const addPair = () => {
  internalValue.value.push({
    key: '',
    value: '',
  });
};

const removePair = (index: number) => {
  internalValue.value.splice(index, 1);
  nextTick(() => {
    validate();
  });
};

const validate = async (): Promise<boolean> => {
  if (!formRefs.value) return true;

  try {
    await Promise.all(formRefs.value!.map(formRef => formRef.validate()));
    return true;
  }
  catch (error) {
    console.error(error);
    return false;
  }
};

const getValue = (): Record<string, string> => {
  const result: Record<string, string> = {};
  internalValue.value.forEach((pair) => {
    if (pair.key && pair.value) {
      result[pair.key] = pair.value;
    }
  });
  return result;
};

defineExpose({
  validate,
  getValue,
});

</script>

<style scoped lang="scss">
.key-value-pairs {
  width: 100%;
}

.key-value-form {
  width: 100%;
}

.pair-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.form-item {
  flex: 1;
  margin-bottom: 0;
}

.form-item :deep(.bk-form-item__content) {
  margin-left: 0 !important;
}

.action-buttons {
  display: flex;
  gap: 8px;
  min-width: 80px;
  padding-top: 4px;
}

</style>
