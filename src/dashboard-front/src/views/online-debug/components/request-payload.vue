<template>
  <bk-tab
    v-model:active="active"
    type="unborder-card"
    class="payload-tab"
  >
    <bk-tab-panel label="Body" name="Body">
      <template #label>
        <div :class="['tab-label', active?.includes('Body') ? 'active' : '']">
          <span class="title">Body</span>
          <span class="count">{{ bodyData?.list?.length || 0 }}</span>
        </div>
      </template>
      <payload-body
        ref="payloadBodyRef"
        :from-data-payload="schema.fromDataPayload"
        :raw-payload="schema.rawPayload"
        @change="handleBodyChange"
      />
    </bk-tab-panel>
    <bk-tab-panel label="Params" name="Params">
      <template #label>
        <div :class="['tab-label', active?.includes('Params') ? 'active' : '']">
          <span class="title">Params</span>
          <span class="count">{{ queryList?.length }}</span>
        </div>
      </template>
      <payload-params
        :query-payload="schema.queryPayload"
        :path-payload="schema.pathPayload"
        :priority-path="schema.priorityPath"
        @query-change="queryChange"
        ref="payloadParamsRef" />
    </bk-tab-panel>
    <bk-tab-panel label="Headers" name="Headers">
      <template #label>
        <div :class="['tab-label', active?.includes('Headers') ? 'active' : '']">
          <span class="title">Headers</span>
          <span class="count">{{ headersList?.length }}</span>
        </div>
      </template>
      <payload-headers
        :headers-payload="schema.headersPayload"
        @change="headersChange"
        ref="payloadHeadersRef" />
    </bk-tab-panel>
  </bk-tab>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import payloadBody from './payload-body.vue';
import payloadParams from './payload-params.vue';
import payloadHeaders from './payload-headers.vue';

const props = defineProps({
  tab: {
    type: String,
    default: 'Params',
  },
  schema: {
    type: Object,
    default: {},
  },
});

const active = ref<string>(props.tab);
const payloadBodyRef = ref();
const payloadParamsRef = ref();
const payloadHeadersRef = ref();

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

watch(
  () => props.tab,
  (v) => {
    active.value = v;
  },
);

defineExpose({
  validate,
  getData,
});

</script>

<style lang="scss" scoped>
.payload-tab {
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
