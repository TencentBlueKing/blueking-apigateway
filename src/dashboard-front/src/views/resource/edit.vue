<template>
  <div class="app-content resource-wrapper" style="position: relative;">
    <div class="actions" v-if="resourceId !== undefined" v-bk-clickoutside="handleClickOutSide">
      <button class="action-btn mr25" @click="isResourceAddrShow = !isResourceAddrShow">
        {{ $t('资源地址') }}
        <i class="apigateway-icon icon-ag-down-small"></i>
      </button>
      <div class="apigateway-resource-addr" v-show="isResourceAddrShow">
        <div class="wrapper">
          <bk-form :label-width="80">
            <bk-form-item
              :label="addr.stage_name"
              v-for="(addr, index) of resourceAddrs"
              :key="index">
              <bk-input :value="addr.url" readonly>
                <template slot="append">
                  <div class="group-text">
                    <i @click="handleCopy(addr.url)" class="apigateway-icon icon-ag-copy-fill copy-btn"></i>
                  </div>
                </template>
              </bk-input>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </div>
    <bk-alert class="mb15" type="warning" :title="$t('官方网关，修改资源配置，可能导致资源不可访问，并且配置有被覆盖的风险，请谨慎修改')" v-if="OfficialApiTipsEnabledFlag && curApigw.is_official"></bk-alert>
    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('基本信息') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form
            ref="nameForm"
            :label-width="190"
            :model="curResource">
            <bk-form-item
              :label="$t('名称')"
              ref="nameFormItem"
              :rules="rules.name"
              :required="true"
              :property="'name'"
              :error-display-type="'normal'">
              <bk-input :placeholder="$t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符')" v-model="curResource.name"></bk-input>
              <p slot="tip" class="ag-tip mt5">
                <i class="apigateway-icon icon-ag-info"></i> {{ $t('资源名称在网关下唯一，将在SDK中用作操作名称，若修改，请联系SDK用户做相应调整') }}
              </p>
            </bk-form-item>
            <bk-form-item :label="$t('描述')">
              <bk-input v-model="curResource.description" :placeholder="$t('不超过512个字符')"></bk-input>
            </bk-form-item>
            <bk-form-item :label="$t('描述(英文)')" v-if="resourceEnableI18nSupportFlag">
              <bk-input v-model="curResource.description_en" :placeholder="$t('不超过512个字符')"></bk-input>
            </bk-form-item>
            <bk-form-item :label="$t('标签')">
              <bk-select
                searchable
                ref="multiSelect"
                multiple
                v-model="curResource.label_ids"
                @change="handleLabelChange"
                @toggle="toggleSelect">
                <template #trigger>
                  <div class="label-wrapper">
                    <span v-if="!curResource.label_ids.length" class="placeholder">{{ $t('请选择') }}</span>
                    <!-- 聚焦 -->
                    <template v-if="selectLabelFocus">
                      <span v-for="label in curResource.label_ids" :key="label" class="label-text">
                        {{ getLabelName(label) }}
                      </span>
                    </template>
                    <!-- 失焦 -->
                    <template v-else>
                      <template v-for="(label, index) in curResource.label_ids">
                        <span :key="label" class="label-text" v-if="index < showCount">
                          {{ getLabelName(label) }}
                        </span>
                      </template>
                      <template v-if="curResource.label_ids.length > showCount">
                        <bk-popover ext-cls="side-label-popover-cls">
                          <div slot="content" class="side-label-popover-content">
                            <span v-for="label in lastLabels" :key="label" class="label-text">
                              {{ getLabelName(label) }}
                            </span>
                          </div>
                          <span class="label-text">
                            +{{ curResource.label_ids.length - showCount }}
                          </span>
                        </bk-popover>
                      </template>
                    </template>
                  </div>
                </template>
                <bk-option v-for="option in labelList"
                  v-bk-tooltips="{ content: $t('标签最多只能选择10个'), disabled: !(!curResource.label_ids.includes(option.id) && curResource.label_ids.length >= 10) }"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name"
                  :disabled="!curResource.label_ids.includes(option.id) && curResource.label_ids.length >= 10">
                </bk-option>
                <div slot="extension" style="cursor: pointer;" class="slot-ag" @click="handleShowLabel">
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
                            <bk-input ref="addLabelInput" v-model="curLabel.name" @keyup.enter.native="createLabel"></bk-input>
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
              <!-- <bk-tag-input
                                placeholder="请选择"
                                v-model="curResource.label_ids"
                                :trigger="'focus'"
                                :list="labelList"
                                :allow-next-focus="false"
                                :content-max-height="200">
                            </bk-tag-input> -->
            </bk-form-item>
            <bk-form-item :label="$t('是否公开')" :desc="$t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')" desc-type="icon">
              <bk-switcher v-model="curResource.is_public" theme="primary" @change="handlePublicChange"></bk-switcher>
            </bk-form-item>
            <bk-form-item
              :label="$t('允许申请权限')"
              :desc="$t('允许，则任何蓝鲸应用可在蓝鲸开发者中心申请资源的访问权限；否则，只能通过网关管理员主动授权为某应用添加权限')"
              :desc-type="'icon'">
              <bk-switcher v-model="curResource.allow_apply_permission" :disabled="!curResource.is_public" theme="primary"></bk-switcher>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('前端配置') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="frontendForm" :label-width="190" :model="curResource">
            <bk-form-item
              :label="$t('请求方法')"
              :required="true"
              ref="methodFormItem"
              :error-display-type="'normal'">
              <bk-select
                :clearable="false"
                v-model="curResource.method"
                @toggle="handleMethodToggle"
                @change="handleClearRemark">
                <bk-option v-for="option in methodList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
            </bk-form-item>
            <bk-form-item
              placeholder="如：/users/{id}/"
              :required="true"
              :rules="rules.path"
              :property="'path'"
              :label="$t('请求路径')"
              :icon-offset="localLanguage === 'en' ? 178 : 156"
              ref="pathFormItem"
              :error-display-type="'normal'">
              <div class="path-form-warpper">
                <bk-input
                  v-model="curResource.path"
                  @input="handleClearRemark"
                  :placeholder="$t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
                  style="float: left; margin-right: 10px; vertical-align: middle;">
                </bk-input>
                <bk-checkbox
                  v-model="curResource.match_subpath"
                  @change="handleSubpathChange">
                  {{ $t('匹配所有子路径') }}
                  <span v-bk-tooltips="$t('若勾选，则添加子路径通配符(*)，如：/users 表示 /users/*，可匹配路径 /users/123/')">
                    <i class="apigateway-icon icon-ag-help"></i>
                  </span>
                </bk-checkbox>
              </div>
              <div slot="tip">
                <p class="ag-tip mt5">
                  <i class="apigateway-icon icon-ag-info"></i>{{ $t('资源请求路径支持路径变量，包含在{}中，如：/users/{id}/') }}
                </p>
              </div>
            </bk-form-item>

          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel">
      <div class="panel-key">
        <strong>{{ $t('后端配置') }}</strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="backendForm" :label-width="190" :model="curResource">
            <bk-form-item label="" style="height: 30px;" v-if="ResourceWithMockEnabledFlag">
              <bk-radio-group v-model="curResource.proxy_type">
                <bk-radio :value="'http'" style="margin-right: 130px;">
                  HTTP
                  <span v-bk-tooltips="$t('发送HTTP请求到后端接口，并返回接口响应')">
                    <i class="apigateway-icon icon-ag-help"></i>
                  </span>
                </bk-radio>
                <bk-radio :value="'mock'">
                  MOCK
                  <span v-bk-tooltips="$t('不发送请求到后端接口，返回使用MOCK配置构造的响应')">
                    <i class="apigateway-icon icon-ag-help"></i>
                  </span>
                </bk-radio>
              </bk-radio-group><br>
            </bk-form-item>
            <!-- http -->
            <section v-show="curResource.proxy_type === 'http'">
              <bk-form-item
                label="Method"
                :required="true"
                :error-display-type="'normal'">
                <bk-select
                  :clearable="false"
                  v-model="curResource.proxy_configs.http.method">
                  <bk-option v-for="option in methodList"
                    :key="option.id"
                    :id="option.id"
                    :name="option.name">
                  </bk-option>
                </bk-select>
              </bk-form-item>
              <bk-form-item
                :rules="rules.path"
                :required="true"
                :property="'proxy_configs.http.path'"
                :icon-offset="230"
                label="Path"
                :error-display-type="'normal'">
                <div class="path-form-warpper">
                  <bk-input
                    type="text"
                    v-model="curResource.proxy_configs.http.path"
                    :placeholder="$t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名')"
                    style="float: left; margin-right: 10px; vertical-align: middle;line-height: 30px;">
                    <template slot="append">
                      <div class="ag-inner-btn" @click="handleCheckResourcePath">{{ $t('校验') }}</div>
                    </template>
                  </bk-input>
                  <bk-checkbox
                    :disabled="true"
                    v-model="curResource.proxy_configs.http.match_subpath">
                    {{ $t('追加匹配的子路径') }}
                    <span v-bk-tooltips="$t('将实际请求中，请求路径通配符(*)匹配到的子路径部分，追加到 Path')">
                      <i class="apigateway-icon icon-ag-help"></i>
                    </span>
                  </bk-checkbox>
                </div>
                <div slot="tip">
                  <p class="ag-tip mt5" style="word-break: break-all;">
                    <i class="apigateway-icon icon-ag-info"></i>
                    {{ $t('后端接口地址的Path，不包含域名或IP，支持路径变量、环境变量，变量包含在{}中，比如：/users/{id}/{env.type}/。') }}
                    <a :href="GLOBAL_CONFIG.DOC.TEMPLATE_VARS" target="_blank" class="ag-primary">{{ $t('更多详情') }}</a>
                  </p>
                </div>
              </bk-form-item>
              <bk-form-item label="Hosts">
                <div class="bk-button-group">
                  <bk-button
                    class="ag-tab-button"
                    :class="httpConf.useDefaultHost ? 'is-selected' : ''"
                    @click="httpConf.useDefaultHost = true">
                    <bk-popover ext-cls="ag-special-popover">
                      <div slot="content" class="pt5 pb5">
                        <bk-table style="width: 600px;"
                          :data="baseStageInfo.hosts"
                          :size="'small'"
                          :max-height="210"
                          :ext-cls="'ag-stage-basic'">
                          <div slot="empty">
                            <table-empty empty />
                          </div>
                          <bk-table-column width="130" :label="$t('环境名称')" column="name" prop="name" :render-header="$renderHeader"></bk-table-column>
                          <bk-table-column :show-overflow-tooltip="false" label="Hosts" column="host" prop="host">
                            <template slot-scope="props">
                              <p class="default-env-text" style="max-width: 250px; " v-for="hostItem of props.row.hosts" :key="hostItem.host" v-bk-overflow-tips>{{hostItem.host}}</p>
                            </template>
                          </bk-table-column>
                          <bk-table-column width="120" :label="$t('权重')">
                            <template slot-scope="props">
                              <template v-if="props.row.loadbalance === 'weighted-roundrobin'">
                                <p class="default-env-text" style="max-width: 120px; " v-for="hostItem of props.row.hosts" :key="hostItem.host">{{hostItem.weight || '--'}}</p>
                              </template>
                              <template v-else>--</template>
                            </template>
                          </bk-table-column>
                        </bk-table>
                      </div>
                      <div class="f14">{{ $t('使用环境配置') }}</div>
                    </bk-popover>
                  </bk-button>
                  <bk-button
                    class="ag-tab-button"
                    :class="!httpConf.useDefaultHost ? 'is-selected' : ''"
                    @click="httpConf.useDefaultHost = false">
                    {{ $t('覆盖环境配置') }}
                  </bk-button>
                  <p class="ag-tip mt5" style="white-space: nowrap;">
                    <i class="apigateway-icon icon-ag-info"></i>
                    {{ $t('使用环境配置，则使用各环境默认Hosts；覆盖环境配置，则使用资源自定义Hosts') }}
                  </p>
                </div>
                <section class="ag-area mt10" style="padding-right: 70px;" v-show="!httpConf.useDefaultHost">
                  <bk-form ref="proxyForm" :label-width="190" :model="curResource">
                    <bk-form-item
                      :label="$t('负载均衡类型')"
                      :required="true"
                      :error-display-type="'normal'">
                      <bk-select
                        :clearable="false"
                        :placeholder="$t('负载均衡类型')"
                        v-model="curResource.proxy_configs.http.upstreams.loadbalance">
                        <bk-option v-for="option in loadbalanceList"
                          :key="option.id"
                          :id="option.id"
                          :name="option.name">
                        </bk-option>
                      </bk-select>
                    </bk-form-item>
                    <bk-form-item
                      label="Hosts"
                      :required="true"
                      :rules="rules.host"
                      :property="'proxy_configs.http.upstreams.hosts.' + index + '.host'"
                      v-for="(hostItem, index) of curResource.proxy_configs.http.upstreams.hosts"
                      :key="index"
                      :icon-offset="curResource.proxy_configs.http.upstreams.loadbalance === 'weighted-roundrobin' ? 90 : 10"
                      :class="{ 'form-item-special': index !== 0 }"
                      :error-display-type="'normal'">
                      <div class="host-item mb10">
                        <bk-input
                          :placeholder="$t('格式: http(s)://host:port')"
                          v-model="hostItem.host"
                          v-if="curResource.proxy_configs.http.upstreams.loadbalance === 'weighted-roundrobin'"
                          :key="curResource.proxy_configs.http.upstreams.loadbalance">
                          <div class="hosts-append-wrapper" slot="append">
                            <bk-input
                              :class="['ag-host-input', 'weights-input', { 'is-error': hostItem.isRoles }]"
                              type="number"
                              :placeholder="$t('权重')"
                              style="border: none !important;"
                              :min="1"
                              :max="10000"
                              :show-controls="false"
                              v-model="hostItem.weight"
                              @input="weightValidate(hostItem)">
                            </bk-input>
                            <i v-if="hostItem.isRoles" class="bk-icon icon-exclamation-circle-shape tooltips-icon" v-bk-tooltips="hostItem.message"></i>
                          </div>
                        </bk-input>

                        <bk-input
                          :placeholder="$t('格式: http(s)://host:port')"
                          v-model="hostItem.host"
                          v-else
                          :key="curResource.proxy_configs.http.upstreams.loadbalance">
                        </bk-input>

                        <i class="add-host-btn apigateway-icon icon-ag-plus-circle-shape" @click="handleAddHost"></i>
                        <i class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape" @click="handleDeleteHost(hostItem, index)" v-if="curResource.proxy_configs.http.upstreams.hosts.length >= 2"></i>
                      </div>
                    </bk-form-item>
                    <p class="ag-tip mt5" style="margin-left: 130px;white-space: nowrap;">
                      <i class="apigateway-icon icon-ag-info"></i>{{ $t('网关调用后端接口的域名或IP，不包含Path，比如：https://example.com') }}
                    </p>
                  </bk-form>
                </section>
              </bk-form-item>

              <bk-form-item :label="$t('超时时间')">
                <div class="bk-button-group">
                  <bk-button
                    class="ag-tab-button"
                    :class="httpConf.useDefaultTimeout ? 'is-selected' : ''"
                    @click="httpConf.useDefaultTimeout = true">
                    <bk-popover ext-cls="ag-special-popover">
                      <div slot="content" class="pt5 pb5">
                        <bk-table style="width: 300px;"
                          :data="baseStageInfo.timeouts"
                          :size="'small'"
                          :max-height="210"
                          :ext-cls="'ag-stage-basic'">
                          <bk-table-column :label="$t('环境名称')" column="name" prop="name" :render-header="$renderHeader"></bk-table-column>
                          <bk-table-column width="100" :label="$t('超时时间')" column="timeout" prop="timeout" :render-header="$renderHeader">
                            <template slot-scope="props">
                              {{props.row.timeout}} {{ $t('秒') }}
                            </template>
                          </bk-table-column>
                        </bk-table>
                      </div>
                      <div class="f14">{{ $t('使用环境配置') }}</div>
                    </bk-popover>
                  </bk-button>
                  <bk-button
                    class="ag-tab-button"
                    :class="!httpConf.useDefaultTimeout ? 'is-selected' : ''"
                    @click="httpConf.useDefaultTimeout = false">
                    {{ $t('覆盖环境配置') }}
                  </bk-button>
                  <p class="ag-tip mt5" style="white-space: nowrap;">
                    <i class="apigateway-icon icon-ag-info"></i>
                    {{ $t('使用环境配置，则使用各环境默认超时时间；覆盖环境配置，则使用资源自定义超时时间') }}
                  </p>
                </div>
                <section class="ag-area mt10" v-if="!httpConf.useDefaultTimeout">
                  <bk-form-item
                    :label="$t('超时时间')"
                    :rules="rules.timeout"
                    :property="'proxy_configs.http.timeout'"
                    :icon-offset="192"
                    :required="true"
                    style="width: 480px;"
                    :error-display-type="'normal'">
                    <bk-input
                      type="number"
                      :show-controls="false"
                      :min="1"
                      v-model="curResource.proxy_configs.http.timeout"
                      class="time-input">
                      <template slot="append">
                        <div class="group-text group-text-style">{{ $t('秒') }}</div>
                      </template>
                    </bk-input>
                    <span class="ag-text" style="line-height: 32px;">{{ $t('最大300秒') }}</span>
                  </bk-form-item>
                </section>
              </bk-form-item>
              <bk-form-item :label="$t('Header转换')">
                <div class="bk-button-group">
                  <bk-button
                    class="ag-tab-button"
                    :class="httpConf.useDefaultHeader ? 'is-selected' : ''"
                    @click="httpConf.useDefaultHeader = true">
                    <bk-popover ext-cls="ag-special-popover">
                      <div slot="content" class="pt5 pb5">
                        <bk-table
                          :data="baseStageInfo.headers"
                          :size="'small'"
                          :max-height="210"
                          :ext-cls="'ag-stage-basic'">
                          <div slot="empty">
                            <table-empty empty />
                          </div>
                          <bk-table-column width="130" :label="$t('环境名称')" column="name" prop="name" :render-header="$renderHeader"></bk-table-column>
                          <bk-table-column width="270" :label="$t('设置')" :show-overflow-tooltip="false">
                            <template slot-scope="props">
                              <template v-if="props.row.set.length">
                                <p class="default-env-text" v-for="item of props.row.set" :key="item.key" v-bk-overflow-tips>{{item.key || '--'}}: {{item.value || '--'}}</p>
                              </template>
                              <template v-else>--</template>
                            </template>
                          </bk-table-column>
                          <bk-table-column :label="$t('删除')" :show-overflow-tooltip="false">
                            <template slot-scope="props">
                              <template v-if="props.row.delete && props.row.delete.length">
                                <p class="default-env-text" v-for="item of props.row.delete" :key="item" v-bk-overflow-tips>{{item}}</p>
                              </template>
                              <template v-else>--</template>
                            </template>
                          </bk-table-column>
                        </bk-table>
                      </div>
                      <div class="f14">{{ $t('使用环境配置') }}</div>
                    </bk-popover>
                  </bk-button>
                  <bk-button
                    class="ag-tab-button mr5"
                    :class="!httpConf.useDefaultHeader ? 'is-selected' : ''"
                    @click="httpConf.useDefaultHeader = false">
                    {{ $t('追加环境配置') }}
                  </bk-button>
                  <p class="ag-tip mt5" style="white-space: nowrap;">
                    <i class="apigateway-icon icon-ag-info"></i>
                    {{ $t('使用环境配置，则使用各环境默认Header转换配置；追加环境配置，则将资源自定义配置与环境默认配置合并') }}
                  </p>
                </div>
                <section class="ag-area ag-area-en mt10" v-show="!httpConf.useDefaultHeader">
                  <bk-form class="ag-header-form" :label-width="0">
                    <bk-form-item label="">
                      <!-- <span class="f12">{{curResource.proxy_configs.http.transform_headers.set}}</span> -->
                      <apigw-key-valuer
                        ref="setKeyValuer"
                        class="mb10"
                        :label="$t('设置')"
                        :key="curResource.proxy_type"
                        v-if="curResource.proxy_type === 'http'"
                        :value="curResource.proxy_configs.http.transform_headers.set">
                      </apigw-key-valuer>
                      <apigw-item
                        ref="deleteKeyValuer"
                        :label="$t('删除')"
                        :value="curResource.proxy_configs.http.transform_headers.delete">
                      </apigw-item>
                    </bk-form-item>
                    <p class="ag-tip mt5" style="white-space: nowrap;">
                      <i class="apigateway-icon icon-ag-info"></i>{{ $t('网关调用后端接口时，请求头处理配置。设置，表示将请求头设置为指定值；删除，表示删除指定的请求头') }}
                    </p>
                  </bk-form>
                </section>
              </bk-form-item>
            </section>
            <!-- mock -->
            <section v-show="curResource.proxy_type === 'mock' && ResourceWithMockEnabledFlag">
              <bk-form-item
                label="Status Code"
                :required="true"
                :rules="rules.code"
                :property="'proxy_configs.mock.code'"
                :error-display-type="'normal'">
                <bk-input
                  type="number"
                  :min="0"
                  :show-controls="false"
                  :placeholder="$t('请输入')"
                  v-model="curResource.proxy_configs.mock.code">
                </bk-input>
              </bk-form-item>
              <bk-form-item
                label="Response Body"
                :key="curResource.proxy_type">
                <code-viewer
                  ref="bodyCodeViewer"
                  :placeholder="$t('请输入内容')"
                  :value="curResource.proxy_configs.mock.body"
                  :width="'100%'"
                  :height="320"
                  :lang="'text'"
                  @input="handleInputBody">
                </code-viewer>
              </bk-form-item>
              <bk-form-item
                label="Headers"
                :rules="rules.name"
                :property="'name'"
                :error-display-type="'normal'">
                <apigw-key-valuer
                  ref="mockKeyValuer"
                  :key="curResource.proxy_type"
                  v-if="curResource.proxy_type === 'mock'"
                  :value="curResource.proxy_configs.mock.headers">
                </apigw-key-valuer>
              </bk-form-item>
            </section>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel">
      <div class="panel-key">
        <strong>{{ $t('安全设置') }}</strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form :label-width="190">
            <bk-form-item :label="$t('应用认证')">
              <bk-switcher
                class="mr20"
                size="small"
                theme="primary"
                :disabled="!curApigw.allow_update_api_auth"
                v-model="curResource.auth_config.app_verified_required">
              </bk-switcher>
              <bk-checkbox
                :true-value="true"
                :false-value="false"
                :disabled="!curResource.auth_config.app_verified_required || !curApigw.allow_update_api_auth"
                v-model="curResource.auth_config.resource_perm_required">
                {{ $t('校验访问权限') }}
              </bk-checkbox>
              <p class="ag-tip mt5">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('应用认证，请求方需提供蓝鲸应用身份信息；校验访问权限，蓝鲸应用需申请资源访问权限。') }}
                <a :href="GLOBAL_CONFIG.DOC.AUTH" target="_blank" class="ag-primary">{{ $t('更多详情') }}</a>
              </p>
            </bk-form-item>
            <bk-form-item :label="$t('用户认证')">
              <bk-switcher
                v-model="curResource.auth_config.auth_verified_required"
                size="small"
                theme="primary">
              </bk-switcher>
              <p class="ag-tip mt5">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('用户认证，请求方需提供蓝鲸用户身份信息。') }}
                <a :href="GLOBAL_CONFIG.DOC.AUTH" target="_blank" class="ag-primary">{{ $t('更多详情') }}</a>
              </p>
            </bk-form-item>

            <span class="ag-span" v-if="resourceDisableStageEnabledFlag"></span>

            <bk-form-item :label="$t('禁用环境')" v-if="resourceDisableStageEnabledFlag">
              <bk-select
                searchable
                multiple
                show-select-all
                v-model="curResource.disabled_stage_ids">
                <bk-option v-for="option in stageList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
              <!-- <bk-tag-input
                                placeholder="请选择"
                                :content-max-height="200"
                                v-model="curResource.disabled_stage_ids"
                                :trigger="'focus'"
                                :list="stageList"
                                :allow-next-focus="false">
                            </bk-tag-input> -->
              <p class="ag-tip mt10">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('资源将不会发布到对应的环境') }}
              </p>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel-action mt20">
      <div class="panel-content" style="margin-left: 270px;">
        <div class="panel-wrapper tc">
          <bk-button
            class="mr5"
            theme="primary"
            style="width: 120px;"
            :loading="isDataLoading"
            @click="submitApigwResource">
            {{ $t('提交') }}
          </bk-button>
          <bk-button
            style="width: 120px;"
            @click="handleApigwResourceCancel">
            {{ $t('取消') }}
          </bk-button>
        </div>
      </div>
    </section>

    <bk-dialog
      v-model="labelDialogConf.visiable"
      theme="primary"
      :width="480"
      :header-position="'left'"
      :title="labelDialogConf.title"
      :loading="labelDialogConf.isLoading"
      @confirm="handleSubmitLabel"
      @cancel="handleCancel">
      <bk-form
        :label-width="200"
        form-type="vertical"
        :model="curLabel"
        :rules="labelRules"
        ref="labelForm">
        <bk-form-item :label="$t('标签名称')" :required="true" :property="'name'">
          <bk-input v-model="curLabel.name"></bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import ApigwKeyValuer from '@/components/key-valuer'
  // import ApigwKeyer from '@/components/keyer'
  import ApigwItem from '@/components/item'

  const httpCodes = [200, 201, 202, 203, 204, 205, 206, 300, 301, 302, 303, 304, 305, 306, 307, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 450, 451, 500, 501, 502, 503, 504, 505]

  const labelMaxWidth = 400

  export default {
    components: {
      ApigwKeyValuer,
      // ApigwKeyer,
      ApigwItem
    },
    data () {
      return {
        varIndex: 0,
        isPageLoading: true,
        isDataLoading: false,
        labelList: [],
        stageList: [],
        resourceAddrs: [],
        isResourceAddrShow: false,
        labelDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('新建标签')
        },
        baseStageInfo: {
          timeouts: [],
          hosts: [],
          headers: []
        },
        curLabel: {
          name: ''
        },
        curLabelList: [
          {
            key: '',
            value: ''
          }
        ],
        loadbalanceList: [
          {
            id: 'roundrobin',
            name: this.$t('轮询(Round-Robin)')
          },
          {
            id: 'weighted-roundrobin',
            name: this.$t('加权轮询(Weighted Round-Robin)')
          }
        ],
        httpConf: {
          useDefaultHost: true,
          useDefaultTimeout: true,
          useDefaultHeader: true
        },
        'httpParams': {
          'method': 'GET',
          'path': '',
          'timeout': 30,
          'upstreams': {
            'loadbalance': 'roundrobin',
            'hosts': [
              {
                'host': '',
                'weight': 100
              }
            ]
          },
          'transform_headers': {
            'set': {},
            'delete': []
          }
        },
        'mockParams': {
          'code': 200,
          'body': '',
          'headers': {}
        },
        curResource: {
          'name': '',
          'description': '',
          'description_en': '',
          'proxy_type': 'http',
          'is_public': true,
          'allow_apply_permission': true,
          'label_ids': [],
          'method': 'GET',
          'path': '',
          'match_subpath': false,
          'proxy_configs': {
            'http': {
              'method': 'GET',
              'path': '',
              'match_subpath': false,
              'timeout': 30,
              'upstreams': {
                'loadbalance': 'roundrobin',
                'hosts': [
                  {
                    'host': '',
                    'weight': 100
                  }
                ]
              },
              'transform_headers': {
                'set': {},
                'delete': []
              }
            },
            'mock': {
              'code': 200,
              'body': '',
              'headers': {}
            }
          },
          'auth_config': {
            'auth_verified_required': true,
            'app_verified_required': true,
            'resource_perm_required': true
          },
          'disabled_stage_ids': []
        },
        isCreateLabel: false,
        selectLabelFocus: false,
        showCount: 4,
        isMaxWidth: false,
        labelRules: {
          name: [
            {
              max: 32,
              message: this.$t('不能多于32个字符'),
              trigger: 'change'
            }
          ]
        },
        cloneData: {
          method: '',
          path: ''
        },
        cloneTips: this.$t('请求方法+请求路径在网关下唯一，请至少调整其中一项'),
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              regex: /^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/,
              message: this.$t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符'),
              trigger: 'blur'
            }
          ],
                    
          path: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              regex: /^\/[\w{}/.-]*$/,
              message: this.$t('斜线(/)开头的合法URL路径，不包含http(s)开头的域名'),
              trigger: 'blur'
            }
          ],

          host: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              regex: /(?=^.{3,255}$)http(s)?:\/\/[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?(\/)?$|^http(s)?:\/\/\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?\/?$|^http(s)?:\/\/\{env.[a-zA-Z][a-zA-Z0-9_]{0,49}\}(\/)?$/,
              message: this.$t('请输入合法Host，如：http://example.com'),
              trigger: 'blur'
            }
          ],

          timeout: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              validator: function (val) {
                if (val < 1 || val > 300) {
                  return false
                }
                return true
              },
              message: this.$t('超时时间不能小于1且不能大于300'),
              trigger: 'blur'
            }
          ],

          code: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              validator: function (val) {
                return httpCodes.includes(Number(val))
              },
              message: this.$t('请输入合法Status Code值'),
              trigger: 'blur'
            }
          ]
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      curApigw () {
        return this.$store.state.curApigw
      },
      methodList () {
        return this.$store.state.options.methodList
      },
      resourceId () {
        return this.$route.params.resourceId || undefined
      },
      isClone () {
        return this.$route.name === 'apigwResourceClone'
      },
      pageTitle () {
        if (this.isClone) {
          return this.$t('克隆资源')
        } else if (this.resourceId !== undefined) {
          return this.$t('编辑资源')
        } else {
          return this.$t('新建资源')
        }
      },
      curApigwName () {
        const apigwList = this.$store.state.apis.apigwList
        const apigw = apigwList.find(apigw => {
          return String(apigw.id) === String(this.apigwId)
        })
        return apigw ? apigw.name : ''
      },
      ResourceWithMockEnabledFlag () {
        if (!this.curApigw.feature_flags) return false
        return this.curApigw.feature_flags.RESOURCE_WITH_MOCK_ENABLED
      },
      resourceDisableStageEnabledFlag () {
        if (!this.curApigw.feature_flags) return false
        return this.curApigw.feature_flags.RESOURCE_DISABLE_STAGE_ENABLED
      },
      backupsCurrent () {
        return this.$route.params.current
      },
      OfficialApiTipsEnabledFlag () {
        if (!this.curApigw.feature_flags) return false
        return this.curApigw.feature_flags.OFFICIAL_API_TIPS_ENABLED
      },
      backupsLimit () {
        return this.$route.params.limit
      },
      backupKeyword () {
        return this.$route.params.keyword
      },
      resourceEnableI18nSupportFlag () {
        if (!this.curApigw.feature_flags) return false
        return this.curApigw.feature_flags.ENABLE_I18N_SUPPORT
      },
      lastLabels () {
        return this.curResource.label_ids.slice(this.showCount)
      },
      localLanguage () {
        return this.$store.state.localLanguage
      },
      isCloneFlag () {
        return this.cloneData.method !== this.curResource.method || this.cloneData.path !== this.curResource.path
      }
    },
    watch: {
      'curResource.auth_config.app_verified_required' (val) {
        if (!val) {
          this.curResource.auth_config.resource_perm_required = false
        }
      },
      isCloneFlag (val) {
        if (this.isClone) {
          if (!val) {
            this.addPathRule()
            this.addMethodValidator()
            this.$refs.pathFormItem.validate()
          } else {
            this.removePathRule()
          }
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwStages()
        this.getApigwLabels()
        this.getApigwStageBaseInfo()

        if (this.resourceId !== undefined) {
          this.getResourceDetail()
          this.getResourceAddr()
        } else {
          this.setHeaderWatch()
          setTimeout(() => {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }, 500)
        }
      },

      goBack () {
        this.goResourceIndex()
      },

      setHeaderWatch () {
        // 临时保存header编辑信息
        this.$watch('httpConf.useDefaultHeader', (newValue, oldValue) => {
          if (!oldValue && newValue) {
            this.saveHttpHeader()
          }
        })

        // 临时保存header编辑信息
        this.$watch('curResource.proxy_type', (newValue, oldValue) => {
          const proxyConfigs = this.curResource.proxy_configs

          if (oldValue === 'http' && newValue === 'mock') {
            if (!this.httpConf.useDefaultHeader) {
              this.saveHttpHeader()
            }
          } else {
            proxyConfigs.mock.headers = (this.$refs.mockKeyValuer && this.$refs.mockKeyValuer.getValue()) || {}
          }
        })
      },

      saveHttpHeader () {
        const header = this.curResource.proxy_configs.http.transform_headers
        header.set = (this.$refs.setKeyValuer && this.$refs.setKeyValuer.getValue()) || {}
        header.delete = (this.$refs.deleteKeyValuer && this.$refs.deleteKeyValuer.getValue()) || []
      },

      async getResourceDetail () {
        try {
          const apigwId = this.apigwId
          const resourceId = this.resourceId
          const res = await this.$store.dispatch('resource/getApigwResourceDetail', { apigwId, resourceId })

          const data = res.data
          const proxyConfigs = res.data.proxy_configs

          // 完善整个数据
          proxyConfigs.mock = proxyConfigs.mock || this.mockParams

          // 开始保存是mock
          if (!proxyConfigs.http) {
            proxyConfigs.http = this.httpParams
          } else {
            const httpConfigs = proxyConfigs.http
            if (httpConfigs.timeout) {
              this.httpConf.useDefaultTimeout = false
            } else {
              // 默认值为30，如果没修改提交时会重置为0
              httpConfigs.timeout = 30
            }

            if (JSON.stringify(httpConfigs.upstreams) === '{}') {
              httpConfigs.upstreams = {
                'loadbalance': 'roundrobin',
                'hosts': [
                  {
                    'host': '',
                    'weight': 100
                  }
                ]
              }
            } else {
              this.httpConf.useDefaultHost = false
            }
            if (JSON.stringify(httpConfigs.transform_headers) === '{}') {
              httpConfigs.transform_headers = {
                'set': {},
                'delete': []
              }
            } else {
              this.httpConf.useDefaultHeader = false
            }
          }

          data.proxy_configs.http.match_subpath = data.match_subpath

          // 克隆操作
          if (this.isClone) {
            this.$set(this.cloneData, 'method', data.method)
            this.$set(this.cloneData, 'path', data.path)
            data.name = `${data.name}_cloned`
            this.remarkFormInput()
          }
          this.curResource = data
          this.setHeaderWatch()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }, 500)
        }
      },

      handleClearRemark () {
        this.$refs.methodFormItem.setValidator({
          state: '',
          content: ''
        })
        this.$refs.pathFormItem.setValidator({
          state: '',
          content: ''
        })
      },

      handleSubpathChange () {
        this.curResource.proxy_configs.http.match_subpath = this.curResource.match_subpath
      },

      remarkFormInput () {
        setTimeout(() => {
          if (!this.isClone) {
            this.$refs.nameFormItem.setValidator({
              state: 'error',
              content: this.$t('资源名称在网关下唯一，请输入新的资源名称')
            })
          }
          this.$refs.methodFormItem.setValidator({
            state: 'error',
            content: this.cloneTips
          })
          this.$refs.pathFormItem.setValidator({
            state: 'error',
            content: this.cloneTips
          })
        }, 1000)
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

      async getApigwStageBaseInfo (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true
        }

        try {
          const res = await this.$store.dispatch('resource/getStageBaseInfo', { apigwId, pageParams })
          const timeouts = []
          const hosts = []
          const headers = []
          res.data.results.forEach(item => {
            const proxyHttp = item.proxy_http
            // 超时时间
            timeouts.push({
              name: item.name,
              timeout: proxyHttp.timeout
            })

            // Hosts
            hosts.push({
              name: item.name,
              loadbalance: proxyHttp.upstreams.loadbalance,
              hosts: proxyHttp.upstreams.hosts
            })

            // Header转换
            const headerItem = {
              name: item.name,
              set: [],
              delete: proxyHttp.transform_headers.delete
            }
            for (const key in proxyHttp.transform_headers.set) {
              headerItem.set.push({
                key: key,
                value: proxyHttp.transform_headers.set[key]
              })
            }
            headers.push(headerItem)
          })
          this.baseStageInfo = {
            timeouts,
            hosts,
            headers
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getResourceAddr (page) {
        const apigwId = this.apigwId
        const resourceId = this.resourceId

        try {
          const res = await this.$store.dispatch('resource/getApigwResourceAddr', { apigwId, resourceId })
          this.resourceAddrs = res.data
        } catch (e) {
          catchErrorHandler(e, this)
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

      handleAddHost () {
        this.curResource.proxy_configs.http.upstreams.hosts.push({
          host: '',
          weight: 100,
          isRoles: false,
          message: ''
        })
      },

      handleDeleteHost (host, index) {
        this.curResource.proxy_configs.http.upstreams.hosts.splice(index, 1)
      },

      handleApigwResourceCancel () {
        this.pageTitle === '编辑资源' ? this.goResourceIndex('update') : this.goResourceIndex()
      },

      goResourceIndex (type) {
        if (type === 'update') {
          this.$router.push({
            name: 'apigwResource',
            params: {
              id: this.apigwId,
              current: this.backupsCurrent,
              limit: this.backupsLimit,
              keyword: this.backupKeyword
            }
          })
        } else {
          this.$router.push({
            name: 'apigwResource',
            params: {
              id: this.apigwId
            }
          })
        }
      },

      formatData () {
        const params = JSON.parse(JSON.stringify(this.curResource))
        const proxyConfigs = params.proxy_configs
        if (params.proxy_type === 'http') {
          delete proxyConfigs.mock

          if (this.httpConf.useDefaultTimeout) {
            proxyConfigs.http.timeout = 0
          }

          if (this.httpConf.useDefaultHeader) {
            proxyConfigs.http.transform_headers = {}
          } else {
            const header = proxyConfigs.http.transform_headers
            header.set = (this.$refs.setKeyValuer && this.$refs.setKeyValuer.getValue()) || {}
            header.delete = (this.$refs.deleteKeyValuer && this.$refs.deleteKeyValuer.getValue()) || []
          }

          if (this.httpConf.useDefaultHost) {
            proxyConfigs.http.upstreams = {}
          }
        } else {
          proxyConfigs.mock.headers = (this.$refs.mockKeyValuer && this.$refs.mockKeyValuer.getValue()) || {}
          delete proxyConfigs.http
        }
        return params
      },

      checkHeader (params, headerKey, type) {
        const varReg = /^[a-zA-Z0-9-]+$/
        const proxy = params.proxy_configs[type]
        const header = (type === 'http') ? proxy.transform_headers[headerKey] : proxy.headers
        for (const key in header) {
          if (!key) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Header转换中的键')
            })
            this.$refs[`${headerKey}KeyValuer`].validate()
            return false
          }

          if (!varReg.test(key)) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入合法的Header转换键')
            })
            this.$refs[`${headerKey}KeyValuer`].validate()
            return false
          }

          if (!header[key]) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Header转换值')
            })
            this.$refs[`${headerKey}KeyValuer`].validate()
            return false
          }

          if (!this.$refs[`${headerKey}KeyValuer`].checkRepeat()) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('后端配置Header转换中不允许重复值')
            })
            return false
          }
        }
        return true
      },

      checkData (params) {
        const hostReg = /(?=^.{3,255}$)http(s)?:\/\/[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?(\/)?$|^http(s)?:\/\/\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?\/?$|^http(s)?:\/\/\{env.[a-zA-Z][a-zA-Z0-9_]{0,49}\}(\/)?$/
        const pathReg = /^\/[\w{}/.-]*$/

        // 是否通过校验
        let isCheck = true

        const fromRefArray = ['nameForm', 'frontendForm']
        for (let i = 0; i < fromRefArray.length; i++) {
          const refName = fromRefArray[i]
          this.$refs[refName].validate().then(validator => {
            isCheck = true
          }, error => {
            isCheck = false
            console.error(error)
          })
        }

        if (params.proxy_type === 'http') {
          if (!params.proxy_configs.http.path) {
            this.$refs.backendForm.validate()
            isCheck = false
          }

          if (!pathReg.test(params.proxy_configs.http.path)) {
            this.$refs.backendForm.validate()
            isCheck = false
          }
        }

        if (params.proxy_type === 'http' && !this.httpConf.useDefaultHost) {
          const httpParams = params.proxy_configs.http
          const hosts = httpParams.upstreams.hosts
          for (let i = 0; i < hosts.length; i++) {
            const hostItem = hosts[i]
            if (!hostItem.host) {
              this.$refs.proxyForm.validate()
              isCheck = false
            }

            if (!hostReg.test(hostItem.host)) {
              this.$refs.proxyForm.validate()
              isCheck = false
            }
            if (hostItem.isRoles) {
              isCheck = false
            }
          }
        }

        if (params.proxy_type === 'http' && !this.httpConf.useDefaultTimeout) {
          const timeout = params.proxy_configs.http.timeout
          if (timeout < 1 || timeout > 300) {
            isCheck = false
          }
        }

        if (params.proxy_type === 'http' && !this.httpConf.useDefaultHeader) {
          // if (!this.checkHeader(params, 'add', 'http')) {
          //     return false
          // }

          // if (!this.checkHeader(params, 'append', 'http')) {
          //     return false
          // }
          if (!this.checkHeader(params, 'set', 'http')) {
            isCheck = false
          }

          if (params.proxy_configs.http.transform_headers['delete']) {
            const keyReg = /^[a-zA-Z0-9-]*$/
            const deleteHeaders = params.proxy_configs.http.transform_headers['delete']
            const uniqueList = [...new Set(deleteHeaders)]

            if (!keyReg.test(deleteHeaders.join(''))) {
              this.$refs.deleteKeyValuer.validate()
              isCheck = false
            }

            if (uniqueList.length < deleteHeaders.length) {
              this.$refs.deleteKeyValuer.validate()
              isCheck = false
            }
          }
        } else if (params.proxy_type === 'mock') {
          const code = params.proxy_configs.mock.code
          if (!code) {
            isCheck = false
          }

          if (!httpCodes.includes(Number(code))) {
            isCheck = false
          }

          if (!this.checkHeader(params, 'mock', 'mock')) {
            isCheck = false
          }
        }

        // 过滤前端校验字段
        if (params.proxy_type === 'http') {
          if (params.proxy_configs.http.upstreams.hosts && params.proxy_configs.http.upstreams.hosts.length) {
            for (let i = 0; i < params.proxy_configs.http.upstreams.hosts.length; i++) {
              delete params.proxy_configs.http.upstreams.hosts[i].isRoles
              delete params.proxy_configs.http.upstreams.hosts[i].message
            }
          }
        }

        if (this.isClone && !this.isCloneFlag) {
          this.addMethodValidator()
          isCheck = false
        }

        return isCheck
      },

      submitApigwResource () {
        const params = this.formatData()

        // 统一触发验证
        if (this.checkData(params)) {
          if (!this.isClone && this.resourceId !== undefined) {
            this.updateApigwResource(params)
          } else {
            this.addApigwResource(params)
          }
        }
      },

      async addApigwResource (data) {
        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          await this.$store.dispatch('resource/addApigwResource', { apigwId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
          this.goResourceIndex()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async updateApigwResource (data) {
        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          const resourceId = this.resourceId
          await this.$store.dispatch('resource/updateApigwResource', { apigwId, resourceId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
          this.goResourceIndex('update')
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async handleCheckResourcePath (data) {
        if (!this.curResource.proxy_configs.http.path) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入Path')
          })
          return false
        }
        try {
          const apigwId = this.apigwId
          const resourceId = this.resourceId
          const data = {
            path: this.curResource.path,
            proxy_path: this.curResource.proxy_configs.http.path
          }
          await this.$store.dispatch('resource/checkApigwResourcePath', { apigwId, resourceId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('验证通过')
          })
          // this.goResourceIndex()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          // this.isDataLoading = false
        }
      },

      handleClickOutSide () {
        this.isResourceAddrShow = false
      },

      handleCopy (text) {
        this.$copyText(text).then((e) => {
          this.isResourceAddrShow = false
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

      handleInputBody (content) {
        this.curResource.proxy_configs.mock.body = content
      },

      handleShowLabelDialog () {
        this.curLabel.name = ''
        this.curLabel.id = undefined
        this.labelDialogConf.title = this.$t('新建标签')
        this.labelDialogConf.visiable = true
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

      handleSubmitLabel () {
        if (this.labelDialogConf.isLoading) {
          return false
        }
        this.labelDialogConf.isLoading = true
        this.$refs.labelForm.validate().then(() => {
          this.addLabel()
        }).catch(() => {
          this.$nextTick(() => {
            this.labelDialogConf.isLoading = false
          })
        })
      },

      handleCancel () {
        this.clearLabelForm()
      },

      handlePublicChange () {
        this.curResource.allow_apply_permission = this.curResource.is_public
      },

      clearLabelForm () {
        this.curLabel.name = ''
        delete this.curLabel.id
        this.$refs.labelForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async addLabel () {
        try {
          const data = { name: this.curLabel.name }
          const apigwId = this.apigwId
          const res = await this.$store.dispatch('label/addApigwLabel', { apigwId, data })
          this.curResource.label_ids.push(res.data.id)
          this.labelDialogConf.visiable = false
          this.clearLabelForm()
          this.getApigwLabels()
          this.abrogate()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.labelDialogConf.isLoading = false
        }
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

      toggleSelect (status) {
        this.selectLabelFocus = status
        this.isCreateLabel = false
        this.curLabel.name = ''
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
      },

      abrogate () {
        if (this.labelRules.name.length > 1) {
          this.labelRules.name.splice(1, 1)
        }
        setTimeout(() => {
          this.isCreateLabel = false
        }, 50)
      },

      weightValidate (hostItem) {
        if (!hostItem.weight) {
          hostItem.isRoles = true
          hostItem.message = this.$t('请输入合法的整数值')
        } else {
          hostItem.isRoles = false
        }
      },
      getLabelName (id) {
        const curLabel = this.labelList.find(label => String(label.id) === String(id)) || {}
        return curLabel.name
      },
      handleLabelChange () {
        const curWidth = document.querySelector('.label-wrapper').offsetWidth
        if (curWidth > labelMaxWidth && !this.isMaxWidth) {
          this.showCount = this.curResource.label_ids.length
          this.isMaxWidth = true
        }
      },
      handleMethodToggle () {
        if (this.isClone && !this.isCloneFlag) {
          this.addMethodValidator()
        }
      },
      addPathRule () {
        if (this.rules.path.find(rule => rule.message === this.cloneTips)) {
          return
        }
        this.rules.path.push({
          validator: (val) => {
            return !(this.cloneData.path === val)
          },
          message: this.cloneTips,
          trigger: 'blur'
        })
      },
      removePathRule () {
        this.rules.path.pop()
      },
      addMethodValidator () {
        setTimeout(() => {
          this.$refs.methodFormItem.setValidator({
            state: 'error',
            content: this.cloneTips
          })
        }, 0)
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';
    .actions {
        position: absolute;
        right: 0;
        top: -42px;

        .action-btn {
            height: 32px;
            line-height: 32px;
            background: #F0F1F5;
            text-align: center;
            padding: 0 9px;
            color: #3A84FF;
            font-size: 14px;
            border-radius: 2px;
            border: none;

            .apigateway-icon {
                transform: scale(1.3);
                display: inline-block;
            }
        }
    }

    .panel-wrapper {
        width: 95% !important;
        padding-left: 50px;

        /deep/ .bk-form-control,
        /deep/ .bk-select {
            /* max-width: 618px; */
        }
        
        .label-wrapper {
            display: inline-block;
            padding: 0 10px;
            .label-text {
                display: flex;
                align-items: center;
                display: inline-block;
                position: relative;
                height: 20px;
                line-height: 20px;
                font-size: 12px;
                padding: 0 10px;
                margin-right: 8px;
                cursor: pointer;
                border-radius: 2px;
                background: #f0f1f5;
                color: #63656e;
            }
            .label-text:last-child {
                margin-right: 0;
            }
            /deep/ .bk-tooltip-ref {
                vertical-align: unset;
                transform: translateX(-3px);
            }
            .placeholder {
                font-size: 12px;
                color: #c3cdd7;
            }
        }
    }

    .host-item {
        position: relative;
    }

    .add-host-btn,
    .delete-host-btn {
        color: #979BA5;
        font-size: 16px;
        display: inline-block;
        cursor: pointer;
        margin-right: 5px;
    }

    .add-host-btn {
        position: absolute;
        right: -28px;
        top: 8px;
    }

    .delete-host-btn {
        position: absolute;
        right: -50px;
        top: 8px;
    }

    .tokens-wrapper {
        position: absolute;
        left: 65px;
        top: 32px;
    }

    .apigateway-resource-addr {
        position: absolute;
        width: 680px;
        margin-top: 10px;
        right: 25px;
        z-index: 1000;
        background: #FFF;
        padding: 23px 30px;
        border-radius: 2px;
        box-shadow: 0 0 5px rgba(0, 0, 0, .5);
        .wrapper {
            max-height: 201px;
            overflow: auto;
        }

        .icon-ag-copy-fill {
            font-size: 16px;
            color: #737987;
            cursor: pointer;
        }

        .bk-form-item+.bk-form-item {
            margin-top: 10px;
        }
    }

    .ag-header-form {
        /deep/ .bk-label {
            display: none;
        }
    }
    .default-env-text {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    /* .ag-area {
        width: 620px;
        max-width: 620px;
    }
    .ag-area-en {
        width: 620px !important;
    } */
    .time-input {
        float: left;
        width: 180px;
        margin-right: 10px;
    }
    .group-text-style {
        width: 74px;
        text-align: center;
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
    .resource-wrapper .ag-tip {
        white-space: normal !important;
    }
    .hosts-append-wrapper {
        i {
            position: absolute;
            right: 4px;
            top: 7px;
            font-size: 16px;
        }
    }
    .weights-input /deep/  input {
        color: #63656e !important;
    }
    .weights-input.is-error /deep/ input[type=text] {
        color: #ff5656 !important;
    }
    .path-form-warpper {
        display: flex;
        align-items: center;
        .bk-form-control {
            flex: 1;
        }
    }
</style>

<style lang="postcss">
    .side-label-popover-cls {
        .tippy-tooltip {
            background: #fff;
            color:#63656E;
            box-shadow: 0 0 6px 0 #dcdee5;
            .tippy-arrow {
                border-top: 8px solid #fff;
            }
        }
        .label-text {
            display: inline-block;
            position: relative;
            height: 20px;
            line-height: 20px;
            font-size: 12px;
            padding: 0 5px;
            margin-right: 8px;
            cursor: pointer;
            border-radius: 2px;
            background: #f0f1f5;
            color: #63656e;
            &:last-child {
                margin-right: 0;
            }
        }
    }
</style>
