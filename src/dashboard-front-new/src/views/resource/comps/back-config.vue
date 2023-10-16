
<template>
  <bk-form ref="backRef" :model="backConfigData" :rules="rules" class="back-config-container">
    <bk-form-item
      :label="t('服务')"
      v-model="backConfigData.backend_id"
      property="method"
      required
    >
      <bk-select
        :input-search="false"
        class="w700">
        <bk-option v-for="item in servicesData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item
      :label="t('请求方法')"
      v-model="backConfigData.method"
      property="method"
      required
    >
      <bk-select
        :input-search="false"
        multiple
        filterable
        multiple-mode="tag"
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
          v-model="backConfigData.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w568"
        />
        <bk-button
          theme="primary"
          outline
          class="ml10"
        >
          {{ t('校验并查看地址') }}
        </bk-button>
        <bk-checkbox class="ml40" v-model="backConfigData.match_subpath">
          {{ t('追加匹配的子路径') }}
        </bk-checkbox>
      </div>
      <div class="common-form-tips">后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在{}中，比如：/users/{id}/{env.type}/。
        更多详情</div>
      <bk-alert
        theme="success"
        class="w700 mt10"
        :title="t('路径校验通过，路径合法，请求将被转发到以下地址')"
      />
    </bk-form-item>
  </bk-form>
</template>
<script setup lang="ts">
import { ref, defineExpose } from 'vue';
import { useI18n } from 'vue-i18n';
import { getBackendsListData } from '@/http';
import { useCommon } from '../../../store';

const { t } = useI18n();
const common = useCommon();
const backConfigData = ref({
  backend_id: '',
  path: '',
  method: '',
  match_subpath: false,
});
const methodData = ref(common.methodList);
const servicesData = ref([]);

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

const init = async () => {
  const res = await getBackendsListData(common.apigwId);
  console.log('res', res);
  servicesData.value = res.results;
};
init();

defineExpose({
  backConfigData,
});
</script>
    <style lang="scss" scoped>
    .back-config-container{
      .public-switch{
          height: 32px;
      }
      .w700{
        width: 700px;
      }
      .w568{
        width: 568px;
      }
    }
    </style>


