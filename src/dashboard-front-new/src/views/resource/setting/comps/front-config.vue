
<template>
  <bk-form ref="frontRef" :model="frontConfigData" :rules="rules" class="front-config-container">
    <bk-form-item
      :label="t('请求方法')"
      property="method"
      required>
      <bk-select
        :input-search="false"
        :clearable="false"
        v-model="frontConfigData.method"
        @change="clearValidate"
        class="w700">
        <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item
      :label="t('请求路径')"
      property="path"
      required>
      <div class="flex-row aligin-items-center">
        <bk-input
          v-model="frontConfigData.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          @input="clearValidate"
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
import mitt from '@/common/event-bus';

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
const cloneTips = ref(t('请求方法+请求路径在网关下唯一，请至少调整其中一项'));
const common = useCommon();
const frontConfigData = ref({
  path: 'GET',
  method: '',
  match_subpath: false,
});

const cloneData = ref({
  path: '',
  method: '',
});
const methodData = ref(common.methodList);

const rules = ref<any>({
  method: [
    {
      validator: (value: string) => {
        if (!value) return true;
        return value !== cloneData.value.method || frontConfigData.value.path !== cloneData.value.path;
      },
      message: cloneTips.value,
      trigger: 'blur',
    },
  ],
  path: [
    {
      validator: (value: string) => {
        console.log('value', value);
        if (!value) return true;
        return value !== cloneData.value.path || frontConfigData.value.method !== cloneData.value.method;
      },
      message: cloneTips.value,
      trigger: 'blur',
    },
    {
      required: true,
      message: t('请求路径不能为空'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^\/[\w{}/.-]*$/.test(value),
      message: t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
      trigger: 'blur',
    },
  ],
});

watch(
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { path, method, match_subpath } = val;
      frontConfigData.value = { path, method, match_subpath };
      if (props.isClone) {
        cloneData.value = { path, method };
        setTimeout(() => {
          validate();
        }, 500);
      }
    }
  },
  { immediate: true },
);

watch(
  () => frontConfigData.value,
  (val: any) => {
    mitt.emit('front-config', val);
  },
  { deep: true },
);

const validate = async () => {
  await frontRef.value?.validate();
};

// 清除表单验证
const clearValidate = () => {
  frontRef.value?.clearValidate();
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

