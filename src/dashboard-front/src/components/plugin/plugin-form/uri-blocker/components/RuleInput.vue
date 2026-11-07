<template>
  <div>
    <BkForm
      v-for="(blockRule, index) in localBlockRules"
      :key="index"
      ref="formRefs"
      :model="blockRule"
      class="form-element"
      :rules="rules"
      v-bind="$attrs"
    >
      <BkFormItem
        :class="{ 'mb-0px': localBlockRules?.length > 1 && index === localBlockRules.length - 1 }"
        class="form-item w-640px"
        label=""
        property="key"
      >
        <div class="multi-line-wrapper">
          <section class="multi-line-item has-suffix">
            <BkInput
              v-model="blockRule.key"
              clearable
            />
            <div class="suffix-actions">
              <AgIcon
                v-if="localBlockRules.length > 1"
                class="icon-btn cursor-pointer"
                color="#979BA5"
                name="minus-circle-shape"
                size="18"
                @click="() => handleRemoveItem(index)"
              />
              <AgIcon
                class="icon-btn cursor-pointer"
                color="#979BA5"
                name="plus-circle-shape"
                size="18"
                @click="handleAddItem"
              />
            </div>
          </section>
        </div>
      </BkFormItem>
    </BkForm>
    <AgIcon
      v-if="!localBlockRules?.length"
      class="icon-btn"
      color="#979BA5"
      name="plus-circle-shape"
      size="18"
      @click="handleAddItem"
    />
  </div>
</template>

<script lang="ts" setup>
interface IProps { blockRules?: string[] }

const { blockRules = [] } = defineProps<IProps>();

const { t } = useI18n();

const formRefs = ref();

const localBlockRules = ref<{ key: string }[]>([]);

const rules = {
  key: [
    {
      validator: () => !!localBlockRules.value?.filter((item: { key: string }) => !!item.key).length,
      message: t('需要至少填写一个规则'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length >= 1 && value.length <= 4096,
      message: t('长度需要在 1 到 4096 个字符之间'),
      trigger: 'blur',
    },
    {
      validator: (val: string) =>
        !val || localBlockRules.value.filter((item: { key: string }) => item.key === val).length <= 1,
      message: t('规则已存在'),
      trigger: 'blur',
    },
  ],
};

watch(() => blockRules, () => {
  localBlockRules.value = blockRules.map((item: string) => ({ key: item }));
}, {
  deep: true,
  immediate: true,
});

const handleAddItem = () => {
  localBlockRules.value.push({ key: '' });
};

const handleRemoveItem = (index: number) => {
  localBlockRules.value.splice(index, 1);
};

const getValue = () =>
  Promise.all(formRefs.value.map((formRef: any) => formRef.validate()))
    .then(() => (localBlockRules.value?.filter((item: { key: string }) => !!item.key) || []).map(({ key }) => key));

defineExpose({ getValue });

</script>

<style lang="scss" scoped>

.multi-line-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .multi-line-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.has-suffix {
  position: relative;

  .suffix-actions {
    position: absolute;
    right: -12px;
    display: flex;
    align-items: center;
    transform: translateX(100%);
    gap: 12px;
  }
}

.form-item {

  :deep(.bk-form-error) {
    position: relative;
  }
}

</style>
