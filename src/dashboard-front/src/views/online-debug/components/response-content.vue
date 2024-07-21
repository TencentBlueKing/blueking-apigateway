<template>
  <div class="response-container">
    <div class="response-title flex">
      <div class="response-type flex">
        <angle-up-fill class="response-header-fold" />
        <bk-tab v-model:active="tabActive" type="unborder-card" class="response-type-tab">
          <bk-tab-panel label="Body" name="body"></bk-tab-panel>
          <bk-tab-panel label="请求详情" name="detail"></bk-tab-panel>
        </bk-tab>
      </div>
      <div class="response-status flex">
        <div class="response-status-item">
          <span class="label">Status：</span>
          <span class="value">400 Bad Request</span>
        </div>
        <div class="response-status-item">
          <span class="label">Time：</span>
          <span class="value">742 ms</span>
        </div>
        <div class="response-status-item">
          <span class="label">Size：</span>
          <span class="value">968 B</span>
        </div>
      </div>
    </div>
    <div class="response-main">
      <div class="response-content-type flex">
        <div class="payload-type">
          <div class="payload-type-item active">
            <span class="icon apigateway-icon icon-ag-menu"></span>
            Pretty
          </div>
          <div class="payload-type-item">
            <span class="icon apigateway-icon icon-ag-menu"></span>
            Raw
          </div>
        </div>
        <bk-select
          class="bk-select"
          v-model="responseType"
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
      <div class="response-content">
        <editor-monaco v-model="editorText" theme="Visual Studio" ref="resourceEditorRef" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import editorMonaco from '@/components/ag-editor.vue';

const tabActive = ref<string>('body');
const responseType = ref<string>('JSON');
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
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();

</script>

<style lang="scss" scoped>
.response-container {
  padding-left: 24px;
  .response-title {
    position: relative;
    .response-type {
      flex: 1;
      .response-header-fold {
        margin-top: -18px;
        margin-right: 8px;
      }
      .response-type-tab {
        flex: 1;
      }
    }
    .response-status {
      position: absolute;
      top: 18px;
      right: 24px;
      .response-status-item {
        font-size: 12px;
        margin-left: 12px;
        .label {
          color: #63656E;
        }
        .value {
          color: #1CAB88;
        }
      }
    }
  }
  .response-main {
    padding-bottom: 15px;
    .response-content-type {
      margin-bottom: 12px;
      .payload-type {
        margin-right: 8px;
      }
    }
    .response-content{
      width: 100%;
      height: 345px;
      background: #FFFFFF;
      border: 1px solid #DCDEE5;
      border-radius: 2px;
    }
  }
}
.flex {
  display: flex;
  align-items: center;
}
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
