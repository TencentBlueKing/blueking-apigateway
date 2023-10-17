
<template>
  <bk-form ref="frontRef" :model="frontConfigData" :rules="rules" class="front-config-container">
    <bk-form-item
      :label="t('请求方法')"
      v-model="frontConfigData.method"
      property="method"
      required
    >
      <bk-select
        :input-search="false"
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
import { ref, defineExpose } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '../../../store';

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

defineExpose({
  frontConfigData,
});
</script>
  <style lang="scss" scoped>
  .front-config-container{
    .public-switch{
        height: 32px;
    }
    .w700{
      width: 700px;
    }
  }
  </style>

