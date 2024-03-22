<template>
  <div class="import-container p20">
    <section v-if="curView === 'import'">
      <div class="import-header flex-row justify-content-between">
        <div class="flex-row align-items-center">
          <bk-upload
            theme="button"
            :custom-request="handleReq"
            class="upload-cls"
            accept=".yaml,.json,.yml"
          >
            <div>
              <i class="icon apigateway-icon icon-ag-add-small"></i>
              {{ t('导入 Swagger 文件') }}
            </div>
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
          <!-- <bk-link theme="primary" :href="GLOBAL_CONFIG.DOC.TEMPLATE_VARS" target="_blank">
            {{ t('模板示例') }}
          </bk-link> -->
          <bk-button theme="primary" text @click="handleShowExample">{{ t('模板示例') }}</bk-button>
          <bk-link theme="primary" class="pl10" :href="GLOBAL_CONFIG.DOC.SWAGGER" target="_blank">
            <i class="apigateway-icon icon-ag-info"></i>
            {{ t('Swagger 说明文档') }}
          </bk-link>
        </div>
      </div>

      <div class="monacoEditor mt10">
        <editor-monaco v-model="editorText" ref="resourceEditorRef" />
      </div>
    </section>
    <section v-else>
      <div class="flex-row justify-content-between">
        <div class="info">
          {{ t('请确认以下资源变更，资源配置：') }}
          <span class="add-info">{{ t('新建') }}
            <span class="ag-strong success pl5 pr5">
              {{ createNum }}
            </span>{{ t('条') }}
          </span>
          <span class="add-info">{{ t('覆盖') }}
            <span class="ag-strong danger pl5 pr5">{{ updateNum }}</span>
            {{ t('条') }}
          </span>
          <span v-if="showDoc">
            ，{{ $t('资源文档：') }}
            <span class="add-info">{{ t('新建') }}<span class="ag-strong success pl5 pr5">1</span>{{ t('条') }}</span>
            <span class="add-info">{{ t('覆盖') }}<span class="ag-strong danger pl5 pr5">1</span>{{ t('条') }}</span>
          </span>
        </div>
      </div>
      <bk-table
        class="table-layout"
        :data="tableData"
        show-overflow-tooltip
        :checked="tableData"
        @selection-change="handleSelectionChange"
      >
        <bk-table-column
          width="80"
          type="selection"
          align="center"
        />
        <bk-table-column
          :label="t('请求路径')"
          prop="path"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('请求方法')"
          prop="method"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('描述')"
          prop="description"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('资源操作类型')"
          prop="path"
        >
          <template #default="{ data }">
            <span class="danger-c" v-if="data?.id">{{ t('覆盖') }}</span>
            <span class="success-c" v-else>{{ t('新建') }}</span>
          </template>
        </bk-table-column>
      </bk-table>
    </section>

    <div class="mt15">
      <bk-button
        :theme="curView === 'import' ? 'primary' : ''"
        @click="handleCheckData"
        :loading="isDataLoading"
      >
        {{ curView === 'import' ? t('下一步') : t('上一步') }}
      </bk-button>
      <span v-bk-tooltips="{ content: t('请确认勾选资源'), disabled: selections.length }" v-if="curView === 'resources'">
        <bk-button
          class="mr10"
          theme="primary"
          type="button"
          :disabled="!selections.length"
          @click="handleImportResource" :loading="isImportLoading">
          {{ $t('确定导入') }}
        </bk-button>
      </span>
      <bk-button @click="goBack">
        {{ t('取消') }}
      </bk-button>
    </div>

    <TmplExampleSideslider :is-show="isShowExample" @on-hidden="handleHiddenExample"></TmplExampleSideslider>
  </div>
</template>
<script setup lang="ts">
import { ref, nextTick, computed } from 'vue';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import editorMonaco from '@/components/ag-editor.vue';
import exampleData from '@/constant/example-data';
import { getStrFromFile } from '@/common/util';
import { checkResourceImport, importResource, importResourceDocSwagger } from '@/http';
import { useCommon } from '@/store';
import { useSelection, useGetGlobalProperties } from '@/hooks';
import TmplExampleSideslider from '@/views/resource/setting/comps/tmpl-example-sideslider.vue';

const router = useRouter();
const { t } = useI18n();
const common = useCommon();
const editorText = ref<string>(exampleData.content);
const { apigwId } = common; // 网关id
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>(); // 实例化
const showDoc = ref<boolean>(false);
const language = ref<string>('zh');
const isDataLoading = ref<boolean>(false);
const isImportLoading = ref<boolean>(false);
const curView = ref<string>('import'); // 当前页面
const tableData = ref<any[]>([]);
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

// 资源新建条数
const createNum = computed(() => {
  const results = deDuplication(selections.value.filter(item => !item.id), 'name');
  return results.length;
});

// 资源覆盖条数
const updateNum = computed(() => {
  const results = deDuplication(selections.value.filter(item => item.id), 'name');
  return results.length;
});

// checkbox hooks
const {
  selections,
  handleSelectionChange,
} = useSelection();

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
const handleCheckData = async () => {
  // 上一步按钮功能
  if (curView.value === 'resources') {
    curView.value = 'import';
    return;
  }
  if (!editorText.value) {
    Message({
      theme: 'error',
      message: t('请输入Swagger内容'),
    });
  }
  try {
    isDataLoading.value = true;
    const parmas: any = {
      content: editorText.value,
      allow_overwrite: true,
    };
    // 如果勾选了资源文档
    if (showDoc.value) {
      parmas.doc_language = language.value;
    }
    const res = await checkResourceImport(apigwId, parmas);
    tableData.value = res;
    curView.value = 'resources';
    nextTick(() => {
      selections.value = JSON.parse(JSON.stringify(tableData.value));
    });
    // resetSelections();
  } catch (error) {

  } finally {
    isDataLoading.value = false;
  }
};

// 确认导入
const handleImportResource = async () => {
  try {
    isImportLoading.value = true;
    const parmas = {
      content: editorText.value,
      selected_resources: selections.value,
    };
    await importResource(apigwId, parmas);
    // 勾选了文档才需要上传swagger文档
    if (showDoc.value) {
      // swagger需要的参数
      const resourceDocs = selections.value.map((e: any) => ({
        language: e.doc.language,
        resource_name: e.name,
      }));
      const paramsDocs = {
        swagger: editorText.value,
        selected_resource_docs: resourceDocs,
        language: language.value,
      };
      await importResourceDocSwagger(apigwId, paramsDocs);
    }
    Message({
      theme: 'success',
      message: t('资源导入成功'),
    });
    goBack();
  } catch (error) {

  } finally {
    isImportLoading.value = false;
  }
};


const deDuplication = (data: any[], k: string) => {
  const map = new Map();
  for (const item of data) {
    if (!map.has(item[k])) {
      map.set(item[k], item);
    }
  }
  return [...map.values()];
};

// 取消返回到资源列表
const goBack = () => {
  router.push({
    name: 'apigwResource',
  });
};

const isShowExample = ref(false);
const handleShowExample = () => {
  isShowExample.value = true;
};

const handleHiddenExample = () => {
  isShowExample.value = false;
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
