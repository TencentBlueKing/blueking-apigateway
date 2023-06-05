<template>
  <div class="app-content resource-container">
    <bk-alert class="mb15" type="warning" :title="versionMessage" v-if="needNewVersion && versionMessage"></bk-alert>

    <div class="ag-top-header">
      <bk-button theme="primary" class="fl mr10" @click="handleCreateResource"> {{ $t('新建') }} </bk-button>
      <!-- <bk-button theme="default" class="fl mr10" @click="handleBatchDelete">批量删除</bk-button>
            <bk-button theme="default" class="fl mr10" @click="handleBatchEdit">批量编辑</bk-button> -->

      <!-- <bk-button theme="default" class="fl mr10" @click="handleImportResource"> {{ $t('导入') }} </bk-button> -->
      <bk-dropdown-menu
        trigger="click"
        @show="isHandleBatchShow = true"
        @hide="isHandleBatchShow = false"
        font-size="medium">
        <bk-button slot="dropdown-trigger">
          <span> {{ $t('批量') }} </span>
          <i :class="['dropdown-icon bk-icon icon-angle-down', { 'open': isHandleBatchShow }]"></i>
        </bk-button>
        <ul class="bk-dropdown-list" slot="dropdown-content">
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              @click="handleBatchEdit">
              {{ $t('编辑资源') }}
            </a>
          </li>
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              @click="handleBatchDelete">
              {{ $t('删除资源') }}
            </a>
          </li>
        </ul>
      </bk-dropdown-menu>
      <bk-dropdown-menu
        trigger="click"
        @show="isImportDropdownShow = true"
        @hide="isImportDropdownShow = false"
        font-size="medium">
        <bk-button slot="dropdown-trigger">
          <span> {{ $t('导入') }} </span>
          <i :class="['dropdown-icon bk-icon icon-angle-down', { 'open': isImportDropdownShow }]"></i>
        </bk-button>
        <ul class="bk-dropdown-list" slot="dropdown-content">
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              @click="handleImportResource($event, !hasFiltered)">
              {{ $t('资源配置') }}
            </a>
          </li>
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              @click="handleImportResourceDoc($event, !hasSelected)">
              {{ $t('资源文档') }}
            </a>
          </li>
        </ul>
      </bk-dropdown-menu>

      <bk-dropdown-menu
        trigger="click"
        @show="isExportDropdownShow = true"
        @hide="isExportDropdownShow = false"
        font-size="medium">
        <bk-button slot="dropdown-trigger">
          <span> {{ $t('导出') }} </span>
          <i :class="['dropdown-icon bk-icon icon-angle-down', { 'open': isExportDropdownShow }]"></i>
        </bk-button>
        <ul class="bk-dropdown-list" slot="dropdown-content">
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              :class="{ disabled: !resourceList.length }"
              @click="handleExportAll($event, !resourceList.length)">
              {{ $t('全部资源') }}
            </a>
          </li>
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              :class="{ disabled: !hasFiltered }"
              v-bk-tooltips.right="{ disabled: hasFiltered, content: $t('请先筛选资源') , boundary: 'window' }"
              @click="handleExportFiltered($event, !hasFiltered)">
              {{ $t('已筛选资源') }}
            </a>
          </li>
          <li class="bk-dropdown-item">
            <a
              href="javascript:;"
              :class="{ disabled: !hasSelected }"
              v-bk-tooltips.right="{ disabled: hasSelected, content: $t('请先勾选资源') , boundary: 'window' }"
              @click="handleExportSelected($event, !hasSelected)">
              {{ $t('已选资源') }}
            </a>
          </li>
        </ul>
      </bk-dropdown-menu>
      <bk-button theme="default" @click="handleShowDiff"> {{ $t('版本对比') }} </bk-button>
      <bk-button theme="default" @click="handleCreateResourceVersion"> {{ $t('去发布版本') }} </bk-button>
      <bk-input
        class="fr mr10"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入请求路径、名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 328px;"
        @enter="handleSearch">
      </bk-input>
    </div>

    <bk-table
      style="margin-top: 15px;"
      ref="resourcesTable"
      :data="resourceList"
      :size="setting.size"
      :pagination="pagination"
      :ext-cls="resourceList.length > 0 ? 'ag-resources-table' : 'ag-resource-table'"
      v-bkloading="{ isLoading: isDataLoading, opacity: 1, immediate: true }"
      :default-expand-all="false"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @select="handlePageSelect"
      @select-all="handlePageSelectAll"
      @filter-change="handleFilterChange"
      @expand-change="handlePageExpandChange"
      @row-click="handleRowClick"
      @row-mouse-leave="tdMouseLeave"
      @row-mouse-enter="tdMouseEnter"
      @sort-change="handleSortChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwResources"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column type="expand" width="30" class="ag-expand-cell">
        <template slot-scope="props">
          <ag-loader :is-loading="props.row.isDataLoading" background-color="#dfe0e5">
            <bk-table
              ext-cls="ag-expand-table"
              :ref="`resourceStages_${props.row.id}`"
              :max-height="378"
              :size="'small'"
              :key="props.row.id"
              :data="props.row.stages"
              :outer-border="false"
              :header-cell-style="{ borderRight: 'none' }">
              <div slot="empty">
                <table-empty empty />
              </div>
              <bk-table-column label="" width="90"></bk-table-column>
              <bk-table-column width="280" prop="stage_name" :label="$t('环境信息')" :render-header="$renderHeader"></bk-table-column>
              <bk-table-column width="120" prop="stage_release_status" :label="$t('发布状态')" :render-header="$renderHeader">
                <template slot-scope="resourceItem">
                  <div v-if="resourceItem.row.stage_release_status"><span class="ag-dot success mr5"></span> {{ $t('已发布') }} </div>
                  <div v-else><span class="ag-dot default mr5"></span> {{ $t('未发布') }} </div>
                </template>
              </bk-table-column>
              <bk-table-column prop="resource_version_name" :label="$t('版本')" :show-overflow-tooltip="true">
                <template slot-scope="resourceItem">
                  <span v-if="resourceItem.row.stage_release_status">{{resourceItem.row.resource_version_display}}</span>
                  <span v-else>--</span>
                </template>
              </bk-table-column>
              <bk-table-column prop="resource_url" :label="$t('资源地址')" :show-overflow-tooltip="false" :render-header="$renderHeader">
                <template slot-scope="resourceItem">
                  <div class="resource-url-box" v-if="resourceItem.row.stage_release_status">
                    <bk-popover :content="resourceItem.row.resource_url">
                      <p class="resource-url">
                        {{resourceItem.row.resource_url}}
                      </p>
                    </bk-popover>
                    <i v-bk-tooltips.right="$t('复制')"
                      class="apigateway-icon icon-ag-document copy-btn f14"
                      @click="handleCopy(resourceItem.row.resource_url)">
                    </i>
                  </div>
                  <p v-else>--</p>
                </template>
              </bk-table-column>
              <bk-table-column width="90" :label="$t('操作')">
                <template slot-scope="resourceItem">
                  <bk-button :disabled="!resourceItem.row.stage_release_status" :text="true" @click="handleShowReleaseResource(resourceItem, resourceItem.row)"> {{ $t('查看资源') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </ag-loader>
        </template>
      </bk-table-column>
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column
        sortable
        :label="$t('名称')"
        min-width="160"
        key="name"
        prop="name"
        :show-overflow-tooltip="true">
        <template slot-scope="props">
          <div class="ag-flex">
            <span class="ag-auto-text">
              <span>{{props.row.name || '--'}}</span>
            </span>
            <div>
              <span class="ag-tag primary ml5" v-if="props.row.is_created"> {{ $t('新创建') }} </span>
              <span class="ag-tag success ml5" v-else-if="props.row.has_updated"> {{ $t('有更新') }} </span>
            </div>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column
        v-if="selecteTabledFields.includes('requestMethod')"
        :label="$t('请求方法')"
        prop="method"
        width="100"
        column-key="method"
        :filters="methodFilters"
        :filter-multiple="false"
        key="requestMethod"
        :render-header="$renderHeader">
        <template slot-scope="props">
          <span class="ag-tag" :class="props.row.method.toLowerCase()">{{props.row.method}}</span>
        </template>
      </bk-table-column>
      <bk-table-column
        v-if="selecteTabledFields.includes('requestPath')"
        :label="$t('请求路径')"
        min-width="120"
        prop="path"
        column-key="path"
        sortable
        :show-overflow-tooltip="true"
        key="requestPath"
        :render-header="$renderHeader">
        <template slot-scope="props">
          <div class="ag-flex">
            <div class="ag-auto-text">
              <span>{{props.row.path || '--'}}</span>
            </div>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column
        v-if="selecteTabledFields.includes('doc')"
        width="80"
        :label="$t('文档')"
        prop="doc"
        column-key="doc"
        key="doc">
        <template slot-scope="props">
          <template v-if="!props.row.resource_doc_languages.length">
            <bk-popover content="添加文档" ext-cls="popover-tips-cls">
              <span
                class="ml10"
                @click.stop="handleShowDoc(props.row, 'zh')">
                <span v-show="!props.row.isDoc">--</span>
                <i class="bk-icon apigateway-icon icon-ag-plus plus-class" slot="dropdown-trigger" v-show="props.row.isDoc"></i>
              </span>
            </bk-popover>
          </template>
          <span v-else>
            <span class="document-info" @click.stop="handleShowDoc(props.row, localLanguage === 'en' ? 'en' : 'zh')">
              <i class="bk-icon apigateway-icon icon-ag-document" slot="dropdown-trigger"></i>
              {{ $t('详情') }}
            </span>
            <!-- <span
                            v-for="(item, index) in props.row.resource_doc_languages" :key="index"
                            class="ag-tag languages-tag mr10" @click.stop="handleShowDoc(props.row, item)"
                        >{{resourceDocLanguages[item]}}</span> -->
          </span>
        </template>
      </bk-table-column>
      <bk-table-column
        v-if="selecteTabledFields.includes('labeled')"
        :label="$t('标签')"
        prop="labels"
        column-key="label"
        width="300"
        :filters="tagFilters"
        :filter-multiple="false"
        :show-overflow-tooltip="false"
        key="label">
        <template slot-scope="props">
          <div
            v-if="!props.row.isEditLabel"
            :class="['label-wrapper', 'pl5', { 'label-item-wrapper': props.row.isRowHover }]"
            @click.stop.prevent="tdClick(props.row)">
            <template v-if="props.row.labels.length">
              <bk-popover :content="props.row.labelText.join('; ')" ext-cls="popover-tips-cls">
                <div class="tag-wrapper">
                  <span :ref="props.row.name">
                    <template v-for="(label, index) of props.row.labels">
                      <span class="new-ag-label vm mb5" v-if="index < props.row.tagOrder" :key="label.id">
                        {{label.name}}
                      </span>
                    </template>
                    <template v-if="props.row.labels.length > props.row.tagOrder">
                      <span class="new-ag-label vm mb5">
                        +{{ props.row.labels.length - props.row.tagOrder }}
                        <!-- ... -->
                      </span>
                    </template>
                  </span>
                </div>
              </bk-popover>
              <i v-show="props.row.isRowHover" class="dropdown-icon bk-icon icon-angle-down angle-down-class angle-down-tag"></i>
            </template>
            <template v-else>
              <span class="empty" v-if="props.row.isAddLabel">
                <span class="add-tag">{{ $t('添加标签') }}</span>
                <i class="dropdown-icon bk-icon icon-angle-down angle-down-class"></i>
              </span>
              <span v-else>--</span>
            </template>
          </div>
          <div v-else class="tag-input-wrapper pl10" @click.stop.prevent="selectClick">
            <bk-select
              style="width: 275px;"
              ext-cls="select-wrapper"
              searchable
              multiple
              display-tag
              ref="multiSelect"
              :auto-height="false"
              :show-on-init="true"
              v-model="labelsIds"
              @toggle="toggleSelect"
              @change="changeSelect">
              <!-- 标签最多选择十个 -->
              <bk-option v-for="option in labelList"
                v-bk-tooltips="{ content: $t('标签最多只能选择10个'), disabled: !(!labelsIds.includes(option.id) && labelsIds.length >= 10) }"
                :key="option.id"
                :id="option.id"
                :name="option.name"
                :disabled="!labelsIds.includes(option.id) && labelsIds.length >= 10">
              </bk-option>
              <div slot="extension" style="cursor: pointer;" class="slot-ag" @click="handleShowLabel" @mouseenter="changeLabelBg">
                <template v-if="isCreateLabel">
                  <div class="slot-wrapper">
                    <div class="input-wrapper">
                      <bk-form
                        :label-width="0"
                        form-type="vertical"
                        :model="curLabel"
                        :rules="labelRules"
                        ref="labelForm">
                        <bk-form-item :required="true" :property="'name'">
                          <bk-input v-model="curLabel.name" ref="addLabelInput" @enter="createLabel"></bk-input>
                        </bk-form-item>
                      </bk-form>
                    </div>
                    <div class="ml5 btn-wrapper">
                      <bk-button
                        theme="primary"
                        text
                        @click.stop="createLabel">
                        {{ $t('确定') }}
                      </bk-button>
                      <span>|</span>
                      <bk-button
                        theme="primary"
                        text
                        @click.stop="abrogate">
                        {{ $t('取消') }}
                      </bk-button>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <i class="bk-icon icon-plus-circle mr5"></i> {{ $t('新建标签') }}
                </template>
              </div>
            </bk-select>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column
        v-if="selecteTabledFields.includes('environment')"
        width="240"
        sortable
        :label="$t('环境列表')"
        column-key="environment"
        prop="environment"
        :show-overflow-tooltip="true"
        key="environment">
        <template slot-scope="props">
          {{ $t('已发布') }} <i class="ag-strong success m5">{{props.row.released_stage_count}}</i>,
          {{ $t('未发布') }}<i class="ag-strong m5">{{props.row.unreleased_stage_count}}</i>,
          <bk-button :text="true"> {{ $t('详情') }} </bk-button>
        </template>
      </bk-table-column>
      <bk-table-column
        v-if="selecteTabledFields.includes('updateTime')"
        sortable
        :label="$t('更新时间')"
        width="230"
        column="updated_time"
        prop="updated_time"
        key="updateTime"
        :render-header="$renderHeader">
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="90" class="ag-action" fixed="right" :show-overflow-tooltip="false">
        <template slot-scope="props">
          <bk-button
            class="mr5"
            theme="primary"
            text
            @click.stop="handleEditResource(props.row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-dropdown-menu ref="dropdown" align="right" position-fixed>
            <i class="bk-icon icon-more ag-more-btn ml10 icon-more-hover" slot="dropdown-trigger"></i>
            <ul class="bk-dropdown-list" slot="dropdown-content" style="width: 80px; ">
              <!-- <li>
                                <a href="javascript:;" @click.stop="handleShowDoc(props.row)">文档</a>
                            </li> -->
              <!-- <template v-if="props.row.resource_doc_languages.length < 2">
                                <li>
                                    <a href="javascript:;" @click="handleShowDoc(props.row, switchLanguages(props.row.resource_doc_languages))"> {{ $t('添加文档') }} </a>
                                </li>
                            </template>
                            <template v-else>
                                <li class="disabled" v-bk-tooltips.left="{ content: $t('文档已添加') , boundary: 'window' }">
                                    <a href="javascript:;"> {{ $t('添加文档') }} </a>
                                </li>
                            </template> -->
              <li>
                <a href="javascript:;" @click.stop="handleCloneResource(props.row)"> {{ $t('克隆') }} </a>
              </li>
              <li>
                <a href="javascript:;" @click.stop="handleDeleteResource(props.row)"> {{ $t('删除') }} </a>
              </li>
            </ul>
          </bk-dropdown-menu>
        </template>
      </bk-table-column>
      <bk-table-column type="setting">
        <bk-table-setting-content
          :fields="setting.fields"
          :selected="setting.selectedFields"
          :size="setting.size"
          :max="setting.max"
          @setting-change="handleSettingChange">
        </bk-table-setting-content>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="batchDeleteDialogConf.visiable"
      theme="primary"
      :width="670"
      :title="batchDeleteDialogConfTitle"
      :mask-close="true"
      @cancel="batchDeleteDialogConf.visiable = false"
      @confirm="batchRemoveResource">
      <div>
        <bk-table
          :data="resourceSelectedList"
          :size="'small'"
          :key="deleteTableIndex"
          :max-height="280">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
        </bk-table>
        <p class="ag-alert warning mt10">
          <i class="apigateway-icon icon-ag-info"></i>
          {{ $t('删除资源后，需要生成新的版本，并发布到目标环境才能生效') }}
        </p>
      </div>
    </bk-dialog>

    <bk-dialog
      v-model="exportDialogConf.visiable"
      theme="primary"
      :mask-close="false"
      :width="500"
      :title="$t('请选择导出的格式')"
      @cancel="exportDialogConf.visiable = false"
      @confirm="exportDownload">
      <div>
        <span class="rosource-number" v-if="hasSelected && exportParams.resource_ids"> {{ selectResource }} </span>
        <span class="rosource-number" v-if="hasFiltered && exportParams.export_type === 'filtered'"> {{ resourceCount }} </span>
        <span class="rosource-number" v-if="exportParams.export_type === 'all'"> {{ $t('选择全部资源') }} </span>
        <bk-form :label-width="128" class="mt20 mb20">
          <bk-form-item :label="$t('导出内容')">
            <bk-radio-group v-model="exportFileDocType">
              <bk-radio class="mr50 mt5" :value="'resource'"> {{ $t('资源配置') }} </bk-radio>
              <bk-radio :value="'docs'"> {{ $t('资源文档') }} </bk-radio>
            </bk-radio-group>
          </bk-form-item>
          <bk-form-item :label="$t('导出格式')" v-if="exportFileDocType === 'resource'">
            <bk-radio-group v-model="exportFileType">
              <bk-radio class="mr40 mt5" :value="'yaml'"> {{ $t('YAML格式') }} </bk-radio>
              <bk-radio :value="'json'"> {{ $t('JSON格式') }} </bk-radio>
            </bk-radio-group>
          </bk-form-item>
          <bk-form-item :label="$t('导出格式')" v-else>
            <bk-radio-group v-model="exportFileType">
              <bk-radio class="mr50 mt5" :value="'zip'">Zip</bk-radio>
              <bk-radio style="margin-left:38px" :value="'tgz'">Tgz</bk-radio>
            </bk-radio-group>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-dialog>

    <bk-dialog
      v-model="batchEditDialogConf.visiable"
      theme="primary"
      :mask-close="false"
      :width="468"
      :title="batchEditDialogConfTitle"
      @cancel="batchEditDialogConf.visiable = false"
      @confirm="batchEditResource">
      <section class="ag-panel small mt15">
        <div class="panel-key">
          <strong> {{ $t('基本信息') }} </strong>
        </div>
        <div class="panel-content ver-middle" style="display: block;">
          <div style="display: block; width: 100%;" class="mb15 mt15">
            <bk-checkbox
              :true-value="true"
              :false-value="false"
              v-model="batchEditParams.isPublic"
              @change="handlePublicChange">
              {{ $t('是否公开') }}
            </bk-checkbox>
          </div>
          <div style="display: block; width: 100%;" class="mb15">
            <bk-checkbox
              :true-value="true"
              :false-value="false"
              :disabled="!batchEditParams.isPublic"
              v-model="batchEditParams.allowApply">
              {{ $t('允许申请权限') }}
            </bk-checkbox>
            <i class="apigateway-icon icon-ag-help" v-bk-tooltips="$t('允许，则任何蓝鲸应用可在蓝鲸开发者中心申请资源的访问权限；否则，只能通过网关管理员主动授权为某应用添加权限')"></i>
          </div>
        </div>
      </section>
    </bk-dialog>

    <bk-dialog
      v-model="deleteDialogConf.visiable"
      theme="primary"
      :width="670"
      :title="deleteDialogConfTitle"
      :mask-close="true"
      @cancel="deleteDialogConf.visiable = false"
      @confirm="removeResource">
      <div>
        <bk-table
          :data="deleteSelectedList"
          :size="'small'"
          :key="deleteTableIndex"
          :max-height="280">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
        </bk-table>
        <p class="ag-alert warning mt10">
          <i class="apigateway-icon icon-ag-info"></i>
          {{ $t('删除资源后，需要生成新的版本，并发布到目标环境才能生效') }}
        </p>
      </div>
    </bk-dialog>

    <version-create-dialog
      ref="versionCreateDialog"
      :title="$t('资源更新，是否生成新版本后再发布？')"
      :is-new="needNewVersion"
      :message="versionMessage"
      :is-auto-direct="true">
    </version-create-dialog>

    <bk-sideslider
      :is-show.sync="diffSidesliderConf.isShow"
      :title="diffSidesliderConf.title"
      :width="diffSidesliderConf.width"
      :quick-close="true">
      <div slot="content" class="p20">
        <version-diff ref="diffRef" :apigw-id="apigwId" :source-id="diffSourceId" :target-id="diffTargetId"></version-diff>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :is-show.sync="docSliderConf.isShow"
      ext-cls="doc-sideslider-cls"
      :quick-close="true"
      :title="docSliderConf.title"
      :width="780"
      :before-close="handleMarkdownClose">
      <div slot="content" v-bkloading="{ isLoading: docSliderConf.isLoading, opacity: 1 }" style="min-height: 350px;">
        <template v-if="!docSliderConf.isLoading">
          <div class="doc-sideslider-wrapper" v-if="!docSliderConf.isLoading">
            <div class="ag-markdown-view pb15" :class="docSliderConf.isEdited ? '' : 'text-center'">
              <h3 v-if="docSliderConf.isEdited"> {{ $t('文档类型') }} </h3>
              <div class="bk-button-group">
                <bk-button
                  class="tab-button"
                  :class="docSliderConf.languages === 'zh' ? 'is-selected' : ''"
                  @click="docSliderConf.languages = 'zh'"
                  :disabled="docSliderConf.isEdited && docSliderConf.languages === 'en'"
                >
                  <!-- 中文文档 -->
                  <li class="bk-dropdown-item">
                    <a
                      href="javascript:;"
                      :class="{ disabled: docSliderConf.isEdited && docSliderConf.languages === 'en' }"
                      v-bk-tooltips.top="{ disabled: !docSliderConf.isEdited || (docSliderConf.isEdited && docSliderConf.languages === 'zh'), content: $t('不允许修改文档类型') , boundary: 'window' }"
                    >
                      {{ $t('中文文档') }}
                    </a>
                  </li>
                </bk-button>
                <bk-button
                  class="tab-button"
                  :class="docSliderConf.languages === 'en' ? 'is-selected' : ''"
                  @click="docSliderConf.languages = 'en'"
                  :disabled="docSliderConf.isEdited && docSliderConf.languages === 'zh'"
                >
                  <!-- 英文文档 -->
                  <li class="bk-dropdown-item">
                    <a
                      href="javascript:;"
                      :class="{ disabled: docSliderConf.isEdited && docSliderConf.languages === 'zh' }"
                      v-bk-tooltips.top="{ disabled: !docSliderConf.isEdited || (docSliderConf.isEdited && docSliderConf.languages === 'en'), content: $t('不允许修改文档类型') , boundary: 'window' }"
                    >
                      {{ $t('英文文档') }}
                    </a>
                  </li>
                </bk-button>
              </div>
            </div>
            <div v-show="!docSliderConf.isEmpty">
              <div class="ag-markdown-view">
                <h3> {{ $t('请求方法/请求路径') }} </h3>
                <p class="pb15">
                  <span class="ag-tag" :class="curResource.method.toLowerCase()">{{curResource.method}}</span>
                  {{curResource.path}}
                </p>
              </div>
              <div class="ag-markdown-view" v-html="docSliderConf.markdownHtml" v-show="!docSliderConf.isEdited"></div>
              <div class="ag-markdown-editor">
                <mavon-editor
                  ref="markdown"
                  v-model="docSliderConf.markdownDoc"
                  v-show="docSliderConf.isEdited"
                  :language="localLanguage"
                  :box-shadow="false"
                  :subfield="false"
                  :ishljs="true"
                  :code-style="'monokai'"
                  :toolbars="toolbars"
                  :tab-size="4"
                />
              </div>
            </div>
                            
            <div v-show="docSliderConf.isEmpty">
              <div class="ap-nodata">
                <table-empty empty :empty-title="docSliderConf.languages === 'zh' ? $t('您尚未创建中文文档') : $t('您尚未创建英文文档')" />
                <bk-button class="mt20" theme="primary" style="width: 120px;" @click="handleEditMarkdown('create')"> {{ $t('立即创建') }} </bk-button>
              </div>
            </div>
                        
            <template v-if="isActionBtnShow">
              <template v-if="!docSliderConf.isEdited">
                <div class="ag-alert primary mt10" v-if="docSliderConf.resourceDocLink">
                  <template>
                    <i class="apigateway-icon icon-ag-info"></i> {{ $t('资源文档修改后，需生成新版本并发布到任一环境，才能生效') }}，
                    <a class="ag-link primary" target="_blank" :href="docSliderConf.resourceDocLink"> {{ $t('查看线上文档') }} </a>
                  </template>
                </div>
              </template>
            </template>
          </div>
          <!-- 侧边吸附效果 -->
          <div class="doc-btn-wrapper" v-if="isActionBtnShow">
            <template v-if="docSliderConf.isEdited">
              <bk-button class="mr5" theme="primary" style="width: 100px;" @click="handleSaveMarkdown" :loading="isDataSaving">{{isUpdate ? $t('更新') : $t('提交')}}</bk-button>
              <bk-button theme="default" style="width: 100px;" @click="handleCancelMarkdown"> {{ $t('取消') }} </bk-button>
            </template>
            <template v-else>
              <bk-button class="mr5" theme="primary" style="width: 100px;" @click="handleEditMarkdown('edit')"> {{ $t('修改') }} </bk-button>
              <bk-button style="width: 100px;" @click="handleDeleteMarkdown"> {{ $t('删除') }} </bk-button>
            </template>
          </div>
        </template>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :is-show.sync="detailSidesliderConf.isShow"
      :title="detailSidesliderConf.title"
      :quick-close="true"
      :width="760">
      <div slot="content" class="pt10 pl30 pr30 pb30" v-bkloading="{ isLoading: isDetailLoading, opacity: 1 }" style="min-height: 250px;">
        <resource-detail :cur-resource="curReleaseResource" v-if="!isDetailLoading"></resource-detail>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
  import Vue from 'vue'
  import { catchErrorHandler, clearFilter } from '@/common/util'
  import mavonEditor from 'mavon-editor'
  import 'mavon-editor/dist/css/index.css'
  import versionCreateDialog from '@/components/create-version'
  import resourceDetail from '@/components/resource-detail'
  import versionDiff from '@/components/version-diff'
  import _ from 'lodash'
  import { bkTableSettingContent } from 'bk-magic-vue'

  Vue.use(mavonEditor)
  export default {
    components: {
      versionCreateDialog,
      resourceDetail,
      versionDiff,
      bkTableSettingContent
    },
    data () {
      const fields = [{
        id: 'requestMethod',
        label: this.$t('请求方法')
      }, {
        id: 'requestPath',
        label: this.$t('请求路径')
      }, {
        id: 'doc',
        label: this.$t('文档')
      }, {
        id: 'labeled',
        label: this.$t('标签')
      }, {
        id: 'environment',
        label: this.$t('环境列表')
      }, {
        id: 'updateTime',
        label: this.$t('更新时间')
      }]
      return {
        keyword: '',
        orderBy: '',
        filterMethod: '',
        filterLabel: '',
        isPageLoading: true,
        isDataLoading: false,
        isDetailLoading: false,
        isDataSaving: false,
        exportFileType: 'yaml',
        exportFileDocType: 'resource',
        exportDialogConf: {
          visiable: false
        },
        resourceSelectedList: [],
        deleteSelectedList: [],
        deleteTableIndex: 0,
        resourceList: [],
        labelList: [],
        diffSidesliderConf: {
          isShow: false,
          width: 1040,
          title: this.$t('版本资源对比')
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        detailSidesliderConf: {
          isShow: false
        },
        batchEditParams: {
          ids: [],
          isPublic: true,
          allowApply: true
        },
        resourceDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('新建标签')
        },
        curReleaseResource: null,
        needNewVersion: false,
        versionMessage: '',

        isExportDropdownShow: false,
        isImportDropdownShow: false,
        isHandleBatchShow: false,

        curResource: {
          name: '',
          method: ''
        },
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 32,
              message: this.$t('不能多于32个字符'),
              trigger: 'blur'
            }
          ],
          title: [
            {
              required: true,
              message: this.$t('请填写名称'),
              trigger: 'blur'
            }
          ]
        },
        isActionBtnShow: false,
        isUpdate: false,
        docSliderConf: {
          title: '',
          markdownDoc: '',
          originMarkdownDoc: '',
          markdownHtml: '',
          resourceDocLink: '',
          hasChange: false,
          isEdited: false,
          isShow: false,
          isDataSaving: false,
          isLoading: false,
          languages: 'zh',
          isEmpty: false,
          hasHandle: false
        },
        offlineDialogConf: {
          visiable: false
        },
        deleteDialogConf: {
          visiable: false
        },
        batchDeleteDialogConf: {
          visiable: false
        },
        batchEditDialogConf: {
          visiable: false
        },
        toolbars: {
          bold: true,
          italic: true,
          header: true,
          underline: true,
          strikethrough: false,
          mark: true,
          superscript: false,
          subscript: false,
          quote: true,
          ol: true,
          ul: true,
          link: true,
          imagelink: false,
          code: true,
          table: true,
          fullscreen: true,
          readmodel: true,
          htmlcode: false,
          help: false,
          /* 1.3.5 */
          undo: false,
          redo: false,
          trash: false,
          save: false,
          /* 1.4.2 */
          navigation: false,
          /* 2.1.8 */
          alignleft: true,
          aligncenter: true,
          alignright: true,
          /* 2.2.1 */
          subfield: true,
          preview: true
        },
        diffSourceId: '',
        diffTargetId: '',
        resourceDocLanguages: { 'zh': this.$t('中文'), 'en': this.$t('英文') },
        exportParams: {
          resource_ids: ''
        },
        setting: {
          max: 3,
          fields: fields,
          selectedFields: fields.slice(0, 4),
          size: 'small'
        },
        selecteTabledFields: ['requestMethod', 'requestPath', 'doc', 'labeled'],
        labelsIds: [],
        curLabel: {
          name: ''
        },
        labelRules: {
          name: [
            {
              max: 32,
              message: this.$t('不能多于32个字符'),
              trigger: 'change'
            }
          ]
        },
        isRequest: true,
        isCreateLabel: false,
        selectedEl: null,
        oldLabelsIds: [],
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        isEnter: false
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      methodFilters () {
        return this.$store.state.options.methodList.map(item => {
          return {
            value: item.id,
            text: item.id

          }
        })
      },
      tagFilters () {
        const labels = this.labelList.map(item => {
          return {
            value: item.name,
            text: item.name
          }
        })
        return labels
      },
      hasSelected () {
        return this.resourceSelectedList.length > 0
      },
      hasFiltered () {
        return this.filterMethod.length > 0 || this.filterLabel.length > 0
      },
      stateLabelName () {
        return this.$store.state.resource.labelName
      },
      stateMethodName () {
        return this.$store.state.resource.methodName
      },
      batchDeleteDialogConfTitle () {
        return this.$t(`确定要删除以下{resourceLength}个资源？`, { resourceLength: this.resourceSelectedList.length })
      },
      deleteDialogConfTitle () {
        return this.$t(`确定要删除以下{deleteLength}个资源？`, { deleteLength: this.deleteSelectedList.length })
      },
      selectResource () {
        return this.$t(`已选择 {resourceIdsLength} 个资源`, { resourceIdsLength: this.exportParams.resource_ids.length })
      },
      resourceCount () {
        return this.$t(`已选择 {count} 个资源`, { count: this.pagination.count })
      },
      batchEditDialogConfTitle () {
        return this.$t(`批量编辑资源共{resourceSelectedLength}个`, { resourceSelectedLength: this.resourceSelectedList.length })
      },
      localLanguage () {
        return this.$store.state.localLanguage
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      orderBy () {
        this.handleSearch()
      },
      filterMethod () {
        this.handleSearch()
      },
      filterLabel () {
        this.handleSearch()
      },
      'docSliderConf.isShow' (value) {
        if (!value && this.docSliderConf.hasHandle) {
          this.getApigwResources()
          this.docSliderConf.hasHandle = false
        }
      },
      'docSliderConf.languages' (value) {
        this.docSliderConf.isLoading = true
        setTimeout(() => {
          this.docSliderConf.isLoading = false
        }, 1000)
        this.showMarkDownContent(value)
      },
      exportFileDocType (value) {
        if (value === 'resource') {
          this.exportFileType = 'yaml'
        } else {
          this.exportFileType = 'zip'
        }
      }
    },
    created () {
      this.init()
    },
    mounted () {
      // 回显筛选高亮
      if (this.$refs.resourcesTable.store && this.stateLabelName) {
        const currentHighlight = this.$refs.resourcesTable.store.states.originColumns.find(item => item.property === 'labels')
        currentHighlight.filteredValue.push(this.stateLabelName)
      }
      if (this.$refs.resourcesTable.store && this.stateMethodName) {
        const currentHighlight = this.$refs.resourcesTable.store.states.originColumns.find(item => item.property === 'method')
        currentHighlight.filteredValue.push(this.stateMethodName)
      }
      const resourceFields = localStorage.getItem('resource-fields')
      if (resourceFields) {
        this.setting.selectedFields = JSON.parse(resourceFields)
        this.selecteTabledFields = JSON.parse(resourceFields).reduce((p, v) => {
          p.push(v.id)
          return p
        }, [])
      }
    },
    beforeDestroy () {
      this.removeEvent()
    },
    methods: {
      init () {
        this.updateCurrent()
        this.getApigwResources()
        this.getApigwLabels()
      },

      updateCurrent () {
        if (this.$route.params.current || this.$route.params.limit) {
          this.pagination.current = this.$route.params.current
          this.pagination.limit = this.$route.params.limit
          this.keyword = this.$route.params.keyword
        }
      },

      async getApigwResources (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          query: this.keyword,
          order_by: this.orderBy
        }

        if (this.stateMethodName) {
          pageParams['method'] = this.stateMethodName.toLowerCase()
          this.filterMethod = this.stateMethodName.toLowerCase()
        }

        pageParams['label_name'] = this.stateLabelName
        this.filterLabel = this.stateLabelName

        this.isDataLoading = true
        try {
          // 获取资源列表
          const res = await this.$store.dispatch('resource/getApigwResources', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.isDataLoading = false
            item.stages = []
            item.name = item.name || '--'
            item.description = item.description || '--'
            item.updated_time = item.updated_time || '--'
            item.tag = item.tag || '--'
            item.labelText = item.labels.map(label => {
              return label.name
            })
          })
          this.resourceList = res.data.results
          this.updateTableEmptyConfig()
          this.resourceList.forEach(item => {
            this.$set(item, 'isEditLabel', false)
            this.$set(item, 'isDoc', false)
            this.$set(item, 'isRowHover', false)
            this.$set(item, 'isAddLabel', false)
            this.$set(item, 'tagOrder', 3)
          })
          this.pagination.count = res.data.count
          this.resetParams()

          // 获取资源是否需要发版本更新
          this.checkNeedNewVersion()
          this.$nextTick(() => {
            this.isTagRef()
          })
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          catchErrorHandler(e, this)
          this.tableEmptyConf.isAbnormal = true
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getApigwLabels (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('label/getApigwLabels', { apigwId, pageParams })

          this.labelList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      resetParams () {
        this.resourceSelectedList = []
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwResources(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwResources(newPage)
      },

      handleCreateResource () {
        this.$router.push({
          name: 'apigwResourceCreate'
        })
      },

      handleImportResource () {
        this.$router.push({
          name: 'apigwResourceImport'
        })
      },

      handleImportResourceDoc () {
        this.$router.push({
          name: 'apigwResourceImportDoc'
        })
      },

      async addResource () {
        try {
          const data = { name: this.curResource.name }
          const apigwId = this.apigwId
          await this.$store.dispatch('resource/addApigwResource', { apigwId, data })
          this.resourceDialogConf.visiable = false
          this.clearResourceForm()
          this.getApigwResources()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async updateResource () {
        try {
          const data = { name: this.curResource.name }
          const apigwId = this.apigwId
          const resourceId = this.curResource.id
          await this.$store.dispatch('resource/updateApigwResource', { apigwId, resourceId, data })
          this.resourceDialogConf.visiable = false
          this.clearResourceForm()
          this.getApigwResources()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async offlineResource () {
        try {
          const apigwId = this.apigwId
          const resourceId = this.curResource.id
          const data = { status: 0 }

          await this.$store.dispatch('resource/updateApigwResourceStatus', { apigwId, resourceId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('下线成功！')
          })
          this.curResource.status = 0
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async removeResource () {
        try {
          const apigwId = this.apigwId
          const resourceId = this.curResource.id
          await this.$store.dispatch('resource/deleteApigwResource', { apigwId, resourceId })
          // 当前页只有一条数据
          if (this.resourceList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getApigwResources()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async batchRemoveResource () {
        const ids = this.resourceSelectedList.map(resource => resource.id)
        const data = { ids }
        const apigwId = this.apigwId

        try {
          await this.$store.dispatch('resource/batchDeleteApigwResource', { apigwId, data })
          this.getApigwResources()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('批量删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async createResourceVersion () {
        this.$bkMessage({
          theme: 'error',
          message: this.$t('第二阶段功能')
        })
      },

      async batchEditResource () {
        const ids = this.resourceSelectedList.map(resource => resource.id)
        const data = {
          ids: ids,
          is_public: this.batchEditParams.isPublic,
          allow_apply_permission: this.batchEditParams.allowApply
        }
        const apigwId = this.apigwId

        try {
          await this.$store.dispatch('resource/batchEditApigwResource', { apigwId, data })
          this.getApigwResources()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('批量编辑成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleSearch (event) {
        this.pagination.current = this.$route.params.current || 1
        this.pagination.count = 0
        this.getApigwResources()
        this.$route.params.current = 1
      },

      handleCopy (text) {
        this.$copyText(text).then((e) => {
          this.$bkMessage({
            theme: 'success',
            limit: 1,
            message: this.$t('复制成功')
          })
        }, () => {
          this.$bkMessage({
            theme: 'error',
            limit: 1,
            message: this.$t('复制失败')
          })
        })
      },

      handleRename (data) {
        this.curResource = JSON.parse(JSON.stringify(data))
        this.resourceDialogConf.title = this.$t('重命名标签')
        this.resourceDialogConf.visiable = true
      },

      handleEditResource (data) {
        this.$router.push({
          name: 'apigwResourceEdit',
          params: {
            id: this.apigwId,
            resourceId: data.id,
            current: this.pagination.current,
            limit: this.pagination.limit,
            keyword: this.keyword
          }
        })
      },

      handleOfflineResource (data) {
        if (!data.status) {
          return false
        }
        this.curResource = data
        this.offlineDialogConf.visiable = true
      },

      handleDeleteResource (data) {
        this.curResource = data
        this.deleteSelectedList = [data]
        this.deleteTableIndex++
        this.deleteDialogConf.visiable = true
      },

      handleShowDiff (data) {
        this.diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280
        this.diffSidesliderConf.isShow = true
        this.diffSourceId = ''
        this.diffTargetId = ''
      },

      handleBatchDelete () {
        if (!this.resourceSelectedList.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要删除的资源')
          })
          return false
        }

        this.deleteTableIndex++
        this.batchDeleteDialogConf.visiable = true
      },

      handleBatchEdit () {
        if (!this.resourceSelectedList.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要编辑的资源')
          })
          return false
        }
        this.batchEditParams.isPublic = true
        this.batchEditParams.allowApply = true
        this.batchEditDialogConf.visiable = true
      },

      handlePageSelect (selection, row) {
        this.resourceSelectedList = selection
      },

      handlePageSelectAll (selection, row) {
        this.resourceSelectedList = selection
      },

      async checkNeedNewVersion () {
        try {
          const res = await this.$store.dispatch('resource/checkNeedNewVersion', {
            apigwId: this.apigwId,
            useGlobalMessage: false
          })
          this.needNewVersion = res.data.need_new_version
          this.versionMessage = res.message
        } catch (e) {
          // catchErrorHandler(e, this)
          this.needNewVersion = false
          this.versionMessage = e.message
        }
      },
      // 保存成功需要更新文档内容
      async reacGetDoc () {
        try {
          const res = await this.$store.dispatch('resource/getApigwResourceDoc', {
            apigwId: this.apigwId,
            resourceId: this.curResource.id
          })
          this.docData = res.data
          const data = _.cloneDeep(this.docData).find(e => e.language === this.docSliderConf.languages)
          this.docSliderConf.id = data.id
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      async handleCreateResourceVersion () {
        try {
          const res = await this.$store.dispatch('resource/checkNeedNewVersion', {
            apigwId: this.apigwId,
            useGlobalMessage: true
          })
          this.needNewVersion = res.data.need_new_version
          this.versionMessage = res.message

          if (this.needNewVersion) {
            this.$refs.versionCreateDialog.show()
          } else {
            this.$router.push({
              name: 'apigwVersionCreate',
              params: {
                id: this.apigwId
              },
              query: {
                from: 'apigwResource'
              }
            })
          }
        } catch (e) {
          catchErrorHandler(e, this)
          this.needNewVersion = false
          this.versionMessage = e.message
        }
      },

      handleCloneResource (data) {
        this.$router.push({
          name: 'apigwResourceClone',
          params: {
            id: this.apigwId,
            resourceId: data.id
          }
        })
      },

      methodFilterMethod (value, row, column) {
        this.filterMethod = value
        return true
      },

      pathFilterMethod (value, row, column) {
        const property = column.property
        return row[property] === value
      },

      tagFilterMethod (value, row, column) {
        const property = column.property
        const labelIds = row[property].map(label => {
          return label.id
        })
        return labelIds.includes(Number(value))
      },

      handleFilterChange (filters) {
        if (filters.method) {
          this.$store.commit('resource/setmethodName', filters.method[0] || '')
          this.filterMethod = filters.method[0] ? filters.method[0] : ''
        }

        if (filters.label) {
          this.$store.commit('resource/setLabelName', filters.label[0] || '')
          this.filterLabel = filters.label[0] ? filters.label[0] : ''
        }
      },

      async handleShowDoc (data, languages) {
        this.curResource = data
        // this.docSliderConf.title = `${data.method}: ${data.path}` data
        this.docSliderConf.title = `${this.$t('文档详情')}【${data.name}】`
        this.docSliderConf.isShow = true
        this.docSliderConf.isEdited = false
        this.docSliderConf.isLoading = true
        this.isActionBtnShow = false
        this.docSliderConf.hasChange = false
        this.docSliderConf.markdownHtml = ''
        this.docSliderConf.markdownDoc = ''
        this.docSliderConf.originMarkdownDoc = ''

        try {
          const res = await this.$store.dispatch('resource/getApigwResourceDoc', {
            apigwId: this.apigwId,
            resourceId: data.id
          })
          this.docData = res.data
          this.$set(this.docSliderConf, 'languages', languages || 'zh')
          this.showMarkDownContent(languages)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.docSliderConf.isLoading = false
          }, 1000)
        }
      },

      showMarkDownContent (languages) {
        const data = _.cloneDeep(this.docData).find(e => e.language === languages)
        this.docSliderConf.markdownDoc = data.content
        this.docSliderConf.resourceDocLink = data.resource_doc_link || ''
        this.docSliderConf.originMarkdownDoc = data.content
        this.docSliderConf.id = data.id || ''
        this.docSliderConf.isEmpty = !data.id
        this.isActionBtnShow = !!data.id
        setTimeout(() => {
          this.docSliderConf.markdownHtml = this.$refs.markdown.markdownIt.render(data.content)
        }, 1200)
      },

      async handleSaveMarkdown () {
        if (!this.docSliderConf.markdownDoc) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入文档内容')
          })
          return false
        }
        try {
          const data = {
            type: 'markdown',
            language: this.docSliderConf.languages,
            content: this.docSliderConf.markdownDoc
          }
          this.docSliderConf.isDataSaving = true
          let dispatchUrl = 'resource/saveApigwResourceDoc'
          const dispatchData = {
            apigwId: this.apigwId,
            resourceId: this.curResource.id,
            data
          }
          if (this.isUpdate) {
            dispatchUrl = 'resource/updateApigwResourceDoc'
            dispatchData.id = this.docSliderConf.id
          }
          await this.$store.dispatch(dispatchUrl, dispatchData)
          this.$nextTick(() => {
            this.docSliderConf.originMarkdownDoc = this.docSliderConf.markdownDoc
            this.docSliderConf.markdownHtml = this.$refs.markdown.markdownIt.render(this.docSliderConf.markdownDoc)
          })
          this.docSliderConf.isEdited = false
          this.docSliderConf.hasChange = false
          this.docSliderConf.hasHandle = true

          this.$bkMessage({
            theme: 'success',
            message: this.$t('保存成功！')
          })
          this.checkNeedNewVersion()
          this.docSliderConf.title = `${this.$t('文档详情')}【${this.curResource.name}】`
          if (!this.isUpdate) {
            this.reacGetDoc()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.docSliderConf.isDataSaving = false
        }
      },

      handleCancelMarkdown () {
        this.docSliderConf.title = `${this.$t('文档详情')}【${this.curResource.name}】`
        const self = this
        if (this.docSliderConf.originMarkdownDoc !== this.docSliderConf.markdownDoc) {
          this.$bkInfo({
            title: this.$t('确认要放弃编辑？'),
            subTitle: this.$t('离开当前页面，当前填写内容将不会保存'),
            confirmFn () {
              self.docSliderConf.hasChange = false
              self.docSliderConf.isEdited = false
              self.docSliderConf.markdownDoc = self.docSliderConf.originMarkdownDoc
              if (!self.isUpdate) {
                self.docSliderConf.isShow = false
              }
            }
          })
        } else {
          self.docSliderConf.hasChange = false
          self.docSliderConf.isEdited = false
          if (!this.isUpdate) {
            this.docSliderConf.isShow = false
          }
        }
      },

      // 修改markdown
      handleEditMarkdown (type) {
        this.docSliderConf.isEdited = true
        this.docSliderConf.isEmpty = false
        this.isActionBtnShow = true
        this.isUpdate = type === 'edit'
        this.docSliderConf.title = `${this.$t('创建文档')}【${this.curResource.name}】}`
        if (this.isUpdate) {
          this.docSliderConf.title = `${this.$t('更新文档')}【${this.curResource.name}】}`
        } else {
          const data = _.cloneDeep(this.docData).find(e => e.language === this.docSliderConf.languages)
          this.docSliderConf.markdownDoc = data.content
        }
      },

      // 删除markdown确认
      handleDeleteMarkdown () {
        const self = this
        this.$bkInfo({
          title: this.$t('确认要删除该文档？'),
          confirmFn () {
            self.deleteApigw()
          }
        })
      },

      async deleteApigw () {
        try {
          await this.$store.dispatch('resource/deleteApigwResourceDoc', {
            apigwId: this.apigwId,
            resourceId: this.curResource.id,
            id: this.docSliderConf.id
          })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
          this.reacGetDoc()
          this.docSliderConf.isEmpty = true
          this.docSliderConf.hasHandle = true
          this.isActionBtnShow = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.docSliderConf.isLoading = false
          }, 1000)
        }
      },

      handleMarkdownChange () {
        this.docSliderConf.hasChange = true
      },

      handleMarkdownClose () {
        const self = this
        if (this.docSliderConf.originMarkdownDoc !== this.docSliderConf.markdownDoc) {
          this.$bkInfo({
            title: this.$t('确认要放弃编辑？'),
            subTitle: this.$t('离开当前页面，当前填写内容将不会保存'),
            confirmFn () {
              self.docSliderConf.hasChange = false
              self.docSliderConf.isEdited = false
              self.docSliderConf.markdownDoc = self.docSliderConf.originMarkdownDoc
              if (!self.isUpdate) {
                self.docSliderConf.isShow = false
              }
            }
          })
          return false
        }
        return true
      },

      handleSortChange (params) {
        if (params.prop === 'name') {
          if (params.order === 'descending') {
            this.orderBy = '-name'
          } else if (params.order === 'ascending') {
            this.orderBy = 'name'
          } else {
            this.orderBy = ''
          }
        }

        if (params.prop === 'path') {
          if (params.order === 'descending') {
            this.orderBy = '-path'
          } else if (params.order === 'ascending') {
            this.orderBy = 'path'
          } else {
            this.orderBy = ''
          }
        }

        if (params.prop === 'updated_time') {
          if (params.order === 'descending') {
            this.orderBy = '-updated_time'
          } else if (params.order === 'ascending') {
            this.orderBy = 'updated_time'
          } else {
            this.orderBy = ''
          }
        }
      },

      handleExportAll (event, disabled) {
        if (disabled) {
          event.stopPropagation()
          return false
        }

        this.exportParams = {
          export_type: 'all'
        }
        this.exportDialogConf.visiable = true
        this.exportFileDocType = 'resource'
        this.exportFileType = 'yaml'
      },

      handleExportSelected (event, disabled) {
        if (disabled) {
          event.stopPropagation()
          return false
        }

        this.exportParams = {
          export_type: 'selected',
          resource_ids: this.resourceSelectedList.map(item => item.id)
        }

        this.exportDialogConf.visiable = true
        this.exportFileDocType = 'resource'
        this.exportFileType = 'yaml'
      },

      handleExportFiltered (event, disabled) {
        if (disabled) {
          event.stopPropagation()
          return false
        }

        this.exportParams = {
          export_type: 'filtered',
          query: this.keyword,
          method: this.filterMethod.toLowerCase(),
          label_name: this.filterLabel
        }

        this.exportDialogConf.visiable = true
      },

      async handlePageExpandChange (row, expandedRows) {
        if (row.isDataLoading || row.stages.length) {
          return false
        }
        row.isDataLoading = true
        try {
          const res = await this.$store.dispatch('resource/getResourceStages', {
            apigwId: this.apigwId,
            resourceId: row.id
          })
          row.stages = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          row.isDataLoading = false
        }
      },

      async handleShowReleaseResource (data, stage) {
        if (this.isDetailLoading) {
          return false
        }
        this.isDetailLoading = true
        try {
          const res = await this.$store.dispatch('resource/getReleaseResource', {
            apigwId: this.apigwId,
            resourceId: data.row.resource_id,
            versionId: data.row.resource_version_id
          })
          this.showReleaseResource(res.data, stage)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.isDetailLoading = false
          }, 1000)
        }
      },

      showReleaseResource (params, stage) {
        this.detailSidesliderConf.isShow = true
        this.detailSidesliderConf.title = this.$t(`{stageName} 环境资源详情`, { stageName: stage.stage_name })
        this.curReleaseResource = params
      },

      handleRowClick (row) {
        this.resourceList.forEach(item => {
          if (item.id === row.id) {
            this.$refs.resourcesTable.toggleRowExpansion(row)
          } else {
            this.$refs.resourcesTable.toggleRowExpansion(item, false)
          }
        })
      },

      handlePublicChange () {
        this.batchEditParams.allowApply = this.batchEditParams.isPublic
      },

      async exportDownload () {
        const data = this.exportParams
        const apigwId = this.apigwId
        this.isDataLoading = true

        data.file_type = this.exportFileType
        let fetchUrl = 'resource/exportApigwResource'
        if (this.exportFileDocType === 'docs') {
          fetchUrl = 'resource/exportApigwResourceDocs'
        }
        try {
          const res = await this.$store.dispatch(fetchUrl, { apigwId, data })
          // 成功则触发下载文件
          if (res.ok) {
            const blob = await res.blob()
            const disposition = res.headers.get('Content-Disposition') || ''
            const url = URL.createObjectURL(blob)
            const elment = document.createElement('a')
            elment.download = (disposition.match(/filename="(\S+?)"/) || [])[1]
            elment.href = url
            elment.click()
            URL.revokeObjectURL(blob)

            this.$bkMessage({
              theme: 'success',
              message: this.$t('导出成功！')
            })
          } else if (res.headers.get('Content-Type') === 'application/json') {
            const { message } = await res.json()
            this.$bkMessage({
              theme: 'error',
              message
            })
          } else {
            throw new Error(res.statusText)
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },
      handleSettingChange ({ fields, size }) {
        if (JSON.stringify(this.setting.selectedFields) !== JSON.stringify(fields)) {
          this.getApigwResources()
        }
        this.setting.size = size
        this.setting.selectedFields = fields
        this.selecteTabledFields = fields.reduce((p, v) => {
          p.push(v.id)
          return p
        }, [])
        window.localStorage.setItem(`resource-fields`, JSON.stringify(this.setting.selectedFields))
      },
      switchLanguages (languages) {
        if (languages.length) {
          return languages[0] === 'en' ? 'zh' : 'en'
        }
        return 'zh'
      },
      tdMouseEnter (index, row, data) {
        setTimeout(() => {
          data.isDoc = true
          data.isRowHover = true
          data.isAddLabel = true
        }, 100)
      },
      tdMouseLeave (index, row, data) {
        setTimeout(() => {
          this.resourceList.forEach(item => {
            item.isDoc = false
            item.isRowHover = false
            item.isAddLabel = false
          })
        }, 100)
      },
      tdClick (data) {
        this.resourceList.forEach(item => {
          item.isEditLabel = false
        })
        data.isEditLabel = true
        this.labelsIds = data.labels.map(item => item.id)
        this.oldLabelsIds = _.cloneDeep(this.labelsIds)
        window.addEventListener('click', this.hideSelected)
        this.isEnter = true
        this.isCreateLabel = false
        this.clearLabelForm()
      },
      handleShowLabel () {
        if (!this.isCreateLabel) {
          this.isCreateLabel = true
          this.changeLabelBg()
          this.$nextTick(() => {
            this.$refs.addLabelInput.focus()
          })
        }
      },
      // 编辑标签
      async updateLabels () {
        let labelId = ''
        this.resourceList.forEach(item => {
          if (item.isEditLabel) {
            labelId = item.id
          }
          item.isEditLabel = false
        })
        try {
          const apigwId = this.apigwId
          const data = {
            'label_ids': this.labelsIds
          }
          await this.$store.dispatch('label/operateApigwLabel', { apigwId, labelId, data })
          this.getApigwResources()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      // 新建标签
      async addLabel () {
        try {
          const data = { name: this.curLabel.name }
          const apigwId = this.apigwId
          const res = await this.$store.dispatch('label/addApigwLabel', { apigwId, data })
          this.isCreateLabel = false
          this.getApigwLabels()
          this.clearLabelForm()
          this.labelsIds.push(res.data.id)
          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      clearLabelForm () {
        this.curLabel.name = ''
      },
      changeSelect (newVal, oldVal) {
        const labels = this.resourceList.find(item => item.isEditLabel)
        if (JSON.stringify(newVal) === JSON.stringify(labels)) {
          this.isRequest = false
        }
        // 最多只能选择十个
        if (newVal.length > 10) {
          const alllabelIds = this.labelList.map(label => label.id)
          this.labelsIds = alllabelIds.slice(0, 10)
        }
      },
      toggleSelect () {
        this.isCreateLabel = false
        this.clearLabelForm()
      },
      // 新增标签
      handleSubmitLabel () {
        this.$refs.labelForm.validate().then(() => {
          this.addLabel()
        })
      },
      handleCancel () {
        this.isRequest = false
      },
      dialogLeave () {
        setTimeout(() => {
          this.isRequest = true
        }, 300)
      },
      createLabel () {
        if (this.labelRules.name.length === 1) {
          this.labelRules.name.push({
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          })
        }
        this.handleSubmitLabel()
        this.getApigwLabels()
      },
      abrogate () {
        if (this.labelRules.name.length > 1) {
          this.labelRules.name.splice(1, 1)
        }
        setTimeout(() => {
          this.curLabel.name = ''
          this.isCreateLabel = false
        }, 50)
      },
      changeLabelBg () {
        if (document.querySelector('.slot-ag')) {
          if (this.isCreateLabel) {
            document.querySelector('.slot-ag').parentNode.classList.add('no-hover')
          } else {
            document.querySelector('.slot-ag').parentNode.classList.remove('no-hover')
          }
        }
      },
      selectClick (e) {
        this.selectedEl = e.target
      },
      // 点击其他位置/enter隐藏更改数据
      hideSelected (e, triggerType) {
        this.$nextTick(() => {
          if (!this.isParent(e.target, document.querySelector('.tippy-content'))) {
            if (JSON.stringify(this.oldLabelsIds) === JSON.stringify(this.labelsIds)) {
              this.resourceList.forEach(item => {
                item.isEditLabel = false
              })
              this.removeEvent()
              // 初始化对应状态
              this.curLabel.name = ''
              this.isCreateLabel = false
              return false
            }
            this.updateLabels()
            window.removeEventListener('click', this.hideSelected)
          }
        })
      },
      handleLabelData () {
        if (JSON.stringify(this.oldLabelsIds) === JSON.stringify(this.labelsIds)) {
          this.resourceList.forEach(item => {
            item.isEditLabel = false
          })
          this.removeEvent()
          return false
        }
        this.updateLabels()
      },
      isParent (obj, parentObj) {
        while (obj !== undefined && obj !== null && obj.tagName.toUpperCase() !== 'BODY') {
          if (obj === parentObj) {
            return true
          }
          obj = obj.parentNode
        }
        return false
      },
      isTagRef () {
        // 标签内容过多展示两个
        this.resourceList.forEach(item => {
          if (this.$refs[item.name] && this.$refs[item.name].offsetWidth > 240) {
            item.tagOrder = 2
          }
        })
      },
      // 手动清空表格筛选
      clearFilterValue () {
        if (this.$refs.resourcesTable && this.$refs.resourcesTable.$refs.tableHeader) {
          const filterPanels = this.$refs.resourcesTable.$refs.tableHeader.filterPanels
          for (const key in filterPanels) {
            filterPanels[key].handleReset()
          }
        }
      },
      clearFilterKey () {
        this.keyword = ''
        this.$refs.resourcesTable.clearFilter()
        if (this.$refs.resourcesTable && this.$refs.resourcesTable.$refs.tableHeader && this.keyword) {
          clearFilter(this.$refs.resourcesTable.$refs.tableHeader)
        }
        if (this.filterMethod || this.filterLabel) {
          this.clearFilterValue()
        }
      },
      updateTableEmptyConfig () {
        if (this.filterMethod || this.filterLabel) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = this.keyword
      },
      // 回车更新Labels
      addLabels (e) {
        if (e.keyCode === 13 && this.isEnter) {
          this.hideSelected(e, 'enter')
          this.isEnter = false
        }
      },
      handleCreateLabels () {
        if (this.isEnter) {
          window.addEventListener('keydown', this.addLabels)
        }
      },
      removeEvent () {
        window.removeEventListener('click', this.hideSelected)
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .ag-dl {
        padding: 15px 40px 5px 30px;
    }

    .ag-user-type {
        width: 560px;
        height: 80px;
        background: #FAFBFD;
        border-radius: 2px;
        border: 1px solid #DCDEE5;
        padding: 17px 20px 0 20px;
        position: relative;
        overflow: hidden;

        .apigateway-icon {
            font-size: 80px;
            position: absolute;
            color: #ECF2FC;
            top: 15px;
            right: 20px;
            z-index: 0;
        }

        strong {
            font-size: 14px;
            margin-bottom: 10px;
            line-height: 1;
            display: block;
        }

        p {
            font-size: 12px;
            color: #63656E;
        }
    }

    .ag-auto-text {
        vertical-align: middle;
    }

    .ag-tag.success {
        width: 44px;
    }

    .languages-tag{
        background: #edf4ff;
        color: #3A84FF;
        display: inline-block;
        width: 44px;
        height: 22px;
        text-align: center;
        line-height: 22px;
        cursor: pointer;
    }

    .ag-no-doc{
        color: #c4c6cc;
        cursor: pointer;
        &:hover{
            color: #3a84ff;
        }
    }

    .ag-flex {
        display: flex;
    }

    .dropdown-icon {
        margin: 0 -4px;
        &.open {
            transform: rotate(180deg);
        }
    }

    .bk-dropdown-item {
        .disabled {
            color: #C4C6CC !important;
            cursor: not-allowed;

            &:hover {
                color: #C4C6CC;
            }
        }
    }

    .resource-url-box {
        display: inline-block;
        padding-right: 20px;
        max-width: 100%;
        position: relative;

        /deep/ .bk-tooltip,
        /deep/ .bk-tooltip-ref {
            width: 100%;
        }

        .copy-btn {
            position: absolute;
            right: 0;
            top: 0;
            background: #FFF;
            padding: 2px;
            border-radius: 2px;
            cursor: pointer;
        }
    }
    .resource-url {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    
    .text-center{
        text-align: center;
    }
    .ag-markdown-view {
        .tab-button {
            padding: 0 12px;
            a {
                color: #63656E;
            }
        }
        .is-selected {
                a {
                    color: #3a84ff;
                }
            }
    }
    .ap-nodata{
        .icon-empty{
            font-size: 80px;
        }
        p{
            font-size: 16px;
            color: #313238;
        }
    }

    .rosource-number{
        color: #c4c6cc;
    }

    .no-document {
        display: inline-block;
        padding: 5px;
    }

    .plus-class {
        font-size: 12px;
        display: inline-block;
        padding: 5px;
        margin-left: -5px;
        border-radius: 2px;
        cursor: pointer;
        color: #979BA5;
        background: #EAEBF0;
        &:hover {
            color: #3A84FF;
            background: #E1ECFF;
        }
    }

    .document-info {
        color: #3A84FF;
        font-size: 12px;
        &:hover {
            cursor: pointer;
        }
    }

    /deep/ .label-item-wrapper {
        position: relative;
        width: 270px;
        line-height: 24px;
        background: #EAEBF0;
        border-radius: 2px;
        overflow: hidden;
        cursor: pointer;
    }

    .label-wrapper {
        white-space: nowrap;
        word-break: keep-all;
        cursor: pointer;
        margin-left: 5px;
        line-height: 32px;
    }

    .empty {
        display: flex;
        align-items: center;
        justify-content: space-between;

        .add-tag {
            color: #C4C6CC;
        }
    }

    .tag-wrapper {
        width: 240px;
        overflow: hidden;
    }

    .angle-down-class {
        margin-right: 5px;
        font-size: 20px;
        color: #63656e;
    }

    .angle-down-tag {
        position: absolute;
        top: 6px;
        right: 0;
    }

    .slot-wrapper {
        display: flex;
        margin-top: 10px;
        padding-bottom: 10px;
        flex-direction: row;
        justify-content: center;
        align-items: center;

        .input-wrapper {
            flex: 1;
        }

        .btn-wrapper {
            width: 60px;
            color: #DCDEE5;

            /deep/ span {
                font-size: 12px;
            }
        }
    }

    .icon-more-hover {
        color: #575961;
        &:hover {
            color: #3a84ff;
        }
    }

    /deep/ .bk-table .bk-table-body td.bk-table-expanded-cell {
        background: #fafbfd;
    }
    
    .resource-container {
        .doc-sideslider-cls /deep/ .bk-sideslider-content {
            overflow: visible;

            pre {
                overflow-x: auto;
                &::-webkit-scrollbar {
                    width: 6px;
                    height: 6px;
                    background-color: #fafafa;
                }
                &::-webkit-scrollbar-thumb {
                    height: 6px;
                    border-radius: 4px;
                    background-color: #ccc;
                }
            }
        }

        /deep/ .bk-sideslider-wrapper {
            overflow-y: visible;
        }

        .doc-sideslider-wrapper {
            overflow: auto;
            max-height: calc(100vh - 104px);
            padding: 30px;
            padding-bottom: 20px;
            
            /deep/ .ag-markdown-view table td {
                word-break: break-all;
            }
        }

        .doc-btn-wrapper {
            padding-top: 8px;
            background: #fff;
            padding-left: 30px;
            height: 52px;
        }
    }
</style>
<style lang="postcss">
.tippy-content{
    max-width: 400px;
}
.bk-table-setting-content{
    width: 400px;
}
.bk-select-extension.no-hover:hover {
    background: #fafbfd;
}
.popover-tips-cls {
    margin: 5px 10px 8px 10px;
}
.app-content .bk-sideslider .bk-sideslider-content {
    ul,
    ul li {
        list-style: disc;
    }
    ol {
        padding: 0;
    }
    ol li {
        list-style: decimal;

    }
    
    p code:not([class^='lang']) {
        padding: 2px 4px;
        color: #313238;
        border: 1px solid #e1e1e8;
        border-radius: 3px;
    }
}
.doc-sideslider-cls {
    .hljs {
        padding: 10px 15px;
        border-radius: 3px;
        overflow-x: auto;
        &::-webkit-scrollbar {
            width: 4px;
        }
        &::-webkit-scrollbar-thumb {
            border-radius: 2px;
            background-color: #ccc;
        }
    }
}
</style>
