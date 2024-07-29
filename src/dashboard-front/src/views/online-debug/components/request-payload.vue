<template>
  <bk-tab
    v-model:active="active"
    type="unborder-card"
  >
    <bk-tab-panel label="Body" name="Body">
      <payload-body
        ref="payloadBodyRef"
        :from-data-payload="schema.fromDataPayload"
        :raw-payload="schema.rawPayload" />
    </bk-tab-panel>
    <bk-tab-panel label="Params" name="Params">
      <payload-params
        :query-payload="schema.queryPayload"
        :path-payload="schema.pathPayload"
        ref="payloadParamsRef" />
    </bk-tab-panel>
    <bk-tab-panel label="Headers" name="Headers">
      <payload-headers
        :headers-payload="schema.headersPayload"
        ref="payloadHeadersRef" />
    </bk-tab-panel>
  </bk-tab>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import payloadBody from './payload-body.vue';
import payloadParams from './payload-params.vue';
import payloadHeaders from './payload-headers.vue';

const active = ref<string>('Body');
const payloadBodyRef = ref();
const payloadParamsRef = ref();
const payloadHeadersRef = ref();

defineProps({
  schema: {
    type: Object,
    default: {},
  },
});

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

defineExpose({
  validate,
  getData,
});

</script>

<style lang="scss" scoped>
.payload-type {
  display: flex;
  align-items: center;
  background: #F0F1F5;
  border-radius: 2px;
  padding: 4px;
  .payload-type-item {
    display: flex;
    align-items: center;
    font-size: 12px;
    color: #63656E;
    padding: 4px 10px;
    cursor: pointer;
    .apigateway-icon {
      margin-right: 4px;
      font-size: 16px;
    }
    &.active  {
      color: #3A84FF;
      background-color: #fff;
      border-radius: 2px;
    }
  }
}
</style>
