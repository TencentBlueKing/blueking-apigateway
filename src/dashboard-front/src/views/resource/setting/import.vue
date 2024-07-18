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
      <!-- 代码编辑器 -->
      <div class="monacoEditor mt10">
        <bk-resize-layout placement="bottom" collapsible immediate style="height: 100%">
          <template #main>
            <div style="height: 100%">
              <!--   编辑器工具栏-->
              <header class="editorToolbar">
                <span class="p10" style="color: #ccc">代码编辑器</span>
                <aside class="toolItems">
                  <section class="toolItem">
                    <search width="18px" height="18px" />
                  </section>
                  <section class="toolItem">
                    <upload width="18px" height="18px" />
                  </section>
                  <section class="toolItem">
                    <filliscreen-line width="18px" height="18px" />
                  </section>
                </aside>
              </header>
              <main class="editorMainContent">
                <!--  编辑器本体  -->
                <editor-monaco v-model="editorText" ref="resourceEditorRef" />
                <!--  右侧的代码 error, warning 计数器  -->
                <aside class="editorErrorCounters">
                  <div
                    class="errorCountItem" :class="{ 'active': activeCodeMsgType === 'error' }"
                    v-bk-tooltips="{ content: 'Error: 6', placement: 'left' }"
                    @click="handleErrorCountClick('error')"
                  >
                    <warn fill="#EA3636" />
                    <span style="color:#EA3636">6</span>
                  </div>
                  <div
                    class="errorCountItem" :class="{ 'active': activeCodeMsgType === 'warning' }"
                    v-bk-tooltips="{ content: 'Warning: 2', placement: 'left' }"
                    @click="handleErrorCountClick('warning')"
                  >
                    <div class="warningCircle"></div>
                    <span style="color: hsla(36.6, 81.7%, 55.1%, 0.5);">2</span>
                  </div>
                  <div
                    class="errorCountItem" :class="{ 'active': activeCodeMsgType === 'all' }"
                    v-bk-tooltips="{ content: 'All: 8', placement: 'left' }"
                    @click="handleErrorCountClick('all')"
                  >
                    <span>all</span>
                    <span>8</span>
                  </div>
                </aside>
              </main>
            </div>
          </template>
          <!--  底部错误信息展示  -->
          <template #aside>
            <div class="editorMessagesWrapper">
              <article
                v-for="(reason, index) in errorReasons" :key="index" class="editorMessage"
                @click="handleErrorMsgClick(reason)"
              >
                <span class="msgPart msgIcon"><warn fill="#EA3636" /></span>
                <span class="msgPart msgHost"></span>
                <span class="msgPart msgBody">{{ reason.message }}</span>
                <span class="msgPart msgErrorCode"></span>
                <span class="msgPart msgPos"></span>
              </article>
            </div>
          </template>
        </bk-resize-layout>
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
      <span
        v-bk-tooltips="{ content: t('请确认勾选资源'), disabled: selections.length }"
        v-if="curView === 'resources'"
      >
        <bk-button
          class="mr10"
          theme="primary"
          type="button"
          :disabled="!selections.length"
          @click="handleImportResource" :loading="isImportLoading"
        >
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
import { ref, nextTick, computed, onMounted } from 'vue';
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
import { Warn, Search, FilliscreenLine, Upload } from 'bkui-vue/lib/icon';
import yaml from 'js-yaml';
import { JSONPath } from 'jsonpath-plus';
import _ from 'lodash';

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

type codeErrorMsgType = 'all' | 'error' | 'warning';
type errorReasonType = {
  json_path: string,
  paths: string[],
  quotedValue: string,
  pathValues: any[],
  message: string,
  isDecorated: boolean,
};

// 选中的代码错误提示 Tab，默认展示 all 即全部类型的错误提示
const activeCodeMsgType = ref<codeErrorMsgType>('all');
// 记录代码错误消息
const errorReasons = ref<errorReasonType[]>([]);

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
  getStrFromFile(file)
    .then((res: any) => {
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
    const params: any = {
      content: editorText.value,
      allow_overwrite: true,
    };
    // 如果勾选了资源文档
    if (showDoc.value) {
      params.doc_language = language.value;
    }
    tableData.value = await checkResourceImport(apigwId, params);
    curView.value = 'resources';
    nextTick(() => {
      selections.value = JSON.parse(JSON.stringify(tableData.value));
    });
    // resetSelections();
  } catch (error) {  // 校验失败会走到这里
    // TODO 处理校验失败
    // console.log(error);
    // 如果是内容错误
    if (error?.code === 'INVALID' && error?.message === 'validate fail') {
      const jsonData = yaml.load(editorText.value) as object;
      const errData: { json_path: string, message: string }[] = error.data ?? [];
      errorReasons.value = errData.map(err => ({
        json_path: err.json_path,
        paths: JSONPath.toPathArray(err.json_path)
          .slice(1),
        quotedValue: getFirstQuotedValue(err.message),
        pathValues: JSONPath(err.json_path, jsonData, () => {
        }, () => {
        })[0] || [],
        message: err.message,
        isDecorated: false,
      }));
      // console.log(errorReasons.value);
      // errorReasons.value.forEach((r) => {
      //   console.log(getStringToFind(r));
      // });
    }
  } finally {
    isDataLoading.value = false;
  }
};

// 确认导入
const handleImportResource = async () => {
  try {
    isImportLoading.value = true;
    const params = {
      content: editorText.value,
      selected_resources: selections.value,
    };
    await importResource(apigwId, params);
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

// 处理代码错误消息点击事件，应跳转到编辑器对应行
const handleErrorMsgClick = (reason: errorReasonType) => {
  const stringToFind = getStringToFind(reason);
  console.log(stringToFind);
  const lineNumber = resourceEditorRef.value.getModel()
    .findMatches(stringToFind, true, false, true, null, true)[0].range.startLineNumber;
  console.log(stringToFind);
  console.log(lineNumber);
  resourceEditorRef.value.setCursorPos({ lineNumber });
};

// 处理右侧错误类型计数器点击事件
const handleErrorCountClick = (type: codeErrorMsgType) => {
  activeCodeMsgType.value = type;
//   TODO 更新错误提示视图
};

// 获取字符串中第一个被 '' 包裹的值
const getFirstQuotedValue = (str: string) => {
  const match = str.match(/'([^']*)'/);
  return match ? match[1] : null;
};

// 从报错中找到要拿去编辑器搜索的字符串
const getStringToFind = (reason: errorReasonType) => {
  const { pathValues, quotedValue } = reason;
  const lastPath = reason.paths[reason.paths.length - 1];
  if (_.isObjectLike(pathValues)) {
    if (_.isObject(pathValues)) {
      if (quotedValue in pathValues) {
        return quotedValue;
      }
      return lastPath;
    }
    if (Array.isArray(pathValues) && _.includes(pathValues, quotedValue)) {
      return quotedValue;
    }
    return lastPath;
  }
  if (lastPath !== quotedValue) {
    return lastPath;
  }
  return quotedValue;
};

onMounted(() => {
  resourceEditorRef.value.genDecorations({ startLineNumber: 3, startColumn: 1, endLineNumber: 5, level: 'Warning' });
  resourceEditorRef.value.setDecorations();
});
</script>
<style scoped lang="scss">
.import-container {
  .import-header {
    .icon-ag-add-small {
      font-size: 16px;
    }

    .desc {
      font-size: 12px;
      color: #979ba5;
    }
  }

  .monacoEditor {
    width: 100%;
    height: calc(100vh - 240px);

    .editorToolbar {
      position: relative;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background-color: #1a1a1a;
      box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2);
      z-index: 6;

      .toolItems {
        height: 100%;
        display: flex;
        align-items: center;

        .toolItem {
          padding: 0 8px;
          display: flex;
          align-items: center;
          cursor: pointer;

          &:hover {
            color: #ccc;
          }
        }
      }
    }

    .editorMainContent {
      display: flex;
      height: 100%;

      .editorErrorCounters {
        width: 32px;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        background-color: #1a1a1a;

        .errorCountItem {
          height: 34px;
          width: 100%;
          border-bottom: 1px solid #222;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          line-height: 12px;
          font-size: 12px;
          cursor: pointer;

          &:last-child {
            border-bottom: none;
          }

          &:hover, &.active {
            background-color: #333;
          }
        }
      }
    }

    .editorMessagesWrapper {
      position: relative;
      height: 100%;
      padding-top: 16px;
      background-color: #1a1a1a;
      border-left: 4px solid #1a1a1a;
      font-size: 12px;

      &.hasErrorMsg {
        border-left: 4px solid #EA3636;
      }

      .editorMessage {
        height: 20px;
        padding: 0 4px 0 12px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
        cursor: pointer;

        &:hover {
          background-color: #333;
        }

        .msgIcon {
          padding-top: 3px;
          display: flex;
          align-items: center;
        }

        .msgBody {
          color: #ccc;
        }
      }
    }

    // 变更代码编辑器伸缩线样式
    :deep(.bk-resize-layout-bottom > .bk-resize-layout-aside) {
      border-top: 1px solid black;
      background: #1a1a1a;
    }

    // ResizeLayout 的折叠按钮样式
    :deep(.bk-resize-layout>.bk-resize-layout-aside .bk-resize-collapse) {
      margin-bottom: 9px;
      background: #1a1a1a;
      box-shadow: 0 0 2px 0 rgba(255, 255, 255, 0.1);
    }

    // ResizeLayout 的折叠区应允许滚动
    :deep(.bk-resize-layout>.bk-resize-layout-aside .bk-resize-layout-aside-content) {
      overflow-y: auto;
    }
  }

  :deep(.upload-cls) {
    .bk-upload-list {
      display: none !important;
    }
  }

  :deep(.lineHighlightError) {
    background-color: #382322;
  }

  :deep(.glyphMarginError) {
    width: 6px !important;
    background: #B34747;
  }

  :deep(.lineHighlightWarning) {
    background-color: hsla(36.6, 81.7%, 55.1%, 0.1);
  }

  :deep(.glyphMarginWarning) {
    width: 6px !important;
    background: hsla(36.6, 81.7%, 55.1%, 0.5);
  }

  // 让错误消息台的滚动条模仿 monaco editor 风格
  /* 整个滚动条 */
  ::-webkit-scrollbar {
    width: 14px; /* 滚动条宽度 */
  }

  /* 滚动条轨道 */
  ::-webkit-scrollbar-track {
    background: #1e1e1e;
  }

  /* 滚动条滑块 */
  ::-webkit-scrollbar-thumb {
    background: #4f4f4f;
  }

  /* 鼠标悬停时的滚动条滑块 */
  ::-webkit-scrollbar-thumb:hover {
    background: #555;
  }

  /* 鼠标按住时的滚动条滑块 */
  ::-webkit-scrollbar-thumb:active {
    background: #5e5e5e;
  }

  .warningCircle {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: hsla(36.6, 81.7%, 55.1%, 0.5);
  }
}
</style>
