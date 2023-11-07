<template>
  <div class="import-container p20">
    <div class="import-header flex-row justify-content-between">
      <div class="flex-row align-items-center">
        <!-- <bk-button>
          <i class="icon apigateway-icon icon-ag-add-small pr10"></i>
          {{ t('导入 Swagger 文件') }}
        </bk-button> -->
        <bk-upload
          theme="button"
          :custom-request="handleReq"
          class="upload-cls"
        >
          <template #default>
            <bk-button>
              <i class="icon apigateway-icon icon-ag-add-small pr10"></i>
              {{ t('导入 Swagger 文件') }}
            </bk-button>
          </template>
        </bk-upload>
        <span class="desc">{{ t('（json /yaml 格式）') }}</span>
        <bk-form class="flex-row">
          <bk-form-item class="mb0" :label-width="20">
            <bk-checkbox v-model="showDoc">
              {{ t('生成资源文档') }}
            </bk-checkbox>
          </bk-form-item>
          <bk-form-item class="mb0" :label="t('文档语言')" v-if="showDoc" :required="true" :label-width="120">
            <bk-radio-group v-model="language">
              <bk-radio label="zh">{{ t('中文文档') }}</bk-radio>
              <bk-radio label="en">{{ t('英文文档') }}</bk-radio>
            </bk-radio-group>
          </bk-form-item>
        </bk-form>
      </div>
      <div class="flex-row align-items-center">
        <bk-link theme="primary">
          {{ t('模板示例') }}
        </bk-link>
        <bk-link theme="primary" class="pl10">
          <i class="apigateway-icon icon-ag-info"></i>
          {{ t('Swagger 说明文档') }}
        </bk-link>
      </div>
    </div>

    <div class="monacoEditor mt10">
      <editor-monaco v-model="editorText" ref="resourceEditorRef" />
    </div>

    <div class="mt15">
      <bk-button
        theme="primary"
        @click="handleCheckData"
        :loading="isDataLoading"
      >
        {{ t('下一步') }}
      </bk-button>

      <bk-button>
        {{ t('取消') }}
      </bk-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import editorMonaco from '@/components/ag-editor.vue';
import { ref, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import exampleData from '@/constant/example-data';
import { Message } from 'bkui-vue';
import { getStrFromFile } from '@/common/util';

const { t } = useI18n();
const editorText = ref<string>(exampleData.content);
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>(); // 实例化
const showDoc = ref<boolean>(false);
const language = ref<string>('zh');
const isDataLoading = ref<boolean>(false);

// 设置editor的内容
const setEditValue = () => {
  nextTick(() => {
    resourceEditorRef.value?.setValue(editorText.value);
  });
};

// 自定义上传方法
const handleReq = (res: any) => {
  const { file } = res;
  const reg = '.*\\.(json|yaml|yml)';
  if (!file.name.match(reg)) {
    Message({
      theme: 'error',
      message: t('仅支持 json, yaml 格式'),
    });
    return;
  }
  // 读取文件内容并赋值给编辑器
  getStrFromFile(file).then((res: any) => {
    editorText.value = res;
    setEditValue();
  });
};
// 下一步需要检查数据
const handleCheckData = () => {
  if (editorText.value) {
    Message({
      theme: 'error',
      message: t('请输入Swagger内容'),
    });
  }
  isDataLoading.value = true;
  try {

  } catch (error) {

  }
};
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

  :deep(.upload-cls) {
    .bk-upload-list{
      display: none !important;
    }
  }
}
</style>
