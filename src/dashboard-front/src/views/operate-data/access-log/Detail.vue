/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<!-- eslint-disable vue/no-v-html -->

<template>
  <BkLoading
    :loading="isDataLoading"
    color="#fafbfd"
    :opacity="1"
  >
    <!-- <div class="access-log-container" v-bkloading="{ isLoading: true, opacity: 1, color: '#FAFBFD' }"> -->
    <div class="access-log-container">
      <div
        v-show="!hasError"
        class="detail-panel"
      >
        <div class="panel-hd">
          <h2
            v-bk-xss-html="titleInfo"
            class="title"
          />
          <small class="time">{{ transformTime(+routeQuery.bk_timestamp) }}</small>
        </div>
        <div class="panel-bd">
          <dl class="details">
            <div
              v-for="({ label, field }, index) in details.fields"
              :key="index"
              class="item"
            >
              <dt class="label">
                {{ label }}
              </dt>
              <dd class="value">
                {{ getFieldText(field) }}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </BkLoading>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import {
  type ILogDetailInterface,
  fetchApigwAccessLogDetail,
} from '@/services/source/access-log';
import { useGatewaysList } from '@/hooks';
// import { useCommon } from '@/stores';

const { t } = useI18n();
const route = useRoute();
// const common = useCommon();

// 组件默认不展示任何请求的错误 Message
// common.setNoGlobalError(true);

// 获取网关数据方法
const { getGatewaysListData } = useGatewaysList({});

const isDataLoading = ref(false);
const hasError = ref(false);
const apigwDataList = ref([]);
const details: any = ref({
  fields: [],
  result: {},
});

const routeQuery = computed(() => route.query);

const routeParams = computed(() => route.params);

const currentApigwName = computed(() => {
  const current = apigwDataList.value.find(item => String(item.id) === String(routeParams.value.id)) || {};
  return current.name || '--';
});

const titleInfo = computed(() => t(
  '蓝鲸应用ID [{detailsAppCode}] 访问API网关 [{currentApigwName}] 资源的请求详情',
  {
    detailsAppCode: details.value?.result?.app_code || '--',
    currentApigwName: currentApigwName.value,
  },
));

const getDetailData = async () => {
  const params: ILogDetailInterface = {
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
  }
  catch (err) {
    console.error(err);
    hasError.value = true;
  }
  finally {
    isDataLoading.value = false;
  }
};

const initData = async () => {
  await getDetailData();
};

const transformTime = (time: number) => dayjs.unix(time).format('YYYY-MM-DD HH:mm:ss');

const getFieldText = (field: string) => {
  if (field === 'timestamp') return transformTime(details.value.result[field]);

  if (details.value.result[field] === false) return false;

  return details.value.result[field] || '--';
};

onMounted(async () => {
  await initData();
  apigwDataList.value = await getGatewaysListData();
});

// 离开组件前重置 noGlobalError 状态，避免其他页面也不展示错误 Message
onBeforeRouteLeave(() => {
  // common.setNoGlobalError(false);
});

onBeforeUnmount(() => {
  // common.setNoGlobalError(false);
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
  margin-bottom: 24px;
  border: 1px solid #EBEDF1;
  background: #fff;

  .panel-bd {
    padding: 16px 0;
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
