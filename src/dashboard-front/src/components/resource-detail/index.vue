<template>
  <div
    class="ag-resource-item"
    v-if="curResource"
    :class="{ 'show-diff': onlyShowDiff }"
  >
    <p
      class="title"
      :class="{
        'ag-diff':
          checkDiff('localData.name') ||
          checkDiff('localData.path') ||
          checkDiff('localData.description') ||
          checkDiff('localData.api_labels') ||
          checkDiff(
            'localData.contexts.resource_auth.config.auth_verified_required'
          ) ||
          checkDiff(
            'localData.contexts.resource_auth.config.app_verified_required'
          ) ||
          checkDiff('localData.is_public') ||
          checkDiff(
            'localData.contexts.resource_auth.config.resource_perm_required'
          ) ||
          checkDiff('localData.is_public') ||
          checkDiff('localData.allow_apply_permission'),
      }"
    >
      {{ $t("基本信息") }}
    </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.name') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("资源名称") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{ localData.name || "--" }}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.path') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("资源地址") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{ localData.path || "--" }}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.description') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("描述") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{ localData.description || "--" }}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.api_labels') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("标签") }}:</label>
        </bk-col>
        <bk-col style="margin-bottom: -4px;" :span="10">
          <template v-if="localData.api_labels?.length">
            <bk-tag
              class="ag-value"
              style="margin-left: 4px; margin-bottom: 4px;"
              v-for="tag in labels?.filter((label) => {
                if (localData.api_labels?.includes(String(label.id)))
                  return true;
              })"
              :key="tag.id"
            >{{ tag.name }}</bk-tag>
          </template>
          <div class="ag-value" v-else>--</div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{
          'ag-diff':
            checkDiff(
              'localData.contexts.resource_auth.config.auth_verified_required'
            ) ||
            checkDiff(
              'localData.contexts.resource_auth.config.app_verified_required'
            ),
        }"
      >
        <bk-col :span="4">
          <label class="ag-key">{{ $t("认证方式") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{ getResourceAuth(localData.contexts.resource_auth.config) }}
          </div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{
          'ag-diff': checkDiff(
            'localData.contexts.resource_auth.config.resource_perm_required'
          ),
        }"
      >
        <bk-col :span="4">
          <label class="ag-key">{{ $t("校验应用权限") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{
              localData.contexts.resource_auth.config.resource_perm_required
                ? $t("校验")
                : $t("不校验")
            }}
          </div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{
          'ag-diff':
            checkDiff('localData.is_public') ||
            checkDiff('localData.allow_apply_permission'),
        }"
      >
        <bk-col :span="4">
          <label class="ag-key">{{ $t("是否公开") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{ localData.is_public ? $t("是") : $t("否") }}
            {{
              localData.allow_apply_permission
                ? `(${$t("允许申请权限")})`
                : `(${$t("不允许申请权限")})`
            }}
          </div>
        </bk-col>
      </bk-row>
    </bk-container>

    <p
      class="title mt15"
      :class="{
        'ag-diff': checkDiff('localData.method') || checkDiff('localData.path'),
      }"
    >
      {{ $t("前端配置") }}
    </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.method') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("请求方法") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{ localData.method }}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.path') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("请求路径") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{ localData.path }}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.match_subpath') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("匹配所有子路径") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{ localData.match_subpath ? $t("是") : $t("否") }}
          </div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.enable_websocket') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("启用 WebSocket") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{ localData.enable_websocket ? $t("是") : $t("否") }}</div>
        </bk-col>
      </bk-row>
    </bk-container>

    <template v-if="localData.proxy?.backend_id">
      <p
        class="title mt15"
        :class="{
          'ag-diff':
            checkDiff('localData.proxy.backend_name') ||
            checkDiff('localData.proxy.config.method') ||
            checkDiff('localData.proxy.config.timeout') ||
            checkDiff('localData.proxy.config.path'),
        }"
      >
        {{ $t("后端配置") }}
      </p>
      <bk-container
        class="ag-kv-box"
        :col="14"
        :margin="6"
        :class="{ 'box-diff': checkDiff('localData.proxy.type') }"
      >
        <!-- <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.type') }">
          <bk-col :span="4">
            <label class="ag-key">{{ $t("后端类型:") }}</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">{{ localData.proxy.type.toUpperCase() }}</div>
          </bk-col>
        </bk-row> -->

        <!-- <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.path') }">
          <bk-col :span="4">
            <label class="ag-key">{{ $t("后端服务地址:") }}</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">{{ localData.proxy.config.path || "--" }}</div>
          </bk-col>
        </bk-row> -->

        <bk-row
          :class="{ 'ag-diff': checkDiff('localData.proxy.backend_name') }"
        >
          <bk-col :span="4">
            <label class="ag-key">{{ $t("后端服务:") }}</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">
              {{ localData.proxy.backend_name || "--" }}
            </div>
          </bk-col>
        </bk-row>

        <template v-if="localData.proxy.type === 'http'">
          <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.method') }"
          >
            <bk-col :span="4">
              <label class="ag-key">{{ $t("请求方法") }}:</label>
            </bk-col>
            <bk-col :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.method || "--" }}
              </div>
            </bk-col>
          </bk-row>

          <bk-row
            :class="{
              'ag-diff': checkDiff('localData.proxy.config.timeout'),
            }"
          >
            <bk-col :span="4">
              <label class="ag-key">{{ $t("自定义超时时间:") }}</label>
            </bk-col>
            <bk-col :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.timeout }}
              </div>
            </bk-col>
          </bk-row>

          <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.path') }"
          >
            <bk-col :span="4">
              <label class="ag-key">{{ $t("请求路径:") }}</label>
            </bk-col>
            <bk-col :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.path || "--" }}
              </div>
            </bk-col>
          </bk-row>

          <!-- <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.upstreams') }"
          >
            <bk-col :span="4">
              <label class="ag-key" style="line-height: 32px">Hosts:</label>
            </bk-col>
            <bk-col :span="10">
              <div
                class="bk-button-group"
                :class="{
                  'button-diff': checkDiff('localData.proxy.config.upstreams'),
                }"
                style="display: flex"
              >
                <div class="readonly-value">
                  {{
                    localData.useDefaultHost
                      ? $t("使用环境配置")
                      : $t("覆盖环境配置")
                  }}
                </div>
              </div>
              <div
                class="detail-wrapper"
                v-if="!localData.useDefaultHost"
                :class="{
                  'wrapper-diff': checkDiff('localData.proxy.config.upstreams'),
                }"
              >
                <div class="content-item">
                  <span class="key"> {{ $t("负载均衡类型") }}： </span>
                  <span class="value">{{
                    weightMap[localData.proxy.config.upstreams.loadbalance]
                  }}</span>
                </div>
                <div class="content-item">
                  <span class="key">Hosts：</span>
                  <div class="value">
                    <bk-table
                      class="bk-host-table f14"
                      :show-header="false"
                      :data="localData.proxy.config.upstreams.hosts"
                      size="small"
                      :border="true"
                      v-if="
                        localData.proxy.config.upstreams.loadbalance ===
                          'weighted-roundrobin'
                      "
                    >
                      <div slot="empty">
                        <table-empty empty />
                      </div>
                      <bk-table-column
                        :show-overflow-tooltip="true"
                        label="Host"
                        prop="host"
                      ></bk-table-column>
                      <bk-table-column
                        :width="60"
                        label="weight"
                        prop="weight"
                      ></bk-table-column>
                    </bk-table>
                    <ul class="ag-list" v-else>
                      <li
                        v-for="hostItem of localData.proxy.config.upstreams.hosts"
                        :key="hostItem.host"
                      >
                        {{ hostItem.host }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </bk-col>
          </bk-row> -->

          <!-- <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.timeout') }"
          >
            <bk-col :span="4">
              <label class="ag-key" style="line-height: 32px"
              >{{ $t("超时时间") }}:</label
              >
            </bk-col>
            <bk-col :span="10">
              <div
                class="bk-button-group"
                :class="{
                  'button-diff': checkDiff('localData.proxy.config.timeout'),
                }"
                style="display: flex"
              >
                <div class="readonly-value">
                  {{
                    localData.useDefaultTimeout
                      ? $t("使用环境配置")
                      : $t("覆盖环境配置")
                  }}
                </div>
              </div>

              <div
                class="detail-wrapper"
                v-if="!localData.useDefaultTimeout"
                :class="{
                  'wrapper-diff': checkDiff('localData.proxy.config.timeout'),
                }"
              >
                <div class="content-item">
                  <span class="key"> {{ $t("超时时间") }}： </span>
                  <span class="value"
                  >{{ localData.proxy.config.timeout }} {{ $t("秒") }}</span
                  >
                </div>
              </div>
            </bk-col>
          </bk-row> -->

          <!-- <bk-row
            :class="{
              'ag-diff': checkDiff('localData.proxy.config.transform_headers'),
            }"
          >
            <bk-col :span="4">
              <label class="ag-key" style="line-height: 32px"
              >{{ $t("Header转换") }}:</label
              >
            </bk-col>
            <bk-col :span="10">
              <div
                class="bk-button-group"
                :class="{
                  'button-diff': checkDiff(
                    'localData.proxy.config.transform_headers'
                  ),
                }"
                style="display: flex"
              >
                <div class="readonly-value">
                  {{
                    localData.useDefaultHeader
                      ? $t("使用环境配置")
                      : $t("追加环境配置")
                  }}
                </div>
              </div>
              <div
                class="detail-wrapper"
                v-if="!localData.useDefaultHeader"
                :class="{
                  'wrapper-diff': checkDiff(
                    'localData.proxy.config.transform_headers'
                  ),
                }"
              >
                <div class="content-item mb5">
                  <span class="key"> {{ $t("设置") }}： </span>
                  <div class="value">
                    <ul
                      class="ag-list"
                      v-if="
                        isEmptyObject(
                          localData.proxy.config.transform_headers.set
                        )
                      "
                    >
                      <li
                        v-for="(addItem, index) in localData.proxy.config
                          .transform_headers.set"
                        :key="index"
                      >
                        <div class="ds-key">{{ index }} :</div>
                        <div class="ds-value">{{ addItem }}</div>
                      </li>
                    </ul>

                    <span v-else>--</span>
                  </div>
                </div>
                <div class="content-item">
                  <span class="key"> {{ $t("删除") }}： </span>
                  <div class="value">
                    <ul
                      class="ag-list"
                      v-if="
                        localData.proxy.config.transform_headers.delete &&
                          localData.proxy.config.transform_headers.delete.length
                      "
                    >
                      <li
                        v-for="deleteItem of localData.proxy.config
                          .transform_headers.delete"
                        :key="deleteItem"
                      >
                        {{ deleteItem }}
                      </li>
                    </ul>
                    <span v-else>--</span>
                  </div>
                </div>
              </div>
            </bk-col>
          </bk-row> -->
        </template>

        <template v-if="localData.proxy.type === 'mock'">
          <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.code') }"
          >
            <bk-col :span="4">
              <label class="ag-key">Status Code:</label>
            </bk-col>
            <bk-col :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.code || "--" }}
              </div>
            </bk-col>
          </bk-row>

          <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.body') }"
          >
            <bk-col :span="4">
              <label class="ag-key">Response Body:</label>
            </bk-col>
            <bk-col :span="10">
              <div class="ag-value">
                <pre class="ag-pre mt0" v-if="localData.proxy.config.body">{{
                  localData.proxy.config.body || "--"
                }}</pre>
                <span v-else>--</span>
              </div>
            </bk-col>
          </bk-row>

          <bk-row
            :class="{ 'ag-diff': checkDiff('localData.proxy.config.headers') }"
          >
            <bk-col :span="4">
              <label class="ag-key">Headers:</label>
            </bk-col>
            <bk-col :span="10">
              <div v-if="isEmptyObject(localData.proxy.config.headers)">
                <ul class="ag-list">
                  <li
                    v-for="(headerItem, index) in localData.proxy.config
                      .headers"
                    :key="index"
                  >
                    {{ index }} : {{ headerItem }}
                  </li>
                </ul>
              </div>
              <span v-else>--</span>
            </bk-col>
          </bk-row>
        </template>
      </bk-container>
    </template>

    <!-- <p class="title mt15" :class="{ 'ag-diff': checkAuthConfigDiff() }">
      {{ $t("安全设置") }}
    </p>
    <bk-container
      class="ag-kv-box"
      :col="14"
      :margin="6"
      v-if="localData.contexts.resource_auth.config"
    >
      <bk-row
        :class="{
          'ag-diff': checkDiff(
            'localData.contexts.resource_auth.config.app_verified_required'
          ),
        }"
        v-if="
          localData.contexts.resource_auth.config.hasOwnProperty(
            'app_verified_required'
          )
        "
      >
        <bk-col :span="4">
          <label class="ag-key">{{ $t("应用认证") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{
              localData.contexts.resource_auth.config.app_verified_required
                ? $t("是")
                : $t("否")
            }}
          </div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{
          'ag-diff': checkDiff(
            'localData.contexts.resource_auth.config.resource_perm_required'
          ),
        }"
        v-if="
          localData.contexts.resource_auth.config.hasOwnProperty(
            'resource_perm_required'
          )
        "
      >
        <bk-col :span="4">
          <label class="ag-key">{{ $t("校验访问权限") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{
              localData.contexts.resource_auth.config.resource_perm_required
                ? $t("是")
                : $t("否")
            }}
          </div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{
          'ag-diff': checkDiff(
            'localData.contexts.resource_auth.config.auth_verified_required'
          ),
        }"
        v-if="
          localData.contexts.resource_auth.config.hasOwnProperty(
            'auth_verified_required'
          )
        "
      >
        <bk-col :span="4">
          <label class="ag-key">{{ $t("用户认证") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{
              localData.contexts.resource_auth.config.auth_verified_required
                ? $t("是")
                : $t("否")
            }}
          </div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.disabled_stages') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("禁用环境") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            {{ localData.disabled_stages.join("; ") || "--" }}
          </div>
        </bk-col>
      </bk-row>
    </bk-container> -->

    <p class="title mt15" :class="{ 'ag-diff': checkDiff('localData.doc_updated_time') }">
      {{ $t("文档") }}
    </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.doc_updated_time') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t("文档更新时间") }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            <template v-if="localLanguage === 'en'">
              {{ localData.doc_updated_time.en || "--" }}
            </template>
            <template v-else>
              {{ localData.doc_updated_time.zh || "--" }}
            </template>
          </div>
        </bk-col>
      </bk-row>
    </bk-container>

    <!--  插件  -->
    <div v-if="localData.plugins?.length">
      <template v-for="plugin in localData.plugins" :key="plugin.id">
        <div class="container-diff" :class="getPluginDiffClass(plugin)">
          <p class="title mt15">
            {{ $t('插件:{name}', { name: plugin.name }) }}
          </p>
          <ConfigDisplayTable :plugin="plugin" first-col-width="auto" />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  ref,
  watch,
} from 'vue';
import cookie from 'cookie';
// import dayjs from 'dayjs';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import ConfigDisplayTable from '@/views/components/plugin-manage/config-display-table.vue';

const common = useCommon();

const { t } = useI18n();

const props = defineProps({
  curResource: {
    type: Object,
    default: () => {
      return null;
    },
  },
  diffData: {
    type: Object,
    default: () => {},
  },
  onlyShowDiff: {
    type: Boolean,
    default: false,
  },
  backendsList: {
    type: Array,
    default: [],
  },
  // 是否作为旧版本资源展示
  isSource: {
    type: Boolean,
    default: false,
  },
});

// const weightMap = reactive({
//   roundrobin: t('轮询(Round-Robin)'),
//   'weighted-roundrobin': t('加权轮询(Weighted Round-Robin)'),
// });

const diffMap = ref<any>({});
const localData = ref<any>({
  name: '',
  disabled_stages: [],
  config: {},
  proxy: {
    type: '',
    config: {
      transform_headers: {
        add: [],
      },
    },
  },
  useDefaultTimeout: true,
  useDefaultHeader: true,
  useDefaultHost: true,
  contexts: {
    resource_auth: {
      config: {},
    },
  },
});

const localLanguage =  cookie.parse(document.cookie).blueking_language || 'zh-cn';

// const formatDate = (value: any) => {
//   if (value) {
//     return dayjs(value).format('YYYY-MM-DD HH:mm:ss');
//   }
//   return '--';
// };

const isEmptyObject = (data: any) => {
  if (data) {
    const keys = Object.keys(data);
    return !!keys.length;
  }
  return false;
};

const isString = (str: any) => {
  return typeof str === 'string';
};

const getResourceAuth = (auth: any) => {
  if (!auth) return '--';
  const tmpArr: string[] = [];

  if (auth?.auth_verified_required) {
    tmpArr.push(`${t('用户认证')}`);
  }
  if (auth?.app_verified_required) {
    tmpArr.push(`${t('蓝鲸应用认证')}`);
  }
  return tmpArr.join(', ');
};

const initLocalData = async () => {
  const data = JSON.parse(JSON.stringify(props.curResource));

  if (data.contexts.resource_auth.config) {
    if (isString(data.contexts.resource_auth.config)) {
      data.contexts.resource_auth.config = JSON.parse(data.contexts.resource_auth.config);
    }
  } else {
    data.config = {};
  }

  if (data.proxy.config) {
    if (isString(data.proxy.config)) {
      data.proxy.config = JSON.parse(data.proxy.config);
    }
  } else {
    data.proxy.config = {};
  }

  if (data.proxy.type === 'http') {
    data.useDefaultTimeout = !data.proxy.config.timeout;

    if (JSON.stringify(data.proxy.config.upstreams) === '{}') {
      data.useDefaultHost = true;
    } else {
      data.useDefaultHost = false;
    }

    if (JSON.stringify(data.proxy.config.transform_headers) === '{}') {
      data.useDefaultHeader = true;
    } else {
      data.useDefaultHeader = false;
    }
  }
  localData.value = data;

  const backendId = localData.value?.proxy?.backend_id;
  if (backendId) {
    const curBackend: any = props.backendsList.find((item: any) => item.id === backendId);
    if (curBackend) {
      localData.value.proxy.backend_name = curBackend.name;
    }
  }
};

const initDiff = () => {
  diffMap.value = {};
  if (!props.diffData) {
    return false;
  }
  findAllDiff(props.diffData);

  // 处理后端配置使用默认配置情况
  if (diffMap.value['localData.proxy.config.timeout']) {
    diffMap.value['localData.useDefaultTimeout'] = true;
  }

  if (diffMap.value['localData.proxy.config.upstreams'] === '{}') {
    diffMap.value['localData.useDefaultHost'] = true;
  }

  if (diffMap.value['localData.proxy.config.transform_headers'] === '{}') {
    diffMap.value['localData.useDefaultHeader'] = true;
  }

  // 处理安全设置禁用环境
  const keys = Object.keys(diffMap.value);
  if (keys.some(item => item.startsWith('localData.disabled_stages'))) {
    diffMap.value['localData.disabled_stages'] = true;
  }
};

const findAllDiff = (value: any, prePath = 'localData') => {
  if (Array.isArray(value)) {
    if (value.length) {
      value.forEach((item) => {
        const path = `${prePath}`;
        findAllDiff(item, path);
      });
    } else {
      diffMap.value[prePath] = '[]';
    }
  } else if (typeof value === 'object') {
    if (JSON.stringify(value) === '{}') {
      diffMap.value[prePath] = '{}';
    } else {
      for (const key of Object.keys(value)) {
        const path = `${prePath}.${key}`;
        findAllDiff(value[key], path);
      }
    }
  } else {
    diffMap.value[prePath] = value;
  }
};

const checkDiff = (path: any) => {
  const keys = Object.keys(diffMap.value);
  return keys.some(item => item.startsWith(path));
};

// const checkAuthConfigDiff = () => {
//   return (
//     checkDiff('localData.contexts.resource_auth.config.app_verified_required')
//     || checkDiff('localData.contexts.resource_auth.config.auth_verified_required')
//     || checkDiff('localData.contexts.resource_auth.config.resource_perm_required')
//     || checkDiff('localData.disabled_stages')
//   );
// };

const getPluginDiffClass = (plugin: any) => {
  // 检查传入的 plugin 是否记录在 diffMap 中
  const diffMapPluginKey = `localData.plugins.${plugin.code || plugin.type}`;
  const isPluginUpdated = Object.keys(diffMap.value).some(item => item.startsWith(diffMapPluginKey));

  // 插件在 diffMap 中，属于更新的内容，给予 item-updated 样式
  if (isPluginUpdated) {
    return 'item-updated';
  }

  // 插件不在 diffMap 中，检查传入的 plugin 是否存在于 curResource.diff.plugins 中
  // 如果存在，说明属于新增或删除的插件，如果不存在说明没有变动
  const diffPlugins = props.curResource?.diff?.plugins ?? {};
  const isPluginAddedOrDeleted = Object.keys(diffPlugins)
    .some((pluginCode: string) => pluginCode === (plugin.type || plugin.code));

  // 属于新增或删除的插件
  if (isPluginAddedOrDeleted) {
    // 传入了 isSource，表示当前 resource 作为旧数据展示，插件的变动属于被删除的内容，给予 item-deleted 样式
    if (props.isSource) {
      return 'item-deleted';
    }

    // 当前 resource 作为新数据展示，插件的变动属于新添加的内容，给予 item-deleted 样式
    return 'item-added';
  }

  // 插件没有变更，返回空 class，不改变样式
  return '';
};

// 网关标签
const labels = computed(() => common.gatewayLabels || []);

watch(
  () => props.curResource,
  () => {
    initDiff();
    initLocalData();
  },
);

initDiff();
initLocalData();
</script>

<style lang="scss" scoped>
.ag-dl {
  padding: 15px 40px 5px 30px;
}

.ag-diff {
  .ag-value {
    color: #fe9c00 !important;
  }

  .ag-pre {
    background: #fbf4e9;
    color: #fe9c00;
  }

  .ag-list {
    background: #fbf4e9;
  }
}

.ag-user-type {
  width: 560px;
  height: 80px;
  background: #fafbfd;
  border-radius: 2px;
  border: 1px solid #dcdee5;
  padding: 17px 20px 0 20px;
  position: relative;
  overflow: hidden;

  .apigateway-icon {
    font-size: 80px;
    position: absolute;
    color: #ecf2fc;
    top: 15px;
    right: 20px;
    z-index: 0;
  }

  strong {
    font-size: 13px;
    margin-bottom: 10px;
    line-height: 1;
    display: block;
  }

  p {
    font-size: 12px;
    color: #63656e;
  }
}

.detail-wrapper {
  padding: 10px 20px 10px 10px;
  background: #f0f1f5;
  margin-top: 6px;
  border-radius: 2px;

  &.wrapper-diff {
    background: #fbf4e9;
  }

  .content-item {
    display: flex;
    font-size: 13px;
    line-height: 26px;
  }

  .key {
    width: 100px;
    text-align: right;
    display: inline-block;
    vertical-align: middle;
    color: #63656e;
    line-height: 28px;
  }
  .value {
    color: #313238;
    flex: 1;
  }
}

.ag-list {
  border-radius: 2px;
  border: 1px solid #dcdee5;
  background: #fff;
  font-size: 13px;

  > li {
    line-height: 22px;
    padding: 0 15px;
    display: flex;
    padding: 5px 10px;
    background: #fff;

    .ds-key {
      white-space: nowrap;
    }
    .ds-value {
      white-space: normal;
      word-break: break-all;
      padding-left: 5px;
    }

    & + li {
      border-top: 1px solid #dcdee5;
    }
  }
}

.ag-tab-button {
  cursor: default;
  &:hover {
    border-color: #c4c6cc;
    color: #63656e;
  }
  &.is-selected {
    border-color: #3a84ff !important;
    color: #3a84ff !important;
    a {
      color: #3a84ff !important;
    }
  }
}

.ag-value {
  white-space: normal;
  word-break: break-all;
}

.bk-host-table {
  tr {
    background: #fff !important;
  }
  td,
  th {
    height: 36px;
    background: #fff !important;
  }
}

.container-diff {
  padding: 2px 8px;
  margin: 18px 0;

  &.item-added {
    background-color: rgba(45, 203, 86, 0.1);
  }

  &.item-updated {
    background-color: rgba(255, 156, 1, 0.1);
  }

  &.item-deleted {
    background-color: rgba(234, 54, 54, 0.1);
  }
}
.ag-kv-box {
  &.box-diff {
    background: #fbf4e9;
    border-radius: 2px;
    padding-top: 10px;
    padding-bottom: 10px;

    .ag-value,
    .ag-list {
      color: #fe9c00;
    }
  }

  .ag-key,
  .ag-value {
    font-size: 12px;
  }
}

.ag-resource-item {
  padding: 20px 30px;
  margin: 0 -30px;
  .title {
    font-size: 12px;
    color: #63656e;
    font-weight: bold;
    padding-bottom: 10px;
    border-bottom: 1px solid #dcdee5;
    margin-bottom: 17px;
  }
  &.show-diff {
    .title {
      display: none;

      &.ag-diff {
        display: block;
      }
    }
    .bk-grid-row {
      display: none;

      &.ag-diff {
        display: block;
      }
    }

    .box-diff {
      .bk-grid-row {
        display: block;
      }
    }
  }
}
</style>

<style lang="scss">
.bk-button-group .readonly-value {
  height: 32px;
  line-height: 32px;
  font-size: 13px;
  color: #313238;
}
.source-version {
  .detail-wrapper.wrapper-diff {
    background: #f0f1f5;
  }

  .ag-diff .ag-pre {
    background: #313238;
    color: #fff;
  }

  .ag-value,
  .ag-list {
    color: #313238 !important;
  }

  .ag-diff .ag-list {
    background: #fff;
  }

  .ag-diff .ag-value {
    color: #313238 !important;
  }

  .ag-kv-box.box-diff {
    background: #fff;
  }
}
.ag-kv-box {
  .bk-grid-row {
    margin-bottom: 12px;
  }
  .ag-key {
    font-size: 14px;
    color: #63656e;
    display: block;
    text-align: right;
    padding-right: 0;
  }

  .ag-value {
    font-size: 14px;
    color: #313238;
  }
}
</style>
