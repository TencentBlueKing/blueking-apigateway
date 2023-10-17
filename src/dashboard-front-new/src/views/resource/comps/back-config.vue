
<template>
  <bk-form ref="backRef" :model="backConfigData" :rules="rules" class="back-config-container">
    <bk-form-item
      :label="t('服务')"
      required
    >
      <bk-select
        :input-search="false"
        class="w700"
        v-model="backConfigData.backend_id" @change="handleServiceChange">
        <bk-option v-for="item in servicesData" :key="item.id" :value="item.id" :label="item.name" />
      </bk-select>
    </bk-form-item>
    <bk-table
      v-if="backConfigData.backend_id"
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
        v-model="backConfigData.method"
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
          @click="handleCheckPath"
        >
          {{ t('校验并查看地址') }}
        </bk-button>
        <bk-checkbox class="ml40" v-model="backConfigData.match_subpath">
          {{ t('追加匹配的子路径') }}
        </bk-checkbox>
      </div>
      <div class="common-form-tips">后端接口地址的 Path，不包含域名或 IP，支持路径变量、环境变量，变量包含在{}中，比如：/users/{id}/{env.type}/。
        更多详情</div>
      <div>
        <bk-alert
          theme="success"
          class="w700 mt10"
          :title="t('路径校验通过，路径合法，请求将被转发到以下地址')"
        />
        <bk-table
          v-if="servicesCheckData.length"
          class="w700 mt10"
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
            :label="t('请求类型')"
          >
            <template>
              {{backConfigData.method || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('请求地址')"
          >
            <template #default="{ data }">
              {{data?.backend_urls && data?.backend_urls[0]}}
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </bk-form-item>
  </bk-form>
</template>
<script setup lang="ts">
import { ref, defineExpose } from 'vue';
import { useI18n } from 'vue-i18n';
import { getBackendsListData, getBackendsDetailData, backendsPathCheck } from '@/http';
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
// 服务列表下拉框数据
const servicesData = ref([]);
// 服务详情
const servicesConfigs = ref([]);

// 校验列表
const servicesCheckData = ref([]);
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

// 选择服务获取服务详情数据
const handleServiceChange = async (backendId: number) => {
  const res = await getBackendsDetailData(common.apigwId, backendId);
  servicesConfigs.value = res.configs;
};

// 校验路径
const handleCheckPath = async () => {
  try {
    const params = {
      backend_id: backConfigData.value.backend_id,
      backend_path: backConfigData.value.path,
    };
    const res = await backendsPathCheck(common.apigwId, params);
    servicesCheckData.value = res;
    console.log('servicesCheckData', servicesCheckData.value);
  } catch (error) {

  }
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
      .table-layout{
        margin: 0 0 20px 150px;
        width: 700px !important;
      }
      .public-switch{
          height: 32px;
      }
      .w700{
        width: 700px !important;
      }
      .w568{
        width: 568px !important;
      }
    }
    </style>


