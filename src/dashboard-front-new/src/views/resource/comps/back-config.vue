
<template>
  <bk-form ref="backRef" :model="backConfigData" :rules="rules" class="back-config-container">
    <bk-form-item
      :label="t('服务')"
      required
    >
      <bk-select
        :input-search="false"
        class="w700"
        v-model="backConfigData.id" @change="handleServiceChange">
        <bk-option v-for="item in servicesData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-table
      v-if="backConfigData.id"
      class="table-layout w700"
      :data="servicesConfigs"
      :border="['outer']"
    >
      <bk-table-column
        :label="t('环境名称')"
      >
        <template #default="{ data }">
          {{data?.stage?.name}}
        </template>
      </bk-table-column>
      <bk-table-column
        :label="t('后端服务地址')"
      >
        <template #default="{ data }">
          {{data?.hosts[0].scheme}}://{{ data?.hosts[0].host }}
        </template>
      </bk-table-column>
      <bk-table-column
        :label="t('超时时间')"
        prop="timeout"
      >
      </bk-table-column>
    </bk-table>
    <bk-form-item
      :label="t('请求方法')"
      required
    >
      <bk-select
        :input-search="false"
        v-model="backConfigData.config.method"
        class="w700">
        <bk-option v-for="item in methodData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-form-item
      :label="t('请求路径')"
      property="config.path"
      required
    >
      <div class="flex-row aligin-items-center">
        <bk-input
          v-model="backConfigData.config.path"
          :placeholder="t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
          clearable
          class="w568"
        />
        <bk-button
          theme="primary"
          outline
          class="ml10"
          @click="handleCheckPath"
          :disabled="!backConfigData.id || !backConfigData.config.path"
        >
          {{ t('校验并查看地址') }}
        </bk-button>
        <bk-checkbox class="ml40" v-model="backConfigData.config.match_subpath">
          {{ t('追加匹配的子路径') }}
        </bk-checkbox>
      </div>
      <div class="common-form-tips">{{ t('后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在{}中，比如：/users/{id}/{env.type}/。') }}
        <a :href="GLOBAL_CONFIG.DOC.TEMPLATE_VARS" target="_blank" class="ag-primary">{{ t('更多详情') }}</a>
      </div>
      <div v-if="servicesCheckData.length">
        <bk-alert
          theme="success"
          class="w700 mt10"
          :title="t('路径校验通过，路径合法，请求将被转发到以下地址')"
        />
        <bk-table
          class="w700 mt10"
          :data="servicesCheckData"
          :border="['outer']"
        >
          <bk-table-column
            :label="t('环境名称')"
          >
            <template #default="{ data }">
              {{data?.stage?.name}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求类型')"
          >
            <template #default="{ data }">
              {{backConfigData.config.method || data?.stage?.name}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求地址')"
          >
            <template #default="{ data }">
              {{data?.backend_urls[0]}}
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </bk-form-item>
  </bk-form>
</template>
<script setup lang="ts">
import { ref, defineExpose, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { getBackendsListData, getBackendsDetailData, backendsPathCheck } from '@/http';
import { useCommon } from '../../../store';

const props = defineProps({
  detail: {
    type: Object,
    default: {},
  },
});

const backRef = ref(null);
const { t } = useI18n();
const common = useCommon();
const backConfigData = ref({
  id: '',
  config: {
    path: '',
    method: '',
    match_subpath: false,
  },
});
const methodData = ref(common.methodList);
// 服务列表下拉框数据
const servicesData = ref([]);
// 服务详情
const servicesConfigs = ref([]);
// window 全局变量
const GLOBAL_CONFIG = ref(window.GLOBAL_CONFIG);
// 校验列表
const servicesCheckData = ref([]);

const rules = {
  'config.path': [
    {
      required: true,
      message: t('请填写请求路径'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^\/[\w{}/.-]*$/.test(value),
      message: t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
      trigger: 'blur',
    },
  ],
};

// 选择服务获取服务详情数据
const handleServiceChange = async (backendId: number) => {
  const res = await getBackendsDetailData(common.apigwId, backendId);
  servicesConfigs.value = res.configs;
};

// 校验路径
const handleCheckPath = async () => {
  try {
    const params = {
      backend_id: backConfigData.value.id,
      backend_path: backConfigData.value.config.path,
    };
    const res = await backendsPathCheck(common.apigwId, params);
    servicesCheckData.value = res;
    console.log('servicesCheckData', servicesCheckData.value);
  } catch (error) {

  }
};

watch(
  () => props.detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { backend } = val;
      backConfigData.value = { ...backend };
      handleServiceChange(backend.id);
    }
  },
  { immediate: true },
);

const init = async () => {
  const res = await getBackendsListData(common.apigwId);
  console.log('res', res);
  servicesData.value = res.results;
};

const validate = async () => {
  await backRef.value?.validate();
};

init();
defineExpose({
  backConfigData,
  validate,
});
</script>
    <style lang="scss" scoped>
    .back-config-container{
      .table-layout{
        margin: 0 0 20px 150px;
        width: 700px !important;
      }
      .public-switch{
          height: 32px;
      }
      .w700{
          max-width: 700px !important;
          width: 70% !important;
        }
      .w568{
        max-width: 568px !important;
        width: 55% !important;
      }
    }
    </style>


