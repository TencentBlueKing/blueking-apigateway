<template>
  <div class="import-docs-container p20">
    <bk-form :label-width="100" v-if="curView === 'import'">
      <bk-form-item :label="t('文档类型')" :label-width="120">
        <bk-button-group>
          <bk-radio-group v-model="docType">
            <bk-button
              class="ag-type-button"
              :selected="docType === 'archive'">
              <bk-radio label="archive" class="ag-type-radio">
                <div class="pl20">
                  <div class="ag-type-name" :class="{ 'default-c': docType === 'archive' }">
                    {{ t('压缩包') }}
                  </div>
                  <div class="ag-type-spec pt5" :class="{ 'default-c': docType === 'archive' }">
                    {{ t('支持 tgz, zip 压缩格式') }}
                  </div>
                </div>
              </bk-radio>
            </bk-button>
            <bk-button
              class="ag-type-button"
              :selected="docType === 'swagger'">
              <bk-radio label="swagger" class="ag-type-radio">
                <div class="pl20">
                  <div class="ag-type-name" :class="{ 'default-c': docType === 'swagger' }">
                    Swagger
                  </div>
                  <div class="ag-type-spec pt5" :class="{ 'default-c': docType === 'swagger' }">
                    {{ t('支持 json, yaml 格式') }}
                  </div>
                </div>
              </bk-radio>
            </bk-button>
          </bk-radio-group>
        </bk-button-group>
      </bk-form-item>
      <bk-form-item :label="t('文档语言')" :label-width="120" v-if="docType === 'swagger'">
        <bk-radio-group v-model="language">
          <bk-radio label="zh">{{ t('中文文档') }}</bk-radio>
          <bk-radio label="en">{{ t('英文文档') }}</bk-radio>
        </bk-radio-group>
      </bk-form-item>
      <bk-form-item :label="t('上传文件')" :label-width="120">
        <div class="flex-row align-items-center justify-content-between" v-if="docType === 'swagger'">
          <bk-upload
            theme="button"
            :custom-request="handleReq"
            class="upload-cls"
            accept=".yaml,.json,.yml"
          >
            <template #default>
              <div>
                <i class="icon apigateway-icon icon-ag-add-small"></i>
                {{ t('导入 Swagger 文件') }}
              </div>
            </template>
          </bk-upload>
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
        <bk-upload
          v-else
          theme="button"
          with-credentials
          :url="`${BK_DASHBOARD_URL}/gateways/${apigwId}/docs/archive/parse/`"
          class="upload-cls"
          name="file"
          @done="handleUploadDone"
          @progress="handleUploadSuccess"
          :header="{ name: 'X-CSRFToken', value: CSRFToken }"
        >
          <template #default>
            <div>
              <i class="icon apigateway-icon icon-ag-add-small"></i>
              {{ t('导入文档压缩包') }}
            </div>
          </template>
        </bk-upload>
      </bk-form-item>

      <bk-form-item :label-width="120">
        <div class="monacoEditor" v-if="docType === 'swagger'">
          <editor-monaco v-model="editorText" ref="resourceEditorRef" />
        </div>
      </bk-form-item>
    </bk-form>

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
          <!-- <span v-if="showDoc">
            ，{{ $t('资源文档：') }}
            <span class="add-info">{{ t('新建') }}<span class="ag-strong success pl5 pr5">1</span>{{ t('条') }}</span>
            <span class="add-info">{{ t('覆盖') }}<span class="ag-strong danger pl5 pr5">1</span>{{ t('条') }}</span>
          </span> -->
        </div>
      </div>
      <bk-table
        class="table-layout"
        :data="tableData"
        show-overflow-tooltip
        :checked="checkData"
        :is-row-select-enable="isRowSelectEnable"
        :row-class="getRowClass"
        @selection-change="handleSelectionChange"
      >
        <bk-table-column
          width="80"
          type="selection"
          align="center"
          :explain="{ content: (col: any, row: any) => getColExplainContent(row) }"
        />
        <bk-table-column
          v-if="docType === 'archive'"
          :label="t('文件名称')"
          prop="filename"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('请求方法')"
        >
          <template #default="{ data }">
            <span v-if="data?.method">{{ data?.method }}</span>
            <span v-else>--</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('请求路径')"
        >
          <template #default="{ data }">
            <span v-if="data?.path">{{ data?.path }}</span>
            <span v-else>--</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('描述')"
          prop="description"
        >
          <template #default="{ data }">
            <span v-if="data?.description">{{ data?.description }}</span>
            <span v-else>--</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('资源操作类型')"
          prop="path"
        >
          <template #default="{ data }">
            <!--  若是没匹配到资源，给出提示  -->
            <!-- 若导入的是 zip -->
            <template v-if="docType === 'archive'">
              <span v-if="!data?.resource" class="warning-c">{{ t('未匹配到资源') }}</span>
              <template v-else>
                <span class="danger-c" v-if="!!data?.resource_doc">{{ t('覆盖') }}</span>
                <span class="success-c" v-else>{{ t('新建') }}</span>
              </template>
            </template>
            <!-- 若导入方式是自行编辑的 yaml -->
            <template v-else>
              <span v-if="!data?.id" class="warning-c">{{ t('未匹配到资源') }}</span>
              <template v-else>
                <span class="danger-c" v-if="hasExistedDoc(data)">{{ t('覆盖') }}</span>
                <span class="success-c" v-else>{{ t('新建') }}</span>
              </template>
            </template>
          </template>
        </bk-table-column>
      </bk-table>
    </section>

    <div
      class="mt15" :class="curView === 'import' ? 'btn-container' : ''"
      v-if="docType === 'swagger' || curView === 'resources'">
      <bk-button
        class="mr8"
        :theme="curView === 'import' ? 'primary' : ''"
        @click="handleCheckData"
        :loading="isDataLoading"
      >
        {{ curView === 'import' ? t('下一步') : t('上一步') }}
      </bk-button>
      <span v-bk-tooltips="{ content: t('请确认勾选资源'), disabled: selections.length }" v-if="curView === 'resources'">
        <bk-button
          class="mr8"
          theme="primary"
          type="button"
          :disabled="!selections.length"
          @click="handleImportDoc" :loading="isImportLoading">
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
import { ref, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';

import editorMonaco from '@/components/ag-editor.vue';
import { getStrFromFile } from '@/common/util';
import { checkResourceImport, importResourceDoc, importResourceDocSwagger } from '@/http';
import exampleData from '@/constant/example-data';
import { useCommon } from '@/store';
import cookie from 'cookie';
import { useSelection, useGetGlobalProperties } from '@/hooks';
import TmplExampleSideslider from '@/views/resource/setting/comps/tmpl-example-sideslider.vue';
import { UploadFile } from 'bkui-vue/lib/upload/upload.type';

interface IFile extends UploadFile {
  response?: {
    data: {
      resource: object,
      resource_doc: object,
    }[]
  }
}

const { t } = useI18n();
const common = useCommon();
const router = useRouter();

// checkbox hooks
const {
  selections,
  handleSelectionChange,
} = useSelection();
const { apigwId } = common; // 网关id
const docType = ref<string>('archive');
const curView = ref<string>('import'); // 当前页面
const tableData = ref<any[]>([]);
const checkData = ref<any[]>([]);
const language = ref<string>('zh');
const isDataLoading = ref<boolean>(false);
const isImportLoading = ref<boolean>(false);
const editorText = ref<string>(exampleData.content);
const zipFile = ref<any>('');
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>(); // 实例化
const { BK_DASHBOARD_URL } = window;
const CSRFToken = cookie.parse(document.cookie)[window.BK_DASHBOARD_CSRF_COOKIE_NAME];
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

// 设置editor的内容
const setEditValue = () => {
  nextTick(() => {
    resourceEditorRef.value?.setValue(editorText.value);
  });
};

// 拿不到上传成功的success的事件先用progress代替
const handleUploadSuccess = async (e: any, file: any) => {
  zipFile.value = file;
};

// 上传完成的方法
const handleUploadDone = async (fileList: IFile[]) => {
  const file = fileList[fileList.length - 1];
  if (!file.response) {
    return Message({ theme: 'error', message: t('上传失败') });
  }
  const res = file.response.data;
  const data = res.map(e => ({ ...e, ...e.resource, ...e.resource_doc }));
  tableData.value = data;
  checkData.value = data.filter(e => !!e.resource); // 有资源文档的才默认选中
  curView.value = 'resources';
  nextTick(() => {
    selections.value = JSON.parse(JSON.stringify(checkData.value));
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
      doc_language: language.value,
    };
    const res = await checkResourceImport(apigwId, parmas);
    tableData.value = res;
    curView.value = 'resources';
    checkData.value = tableData.value;
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
const handleImportDoc = async () => {
  try {
    isImportLoading.value = true;
    // swagger需要的参数
    const resourceDocs = selections.value.map((e: any) => ({
      language: e.language || e.doc?.language,
      resource_name: e.resource?.name || e.name,
    }));
    // 压缩包需要的参数
    const formData = new FormData();
    formData.append('file', zipFile.value);
    // formData.append('selected_resource_docs', JSON.stringify(selections.value));
    formData.append('selected_resource_docs', JSON.stringify(resourceDocs));
    const paramsSwagger = {
      swagger: editorText.value,
      selected_resource_docs: resourceDocs,
      language: language.value,
    };
    const params = docType.value === 'archive' ? formData : paramsSwagger;
    const fetchUrl: any = docType.value === 'archive' ? importResourceDoc : importResourceDocSwagger;
    const message = docType.value === 'archive' ? '资源文档' : '资源';
    await fetchUrl(apigwId, params);
    Message({
      theme: 'success',
      message: t(`${message}导入成功`),
    });
    isImportLoading.value = false;
    goBack();
  } catch {
    isImportLoading.value = false;
  }
};

// 没有资源不能导入
const isRowSelectEnable = (data: any) => {
  // console.log('row', data);
  if (docType.value === 'swagger') return true; // 如果是swagger 则可以选择
  return !!data?.row.resource;
};

// 获取 checkbox 悬浮时的文本
const getColExplainContent = (row: any) => {
  if (docType.value !== 'swagger' && !row?.resource) {
    return t('文件名需要跟资源名称完全一致才能导入，请检查文件名');
  }
  return t('已匹配到资源');
};

// 为不能选中的行添加类名
const getRowClass = (data: any) => {
  if (docType.value !== 'swagger' && !data?.resource) return 'row-disabled';
};

// 取消返回到资源列表
const goBack = () => {
  router.push({
    name: 'apigwResource',
  });
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

const isShowExample = ref(false);
const handleShowExample = () => {
  isShowExample.value = true;
};

const handleHiddenExample = () => {
  isShowExample.value = false;
};

const hasExistedDoc = (data?: { doc?: { id: number, language: string }[] }) => {
  if (!data?.doc?.length) {
    return false;
  }

  return data.doc.find(item => item.language === language.value)?.id;
};

</script>
<style scoped lang="scss">
.import-docs-container{
  .ag-type-button{
    height: auto;
    text-align: left;
    .ag-type-radio{
      width: 240px;
      padding: 5px 0;
    }
    .ag-type-name{
      font-size: 12px;
      font-weight: bold;
    }
    .ag-type-spec {
      font-size: 12px;
    }
  }
  .is-selected{
    background-color: #f6f9ff;
    border-color: #3a84ff;
    color: #3a84ff !important;
    position: relative;
    z-index: 1;
  }

  .monacoEditor {
    width: 100%;
    height: calc(100vh - 400px);
  }

  .btn-container{
    margin-left: 120px;
  }

  :deep(.upload-cls) {
    .bk-upload-list{
      display: none !important;
    }
  }

  // 不能被选中的表格行的样式
  :deep(.row-disabled) {
    td {
      background-color: #fafbfd;
    }
  }
}
</style>
