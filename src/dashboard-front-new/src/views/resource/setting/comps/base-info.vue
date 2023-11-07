
<template>
  <bk-form ref="formRef" :model="formData" :rules="rules">
    <bk-form-item
      :label="t('名称')"
      property="name"
      required
    >
      <bk-input
        v-model="formData.name"
        class="w700"
        :placeholder="t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符')"
        clearable
      />
    </bk-form-item>
    <bk-form-item
      :label="t('描述')"
    >
      <bk-input
        v-model="formData.description"
        :placeholder="t('请输入')"
        clearable
        class="w700"
      />
    </bk-form-item>
    <bk-form-item
      :label="t('标签')"
    >
      <bk-select
        class="w700"
        v-model="formData.label_ids"
        :input-search="false"
        multiple
        filterable
        multiple-mode="tag">
        <bk-option v-for="item in labelsData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item
      :label="t('认证方式')"
    >
      <bk-checkbox v-model="formData.auth_config.app_verified_required">
        {{ t('蓝鲸应用认证') }}
      </bk-checkbox>
      <bk-checkbox class="ml40" v-model="formData.auth_config.auth_verified_required">
        {{ t('用户认证') }}
      </bk-checkbox>
    </bk-form-item>
    <bk-form-item
      :label="t('检验应用权限')"
      v-if="formData.auth_config.app_verified_required"
    >
      <bk-switcher
        v-model="formData.auth_config.resource_perm_required"
        theme="primary"
      />
    </bk-form-item>
    <bk-form-item
      :label="t('是否公开')"
      property="is_public"
    >
      <div class="flex-row align-items-center public-switch">
        <bk-switcher
          v-model="formData.is_public"
          theme="primary"
        />
        <bk-checkbox
          v-if="formData.is_public" class="ml40"
          v-model="formData.allow_apply_permission">
          {{ t('允许申请权限') }}
        </bk-checkbox>
      </div>
    </bk-form-item>
  </bk-form>
</template>
<script setup lang="ts">
import { ref, defineExpose, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { getGatewayLabels } from '@/http';
import { useCommon } from '@/store';

const props = defineProps({
  detail: {
    type: Object,
    default: {},
  },
});

const formRef = ref(null);
const { t } = useI18n();
const common = useCommon();
const formData = ref({
  name: '',
  description: '',
  label_ids: [],
  auth_config: {
    auth_verified_required: false,
    app_verified_required: false,
    resource_perm_required: false,
  },
  is_public: false,
  allow_apply_permission: false,
});

console.log('formData1', props.detail);
const labelsData = ref([]);

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/;
        return reg.test(value);
      },
      message: '由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符',
      trigger: 'blur',
    },
  ],
};

watch(
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { name, description, auth_config, is_public, allow_apply_permission, labels } = val;
      const label_ids = labels.map((e: {id: number, name: string}) => e.id);
      formData.value = { name, description, auth_config, is_public, allow_apply_permission, label_ids };
      console.log('formData', formData.value);
    }
  },
  { immediate: true },
);

watch(
  () => formData.value.is_public,
  (val: boolean) => {
    // 必须要公开 才能允许申请权限
    formData.value.allow_apply_permission = val;
  },
);

const init = async () => {
  const res = await getGatewayLabels(common.apigwId);
  labelsData.value = res;
};

const validate = async () => {
  await formRef.value?.validate();
};

init();
defineExpose({
  formData,
  validate,
});
</script>
<style lang="scss" scoped>
.public-switch{
    height: 32px;
}
.w700{
  max-width: 700px;
  width: 70%;
}
</style>
