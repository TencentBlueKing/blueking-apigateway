<template>
  <div class="import-docs-container p-20px">
    <BkForm
      v-if="curView === 'import'"
      :label-width="100"
    >
      <BkFormItem
        :label="t('文档类型')"
        :label-width="120"
      >
        <BkButtonGroup>
          <BkRadioGroup v-model="docType">
            <BkButton
              class="ag-type-button"
              :selected="docType === 'archive'"
            >
              <BkRadio
                label="archive"
                class="ag-type-radio"
              >
                <div class="pl-20px">
                  <div
                    class="ag-type-name"
                    :class="{ 'color-#3A84FF': docType === 'archive' }"
                  >
                    {{ t('压缩包') }}
                  </div>
                  <div
                    class="ag-type-spec pt-5px"
                    :class="{ 'color-#3A84FF': docType === 'archive' }"
                  >
                    {{ t('支持 tgz, zip 压缩格式') }}
                  </div>
                </div>
              </BkRadio>
            </BkButton>
            <BkButton
              class="ag-type-button"
              :selected="docType === 'swagger'"
            >
              <BkRadio
                label="swagger"
                class="ag-type-radio"
              >
                <div class="pl-20px">
                  <div
                    class="ag-type-name"
                    :class="{ 'color-#3A84FF': docType === 'swagger' }"
                  >
                    Swagger
                  </div>
                  <div
                    class="ag-type-spec pt-5px"
                    :class="{ 'color-#3A84FF': docType === 'swagger' }"
                  >
                    {{ t('支持 json, yaml 格式') }}
                  </div>
                </div>
              </BkRadio>
            </BkButton>
          </BkRadioGroup>
        </BkButtonGroup>
      </BkFormItem>
      <BkFormItem
        v-if="docType === 'swagger'"
        :label="t('文档语言')"
        :label-width="120"
      >
        <BkRadioGroup v-model="language">
          <BkRadio label="zh">
            {{ t('中文文档') }}
          </BkRadio>
          <BkRadio label="en">
            {{ t('英文文档') }}
          </BkRadio>
        </BkRadioGroup>
      </BkFormItem>
      <BkFormItem
        :label="t('上传文件')"
        :label-width="120"
      >
        <div
          v-if="docType === 'swagger'"
          class="flex items-center justify-between"
        >
          <BkUpload
            theme="button"
            :custom-request="handleReq"
            class="upload-cls"
            accept=".yaml,.json,.yml"
          >
            <template #default>
              <div>
                <AgIcon
                  name="add-small"
                  class="icon"
                />
                {{ t('导入 Swagger 文件') }}
              </div>
            </template>
          </BkUpload>
          <div class="flex items-center">
            <BkButton
              theme="primary"
              text
              @click="handleShowExample"
            >
              {{ t('模板示例') }}
            </BkButton>
            <BkLink
              theme="primary"
              class="pl-10px"
              :href="envStore.swaggerDocURL"
              target="_blank"
            >
              <AgIcon name="info" />
              {{ t('Swagger 说明文档') }}
            </BkLink>
          </div>
        </div>
        <BkUpload
          v-else
          theme="button"
          with-credentials
          :url="`${envStore.env.BK_DASHBOARD_URL}/gateways/${gatewayId}/docs/archive/parse/`"
          class="upload-cls"
          name="file"
          :header="{ name: 'X-CSRFToken', value: CSRFToken }"
          @done="handleUploadDone"
          @progress="handleUploadSuccess"
        >
          <template #default>
            <div>
              <AgIcon
                name="add-small"
                class="icon"
              />
              {{ t('导入文档压缩包') }}
            </div>
          </template>
        </BkUpload>
      </BkFormItem>

      <BkFormItem :label-width="120">
        <div
          v-if="docType === 'swagger'"
          class="monaco-editor-wrapper"
        >
          <editor-monaco
            ref="resourceEditorRef"
            v-model="editorText"
          />
        </div>
      </BkFormItem>
    </BkForm>

    <section v-else>
      <div class="flex justify-between">
        <div class="info">
          {{ t('请确认以下资源变更，资源配置：') }}
          <span class="add-info">{{ t('新建') }}
            <span class="font-bold color-#2dcb56 px-5px">
              {{ createNum }}
            </span>{{ t('条') }}
          </span>
          <span class="add-info">{{ t('覆盖') }}
            <span class="font-bold color-#ea3636 px-5px">{{ updateNum }}</span>
            {{ t('条') }}
          </span>
          <!-- <span v-if="showDoc">
            ，{{ t('资源文档：') }}
            <span class="add-info">{{ t('新建') }}<span class="font-bold color-#2dcb56 px-5px">1</span>{{ t('条') }}</span>
            <span class="add-info">{{ t('覆盖') }}<span class="font-bold color-#ea3636 px-5px">1</span>{{ t('条') }}</span>
            </span> -->
        </div>
      </div>
      <BkTable
        class="table-layout"
        :data="tableData"
        show-overflow-tooltip
        :checked="checkData"
        :is-row-select-enable="isRowSelectEnable"
        :row-class="getRowClass"
        @selection-change="handleSelectionChange"
      >
        <BkTableColumn
          width="80"
          type="selection"
          align="center"
          :explain="{ content: (col: any, row: any) => getColExplainContent(row) }"
        />
        <BkTableColumn
          v-if="docType === 'archive'"
          :label="t('文件名称')"
          prop="filename"
        />
        <BkTableColumn
          :label="t('请求方法')"
        >
          <template #default="{ data }">
            <span v-if="data?.method">{{ data?.method }}</span>
            <span v-else>--</span>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('请求路径')"
        >
          <template #default="{ data }">
            <span v-if="data?.path">{{ data?.path }}</span>
            <span v-else>--</span>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('描述')"
          prop="description"
        >
          <template #default="{ data }">
            <span v-if="data?.description">{{ data?.description }}</span>
            <span v-else>--</span>
          </template>
        </BkTableColumn>
        <BkTableColumn
          :label="t('资源操作类型')"
          prop="path"
        >
          <template #default="{ data }">
            <!--  若是没匹配到资源，给出提示  -->
            <!-- 若导入的是 zip -->
            <template v-if="docType === 'archive'">
              <span
                v-if="!data?.resource"
                class="color-#ff9c01"
              >{{ t('未匹配到资源') }}</span>
              <template v-else>
                <span
                  v-if="!!data?.resource_doc"
                  class="color-#ea3636"
                >{{ t('覆盖') }}</span>
                <span
                  v-else
                  class="color-#2dcb56"
                >{{ t('新建') }}</span>
              </template>
            </template>
            <!-- 若导入方式是自行编辑的 yaml -->
            <template v-else>
              <span
                v-if="!data?.id"
                class="color-#ff9c01"
              >{{ t('未匹配到资源') }}</span>
              <template v-else>
                <span
                  v-if="hasExistedDoc(data)"
                  class="color-#ea3636"
                >{{ t('覆盖') }}</span>
                <span
                  v-else
                  class="color-#2dcb56"
                >{{ t('新建') }}</span>
              </template>
            </template>
          </template>
        </BkTableColumn>
      </BkTable>
    </section>

    <div
      v-if="docType === 'swagger' || curView === 'resources'"
      class="mt-15px"
      :class="curView === 'import' ? 'btn-container' : ''"
    >
      <BkButton
        class="mr-8px"
        :theme="curView === 'import' ? 'primary' : ''"
        :loading="isDataLoading"
        @click="handleCheckData"
      >
        {{ curView === 'import' ? t('下一步') : t('上一步') }}
      </BkButton>
      <span
        v-if="curView === 'resources'"
        v-bk-tooltips="{ content: t('请确认勾选资源'), disabled: selections.length }"
      >
        <BkButton
          class="mr-8px"
          theme="primary"
          type="button"
          :disabled="!selections.length"
          :loading="isImportLoading"
          @click="handleImportDoc"
        >
          {{ t('确定导入') }}
        </BkButton>
      </span>
      <BkButton @click="goBack">
        {{ t('取消') }}
      </BkButton>
    </div>

    <TmplExampleSideslider
      :is-show="isShowExample"
      @on-hidden="handleHiddenExample"
    />
  </div>
</template>

<script setup lang="ts">
import { Message } from 'bkui-vue';
import editorMonaco from '@/components/ag-editor/Index.vue';
import { getStrFromFile } from '@/utils';
import {
  checkResourceImport,
  importResourceDoc,
  importResourceDocSwagger,
} from '@/services/source/resource';
import { RESOURCE_IMPORT_EXAMPLE } from '@/constants';
import { useSelection } from '@/hooks';
import TmplExampleSideslider from '../components/TmplExampleSideslider.vue';
import { type UploadFile } from 'bkui-vue/lib/upload/upload.type';
import Cookie from 'js-cookie';
import { useEnv } from '@/stores';

interface IFile extends UploadFile {
  response?: {
    data: {
      resource: object
      resource_doc: object
    }[]
  }
}

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();
const envStore = useEnv();

// checkbox hooks
const {
  selections,
  handleSelectionChange,
} = useSelection();

const docType = ref('archive');
const curView = ref('import'); // 当前页面
const tableData = ref<any[]>([]);
const checkData = ref<any[]>([]);
const language = ref('zh');
const isDataLoading = ref(false);
const isImportLoading = ref(false);
const editorText = ref<string>(RESOURCE_IMPORT_EXAMPLE.content);
const zipFile = ref<any>('');
const resourceEditorRef = ref<InstanceType<typeof editorMonaco>>(); // 实例化

const CSRFToken = Cookie.get('bk_apigw_dashboard_csrftoken');

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
    return Message({
      theme: 'error',
      message: t('上传失败'),
    });
  }
  const res = file.response.data;
  const data = res.map(e => ({
    ...e,
    ...e.resource,
    ...e.resource_doc,
  }));
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
    const res = await checkResourceImport(gatewayId, parmas);
    tableData.value = res;
    curView.value = 'resources';
    checkData.value = tableData.value;
    nextTick(() => {
      selections.value = JSON.parse(JSON.stringify(tableData.value));
    });
    // resetSelections();
  }
  finally {
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
    await fetchUrl(gatewayId, params);
    Message({
      theme: 'success',
      message: t(`${message}导入成功`),
    });
    isImportLoading.value = false;
    goBack();
  }
  catch {
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
  router.push({ name: 'apigwResource' });
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

const hasExistedDoc = (data?: {
  doc?: {
    id: number
    language: string
  }[]
}) => {
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
    position: relative;
    z-index: 1;
    color: #3a84ff !important;
    background-color: #f6f9ff;
    border-color: #3a84ff;
  }

  .monaco-editor-wrapper {
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
