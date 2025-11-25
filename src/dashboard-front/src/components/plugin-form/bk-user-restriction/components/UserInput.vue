<template>
  <div>
    <BkForm
      v-for="(user, index) in localUsers"
      :key="index"
      ref="forms"
      :model="user"
      class="form-element"
      v-bind="$attrs"
      :rules="rules"
    >
      <BkFormItem
        :class="{ 'mb-0px': localUsers?.length > 1 && index === localUsers.length - 1 }"
        class="form-item w-640px"
        label=""
        property="key"
      >
        <div class="multi-line-wrapper">
          <section class="multi-line-item has-suffix">
            <BkInput
              v-model="user.key"
              clearable
            />
            <div class="suffix-actions">
              <AgIcon
                v-if="localUsers.length > 1"
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
      v-if="!localUsers?.length"
      class="icon-btn"
      color="#979BA5"
      name="plus-circle-shape"
      size="18"
      @click="handleAddItem"
    />
  </div>
</template>

<script lang="ts" setup>
import { Form } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';

interface IProps { users?: { key: string }[] }

const { users = [] } = defineProps<IProps>();

const { t } = useI18n();

const localUsers = ref<{ key: string }[]>([]);

const formRefs = useTemplateRef<InstanceType<typeof Form>[]>('forms');

const rules = {
  key: [
    {
      validator: (val: string) => localUsers.value.filter(item => item.key === val).length <= 1,
      message: t('用户已存在'),
      trigger: 'blur',
    },
  ],
};

watch(() => users, () => {
  localUsers.value = cloneDeep(users);
}, {
  deep: true,
  immediate: true,
});

const handleAddItem = () => {
  localUsers.value.push({ key: '' });
};

const handleRemoveItem = (index: number) => {
  localUsers.value.splice(index, 1);
};

const validate = async () => {
  return await Promise.all(formRefs.value!.map(formRef => formRef.validate()));
};

const getValue = async () => {
  return Promise.resolve(localUsers.value?.filter(item => !!item.key) || []);
};

defineExpose({
  validate,
  getValue,
});

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
