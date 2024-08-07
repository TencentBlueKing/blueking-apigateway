<template>
  <bk-collapse
    class="params-collapse"
    v-model="activeIndex"
  >
    <bk-collapse-panel :name="1" style="margin-bottom: 20px">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill :class="['params-header-fold', activeIndex?.includes(1) ? '' : 'fold']" />
            <span>{{ t('Query 参数') }}</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="queryRef" :list="queryList" @change="handleQueryChange" />
        </div>
      </template>
    </bk-collapse-panel>
    <bk-collapse-panel :name="2">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill :class="['params-header-fold', activeIndex?.includes(2) ? '' : 'fold']" />
            <span>{{ t('Path 参数') }}</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="pathRef" :list="pathList" @change="handlePathChange" />
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
  priorityPath: {
    type: Array,
    default: [],
  },
});

const emit = defineEmits(['queryChange', 'pathChange']);

const queryRef = ref();
const queryList = ref<any[]>([]);
const pathRef = ref();
const pathList = ref<any[]>([]);
const activeIndex = ref<number[]>([1]);

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

const handleQueryChange = (list: any) => {
  emit('queryChange', list);
};

const handlePathChange = (list: any) => {
  emit('pathChange', list);
};

watch(
  () => [props.queryPayload, props.pathPayload, props.priorityPath],
  ([v1, v2, v3]) => {
    queryList.value = v1;
    pathList.value = v3?.length ? v3 : v2;
  },
  {
    deep: true,
  },
);

watch(
  () => pathList.value,
  (v) => {
    if (v?.length && v[0]?.name) {
      activeIndex.value = [1, 2];
    } else {
      activeIndex.value = [1];
    }
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
      margin-right: 8px;
      transition: all .2s;
      &.fold {
        transform: rotate(-90deg);
      }
    }
  }
}
.params-collapse {
  :deep(.bk-collapse-content) {
    padding: 0;
  }
}
</style>
