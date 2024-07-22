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
              <!--  顶部编辑器工具栏-->
              <header class="editorToolbar">
                <span class="p10" style="color: #ccc">代码编辑器</span>
                <aside class="toolItems">
                  <section class="toolItem" :class="{ 'active': isFindPanelVisible }" @click="toggleFindToolClick()">
                    <search width="18px" height="18px" />
                  </section>
<!--                  <section class="toolItem">-->
<!--                    <upload width="18px" height="18px" />-->
<!--                  </section>-->
                  <section class="toolItem">
                    <filliscreen-line width="18px" height="18px" />
                  </section>
                </aside>
              </header>
              <main class="editorMainContent">
                <!--  编辑器本体  -->
                <editor-monaco v-model="editorText" ref="resourceEditorRef" @findStateChanged="(isVisible) => { isFindPanelVisible = isVisible; }" />
                <!--  右侧的代码 error, warning 计数器  -->
                <aside class="editorErrorCounters">
                  <div
                    class="errorCountItem" :class="{ 'active': activeCodeMsgType === 'Error' }"
                    v-bk-tooltips="{ content: `Error: ${msgAsErrorNum}`, placement: 'left' }"
                    @click="handleErrorCountClick('Error')"
                  >
                    <warn fill="#EA3636" />
                    <span style="color:#EA3636">{{ msgAsErrorNum }}</span>
                  </div>
                  <div
                    class="errorCountItem" :class="{ 'active': activeCodeMsgType === 'Warning' }"
                    v-bk-tooltips="{ content: `Warning: ${msgAsWarningNum}`, placement: 'left' }"
                    @click="handleErrorCountClick('Warning')"
                  >
                    <div class="warningCircle"></div>
                    <span style="color: hsla(36.6, 81.7%, 55.1%, 0.5);">{{ msgAsWarningNum }}</span>
                  </div>
                  <div
                    class="errorCountItem" :class="{ 'active': activeCodeMsgType === 'All' }"
                    v-bk-tooltips="{ content: `All: ${errorReasons.length}`, placement: 'left' }"
                    @click="handleErrorCountClick('All')"
                  >
                    <span>all</span>
                    <span>{{ msgAsErrorNum + msgAsWarningNum }}</span>
                  </div>
                </aside>
              </main>
            </div>
          </template>
          <!--  底部错误信息展示  -->
          <template #aside>
            <div class="editorMessagesWrapper" :class="{ 'hasErrorMsg': visibleErrorReasons.length > 0 }">
              <article
                v-for="(reason, index) in visibleErrorReasons" :key="index" class="editorMessage"
                @click="handleErrorMsgClick(reason)"
              >
                <span class="msgPart msgIcon"><warn fill="#EA3636" /></span>
                <span class="msgPart msgHost"></span>
                <span class="msgPart msgBody">{{ reason.message }}</span>
                <span class="msgPart msgErrorCode"></span>
                <span v-if="reason.position" class="msgPart msgPos">
                  {{ `(${reason.position.lineNumber}, ${reason.position.column})` }}
                </span>
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
        :disabled="curView === 'import' && !isCodeValid"
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
import {
  ref,
  nextTick,
  computed,
  watch,
} from 'vue';
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

import type { IPosition } from 'monaco-editor';
import type { ErrorReasonType, CodeErrorMsgType } from '@/types/common';

type CodeErrorResponse = {
  code: string,
  data: { json_path: string, message: string }[],
  details: any[],
  message: string,
};

const router = useRouter();
const { t } = useI18n();
const common = useCommon();
const editorText = ref<string>(exampleData.content);
const { apigwId } = common; // 网关id
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>(); // 实例化
const showDoc = ref<boolean>(false);
const language = ref<string>('zh');
const isDataLoading = ref<boolean>(false);
const isCodeValid = ref<boolean>(false);
const isImportLoading = ref<boolean>(false);
const curView = ref<string>('import'); // 当前页面
const tableData = ref<any[]>([]);
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

// 选中的代码错误提示 Tab，默认展示 all 即全部类型的错误提示
const activeCodeMsgType = ref<CodeErrorMsgType>('All');
// 记录代码错误消息
const errorReasons = ref<ErrorReasonType[]>([]);
const isFindPanelVisible = ref(false);

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

// 可视的错误消息，实际要渲染到编辑器视图的数据
const visibleErrorReasons = computed(() => {
  if (activeCodeMsgType.value === 'All') return errorReasons.value;

  if (activeCodeMsgType.value === 'Error') {
    return errorReasons.value.filter(r => r.level === 'Error');
  }

  if (activeCodeMsgType.value === 'Warning') {
    return errorReasons.value.filter(r => r.level === 'Warning');
  }
  return [];
});

const msgAsErrorNum = computed(() => {
  return errorReasons.value.filter(r => r.level === 'Error').length;
});

const msgAsWarningNum = computed(() => {
  return errorReasons.value.filter(r => r.level === 'Warning').length;
});

// 防抖的代码校验
const debouncedCheckData = _.debounce((args) => {
  handleCheckData(args);
}, 1000);

// 代码有变化时自动校验
watch(editorText, () => {
  debouncedCheckData({ changeView: false });
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
const handleCheckData = async ({ changeView = true } = { changeView: true }) => {
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
    isCodeValid.value = true;
    resourceEditorRef.value.clearDecorations();
    errorReasons.value = [];
    // 判断是否跳转，默认为是
    if (changeView) {
      curView.value = 'resources';
      nextTick(() => {
        selections.value = JSON.parse(JSON.stringify(tableData.value));
      });
    }
    // resetSelections();
  } catch (err: unknown) {  // 校验失败会走到这里
    // console.log(error);
    isCodeValid.value = false;
    const error = err as CodeErrorResponse;
    // 如果是内容错误
    if (error?.code === 'INVALID' && error?.message === 'validate fail') {
      const editorJsonObj = yaml.load(editorText.value) as object;
      const errData: { json_path: string, message: string }[] = error.data ?? [];
      errorReasons.value = errData.map((err) => {
        // 从 jsonpath 提取路径组成数组，去掉开头的 $
        const paths = JSONPath.toPathArray(err.json_path)
          .slice(1);
        // 找到 jsonpath 指向的值
        const pathValue = JSONPath(err.json_path, editorJsonObj, null, null)[0] ?? [];
        // 提取后端错误消息中第一个用引号包起来的字符串，它常常就是代码错误所在
        const quotedValue = getFirstQuotedValue(err.message);
        const stringToFind = '';
        // jsonpath 指向的键名
        const lastPath = paths[paths.length - 1];
        // 记录正则匹配到的起始位置，从 0 开始，没有匹配项时为 -1
        let offset = -1;
        // 用于搜索的正则
        let regex: RegExp | null = null;
        // 匹配项在 editor 中的 Position
        let position: IPosition | null = null;
        // 生成用于搜索 jsonpath 所在行的正则
        // 判断 jsonpath 指向的是否为数组成员，是的话不传入 key
        if (Number.isInteger(Number.parseInt(lastPath, 10))) {
          regex = getRegexFromObj({ objValue: pathValue });
        } else {
          regex = getRegexFromObj({ objKey: lastPath, objValue: pathValue });
        }
        offset = resourceEditorRef.value.getValue()
          .search(regex);
        // 用 editor 的 api 找到 Position
        if (offset > -1) {
          position = resourceEditorRef.value.getModel().getPositionAt(offset);
        }
        return {
          paths,
          quotedValue,
          pathValue,
          stringToFind,
          offset,
          regex,
          position,
          json_path: err.json_path,
          message: err.message,
          isDecorated: false,
          level: 'Error',
        };
      });
      console.log(errorReasons.value);
      updateEditorDecorations();
    }
    // }
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

// 触发编辑器高亮
const updateEditorDecorations = () => {
  resourceEditorRef.value.clearDecorations();
  resourceEditorRef.value.genLineDecorations(visibleErrorReasons.value.map(r => ({
    position: r.position,
    level: r.level,
  })));
  resourceEditorRef.value.setDecorations();
};

// 处理代码错误消息点击事件，应跳转到编辑器对应行
const handleErrorMsgClick = (reason: ErrorReasonType) => {
  resourceEditorRef.value.setCursorPos(reason.position);
};

// 从把 jsonpath 指向的对象转换成正则
const getRegexFromObj = ({ objKey, objValue }: { objKey?: string, objValue: any }): RegExp => {
  let exp = '';
  if (objKey) {
    exp = `\\b${objKey}\\b:[\\s\\S\\n\\r]*?`;
  }
  Object.entries(objValue)
    .forEach((e) => {
      exp += `\\b${e[0]}\\b[\\s\\S\\n\\r]*?`;
      if (!_.isObject(e[1])) {
        exp += `${e[1]}[\\s\\S\\n\\r]*?`;
      }
    });
  return new RegExp(exp, 'gm');
};

// 获取字符串中第一个被 '' 包裹的值
const getFirstQuotedValue = (str: string) => {
  const match = str.match(/'([^']*)'/);
  return match ? match[1] : null;
};

// 处理右侧错误类型计数器点击事件
const handleErrorCountClick = (type: CodeErrorMsgType) => {
  activeCodeMsgType.value = type;
  updateEditorDecorations();
};

// 切换搜索面板
const toggleFindToolClick = () => {
  if (isFindPanelVisible.value) {
    resourceEditorRef.value.closeFindPanel();
  } else {
    resourceEditorRef.value.showFindPanel();
  }
}
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

          &.active, &:hover {
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
        border-left: 4px solid #B34747;
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

  // 编辑器错误行高亮样式
  :deep(.lineHighlightError) {
    background-color: #382322;
    opacity: .7;
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
