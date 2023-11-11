
<template>
  <bk-form ref="frontRef" :model="frontConfigData" :rules="rules" class="front-config-container">
    <bk-form-item
      :label="t('请求方法')"
      property="method"
      required>
      <bk-select
        :input-search="false"
        v-model="frontConfigData.method"
        class="w700">
        <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item
      :label="t('请求路径')"
      property="path"
      required
    >
      <div class="flex-row aligin-items-center">
        <bk-input
          v-model="frontConfigData.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w700"
        />
        <bk-checkbox class="ml40" v-model="frontConfigData.match_subpath">
          {{ t('匹配所有路径') }}
        </bk-checkbox>
      </div>
    </bk-form-item>
  </bk-form>
</template>
<script setup lang="ts">
import { ref, defineExpose, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '../../../../store';

const props = defineProps({
  detail: {
    type: Object,
    default: {},
  },
  isClone: {
    type: Boolean,
    default: false,
  },
});

const frontRef = ref(null);
const { t } = useI18n();
const common = useCommon();
const frontConfigData = ref({
  path: '',
  method: '',
  match_subpath: false,
});
const methodData = ref(common.methodList);

const rules = {
  path: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^\/[\w{}/.-]*$/.test(value),
      message: t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { path, method, match_subpath } = val;
      frontConfigData.value = { path, method, match_subpath };
      console.log('formData', frontConfigData.value);
    }
  },
  { immediate: true },
);

const validate = async () => {
  await frontRef.value?.validate();
};

defineExpose({
  frontConfigData,
  validate,
});
</script>
  <style lang="scss" scoped>
  .front-config-container{
    .public-switch{
        height: 32px;
    }
    .w700{
      max-width: 700px;
      width: 70%;
    }
  }
  </style>

