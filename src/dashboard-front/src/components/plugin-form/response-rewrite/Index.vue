<template>
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
  >
    <BkFormItem
      :label="t('状态码')"
      property="status_code"
      :description="t('修改上游返回状态码，默认保留原始响应代码。')"
      required
    >
      <BkInput
        v-model="formData.status_code"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('响应体')"
      property="body"
      :description="t('修改上游返回的 body 内容，如果设置了新内容，header 里面的 content-length 字段也会被去掉。')"
    >
      <BkInput
        v-model="formData.body"
      />
    </BkFormItem>
    <BkFormItem
      label="body_base64"
      property="body_base64"
      :description="t('当设置时，在写给客户端之前，在body中传递的主体将被解码，这在一些图像和 Protobuffer 场景中使用。注意，这个字段只允许对插件配置中传递的主体进行解码，并不对上游响应进行解码。')"
    >
      <BkSwitcher
        v-model="formData.body_base64"
        theme="primary"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('添加请求头')"
      property="headers.add"
      :description="t('添加新的请求头')"
    >
      <KeyValuePairs
        ref="addRef"
        v-model="formData.headers.add"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('设置请求头')"
      property="headers.set"
      :description="t('设置请求头')"
    >
      <KeyValuePairs
        ref="setRef"
        v-model="formData.headers.set"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('删除请求头')"
      property="headers.remove"
      :description="t('删除请求头')"
    >
      <removeHeaders
        ref="removeRef"
        v-model="formData.headers.remove"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('表达式列表')"
      property="vars"
      :description="
        t('vars 是一个表达式列表，只有满足条件的请求和响应才会修改 body 和 header 信息，来自 lua-resty-expr。如果 vars 字段为空，那么所有的重写动作都会被无条件的执行。')"
    >
      <BkInput
        v-model="formData.vars"
        :placeholder="t('请输入')"
        type="textarea"
        :rows="10"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import KeyValuePairs from '@/components/plugin-form/api-breaker/components/KeyValuePairs.vue';
import removeHeaders from '@/components/plugin-form/api-breaker/components/removeHeaders.vue';

interface KeyValuePair {
  key: string
  value: string
}

interface IFormData {
  status_code: string
  body: string
  body_base64: boolean
  headers: {
    add: KeyValuePair[]
    set: KeyValuePair[]
    remove: { key: string }[]
  }
  vars: string
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');
const addRef = useTemplateRef('addRef');
const setRef = useTemplateRef('setRef');
const removeRef = useTemplateRef('removeRef');

const getDefaultData = () => ({
  status_code: '',
  body: '',
  body_base64: false,
  headers: {
    add: [],
    set: [],
    remove: [],
  },
  vars: '',
});

const formData = ref<IFormData>(getDefaultData());

const rules = {};

watch(() => data, () => {
  if (data?.headers?.add) {
    formData.value = cloneDeep(data);
  }
  else {
    formData.value = getDefaultData();
  }
}, {
  immediate: true,
  deep: true,
});

const validate = () => formRef.value?.validate();

const getValue = () => validate()?.then(() => formData.value);

defineExpose({
  validate,
  getValue,
});

</script>

<style lang="scss" scoped>
</style>
