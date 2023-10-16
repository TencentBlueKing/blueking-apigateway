
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
      v-model="formData.label_ids"
    >
      <bk-select
        class="w700"
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
import { ref, defineExpose } from 'vue';
import { useI18n } from 'vue-i18n';
import { getGatewayLabels } from '@/http';
import { useCommon } from '@/store';

const { t } = useI18n();
const common = useCommon();
const formData = ref({
  name: '',
  description: '',
  label_ids: [],
  auth_config: {},
  is_public: false,
});

const labelsData = ref([]);

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length >= 3,
      message: t('不能小于3个字符'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length <= 30,
      message: t('不能多于30个字符'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-z][a-z0-9-]*$/;
        return reg.test(value);
      },
      message: '由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符',
      trigger: 'blur',
    },
  ],
};

const init = async () => {
  const res = await getGatewayLabels(common.apigwId);
  console.log('res', res);
  labelsData.value = res;
};
init();

defineExpose({
  formData,
});
</script>
<style lang="scss" scoped>
.public-switch{
    height: 32px;
}
.w700{
    width: 700px;
}
</style>
