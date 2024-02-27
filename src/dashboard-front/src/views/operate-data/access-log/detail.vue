<!-- eslint-disable vue/no-v-html -->

<template>
  <bk-loading :loading="isDataLoading" color="#fafbfd" :opacity="1">
    <!-- <div class="access-log-container" v-bkloading="{ isLoading: true, opacity: 1, color: '#FAFBFD' }"> -->
    <div class="access-log-container">
      <div class="detail-panel" v-show="!hasError">
        <div class="panel-hd">
          <h2 class="title" v-html="titleInfo"></h2>
          <small class="time">{{transformTime(+routeQuery.bk_timestamp)}}</small>
        </div>
        <div class="panel-bd">
          <dl class="details">
            <div class="item" v-for="({ label, field }, index) in details.fields" :key="index">
              <dt class="label">{{label}}</dt>
              <dd class="value">
                {{field === 'timestamp' ? transformTime(details.result[field]) : details.result[field]}}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </bk-loading>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import dayjs from 'dayjs';

import { useGetApiList } from '@/hooks';

import i18n from '@/language/i18n';
import { fetchApigwAccessLogDetail } from '@/http';
import { LogDetailInterface } from './common/type';

const { t } = i18n.global;
const route = useRoute();

const isDataLoading = ref(false);
const hasError = ref(false);

const apigwDataList = ref([]);

const details: any = ref({
  fields: [],
  result: {},
});

const getDetailData = async () => {
  const params: LogDetailInterface = {
    bk_nonce: String(routeQuery.value.bk_nonce),
    bk_signature: String(routeQuery.value.bk_signature),
    bk_timestamp: String(routeQuery.value.bk_timestamp),
    shared_by: String(routeQuery.value.shared_by),
  };
  isDataLoading.value = true;
  try {
    const res = await fetchApigwAccessLogDetail(+routeParams.value.id, String(routeParams.value.requestId), params);
    details.value.result = res.results[0] || {};
    details.value.fields = res.fields;
  } catch (e) {
    console.error(e);
    hasError.value = true;
  } finally {
    isDataLoading.value = false;
  }
};

const initData = async () => {
  await getDetailData();
};

const routeQuery = computed(() => route.query);
const routeParams = computed(() => route.params);

const currentApigwName = computed(() => {
  const current = apigwDataList.value.find(item => String(item.id) === String(routeParams.value.id)) || {};
  const name = current.name || '';
  return name;
});

const titleInfo = computed(() => t(
  '蓝鲸应用ID [{detailsAppCode}] 访问API网关 [{currentApigwName}] 资源的请求详情',
  { detailsAppCode: details.value.result.app_code, currentApigwName: currentApigwName.value },
));

const transformTime = (time: number) => dayjs.unix(time).format('YYYY-MM-DD HH:mm:ss');

onMounted(async () => {
  // console.error('routeParams', routeParams.value);
  // console.error('routeQuery', routeQuery.value);
  // console.error('apigwDataList.valueapigwDataList.value', apigwDataList.value);
  await initData();
  apigwDataList.value = useGetApiList({}).dataList.value;
});
</script>

<style lang="scss" scoped>
.access-log-container {
  width: 1280px;
  min-height: calc(100vh - 138px);
  margin: 0 auto;
  overflow: hidden;
}

.detail-panel {
  margin-top: 24px;
  border: 1px solid #EBEDF1;
  background: #fff;

  .panel-bd {
    padding: 16px 0 32px 0;
  }

  .panel-hd {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #EBEDF1;
    padding: 0 30px;

    .title {
      font-size: 22px;
      color: #313238;
      margin: 20px 0;
    }

    .time {
      font-size: 14px;
      color: #C4C6CC;
    }
  }
}

.details {
  position: relative;
  padding: 16px 0;
  .item {
    display: flex;
    margin-bottom: 8px;
    font-size: 12px;

    .label {
      position: relative;
      flex: none;
      width: 200px;
      font-weight: bold;
      color: #63656E;
      margin-right: 32px;
      text-align: right;
    }
    .value {
      flex: none;
      width: 500px;
      white-space: pre-wrap;
      word-break: break-word;
      color: #63656E;
      line-height: 20px;
    }
  }

  .share-btn {
    position: absolute;
    right: 0;
    top: 18px;
  }
}
</style>
