<template>
  <bk-collapse
    class="params-collapse"
    v-model="activeIndex"
  >
    <bk-collapse-panel :name="1">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill :class="['params-header-fold', activeIndex?.includes(1) ? '' : 'fold']" />
            <span>{{ t('Headers 参数') }}</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="editTableRef" :list="headerList" @change="handleChange" />
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
  headersPayload: {
    type: Array,
    default: [],
  },
});

const emit = defineEmits(['change']);

const activeIndex = ref<number[]>([1]);
const editTableRef = ref();
const headerList = ref<any[]>([]);

const validate = async () => {
  return await editTableRef.value?.validate();
};

const getData = () => {
  return editTableRef.value?.getTableData();
};

const handleChange = (list: any) => {
  emit('change', list);
};

watch(
  () => props.headersPayload,
  (v: any) => {
    headerList.value = v;
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
