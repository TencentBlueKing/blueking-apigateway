<template>
  <bk-collapse
    class="params-collapse"
    v-model="activeIndex"
  >
    <bk-collapse-panel :name="1" style="margin-bottom: 20px">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill class="params-header-fold" /><span>Query 参数</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="editTableRef1" />
        </div>
      </template>
    </bk-collapse-panel>
    <bk-collapse-panel :name="2">
      <template #header>
        <div class="params-header">
          <div class="params-header-title">
            <angle-up-fill class="params-header-fold" /><span>Path 参数</span>
          </div>
        </div>
      </template>
      <template #content>
        <div>
          <edit-table ref="editTableRef2" />
        </div>
      </template>
    </bk-collapse-panel>
  </bk-collapse>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import editTable from '@/views/online-debug/components/edit-table.vue';

const { t } = useI18n();
const editTableRef1 = ref();
const editTableRef2 = ref();
const activeIndex = ref<number[]>([1, 2]);

const getData = () => {
  return {
    query: editTableRef1.value?.getTableData(),
    path: editTableRef2.value?.getTableData(),
  };
};

defineExpose({
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
