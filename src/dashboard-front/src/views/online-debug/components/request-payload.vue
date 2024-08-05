<template>
  <bk-tab
    v-model:active="active"
    type="unborder-card"
    class="payload-tab"
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
        :priority-path="schema.priorityPath"
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
}
</style>
