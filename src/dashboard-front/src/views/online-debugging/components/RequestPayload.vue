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

<template>
  <BkTab
    v-model:active="active"
    type="unborder-card"
    class="payload-tab"
  >
    <BkTabPanel
      label="Body"
      name="Body"
    >
      <template #label>
        <div
          class="tab-label"
          :class="[active?.includes('Body') ? 'active' : '']"
        >
          <span class="title">Body</span>
          <span class="count">{{ bodyData?.list?.length || 0 }}</span>
        </div>
      </template>
      <PayloadBody
        ref="payloadBodyRef"
        :from-data-payload="schema.fromDataPayload"
        :raw-payload="schema.rawPayload"
        @change="handleBodyChange"
      />
    </BkTabPanel>
    <BkTabPanel
      label="Params"
      name="Params"
    >
      <template #label>
        <div
          class="tab-label"
          :class="[active?.includes('Params') ? 'active' : '']"
        >
          <span class="title">Params</span>
          <span class="count">{{ queryList?.length }}</span>
        </div>
      </template>
      <PayloadParams
        ref="payloadParamsRef"
        :query-payload="schema.queryPayload"
        :path-payload="schema.pathPayload"
        :priority-path="schema.priorityPath"
        @query-change="queryChange"
      />
    </BkTabPanel>
    <BkTabPanel
      label="Headers"
      name="Headers"
    >
      <template #label>
        <div
          class="tab-label"
          :class="[active?.includes('Headers') ? 'active' : '']"
        >
          <span class="title">Headers</span>
          <span class="count">{{ headersList?.length }}</span>
        </div>
      </template>
      <PayloadHeaders
        ref="payloadHeadersRef"
        :headers-payload="schema.headersPayload"
        @change="headersChange"
      />
    </BkTabPanel>
  </BkTab>
</template>

<script lang="ts" setup>
import PayloadBody from './PayloadBody.vue';
import PayloadParams from './PayloadParams.vue';
import PayloadHeaders from './PayloadHeaders.vue';

interface IProps {
  tab?: string
  schema?: object
}

const {
  tab = 'Params',
  schema = {},
} = defineProps<IProps>();

const active = ref<string>(tab);
const payloadBodyRef = ref();
const payloadParamsRef = ref();
const payloadHeadersRef = ref();

watch(
  () => tab,
  (value) => {
    active.value = value;
  },
);

const validate = async () => {
  const bodyValidate = await payloadBodyRef.value?.validate();
  const paramsValidate = await payloadParamsRef.value?.validate();
  const headersValidate = await payloadHeadersRef.value?.validate();

  if (bodyValidate && paramsValidate && headersValidate) {
    return true;
  }
  return false;
};

const getData = () => {
  return {
    body: payloadBodyRef.value?.getData(),
    params: payloadParamsRef.value?.getData(),
    headers: payloadHeadersRef.value?.getData(),
  };
};

const headersList = ref<any>([]);
const headersChange = (list: any) => {
  headersList.value = list;
};

const queryList = ref<any>([]);
const queryChange = (list: any) => {
  queryList.value = list;
};

// const pathList = ref<any>([]);
// const pathChange = (list: any) => {
//   pathList.value = list;
// };

const bodyData = ref<any>({});
const handleBodyChange = (data: any) => {
  bodyData.value = data;
};

defineExpose({
  validate,
  getData,
});

</script>

<style lang="scss" scoped>
.payload-tab {
  height: 100%;
  :deep(.bk-tab-content) {
    padding: 12px 24px 12px 0px;
  }
  .tab-label {
    .title {
      font-size: 14px;
      color: #63656E;
      margin-right: 4px;
    }
    .count {
      padding: 0px 8px;
      font-size: 12px;
      color: #979BA5;
      background: #F0F1F5;
      border-radius: 8px;
    }
    &.active {
      .title {
        color: #3A84FF;
      }
      .count {
        color: #3A84FF;
        background: #E1ECFF;
      }
    }
  }
}
</style>
