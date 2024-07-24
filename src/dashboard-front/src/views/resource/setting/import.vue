<template>
  <div class="importWrapper">
    <header class="steps-indicator-wrap">
      <main class="stepsIndicator">
        <bk-steps
          :steps="[
            { title: '校验文件' },
            { title: '资源信息确认' },
          ]"
          :cur-step="curView === 'import' ? 1 : 2"
          theme="primary"
        />
      </main>
    </header>
    <!--  导入前视图，代码编辑器在此页  -->
    <div v-if="curView === 'import'" class="import-container">
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
          <!--            <bk-form class="flex-row">-->
          <!--              <bk-form-item class="mb0" :label-width="20">-->
          <!--                <bk-checkbox v-model="showDoc">-->
          <!--                  {{ t('生成资源文档') }}-->
          <!--                </bk-checkbox>-->
          <!--              </bk-form-item>-->
          <!--  <bk-form-item class="mb0" :label="t('文档语言')" v-if="showDoc" :required="true" :label-width="120">-->
          <!--                <bk-radio-group v-model="language">-->
          <!--                  <bk-radio label="zh">{{ t('中文文档') }}</bk-radio>-->
          <!--                  <bk-radio label="en">{{ t('英文文档') }}</bk-radio>-->
          <!--                </bk-radio-group>-->
          <!--              </bk-form-item>-->
          <!--            </bk-form>-->
        </div>
        <div class="flex-row align-items-center">
          <bk-button theme="primary" text style="font-size: 12px;" @click="handleShowExample">
            {{
              t('模板示例')
            }}
          </bk-button>
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
                <editor-monaco
                  v-model="editorText"
                  ref="resourceEditorRef"
                  @find-state-changed="(isVisible) => {
                    isFindPanelVisible = isVisible;
                  }"
                />
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
      <TmplExampleSideslider :is-show="isShowExample" @on-hidden="handleHiddenExample"></TmplExampleSideslider>
    </div>
    <!--  导入后视图  -->
    <div v-else class="imported-resources-wrap">
      <header class="res-counter-banner">
        <main>
          <info-line width="14px" height="14px" fill="#3A84FF" class="mr5" />
          <span>共<span class="ag-strong pl5 pr5">{{ tableData.length }}</span>个资源，新增<span
            class="ag-strong success pl5 pr5"
          >{{ tableDataToAdd.length }}</span>个，更新<span
            class="ag-strong warning pl5 pr5"
          >{{ tableDataToUpdate.length }}</span>个，取消导入<span class="ag-strong danger pl5 pr5">{{
              tableDataUnchecked.length
            }}</span>个</span>
        </main>
        <aside>
          <bk-button
            text
            theme="primary"
            @click="handleRecoverAllRes()"
          >
            <left-turn-line fill="#3A84FF" />
            {{ t('恢复取消导入的资源') }}
          </bk-button>
        </aside>
      </header>
      <!--  新增的资源  -->
      <section class="res-content-wrap add">
        <bk-collapse
          v-model="activeIndexAdd"
          :list="collapsePanelListAdd"
          header-icon="right-shape"
        >
          <template #title>
            <div class="collapse-panel-title">
              <!--              <span>新增的资源（共{{ createNum }}个）</span>-->
              <span>新增的资源（共{{ tableDataToAdd.length }}个）</span>
              <bk-input
                :clearable="true"
                :placeholder="t('请输入资源名称，按Enter搜索')"
                :right-icon="'bk-icon icon-search'"
                style="width: 240px;"
                @click.stop.prevent
              />
            </div>
          </template>
          <template #content>
            <div class="collapse-panel-table-wrap">
              <bk-table
                class="table-layout"
                :data="tableDataToAdd"
                row-key="name"
                show-overflow-tooltip
              >
                <bk-table-column
                  :label="t('资源名称')"
                  prop="name"
                >
                </bk-table-column>
                <!--  认证方式列  -->
                <bk-table-column
                  :label="() => renderAuthConfigColLabel('add')"
                >
                  <template #default="{ row }">
                    {{ getAuthConfigText(row?.auth_config) }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('校验应用权限')"
                >
                  <template #default="{ row }">
                    {{ getPermRequiredText(row?.auth_config) }}
                  </template>
                </bk-table-column>
                <!--  “是否公开”列  -->
                <bk-table-column
                  :label="() => renderIsPublicColLabel('add')"
                >
                  <template #default="{ row }">
                    <span>
                      {{ row.is_public ? t('是') : row.is_public === false ? t('否') : t('是') }}
                    </span>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('允许申请权限')"
                >
                  <template #default="{ row }">
                    {{
                      row.allow_apply_permission ? t('是') : row.allow_apply_permission === false ? t('否') : t('是')
                    }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('前端请求路径')"
                  prop="path"
                >
                </bk-table-column>
                <bk-table-column
                  :label="t('前端请求方法')"
                  prop="method"
                  :show-overflow-tooltip="false"
                >
                  <template #default="{ row }">
                    <bk-tag :theme="methodsEnum[row?.method]">{{ row?.method }}</bk-tag>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端服务')"
                  prop="method"
                >
                  <template #default="{ row }">
                    {{ row.backend?.name ?? 'default' }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端请求方法')"
                  prop="method"
                  :show-overflow-tooltip="false"
                >
                  <template #default="{ row }">
                    <bk-tag
                      :theme="methodsEnum[row.backend?.method ?? row.method]"
                    >
                      {{ row.backend?.method ?? row.method }}
                    </bk-tag>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端请求路径')"
                  prop="path"
                >
                  <template #default="{ row }">
                    {{ row.backend?.path ?? row.path }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('资源文档')"
                  prop="doc"
                >
                  <template #default="{ row }">
                    <bk-button
                      text
                      theme="primary"
                    >
                      <doc-fill fill="#3A84FF" />
                      {{ t('详情') }}
                    </bk-button>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('插件数量')"
                  prop="plugin_configs"
                >
                  <template #default="{ row }">
                    <span>{{ row.plugin_configs?.length ?? 0 }}</span>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('操作')"
                  width="200"
                  fixed="right"
                  prop="act"
                >
                  <template #default="{ row }">
                    <bk-button
                      text
                      theme="primary"
                    >
                      {{ t('修改配置') }}
                    </bk-button>
                    <bk-button
                      text
                      theme="primary"
                      class="pl10 pr10"
                      @click="() => {
                        toggleRowUnchecked(row)
                      }"
                    >
                      {{ t('不导入') }}
                    </bk-button>
                  </template>
                </bk-table-column>
              </bk-table>
            </div>
          </template>
        </bk-collapse>
      </section>
      <!--  更新的资源  -->
      <section class="res-content-wrap update">
        <bk-collapse
          v-model="activeIndexUpdate"
          :list="collapsePanelListUpdate"
          header-icon="right-shape"
        >
          <template #title>
            <div class="collapse-panel-title">
              <span>更新的资源（共{{ tableDataToUpdate.length }}个）</span>
              <bk-input
                :clearable="true"
                :placeholder="t('请输入资源名称，按Enter搜索')"
                :right-icon="'bk-icon icon-search'"
                style="width: 240px;"
                @click.stop.prevent
              />
            </div>
          </template>
          <template #content>
            <div class="collapse-panel-table-wrap">
              <bk-table
                class="table-layout"
                :data="tableDataToUpdate"
                show-overflow-tooltip
                row-key="name"
                :checked="tableData"
                @selection-change="handleSelectionChange"
              >
                <bk-table-column
                  :label="t('资源名称')"
                  prop="name"
                >
                </bk-table-column>
                <!--  认证方式列  -->
                <bk-table-column
                  :label="() => renderAuthConfigColLabel('update')"
                >
                  <template #default="{ row }">
                    {{ getAuthConfigText(row?.auth_config) }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('校验应用权限')"
                >
                  <template #default="{ row }">
                    {{ getPermRequiredText(row?.auth_config) }}
                  </template>
                </bk-table-column>
                <!--  “是否公开”列  -->
                <bk-table-column
                  :label="() => renderIsPublicColLabel('update')"
                >
                  <template #default="{ row }">
                    <span>
                      {{ row.is_public ? t('是') : row.is_public === false ? t('否') : t('是') }}
                    </span>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('允许申请权限')"
                >
                  <template #default="{ row }">
                    {{
                      row.allow_apply_permission ? t('是') : row.allow_apply_permission === false ? t('否') : t('是')
                    }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('前端请求路径')"
                  prop="path"
                >
                </bk-table-column>
                <bk-table-column
                  :label="t('前端请求方法')"
                  prop="method"
                  :show-overflow-tooltip="false"
                >
                  <template #default="{ row }">
                    <bk-tag :theme="methodsEnum[row?.method]">{{ row?.method }}</bk-tag>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端服务')"
                  prop="method"
                >
                  <template #default="{ row }">
                    {{ row.backend?.name ?? 'default' }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端请求方法')"
                  prop="method"
                  :show-overflow-tooltip="false"
                >
                  <template #default="{ row }">
                    <bk-tag
                      :theme="methodsEnum[row.backend?.method ?? row.method]"
                    >
                      {{ row.backend?.method ?? row.method }}
                    </bk-tag>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端请求路径')"
                  prop="path"
                >
                  <template #default="{ row }">
                    {{ row.backend?.path ?? row.path }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('资源文档')"
                  prop="doc"
                >
                  <template #default="{ row }">
                    <bk-button
                      text
                      theme="primary"
                    >
                      <doc-fill fill="#3A84FF" />
                      {{ t('详情') }}
                    </bk-button>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('插件数量')"
                  prop="plugin_configs"
                >
                  <template #default="{ row }">
                    <span>{{ row.plugin_configs?.length ?? 0 }}</span>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('操作')"
                  width="200"
                  fixed="right"
                  prop="act"
                >
                  <template #default="{ row }">
                    <bk-button
                      text
                      theme="primary"
                      @click="handleEditResource(row.id, 'edit')"
                    >
                      >
                      {{ t('修改配置') }}
                    </bk-button>
                    <bk-button
                      text
                      theme="primary"
                      class="pl10 pr10"
                      @click="() => {
                        toggleRowUnchecked(row)
                      }"
                    >
                      {{ t('不导入') }}
                    </bk-button>
                  </template>
                </bk-table-column>
              </bk-table>
            </div>
          </template>
        </bk-collapse>
      </section>
      <!--  不导入的资源  -->
      <section class="res-content-wrap unchecked">
        <bk-collapse
          v-model="activeIndexUnchecked"
          :list="collapsePanelListUnchecked"
          header-icon="right-shape"
        >
          <template #title>
            <div class="collapse-panel-title">
              <span>不导入的资源（共{{ tableDataUnchecked.length }}个）</span>
              <bk-input
                :clearable="true"
                :placeholder="t('请输入资源名称，按Enter搜索')"
                :right-icon="'bk-icon icon-search'"
                style="width: 240px;"
                @click.stop.prevent
              />
            </div>
          </template>
          <template #content>
            <div class="collapse-panel-table-wrap">
              <bk-table
                class="table-layout"
                :data="tableDataUnchecked"
                show-overflow-tooltip
                row-key="name"
              >
                <bk-table-column
                  :label="t('资源名称')"
                  prop="name"
                >
                </bk-table-column>
                <bk-table-column
                  :label="t('认证方式')"
                >
                  <template #default="{ row }">
                    {{ getAuthConfigText(row?.auth_config) }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('校验应用权限')"
                >
                  <template #default="{ row }">
                    {{ getPermRequiredText(row?.auth_config) }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('是否公开')"
                >
                  <template #default="{ row }">
                    <span>
                      {{ row.is_public ? t('是') : row.is_public === false ? t('否') : t('是') }}
                    </span>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('允许申请权限')"
                >
                  <template #default="{ row }">
                    {{
                      row.allow_apply_permission ? t('是') : row.allow_apply_permission === false ? t('否') : t('是')
                    }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('前端请求路径')"
                  prop="path"
                >
                </bk-table-column>
                <bk-table-column
                  :label="t('前端请求方法')"
                  prop="method"
                  :show-overflow-tooltip="false"
                >
                  <template #default="{ row }">
                    <bk-tag :theme="methodsEnum[row?.method]">{{ row?.method }}</bk-tag>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端服务')"
                  prop="method"
                >
                  <template #default="{ row }">
                    {{ row.backend?.name ?? 'default' }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端请求方法')"
                  prop="method"
                  :show-overflow-tooltip="false"
                >
                  <template #default="{ row }">
                    <bk-tag
                      :theme="methodsEnum[row.backend?.method ?? row.method]"
                    >
                      {{ row.backend?.method ?? row.method }}
                    </bk-tag>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('后端请求路径')"
                  prop="path"
                >
                  <template #default="{ row }">
                    {{ row.backend?.path ?? row.path }}
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('资源文档')"
                  prop="doc"
                >
                  <template #default="{ row }">
                    <bk-button
                      text
                      theme="primary"
                    >
                      <doc-fill fill="#3A84FF" />
                      {{ t('详情') }}
                    </bk-button>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('插件数量')"
                  prop="plugin_configs"
                >
                  <template #default="{ row }">
                    <span>{{ row.plugin_configs?.length ?? 0 }}</span>
                  </template>
                </bk-table-column>
                <bk-table-column
                  :label="t('操作')"
                  width="200"
                  fixed="right"
                  prop="act"
                >
                  <template #default="{ row }">
                    <bk-button
                      text
                      theme="primary"
                      class="pl10 pr10"
                      @click="() => {
                        toggleRowUnchecked(row)
                      }"
                    >
                      {{ t('恢复导入') }}
                    </bk-button>
                  </template>
                </bk-table-column>
              </bk-table>
            </div>
          </template>
        </bk-collapse>
      </section>
      <!--      <section class="flex-row justify-content-between">-->
      <!--        <div class="info">-->
      <!--          {{ t('请确认以下资源变更，资源配置：') }}-->
      <!--          <span class="add-info">{{ t('新建') }}-->
      <!--            <span class="ag-strong success pl5 pr5">-->
      <!--              {{ createNum }}-->
      <!--            </span>{{ t('条') }}-->
      <!--          </span>-->
      <!--          <span class="add-info">{{ t('覆盖') }}-->
      <!--            <span class="ag-strong danger pl5 pr5">{{ updateNum }}</span>-->
      <!--            {{ t('条') }}-->
      <!--          </span>-->
      <!--          <span v-if="showDoc">-->
      <!--            ，{{ $t('资源文档：') }}-->
      <!--            <span class="add-info">{{ t('新建') }}<span class="ag-strong success pl5 pr5">1</span>{{ t('条') }}</span>-->
      <!--            <span class="add-info">{{ t('覆盖') }}<span class="ag-strong danger pl5 pr5">1</span>{{ t('条') }}</span>-->
      <!--          </span>-->
      <!--        </div>-->
      <!--      </section>-->
    </div>
    <footer class="page-actions-wrap">
      <main class="page-actions">
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
      </main>
    </footer>
  </div>
</template>
<script setup lang="tsx">
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
import {
  Warn,
  Search,
  FilliscreenLine,
  Share,
  InfoLine,
  DocFill,
  LeftTurnLine,
  // Upload,
} from 'bkui-vue/lib/icon';
import yaml from 'js-yaml';
import { JSONPath } from 'jsonpath-plus';
import _ from 'lodash';

import type { IPosition } from 'monaco-editor';
import type { ErrorReasonType, CodeErrorMsgType } from '@/types/common';
import { MethodsEnum } from '@/types';

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
const methodsEnum: any = Object.freeze(MethodsEnum);
const { GLOBAL_CONFIG } = globalProperties;

// 选中的代码错误提示 Tab，默认展示 all 即全部类型的错误提示
const activeCodeMsgType = ref<CodeErrorMsgType>('All');
// 记录代码错误消息
const errorReasons = ref<ErrorReasonType[]>([]);
const isFindPanelVisible = ref(false);

const activeIndexAdd = ref(0);
const collapsePanelListAdd = ref([{ name: '新增资源' }]);

const activeIndexUpdate = ref(0);
const collapsePanelListUpdate = ref([{ name: '更新资源' }]);

const activeIndexUnchecked = ref(0);
const collapsePanelListUnchecked = ref([{ name: '不导入资源' }]);

const tableDataToAdd = computed(() => {
  return tableData.value.filter(data => !data.id && !data._unchecked);
});

const tableDataToUpdate = computed(() => {
  return tableData.value.filter(data => data.id && !data._unchecked);
});
// 被取消导入的资源
const tableDataUnchecked = computed(() => {
  return tableData.value.filter(data => data._unchecked);
});

// 资源新建条数
// const createNum = computed(() => {
//   const results = deDuplication(selections.value.filter(item => !item.id), 'name');
//   return results.length;
// });

// 资源覆盖条数
// const updateNum = computed(() => {
//   const results = deDuplication(selections.value.filter(item => item.id), 'name');
//   return results.length;
// });

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
    const res = await checkResourceImport(apigwId, params);
    tableData.value = res.map(data => ({
      ...data,
      _unchecked: false, // 标记是否不导入
    }));
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


// const deDuplication = (data: any[], k: string) => {
//   const map = new Map();
//   for (const item of data) {
//     if (!map.has(item[k])) {
//       map.set(item[k], item);
//     }
//   }
//   return [...map.values()];
// };

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
};

const getAuthConfigText = (authConfig: string | object | null | undefined) => {
  if (!authConfig) return '--';
  let auth;

  if (typeof authConfig === 'string') {
    auth = JSON.parse(authConfig);
  } else {
    auth = authConfig;
  }
  const tmpArr: string[] = [];

  if (auth?.app_verified_required) {
    tmpArr.push(`${t('蓝鲸应用认证')}`);
  }
  if (auth?.auth_verified_required) {
    tmpArr.push(`${t('用户认证')}`);
  }
  return tmpArr.join(', ') || '--';
};

const getPermRequiredText = (authConfig: string | object | null | undefined) => {
  if (!authConfig) return '--';
  let auth;

  if (typeof authConfig === 'string') {
    auth = JSON.parse(authConfig);
  } else {
    auth = authConfig;
  }
  if (auth?.resource_perm_required) {
    return `${t('校验')}`;
  }
  return `${t('不校验')}`;
};

// 切换资源是否导入
const toggleRowUnchecked = (row: any) => {
  const data = tableData.value.find(d => d.name === row.name);
  if (data) data._unchecked = !data._unchecked;
};

// 还原所有不导入的资源
const handleRecoverAllRes = () => {
  tableData.value.forEach(d => d._unchecked = false);
};

// 编辑资源
const handleEditResource = (id: number) => {
  const name = 'apigwResourceEdit';
  resourceVersionStore.setPageStatus({
    isDetail: false,
    isShowLeft: true,
  });
  router.push({
    name,
    params: {
      resourceId: id,
    },
  });
};

const tempAuthConfig = ref({
  app_verified_required: false,
  auth_verified_required: false,
  resource_perm_required: false,
});

const handleConfirmAuthConfigPopConfirm = (action: 'add' | 'update') => {
  if (tempAuthConfig.value.app_verified_required === false) tempAuthConfig.value.resource_perm_required = false;
  tableData.value.filter(item => !item._unchecked)
    .forEach(data => {
      if ((action === 'add' && !data.id) || (action === 'update' && data.id)) {
        data.auth_config = {
          ...tempAuthConfig.value,
        }
      }
    });
};

const handleCancelAuthConfigPopConfirm = () => {
  tempAuthConfig.value = {
    app_verified_required: false,
    auth_verified_required: false,
    resource_perm_required: false,
  }
}

const renderAuthConfigColLabel = (action: 'add' | 'update') => {
  return (
    <div>
      <div class="auth-config-col-label">
        <span>{t('认证方式')}</span>
        <bk-pop-confirm
          width="430"
          trigger="click"
          title={t('批量修改认证方式')}
          content={
            <div class="multi-edit-popconfirm-wrap auth-config">
              <bk-form model={tempAuthConfig.value} labelWidth="120" labelPosition="right">
                <bk-form-item label={t('认证方式')} required={true}>
                  <bk-checkbox
                    v-model={tempAuthConfig.value.app_verified_required}
                  >
                      <span class="bottom-line" v-bk-tooltips={{ content: t('请求方需提供蓝鲸应用身份信息') }}>
                        {t('蓝鲸应用认证')}
                      </span>
                  </bk-checkbox>
                  <bk-checkbox class="ml40" v-model={tempAuthConfig.value.auth_verified_required}>
                      <span class="bottom-line" v-bk-tooltips={{ content: t('请求方需提供蓝鲸用户身份信息') }}>
                        {t('用户认证')}
                      </span>
                  </bk-checkbox>
                </bk-form-item>
                {tempAuthConfig.value.app_verified_required ?
                  <bk-form-item label={t('检验应用权限')}>
                    <bk-switcher
                      v-model={tempAuthConfig.value.resource_perm_required}
                      theme="primary"
                      size="small"
                    />
                  </bk-form-item> : ''
                }
              </bk-form>
            </div>
          }
          onConfirm={() => handleConfirmAuthConfigPopConfirm(action)}
          onCancel={() => handleCancelAuthConfigPopConfirm()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action ml5 f14 default-c"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改认证方式')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};

const tempPublicConfig = ref({
  is_public: false,
  allow_apply_permission: false,
});

const handleConfirmPublicConfigPopConfirm = (action: 'add' | 'update') => {
  const isPublic = tempPublicConfig.value.is_public;
  const allowApplyPermission = tempPublicConfig.value.allow_apply_permission && isPublic;

  tableData.value.filter(item => !item._unchecked)
    .forEach(item => {
      if ((action === 'add' && !item.id) || (action === 'update' && item.id)) {
        item.is_public = isPublic;
        item.allow_apply_permission = allowApplyPermission;
      }
    });
};

const handleCancelPublicConfigPopConfirm = () => {
  tempPublicConfig.value = {
    is_public: false,
    allow_apply_permission: false,
  }
}

const renderIsPublicColLabel = (action: 'add' | 'update') => {
  return (
    <div>
      <div class="public-config-col-label">
        <span>{t('是否公开')}</span>
        <bk-pop-confirm
          width="320"
          trigger="click"
          title={t('批量修改公开设置')}
          content={
            <div class="multi-edit-popconfirm-wrap public-config">
              <bk-form model={tempPublicConfig.value} labelWidth="100" labelPosition="right">
                <bk-form-item
                  label={t('是否公开')} required={true}
                  description={t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')}
                >
                  <bk-switcher
                    v-model={tempPublicConfig.value.is_public}
                    theme="primary"
                    size="small"
                  />
                </bk-form-item>
                {tempPublicConfig.value.is_public ?
                  <bk-form-item label="">
                    <bk-checkbox
                      v-model={tempPublicConfig.value.allow_apply_permission}
                    >
                      <span class="bottom-line">
                        {t('允许申请权限')}
                      </span>
                    </bk-checkbox>
                  </bk-form-item> : ''
                }
              </bk-form>
            </div>
          }
          onConfirm={() => handleConfirmPublicConfigPopConfirm(action)}
          onCancel={() => handleCancelPublicConfigPopConfirm()}
        >
          <i
            class="apigateway-icon icon-ag-bulk-edit edit-action ml5 f14 default-c"
            v-bk-tooltips={{
              content: (
                <div>
                  {t('批量修改公开设置')}
                </div>
              ),
            }}
          />
        </bk-pop-confirm>
      </div>
    </div>
  );
};
</script>
<style scoped lang="scss">
//$successColor: #34d97b;
//$warningColor: #ffb400;
//$failColor: #ff5656;

.importWrapper {
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

    .stepsIndicator {
      width: 50%;
    }
  }

  .page-actions-wrap {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    padding-left: 48px;
    border-top: 1px solid #DCDEE5;
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

  .monacoEditor {
    width: 100%;
    height: calc(100vh - 240px);
    border-radius: 2px;
    overflow: hidden;

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

.imported-resources-wrap {
  margin: 20px 24px;

  .res-counter-banner {
    height: 40px;
    padding: 0 12px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
  }

  .res-content-wrap {
    //padding: 24px;
    margin-bottom: 12px;
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
  }

  .collapse-panel-title {
    flex-grow: 1;
    display: inline-flex;
    position: relative;
    justify-content: space-between;
    align-items: center;
  }

  .collapse-panel-table-wrap {
    padding-bottom: 24px;
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

</style>
