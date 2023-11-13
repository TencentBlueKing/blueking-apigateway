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
                    {{ t('Swagger') }}
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
          >
            <template #default>
              <bk-button>
                <i class="icon apigateway-icon icon-ag-add-small pr10"></i>
                {{ t('导入 Swagger 文件') }}
              </bk-button>
            </template>
          </bk-upload>
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
            <bk-button>
              <i class="icon apigateway-icon icon-ag-add-small pr10"></i>
              {{ t('导入文档压缩包') }}
            </bk-button>
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
        @selection-change="handleSelectionChange"
      >
        <bk-table-column
          width="80"
          type="selection"
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
            <span class="danger-c" v-if="data?.id">{{ t('覆盖') }}</span>
            <span class="success-c" v-else>{{ t('新建') }}</span>
          </template>
        </bk-table-column>
      </bk-table>
    </section>

    <div
      class="mt15" :class="curView === 'import' ? 'btn-container' : ''"
      v-if="docType === 'swagger' || curView === 'resources'">
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
          @click="handleImportDoc" :loading="isImportLoading">
          {{ $t('确定导入') }}
        </bk-button>
      </span>
      <bk-button @click="goBack">
        {{ t('取消') }}
      </bk-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import editorMonaco from '@/components/ag-editor.vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import { getStrFromFile } from '@/common/util';
import { checkResourceImport, importResourceDoc, importResource } from '@/http';
import exampleData from '@/constant/example-data';
import { useCommon } from '@/store';
import cookie from 'cookie';
import { useSelection } from '@/hooks';
import { useRouter } from 'vue-router';

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
const CSRFToken = cookie.parse(document.cookie)[window.BK_DASHBOARD_CSRF_COOKIE_NAME || `${window.BK_PAAS_APP_ID}_csrftoken`];

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
const handleUploadDone = async (response: any) => {
  const res = response[0].response.data;
  const data = res.map((e: any) => ({ ...e, ...e.resource, ...e.resource_doc }));
  tableData.value = data;
  checkData.value = data.filter((e: any) => !!e.resource_doc); // 有资源文档的才默认选中
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
  const formData = new FormData();
  formData.append('file', zipFile.value);
  formData.append('selected_resource_docs', JSON.stringify(selections.value));

  try {
    isImportLoading.value = true;

    const paramsSwagger = {
      content: editorText.value,
      selected_resources: selections.value,
    };
    const parmas = docType.value === 'archive' ? formData : paramsSwagger;
    const fetchUrl: any = docType.value === 'archive' ? importResourceDoc : importResource;
    const message = docType.value === 'archive' ? '资源文档' : '资源';
    await fetchUrl(apigwId, parmas);
    Message({
      theme: 'success',
      message: t(`${message}导入成功`),
    });
    goBack();
  } catch (error) {} finally {
    isImportLoading.value = false;
  }
};

// 没有资源不能导入
const isRowSelectEnable = (data: any) => {
  console.log('row', data);
  if (docType.value === 'swagger') return true; // 如果是swagger 则可以选择
  return data?.row.resource_doc;
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
}
</style>
