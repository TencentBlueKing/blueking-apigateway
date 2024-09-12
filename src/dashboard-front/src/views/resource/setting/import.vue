<!-- eslint-disable max-len -->

<template>
  <div v-if="!isImportResultVisible" class="import-wrapper">
    <header class="steps-indicator-wrap">
      <main class="steps-indicator">
        <bk-steps
          :steps="[
            { title: t('校验文件') },
            { title: t('资源信息确认') },
          ]"
          :cur-step="curView === 'import' ? 1 : 2"
          theme="primary"
        />
      </main>
    </header>
    <!--  导入前视图，代码编辑器在此页  -->
    <div v-if="curView === 'import'" class="import-container">
      <div class="import-header flex-row">
        <div class="flex-row align-items-center">
          <bk-upload
            theme="button"
            :custom-request="handleReq"
            class="upload-cls"
            accept=".yaml,.json,.yml"
          >
            <div>
              <i class="icon apigateway-icon icon-ag-upload"></i>
              {{ t('上传文件') }}
            </div>
          </bk-upload>
          <span class="desc">{{ t('支持 Swagger 2.0 和 OpenAPI 3.0 规范的文件，文件格式支持 JSON、YAML') }}</span>
          <span class="desc">
            <bk-link
              theme="primary" :href="GLOBAL_CONFIG.DOC.SWAGGER" target="_blank"
              style="font-size: 12px;"
            >
              <span class="flex-row align-items-center">
                <share width="12px" height="12px" fill="#3A84FF" style="margin-right: 4px;" />{{ t('使用指引') }}
              </span>
            </bk-link>
          </span>
        </div>
        <div class="flex-row align-items-center">
          <bk-form class="flex-row">
            <bk-form-item
              class="mb0"
              :label-width="20"
            >
              <bk-checkbox v-model="showDoc" size="small">
                {{ t('生成资源文档') }}
              </bk-checkbox>
            </bk-form-item>
            <bk-form-item
              v-if="showDoc"
              class="mb0"
              :label="t('文档语言')"
              :required="true"
              :label-width="120"
            >
              <bk-radio-group v-model="language" size="small">
                <bk-radio label="zh">{{ t('中文文档') }}</bk-radio>
                <bk-radio label="en">{{ t('英文文档') }}</bk-radio>
              </bk-radio-group>
            </bk-form-item>
          </bk-form>
        </div>
        <div class="flex-row align-items-center" style="margin-left: auto;">
          <bk-button theme="primary" text style="font-size: 12px;" @click="handleShowExample">
            {{
              t('模板示例')
            }}
          </bk-button>
        </div>
      </div>
      <!-- 代码编辑器 -->
      <div class="monaco-editor" :class="{ 'hide-collapse-btn': visibleErrorReasons.length < 1 }" ref="editorWrapRef">
        <bk-resize-layout
          ref="resizeLayoutRef"
          placement="bottom"
          collapsible
          :border="false"
          :max="resizeLayoutAsideMax"
          :min="resizeLayoutAsideMin"
          style="height: 100%"
          @collapse-change="updateIsEditorMsgCollapsed"
        >
          <template #main>
            <div class="editor-layout-main">
              <!--  顶部编辑器工具栏-->
              <header class="editor-toolbar">
                <span class="p10 pl25" style="color: #ccc">{{ t('代码编辑器') }}</span>
                <aside class="tool-items">
                  <section class="tool-item" :class="{ 'active': isFindPanelVisible }" @click="toggleFindToolClick()">
                    <i class="apigateway-icon icon-ag-search f16"></i>
                  </section>
                  <section class="tool-item" @click="handleFontSizeClick()">
                    <i class="apigateway-icon icon-ag-font f16"></i>
                  </section>
                  <section class="tool-item" @click="handleFullScreenClick()">
                    <i class="apigateway-icon icon-ag-gongneng-quanping2 f16"></i>
                  </section>
                </aside>
              </header>
              <main class="editor-main-content" :class="{ 'show-valid-msg': isValidBannerVisible }">
                <!--  编辑器本体  -->
                <editor-monaco
                  v-model="editorText"
                  ref="resourceEditorRef"
                  @find-state-changed="(isVisible) => {
                    isFindPanelVisible = isVisible;
                  }"
                />
                <!--  右侧的代码 error, warning 计数器  -->
                <aside class="editor-side-bar">
                  <main class="editor-error-counters">
                    <div
                      class="error-count-item" :class="{ 'active': activeCodeMsgType === 'Error' }"
                      v-bk-tooltips="{ content: `Error: ${msgAsErrorNum}`, placement: 'left' }"
                      @click="handleErrorCountClick('Error')"
                    >
                      <i class="apigateway-icon icon-ag-exclamation-circle-fill icon mb0 f12" style="color:#EA3636"></i>
                      <span class="num" style="color:#EA3636">{{ msgAsErrorNum }}</span>
                    </div>
                    <!--                    <div-->
                    <!--                      class="error-count-item" :class="{ 'active': activeCodeMsgType === 'All' }"-->
                    <!--                      v-bk-tooltips="{ content: `All: ${errorReasons.length}`, placement: 'left' }"-->
                    <!--                      @click="handleErrorCountClick('All')"-->
                    <!--                    >-->
                    <!--                      <span class="icon">all</span>-->
                    <!--                      <span class="num">{{ msgAsErrorNum + msgAsWarningNum }}</span>-->
                    <!--                    </div>-->
                  </main>
                  <footer class="editor-error-shifts">
                    <div class="shift-btn prev" @click="setEditorCursor('top')">
                      <collapse-left width="18px" height="18px" fill="#C4C6CC" />
                    </div>
                    <div class="shift-btn next" @click="setEditorCursor('bottom')">
                      <collapse-left width="18px" height="18px" fill="#C4C6CC" />
                    </div>
                  </footer>
                </aside>
              </main>
              <!--  底部“语法校验”按钮栏  -->
              <footer class="editor-footer-bar">
                <article v-if="isValidBannerVisible" class="validation-message">
                  <success class="success-c" width="14px" height="14px" />
                  <span class="msg-part msg-body">{{ t('校验通过') }}</span>
                  <!--                  <close-line-->
                  <!--                    width="14px" height="14px" fill="#DCDEE5" style="margin-left: auto; cursor: pointer;"-->
                  <!--                    @click="() => { isValidBannerVisible = false }"-->
                  <!--                  ></close-line>-->
                </article>
                <article v-else class="editor-footer-validate-btn">
                  <bk-button
                    theme="primary"
                    size="small"
                    :loading="isDataLoading"
                    :disabled="isDataLoading"
                    @click="handleCheckData({ changeView: false })"
                  >
                    <play-shape />
                    {{ t('语法校验') }}
                  </bk-button>
                </article>
              </footer>
            </div>
          </template>
          <!--  底部错误信息展示  -->
          <template #aside>
            <div class="editor-messages-wrapper" :class="{ 'has-error-msg': visibleErrorReasons.length > 0 }">
              <article
                v-for="(reason, index) in visibleErrorReasons"
                :key="index"
                class="editor-message"
                :class="{ 'active': activeVisibleErrorMsgIndex === index }"
                @click="handleErrorMsgClick(reason, index)"
              >
                <span class="msg-part msg-icon">
                  <i class="apigateway-icon icon-ag-exclamation-circle-fill f12" style="color:#B34747"></i>
                </span>
                <span class="msg-part msg-host"></span>
                <span class="msg-part msg-body">{{ reason.message }}</span>
                <span class="msg-part msg-error-code">{{ reason.json_path }}</span>
                <span v-if="reason.position" class="msg-part msgPos">
                  {{ `(${reason.position.lineNumber}, ${reason.position.column})` }}
                </span>
              </article>
            </div>
          </template>
        </bk-resize-layout>
      </div>
      <TmplExampleSideslider :is-show="isShowExample" @on-hidden="handleHiddenExample"></TmplExampleSideslider>
    </div>
    <!--  导入后视图  -->
    <div v-else class="imported-resources-wrap">
      <header class="res-counter-banner">
        <main>
          <i class="apigateway-icon icon-ag-info mr5 f16 default-c" />
          <span>{{ t('共') }}<span class="ag-strong pl5 pr5">{{ tableData.length }}</span>{{ t('个资源，新增') }}<span
            class="ag-strong success pl5 pr5"
          >{{ tableDataToAdd.length }}</span>{{ t('个，更新') }}<span
            class="ag-strong warning pl5 pr5"
          >{{ tableDataToUpdate.length }}</span>{{ t('个，取消导入') }}<span class="ag-strong danger pl5 pr5">{{
            tableDataUnchecked.length
          }}</span>{{ t('个') }}</span>
        </main>
        <aside>
          <bk-button
            text
            theme="primary"
            @click="handleRecoverAllRes()"
          >
            <i class="apigateway-icon icon-ag-undo-2 mr4 f16 default-c"></i>
            {{ t('恢复取消导入的资源') }}
          </bk-button>
        </aside>
      </header>
      <section class="res-content-wrap">
        <bk-collapse
          class="collapse-cls"
          v-model="panelNamesList"
          use-card-theme
        >
          <!--  新增的资源  -->
          <bk-collapse-panel name="add">
            <template #header>
              <div class="panel-header" ref="panelHeadAddRef">
                <main class="flex-row align-items-center">
                  <angle-up-fill
                    :class="[panelNamesList.includes('add') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ t('新增的资源（共') }}
                    <span class="success-c">{{ tableDataToAdd.length }}</span>
                    {{ t('个）') }}
                  </div>
                </main>
                <aside @click.stop.prevent>
                  <bk-input
                    v-model="filterInputAddClone"
                    clearable
                    :placeholder="t('请输入资源名称/路径，按Enter搜索')"
                    style="width: 578px;"
                    @enter="filterData('add')"
                    @clear="filterData('add')"
                  >
                    <template #prefix>
                      <aside
                        class="flex-row align-items-center ml10"
                        @click="filterData('add')"
                      >
                        <i class="apigateway-icon icon-ag-search f14"></i>
                      </aside>
                    </template>
                  </bk-input>
                </aside>
              </div>
            </template>
            <template #content>
              <div>
                <!--  新增资源 table  -->
                <TableResToAction
                  action="add"
                  :table-data="tableDataToAdd"
                  :show-doc="showDoc"
                  :keyword="filterInputAddClone"
                  v-model:tempAuthConfig="tempAuthConfig"
                  v-model:tempPublicConfig="tempPublicConfig"
                  @show-row-doc="handleShowResourceDoc"
                  @show-row-plugin="handleShowPluginsSlider"
                  @show-row-edit="handleEdit"
                  @toggle-row-unchecked="toggleRowUnchecked"
                  @confirm-auth-config="handleConfirmAuthConfigPopConfirm"
                  @confirm-pub-config="handleConfirmPublicConfigPopConfirm"
                  @clear-filter="clearFilterInput"
                ></TableResToAction>
              </div>
            </template>
          </bk-collapse-panel>
          <!--  更新的资源  -->
          <bk-collapse-panel name="update">
            <template #header>
              <div class="panel-header" ref="panelHeadUpdateRef">
                <main class="flex-row align-items-center">
                  <angle-up-fill
                    :class="[panelNamesList.includes('update') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ t('更新的资源（共') }}
                    <span class="warning-c">{{ tableDataToUpdate.length }}</span>
                    {{ t('个）') }}
                  </div>
                </main>
                <aside @click.stop.prevent>
                  <bk-input
                    v-model="filterInputUpdateClone"
                    clearable
                    :placeholder="t('请输入资源名称/路径，按Enter搜索')"
                    style="width: 578px;"
                    @enter="filterData('update')"
                    @clear="filterData('update')"
                  >
                    <template #prefix>
                      <aside
                        class="flex-row align-items-center ml10"
                        @click="filterData('update')"
                      >
                        <i class="apigateway-icon icon-ag-search f14"></i>
                      </aside>
                    </template>
                  </bk-input>
                </aside>
              </div>
            </template>
            <template #content>
              <div>
                <!--  更新资源 table  -->
                <TableResToAction
                  action="update"
                  :table-data="tableDataToUpdate"
                  :keyword="filterInputUpdateClone"
                  v-model:tempAuthConfig="tempAuthConfig"
                  v-model:tempPublicConfig="tempPublicConfig"
                  @show-row-doc="handleShowResourceDoc"
                  @show-row-plugin="handleShowPluginsSlider"
                  @show-row-edit="handleEdit"
                  @toggle-row-unchecked="toggleRowUnchecked"
                  @confirm-auth-config="handleConfirmAuthConfigPopConfirm"
                  @confirm-pub-config="handleConfirmPublicConfigPopConfirm"
                  @clear-filter="clearFilterInput"
                ></TableResToAction>
              </div>
            </template>
          </bk-collapse-panel>
          <!--  不导入的资源  -->
          <bk-collapse-panel name="uncheck">
            <template #header>
              <div class="panel-header" ref="panelHeadUncheckRef">
                <main class="flex-row align-items-center">
                  <angle-up-fill
                    :class="[panelNamesList.includes('uncheck') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ t('不导入的资源（共') }}
                    <span class="danger-c">{{ tableDataUnchecked.length }}</span>
                    {{ t('个）') }}
                  </div>
                </main>
              </div>
            </template>
            <template #content>
              <div>
                <TableResToUncheck
                  :table-data="tableDataUnchecked"
                  @show-row-doc="handleShowResourceDoc"
                  @show-row-plugin="handleShowPluginsSlider"
                  @toggle-row-unchecked="toggleRowUnchecked"
                ></TableResToUncheck>
              </div>
            </template>
          </bk-collapse-panel>
        </bk-collapse>
      </section>
    </div>
    <footer class="page-actions-wrap">
      <main class="page-actions">
        <bk-button
          :theme="curView === 'import' ? 'primary' : ''"
          @click="handleCheckData"
          :loading="isDataLoading"
          :disabled="curView === 'import' && !isCodeValid"
          v-bk-tooltips="{ content: isCodeModified ? t('请先进行语法检测') : t('请先修复报错信息后再导入'), disabled: isCodeValid && !isCodeModified }"
        >
          {{ curView === 'import' ? t('下一步') : t('上一步') }}
        </bk-button>
        <span
          v-bk-tooltips="{ content: t('请确认导入的资源'), disabled: (tableDataToAdd.length < 1) && (tableDataToUpdate.length < 1) }"
          v-if="curView === 'resources'"
        >
          <bk-button
            theme="primary"
            type="button"
            :disabled="(tableDataToAdd.length < 1) && (tableDataToUpdate.length < 1)"
            :loading="isImportLoading"
            @click="showImportConfirmDialog"
          >
            {{ $t('确定导入') }}
          </bk-button>
        </span>
        <bk-button @click="goBack">
          {{ t('取消') }}
        </bk-button>
      </main>
    </footer>
    <!--  编辑资源侧栏  -->
    <EditImportResourceSideSlider
      :resource="editingResource"
      :is-slider-show="isSliderShow"
      @on-hidden="handleEditSliderHidden"
      @submit="handleEditSubmit"
    ></EditImportResourceSideSlider>
    <!--  导入确认弹窗  -->
    <bk-dialog
      v-model:is-show="isImportConfirmDialogVisible"
      class="custom-main-dialog"
      width="400"
      mask-close
    >
      <div class="dialog-content">
        <div class="dialog-title">
          {{ t('确认导入资源？') }}
        </div>
        <div class="dialog-main">
          <header class="apigateway-name">{{ t('网关：') }}<span class="text">{{ common.apigwName }}</span></header>
          <main class="import-tips">
            {{ t('将新增') }}
            <span class="ag-strong success-c">{{ tableDataToAdd.length }}</span>
            {{ t('条资源，更新覆盖') }}
            <span class="ag-strong warning-c">{{ tableDataToUpdate.length }}</span>
            {{ t('条资源') }}
          </main>
        </div>
        <div class="dialog-footer">
          <bk-button theme="primary" @click="handleImportResource">{{ t('确定导入') }}</bk-button>
          <bk-button class="ml10" @click="isImportConfirmDialogVisible = false">{{ t('取消') }}</bk-button>
        </div>
      </div>
    </bk-dialog>
    <!-- 文档侧边栏 -->
    <ResourceDocSideSlider
      v-model="isResourceDocSliderVisible"
      :resource="editingResource"
      :show-footer="false"
      :show-create-btn="false"
      :is-preview="!editingResource.id"
      :preview-lang="language"
    ></ResourceDocSideSlider>
    <!--  查看插件侧边栏  -->
    <PluginPreviewSideSlider
      :plugins="editingResource.plugin_configs"
      :is-slider-show="isPluginsSliderShow"
      @on-hidden="isPluginsSliderShow = false"
    ></PluginPreviewSideSlider>
  </div>
  <!--  导入结果展示页  -->
  <div v-else class="import-result-wrapper">
    <!--  导入中  -->
    <article v-if="isImportLoading" class="content-wrap loading">
      <main class="content-main">
        <bk-loading
          mode="spin"
          theme="primary"
          loading
        >
          <div style="width: 100%; height: 48px" />
        </bk-loading>
        <section class="title">
          {{ t('正在导入') }}
          <span class="ag-strong">{{ tableDataToAdd.length + tableDataToUpdate.length }}</span>
          {{ t('个资源，请稍等...') }}
        </section>
      </main>
      <footer class="content-footer">
        <span>{{ t('新增了') }}
          <span
            class="ag-strong success pl5 pr5"
          >{{ tableDataToAdd.length }}</span>{{ t('个，更新') }}
          <span
            class="ag-strong warning pl5 pr5"
          >{{ tableDataToUpdate.length }}</span>{{ t('个资源') }}
        </span>
      </footer>
    </article>
    <!--  导入成功  -->
    <article v-else-if="isImportSucceeded" class="content-wrap success">
      <main class="content-main">
        <success width="64px" height="64px" fill="#2DCB56" />
        <section class="title">
          {{ t('成功导入') }}
          <span class="ag-strong">{{ tableDataToAdd.length + tableDataToUpdate.length }}</span>
          {{ t('个资源') }}
        </section>
      </main>
      <footer class="content-footer">
        <span>{{ t('新增了') }}
          <span
            class="ag-strong success pl5 pr5"
          >{{ tableDataToAdd.length }}</span>{{ t('个，更新') }}
          <span
            class="ag-strong warning pl5 pr5"
          >{{ tableDataToUpdate.length }}</span>{{ t('个资源，为了后续导入方便，请及时下载最新的资源文件') }}
        </span>
        <span class="download-btn" @click="isDownloadDialogShow = true"><i
          class="apigateway-icon icon-ag-download btn-icon"
        />{{
          t('下载资源文件')
        }}</span>
        <span>{{ t('（包含所有资源）') }}</span>
      </footer>
      <section class="actions">
        <bk-button theme="primary" @click="goBack()">
          {{
            t('返回查看')
          }}
        </bk-button>
        <!--        <bk-button @click="goBack()">-->
        <!--          {{-->
        <!--            t('继续导入')-->
        <!--          }}-->
        <!--        </bk-button>-->
      </section>
    </article>
    <!--  导入失败  -->
    <article v-else class="content-wrap fail">
      <main class="content-main">
        <close width="64px" height="64px" fill="#EA3636" />
        <section class="title">
          {{ t('资源导入失败') }}
        </section>
      </main>
      <section class="actions">
        <bk-button theme="primary" @click="handleImportResource()">
          {{
            t('失败重试')
          }}
        </bk-button>
        <bk-button @click="handleReturnClick()">
          {{
            t('返回修改配置')
          }}
        </bk-button>
      </section>
      <section v-if="importErrorMsg" class="error-msg">
        <bk-alert
          theme="error"
          :title="importErrorMsg"
          closable
          style="width: 800px;"
        />
      </section>
    </article>
    <!--  下载 dialog  -->
    <DownloadDialog v-model="isDownloadDialogShow" />
  </div>
</template>
<script setup lang="tsx">
import {
  ref,
  nextTick,
  computed,
  watch,
  onMounted,
} from 'vue';
import { InfoBox, Message, ResizeLayout } from 'bkui-vue';
import { useI18n } from 'vue-i18n';

// 此组件使用 TSX，通过 import { useRouter } from 'vue-router' 引入的路由api无法正常工作
// 请改用下面的写法：
// 引入：
// import useTsxRouter from './hooks/useTsxRouter';
// 使用：
// const { useRouter, onBeforeRouteLeave } = useTsxRouter();
// const router = useRouter();

import useTsxRouter from './hooks/useTsxRouter';
import editorMonaco from '@/components/ag-editor.vue';
import exampleData from '@/constant/example-data';
import { getStrFromFile } from '@/common/util';
import { checkResourceImport, importResource } from '@/http';
import { useCommon } from '@/store';
import { useGetGlobalProperties } from '@/hooks';
import TmplExampleSideslider from '@/views/resource/setting/comps/tmpl-example-sideslider.vue';
import {
  Share,
  PlayShape,
  Success,
  CollapseLeft,
  Close, AngleUpFill,
} from 'bkui-vue/lib/icon';
import yaml from 'js-yaml';
import { JSONPath } from 'jsonpath-plus';
import _ from 'lodash';

import type { IPosition } from 'monaco-editor';
import type { ErrorReasonType, CodeErrorMsgType } from '@/types/common';
import EditImportResourceSideSlider from '@/views/resource/setting/comps/edit-import-resource-side-slider.vue';
import DownloadDialog from '@/views/resource/setting/comps/download-dialog.vue';
import PluginPreviewSideSlider from '@/views/resource/setting/comps/plugin-preview-side-slider.vue';
import ResourceDocSideSlider from '@/views/components/resource-doc-slider/index.vue';
import {
  ActionType,
  IImportedResource,
  ILocalImportedResource,
} from '@/views/resource/setting/types';
import TableResToAction from '@/views/resource/setting/comps/table-res-to-action.vue';
import TableResToUncheck from '@/views/resource/setting/comps/table-res-to-uncheck.vue';
// @ts-ignore
import { useParentElement } from '@vueuse/core';

type CodeErrorResponse = {
  code: string,
  data: { json_path: string, message: string }[],
  details: any[],
  message: string,
};

const { useRouter, onBeforeRouteLeave } = useTsxRouter();
const router = useRouter();
const { t } = useI18n();
const common = useCommon();
const editorText = ref<string>(exampleData.content);
const { apigwId } = common; // 网关id
const resourceEditorRef = ref<InstanceType<typeof editorMonaco>>(); // 实例化
const showDoc = ref(true);
const language = ref<'zh' | 'en'>('zh');
const isDataLoading = ref(false);
// 代码校验是否通过
const isCodeValid = ref(false);
// 代码校验后是否修改过代码
const isCodeModified = ref(true);
const isImportLoading = ref(false);
// 是否展示导入结果页（loading、success、fail）
const isImportResultVisible = ref(false);
// 导入是否成功
const isImportSucceeded = ref(false);
const curView = ref<'import' | 'resources'>('import'); // 当前页面
const tableData = ref<ILocalImportedResource[]>([]);
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

// 选中的代码错误提示 Tab，默认展示 all 即全部类型的错误提示
const activeCodeMsgType = ref<CodeErrorMsgType>('All');
// 记录代码错误消息
const errorReasons = ref<ErrorReasonType[]>([]);
const isFindPanelVisible = ref(false);
// 资源确认页的 collapse 面板列表
const panelNamesList = ref(['add', 'update', 'uncheck']);
// 资源确认页的 collapse 面板标题，稍后添加样式要用
const panelHeadAddRef = ref<HTMLDivElement | null>(null);
const panelHeadUpdateRef = ref<HTMLDivElement | null>(null);
const panelHeadUncheckRef = ref<HTMLDivElement | null>(null);

const isImportConfirmDialogVisible = ref(false);
const isResourceDocSliderVisible = ref(false);
const isValidBannerVisible = ref(false);

const editingResource = ref<ILocalImportedResource>({
  name: '',
  description: '',
  label_ids: [],
  labels: [],
  auth_config: {
    auth_verified_required: true,
    app_verified_required: true,
    resource_perm_required: true,
  },
  is_public: true,
  allow_apply_permission: true,
  _localId: -1,
  _unchecked: false,
});
const isSliderShow = ref(false);
const isPluginsSliderShow = ref(false);

// 编辑器所在的 resize-layout
const resizeLayoutRef = ref<InstanceType<typeof ResizeLayout> | null>(null);
// resizeLayout 拉伸区高度范围
const resizeLayoutAsideMax = ref(100);
const resizeLayoutAsideMin = ref(50);

// 导入失败消息
const importErrorMsg = ref('');
// 导入成功后的下载资源 dialog 是否可视
const isDownloadDialogShow = ref(false);

// 展示在“新增的资源”一栏的资源
const tableDataToAdd = computed(() => {
  return tableData.value.filter((data) => {
    return !data.id
      && !data._unchecked
      && (data.name.includes(filterInputAdd.value) || data.path.includes(filterInputAdd.value));
  });
});

// 展示在“更新的资源”一栏的资源
const tableDataToUpdate = computed(() => {
  return tableData.value.filter((data) => {
    return data.id
      && !data._unchecked
      && (data.name.includes(filterInputUpdate.value) || data.path.includes(filterInputUpdate.value));
  });
});

// 被取消导入的资源
const tableDataUnchecked = computed(() => {
  return tableData.value.filter(data => data._unchecked);
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

// const msgAsWarningNum = computed(() => {
//   return errorReasons.value.filter(r => r.level === 'Warning').length;
// });

// 代码有变化时重置校验状态
watch(editorText, () => {
  isCodeValid.value = false;
  isCodeModified.value = true;
  isValidBannerVisible.value = false;
  activeVisibleErrorMsgIndex.value = -1;
});

// 返回编辑器页时自动折叠错误消息
watch(curView, async (newCurView, oldCurView) => {
  if (newCurView === 'import' && oldCurView === 'resources') {
    await nextTick(() => {
      resizeLayoutRef.value?.setCollapse(true);
      isEditorMsgCollapsed = true;
    });
  } else if (newCurView === 'resources' && oldCurView === 'import') {
    // 从编辑器页进入资源结果确认页时会走到这里
    // 给 collapse 表头添加固定样式
    await nextTick(() => {
      [
        useParentElement(panelHeadAddRef),
        useParentElement(panelHeadUpdateRef),
        useParentElement(panelHeadUncheckRef),
      ].forEach((parentEl) => {
        parentEl.value?.classList.add('panel-head-sticky-top');
      });
    });
  }
});

// 进入页面默认折叠编辑器错误消息栏
onMounted(() => {
  resizeLayoutRef.value?.setCollapse(true);
  // 设置拉伸区高度范围
  const editorViewportHeight = resizeLayoutRef.value?.$el.clientHeight - 92;
  resizeLayoutAsideMax.value = Math.floor(editorViewportHeight * 0.8);
  resizeLayoutAsideMin.value = Math.ceil(editorViewportHeight * 0.2);
  // 更改编辑器主题和行号左边的提示列(glyph margin)
  if (resourceEditorRef?.value) {
    resourceEditorRef.value.setTheme('import-theme');
    resourceEditorRef.value.updateOptions({ glyphMargin: true });
  }
});

// 监听路由离开，提示用户是否要在导入中离开
onBeforeRouteLeave((to, from, next) => {
  // 如果正在导入中...
  if (isImportResultVisible.value && isImportLoading.value) {
    InfoBox({
      title: t('确认离开当前页？'),
      subTitle: t('离开将会导致未保存信息丢失'),
      confirmText: t('离开'),
      cancelText: t('取消'),
      onConfirm() {
        next();
      },
      onClosed() {
        return false;
      },
    });
  } else next();
});

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
    })
    .then(() => {
      handleCheckData({ changeView: false });
    });
};

// 下一步需要检查数据
const handleCheckData = async ({ changeView }: { changeView: boolean }) => {
  const _changeView = changeView ?? true;
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
    // 清空编辑器高亮样式和所有下划波浪线
    resourceEditorRef.value?.clearDecorations();
    resourceEditorRef.value?.clearMarkers();
    errorReasons.value = [];
    // 重置可视错误消息类型
    activeCodeMsgType.value = 'All';
    const params: any = {
      content: editorText.value,
      allow_overwrite: true,
    };
    // 如果勾选了资源文档
    if (showDoc.value) {
      params.doc_language = language.value;
    }
    // 配置是否显示错误 Message，只校验代码时不显示，改为展示在编辑器的错误消息栏中
    const interceptorConfig = _changeView ? {} : { globalError: false };
    const res = await checkResourceImport(apigwId, params, interceptorConfig) as IImportedResource[];
    tableData.value = res.map((data, index: number) => ({
      ...data,
      _unchecked: false, // 标记是否不导入
      _localId: index, // 给一个本地id以识别修改了哪一条数据
    }));
    isCodeValid.value = true;
    isValidBannerVisible.value = true;
    // 折叠错误消息栏
    if (!isEditorMsgCollapsed) {
      await nextTick(() => {
        resizeLayoutRef?.value?.setCollapse(true);
      });
    }
    // 判断是否跳转，默认为是
    if (_changeView) {
      curView.value = 'resources';
    }
  } catch (err: unknown) {  // 校验失败会走到这里
    // console.log(error);
    isCodeValid.value = false;
    isValidBannerVisible.value = false;
    const error = err as CodeErrorResponse;
    // 如果是内容错误
    if (error?.code === 'INVALID' && error?.message === 'validate fail') {
      const editorJsonObj = yaml.load(editorText.value) as object;
      const errData: { json_path: string, message: string }[] = error.data ?? [];
      errorReasons.value = errData.map((err) => {
        if (err.json_path !== '$' && err.json_path !== '') {
          // 从 jsonpath 提取路径组成数组，去掉开头的 $
          let paths = JSONPath.toPathArray(err.json_path)
            .slice(1);
          // 找到 jsonpath 指向的值
          let pathValue = JSONPath(err.json_path, editorJsonObj, null, null)[0] ?? null;
          // 当获取 json_path 指向的值失败时，检查是不是因为 json_path 中有大写的 http method
          if (pathValue === null) {
            const httpMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'];
            // 把 json_path 中的大写 method 规范化为小写的
            if (paths.some(item => httpMethods.includes(item))) {
              paths = paths.map(item => (httpMethods.includes(item) ? item.toLowerCase() : item));
              pathValue = JSONPath(`$.${paths.join('.')}`, editorJsonObj, null, null)[0] ?? null;
            }
          }
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
          // 判断 jsonpath 指向的是否为数组成员，是的话传入倒数第二个 path
          const isInteger = Number.isInteger(Number(lastPath)) && lastPath.trim() !== '';
          const objKey = isInteger ? paths[paths.length - 2] : lastPath;
          regex = getRegexFromObj({ objKey, objValue: pathValue });

          offset = resourceEditorRef.value.getValue()
            .search(regex);
          // 用 editor 的 api 找到 Position
          if (offset > -1) {
            position = resourceEditorRef.value.getModel()
              .getPositionAt(offset);
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
        }
        return {
          json_path: err.json_path,
          message: err.message ?? t('未知错误'),
          level: 'Error',
        };
      });
    } else {
      // 其他错误会走到这里，包括格式错误等等
      errorReasons.value.push({
        message: error?.message ?? t('未知错误'),
        level: 'Error',
      });
    }
    // console.log('errorReasons:');
    // console.log(errorReasons.value);
    // 更新编辑器高亮样式和下划波浪线
    updateEditorDecorations();
    updateEditorMarkers();
    // 展开错误消息栏
    if (isEditorMsgCollapsed) {
      await nextTick(() => {
        resizeLayoutRef?.value?.setCollapse(false);
      });
    }
  } finally {
    isDataLoading.value = false;
    isCodeModified.value = false;
    activeVisibleErrorMsgIndex.value = -1;
  }
};

// 唤出确认导入Dialog
const showImportConfirmDialog = () => {
  isImportConfirmDialogVisible.value = true;
};

// 确认导入
const handleImportResource = async () => {
  isImportConfirmDialogVisible.value = false;
  try {
    isImportLoading.value = true;
    isImportResultVisible.value = true;
    const import_resources = tableData.value.filter(e => e._unchecked === false)
      .map((e) => {
        const {
          _unchecked,
          _localId,
          backend,
          ...restOfResource
        } = e;  // 去掉_unchecked 和 _localId 属性，不要发到后端
        return { ...restOfResource, backend_config: { ...backend.config }, backend_name: backend.name };
      });
    const params = { import_resources };
    // 如果勾选了资源文档，传入 doc_language
    if (showDoc.value) {
      Object.assign(params, { doc_language: language.value });
    }
    await importResource(apigwId, params);
    isImportSucceeded.value = true;
  } catch (err: unknown) {
    const error = err as { message: string };
    importErrorMsg.value = error?.message ? `${t('失败原因：')}${error.message}` : '';
    isImportSucceeded.value = false;
  } finally {
    isImportLoading.value = false;
  }
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

const handleEditSliderHidden = () => {
  isSliderShow.value = false;
};

// 确认修改配置后
const handleEditSubmit = (newResource: ILocalImportedResource) => {
  const pos = tableData.value.findIndex(data => data._localId === newResource._localId);
  if (pos > -1) tableData.value[pos] = { ...tableData.value[pos], ...newResource };
  // console.log('newResource:');
  // console.log(newResource);
  // console.log('pos');
  // console.log(pos);
  // console.log('tableData.value:');
  // console.log(tableData.value);
};

// 点击修改配置时，会唤出 SideSlider
const handleEdit = (resourceRow: ILocalImportedResource) => {
  const _editingResource = tableData.value.find(data => data._localId === resourceRow._localId);
  if (_editingResource) editingResource.value = { ...editingResource.value, ..._editingResource };
  isSliderShow.value = true;
};

// 点击查看文档时，会唤出 SideSlider
const handleShowResourceDoc = (resourceRow: ILocalImportedResource) => {
  const _editingResource = tableData.value.find(data => data._localId === resourceRow._localId);
  if (_editingResource) editingResource.value = { ...editingResource.value, ..._editingResource };
  isResourceDocSliderVisible.value = true;
};

// 点击插件数时，会唤出 PluginsSlider
const handleShowPluginsSlider = (resourceRow: ILocalImportedResource) => {
  if (!resourceRow.plugin_configs || resourceRow.plugin_configs?.length < 1) return;
  const _editingResource = tableData.value.find(data => data._localId === resourceRow._localId);
  if (_editingResource) editingResource.value = { ...editingResource.value, ..._editingResource };
  isPluginsSliderShow.value = true;
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

// 触发编辑器添加下划波浪线
const updateEditorMarkers = () => {
  resourceEditorRef.value.clearMarkers();
  resourceEditorRef.value.genMarkers(errorReasons.value.map(r => ({
    position: r.position,
    message: r.message,
  })));
  resourceEditorRef.value.setMarkers();
};

// 处理代码错误消息点击事件，应跳转到编辑器对应行
const handleErrorMsgClick = (reason: ErrorReasonType, index: number) => {
  if (reason.position) {
    resourceEditorRef.value.setCursorPos(reason.position);
  }
  activeVisibleErrorMsgIndex.value = index;
};

const activeVisibleErrorMsgIndex = ref(-1);

const setEditorCursor = (pos: 'top' | 'bottom') => {
  pos === 'top'
    ? resourceEditorRef.value.setCursorPos({ lineNumber: 1 })
    : resourceEditorRef.value.setCursorPos({ toBottom: true });
};

// 从把 jsonpath 指向的对象转换成正则
const getRegexFromObj = ({ objKey, objValue }: { objKey: string, objValue: any }): RegExp => {
  const exp = `[\\b/$'"]*?${removeStarting$(objKey)}[\\b\\s/$'"]*?:${getRegexString(objValue)}`;
  return new RegExp(exp, 'gm');
};

// 递归地把变量转换成可以生成正则表达式的字符串
const getRegexString = (value: any): string => {
  let expStr = '[-"\\s\\n\\r]*?';

  if (_.isObject(value)) {
    if (Array.isArray(value)) {
      if (value.length < 1) {
        expStr += '[\'"\\s\\n\\r]*?\\[\\][\'"\\s\\n\\r]*?';
      } else {
        value.forEach((el) => {
          if (_.isObject(el)) {
            expStr += getRegexString(el);
          } else {
            expStr += `['"\\s\\n\\r]*?${escapeAsteroid(el)}['"\\s\\n\\r]*?`;
          }
        });
      }
    } else {
      if (Object.keys(value).length < 1) {
        expStr += '[\'"\\s\\n\\r]*?{}[\'"\\s\\n\\r]*?';
      } else {
        Object.entries(value)
          .forEach(([key, val]) => {
            expStr += `[\\b/$'"]*?${removeStarting$(key)}[\\b\\s/$'"]*?:`;
            if (_.isObject(val)) {
              expStr += getRegexString(val);
            } else {
              expStr += `['"\\s\\n\\r]*?${val === null ? '' : escapeAsteroid(val)}['"\\s\\n\\r]*?`;
            }
          });
      }
    }
  } else {
    expStr += `${value === null ? '' : escapeAsteroid(value)}['"\\s\\n\\r]*?`;
  }

  return expStr;
};

const removeStarting$ = (str: string): string => {
  if (str.startsWith('$')) {
    return str.substring(1);
  }
  return str;
};

// 转义*号符
const escapeAsteroid = (str: string): string => {
  if (typeof str === 'string') {
    return str.replaceAll('*', '\\*');
  }
  return str;
};

// 获取字符串中第一个被 '' 包裹的值
const getFirstQuotedValue = (str: string) => {
  const match = str.match(/'([^']*)'/);
  return match ? match[1] : null;
};

// 处理右侧错误类型计数器点击事件
const handleErrorCountClick = (type: CodeErrorMsgType) => {
  // 重复点击同一个类型，则重置选中态
  activeCodeMsgType.value = (type === activeCodeMsgType.value) ? 'All' : type;
  activeVisibleErrorMsgIndex.value = -1;
  updateEditorDecorations();
  // 如果有错误消息，点击后可以展开/收起错误消息栏
  if (visibleErrorReasons.value.length > 0) {
    nextTick(() => {
      if (isEditorMsgCollapsed) {
        resizeLayoutRef.value?.setCollapse(false);
      } else {
        resizeLayoutRef.value?.setCollapse(true);
      }
    });
  }
};

// 切换搜索面板
const toggleFindToolClick = () => {
  if (isFindPanelVisible.value) {
    resourceEditorRef.value.closeFindPanel();
  } else {
    resourceEditorRef.value.showFindPanel();
  }
};

// 切换字号
const handleFontSizeClick = () => {
  resourceEditorRef.value.switchFontSize();
};

// 切换资源是否导入
const toggleRowUnchecked = (row: ILocalImportedResource) => {
  const data = tableData.value.find(d => d._localId === row._localId);
  if (data) data._unchecked = !data._unchecked;
};

// 还原所有不导入的资源
const handleRecoverAllRes = () => {
  tableData.value.forEach(d => d._unchecked = false);
};

const tempAuthConfig = ref({
  app_verified_required: false,
  auth_verified_required: false,
  resource_perm_required: false,
});

// 批量修改认证方式确认后
const handleConfirmAuthConfigPopConfirm = (action: ActionType) => {
  if (tempAuthConfig.value.app_verified_required === false) tempAuthConfig.value.resource_perm_required = false;
  tableData.value.filter(item => !item._unchecked)
    .forEach((data) => {
      if ((action === 'add' && !data.id) || (action === 'update' && data.id)) {
        data.auth_config = {
          ...tempAuthConfig.value,
        };
      }
    });
};

const tempPublicConfig = ref({
  is_public: false,
  allow_apply_permission: false,
});

// 批量修改公开设置确认后
const handleConfirmPublicConfigPopConfirm = (action: ActionType) => {
  const isPublic = tempPublicConfig.value.is_public;
  const allowApplyPermission = tempPublicConfig.value.allow_apply_permission && isPublic;

  tableData.value.filter(item => !item._unchecked)
    .forEach((item) => {
      if ((action === 'add' && !item.id) || (action === 'update' && item.id)) {
        item.is_public = isPublic;
        item.allow_apply_permission = allowApplyPermission;
      }
    });
};

const filterInputAdd = ref('');
const filterInputAddClone = ref('');
const filterInputUpdate = ref('');
const filterInputUpdateClone = ref('');

const filterData = (action: ActionType) => {
  if (action === 'add') {
    filterInputAdd.value = filterInputAddClone.value;
  }

  if (action === 'update') {
    filterInputUpdate.value = filterInputUpdateClone.value;
  }
};

const clearFilterInput = (action: ActionType) => {
  if (action === 'add') {
    filterInputAdd.value = '';
    filterInputAddClone.value = '';
  }

  if (action === 'update') {
    filterInputUpdate.value = '';
    filterInputUpdateClone.value = '';
  }
};

const editorWrapRef = ref<HTMLElement | null>(null);
// 编辑器全屏
const handleFullScreenClick = () => {
  if (editorWrapRef?.value?.requestFullscreen) {
    editorWrapRef.value.requestFullscreen();
  }
};

// 记录编辑器错误消息栏折叠状态
let isEditorMsgCollapsed = false;
const updateIsEditorMsgCollapsed = (collapsed: boolean) => {
  isEditorMsgCollapsed = collapsed;
};

const handleReturnClick = () => {
  isImportSucceeded.value = false;
  isImportResultVisible.value = false;
  isImportLoading.value = false;
};
</script>
<style scoped lang="scss">

.import-wrapper {
  position: relative;
  min-height: 100%;

  .steps-indicator-wrap,
  .page-actions-wrap {
    height: 52px;
    display: flex;
    align-items: center;
    background: #FFFFFF;
    z-index: 100;
  }

  .steps-indicator-wrap {
    position: sticky;
    top: 0;
    justify-content: center;
    border-bottom: 1px solid #DCDEE5;

    .steps-indicator {
      width: 360px;
    }
  }

  .page-actions-wrap {
    position: sticky;
    left: 0;
    right: 0;
    bottom: 0;
    padding-left: 48px;
    border-top: 1px solid #DCDEE5;

    .page-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

.import-container {
  padding: 20px 24px 18px;
  margin: 20px 24px;
  background-color: #FFFFFF;
  box-shadow: 0 2px 4px 0 #1919290d;

  .import-header {
    .icon-ag-add-small {
      font-size: 16px;
    }

    .desc {
      margin-left: 12px;
      font-size: 12px;
      color: #979ba5;
    }
  }

  .monaco-editor {
    width: 100%;
    height: calc(100vh - 330px);
    margin-top: 10px;
    border-radius: 2px;
    overflow: hidden;

    .editor-layout-main {
      height: 100%;
      display: flex;
      flex-direction: column;

      .editor-toolbar {
        height: 40px;
        position: relative;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #2e2e2e;
        box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2);
        z-index: 6;

        .tool-items {
          height: 100%;
          padding-right: 16px;
          display: flex;
          align-items: center;
          gap: 16px;

          .tool-item {
            display: flex;
            align-items: center;
            color: #999;
            cursor: pointer;

            &.active, &:hover {
              color: #ccc;
            }
          }
        }
      }

      .editor-main-content {
        display: flex;
        // 100% - 40px(.editor-toolbar高度) - 52px(.editor-footer-bar高度)
        height: calc(100% - 92px);

        .editor-side-bar {
          width: 32px;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          background-color: #212121;

          .editor-error-counters {
            width: 32px;
            display: flex;
            flex-direction: column;
            align-items: center;

            .error-count-item {
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
                background-color: #3e3e3e;
              }

              .icon {
                margin-bottom: 2px;
              }

              .num {
                font-size: 12px;
                line-height: 14px;
              }
            }
          }

          .editor-error-shifts {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;

            .shift-btn {
              width: 24px;
              height: 24px;
              display: flex;
              justify-content: center;
              align-items: center;
              background: #4D4D4D;
              border-radius: 2px;
              cursor: pointer;

              &:active {
                background: #666;
              }
            }

            .shift-btn.prev {
              transform: rotate(-90deg);
            }

            .shift-btn.next {
              transform: rotate(90deg);
            }
          }
        }
      }

      .editor-footer-bar {
        background-color: #1a1a1a;
        box-shadow: 0 -2px 4px 0 #00000029;
        z-index: 1;

        .editor-footer-validate-btn {
          height: 52px;
          padding-left: 24px;
          display: flex;
          align-items: center;
        }

        .validation-message {
          height: 52px;
          padding-left: 24px;
          padding-right: 24px;
          display: flex;
          align-items: center;
          gap: 8px;
          background-color: #212121;;
          font-size: 12px;
          color: #DCDEE5;
          border-left: 4px solid #34d97b;
        }
      }
    }

    .editor-messages-wrapper {
      position: relative;
      height: 100%;
      padding-top: 16px;
      background-color: #212121;
      border-left: 4px solid #1a1a1a;
      font-size: 12px;

      &.has-error-msg {
        border-left: 4px solid #B34747;
      }

      .editor-message {
        height: 20px;
        padding: 0 4px 0 12px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
        cursor: pointer;

        &.active,
        &:hover {
          background-color: #333;
        }

        .msg-body {
          color: #ccc;
        }
      }
    }

    // 变更代码编辑器伸缩线样式
    :deep(.bk-resize-layout-bottom > .bk-resize-layout-aside) {
      border-top: 1px solid black;
      background: #212121;
    }

    // ResizeLayout 的折叠按钮样式
    :deep(.bk-resize-layout > .bk-resize-layout-aside .bk-resize-collapse) {
      margin-bottom: 9px;
      margin-left: -16px;
      background: #313238;

      &:hover {
        background-color: #63656E;
      }
    }

    &.hide-collapse-btn {
      // 隐藏 ResizeLayout 的折叠按钮
      :deep(.bk-resize-layout > .bk-resize-layout-aside .bk-resize-collapse) {
        display: none !important;
      }
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
  :deep(.line-highlight-error) {
    background-color: #382322;
    opacity: .7;
  }

  // 行号左侧图标样式
  :deep(.apigateway-icon.icon-ag-exclamation-circle-fill.f14) {
    color: #b34747;
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
}

.imported-resources-wrap {
  margin: 20px 24px 0 24px;
  //min-height: 768px;

  .res-counter-banner {
    height: 40px;
    padding: 0 24px 0 12px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
  }

  .res-content-wrap {
    height: calc(100vh - 285px);
    overflow-y: scroll;

    &::-webkit-scrollbar {
      width: 4px;
      height: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: #ddd;
      border-radius: 20px;
      box-shadow: inset 0 0 6px #cccccc4d;
    }

    :deep(.collapse-cls) {
      margin-bottom: 24px;

      .bk-collapse-item {
        background: #fff;
        box-shadow: 0 2px 4px 0 #1919290d;
        margin-bottom: 16px;
      }

      // 折叠让 .panel-header 粘滞固定到顶部
      .panel-head-sticky-top {
        position: sticky;
        top: 0;
        background-color: #ffffff;
        z-index: 3;
      }
    }

    :deep(.bk-collapse-content) {
      padding-top: 0 !important;
      padding-bottom: 0 !important;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 19px 24px;
      cursor: pointer;

      .title {
        font-weight: 700;
        font-size: 14px;
        color: #313238;
        margin-left: 8px;
      }

      .panel-header-show {
        transition: .2s;
        transform: rotate(0deg);
      }

      .panel-header-hide {
        transition: .2s;
        transform: rotate(-90deg);
      }
    }
  }
}

.import-result-wrapper {
  height: 400px;
  margin: 20px 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #FFFFFF;
  box-shadow: 0 2px 4px 0 #1919290d;

  .content-wrap {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    .content-main {
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 40px;

      .title {
        color: #313238;
        font-size: 24px;
        line-height: 32px;
      }
    }

    .content-footer {
      color: #63656E;

      .download-btn {
        margin-left: 4px;
        color: #3A84F6;
        cursor: pointer;

        .btn-icon {
          font-size: 18px;
        }
      }
    }

    .actions {
      margin-top: 28px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .error-msg {
      margin-top: 16px;
    }
  }
}

:deep(.bk-collapse-header) {
  display: flex;
  align-items: center;
}

:deep(.bk-collapse-header .bk-collapse-title) {
  flex-grow: 1;
  display: inline-flex;
  align-items: center;
}

:deep(.bk-collapse-content) {
  padding-left: 24px;
  padding-right: 24px;
}

:deep(.multi-edit-popconfirm-wrap .auth-config) {
  font-size: 12px;
}

.custom-main-dialog {
  :deep(.bk-dialog-title) {
    display: none;
  }

  :deep(.bk-modal-footer) {
    display: none;
  }

  .dialog-content {
    .publish-icon {
      text-align: center;
      margin-bottom: 18px;
      font-size: 42px;
      line-height: 32px;
    }

    .dialog-title {
      font-size: 20px;
      color: #313238;
      text-align: center;
      margin-bottom: 16px;
    }

    .dialog-main {

      .apigateway-name {
        margin-bottom: 16px;

        .text {
          font-weight: 700;
        }
      }

      .import-tips {
        background: #F5F6FA;
        border-radius: 2px;
        margin-bottom: 25px;
        padding: 12px 16px;
        color: #63656E;

        span {
          font-weight: 700;
        }
      }
    }

    .dialog-footer {
      text-align: center;
    }
  }
}

:deep(.import-container .import-header .bk-form .bk-checkbox-label) {
  font-size: 12px;
}

:deep(.import-container .import-header .bk-form .bk-form-label) {
  font-size: 12px;
}

:deep(.import-container .import-header .bk-form .bk-form-content) {
  height: 32px;
}
</style>
