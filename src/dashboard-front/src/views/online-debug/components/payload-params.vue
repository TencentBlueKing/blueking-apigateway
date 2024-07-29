<template>
  <bk-collapse
    class="params-collapse"
    v-model="activeIndex"
  >
    <bk-collapse-panel :name="1" style="margin-bottom: 20px">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill class="params-header-fold" /><span>{{ t('Query 参数') }}</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="queryRef" :list="queryList" />
        </div>
      </template>
    </bk-collapse-panel>
    <bk-collapse-panel :name="2">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill class="params-header-fold" /><span>{{ t('Path 参数') }}</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="pathRef" :list="pathList" />
        </div>
      </template>
    </bk-collapse-panel>
  </bk-collapse>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import editTable from '@/views/online-debug/components/edit-table.vue';

const { t } = useI18n();

const props = defineProps({
  queryPayload: {
    type: Array,
    default: [],
  },
  pathPayload: {
    type: Array,
    default: [],
  },
});

const queryRef = ref();
const queryList = ref<any[]>([]);
const pathRef = ref();
const pathList = ref<any[]>([]);
const activeIndex = ref<number[]>([1, 2]);

const validate = async () => {
  const query = await queryRef.value?.validate();
  const path = await pathRef.value?.validate();

  if (query && path) {
    return true;
  }
  return false;
};

const getData = () => {
  return {
    query: queryRef.value?.getTableData(),
    path: pathRef.value?.getTableData(),
  };
};

watch(
  () => [props.queryPayload, props.pathPayload],
  ([v1, v2]) => {
    queryList.value = v1;
    pathList.value = v2;
  },
  {
    deep: true,
  },
);

defineExpose({
  validate,
  getData,
});

</script>

<style lang="scss" scoped>
.params-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  cursor: pointer;
  .params-header-title {
    font-weight: 700;
    font-size: 14px;
    color: #313238;
    display: flex;
    align-items: center;
    .params-header-fold {
      margin-top: 2px;
      margin-right: 8px;
    }
  }
}
.params-collapse {
  :deep(.bk-collapse-content) {
    padding: 0;
  }
}
</style>
