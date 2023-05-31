<template>
  <div class="app-content">
    <bk-tab
      :active.sync="bindTabActive"
      :ext-cls="'ag-bind-tab'">
      <bk-tab-panel
        :label="$t('基本信息')"
        :name="'baseInfo'">
        <bk-form
          ref="form"
          :label-width="160"
          :model="curStrategy"
          class="pl20 pr20"
          style="max-width: 1280px;">
          <bk-form-item
            :label="$t('名称')"
            :required="true"
            :rules="rules.name"
            :property="'name'">
            <bk-input :placeholder="$t('请输入')" v-model="curStrategy.name"></bk-input>
          </bk-form-item>
          <bk-form-item
            :label="$t('类型')"
            :required="true"
            :rules="rules.type"
            :property="'type'">
            <bk-select v-model="curStrategy.type" :disabled="strategyId !== undefined">
              <bk-option
                v-for="option in typeList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="$t('备注')">
            <bk-input type="textarea" v-model="curStrategy.comment"></bk-input>
          </bk-form-item>

          <div class="ag-span"></div>

          <template v-if="curStrategy.type && curStrategy.type === 'ip_access_control'">
            <bk-form-item :label="$t('访问控制类型')" :required="true">
              <bk-select
                :clearable="false"
                :disabled="strategyId !== undefined"
                v-model="curStrategy.ip_access_control.type">
                <bk-option
                  v-for="option in controllList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
            </bk-form-item>

            <bk-form-item :label="$t('策略IP分组')">
              <bk-button class="mr10" @click="handleBatchRemoveIPGroup"> {{ $t('批量删除') }} </bk-button>
              <bk-button @click="handleShowIPGroupSlider"> {{ $t('添加') }} </bk-button>
              <bk-table style="margin-top: 15px;"
                :data="curPageData"
                :size="'small'"
                :pagination="pagination"
                @page-limit-change="handlePageLimitChange"
                @page-change="handlePageChange"
                @selection-change="handleIPGroupSelect">
                <div slot="empty">
                  <table-empty empty />
                </div>
                <bk-table-column type="selection" width="60" align="center"></bk-table-column>
                <bk-table-column :label="$t('IP分组名称')" prop="name" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('IP分组备注')" prop="comment" :render-header="$renderHeader">
                  <template slot-scope="props">
                    {{props.row.comment || '--'}}
                  </template>
                </bk-table-column>
                <bk-table-column :label="$t('IP分组更新时间')" prop="updated_time" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('操作')" width="100">
                  <template slot-scope="props">
                    <bk-popconfirm
                      placement="top"
                      @confirm="handleRemoveIPGroup(props.row)">
                      <bk-button theme="primary" text> {{ $t('删除') }} </bk-button>
                    </bk-popconfirm>
                  </template>
                </bk-table-column>
              </bk-table>
              <p class="ag-tip mt10">
                <i class="apigateway-icon icon-ag-info"></i> {{ $t('IP分组为空时，若类型为“允许“，表示不允许任何IP访问，若类型为“拒绝”，表示允许任何IP访问') }}
              </p>
            </bk-form-item>
          </template>
          <template v-if="curStrategy.type && curStrategy.type === 'rate_limit'">
            <bk-form-item :label="$t('默认频率限制')">
              <div class="token-area">
                <div class="tokens-wrapper">
                  <bk-input
                    type="number"
                    :placeholder="$t('输入')"
                    :min="1"
                    :clearable="true"
                    :show-controls="false"
                    v-model="curStrategy.rate_limit.default.tokens"
                    style="width: 90px; float: left;">
                  </bk-input>
                  <span class="fl ag-text mr10 ml10">次/</span>
                  <bk-select
                    v-model="curStrategy.rate_limit.default.period"
                    :placeholder="$t('单位')"
                    style="width: 70px; float: left; margin-right: 10px;"
                    :clearable="false">
                    <bk-option v-for="option in unitList"
                      :key="option.id"
                      :id="option.id"
                      :name="option.name">
                    </bk-option>
                  </bk-select>
                </div>
                <p class="ag-tip pt10">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ $t('应用的默认频率限制。绑定环境时，表示应用对环境下所有资源的总频率限制；绑定资源时，表示应用对单个资源的频率限制') }}
                </p>
              </div>
            </bk-form-item>

            <bk-form-item :label="$t('特殊应用频率限制')">
              <div class="token-area">
                <div class="tokens-wrapper">
                  <template v-if="curStrategy.rate_limit.apps.length">
                    <div v-for="(app, index) of curStrategy.rate_limit.apps" :key="index">
                      <bk-input
                        type="number"
                        :placeholder="$t('输入')"
                        :min="1"
                        :clearable="true"
                        :show-controls="false"
                        v-model="app.tokens"
                        style="width: 90px; float: left;">
                      </bk-input>
                      <span class="fl ag-text mr10 ml10">次/</span>
                      <bk-select
                        v-model="app.period"
                        :placeholder="$t('单位')"
                        style="width: 70px; float: left; margin-right: 10px;"
                        :clearable="false">
                        <bk-option v-for="option in unitList"
                          :key="option.id"
                          :id="option.id"
                          :name="option.name">
                        </bk-option>
                      </bk-select>
                      <span class="fl ag-text mr10 ml10">/</span>
                      <bk-input
                        :placeholder="$t('蓝鲸应用ID')"
                        :clearable="true"
                        :show-controls="false"
                        v-model="app.appId"
                        style="width: 175px; float: left;">
                      </bk-input>
                      <button class="ag-icon-button ml5" @click="handleAddRateApp">
                        <i class="apigateway-icon icon-ag-plus-circle-shape"></i>
                      </button>
                      <button class="ag-icon-button" @click="handleRemoveRateApp(app, index)">
                        <i class="apigateway-icon icon-ag-minus-circle-shape"></i>
                      </button>
                    </div>
                  </template>
                  <template v-else>
                    <bk-button theme="primary" icon="plus" size="small" @click="handleAddRateApp"> {{ $t('添加应用频率限制') }} </bk-button>
                  </template>
                </div>
                <p class="ag-tip pt10">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ $t('特殊应用的频率限制，将对指定应用覆盖默认频率限制') }}
                </p>
              </div>
            </bk-form-item>
          </template>
          <template v-if="curStrategy.type && curStrategy.type === 'user_verified_unrequired_apps'">
            <bk-form-item :label="$t('免用户认证应用ID')">
              <bk-tag-input
                ref="bkAppCodeTagInpurComp"
                :placeholder="$t('请输入蓝鲸应用ID，并按Enter确认')"
                v-model="curStrategy.user_verified_unrequired_apps.bk_app_code_list"
                :allow-create="true"
                :list="appCodeList"
                :has-delete-icon="true"
                @blur="tagInputBlurHandler">
              </bk-tag-input>
              <!-- [a-z][a-z0-9-]+ -->
              <!-- <bk-input type="textarea" v-model="curStrategy.user_verified_unrequired_apps.bk_app_code_list"></bk-input> -->
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('资源要求用户认证时，免用户认证的应用，在用户未认证时也可以访问资源') }}
              </p>
            </bk-form-item>
          </template>
          <template v-if="curStrategy.type && curStrategy.type === 'cors'">
            <div class="ag-alert primary mt10 mb10" style="margin-left: 160px;">
              <i class="apigateway-icon icon-ag-info"></i> {{ $t('启用 CORS 策略后，若网关与后端接口同时生成 CORS 相关响应头，将优先使用网关生成的 CORS 响应头') }}，
              <a class="ag-link primary" target="_blank" :href="GLOBAL_CONFIG.DOC.CORS"> {{ $t('更多详情') }} </a>
            </div>

            <bk-form-item
              label="Allowed origins"
              :required="true"
              :rules="rules.allowed_origins"
              :property="'cors.allowed_origins'">
              <bk-tag-input
                v-model="curStrategy.cors.allowed_origins"
                :allow-create="true"
                :allow-auto-match="true"
                :has-delete-icon="true"
                :paste-fn="pasteAllowedOrigins">
              </bk-tag-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('首部Access-Control-Allow-Origin，指定允许访问该服务的请求域，如 http://example.com') }}
              </p>
            </bk-form-item>
            <bk-form-item
              label="Allowed methods"
              :required="true"
              :rules="rules.allowed_methods"
              :property="'cors.allowed_methods'">
              <bk-select
                multiple
                :clearable="false"
                :show-select-all="true"
                v-model="curStrategy.cors.allowed_methods">
                <bk-option v-for="option in methodList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('首部Access-Control-Allow-Methods，用于预检请求的响应，指明实际请求所允许使用的 HTTP 方法') }}
              </p>
            </bk-form-item>
            <bk-form-item
              label="Allowed headers"
              :required="true"
              :rules="rules.allowed_headers"
              :property="'cors.allowed_headers'">
              <bk-tag-input
                v-model="curStrategy.cors.allowed_headers"
                :allow-create="true"
                :allow-auto-match="true"
                :has-delete-icon="true"
                :paste-fn="pasteAllowedHeaders">
              </bk-tag-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('首部Access-Control-Allow-Headers，用于预检请求的响应，指明实际请求中允许携带的首部字段') }}
              </p>
            </bk-form-item>
            <bk-form-item label="Exposed headers">
              <bk-tag-input
                v-model="curStrategy.cors.exposed_headers"
                :allow-create="true"
                :allow-auto-match="true"
                :has-delete-icon="true"
                :paste-fn="pasteExposedHeaders">
              </bk-tag-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('首部Access-Control-Expose-Headers，表示允许浏览器访问的响应首部字段') }}
              </p>
            </bk-form-item>
            <bk-form-item label="Max age">
              <bk-input v-model="curStrategy.cors.max_age" type="number" :max="9999999" :min="0" :precision="0">
                <template slot="append">
                  <div class="group-text">秒</div>
                </template>
              </bk-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('首部Access-Control-Max-Age，表示预检结果的缓存时间，单位秒') }}
              </p>
            </bk-form-item>
            <bk-form-item label="Allow credentials">
              <bk-checkbox
                :true-value="true"
                :false-value="false"
                v-model="curStrategy.cors.allow_credentials">
              </bk-checkbox>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('首部Access-Control-Allow-Credentials，表示是否允许发送身份凭证，如Cookies、HTTP认证信息等') }}
              </p>
            </bk-form-item>
          </template>
          <template v-if="curStrategy.type && curStrategy.type === 'error_status_code_200'">
            <p class="ag-tip mb20" style="margin-left: 160px;">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ $t('请求网关资源出现错误时，如超过频率、认证失败等，响应状态码设置为200，不推荐，默认使用标准 HTTP 状态码。') }}
              <a :href="GLOBAL_CONFIG.DOC.ERROR_CODE" target="_blank" class="ag-primary"> {{ $t('更多详情') }} </a>
            </p>
          </template>
          <template v-if="curStrategy.type && curStrategy.type === 'circuit_breaker'">
            <div class="ag-alert primary mt10 mb10" style="margin-left: 160px;">
              <i class="apigateway-icon icon-ag-info"></i>{{ $t('当资源后端主机出现故障时提供断路功能') }}，
              <a class="ag-link primary" target="_blank" :href="GLOBAL_CONFIG.DOC.BREAKER"> {{ $t('更多详情') }} </a>
            </div>

            <bk-form-item
              :label="$t('断路器触发条件')">
              <div>
                <bk-checkbox
                  :true-value="true"
                  :false-value="false"
                  v-model="curStrategy.circuit_breaker.conditions.http_error">
                  {{ $t('后端响应状态码错误') }}
                </bk-checkbox>

                <div class="ml50" style="display: inline-block;" v-if="curStrategy.circuit_breaker.conditions.http_error">
                  <span class="f14 vm mr5" style="display: inline-block; color: #63656e;"> {{ $t('错误状态码') }} <i style="color: red; font-style: normal;" class="vm">*</i></span>
                  <bk-select
                    class="vm"
                    style="width: 300px; display: inline-block;"
                    searchable
                    multiple
                    show-select-all
                    v-model="curStrategy.circuit_breaker.conditions.status_code">
                    <bk-option v-for="option in errorCodeList"
                      :key="option.id"
                      :id="option.id"
                      :name="option.name">
                    </bk-option>
                  </bk-select>
                </div>
              </div>
              <div>
                <bk-checkbox
                  :true-value="true"
                  :false-value="false"
                  v-model="curStrategy.circuit_breaker.conditions.timeout">
                  {{ $t('访问后端接口超时') }}
                </bk-checkbox>
              </div>
              <div>
                <bk-checkbox
                  :true-value="true"
                  :false-value="false"
                  v-model="curStrategy.circuit_breaker.conditions.network_error">
                  {{ $t('访问后端接口网络连接错误') }}
                </bk-checkbox>
              </div>
            </bk-form-item>

            <bk-form-item
              :label="$t('计数时间窗口')"
              :required="true"
              :rules="rules.window_duration"
              :property="'circuit_breaker.window.duration'"
              :icon-offset="50">
              <bk-input
                type="number"
                v-model="curStrategy.circuit_breaker.window.duration"
                :clearable="false"
                :min="10"
                :max="120"
                :show-controls="false"
                :precision="0">
                <template slot="append">
                  <div class="group-text">秒</div>
                </template>
              </bk-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('统计请求次数的时间窗口，取值范围 10~120 秒') }}
              </p>
            </bk-form-item>

            <bk-form-item
              :label="$t('请求错误数阈值')"
              :required="true"
              :rules="rules.threshold"
              :property="'circuit_breaker.strategy.options.threshold'">
              <bk-input
                type="number"
                v-model="curStrategy.circuit_breaker.strategy.options.threshold"
                :clearable="false"
                :min="1"
                :max="10000"
                :show-controls="false"
                :precision="0">
              </bk-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('触发断路的请求出错次数阈值，取值范围 1~10000 次；计数时间窗口内，若资源后端主机符合条件的出错次数达到阈值，则该资源后端主机触发断路，断路器处于断开状态') }}
              </p>
            </bk-form-item>

            <bk-form-item
              :label="$t('断开重试间隔')"
              :required="true"
              :rules="rules.back_off"
              :property="'circuit_breaker.back_off.options.interval'"
              :icon-offset="50">
              <bk-input
                type="number"
                v-model="curStrategy.circuit_breaker.back_off.options.interval"
                :clearable="false"
                :min="10"
                :max="300"
                :show-controls="false"
                :precision="0">
                <template slot="append">
                  <div class="group-text">秒</div>
                </template>
              </bk-input>
              <p class="ag-tip pt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('断路器断开后，允许探测请求通过的时间间隔，取值范围 10~300 秒；断开并等待重试间隔后，将允许部分探测请求通过，这些请求成功，则结束断路，否则，重新开始断路') }}
              </p>
            </bk-form-item>

          </template>
          <bk-form-item>
            <section class="ag-panel-action">
              <div class="panel-content">
                <div class="panel-wrapper tc mt0">
                  <bk-button class="mr5" theme="primary" style="width: 120px;" @click="submitApigwStrategy" :loading="isDataLoading"> {{ $t('提交') }} </bk-button>
                  <bk-button style="width: 120px;" @click="handleApigwStrategyCancel"> {{ $t('取消') }} </bk-button>
                </div>
              </div>
            </section>
          </bk-form-item>
        </bk-form>
      </bk-tab-panel>

      <bk-tab-panel
        v-if="strategyId !== undefined"
        :name="'stage'"
        :label="$t('绑定环境列表')"
        style="padding-left: 20px; padding-right: 20px;">
        <bk-button class="mr10" @click="handleBatchUnbindStage"> {{ $t('批量解绑') }} </bk-button>
        <bk-button @click="handleBindStage"> {{ $t('绑定环境') }} </bk-button>
        <bk-table
          style="margin-top: 15px;"
          :data="stageBindList"
          :size="'small'"
          @selection-change="handleStageSelect">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="$t('环境名称')" prop="name" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('环境描述')" prop="description" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('操作')" width="200">
            <template slot-scope="props">
              <bk-popconfirm
                placement="top"
                @confirm="handleUnbindStage(props.row)">
                <bk-button theme="primary" text> {{ $t('解绑') }} </bk-button>
              </bk-popconfirm>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-tab-panel>

      <bk-tab-panel
        v-if="strategyId !== undefined && !['ip_access_control', 'error_status_code_200'].includes(curStrategy.type)"
        :name="'resource'"
        :label="$t('绑定资源列表')"
        style="padding-left: 20px; padding-right: 20px;">
        <bk-button
          class="mr10"
          @click="handleBatchUnbindResource">
          {{ $t('批量解绑') }}
        </bk-button>
        <bk-button
          @click="handleBindResource">
          {{ $t('绑定资源') }}
        </bk-button>
        <bk-table
          style="margin-top: 15px;"
          :data="resourceBindList"
          :size="'small'"
          @selection-change="handleResourceSelect">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('操作')" width="200">
            <template slot-scope="props">
              <bk-popconfirm
                placement="top"
                @confirm="handleUnbindResource(props.row)">
                <bk-button theme="primary" text> {{ $t('解绑') }} </bk-button>
              </bk-popconfirm>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-tab-panel>
    </bk-tab>

    <bk-sideslider
      :title="IPGroupBindSliderConf.title"
      :width="700"
      :is-show.sync="IPGroupBindSliderConf.isShow"
      :quick-close="true"
      :before-close="handleIpBeforeClose">
      <div slot="content" class="p30">
        <bk-form ref="IPGroupBindForm" :label-width="70">
          <bk-form-item
            :label="$t('IP分组')">
            <div class="bk-alert bk-alert-info mb10">
              <div class="bk-alert-wraper">
                <i class="bk-icon icon-info"></i>
                <div class="bk-alert-content">
                  <div class="bk-alert-title"><router-link class="ag-link primary" :to="{ name: 'apigwStrategy', params: { id: apigwId }, query: { type: 'IPGroup' } }"> {{ $t('IP分组') }} </router-link> {{ $t('用于管理一组IP，方便IP访问控制策略，维护IP信息') }} </div>
                  <div class="bk-alert-description"></div>
                </div>
              </div>
            </div>
            <bk-transfer
              ext-cls="resource-transfer-wrapper"
              :target-list="IPGroupTargetList"
              :source-list="IPGroupList"
              :display-key="'name'"
              :setting-key="'id'"
              :title="[$t('未选IP分组'), $t('已选IP分组')]"
              :searchable="true"
              @change="handleIPGroupChange">
              <div
                slot="source-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.name"
              >
                {{ data.name }}
              </div>
              <div
                slot="target-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.name"
              >
                {{ data.name }}
              </div>
              <div slot="left-empty-content">
                <div class="ag-empty-content f14" style="line-height: 195px; color: #c4c6cc;">
                  <template v-if="!IPGroupTargetList.length && !IPGroupList.length">
                    {{ $t('暂无IP分组，请前往') }} <router-link class="ag-link primary" :to="{ name: 'apigwStrategy', params: { id: apigwId }, query: { type: 'IPGroup' } }"> {{ $t('IP分组') }} </router-link> {{ $t('添加') }}
                  </template>
                  <template v-else>
                    {{ $t('无数据') }}
                  </template>
                </div>
              </div>
            </bk-transfer>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="handleBindIPGroup"> {{ $t('确定') }} </bk-button>
            <bk-button @click="handleHideIPGroupSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :title="stageBindSliderConf.title"
      :width="560"
      :is-show.sync="stageBindSliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" class="p30">
        <bk-form ref="stageBindForm" :label-width="60" :model="curStrategy" style="min-height: 600px;">
          <bk-form-item
            :label="$t('名称')">
            <span class="f12">{{curStrategy.name || '--'}}</span>
          </bk-form-item>
          <bk-form-item
            :label="$t('环境')">
            <bk-select
              searchable
              multiple
              show-select-all
              v-model="scopeIds">
              <bk-option v-for="option in stageList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
            <!-- <bk-tag-input
                            v-model="scopeIds"
                            placeholder="请选择环境"
                            :list="stageList"
                            :trigger="'focus'"
                            :content-max-height="200"
                            :allow-next-focus="false">
                        </bk-tag-input> -->
            <div class="ag-alert warning mt10">
              <i class="apigateway-icon icon-ag-info"></i>
              <p> {{ $t('如果环境已经绑定了一个策略，则会被本策略覆盖，请谨慎操作') }} </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="checkBindeResources" :loading="isChecking"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideStageSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :title="resourceBindSliderConf.title"
      :width="840"
      :is-show.sync="resourceBindSliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" class="p30">
        <bk-form ref="resourceBindForm" :label-width="60" :model="curStrategy">
          <bk-form-item
            :label="$t('名称')">
            <span class="f12">{{curStrategy.name}}</span>
          </bk-form-item>
          <bk-form-item
            :label="$t('资源')">
            <bk-transfer
              ext-cls="resource-transfer-wrapper"
              :key="renderTransferIndex"
              :target-list="resourceTargetList"
              :source-list="resourceList"
              :display-key="'resourceName'"
              :setting-key="'id'"
              :title="[$t('未选资源'), $t('已选资源')]"
              :searchable="true"
              @change="handleResourceChange">
              <div
                slot="source-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.resourceName"
              >
                {{ data.resourceName }}
              </div>
              <div
                slot="target-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.resourceName"
              >
                {{ data.resourceName }}
              </div>
            </bk-transfer>
            <div class="ag-alert warning mt10">
              <i class="apigateway-icon icon-ag-info"></i>
              <p> {{ $t('如果资源已经绑定了一个策略，则会被本策略覆盖，请谨慎操作') }} </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="checkBindeResources" :loading="isChecking"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideResourceSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-dialog
      v-model="unbindResourceConf.isShow"
      theme="primary"
      :width="670"
      :title="`${curStrategy.scope_type === 'stage' ? $t('环境') : $t('资源') }${$t('绑定变更，请确认')}`"
      :mask-close="true"
      @cancel="unbindResourceConf.isShow = false"
      @confirm="submitBindingData">
      <div>
        <bk-table
          :data="bindChangeResources"
          :size="'small'"
          :max-height="280"
          :key="tableIndex">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('环境名称')" prop="name" v-if="curStrategy.scope_type === 'stage'" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求路径')" prop="path" v-if="curStrategy.scope_type === 'resource'" :render-header="$renderHeader">
            <template slot-scope="props">
              <span class="ag-auto-text" v-bk-tooltips.right="props.row.path || '--'">{{props.row.path || '--'}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" v-if="curStrategy.scope_type === 'resource'" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('原策略')">
            <template slot-scope="props">
              <span class="ag-auto-text" v-bk-tooltips.right="props.row.oldStrategy.access_strategy_name || '--'">{{props.row.oldStrategy.access_strategy_name || '--'}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('目标策略')" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.bindStatus === 'delete'">
                --
              </template>
              <template v-else>
                <span class="ag-auto-text" v-bk-tooltips.right="props.row.newStrategy.name || '--'">{{props.row.newStrategy.name || '--'}}</span>
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('变更状态')" prop="bindStatus" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.bindStatus === 'add'">
                <span class="ag-tag primary"> {{ $t('绑定') }} </span>
              </template>
              <template v-else-if="props.row.bindStatus === 'delete'">
                <span class="ag-tag warning"> {{ $t('解绑') }} </span>
              </template>
              <template v-else-if="props.row.bindStatus === 'merge'">
                <span class="ag-tag danger"> {{ $t('覆盖') }} </span>
              </template>
            </template>
          </bk-table-column>
        </bk-table>
        <template v-if="curStrategy.scope_type === 'stage'">
          <div class="ag-alert warning mt10" v-if="mergeResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分环境已经绑定了策略，如果继续操作，原来的策略将被本策略覆盖') }} </p>
          </div>
          <div class="ag-alert warning mt10" v-else-if="unbindResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分环境被取消选中，如果继续操作，原来的绑定将被解绑') }} </p>
          </div>
        </template>
        <template v-else>
          <div class="ag-alert warning mt10" v-if="mergeResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分资源已经绑定了策略，如果继续操作，原来的策略将被本策略覆盖') }} </p>
          </div>
          <div class="ag-alert warning mt10" v-else-if="unbindResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分资源被取消选中，如果继续操作，原来的绑定将被解绑') }} </p>
          </div>
        </template>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler, sortByKey } from '@/common/util'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    mixins: [sidebarMixin],
    data () {
      return {
        bindChangeResources: [],
        tableIndex: 0,
        isPageLoading: true,
        isDataLoading: false,
        isChecking: false,
        appCodeList: [],
        renderTransferIndex: 0,
        curStrategy: {
          name: '',
          type: 'ip_access_control',
          comment: '',
          user_verified_unrequired_apps: {
            bk_app_code_list: []
          },
          ip_access_control: {
            type: 'allow',
            ip_group_list: []
          },
          rate_limit: {
            default: {
              tokens: '',
              period: 1
            },
            apps: []
          },
          cors: {
            allowed_origins: [],
            allowed_methods: ['GET', 'POST', 'PUT', 'PATCH', 'HEAD', 'DELETE', 'OPTIONS'],
            allowed_headers: ['Accept', 'Cache-Control', 'Content-Type', 'Keep-Alive', 'Origin', 'User-Agent', 'X-Requested-With'],
            exposed_headers: [],
            max_age: 86400,
            allow_credentials: true
          },
          circuit_breaker: {
            window: {
              duration: 30
            },
            conditions: {
              http_error: true,
              status_code: [500, 502, 503, 504],
              timeout: true,
              network_error: true
            },

            strategy: {
              type: 'threshold',
              options: {
                threshold: 10000
              }
            },

            back_off: {
              type: 'fixed',
              options: {
                interval: 120
              }
            }
          }
        },
        errorCodeList: [
          {
            id: 500,
            name: '500',
            text: 'StatusInternalServerError'
          },
          {
            id: 501,
            name: '501',
            text: 'StatusNotImplemented'
          },
          {
            id: 502,
            name: '502',
            text: 'StatusBadGateway'
          },
          {
            id: 503,
            name: '503',
            text: 'StatusServiceUnavailable'
          },
          {
            id: 504,
            name: '504',
            text: 'StatusGatewayTimeout'
          },
          {
            id: 505,
            name: '505',
            text: 'StatusHTTPVersionNotSupported'
          },
          {
            id: 506,
            name: '506',
            text: 'StatusVariantAlsoNegotiates'
          },
          {
            id: 507,
            name: '507',
            text: 'StatusInsufficientStorage'
          },
          {
            id: 508,
            name: '508',
            text: 'StatusLoopDetected'
          },
          {
            id: 510,
            name: '510',
            text: 'StatusNotExtended'
          },
          {
            id: 511,
            name: '511',
            text: 'StatusNetworkAuthenticationRequired'
          }
        ],
        IPGroupList: [],
        IPGroupTargetList: [],
        IPGroupTargetValueList: [],
        IPGroupSelectedList: [],
        curStrategyIPGroupList: [],
        isIPGroupLoading: false,
        allAppIds: [],
        scopeIds: [],
        typeKeys: [
          'ip_access_control',
          'rate_limit',
          'user_verified_unrequired_apps',
          'cors',
          'error_status_code_200',
          'circuit_breaker'
        ],
        typeList: [
          {
            id: 'ip_access_control',
            name: this.$t('IP访问控制')
          },
          {
            id: 'rate_limit',
            name: this.$t('频率控制')
          },
          {
            id: 'cors',
            name: this.$t('跨域资源共享(CORS)')
          },
          {
            id: 'circuit_breaker',
            name: this.$t('断路器')
          },
          {
            id: 'user_verified_unrequired_apps',
            name: this.$t('免用户认证应用白名单')
          },
          {
            id: 'error_status_code_200',
            name: this.$t('网关错误使用HTTP状态码200(不推荐)')
          }
        ],
        controllList: [
          {
            id: 'allow',
            name: this.$t('允许')
          },
          {
            id: 'deny',
            name: this.$t('拒绝')
          }
        ],
        unitList: [
          {
            id: 1,
            name: this.$t('秒')
          },
          {
            id: 60,
            name: this.$t('分')
          },
          {
            id: 3600,
            name: this.$t('时')
          },
          {
            id: 86400,
            name: this.$t('天')
          }
        ],
        bindTabActive: 'baseInfo',
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          type: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          allowed_origins: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          allowed_methods: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          allowed_headers: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          window_duration: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          back_off: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          threshold: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        },
        IPGroupBindSliderConf: {
          title: this.$t('添加IP分组'),
          isShow: false
        },
        stageBindSliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('绑定环境')
        },
        resourceBindSliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('绑定资源')
        },
        stageList: [],
        curStrategyStages: [],
        stageUnbindList: [],

        curStrategyResources: [],
        resourceList: [],
        resourceSourceList: [],
        resourceTargetList: [],
        resourceTargetListCache: [], // 用于解绑对比
        resourceUnbindList: [],
        unbindResources: [],
        mergeResources: [],
        unbindResourceConf: {
          isShow: false
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        curPageData: [],
        methodList: [
          {
            id: 'GET',
            name: 'GET'
          },
          {
            id: 'POST',
            name: 'POST'
          },
          {
            id: 'PUT',
            name: 'PUT'
          },
          {
            id: 'PATCH',
            name: 'PATCH'
          },
          {
            id: 'DELETE',
            name: 'DELETE'
          },

          {
            id: 'HEAD',
            name: 'HEAD'
          },
          {
            id: 'OPTIONS',
            name: 'OPTIONS'
          }
        ],
        pasteAllowedOrigins: (value) => {
          const items = value.split(/[,; ]+/)
          items.forEach(item => {
            if (!this.curStrategy.cors['allowed_origins'].includes(item)) {
              this.curStrategy.cors['allowed_origins'].push(item)
            }
          })
          return value.split(/[,; ]+/)
        },
        pasteAllowedHeaders: (value) => {
          const items = value.split(/[,; ]+/)
          items.forEach(item => {
            if (!this.curStrategy.cors['allowed_headers'].includes(item)) {
              this.curStrategy.cors['allowed_headers'].push(item)
            }
          })
          return value.split(/[,; ]+/)
        },
        pasteExposedHeaders: (value) => {
          const items = value.split(/[,; ]+/)
          items.forEach(item => {
            if (!this.curStrategy.cors['exposed_headers'].includes(item)) {
              this.curStrategy.cors['exposed_headers'].push(item)
            }
          })
          return value.split(/[,; ]+/)
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      strategyId () {
        return this.$route.params.strategyId || undefined
      },
      stageBindList () {
        const results = []
        this.curStrategyStages.forEach(item => {
          const matchItem = this.stageList.find(stage => item.scope_id === stage.id)

          if (matchItem) {
            results.push({
              id: matchItem.id,
              name: matchItem.name,
              description: matchItem.description || '--'
            })
          }
        })
        return results
      },

      resourceBindList () {
        const results = []
        this.curStrategyResources.forEach(item => {
          const matchItem = this.resourceList.find(resource => item.scope_id === resource.id)
          if (matchItem) {
            results.push({
              id: matchItem.id,
              path: matchItem.path,
              method: matchItem.method,
              description: matchItem.description || '--'
            })
          }
        })
        return sortByKey(results, 'path')
      }
    },
    watch: {
      'curStrategy.ip_access_control.ip_group_list' () {
        const results = []
        this.IPGroupList.forEach(item => {
          if (this.curStrategy.ip_access_control && this.curStrategy.ip_access_control.ip_group_list.includes(item.id)) {
            results.push(item)
          }
        })
        this.curStrategyIPGroupList = results
        this.pagination.count = results.length
        this.pagination.current = 1
        this.getCurPageData(1)
      },
      'IPGroupList' () {
        const results = []
        this.IPGroupList.forEach(item => {
          if (this.curStrategy.ip_access_control && this.curStrategy.ip_access_control.ip_group_list.includes(item.id)) {
            results.push(item)
          }
        })
        this.curStrategyIPGroupList = results
        this.pagination.count = results.length
        this.pagination.current = 1
        this.getCurPageData(1)
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        if (this.strategyId !== undefined) {
          this.getStrategyDetail()
          this.getApigwStages()
          this.getApigwResources()
        } else {
          setTimeout(() => {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }, 500)
        }
        this.getApigwIPGroups()
      },

      goBack () {
        this.goStrategyIndex()
      },

      async getStrategyDetail () {
        try {
          const apigwId = this.apigwId
          const strategyId = this.strategyId
          const res = await this.$store.dispatch('strategy/getApigwStrategyDetail', { apigwId, strategyId })
          const data = res.data

          // 将rate limit转化
          if (data.type === 'rate_limit') {
            const rateLimit = data.rate_limit
            const rates = rateLimit.rates

            // 默认default
            if (!rates['__default']) {
              rates['__default'] = [
                {
                  tokens: '',
                  period: 1
                }
              ]
            }

            rateLimit.apps = []
            for (const key in rates) {
              if (key === '__default') {
                rateLimit['default'] = {
                  tokens: rates[key][0].tokens,
                  period: rates[key][0].period
                }
              } else {
                rateLimit.apps.push({
                  tokens: rates[key][0].tokens,
                  period: rates[key][0].period,
                  appId: key
                })
              }
            }

            data['ip_access_control'] = {
              type: 'allow',
              ip_group_list: []
            }
          }

          this.curStrategy = data
          this.scopeIds = []
          this.getApigwStrategyStages()
          this.getApigwStrategyResources()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }, 500)
        }
      },

      async getApigwIPGroups (page) {
        const apigwId = this.apigwId

        this.isIPGroupLoading = true
        try {
          const pageParams = {
            query: '',
            no_page: true,
            order_by: 'name'
          }
          const res = await this.$store.dispatch('strategy/getApigwIPGroups', { apigwId, pageParams })

          this.IPGroupList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isIPGroupLoading = false
        }
      },

      handleApigwStrategyCancel () {
        this.goStrategyIndex()
      },

      goStrategyIndex () {
        if (this.$route.query.from) {
          this.$router.push({
            name: this.$route.query.from,
            params: {
              id: this.apigwId
            }
          })
        } else {
          this.$router.push({
            name: 'apigwStrategy',
            params: {
              id: this.apigwId
            }
          })
        }
      },

      submitApigwStrategy () {
        const bkAppCodeTagInpurComp = this.$refs.bkAppCodeTagInpurComp
        if (bkAppCodeTagInpurComp) {
          const curInputValue = bkAppCodeTagInpurComp.curInputValue || ''
          // curInputValue 有值说明 tag-input 还没有 blur
          if (curInputValue) {
            this.tagInputBlurHandler(curInputValue)
          }
        }

        const params = this.formatData()

        if (this.checkData(params)) {
          if (this.strategyId !== undefined) {
            this.updateApigwStrategy(params)
          } else {
            this.addApigwStrategy(params)
          }
        }
      },

      checkData (params) {
        const codeReg = /^[a-z][a-z0-9-_]+$/

        if (!params.name) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入名称')
          })
          this.$refs.form.validate()
          return false
        }

        if (!params.type) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择类型')
          })
          this.$refs.form.validate()
          return false
        }

        if (params.type === 'rate_limit') {
          const rates = params.rate_limit.rates
          for (const key in rates) {
            if (!key) {
              this.$bkMessage({
                theme: 'error',
                message: this.$t('请输入特殊应用频率限制的蓝鲸应用ID')
              })
              return false
            }

            if (key !== '__default' && !rates[key][0].tokens) {
              this.$bkMessage({
                theme: 'error',
                message: this.$t('请输入特殊应用频率限制的频率值')
              })
              return false
            }
          }

          const map = {}
          for (const id of this.allAppIds) {
            if (!codeReg.test(id)) {
              this.$bkMessage({
                theme: 'error',
                delay: 5000,
                message: this.$t('应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母')
              })
              return false
            }
            if (map[id]) {
              this.$bkMessage({
                theme: 'error',
                message: this.$t('蓝鲸应用ID不允许重复')
              })
              return false
            } else {
              map[id] = id
            }
          }
        } else if (params.type === 'user_verified_unrequired_apps') {
          const codes = this.curStrategy.user_verified_unrequired_apps.bk_app_code_list

          for (const code of codes) {
            if (!codeReg.test(code)) {
              this.$bkMessage({
                theme: 'error',
                delay: 5000,
                message: this.$t('应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母')
              })
              return false
            }
          }
        } else if (params.type === 'cors') {
          if (!params.cors.allowed_origins.length) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Allowed origins')
            })
            this.$refs.form.validate()
            return false
          }

          if (!params.cors.allowed_methods.length) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Allowed methods')
            })
            this.$refs.form.validate()
            return false
          }

          if (!params.cors.allowed_headers.length) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Allowed headers')
            })
            this.$refs.form.validate()
            return false
          }
        } else if (params.type === 'circuit_breaker') {
          if (!params.circuit_breaker.window.duration) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入判断时间窗口值')
            })
            this.$refs.form.validate()
            return false
          }

          if (!params.circuit_breaker.back_off.options.interval) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入断路器打开超时时间')
            })
            this.$refs.form.validate()
            return false
          }

          const useHttpError = params.circuit_breaker.conditions.http_error
          const useTimeout = params.circuit_breaker.conditions.timeout
          const useNetworkError = params.circuit_breaker.conditions.network_error
          if (!useHttpError && !useTimeout && !useNetworkError) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请选择断路器触发条件')
            })
            return false
          }

          if (params.circuit_breaker.conditions.http_error && !params.circuit_breaker.conditions.status_code.length) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请选择错误状态码')
            })
            return false
          }

          if (!params.circuit_breaker.strategy.options.threshold) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入错误数阈值')
            })
            this.$refs.form.validate()
            return false
          }
        }
        return true
      },

      formatData () {
        this.allAppIds = []
        const params = JSON.parse(JSON.stringify(this.curStrategy))

        if (params.type === 'rate_limit') {
          const rateLimit = params.rate_limit
          const defaultRate = rateLimit.default
          const appRates = rateLimit.apps

          rateLimit.rates = {}
          if (defaultRate.tokens) {
            rateLimit.rates['__default'] = [
              {
                tokens: defaultRate.tokens,
                period: defaultRate.period
              }
            ]
          }

          appRates.forEach(item => {
            if (item.appId || item.tokens) {
              this.allAppIds.push(item.appId)

              rateLimit.rates[item.appId] = [
                {
                  tokens: item.tokens,
                  period: item.period
                }
              ]
            }
          })
        } else if (params.type === 'error_status_code_200') {
          params.error_status_code_200 = { allow: true }
        } else if (params.type === 'circuit_breaker') {
          if (!params.circuit_breaker.conditions.http_error) {
            params.circuit_breaker.conditions.status_code = []
          }
        }

        this.typeKeys.forEach(key => {
          if (key !== params.type) {
            delete params[key]
          }
        })
        return params
      },

      async addApigwStrategy (data) {
        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          await this.$store.dispatch('strategy/addApigwStrategy', { apigwId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
          this.goStrategyIndex()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async updateApigwStrategy (data) {
        try {
          const apigwId = this.apigwId
          const strategyId = this.strategyId
          await this.$store.dispatch('strategy/updateApigwStrategy', { apigwId, strategyId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
          this.goStrategyIndex()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleIPGroupSelect (selectedList) {
        this.IPGroupSelectedList = selectedList
      },

      handleBatchRemoveIPGroup () {
        const self = this
        if (!self.IPGroupSelectedList.length) {
          self.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要删除的IP分组')
          })
          return false
        }

        self.$bkInfo({
          title: this.$t('确认要批量删除IP分组？'),
          confirmFn () {
            const valueList = self.curStrategy['ip_access_control'].ip_group_list
            self.curStrategy['ip_access_control'].ip_group_list = valueList.filter(id => {
              for (const item of self.IPGroupSelectedList) {
                if (item.id === id) {
                  return false
                }
              }
              return true
            })
            self.IPGroupSelectedList = []
          }
        })
      },

      handleIPGroupChange (sourceList, targetList, targetValueList) {
        this.IPGroupTargetValueList = targetValueList
      },

      handleBindIPGroup () {
        this.curStrategy['ip_access_control'].ip_group_list = this.IPGroupTargetValueList
        this.IPGroupBindSliderConf.isShow = false
      },

      handleHideIPGroupSlider () {
        this.IPGroupBindSliderConf.isShow = false
      },

      handleShowIPGroupSlider () {
        this.IPGroupTargetList = this.curStrategy['ip_access_control'].ip_group_list
        this.IPGroupBindSliderConf.isShow = true
        // 收集状态
        this.initSidebarFormData(this.IPGroupTargetValueList)
      },

      handleRemoveIPGroup (IPGroup) {
        const valueList = this.curStrategy['ip_access_control'].ip_group_list
        this.curStrategy['ip_access_control'].ip_group_list = valueList.filter(item => {
          return item !== IPGroup.id
        })
      },

      async handleBindStage () {
        this.curStrategy.scope_type = 'stage'
        this.scopeIds = []
        this.stageBindSliderConf.isShow = true
        await this.getApigwStrategyStages()
        this.initSidebarFormData(this.scopeIds)
      },

      async getApigwStages (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('stage/getApigwStages', { apigwId, pageParams })

          this.stageList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwStrategyStages () {
        const apigwId = this.apigwId
        const strategyId = this.strategyId
        const scopeType = 'stage'
        const type = this.curStrategy.type
        try {
          const res = await this.$store.dispatch('strategy/getApigwStrategyBindings', { apigwId, strategyId, scopeType, type })
          this.curStrategyStages = res.data.results
          res.data.results.forEach(item => {
            this.scopeIds.push(item.scope_id)
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async submitApigwStrategyStages () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const data = {
          scope_type: this.curStrategy.scope_type,
          scope_ids: this.scopeIds,
          type: this.curStrategy.type,
          delete: true
        }

        try {
          await this.$store.dispatch('strategy/updateApigwStrategyBindings', { apigwId, strategyId, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('绑定环境成功')
          })
          this.stageBindSliderConf.isShow = false
          this.getApigwStrategyStages()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleHideStageSlider () {
        this.stageBindSliderConf.isShow = false
      },

      async handleUnbindStage (stage) {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const data = {
          scope_type: 'stage',
          scope_ids: [],
          type: this.curStrategy.type
        }

        if (Array.isArray(stage)) {
          stage.forEach(item => {
            data.scope_ids.push(item.id)
          })
        } else {
          data.scope_ids.push(stage.id)
        }

        try {
          await this.$store.dispatch('strategy/deleteApigwStrategyBindings', { apigwId, strategyId, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('解绑环境成功')
          })
          this.getApigwStrategyStages()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleStageSelect (selectedList) {
        this.stageUnbindList = selectedList
      },
      handleBatchUnbindStage () {
        const self = this

        if (!self.stageUnbindList.length) {
          self.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要解绑的环境')
          })
          return false
        }

        self.$bkInfo({
          title: this.$t('确认要批量解绑环境？'),
          confirmFn () {
            self.handleUnbindStage(self.stageUnbindList)
          }
        })
      },

      async handleBindResource () {
        this.scopeIds = []
        this.curStrategy.scope_type = 'resource'
        this.renderTransferIndex++
        this.resourceBindSliderConf.isShow = true
        await this.getApigwStrategyResources()
        this.initSidebarFormData(this.scopeIds)
      },

      async getApigwResources (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'path'
        }

        try {
          const res = await this.$store.dispatch('resource/getApigwResources', { apigwId, pageParams })

          res.data.results.forEach(item => {
            item.resourceName = `${item.method}：${item.path}`
          })
          this.resourceList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      sort (list, key) {
        const sortKeys = list.map(item => {
          return item[key]
        })
        const results = []
        sortKeys.sort()

        sortKeys.forEach(sortItem => {
          list.forEach(item => {
            if (item[key] === sortItem) {
              results.push(item)
            }
          })
        })
        return results
      },

      async getApigwStrategyResources () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const scopeType = 'resource'
        const type = this.curStrategy.type
        try {
          const res = await this.$store.dispatch('strategy/getApigwStrategyBindings', { apigwId, strategyId, scopeType, type })
          this.curStrategyResources = res.data.results
          this.resourceTargetList = []
          this.resourceTargetListCache = []

          res.data.results.forEach(item => {
            this.scopeIds.push(item.scope_id)
            this.resourceTargetList.push(item.scope_id)
            this.resourceTargetListCache.push(item.scope_id)
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async checkBindeResources () {
        if (this.isChecking) {
          return false
        }
        this.isChecking = true

        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const originList = this.curStrategy.scope_type === 'stage' ? this.stageList : this.resourceList
        const data = {
          scope_type: this.curStrategy.scope_type,
          scope_ids: this.scopeIds,
          type: this.curStrategy.type
        }
        try {
          const res = await this.$store.dispatch('strategy/checkApigwStrategyBindings', { apigwId, strategyId, data })
          const addList = res.data.normal_bind.map(item => {
            return item.scope_id
          })

          const deleteList = res.data.unbind.map(item => {
            return item.scope_id
          })

          const mergeList = res.data.overwrite_bind.map(item => {
            return item.scope_id
          })

          this.addResources = originList.filter(resource => {
            return addList.includes(resource.id)
          })

          this.unbindResources = originList.filter(resource => {
            return deleteList.includes(resource.id)
          })

          this.mergeResources = originList.filter(resource => {
            return mergeList.includes(resource.id)
          })

          this.bindChangeResources = []

          this.mergeResources.forEach(item => {
            item.bindStatus = 'merge'
            item.newStrategy = this.curStrategy
            item.oldStrategy = res.data.overwrite_bind.find(mergeItem => {
              return mergeItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          this.unbindResources.forEach(item => {
            item.bindStatus = 'delete'
            item.newStrategy = this.curStrategy
            item.oldStrategy = res.data.unbind.find(deleteItem => {
              return deleteItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          this.addResources.forEach(item => {
            item.bindStatus = 'add'
            item.newStrategy = this.curStrategy
            item.oldStrategy = res.data.normal_bind.find(addItem => {
              return addItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          if (this.bindChangeResources.length) {
            this.tableIndex++
            setTimeout(() => {
              this.unbindResourceConf.isShow = true
            }, 10)
          } else {
            this.submitBindingData()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      submitBindingData () {
        if (this.curStrategy.scope_type === 'stage') {
          this.submitApigwStrategyStages()
        } else {
          this.submitApigwStrategyResources()
        }
      },

      async submitApigwStrategyResources () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const data = {
          scope_type: this.curStrategy.scope_type,
          scope_ids: this.scopeIds,
          type: this.curStrategy.type,
          delete: true
        }

        try {
          await this.$store.dispatch('strategy/updateApigwStrategyBindings', { apigwId, strategyId, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('绑定资源成功')
          })
          this.resourceBindSliderConf.isShow = false
          this.getApigwStrategyResources()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleHideResourceSlider () {
        this.resourceBindSliderConf.isShow = false
      },

      handleResourceChange (sourceList, targetList, targetValueList) {
        this.scopeIds = targetValueList
      },

      async handleUnbindResource (resource) {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const data = {
          scope_type: 'resource',
          scope_ids: [],
          type: this.curStrategy.type
        }

        if (Array.isArray(resource)) {
          resource.forEach(item => {
            data.scope_ids.push(item.id)
          })
        } else {
          data.scope_ids.push(resource.id)
        }

        try {
          await this.$store.dispatch('strategy/deleteApigwStrategyBindings', { apigwId, strategyId, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('解绑资源成功')
          })
          this.getApigwStrategyResources()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleResourceSelect (selectedList) {
        this.resourceUnbindList = selectedList
      },

      handleBatchUnbindResource () {
        const self = this

        if (!self.resourceUnbindList.length) {
          self.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要解绑的资源')
          })
          return false
        }

        self.$bkInfo({
          title: this.$t('确认要批量解绑资源？'),
          confirmFn () {
            self.handleUnbindResource(self.resourceUnbindList)
          }
        })
      },

      handleAddRateApp () {
        this.curStrategy.rate_limit.apps.push({
          appId: '',
          tokens: '',
          period: 1
        })
      },

      handleRemoveRateApp (app, index) {
        this.curStrategy.rate_limit.apps.splice(index, 1)
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getCurPageData(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getCurPageData(newPage)
      },

      getCurPageData (page = 1) {
        const offset = (page - 1) * this.pagination.limit
        this.curPageData = [...this.curStrategyIPGroupList].splice(offset, this.pagination.limit)
      },

      tagInputBlurHandler (input, tags) {
        const v = input.trim()
        if (!v) {
          return
        }
        this.$refs.bkAppCodeTagInpurComp.handlerResultSelect(v, 'custom')
      },
      // ip分组
      async handleIpBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.IPGroupTargetValueList))
      },
      // 环境/资源
      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.scopeIds))
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .token-area {
        border-radius: 2px;
        border: 1px solid #F0F1F5;
        background: #FAFBFD;
        padding: 20px;
    }
</style>
