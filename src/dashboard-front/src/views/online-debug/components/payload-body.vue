<template>
  <div class="body-payload">
    <div class="table-header">
      <div class="body-type">
        <div
          :class="['body-type-item', type === 'data' ? 'active' : '']"
          @click="type = 'data'">
          form-data
        </div>
        <div
          :class="['body-type-item', type === 'urlencoded' ? 'active' : '']"
          @click="type = 'urlencoded'">
          x-www-form-urlencoded
        </div>
        <div
          :class="['body-type-item', type === 'raw' ? 'active' : '']"
          @click="type = 'raw'">
          raw
        </div>
        <bk-select
          v-show="type === 'raw'"
          class="raw-select"
          v-model="rawType"
          :clearable="false"
          :filterable="false"
        >
          <bk-option
            v-for="(item, index) in datasource"
            :id="item.value"
            :key="index"
            :name="item.label"
          />
        </bk-select>
      </div>
      <!-- <div class="payload-type">
          <div class="payload-type-item active">
            <span class="icon apigateway-icon icon-ag-menu"></span>
            表格模式
          </div>
          <div class="payload-type-item">
            <span class="icon apigateway-icon icon-ag-menu"></span>
            代码模式
          </div>
        </div> -->
    </div>
    <edit-table v-show="type !== 'raw'" ref="editTableRef" />
    <div class="raw-content" v-show="type === 'raw'">
      <editor-monaco v-model="editorText" theme="Visual Studio" ref="resourceEditorRef" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import editTable from '@/views/online-debug/components/edit-table.vue';
import editorMonaco from '@/components/ag-editor.vue';

const { t } = useI18n();

const type = ref<string>('data');
const rawType = ref<string>('JSON');
const editTableRef = ref();
const datasource = ref([
  {
    value: 'climbing',
    label: 'JSON',
  },
  {
    value: 'climbing1',
    label: 'XML',
  },
  {
    value: 'climbing2',
    label: 'HTML',
  },
  {
    value: 'fitness',
    label: 'TEXT',
  },
]);
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();
const editorText = ref<string>(`{
	"type": "team",
	"test": {
		"testPage": "tools/testing/run-tests.htm",
		"enabled": true
	},
    "search": {
        "excludeFolders": [
			".git",
			"tools/testing/qunit",
			"tools/testing/chutzpah",
			"server.net"
        ]
}`);

const getData = () => {
  if (type.value !== 'raw') {
    return {
      type: type.value,
      list: editTableRef.value?.getTableData(),
    };
  }
  return {
    type: type.value,
    rawType: rawType.value,
    text: editorText.value,
  };
};

defineExpose({
  getData,
});
</script>

<style lang="scss" scoped>
.table-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  .body-type {
    display: flex;
    align-items: center;
    padding-bottom: 10px;
    .body-type-item {
      padding: 4px 8px;
      background: #F0F1F5;
      border-radius: 11px;
      color: #63656E;
      font-size: 12px;
      cursor: pointer;
      &:not(:nth-last-child(1)) {
        margin-right: 8px;
      }
      &.active {
        color: #FFFFFF;
        background: #3A84FF;
        position: relative;
        padding-left: 36px;
        &::before {
          position: absolute;
          content: ' ';
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 1px solid #fff;
          top: 50%;
          transform: translateY(-50%);
          left: 12px;
        }
        &::after {
          position: absolute;
          content: ' ';
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #FFFFFF;
          top: 50%;
          transform: translateY(-50%);
          left: 16px;
        }
      }
    }
  }
}
.raw-select {
  width: 120px;
}
.raw-content {
  width: 100%;
  height: 312px;
  background: #FFFFFF;
  border: 1px solid #DCDEE5;
  border-radius: 2px;
}
</style>
