<template>
  <div class="import-container p20">
    <div class="import-header flex-row justify-content-between">
      <div class="flex-row align-items-center">
        <bk-button>
          <i class="icon apigateway-icon icon-ag-add-small pr10"></i>
          导入 Swagger 文件
        </bk-button>
        <span class="desc">（json /yaml 格式）</span>
        <bk-form class="flex-row">
          <bk-form-item class="mb0" :label-width="20">
            <bk-checkbox>
              生成资源文档
            </bk-checkbox>
          </bk-form-item>
          <bk-form-item class="mb0" label="文档语言" :required="true" :label-width="120">
            <bk-radio-group>
              <bk-radio label="zh">中文文档</bk-radio>
              <bk-radio label="en">英文文档</bk-radio>
            </bk-radio-group>
          </bk-form-item>
        </bk-form>
      </div>
      <div class="flex-row align-items-center">
        <bk-link theme="primary">
          模板示例
        </bk-link>
        <bk-link theme="primary" class="pl10">
          <i class="apigateway-icon icon-ag-info"></i>
          Swagger 说明文档
        </bk-link>
      </div>
    </div>

    <div class="monacoEditor mt20">
      <editor-monaco v-model="test" ref="resourceEditorRef" />
    </div>
  </div>
</template>
<script setup lang="ts">
import editorMonaco from '@/components/ag-editor.vue';
import { ref, watch, nextTick } from 'vue';

const test = ref<string>('test111111');
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>(); // 实例化

nextTick(() => {
  resourceEditorRef.value?.setValue(test.value);
});

watch(test, () => {
  console.log('tse', test.value);
});

</script>
<style scoped lang="scss">
.import-container{
  .import-header{
    .icon-ag-add-small{
      font-size: 16px;
    }
    .desc{
      font-size: 12px;
      color: #979ba5;
    }
  }
  .monacoEditor {
    width: 100%;
    height: calc(100vh - 240px);
  }
}
</style>
